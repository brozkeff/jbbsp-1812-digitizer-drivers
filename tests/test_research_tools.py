# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Synthetic infrastructure tests, never physical-tablet acceptance tests."""
import contextlib
import hashlib
import io
import json
import os
import queue
import select
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools import artifacts, draco, validate_docs
from tools.serial_backend import PosixPort, Settings
from tools.sessions import SessionWriter, load_session


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "session"

    def record(self):
        writer = SessionWriter(self.path, {"port": "synthetic"}, "fixture")
        writer.receive(b"\x00\xff\x11")
        writer.receive(b"\x13\r\n\x80")
        writer.finish("complete")
        return writer

    def test_raw_replay_is_lossless_and_tx_never_replayed(self):
        writer = SessionWriter(self.path, {})
        writer.receive(b"a\x00\xff")
        writer.event("tx", hex="deadbeef", length=4)
        writer.receive(b"\x11\x13\n\r")
        writer.finish("complete")
        out = io.BytesIO()
        draco.replay(self.path, out)
        self.assertEqual(out.getvalue(), b"a\x00\xff\x11\x13\n\r")

    def test_checksum_detects_corruption(self):
        self.record()
        (self.path / "rx.bin").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "integrity"):
            load_session(self.path)

    def test_events_must_reconstruct_raw_even_with_updated_hash(self):
        self.record()
        path = self.path / "events.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines()]
        next(e for e in events if e["kind"] == "rx")["offset"] = 7
        path.write_text("".join(json.dumps(e) + "\n" for e in events))
        manifest = json.loads((self.path / "session.json").read_text())
        manifest["files"]["events.jsonl"] = {
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        (self.path / "session.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "raw stream"):
            load_session(self.path)

    def test_incomplete_session_is_not_verified(self):
        writer = SessionWriter(self.path, {})
        try:
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                load_session(self.path)
        finally:
            writer.finish("interrupted")

    def test_existing_directory_is_not_overwritten(self):
        self.record()
        with self.assertRaises(FileExistsError):
            SessionWriter(self.path, {})

    def test_analysis_labels_host_timing_and_handles_silence(self):
        writer = SessionWriter(self.path, {})
        writer.finish("complete")
        report = draco.analyze(self.path)
        self.assertIsNone(report["high_bit_fraction"])
        self.assertEqual(report["rx_bytes"], 0)
        self.assertIn("not packet", report["interpretation"])


@unittest.skipUnless(os.name == "posix", "PTY tests require POSIX")
class SerialTests(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = os.openpty()
        self.addCleanup(self.close_descriptors)
        self.port = os.ttyname(self.slave)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "capture"
        self.settings = Settings(self.port, backend="posix")

    def close_descriptors(self):
        for fd in (self.master, self.slave):
            with contextlib.suppress(OSError):
                os.close(fd)

    def wait_open(self):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            path = self.path / "events.jsonl"
            if path.exists() and '"kind": "opened"' in path.read_text():
                return
            time.sleep(0.005)
        raise AssertionError("capture did not open")

    def test_capture_fragmented_control_bytes_without_tx_and_restores_tty(self):
        import termios
        before = termios.tcgetattr(self.slave)
        failures = []
        def producer():
            try:
                self.wait_open()
                for chunk in (b"\x00\x80", b"\xff\x11\x13", b"\r\nabc"):
                    os.write(self.master, chunk)
                    time.sleep(0.015)
            except BaseException as exc:
                failures.append(exc)
        thread = threading.Thread(target=producer)
        thread.start()
        result = draco.run_capture(self.settings, self.path, 0.15)
        thread.join(3)
        self.assertFalse(failures)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(load_session(self.path)[2], b"\x00\x80\xff\x11\x13\r\nabc")
        self.assertFalse(select.select([self.master], [], [], 0)[0], "capture emitted data")
        self.assertEqual(termios.tcgetattr(self.slave), before)

    def test_zero_byte_timeout(self):
        result = draco.run_capture(self.settings, self.path, 0.03)
        self.assertEqual(result["rx_bytes"], 0)
        self.assertEqual(result["status"], "complete")

    def test_pyserial_preserves_control_bytes_without_tx(self):
        failures = []
        def producer():
            try:
                self.wait_open()
                os.write(self.master, b"\x00\xff\x11\x13\r\n")
            except BaseException as exc:
                failures.append(exc)
        thread = threading.Thread(target=producer)
        thread.start()
        result = draco.run_capture(Settings(self.port, backend="pyserial"), self.path, 0.1)
        thread.join(3)
        self.assertFalse(failures)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(load_session(self.path)[2], b"\x00\xff\x11\x13\r\n")
        self.assertFalse(select.select([self.master], [], [], 0)[0])

    def test_exclusive_open_and_release(self):
        first = PosixPort(self.settings).open()
        try:
            with self.assertRaises(OSError):
                PosixPort(self.settings).open()
        finally:
            first.close()
        PosixPort(self.settings).open().close()

    def test_disconnect_finalizes_error_capture(self):
        def disconnect():
            self.wait_open()
            os.close(self.master)
        thread = threading.Thread(target=disconnect)
        thread.start()
        result = draco.run_capture(self.settings, self.path, 0.2)
        thread.join(3)
        self.assertEqual(result["status"], "error")
        self.assertEqual(load_session(self.path)[0]["status"], "error")

    def test_missing_device_records_error(self):
        result = draco.run_capture(Settings("/does-not-exist", backend="posix"), self.path, 0.02)
        self.assertEqual(result["status"], "error")
        self.assertEqual(load_session(self.path)[2], b"")

    def test_sigint_finalizes_recording(self):
        proc = subprocess.Popen([sys.executable, "tools/draco.py", "capture", "--port", self.port,
                                 "--backend", "posix", "--duration", "5", "--output", str(self.path)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.wait_open()
            proc.send_signal(signal.SIGINT)
            stdout, stderr = proc.communicate(timeout=3)
            self.assertEqual(proc.returncode, 130, stderr)
            self.assertEqual(json.loads(stdout)["status"], "interrupted")
            self.assertEqual(load_session(self.path)[0]["status"], "interrupted")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    def test_scheduled_probe_logs_exact_transmission(self):
        recipe = {"name": "synthetic-only", "source": "original PTY fixture", "steps": [
            {"kind": "tx", "at_ms": 10, "hex": "00ff11"},
            {"kind": "annotation", "at_ms": 15, "text": "test"},
            {"kind": "tx", "at_ms": 20, "hex": "13aa"}]}
        result = draco.run_capture(self.settings, self.path, 0.05, recipe=recipe, recipe_hash="fixture")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(os.read(self.master, 100), b"\x00\xff\x11\x13\xaa")
        _, events, _ = load_session(self.path)
        self.assertEqual([e["hex"] for e in events if e["kind"] == "tx"], ["00ff11", "13aa"])
        self.assertEqual([e["kind"] for e in events if e["kind"].startswith("tx")],
                         ["tx-attempt", "tx", "tx-attempt", "tx"])

    def test_operator_annotations_stop_capture(self):
        annotations = queue.Queue()
        annotations.put("button one")
        annotations.put(":stop")
        result = draco.run_capture(self.settings, self.path, 1, annotations=annotations)
        self.assertEqual(result["status"], "stopped")
        events = load_session(self.path)[1]
        self.assertEqual([e["text"] for e in events if e["kind"] == "annotation"],
                         ["button one", ":stop"])


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "recipe.json"
        self.recipe = {"schema_version": 1, "name": "synthetic", "persistent": False,
                       "source": "original fixture", "rationale": "test", "recovery": "close",
                       "steps": [{"kind": "tx", "at_ms": 0, "hex": "00ff"}]}

    def save(self):
        self.path.write_text(json.dumps(self.recipe))

    def test_preview_does_not_open_or_create_session(self):
        self.save()
        out = Path(self.temp.name) / "not-created"
        with patch("tools.draco.make_port", side_effect=AssertionError("opened")), contextlib.redirect_stdout(io.StringIO()):
            result = draco.main(["probe", "--port", "invalid", "--recipe", str(self.path), "--output", str(out)])
        self.assertEqual(result, 0)
        self.assertFalse(out.exists())

    def test_persistent_and_unattributed_recipes_rejected(self):
        for key, value in (("persistent", True), ("source", "")):
            with self.subTest(key=key):
                old = self.recipe[key]
                self.recipe[key] = value
                self.save()
                with self.assertRaises(ValueError):
                    draco.read_recipe(self.path, 1)
                self.recipe[key] = old

    def test_invalid_schedule_and_payload_rejected(self):
        for steps in ([{"kind": "tx", "at_ms": -1, "hex": "00"}],
                      [{"kind": "tx", "at_ms": float("nan"), "hex": "00"}],
                      [{"kind": "tx", "at_ms": 1000, "hex": "00"}],
                      [{"kind": "tx", "at_ms": 0, "hex": "zz"}],
                      [{"kind": "lines", "at_ms": 0, "dtr": 1, "rts": False}]):
            self.recipe["steps"] = steps
            self.save()
            with self.assertRaises(ValueError):
                draco.read_recipe(self.path, 1)

    def test_nonobject_recipe_and_steps_rejected(self):
        for value in ([], {**self.recipe, "steps": [None]}):
            self.path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                draco.read_recipe(self.path, 1)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.root = self.repo / ".artifacts"
        self.root.mkdir()
        self.patches = [patch.object(artifacts, "REPO", self.repo), patch.object(artifacts, "ROOT", self.root)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_ingest_inventory_and_member_hashes(self):
        source = self.repo / "synthetic.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("original-fixture.com", b"\x90\xc3")
        report = self.repo / "docs/research/acquisitions/fixture.md"
        result = artifacts.acquire(source, "fixture.zip", "zip", local=True, report=report)
        self.assertEqual(result["status"], "acquired")
        self.assertEqual(result["artifact"]["members"][0]["sha256"], hashlib.sha256(b"\x90\xc3").hexdigest())
        self.assertNotIn("original-fixture.com", report.read_text())
        metadata = validate_docs.frontmatter(report.read_text())
        self.assertEqual(metadata["status"], "observed")
        self.assertEqual(set(metadata), {"title", "created", "status"})
        published = json.loads(report.read_text().split("```json\n")[1].split("```")[0])
        self.assertEqual(published["received"], result["received"])
        self.assertNotIn("members", published["artifact"])

    def test_reject_html_as_archive_and_record_failure(self):
        source = self.repo / "response.html"
        source.write_text("<!doctype html><html>not an archive</html>")
        result = artifacts.acquire(source, "fixture.zip", "zip", local=True)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["received"]["format"], "html")
        self.assertFalse((self.root / "downloads/fixture.zip").exists())
        self.assertTrue((self.root / "receipts" / (result["id"] + ".json")).exists())

    def test_network_failure_is_a_receipt_not_a_fake_checksum(self):
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            result = artifacts.acquire("https://example.invalid/tablet.zip", "tablet.zip", "zip")
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("artifact", result)
        self.assertNotIn("received", result)

    def test_path_traversal_and_symlinks_rejected_before_extraction(self):
        source = self.root / "evil.zip"
        for member in ("../escape", "C:\\escape", "/absolute"):
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(member, b"x")
            with self.assertRaises(ValueError):
                artifacts.extract(source)
        with zipfile.ZipFile(source, "w") as archive:
            item = zipfile.ZipInfo("link")
            item.create_system = 3
            item.external_attr = 0o120777 << 16
            archive.writestr(item, "target")
        with self.assertRaises(ValueError):
            artifacts.extract(source)
        self.assertFalse((self.root / "extracted/evil").exists())

    def test_extraction_stays_ignored_and_never_executable(self):
        source = self.root / "fixture.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("dir/demo.com", b"\x90\xc3")
        artifacts.extract(source)
        target = self.root / "extracted/fixture/dir/demo.com"
        self.assertEqual(target.read_bytes(), b"\x90\xc3")
        self.assertEqual(target.stat().st_mode & 0o111, 0)

    def test_reject_output_outside_artifact_tree(self):
        with self.assertRaises(ValueError):
            artifacts.inside(self.repo / "vendor.exe")
        with self.assertRaises(ValueError):
            artifacts.filename("../vendor.exe")

    def test_identify_mz_ne_pe_and_refuse_raw_exe_disassembly(self):
        path = self.root / "test.exe"
        data = bytearray(128)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3c, 64)
        for signature, expected in ((b"NE\0\0", "ne"), (b"PE\0\0", "pe"), (b"\0" * 4, "mz")):
            data[64:68] = signature
            path.write_bytes(data)
            self.assertEqual(artifacts.identify(path), expected)
        with self.assertRaises(ValueError):
            artifacts.disassemble(path)


class DocumentationTests(unittest.TestCase):
    def test_optional_metadata_and_third_party_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md"):
                (root / name).write_text("# Project\n")
            doc = root / "docs/reference.md"
            doc.write_text("# Reference\nSource: Summagraphics; all rights reserved.\n")
            self.assertEqual(validate_docs.validate(root), (4, []))
            doc.write_text('---\ntitle: "Observation"\ncreated: 2026-10-22\nstatus: observed\n---\n')
            self.assertEqual(validate_docs.validate(root), (4, []))
            doc.write_text("[Missing](missing.md)\n")
            self.assertIn("broken local link", validate_docs.validate(root)[1][0])

    def test_invalid_metadata_is_rejected(self):
        valid = '---\ntitle: "Observation"\ncreated: 2026-10-22\nstatus: observed\n---\n'
        for text in (valid.replace("2026-10-22", "2026-13-22"),
                     valid.replace("observed", "invented"),
                     valid.replace("status: observed", "updated: 2026-10-21\nstatus: observed"),
                     valid.replace('title: "Observation"\n', ""),
                     valid.replace('"Observation"', "[]")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_docs.frontmatter(text)


if __name__ == "__main__":
    unittest.main()
