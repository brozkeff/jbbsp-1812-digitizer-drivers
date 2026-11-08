# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
"""Presentation HTTP and synthetic serial checks; no tablet validation."""
import importlib.util
import json
import os
from pathlib import Path
import pty
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SPEC = importlib.util.spec_from_file_location(
    "presentation", Path(__file__).resolve().parents[1] / "docs/openalt-2026/server.py"
)
presentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(presentation)


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.server = presentation.ThreadingHTTPServer(('127.0.0.1', 0), presentation.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        presentation.stop()

    def post(self, path: str, data: dict, origin: str | None = None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        with urlopen(Request(self.url + path, data=json.dumps(data).encode(), headers=headers)) as response:
            return json.load(response)

    def test_page_and_failed_open(self):
        with urlopen(self.url) as response:
            self.assertIn(b'10-minute lightning talk', response.read())
        with self.assertRaises(HTTPError) as error:
            self.post('/start', {'port': '/nonexistent/draco-test'})
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        self.assertIsNone(presentation.port)
        with self.assertRaises(HTTPError) as error:
            self.post('/start', {}, 'https://example.com')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_synthetic_receive_stop_and_restart(self):
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        for _ in range(2):
            self.post('/start', {'port': os.ttyname(slave)})
            os.write(master, bytes.fromhex('99 18 11 1d 0c'))
            deadline = time.monotonic() + 2
            while True:
                with urlopen(self.url + '/data') as response:
                    output = json.load(response)['text']
                if 'u=2200 v=1565' in output or time.monotonic() >= deadline:
                    break
                time.sleep(0.02)
            self.assertIn('u=2200 v=1565', output)
            self.assertEqual(self.post('/stop', {})['status'], 'Stopped')
            self.assertIsNone(presentation.port)
            self.assertIsNone(presentation.reader_thread)
            self.assertEqual(presentation.status, 'Stopped')
