# Contributing

Follow [project rights and attribution](README.md#rights-and-attribution).
Keep code minimal, docs useful, and commits small. Do not push unless requested.
Use `uv run` for Python 3.15 in `.venv`; dependency changes
include `pyproject.toml` and `uv.lock`. Preserve license headers on original code.

Keep findings in `docs/`, with sources and explicit evidence labels:
**user report**, **source claim**, **observation**, **hypothesis**, or **unknown**.
Use frontmatter only on dated reports: `title`, `created` (ISO date), and `status`;
optional `updated` must not precede `created`. Status is `active`, `draft`,
`observed`, `proposed`, `template`, or `superseded`. Ordinary guides need none.
Copyright and documentation licensing live in the README, not repeated page headers.

Downloads, extracted files, OCR, and vendor code/disassembly stay in `.artifacts/`.
Publish concise attributed factual findings with provenance; the MM reference is
explicitly outside the EUPL grant. Do not publish copied vendor code or complete
manual transcriptions. Review staged filenames/content; never force-add artifacts
or working `sessions/`. Public hardware traces need review and provenance.

Read the [clean-room boundary](docs/research/clean-room.md) before vendor-code
inspection or production decoder work. Keep research and implementation contexts
separate. Reserve `docs/decisions/` for actual implementation ADRs containing
context, decision, alternatives, consequences, and validation.

For relevant changes run:

```sh
uv run python -m unittest discover -s tests -v
uv run python tools/validate_docs.py
```

Hardware reports use the [bring-up report fields](docs/experiments/bringup.md#report-fields).
Synthetic PTYs establish tooling behavior, never tablet success.
