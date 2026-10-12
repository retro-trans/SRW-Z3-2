# Map defeat quotes — 0.5.28

The user's Nigel screenshot from public 0.5.18 displays Japanese despite
English quote text already being present in both RPW and executable UI
translations. Map defeat dialogue uses a separate static native table.

## Binding and coverage

- Table at VA `0xa1ca28`, TOC pointer `0x99b298`: 249 three-word records,
  matching the complete RPW `deadmsg` table's pilot codes and selection modes.
  The native table stores pilot code, mode, then a quote pointer; RPW stores
  quote offset, pilot code, then mode. All source texts match exactly.
- Native selector `0x1a8028–0x1a80c0` searches these records and preserves its
  alias and unknown-code behavior. Call sites include `0x1934b4`, `0x1935d4`
  and `0x1a847c`.
- Native state stores `0x1a7fec–0x1a8018` copy the selected pilot, mode and
  quote pointer. The dialogue composer at `0x1a85c8` obtains that stored
  quote pointer for the `0x68f978` concatenation call.
- Relocate all 178 distinct quotes as mapped cp932/VWF strings. Repoint only
  the 249 native text-pointer fields; retain the original Japanese bytes,
  pilot IDs, modes, sentinel, alias mapping and consumer instructions.
- Rebuild all 249 RPW quote cells as well, including ten instances of the
  two nonverbal strings. Normalize those existing approved translations to
  `!!!` and nine dots; no untranslated entry remains in this category.

## Meaning and text bounds

Review the 176 verbal quotes in consecutive slices of 80, 80 and 16, using
the existing source briefs and speaker records. Independent barks are not
treated as a conversation. Apply 21 concrete meaning corrections; preserve
retreats, bailout commands, interrupted clauses and radio reports without
inventing deaths or unidentified attackers. Nigel's wording is:

> Damn! This disgraces the Tri-Stars...!

Synchronize active RPW, executable and answer text so later merges cannot
restore older wording. `review28_wording_audit.json` preserves English-only
review reports, retained source omissions and uncertainties. In particular,
Code: White's existing inferred “save us” remains documented rather than
being treated as an explicit source verb.

All quotes preserve source line breaks and bracket structure, fit within
three speech rows and 960 width units per row, and fit the native 256-byte
composition buffer with 30 bytes for a pilot display name, a newline and NUL.
The largest reviewed composition reserve is 175 bytes. Canonical user
spellings remain unchanged.

## Verification

Guard source table, TOC pointer, selector and state-store code. Verify byte
isolation to pointer fields. Execute the actual native selector for every
pilot code, its alias, sentinel and an unknown code; execute every native
quote-state store. Read back all 249 executable payload references and all
249 RPW cells in the finished build. Retain every earlier repair, verify both
ISO directory trees, and validate original/public-0.5.18 Retro Trans routes
with full-image patch round trips before publication.

In-game appearance is pending user testing; static readback and instruction
execution do not claim runtime visual confirmation. Publication requires
explicit consent for 0.5.28.
