# Sources and recovery

Accessed **2026-10-22** unless stated otherwise. A source claim is not a measured
property of the Draco 18. Hashes identify acquired bytes, not authenticity or rights.

## Primary references and identity leads

| ID | Source | Scope |
|---|---|---|
| FCC-18 | [JBBSP-1812 grant mirror](https://fccid.io/JBBSP-1812) | Smartech SP-1812 identity, 1991 grant; no protocol |
| FCC-12 | [JBBSP-1212](https://fccid.io/JBBSP-1212) | Related applicant/model, not equivalence |
| OEM-INDEX | [Smartech index](https://device.report/smartech) | Discovery only; mixes unrelated companies |
| MM-INDEX | [Manufacturer legacy manuals](https://www.gtcocalcomp.com/legacy-products-user-guides/) | MM 1812 and related references |
| MM-18 | [MM 1812 technical reference](https://www.gtcocalcomp.com/wp-content/uploads/2018/02/MM-1812-Technical-Reference.pdf) | Bit Pad version, December 1989; [abbreviated reference](mm1812-reference.md), [receipt](acquisitions/2026-10-22-mm1812-retry.md), [earlier failure](acquisitions/2026-10-22-mm1812.md) |
| MM-DRIVER | [Writing Drivers for MM Series](https://www.gtcocalcomp.com/wp-content/uploads/2018/02/Writing-Drivers-for-MM-Series.pdf) | Acquired/text extracted; BASIC examples exposed to researcher; [receipt](acquisitions/2026-10-22-mm-driver-reference.md) |
| CC-COMMANDS | [DrawingBoard III commands](https://www.gtcocalcomp.com/wp-content/uploads/2018/02/DrawingBoard-III-Commands.pdf) | CalComp behavior, not proven on Qtronix |
| XORG | [X.Org driver archive](https://xorg.freedesktop.org/archive/individual/driver/) | summa/calcomp archives listed; no source inspected for implementation |

Host, CADCraft, serial, and uinput references are linked where used in the
[hardware inventory](../hardware/tablet.md), [capture contract](../protocol/capture-format.md),
and [roadmap](../integration/roadmap.md). Licensing sources are in the
[root README](../../README.md#rights-and-attribution).

## Qtronix recovery candidates

No Qtronix binary is recovered. The supplied inventory remains ignored in `tmp/`;
its SHA-256 is `b562a0b22e3b0d940f6f1ba82e8fcbb1ac8282414ce6047e0983adeb5cd59201`
and identifies the text, not the missing archive. Draco 18's catalog inventory
lists 15 entries/568,309 uncompressed bytes, mainly 1995–1996; this dates software,
not the tablet.

| Catalog | Claimed file | Inspect first if recovered |
|---|---|---|
| [Draco 18](https://www.input-drivers.com/drivers/65/65813.htm) | `draco18.zip` | `readme.1st`, `readme.w95`, `qdtablet.inf`, then mode/configuration utilities |
| [QD-1212](https://www.input-drivers.com/drivers/52/52536.htm) | `draco.zip` | `qdadi.doc`, `qdset.doc`, `readme.doc`, `qdset.par`, `tosumma.exe`, `tomouse.exe`, `qdset.exe`, `qdadi.com` |
| [Draco 12 Win95a](https://www.input-drivers.com/drivers/57/57982.htm) | `DRACO12` | Identify actual format/contents first |

[Qtronix catalog index](https://www.input-drivers.com/companies/868.htm).
The tested Draco 18 download returned an updater advertisement, rejected as ZIP
([receipt](acquisitions/2026-10-22-draco18-link.md)); a guessed DriverGuide detail
URL redirected to a generic manufacturer page. No driver was executed.

Prior searches covered exact FCC/OEM IDs and utility names, Archive.org/indexed
historical downloads, and manufacturer aliases without recovering a verified binary.
Unrelated games/phones called `draco.zip` and modern Smartech companies were excluded.
This was not an exhaustive archive crawl. Earlier shell DNS and PDF browser limits
were acquisition restrictions, not missing-document proof; the MM downloads later
succeeded. X.Org raw-source retrieval failed; its index remained available.

Preservation leads: [2003 Draco 12 forum request/driver offer](https://www.thecadforums.com/threads/does-anyone-here-use-or-have-the-draco-12-ditizer-by-qtronix.60134/)
and [2011 boxed Draco 12 discussion](https://render.ru/xen/threads/qtronix-draco-12-digitizer.140314/).
Neither yielded an attachment. No one was contacted; no archive was purchased.

## Hardware-free follow-up, 2026-10-22

**Observed:** OCR completed for all 82 MM pages with Tesseract 5.5.0 and Poppler,
rendered at 2200-pixel maximum dimension with one OCR thread per page. Output,
page images, and hash/tool provenance remain in
`.artifacts/mm1812-ocr-2026-10-22/`. The reference's technical tables were checked
against rendered pages; OCR confused letters/digits and is not authoritative.
**Source claim:** this is the Bit Pad version, publication 84-DM71-B50, not a
universal MM protocol. Reset text and Appendix D disagree about factory gating;
[the digest](mm1812-reference.md) preserves that discrepancy.

| Recovery check | Observed outcome / limit |
|---|---|
| Exact-name web searches: `draco18.zip`, `qdadi.doc`, `qdset.exe`, `tosumma.exe`, FCC/OEM aliases | Catalogs and unrelated hits; no verified driver recovered |
| [DiscMaster deep filename search](https://discmaster.textfiles.com/search?q=draco18.zip&mode=deep&outputAs=json) | Empty lists for `draco18.zip`, `tosumma.exe`, and `qdset.doc`; index coverage is not exhaustive |
| [Internet Archive metadata search](https://archive.org/advancedsearch.php?q=%22qtronix%22&fl%5B%5D=identifier&fl%5B%5D=title&rows=50&output=json) | 13 item matches, no Draco-named title; includes mouse/OEM software and generic driver CDs, not proof of digitizer contents |
| [Bitsavers mirror's Qtronix index](https://ftpmirror.your.org/pub/misc/bitsavers/pdf/qtronix/) | Only `qtronix_scorpius-35/` listed; no digitizer manual there; direct Bitsavers hosts returned HTTP 404 |
| [Wayback CDX query](https://web.archive.org/cdx/search/cdx?url=qtronix.com/*&output=json&filter=urlkey:.*(draco%7Cdigit%7Cqd).*&filter=statuscode:200&collapse=urlkey&filter=mimetype:application/zip) and [availability API](https://archive.org/wayback/available?url=www.qtronix.com/) | HTTP errors here; snapshot coverage remains unknown |

Local search responses are ignored as `.artifacts/qtronix-*`. DiscMaster's broader
Qtronix filename query also returns kernel-source paths; only metadata was read.
No additional vendor driver code was inspected or executed, and no hardware opened.

The [Clube do Hardware volume 4 inventory](https://archive.org/download/ch-vol-4.7z/lista_vol_04.txt)
was acquired through the artifact tool: 7,918 bytes, SHA-256
`2c4965b9af60d7d930d8e154acd41d803c94382fb9730b943b92ac0e982b8728`,
receipt `397936ea-2cd2-4515-a78c-37a7117fe3f4`. It lists Qtronix PS/2/serial
mouse and integrated keyboard/mouse entries, without a named digitizer. The
431,692,524-byte archive was not downloaded; an abbreviated inventory cannot prove
all of its contents, but it does not justify prioritizing this disc.

**User report:** no original disks, backups, or old computer are available.
Next targets are archived manufacturer/FTP pages and CD inventories naming the
exact tablet files. Avoid large disc downloads without a relevant member listing.
Historical catalog/forum links remain leads; repeated updater links add no evidence.

## Acquisition and inspection

Search archived manufacturer download pages, historical FTP/CD indexes, and exact
filenames. Validate contents/provenance, not archive names. Use existing tools:

```sh
uv run python tools/artifacts.py fetch 'HTTPS-DIRECT-URL' --name draco18.zip --kind zip
uv run python tools/artifacts.py ingest /path/to/recovered.zip --name recovered.zip --kind zip
uv run python tools/artifacts.py inspect .artifacts/downloads/recovered.zip
uv run python tools/artifacts.py extract .artifacts/downloads/recovered.zip
```

Optional `--report docs/research/acquisitions/NEW.md` publishes a receipt. Record
original/final URLs, UTC times, size, hash, format, tool version, and outcome. Full
member inventories/hashes stay ignored. Failed downloads have no acquired-artifact
hash; rejected response hashes, if present, describe only that response.

Read documents, INF/configuration, and executable headers before code analysis;
`.doc` and `.com` extensions do not establish format. The disassembly helper supports
raw COM candidates only, not MZ/NE executables. Win3.x/16-bit formats need a suitable
loader. Keep strings/decompilation private; recovered sequences remain hypotheses.
If emulation becomes necessary, use a disposable guest with simulated UART, no
physical passthrough/network/home mount; record guest provenance. Never run a legacy
installer on the host. Follow the [clean-room process](clean-room.md).
