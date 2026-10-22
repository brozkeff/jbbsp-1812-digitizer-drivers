#!/usr/bin/env python3
# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Raw serial evidence tools. No Qtronix decoder or implicit initialization."""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import importlib.util
import json
import math
import os
import platform
import queue
import statistics
import sys
import threading
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.serial_backend import Settings, make_port
from tools.sessions import VERSION, SessionWriter, load_session


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def doctor():
    def read(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return None

    nodes = []
    for pattern in ("/dev/ttyS*", "/dev/ttyUSB*", "/dev/ttyACM*"):
        for path in sorted(glob.glob(pattern)):
            st = Path(path).stat()
            nodes.append({"path": path, "mode": oct(st.st_mode & 0o777),
                          "uid": st.st_uid, "gid": st.st_gid,
                          "readable": os.access(path, os.R_OK),
                          "writable": os.access(path, os.W_OK)})
    uarts = []
    for path in sorted(Path("/sys/class/tty").glob("ttyS*")):
        entry = {"name": path.name, "device": str((path / "device").resolve())}
        for key in ("type", "port", "irq", "uartclk"):
            entry[key] = read(path / key)
        uarts.append(entry)
    groups = {}
    if os.name == "posix":
        import grp
        import pwd
        account = pwd.getpwuid(os.getuid())
        groups["effective_gids"] = os.getgroups()
        groups["account_name"] = account.pw_name
        groups["account_group_names"] = [g.gr_name for g in grp.getgrall()
                                          if account.pw_name in g.gr_mem
                                          or g.gr_gid == account.pw_gid]
    return {"tool_version": VERSION, "platform": platform.platform(),
            "dmi": {key: read(Path("/sys/class/dmi/id") / key)
                    for key in ("sys_vendor", "product_name", "board_name")},
            "python": platform.python_version(), "pyserial_available":
            importlib.util.find_spec("serial") is not None,
            "groups": groups, "nodes": nodes, "uarts": uarts,
            "notes": ["No serial ports were opened.",
                      "Missing nodes can indicate a sandbox device namespace.",
                      "Use fuser/systemctl on the host to investigate competing users."]}


def read_recipe(path, duration):
    data = Path(path).read_bytes()
    recipe = json.loads(data)
    if not isinstance(recipe, dict):
        raise ValueError("Recipe must be a JSON object")
    if recipe.get("schema_version") != 1:
        raise ValueError("Recipe requires schema_version 1")
    if recipe.get("persistent", True) is not False:
        raise ValueError("Only explicitly nonpersistent recipes are supported")
    for key in ("name", "source", "rationale", "recovery"):
        if not isinstance(recipe.get(key), str) or not recipe[key].strip():
            raise ValueError(f"Recipe requires {key}")
    steps = recipe.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > 256:
        raise ValueError("Recipe needs 1..256 steps")
    last = -1
    total = 0
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("Recipe steps must be JSON objects")
        at = step.get("at_ms")
        if type(at) not in (int, float) or not math.isfinite(at) or at < last:
            raise ValueError("Recipe at_ms must be finite, nonnegative and ordered")
        if at < 0 or at >= duration * 1000:
            raise ValueError("Recipe step is outside capture duration")
        last = at
        kind = step.get("kind")
        if kind == "tx":
            payload = bytes.fromhex(step["hex"])
            if not payload or len(payload) > 4096:
                raise ValueError("TX step must contain 1..4096 bytes")
            total += len(payload)
        elif kind == "lines":
            if any(type(step.get(key)) is not bool for key in ("dtr", "rts")):
                raise ValueError("Line step requires boolean dtr and rts")
        elif kind == "annotation":
            if not isinstance(step.get("text"), str) or not step["text"].strip():
                raise ValueError("Annotation step requires text")
        else:
            raise ValueError(f"Unsupported recipe step: {kind}")
    if total > 65536:
        raise ValueError("Recipe exceeds 64 KiB TX limit")
    return recipe, hashlib.sha256(data).hexdigest()


def run_capture(settings, directory, duration, *, note="", recipe=None,
                recipe_hash=None, annotations=None, port_factory=make_port):
    settings.validate()
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be positive and finite")
    # Create evidence before opening the device: failed opens are useful evidence.
    writer = SessionWriter(directory, settings.to_dict(), note)
    port = None
    status = "error"
    outcome = {}
    error = None
    if recipe:
        writer.event("recipe", name=recipe["name"], source=recipe["source"],
                     sha256=recipe_hash, recipe=recipe)
    try:
        port = port_factory(settings)
        writer.event("open-request", settings=settings.to_dict(),
                     electrical_caveat="Opening may itself change RTS/DTR")
        port.open()
        writer.manifest["backend"] = port.name
        writer.event("opened", backend=port.name, line_support=port.line_support)
        writer.event("modem-status", **port.modem_status())
        started = time.monotonic()
        steps = recipe["steps"] if recipe else []
        index = 0
        stop = False
        while not stop:
            elapsed = time.monotonic() - started
            if elapsed >= duration:
                break
            if annotations is not None:
                while True:
                    try:
                        text = annotations.get_nowait()
                    except queue.Empty:
                        break
                    writer.event("annotation", text=text)
                    if text == ":stop":
                        stop = True
            if stop:
                break
            while index < len(steps) and elapsed * 1000 >= steps[index]["at_ms"]:
                step = steps[index]
                if step["kind"] == "tx":
                    payload = bytes.fromhex(step["hex"])
                    # Intent is written first so partial/failed TX is never hidden.
                    writer.event("tx-attempt", hex=payload.hex(), length=len(payload))
                    count = port.write(payload)
                    writer.event("tx", hex=payload.hex(), length=count)
                elif step["kind"] == "lines":
                    writer.event("lines-attempt", dtr=step["dtr"], rts=step["rts"])
                    support = port.set_lines(step["dtr"], step["rts"])
                    writer.event("lines", dtr=step["dtr"], rts=step["rts"], support=support)
                else:
                    writer.event("annotation", text=step["text"])
                index += 1
                elapsed = time.monotonic() - started
            timeout = min(0.1, max(0, duration - elapsed))
            if index < len(steps):
                timeout = min(timeout, max(0, steps[index]["at_ms"] / 1000 - elapsed))
            writer.receive(port.read(timeout))
        outcome["recipe_steps_completed"] = index
        outcome["recipe_steps_total"] = len(steps)
        status = "stopped" if stop else "complete"
    except KeyboardInterrupt:
        status = "interrupted"
    except Exception as exc:
        error = exc
        writer.event("error", error_type=type(exc).__name__, message=str(exc))
        outcome["error"] = str(exc)
    finally:
        if port is not None:
            try:
                cleanup = port.close()
                writer.event("closed", cleanup_errors=cleanup,
                             original_lines_restored=port.original_lines_restored)
                if cleanup:
                    status = "error"
                    outcome["cleanup_errors"] = cleanup
            except Exception as exc:
                writer.event("cleanup-error", message=str(exc))
                status = "error"
                error = error or exc
        writer.finish(status, **outcome)
    result = {"session": str(directory), "session_id": writer.manifest["session_id"],
              "status": status, "rx_bytes": writer.count, **outcome}
    if error:
        result["hint"] = ("Check host device visibility, access rights and competing users. "
                          "A missing sandbox node is not a disabled UART.")
    return result


def analyze(directory):
    manifest, events, raw = load_session(directory)
    rx = [event for event in events if event["kind"] == "rx"]
    gaps = [(b["t_ns"] - a["t_ns"]) / 1e6 for a, b in zip(rx, rx[1:])]
    counts = collections.Counter(raw)
    return {"session_id": manifest["session_id"], "status": manifest["status"],
            "rx_bytes": len(raw), "rx_chunks": len(rx),
            "high_bit_fraction": sum(count for value, count in counts.items() if value & 128)
            / len(raw) if raw else None,
            "byte_histogram": {f"{key:02x}": value for key, value in sorted(counts.items())},
            "chunk_lengths": dict(collections.Counter(e["length"] for e in rx)),
            "host_chunk_gap_ms": {"median": statistics.median(gaps) if gaps else None,
                                  "max": max(gaps) if gaps else None},
            "annotations": [e for e in events if e["kind"] == "annotation"],
            "interpretation": "Chunk boundaries/timing are not packet boundaries/wire timing; no protocol identified."}


def replay(directory, stream, realtime=False):
    _, events, _ = load_session(directory)
    previous = 0
    for event in events:
        if event["kind"] != "rx":
            continue
        if realtime:
            time.sleep((event["t_ns"] - previous) / 1e9)
        stream.write(bytes.fromhex(event["hex"]))
        stream.flush()
        previous = event["t_ns"]


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Read host/sysfs inventory; never opens serial ports")
    for name in ("capture", "probe"):
        command = sub.add_parser(name)
        command.add_argument("--port", required=True)
        command.add_argument("--baud", type=int, default=9600)
        command.add_argument("--bits", type=int, choices=(7, 8), default=8)
        command.add_argument("--parity", choices=("N", "E", "O"), default="N")
        command.add_argument("--stopbits", type=int, choices=(1, 2), default=1)
        command.add_argument("--dtr", choices=("on", "off"), default="off")
        command.add_argument("--rts", choices=("on", "off"), default="off")
        command.add_argument("--backend", choices=("auto", "posix", "pyserial"), default="auto")
        command.add_argument("--duration", type=positive, default=30)
        command.add_argument("--output", type=Path, required=True, help="New session directory")
        command.add_argument("--note", default="")
        command.add_argument("--annotate-stdin", action="store_true",
                             help="Record typed lines as annotations; :stop ends capture")
        if name == "probe":
            command.add_argument("--recipe", type=Path, required=True)
            command.add_argument("--execute", action="store_true",
                                 help="Open the port and execute the reviewed volatile recipe")
    command = sub.add_parser("analyze")
    command.add_argument("session", type=Path)
    command = sub.add_parser("replay", help="Offline raw receive bytes to stdout")
    command.add_argument("session", type=Path)
    command.add_argument("--realtime", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(), indent=2))
        elif args.command == "analyze":
            print(json.dumps(analyze(args.session), indent=2))
        elif args.command == "replay":
            replay(args.session, sys.stdout.buffer, args.realtime)
        else:
            recipe, digest = (read_recipe(args.recipe, args.duration)
                              if args.command == "probe" else (None, None))
            if args.command == "probe" and not args.execute:
                print(json.dumps({"action": "preview-only", "recipe_sha256": digest,
                                  "recipe": recipe}, indent=2))
                return 0
            annotations = None
            if args.annotate_stdin:
                annotations = queue.Queue()
                def read_annotations():
                    for line in sys.stdin:
                        annotations.put(line.rstrip("\r\n"))
                threading.Thread(target=read_annotations, daemon=True).start()
            settings = Settings(args.port, args.baud, args.bits, args.parity,
                                args.stopbits, args.dtr == "on", args.rts == "on", args.backend)
            result = run_capture(settings, args.output, args.duration, note=args.note,
                                 recipe=recipe, recipe_hash=digest, annotations=annotations)
            print(json.dumps(result, indent=2))
            return 130 if result["status"] == "interrupted" else (
                0 if result["status"] in ("complete", "stopped") else 1)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"draco: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
