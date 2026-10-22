# Research CLI and capture format v1

`uv run python tools/draco.py` provides `doctor`, `capture`, `probe`, `replay`,
and `analyze`. It does not decode the tablet or inject desktop input.

## Capture

Explicit port and **new output directory** required. Defaults: 9600 8N1, 30 seconds,
DTR/RTS requested off, all flow control disabled. These are tool defaults.
`--backend auto` selects pySerial; `posix` explicitly chooses the Linux transport
(standard baud constants, 7/8 bits, N/E/O parity, 1/2 stop bits).

POSIX requests exclusive ownership and restores termios/available modem-line state;
pySerial uses POSIX exclusive mode but does not promise prior settings restoration.
Both can affect lines on open/close; unsupported operations are recorded.
[pySerial API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

Use the [bring-up command](../experiments/bringup.md#2-annotated-receive-trial).
`--annotate-stdin` records entered lines; `:stop` finalizes. Exit codes: 0 for normal
completion/operator stop, 130 for finalized Ctrl-C interruption, 1 for access,
transport, or integrity errors. Zero-byte silence is valid evidence.

| File | Contract |
|---|---|
| `session.json` | Schema/tool version, UUID, UTC bounds, requested settings/backend, status, counts, evidence SHA-256 and sizes |
| `rx.bin` | Original receive bytes, in order, with no text/packet conversion |
| `events.jsonl` | Sequenced UTC/elapsed monotonic-nanosecond events: RX offset/length/hex, TX intention/completion, annotations, lifecycle/errors |

Times describe host receipt chunks, not wire bytes. Analyze/replay verify hashes,
sizes, sequence/timing, contiguous offsets, byte counts, and exact RX reconstruction.
Unfinalized `recording` sessions are retained but rejected; finalized error/interrupted
sessions are readable if internally consistent. Hashes are not signatures.

```sh
uv run python tools/draco.py analyze sessions/e02-puck-9600-8n1
uv run python tools/draco.py replay sessions/e02-puck-9600-8n1 > sessions/replayed.bin
```

Replay writes only RX to stdout; it never opens hardware or replays TX. Default is
immediate; `--realtime` approximates chunk spacing. Analyze reports histograms,
high-bit fraction, chunk lengths/gaps, and annotations, not packets or coordinates.

## Probe recipes

Preview/validation opens no hardware; `--execute` enables the experiment. Capture
has no TX option. Recipes require `schema_version: 1`, nonempty `name`, `source`,
`rationale`, `recovery`, `persistent: false`, and ordered `steps`. Each step has
`at_ms` from successful port opening and `kind`: `tx` (`hex`), `lines` (boolean `dtr`
and `rts`), or `annotation` (`text`). All steps must fit the duration. Limits: 256
steps, 4096 bytes/TX, 64 KiB total. Reception continues between steps.

```json
{
  "schema_version": 1,
  "name": "annotation-only-example",
  "source": "docs/protocol/capture-format.md",
  "rationale": "Demonstrate timing without device commands",
  "recovery": "Close the serial port",
  "persistent": false,
  "steps": [{"at_ms": 100, "kind": "annotation", "text": "move puck now"}]
}
```

The recipe and its SHA-256 are recorded. `source` is provenance, not proof of
applicability. TX attempts precede writes in the log; partial/failing writes remain
visible. OS acceptance is not device acknowledgment. There is no automatic settings
sweep, persistent save operation, or verified Qtronix initializer.
