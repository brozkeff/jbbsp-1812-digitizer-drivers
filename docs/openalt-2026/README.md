# OpenAlt 2026 lightning talk

**Qtronix Draco 18** · Martin brozkeff Malec · Brno, 8 November 2026 · 10 minutes.

[Open the slides](index.html) · [Project](../../README.md) ·
[Hardware](../hardware/tablet.md) · [Trial evidence](../observations/2026-10-22-validation.md).

## Presentation laptop

On the HP ProBook 6470b, update the `testing` branch and prepare Python while online.
From the repository root:

```sh
git switch testing
git pull --ff-only
uv sync --locked
uv run --offline python docs/openalt-2026/server.py
```

Open <http://127.0.0.1:8765/>. Use **F11** for fullscreen, **PageDown / PageUp**
for slides, or scroll. Tall slides can be scrolled before advancing. Stop the
server with Ctrl-C.

The slides and measured grid work offline, including when `index.html` is opened
as a file. Live controls require the server. Documentation links open GitHub's
`testing` branch and need a connection. Work Sans and Ubuntu Mono are used when
installed; otherwise system fonts apply. No fonts or scripts are downloaded.

## Live demo

1. Connect the dock and powered digitizer; confirm the serial port.
2. Enter `/dev/ttyS0` (or the confirmed port), then **Start listening**.
3. Move the puck and press a button; show the raw hex and tentative coordinates.
4. **Stop** before switching tools. Power down before exchanging puck and pen.

Receive only: 9600 baud, 8 data bits, no parity, 1 stop bit; flow control off,
DTR/RTS requested off. Opening a port may affect control lines. No device commands
are sent. The display retains only the latest 200 bytes; it does not save a capture.
Use [the research CLI](../protocol/capture-format.md) for recorded sessions.

If the live demo fails, continue with **Measured grid**. Select A–I for the
recorded puck medians and approximate paper positions relative to G. The byte
example on the serial slide is synthetic; the grid medians come from the linked
trial evidence. The coordinate display is exploratory, not a production decoder.
