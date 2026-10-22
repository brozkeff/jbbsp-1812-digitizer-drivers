#!/usr/bin/env python3
# Copyright (c) 2026 Martin brozkeff Malec
# SPDX-License-Identifier: EUPL-1.2
# Licensed under EUPL v. 1.2 only.
"""Validate this project's simple YAML subset, metadata, and local Markdown links."""
from __future__ import annotations

import ast
import datetime
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = Path(__file__).resolve().parent.parent
REQUIRED = {"title", "created", "status"}
STATUSES = {"active", "draft", "observed", "proposed", "template", "superseded"}


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Missing opening YAML frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing closing frontmatter delimiter") from exc
    values = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z_]+): (.+)", line)
        if not match or match[1] in values:
            raise ValueError("Use unique single-line YAML fields in the supported subset")
        key, value = match.groups()
        if value.startswith(("'", '"')):
            value = ast.literal_eval(value)
        elif value.startswith("["):
            if not re.fullmatch(r"\[[a-zA-Z0-9_-]+(?:, [a-zA-Z0-9_-]+)*\]", value):
                raise ValueError("tags must be a nonempty inline YAML list of plain tokens")
            value = value[1:-1].split(", ")
        elif not re.fullmatch(r"[a-zA-Z0-9_.-]+", value):
            raise ValueError("Quote descriptive YAML scalar values")
        values[key] = value
    missing = REQUIRED - values.keys()
    if missing:
        raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
    created = datetime.date.fromisoformat(values["created"])
    updated = datetime.date.fromisoformat(values.get("updated", values["created"]))
    if updated < created:
        raise ValueError("updated precedes created")
    if values["status"] not in STATUSES:
        raise ValueError("Invalid status")
    if "tags" in values and (not isinstance(values["tags"], list) or not values["tags"]):
        raise ValueError("tags must be a nonempty list")
    if not isinstance(values["title"], str) or not values["title"]:
        raise ValueError("title must be a nonempty string")
    return values


def validate(root=REPO):
    root = Path(root)
    errors = []
    paths = sorted((root / "docs").rglob("*.md"))
    paths += [root / name for name in ("README.md", "CONTRIBUTING.md", "AGENTS.md")]
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
            if text.splitlines()[:1] == ["---"]:
                frontmatter(text)
            # Ignore examples inside fenced code, which can contain literal link syntax.
            prose = re.sub(r"```.*?```", "", text, flags=re.S)
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
                target = target.strip("<>")
                url = urlsplit(target)
                if url.scheme or target.startswith("#"):
                    continue
                local = path.parent / unquote(url.path)
                if not local.exists():
                    errors.append(f"{path.relative_to(root)}: broken local link {target}")
        except (OSError, ValueError, SyntaxError, TypeError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    return len(paths), errors


def main():
    count, errors = validate()
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Checked {count} Markdown documents; {len(errors)} errors.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
