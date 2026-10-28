#!/usr/bin/env python3
"""
stream.py - Darkstar companion for the Raspberry Pi camera (Tailscale "tunnel" mode).

Implements Darkstar's companion protocol (docs/companion-protocol.md):
  * Video  : TCP 5600. Client sends "DSV1 <token>\n", then receives frames
             packed as >BIQ (type, length, timestamp_us) + payload.
             type 1 = JSON hello, 2 = H.264 key frame, 3 = H.264 delta frame.
  * Files  : HTTP 8765 with "Authorization: Bearer <token>"
             /api/status, /api/missions, /api/logs

SETUP (once, on the Pi)
    sudo apt install -y python3-picamera2 python3-av
    cd ~/drone-stream
    python3 -m venv --system-site-packages .venv

RUN
    source .venv/bin/activate
    DARKSTAR_TOKEN=yourSecret123 python stream.py

DARKSTAR (laptop) - Connection -> "Companion video and files":
    Address   : the Pi's 100.x.x.x Tailscale IP (printed below)
    Token     : the same DARKSTAR_TOKEN
    Transport : "Unencrypted services inside a Tailscale tunnel..."
    Video port 5600, Files port 8765 -> Save
"""

import json
import os
import re
import socket
import struct
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Full, Queue
from urllib.parse import unquote

from picamera2 import Picamera2
from picamera2.outputs import Output

# ---------------- settings ----------------
TOKEN = os.environ.get("DARKSTAR_TOKEN", "changeme")   # MUST match the token typed in Darkstar
WIDTH, HEIGHT, FPS = 1280, 720, 25
BITRATE = 2_500_000          # bits/s; lower (e.g. 1_200_000) on a weak link
VIDEO_PORT = 5600
FILES_PORT = 8765
DATA_DIR = Path.home() / "drone-stream"
MISSIONS_DIR = DATA_DIR / "missions"
LOGS_DIR = DATA_DIR / "logs"
# ------------------------------------------

HEADER = struct.Struct(">BIQ")
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


# ---------------- H.264 helpers ----------------
def split_nals(data: bytes):
    """Split an Annex-B buffer into NAL units (without start codes)."""
    out, i, n = [], 0, len(data)
    starts = []
    while i < n - 3:
        if data[i] == 0 and data[i + 1] == 0:
            if data[i + 2] == 1:
                starts.append((i, i + 3)); i += 3; continue
            if data[i + 2] == 0 and i + 3 < n and data[i + 3] == 1:
                starts.append((i, i + 4)); i += 4; continue
        i += 1
    for k, (_, body) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else n
        out.append(data[body:end])
    return out


def annexb(nals):
    return b"".join(b"\x00\x00\x00\x01" + x for x in nals)


# ---------------- video fan-out ----------------
class Hub:
    """Receives encoded frames from picamera2 and hands them to every viewer."""

    def __init__(self):
        self.lock = threading.Lock()
        self.clients: list[Queue] = []
        self.sps = self.pps = None
        self.codec = None

    def hello(self) -> bytes | None:
        if not self.codec:
            return None
        body = json.dumps({"codec": self.codec, "width": WIDTH, "height": HEIGHT, "fps": FPS,
                           "kbps": BITRATE // 1000, "source": "picamera2"}).encode()
        return HEADER.pack(1, len(body), 0) + body

    def add(self) -> Queue:
        q = Queue(maxsize=120)
        with self.lock:
            self.clients.append(q)
        return q

    def remove(self, q: Queue):
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)

    def push(self, data: bytes):
        nals = split_nals(bytes(data))
        if not nals:
            return
        types = {x[0] & 0x1F for x in nals}
        for x in nals:
            t = x[0] & 0x1F
            if t == 7:
                self.sps = x
                if len(x) >= 4:
                    self.codec = "avc1.%02x%02x%02x" % (x[1], x[2], x[3])
            elif t == 8:
                self.pps = x
        key = 5 in types
        if key and (7 not in types or 8 not in types):
            if not (self.sps and self.pps):
                return                       # cannot decode yet
            nals = [self.sps, self.pps] + [x for x in nals if (x[0] & 0x1F) not in (7, 8)]
        if not self.codec:
            return
        payload = annexb(nals)
        frame = HEADER.pack(2 if key else 3, len(payload), time.monotonic_ns() // 1000) + payload
        with self.lock:
            clients = list(self.clients)
        for q in clients:
            try:
                q.put_nowait((key, frame))
            except Full:                      # slow viewer: flush, it will resync on next key frame
                with q.mutex:
                    q.queue.clear()


hub = Hub()


class HubOutput(Output):
    def outputframe(self, frame, keyframe=True, timestamp=None, *args, **kwargs):
        hub.push(frame)


def serve_viewer(conn: socket.socket, addr):
    q = None
    try:
        conn.settimeout(5)
        line = b""
        while not line.endswith(b"\n") and len(line) < 512:
            ch = conn.recv(1)
            if not ch:
                return
            line += ch
        if line.strip() != f"DSV1 {TOKEN}".encode():
            print(f"[video] {addr[0]} sent a wrong token - closed")
            return
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        conn.settimeout(10)
        for _ in range(50):                   # wait up to 5 s for first SPS
            if hub.hello():
                break
            time.sleep(0.1)
        hello = hub.hello()
        if not hello:
            print("[video] encoder produced no SPS yet - closing")
            return
        conn.sendall(hello)
        print(f"[video] {addr[0]} watching ({hub.codec})")
        q = hub.add()
        waiting_key = True
        while True:
            try:
                key, frame = q.get(timeout=5)
            except Empty:
                continue
            if waiting_key and not key:
                continue
            waiting_key = False
            conn.sendall(frame)
    except OSError:
        pass
    finally:
        if q is not None:
            hub.remove(q)
            print(f"[video] {addr[0]} left")
        conn.close()


def video_server(bind_ip: str):
    srv = socket.create_server((bind_ip, VIDEO_PORT))   # SO_REUSEADDR is set automatically
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=serve_viewer, args=(conn, addr), daemon=True).start()


# ---------------- file API ----------------
class FilesHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth(self):
        if self.headers.get("Authorization", "") != f"Bearer {TOKEN}":
            self._send(401, {"detail": "bad token"})
            return False
        return True

    @staticmethod
    def _listing(d: Path, pattern: str):
        return [{"name": p.name, "bytes": p.stat().st_size} for p in sorted(d.glob(pattern)) if p.is_file()]

    def do_GET(self):
        if not self._auth():
            return
        p = self.path
        if p == "/api/status":
            self._send(200, {"ok": True, "version": "stream.py", "camera": f"{WIDTH}x{HEIGHT}@{FPS}",
                             "codec": hub.codec, "viewers": len(hub.clients)})
        elif p == "/api/missions":
            self._send(200, self._listing(MISSIONS_DIR, "*.waypoints"))
        elif p == "/api/logs":
            self._send(200, self._listing(LOGS_DIR, "*"))
        elif p.startswith("/api/logs/"):
            name = unquote(p[len("/api/logs/"):])
            f = LOGS_DIR / name
            if SAFE_NAME.match(name) and f.is_file():
                self._send(200, raw=f.read_bytes(), ctype="application/octet-stream")
            else:
                self._send(404, {"detail": "no such log"})
        else:
            self._send(404, {"detail": "no such route"})

    def do_PUT(self):
        if not self._auth():
            return
        if not self.path.startswith("/api/missions/"):
            return self._send(404, {"detail": "no such route"})
        name = unquote(self.path[len("/api/missions/"):])
        if not name.endswith(".waypoints"):
            name += ".waypoints"
        if not SAFE_NAME.match(name):
            return self._send(400, {"detail": "bad name"})
        n = int(self.headers.get("Content-Length", "0"))
        if n > 4 << 20:
            return self._send(413, {"detail": "too large"})
        body = self.rfile.read(n)
        (MISSIONS_DIR / name).write_bytes(body)
        self._send(200, {"name": name, "items": max(0, body.count(b"\n") - 1)})

    def do_DELETE(self):
        if not self._auth():
            return
        name = unquote(self.path[len("/api/missions/"):])
        f = MISSIONS_DIR / name
        if self.path.startswith("/api/missions/") and SAFE_NAME.match(name) and f.is_file():
            f.unlink()
        self._send(200, {"deleted": True})


# ---------------- camera ----------------
def is_pi5() -> bool:
    try:
        return "Raspberry Pi 5" in Path("/proc/device-tree/model").read_text(errors="ignore")
    except OSError:
        return False


def make_encoder():
    iperiod = FPS                                # key frame every second -> fast join/recovery
    if is_pi5():                                 # Pi 5 has no hardware H.264 encoder
        from picamera2.encoders import LibavH264Encoder
        try:
            return LibavH264Encoder(bitrate=BITRATE, repeat=True, iperiod=iperiod, profile="baseline")
        except TypeError:
            return LibavH264Encoder(bitrate=BITRATE, repeat=True, iperiod=iperiod)
    from picamera2.encoders import H264Encoder
    try:
        return H264Encoder(bitrate=BITRATE, repeat=True, iperiod=iperiod, profile="baseline")
    except TypeError:
        return H264Encoder(bitrate=BITRATE, repeat=True, iperiod=iperiod)


def tailscale_ip():
    try:
        return subprocess.check_output(["tailscale", "ip", "-4"], text=True, timeout=5).split()[0]
    except Exception:
        return None


def main():
    if TOKEN == "changeme":
        print("WARNING: using the default token 'changeme'. Set DARKSTAR_TOKEN=... for real use.")
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    ip = tailscale_ip()
    bind_ip = ip or "0.0.0.0"           # only listen on the tailnet when Tailscale is up

    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "YUV420"},
        controls={"FrameDurationLimits": (int(1e6 / FPS), int(1e6 / FPS))},
    ))
    picam2.start_recording(make_encoder(), HubOutput())

    threading.Thread(target=video_server, args=(bind_ip,), daemon=True).start()
    files = ThreadingHTTPServer((bind_ip, FILES_PORT), FilesHandler)
    threading.Thread(target=files.serve_forever, daemon=True).start()

    print(f"\nDarkstar companion running - {WIDTH}x{HEIGHT} @ {FPS} fps H.264")
    print("In Darkstar -> Connection -> Companion video and files:")
    print(f"  Address   : {ip or '<Pi Tailscale 100.x IP - tailscale is NOT up!>'}")
    print(f"  Token     : {TOKEN}")
    print("  Transport : Tailscale tunnel")
    print(f"  Video port: {VIDEO_PORT}   Files port: {FILES_PORT}")
    print("Ctrl-C to stop.\n")
    try:
        while True:
            time.sleep(1)
    finally:
        picam2.stop_recording()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped")
