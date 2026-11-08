# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
"""Local presentation server; hardware access is explicitly requested."""
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.serial_backend import PosixPort, Settings

lock = threading.Lock()
session_lock = threading.Lock()
port = None
reader_thread = None
buffer = bytearray()
status = "Not connected"


def reader(device):
    global status
    try:
        while port is device:
            data = device.read(0.2)
            if data:
                with lock:
                    buffer.extend(data)
                    del buffer[:-200]
    except Exception as exc:
        if port is device:
            status = f"Serial error: {exc} · stop before retrying"


def stop() -> None:
    global port, reader_thread
    device, port = port, None
    if reader_thread:
        reader_thread.join()
        reader_thread = None
    if device:
        device.close()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def reply(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != '/data':
            return super().do_GET()
        with lock:
            raw = bytes(buffer)
        groups = []
        i = 0
        while i + 5 <= len(raw):
            if raw[i] & 128 and all(not b & 128 for b in raw[i+1:i+5]):
                b = raw[i:i+5]
                groups.append(f'{b.hex(" ")}  u={b[1]+128*b[2]} v={b[3]+128*b[4]}')
                i += 5
            else:
                i += 1
        self.reply({'text': f'{status}\nRaw: {raw.hex(" ")}\nTentative groups and coordinates:\n' + '\n'.join(groups[-8:])})

    def do_POST(self):
        with session_lock:
            self.handle_action()

    def handle_action(self):
        global port, status, reader_thread
        if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
            return self.reply({'error': 'Origin rejected'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 4096:
                raise ValueError('Request too large')
            data = json.loads(self.rfile.read(length) or b'{}')
            if self.path == '/stop':
                stop()
                status = 'Stopped'
            elif self.path == '/start':
                if port:
                    raise ValueError('Stop the current session first')
                device = PosixPort(Settings(port=data['port'], backend='posix')).open()
                port = device
                with lock:
                    buffer.clear()
                status = 'Listening · 9600 baud · 8 data bits · no parity · 1 stop bit'
                reader_thread = threading.Thread(target=reader, args=(device,), daemon=True)
                reader_thread.start()
            else:
                return self.reply({'error': 'Not found'}, 404)
            self.reply({'status': status})
        except Exception as exc:
            self.reply({'error': str(exc)}, 400)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('Open http://127.0.0.1:8765/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with session_lock:
            stop()
        server.server_close()
