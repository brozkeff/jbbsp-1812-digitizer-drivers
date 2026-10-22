# MM 1812 Bit Pad version — practical reference

An abbreviated factual reference to **MM 1812 Digitizer (Bit Pad Version),
Technical Reference**, Summagraphics Corporation, publication **84-DM71-B50**,
issued **December 1989**. Prepared from the acquired scan on 2026-10-22.

| Provenance | Value |
|---|---|
| Original document | [Manufacturer-hosted PDF](https://www.gtcocalcomp.com/wp-content/uploads/2018/02/MM-1812-Technical-Reference.pdf) |
| Acquired | 2026-10-22, 00:07:12–00:07:14 UTC; [receipt](acquisitions/2026-10-22-mm1812-retry.md) |
| File | `MM-1812-Technical-Reference.pdf`, 12,165,229 bytes, 82 PDF pages |
| SHA-256 | `46444674fe6135d53f521d8290fb885b322bd4f4ebf9e74996054b05e64b5d13` |
| Source notice | Copyright Summagraphics Corporation 1985. All rights reserved. (PDF p. 2) |

This digest is **excluded from the repository license grant**. Source rights remain
with their owners; no permission to redistribute the original manual is asserted.
It summarizes technical facts in new prose, without the manual's software examples,
flowcharts, illustrations, or full transcription. The PDF and OCR remain ignored.

**Evidence level: source claims about this MM 1812 version.** None establishes
Qtronix Draco 18 compatibility. The manual itself warns that similarly named
Summagraphics formats can differ (manual p. 3-3 / PDF p. 20). Page references below
use the chapter pagination in the contents, followed by **one-based PDF pages**.

## Setup and serial interface

The MM is an RS-232-C **DTE**, with a female DB-25 interface. Its RTS and DTR are
permanently asserted. The manual lists baud rates **110, 150, 300, 1200, 2400,
4800, 9600, 19200**; parity is selectable as none/even/odd, with one/two stop bits.
The binary wire diagram assigns bit 7 to parity and bits 6–0 to information.
Account for UART word length and parity handling before comparing captured bytes;
the manual does not express the factory setup as a modern shorthand such as 8N1.
(2-9, 3-3–3-5, 5-7 / PDF 17, 20–22, 53.)

| DB-25 pin | Signal | Direction at MM |
|---|---|---|
| 1 | Shield/frame ground | Connector shield |
| 2 | TXD | MM to host |
| 3 | RXD | Host to MM |
| 4 | RTS | Output, asserted |
| 5 | CTS | Input, optional transmission gate |
| 7 | Signal ground | Data reference |
| 20 | DTR | Output, asserted |

CTS has an internal pull-up: leaving it disconnected permits transmission even
when CTS gating is enabled. Driving it inactive inhibits reports; disabling gating
makes the MM ignore CTS. Thus, a connected handshake line can explain silence
where a disconnected one would not. These are **MM pin assignments**, not a wiring
plan for the unverified Qtronix connector. (2-9, 5-8 / PDF 17, 54.)

Three eight-position DIP banks configure the unit. Bank 1 controls remote commands,
proximity transmission, collection mode, coordinate mode, and report rate. Bank 2
controls ASCII/binary format, CR versus CRLF termination, increment, and resolution.
Bank 3 controls parity, stop bits, CTS, cursor code, and baud. Changed switches take
effect after reset or power-up. The reset access and switches are on the underside;
record their positions before changing them. (5-4, D-2–D-4 / PDF 50, 77–79.)

The factory selections listed across the reference are 9600 baud, even parity,
two stop bits, ASCII BCD with CRLF, cursor code A, absolute coordinates, 200 lpi,
increment disabled, remote control enabled, always-transmit proximity behavior,
and CTS enabled. **Factory collection mode is inconsistent in the source:** the
reset section says Stream at 100 reports/s, but Appendix D marks both stream and
switch enabled, the combination otherwise described as Switch Stream. Preserve
that uncertainty instead of assuming unattended continuous output.
(3-3, 3-12, 3-25, D-2–D-4 / PDF 20, 29, 42, 77–79.)

## Reports and coordinates

Coordinates are **counts at the selected resolution**, not inches or millimeters.
Absolute origin is fixed at the lower left; this Bit Pad version cannot relocate
it. Relative coordinates measure displacement from the **last issued report**.
Out-of-proximity reports repeat the last valid absolute position or give zero
relative displacement; their status distinguishes them from current measurements.
Transmission outside proximity can instead be disabled by switch.
(2-8, 3-19–3-20 / PDF 16, 36–37.)

### Five-byte binary format

The first byte has the phase marker in bit 6, four button-code bits in bits 5–2,
zero in bit 1, and proximity in bit 0. Proximity is **0 inside / 1 outside**.
The following four bytes have bit 6 clear and carry six information bits each:
X low, X high, Y low, Y high. Bit 7 is shown as parity throughout. Absolute values
use 12 bits per axis; relative values use the same width with the high coordinate
bit as sign and negative values represented in two's complement.
(3-4–3-5 / PDF 21–22, Table 3-1.)

The phase marker is therefore **bit 6**, not an assumed high bit copied from another
MM format. UART parity bits and actual packet information must be distinguished.
This description is a comparison reference, not a production decoder specification
validated against the Draco 18.

### ASCII BCD format

Each axis occupies four characters, separated by commas, followed by a one-character
button/proximity flag. Absolute axes are four decimal digits; a negative relative
axis uses a minus sign plus three digits. A positive relative axis can use all four
digit positions. Reports end with CR or CRLF according to the switch. These are
ASCII decimal characters, not packed BCD bytes. (3-6 / PDF 23.)

For a four-button cursor, code A identifies buttons 1–4 as **1, 2, 4, 8**; code B
uses **1, 2, 3, 4**. No button is 0. Cursor buttons are explicitly **not additive**,
so a code resembling a bitmask is not evidence of simultaneous-button support.
ASCII flag 9 means out of proximity. The MM stylus table separately lists tip,
barrel, and both; this does not establish those controls on the project's single-
button stylus. (3-5–3-6 / PDF 22–23.)

Binary absolute output saturates at **4095**, ASCII absolute at **9999**. Higher
resolution can therefore reduce usable reporting area: at 1000 lpi, binary reaches
only 4.095 inches per axis, while ASCII also cannot span the full tablet. Relative
reporting has signed-range limits; ASCII permits only three negative magnitude
digits. Do not mistake saturation or truncated displacement for the physical edge.
(3-19–3-21 / PDF 36–38.)

## Commands and report flow

Commands are case-sensitive, single-byte ASCII characters; the MM command buffer
holds 16 bytes. Most parameter changes require remote control enabled. Even with
it disabled, the documented exceptions are trigger `T`, reset NUL, XON/XOFF,
configuration query ENQ, space, and CR. Uppercase **S** selects Remote Request;
lowercase **s** queries identification. (2-9, 3-2, D-1 / PDF 17, 19, 76.)

| Operation | Character / hexadecimal | External behavior |
|---|---|---|
| Point | `P` / `50` | One report for a button press |
| Stream | `H`–`O` / `48`–`4F` | Continuous reports |
| Switch Stream | `@`–`G` / `40`–`47` | Reports while a button is held |
| Remote Request | `S` / `53` | Wait for host triggers |
| Trigger | `T` / `54` | Request one report, including current button code |
| Absolute / relative | `Q` / `51`; `R` / `52` | Change coordinate interpretation |
| Identification | `s` / `73`; ENQ / `05` | Return model and firmware version text |
| Stop / resume | XOFF / `13`; XON / `11` | Gate outgoing reports |
| Reset | NUL / `00` | Restore current physical switch selections |
| No operation | Space / `20`; CR / `0D` | Padding, no state change |

The eight Stream and Switch Stream commands select approximate binary report rates
of **2, 4, 10, 20, 40, 70, 100, maximum**, respectively. ASCII length and baud affect
achievable throughput. Point mode is button-triggered, not a continuous button-state
feed. Remote Request emits nothing merely because a button is pressed; `T` also
requests a sample in other modes. Its documented response latency is 1–10 ms.
(3-10–3-13 / PDF 27–30; D-1 / PDF 76.)

Increment commands `a`–`h` (`61`–`68`) select **0, 1, 2, 3, 4, 5, 10, 20 counts**;
0 disables filtering. Reports require sufficient movement along either axis from
the last emitted position. Stream plus increment still reports button press and
release at the last valid coordinates when movement stays below the threshold.
(3-15 / PDF 32.)

Resolution commands `i`–`p` (`69`–`70`) select **100, 127, 200, 254, 400, 500, 508,
1000 lpi**, respectively. The metric selections are 127 lpi = 5 lines/mm,
254 = 10 lines/mm, 508 = 20 lines/mm. Resolution does not establish accuracy, and
format range must be checked before increasing it. (3-22 / PDF 39.)

XOFF may pause **mid-report after a byte**; XON continues with the following byte,
not necessarily a new phase marker. Commands still work while stopped. On this MM,
reset also clears the stopped state and restores switch defaults, whereas XON
preserves remotely selected parameters. Allow the documented **10 ms** after reset
before further commands. These behaviors differ from some older Bit Pad models.
(3-7, 3-24–3-25, C-1 / PDF 24, 41–42, 74.)

The identification reply begins with `BP1812` and contains a firmware version;
its line ending follows the terminator switch. It is identification text, not a
coordinate packet. None of these bytes has been sent to the Qtronix as part of
this work. (3-23 / PDF 40.)

## Diagnostics and practical limits

A terminal-style functional check requires matching serial parameters and **ASCII
report format**. Horizontal motion should change X while Y stays approximately
constant; vertical motion reverses those roles. Unreadable text can mean binary
mode or serial mismatch, while no text can reflect collection/proximity/CTS gating.
(6-2 / PDF 63.)

Self-test `t` (`74`) checks analog circuitry, cursor/stylus connection, and digital
circuitry/ROM. Keep the tool on the active surface. The one-byte response marks the
three checks in bits 0–2, proximity in bit 3, and aggregate pass in bit 6; bit 7
is parity. Here proximity **1 means on-table**, opposite the normal packet flag.
A successful in-proximity result is ASCII **O** (`4F` ignoring parity), not digit
zero. Code check `x` (`78`) returns a six-character firmware checksum: period,
number sign, and four ASCII hexadecimal digits. Record raw replies before interpreting
them. (6-3–6-5 / PDF 64–66.)

Appendix B gives typical cursor accuracy ±0.025 inches and proximity 0.5 inches,
stylus proximity 0.3 inches, and stationary jitter ±1 cursor/±2 stylus counts at
1000 lpi. Typical accuracy/proximity applies at 25°C across more than 99% of the
active area, with edge/corner degradation. These are historical **MM claims**,
not acceptance thresholds or measured Qtronix performance. (B-2 / PDF 72.)

For failed operation, the manual's recovery path is power-down, verify power/data
and tool connections, match host parameters, power-up, and repeat diagnostics.
Do not transfer its power-connector or supply assumptions to the Draco. The useful
next project step is to recover Qtronix-specific documentation or compare labeled
traces against these candidate behaviors; follow the project's
[bring-up guide](../experiments/bringup.md) and
[clean-room boundary](clean-room.md) before device or implementation work.
(6-6 / PDF 67; project guidance distinguished from source claims.)
