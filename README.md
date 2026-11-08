# Qtronix Draco 18 research

Independent research and clean-room driver work for the RS-232 digitizer marked
QTronix Draco 18, **FCC ID JBBSP-1812**.

Linux and CADCraft are the first targets.

**Current result:** physical captures on ttyS0 at 9600 8N1 received repeatable
five-byte groups during puck and pen trials. Coordinate interpretation remains
tentative; precise calibration is unverified. See the
[hardware findings](docs/observations/2026-10-22-validation.md) and
[next-session plan](docs/integration/roadmap.md#next-session).

| Need | Read |
|---|---|
| OpenAlt 2026 lightning talk and live demo | [Slides and laptop setup](docs/openalt-2026/README.md) |
| Evidence and completed checks | [Observation history](docs/observations/2026-10-22-validation.md) |
| Equipment and unknowns | [Hardware inventory](docs/hardware/tablet.md) |
| First communication test | [Bring-up guide](docs/experiments/bringup.md) |
| CLI and recorded data | [Capture format](docs/protocol/capture-format.md) |
| Manuals and driver recovery | [Sources](docs/research/sources.md) |
| Abbreviated manufacturer manual | [MM 1812 Bit Pad reference](docs/research/mm1812-reference.md) |
| Research/implementation boundary | [Clean-room process](docs/research/clean-room.md) |
| Measurement and later integration | [Calibration](docs/experiments/calibration.md), [roadmap](docs/integration/roadmap.md) |

Use uv-managed **Python 3.15**; dependencies are in `pyproject.toml` and `uv.lock`.
Commands:

```sh
uv sync
uv run python tools/draco.py doctor
uv run python tools/draco.py --help
uv run python -m unittest discover -s tests -v
uv run python tools/validate_docs.py
```

Hardware opens require an explicit port; probe transmission additionally requires
`--execute`. Follow the bring-up guide before using either. Downloads, OCR, vendor
analysis, and working sessions stay ignored. See [contributing](CONTRIBUTING.md).

## Rights and attribution

Copyright (c) 2026 Martin brozkeff Malec. Original project code and documentation
are licensed under **EUPL v. 1.2 only** (`EUPL-1.2`); see [LICENSE](LICENSE).
Source and data files retain their individual notices. Third-party materials and
the attributed MM-1812 reference are excluded from this grant and retain their
source rights. An attribution does not establish permission to redistribute a manual.

Development uses GPT-6.1-Sol.

No affiliation with Qtronix, Smartech, Summagraphics,
GTCO CalComp, Autodesk, HP, or CADCraft is implied.
