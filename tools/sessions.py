# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Versioned, lossless host-receipt evidence with offline integrity validation."""
from __future__ import annotations

import hashlib
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SessionWriter:
    def __init__(self, directory, settings, note=""):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic_ns()
        self.raw = (self.directory / "rx.bin").open("xb")
        self.events = (self.directory / "events.jsonl").open("x", encoding="utf-8")
        self.count = 0
        self.seq = 0
        self.manifest = {"schema_version": 1, "tool_version": VERSION,
                         "session_id": str(uuid.uuid4()), "started_utc": utc_now(),
                         "status": "recording", "settings": settings,
                         "host": {"system": platform.system(), "release": platform.release(),
                                  "python": platform.python_version()},
                         "note": note, "timestamp_scope": "host-receipt-chunks"}
        self._save_manifest()
        if note:
            self.event("annotation", text=note)

    def _save_manifest(self):
        temp = self.directory / "session.json.tmp"
        temp.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.directory / "session.json")

    def event(self, kind, **fields):
        event = {"seq": self.seq, "t_ns": time.monotonic_ns() - self.started,
                 "utc": utc_now(), "kind": kind, **fields}
        self.seq += 1
        self.events.write(json.dumps(event, sort_keys=True) + "\n")
        self.events.flush()
        return event

    def receive(self, data):
        if not data:
            return
        offset = self.count
        self.raw.write(data)
        self.raw.flush()
        self.count += len(data)
        self.event("rx", offset=offset, length=len(data), hex=data.hex())

    def finish(self, status, **fields):
        if self.events.closed:
            return
        self.event("end", status=status, **fields)
        self.raw.close()
        self.events.close()
        self.manifest.update(status=status, ended_utc=utc_now(), rx_bytes=self.count,
                             event_count=self.seq, **fields)
        self.manifest["files"] = {name: {"sha256": sha256_file(self.directory / name),
                                         "bytes": (self.directory / name).stat().st_size}
                                  for name in ("rx.bin", "events.jsonl")}
        self._save_manifest()


def load_session(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "session.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported capture schema version")
    if manifest.get("status") == "recording" or not manifest.get("files"):
        raise ValueError("Incomplete recording: preserve it but do not claim verified integrity")
    for name in ("rx.bin", "events.jsonl"):
        info = manifest["files"][name]
        path = directory / name
        if path.stat().st_size != info["bytes"] or sha256_file(path) != info["sha256"]:
            raise ValueError(f"Capture integrity mismatch: {name}")
    raw = (directory / "rx.bin").read_bytes()
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text(
        encoding="utf-8").splitlines()]
    offset, last_time = 0, -1
    if len(events) != manifest["event_count"]:
        raise ValueError("Event count mismatch")
    for seq, event in enumerate(events):
        if event["seq"] != seq or event["t_ns"] < last_time:
            raise ValueError("Invalid event ordering")
        last_time = event["t_ns"]
        if event["kind"] == "rx":
            data = bytes.fromhex(event["hex"])
            if (event["offset"] != offset or event["length"] != len(data)
                    or raw[offset:offset + len(data)] != data):
                raise ValueError("Receive events do not match raw stream")
            offset += len(data)
    if offset != len(raw) or manifest["rx_bytes"] != len(raw):
        raise ValueError("Raw byte count mismatch")
    if not events or events[-1].get("kind") != "end":
        raise ValueError("Missing terminal event")
    return manifest, events, raw
