# Roadmap and integration gates

| Stage | Deliverable | Evidence required |
|---|---|---|
| Research tools | Capture, replay, provenance, procedures | Synthetic tests and scoped hardware reports; current stage |
| Device characterization | Puck/pen traces, settings, initialization, calibration | Independent movements/buttons predicted after reopen/power cycle |
| Linux/CADCraft | Clean-room decoder and calibrated input | Reviewed specification handoff and disposable-drawing tests |
| Linux desktop | Absolute input, then relative pointer | uinput/desktop classification, button release, lift/re-entry tests |
| Windows/macOS | Reuse proven decoder, later platform integration | Real hosts/adapters and maintained regression fixtures |

Define the production event interface after measurement: raw counts, time, tool
profile, buttons/transitions, and observed proximity. Separate transport, decoding,
calibration, overlay mapping, and outputs. Do not invent pressure/tool ID.

## Next session

Hardware testing stopped at the operator's request after pen G.
Review the [hardware findings](../observations/2026-10-22-validation.md).
The remaining pen paper targets are optional future work, not an immediate task.

1. **Offline first:** draft a research behavioral specification from the preserved
   sessions. State confidence in framing, coordinate pairs/directions, individual
   puck buttons and pen switches. Include startup fragments and accidental presses;
   distinguish observed results from requested actions. Keep unknown header bits,
   combinations, release/proximity semantics, units and mode identity explicit.
   Any production implementation requires the separate
   [clean-room handoff](../research/clean-room.md), not this research context.
2. **Resolve input behavior before integration:** in a future bounded hardware
   session, test press/hold/release, lift/re-entry and reopen/restart explicitly.
   Silence is not an explicit release or proximity event. Establish how a later
   consumer can release buttons safely; do not infer missing transitions from
   today's gated captures. Test tip plus side button separately if needed; `9B`
   is still only a combined-action hypothesis. Record actual actions with capture
   annotations rather than relying on a wall-clock instruction schedule.
3. **Measure when calibration is wanted:** choose a tool and application tolerance,
   record active-area bounds, and secure a measured reference covering the intended
   work area. Use widely spaced corners/edges and interior fitting targets, plus
   separate validation targets. Follow the [calibration procedure](../experiments/calibration.md)
   for repeat placements, affine fitting, and error/uncertainty reporting. Corners
   alone do not establish interior accuracy. Repeat for pen only when its calibrated
   use is needed; there is no need to finish today's approximate pen paper grid.
4. **Then implement and integrate:** after reviewing the specification and allowed
   fixtures, use a fresh implementation context for the decoder. Validate fragmented
   input and recorded failure cases before a calibrated CADCraft disposable-drawing
   trial. Desktop injection follows proven release/disconnect handling.

Keep the working 9600 8N1 setting as the next comparison baseline. A new baud sweep
or transmitted initializer is not justified by current receive success. Reconfirm
the chosen port, equipment, tool, power state and reference registration next time;
hardware opens and any future probe execution remain explicit CLI actions.

## CADCraft

Observed version: package **0.8.0-1**, CLI **0.8.0**. GUI integration is untested.
The [v0.8.0 control specification](https://raw.githubusercontent.com/storytold/cadcraft/v0.8.0/docs/control-protocol.md)
describes loopback JSON-lines TCP via `cadcraft --control 7979` and
`cadcraft-cli mcp --connect 127.0.0.1:7979`. Inspect `control.methods` first.
Relevant methods: `ui.pointer`, `ui.inspect`, `cmdline.input`, `cmdline.state`,
`engine.execute`, `drawing.inspect`. Headless CLI/MCP has a separate drawing unless
explicitly connected. GUI `--help` starts the application; use CLI help instead.

For the later bridge use drawing-world coordinates, a persistent connection,
correlated IDs, bounded work, and preserved button transitions. Verify pointer
press/hold/release support. Stop actions on disconnect; inspect state after
ambiguous mutation timeouts before retrying. Never duplicate clicks on reconnect.

Acceptance: a calibrated line/polyline through known marks in a disposable drawing;
inspect coordinates/entity counts, test buttons/cancel/one menu region, proximity,
CAD disconnect/restart, then save/reopen DXF. Headless geometry tests and GUI pointer
tests establish different things.

## Desktop and portability

[Linux uinput](https://docs.kernel.org/input/uinput.html) provides userspace virtual
input; consider libevdev when implementing it. Use a project identity and measured
capabilities, not Wacom IDs. Test X11/Wayland and absolute mapping/aspect ratio;
relative mode needs jump-free re-entry and button release on disconnect. Install
narrow permissions only when needed; do not grant broad input-device access.

A laptop USB host port cannot become a USB HID peripheral through uinput.
A physical HID bridge needs gadget-capable hardware/microcontroller. A USB-to-RS232
adapter remains serial: record its model, driver, and handshake differences.
Windows/macOS injection, signing, packaging, and deployment follow Linux validation.
