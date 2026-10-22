# Clean-room boundary

The production implementation must be original. Research publishes behavioral
facts and evidence; implementation consumes a reviewed specification. This is an
engineering process, not a legal certification.

## Research

Keep vendor binaries/source, extracted material, OCR, strings, disassembly, and
decompilation in ignored `.artifacts/`. Historical open-source drivers also need
license/provenance review; do not silently import them.

Publish concise factual findings: serial settings, command/reply bytes, timing,
packet fields, mode behavior, confidence, and limitations. Cite sources/pages and
artifact hashes. The attributed MM reference is a documented exception for a
factual digest, not permission to publish a full transcription or software examples.
Do not publish vendor routines or pseudocode that mirrors their control flow.
Source claims remain unverified on this tablet until hardware confirms them.

## Production handoff

Before implementing a decoder, prepare:

- Reviewed behavioral specification with evidence/confidence and unsupported cases.
- Independently collected traces or independently constructed fixtures, expected
  behavior, and provenance.
- Researcher's exposure declaration and implementer's allowed-input declaration.

Use a separate person or fresh agent context that has not seen vendor code,
decompilation, private analysis, or inherited research conversation. Pass only the
reviewed specification and allowed fixtures; record the dated handoff. Driver
architecture decisions then belong in `docs/decisions/`.

The current tools are generic logging, receipt, diagnostics, and replay utilities;
they contain no Qtronix decoder. This research context has seen BASIC examples in
*Writing Drivers for MM Series* and reads the MM technical manual. It must not be
inherited by the eventual production implementer. No Qtronix driver binary/source
has been inspected.

## Publication

Never force-add `.artifacts/`, `tmp/`, or working `sessions/`. Publish reviewed
original reports/tools and independently sourced fixtures. Source rights stay with
their owners; checksums establish byte identity, not authenticity or redistribution
rights. See [project attribution](../../README.md#rights-and-attribution).
