#!/usr/bin/env python3
# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Acquire and inspect vendor artifacts locally; never execute acquired code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / ".artifacts"
LIMIT = 32 * 1024 * 1024
EXPANDED_LIMIT = 128 * 1024 * 1024


def now():
    return datetime.now(timezone.utc).isoformat()


def inside(path):
    path = Path(path).resolve()
    root = ROOT.resolve()
    if not root.is_relative_to(REPO) or not path.is_relative_to(root):
        raise ValueError("Vendor material and analysis must remain inside repository .artifacts/")
    return path


def filename(name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", name):
        raise ValueError("Use a simple filename of at most 128 characters")
    return name


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_bounded(source, target):
    count = 0
    while chunk := source.read(65536):
        count += len(chunk)
        if count > LIMIT:
            raise ValueError("Artifact exceeds the 32 MiB acquisition limit")
        target.write(chunk)
    return count


def identify(path):
    path = Path(path)
    with path.open("rb") as stream:
        head = stream.read(512)
        stripped = head.lstrip().lower()
        if stripped.startswith((b"<!doctype html", b"<html")):
            return "html"
        if head.startswith(b"%PDF-"):
            return "pdf"
        if zipfile.is_zipfile(path):
            return "zip"
        if head.startswith(b"MZ"):
            if len(head) >= 64:
                offset = struct.unpack_from("<I", head, 0x3c)[0]
                if 0x40 <= offset <= path.stat().st_size - 2:
                    stream.seek(offset)
                    signature = stream.read(4)
                    if signature.startswith(b"NE"):
                        return "ne"
                    if signature == b"PE\0\0":
                        return "pe"
            return "mz"
        if path.suffix.lower() == ".com":
            return "com-candidate"
        return "unknown"


def zip_inventory(path):
    result = []
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 1024 or sum(m.file_size for m in members) > EXPANDED_LIMIT:
            raise ValueError("Archive exceeds member-count or expanded-size limit")
        for member in members:
            h = hashlib.sha256()
            if not member.is_dir():
                if member.file_size > LIMIT:
                    raise ValueError("Archive member exceeds size limit")
                with archive.open(member) as stream:
                    for chunk in iter(lambda: stream.read(65536), b""):
                        h.update(chunk)
            result.append({"name": member.filename, "bytes": member.file_size,
                           "compressed_bytes": member.compress_size,
                           "sha256": h.hexdigest() if not member.is_dir() else None,
                           "claimed_dos_timestamp": list(member.date_time)})
    return result


def inspect_file(path):
    path = inside(path)
    info = {"path": str(path.relative_to(REPO)), "size": path.stat().st_size,
            "sha256": digest(path), "format": identify(path), "inspected_utc": now()}
    if info["format"] == "zip":
        info["members"] = zip_inventory(path)
    return info


def save_receipt(receipt, report=None):
    folder = inside(ROOT / "receipts")
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / (receipt["id"] + ".json")
    dest.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if report:
        report = Path(report).resolve()
        allowed = (REPO / "docs/research/acquisitions").resolve()
        if not report.is_relative_to(allowed) or report.suffix != ".md":
            raise ValueError("Public receipts must be Markdown under docs/research/acquisitions/")
        if report.exists():
            raise FileExistsError(f"Refusing to overwrite report: {report}")
        report.parent.mkdir(parents=True, exist_ok=True)
        day = receipt["started_utc"][:10]
        artifact = receipt.get("artifact", {})
        # JSON quoting is a valid YAML scalar; content cannot create new YAML fields.
        title = json.dumps("Acquisition " + receipt["id"])
        lines = ["---", f"title: {title}",
                 f"created: {day}", "status: observed", "---", "",
                 "# Artifact acquisition", "",
                 "```json", json.dumps(receipt, indent=2), "```", "",
                 "Hashes identify acquired bytes, not redistribution rights. Vendor material stays ignored.", ""]
        # Avoid publishing vendor names/content inventories or disassembly accidentally.
        public = dict(receipt)
        public["artifact"] = {k: v for k, v in artifact.items() if k != "members"}
        lines[lines.index(json.dumps(receipt, indent=2))] = json.dumps(public, indent=2)
        report.write_text("\n".join(lines), encoding="utf-8")
    return dest


def acquire(source, name, kind, *, local=False, report=None):
    name = filename(name)
    receipt = {"id": str(uuid.uuid4()), "tool_version": "0.1.0", "started_utc": now(),
               "method": "local-ingest" if local else "https-fetch", "source": str(source),
               "expected_kind": kind, "status": "failed"}
    folder = inside(ROOT / "downloads")
    folder.mkdir(parents=True, exist_ok=True)
    target = inside(folder / name)
    partial = inside(folder / (receipt["id"] + ".partial"))
    try:
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite {target}")
        if local:
            with Path(source).open("rb") as incoming, partial.open("xb") as out:
                copy_bounded(incoming, out)
        else:
            url = urllib.parse.urlsplit(source)
            if url.scheme != "https" or url.username or url.password:
                raise ValueError("Use a credential-free HTTPS direct artifact URL")
            request = urllib.request.Request(source, headers={"User-Agent": "JBBSP-1812-research/0.1"})
            with urllib.request.urlopen(request, timeout=20) as response, partial.open("xb") as out:
                final = response.geturl()
                if urllib.parse.urlsplit(final).scheme != "https":
                    raise ValueError("Refusing an HTTPS-to-HTTP redirect")
                receipt.update(final_url=final, http_status=response.status,
                               content_type=response.headers.get("Content-Type"))
                copy_bounded(response, out)
        actual = identify(partial)
        # Extensionless partials cannot be identified as COM until the final name.
        if actual == "unknown" and target.suffix.lower() == ".com":
            actual = "com-candidate"
        receipt["received"] = {"bytes": partial.stat().st_size, "sha256": digest(partial),
                               "format": actual}
        expected = {"zip": {"zip"}, "pdf": {"pdf"},
                    "executable": {"mz", "ne", "pe", "com-candidate"},
                    "any": {"zip", "pdf", "mz", "ne", "pe", "com-candidate", "unknown"}}[kind]
        if actual not in expected or partial.stat().st_size == 0:
            raise ValueError(f"Expected {kind}; received {actual} (not a verified artifact)")
        if actual == "zip":
            zip_inventory(partial)  # Validate CRCs and size constraints before accepting.
        partial.rename(target)
        receipt.update(status="acquired", artifact=inspect_file(target))
    except Exception as exc:
        receipt.update(error_type=type(exc).__name__, error=str(exc))
        if partial.exists():
            rejected = inside(ROOT / "rejected")
            rejected.mkdir(parents=True, exist_ok=True)
            partial.rename(rejected / (receipt["id"] + ".bin"))
    receipt["finished_utc"] = now()
    save_receipt(receipt, report)
    return receipt


def extract(path):
    path = inside(path)
    info = inspect_file(path)
    if info["format"] != "zip":
        raise ValueError("Only ZIP extraction is supported")
    target = inside(ROOT / "extracted" / filename(path.stem))
    # Validate every path and type before writing any members.
    with zipfile.ZipFile(path) as archive:
        destinations = set()
        for item in archive.infolist():
            pure = PurePosixPath(item.filename.replace("\\", "/"))
            if pure.is_absolute() or ".." in pure.parts or ":" in str(pure):
                raise ValueError("Unsafe archive member path")
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) and not
                                      (stat.S_ISREG(mode) or stat.S_ISDIR(mode))):
                raise ValueError("Archive contains a non-regular member")
            dest = inside(target.joinpath(*pure.parts))
            if dest in destinations:
                raise ValueError("Duplicate archive member path")
            destinations.add(dest)
        target.mkdir(parents=True, exist_ok=False)
        for item in archive.infolist():
            dest = inside(target.joinpath(*PurePosixPath(item.filename.replace("\\", "/")).parts))
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, dest.open("xb") as out:
                    copy_bounded(source, out)
                os.chmod(dest, 0o600)  # Acquired binaries are never made executable.
    (target / "_extraction.json").write_text(json.dumps(
        {"source_sha256": info["sha256"], "time_utc": now(), "members": info["members"]},
        indent=2) + "\n", encoding="utf-8")
    return {"directory": str(target.relative_to(REPO)), "source_sha256": info["sha256"]}


def disassemble(path):
    path = inside(path)
    if identify(path) != "com-candidate":
        raise ValueError("Raw disassembly supports .com candidates only; use a proper MZ/NE/PE loader")
    tool = shutil.which("objdump")
    if not tool:
        raise ValueError("GNU objdump is required")
    folder = inside(ROOT / "analysis" / digest(path))
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / "objdump-i8086.txt"
    command = [tool, "-D", "-b", "binary", "-m", "i8086", "--adjust-vma=0x100", str(path)]
    with output.open("w", encoding="utf-8") as out:
        result = subprocess.run(command, stdout=out, stderr=subprocess.PIPE, text=True, timeout=30)
    version = subprocess.run([tool, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    record = {"input_sha256": digest(path), "time_utc": now(), "command": command,
              "tool_version": version, "returncode": result.returncode,
              "stderr": result.stderr, "output_sha256": digest(output)}
    (folder / "analysis.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if result.returncode:
        raise ValueError(f"objdump failed; see ignored analysis directory: {folder}")
    return {"analysis_directory": str(folder.relative_to(REPO)), "input_sha256": record["input_sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "ingest"):
        command = sub.add_parser(name)
        command.add_argument("source")
        command.add_argument("--name", required=True)
        command.add_argument("--kind", choices=("zip", "pdf", "executable", "any"), required=True)
        command.add_argument("--report", help="New Markdown provenance report under docs/research/acquisitions/")
    for name in ("inspect", "extract", "disassemble"):
        command = sub.add_parser(name)
        command.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in ("fetch", "ingest"):
            result = acquire(args.source, args.name, args.kind,
                             local=args.command == "ingest", report=args.report)
            # Never dump vendor strings, member inventories or disassembly to stdout.
            print(json.dumps({k: v for k, v in result.items() if k != "artifact"}, indent=2))
            return 0 if result["status"] == "acquired" else 1
        if args.command == "inspect":
            result = inspect_file(args.path)
            folder = inside(ROOT / "analysis" / result["sha256"])
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({k: v for k, v in result.items() if k != "members"}, indent=2))
        else:
            print(json.dumps(extract(args.path) if args.command == "extract"
                             else disassemble(args.path), indent=2))
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print(f"artifacts: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
