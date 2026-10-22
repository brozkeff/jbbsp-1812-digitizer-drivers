# Serial bring-up

**Proposed procedure; requires an operator at the tablet.** Read the
[hardware inventory](../hardware/tablet.md) and preserve every result, including silence.

## 1. Inventory and access

Record tablet/dock/supply labels, cable/adapter identities, connector pins/genders,
setup controls, and LED states. Do not change unknown controls or hot-swap tools.
Continuity measurements need disconnected, unpowered cables. Use proper RS-232,
not a TTL UART cable; never bridge unknown tablet pins.

Inspect from a normal host terminal:

```sh
id
ls -l /dev/ttyS0
uv run python tools/draco.py doctor
fuser -v /dev/ttyS0
systemctl status serial-getty@ttyS0.service --no-pager
systemctl status ModemManager.service --no-pager
```

Select the port explicitly; do not open a console or another application's port.
Missing `/dev` with UARTs in sysfs suggests namespace restrictions; permission
errors require comparing node ownership/ACLs and effective groups. An account's
new group membership may need a fresh login. Busy ports require identifying the
owner (possibly ModemManager/getty/brltty), not blindly disabling services.
Do not use root, `chmod 666`, or automatic group/udev/service/BIOS changes.
A disconnected-port loopback or known-good RS-232 device can confirm dock mapping
when the pinout is known. Missing optional host commands are not tablet failures.

## 2. Annotated receive trial

Use a new directory for each trial. Start with the connected puck:

```sh
uv run python tools/draco.py capture --port /dev/ttyS0 --backend posix \
  --baud 9600 --bits 8 --parity N --stopbits 1 --dtr off --rts off \
  --duration 30 --output sessions/e02-puck-9600-8n1 --annotate-stdin \
  --note 'puck connected; unchanged power and setup controls'
uv run python tools/draco.py analyze sessions/e02-puck-9600-8n1
```

Annotate puck absent, center/still, horizontal and vertical movement, individual
buttons, then lift/re-entry. Repeat if 30 seconds is insufficient. Type `:stop`
to finalize early. Do not power-cycle in the first baseline. Preserve raw bytes,
settings, actions, counts, and hashes; tool defaults are not measured device defaults.

If silent/inconsistent, try separate receive-only trials: **9600 8O1**, **1200 7N1**,
**1200 8N1**, then **9600 7E1**, **4800 8N1**, **2400 8N1**, **19200 8N1**.
Keep flow control off initially; record DTR/RTS requests. Change one factor at a
time. These are discovery candidates, not an exhaustive compatibility matrix.
Opening a port can change control lines even without application TX.

## 3. Hypotheses and silence

| Candidate | Basis | Needed evidence |
|---|---|---|
| Summagraphics/MM family | User lead; catalog lists `tosumma.exe` | Exact format/settings, source-backed commands, absolute positions/buttons |
| Microsoft mouse | User lead; `tomouse.exe` listing | Relative framing/deltas and actual button limitations |
| Mouse Systems | Comparison candidate | Independent movement/button matches |
| CalComp family | User lead; manufacturer references | Exact selected format and behavior |
| Qtronix/Smartech native | Device identity | Labeled traces and recovered documentation |

The [DrawingBoard III reference](https://www.gtcocalcomp.com/wp-content/uploads/2018/02/DrawingBoard-III-Commands.pdf)
reports CalComp modes including 9600 8O1 MM and 1200-baud mouse configurations.
These are CalComp claims, not Qtronix defaults; MM-family references also describe
different versions. A matching-looking header is insufficient evidence.

After bounded trials, inspect cabling/control lines and setup controls. Point,
button-gated, or prompted modes may be silent. Test DTR/RTS variations as recorded
experiments. A breakout/analyzer or level-safe RS-232 receiver may be needed to
separate wiring/framing faults; host timestamps do not measure wire timing.

Only a relevant source-backed **volatile** sequence justifies a probe recipe with
exact bytes, settings, timing, expected response, provenance, and recovery:

```sh
uv run python tools/draco.py probe --port /dev/ttyS0 --backend posix \
  --output sessions/e03-init --recipe .artifacts/recipes/reviewed.json
```

This previews only. Review its source/applicability before explicitly adding
`--execute`. No working Qtronix initializer or persistent save command is supplied.
See the [recipe contract](../protocol/capture-format.md#probe-recipes).

## 4. Characterize a repeatable candidate

Collect fixed points, horizontal/vertical/diagonal sweeps, corners/edges, and puck
rotation about its crosshair. Preserve high/control bits; host chunks are not packets.
At center, press/hold/release each of four buttons ten times, then combinations and
movement-plus-buttons. Test lift/re-entry, reopen, and a recorded power cycle;
measure persistence without saving settings. Then close capture, power down,
swap to the stylus, and repeat separately. Do not infer pressure or tool ID.

A candidate must predict independent positions/buttons and measured proximity,
handle fragmented/noisy captures, and repeat after restart. Only then prepare a
[clean-room handoff](../research/clean-room.md) and [calibration](calibration.md).

## Report fields

Use a dated `docs/observations/` Markdown report with `title`, `created`, and `status`
frontmatter. Include question/hypothesis, evidence level, operator/time, equipment,
settings/backend, controls/LEDs, exact command, session UUID/path, recipe source/hash,
actions/annotations, byte counts and evidence hashes, results, errors/recovery,
limitations/uncertainty, conclusion, and next discriminating trial. Distinguish
operator reports, measured results, proposals, and PTY checks.
