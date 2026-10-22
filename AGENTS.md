# Agent instructions

Follow [rights and attribution](README.md#rights-and-attribution) and
[contribution rules](CONTRIBUTING.md). Development uses GPT-6.1-Sol; owner: @brozkeff.

- Run Python through `uv run`, Python 3.15 `.venv`. Track dependencies and `uv.lock`.
- Follow Ponytail: minimal code, concise docs, one home for each fact.
- Record findings in `docs/`, separating reports, source claims, observations, and
  hypotheses. Frontmatter belongs on dated evidence/acquisition reports only.
- Keep copyright/licensing for documentation in README; retain source-file headers
  and unmodified LICENSE. The attributed MM-1812 reference is excluded from EUPL.
- Downloads, extracted material, OCR, and disassembler/decompiler output stay in
  ignored `.artifacts/`. Commit only original tools, provenance, concise attributed
  findings, behavioral specifications, and independently generated fixtures.
- Read [the clean-room process](docs/research/clean-room.md) before vendor-code
  inspection or production decoding. Never copy/translate vendor code into drivers.
- Commit coherent pieces as completed; Git operations are authorized. Do not push.
  If `.git` is read-only, preserve commits in `.artifacts/progress.git`, export
  `.artifacts/progress.bundle`, and report the limitation.
- Never change groups, BIOS, udev rules, or services automatically. Hardware opens
  and transmissions must be explicit in the research CLI.
- Research stays outside `docs/decisions/`; ADRs record implementation choices.
  Never claim hardware success from PTYs.
