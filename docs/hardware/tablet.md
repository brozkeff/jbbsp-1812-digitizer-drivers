# Hardware inventory

## Tablet — user reports

Qtronix **Draco 18**, Taiwan R.O.C., RS-232, label **FCC ID JBBSP-1812**.
Red power LED is lit; the green LED lights with the puck on the surface.
Neither LED establishes serial output.

| Item | Reported | Still needed |
|---|---|---|
| Surface | Described as 18-inch | Measured active width/height and coordinate bounds |
| Puck | Four buttons, crosshair/coil; connected | Button labels, connector, transitions/combinations |
| Stylus | Single button; replaces puck | Tip/switch behavior, coordinates, offsets; swap only powered down |
| Power | Power switch on | Supply voltage/current/polarity and startup behavior |
| Cable | RS-232 through laptop dock | Connector genders/pins, adapters, wiring, handshakes |
| Setup | Unknown | Switches, positions, reset controls, any configuration strip |

**Source claim:** the [FCC grant mirror](https://fccid.io/JBBSP-1812), accessed
2026-10-22, identifies Smartech Technology Inc., model SP-1812, grant 1991-11-18,
application 1991-10-04. This identifies an OEM lead, not this unit's manufacture
date, dimensions, or protocol. Draco 12/QD-1212, SP-1212, and SP-1812II remain
related-model leads; no additional equivalent retail model is verified.

Resolution, accuracy, rate, baud/parity, packets, initialization, relative mode,
proximity reporting, and persistence are unknown. Pressure, tilt, and automatic
tool identification are not established.

## Host observations

A Linux host used a dock RS-232 connection. Explicit captures on /dev/ttyS0
received puck and pen data at 9600 8N1, flow control off, with DTR/RTS requested
off. Port access does not establish cable pinout or electrical line behavior.
The dock model and wiring remain unconfirmed. No BIOS, group, udev, or service
changes were made. The doctor command inspects host inventory without opening
ports; review its account and machine details before sharing output.

## Overlay — user report

Two-sided paper under foil: AutoCAD AME/AutoShade, with Modify, Primitives,
Inquiry, Utility, Display and RenderMan sections; reverse: AME and Region Modeler,
and AutoShade. These are candidate software menu regions, not verified firmware
controls. Record dimensions, orientation, registration marks, legends, and region
bounds. Keep separate profiles for each side/registration and tool; use the puck
crosshair as reference. Original scans and a proprietary-overlay recreation are
not included. See [calibration](../experiments/calibration.md).
