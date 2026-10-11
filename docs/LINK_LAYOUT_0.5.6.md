# Link and command layout — 0.5.6

The reported name, dialogue and backlog selections retain the original link
IDs, colors and navigation. The new executable geometry uses the width actually
drawn, including name substitutions and native glyphs. SRW Z3's Rodin Bold font
profile from 0.5.5 remains in use.

`tools/link_layout.py` follows the reference's `link_background_layout.py`,
`main_link_background_layout.py`, `link_identity_geometry.py` and
`dialogue_link_scene.py`. Tengoku sites were found independently in the verified
BLJS10299 executable. In particular, Tengoku's primary draw context lives in
r28; the reference's r27 assumption does not apply here.

| Path | Tengoku binding | Change |
| --- | --- | --- |
| Drawer width | 0x141a8 / 0x1488c | Capture initial and final pen; private float scratch |
| Dialogue/backlog segments | 0x2209e4 / 0x21f700 | Accumulate width at 1/128 pixel precision; preserve line y |
| Link registration | 0x21cddc | Cache width per 16-bank × 16-slot render index |
| Backlog selection | 0x216a3c / 0x216ad0 | Read cached width; keep native position/height/color |
| Dialogue selection | 0x214b54 | Match both scene pointer and glossary index; use rendered position |
| Registration identity | 0x21ce04 / 0x21ce74 | Null scene falls back to scene zero; compare translated display keys without overwriting native keys |
| Speaker name box | 0x2aae04 | Use VWF units × live quad/32; unknown native names keep native pitch |
| Command centering | 0x14a28 | Center translated UTF-8 captions using live quad; native misses and CP932 widgets retain original path |

The source spans, private scratch address, generated helpers and changed file
ranges are recorded in the build report. Scratch payloads have 16-byte alignment.
Instruction tests cover fractional widths, bank limits, mixed scene identities,
custom/native names, null/explicit scenes and centering fallback.

The complete regression run contains 208 tests: 207 passed, one optional
Capstone check skipped. Final-artifact readback verifies all 12 matched files,
all 15 installed layout helpers, 14 encoded/native width cases and both
assembled prologue keys. `work/ui/link_layout_0.5.6.json` records this evidence,
the five original screenshots and approximate bounds in original image pixels.

`tools/operation_layout.py` adds exact keys for the two assembled prologue
headings. Prologue 1 reads **Prologue 1: At the End of the Time Prison**.
The original title fragments and formatter remain byte-exact, preserving other
consumers of those fragments.

The native mission splitter at 0x1aa6e8 uses 103-byte slots: two color bytes,
at most 100 text bytes, and a terminator. The reported 122-byte English line
overwrote the following slot. Its complete explanation now reads:

> This scenario has no SR Point.  
> Blue text marks the final victory condition.  
> Meeting it clears the map.

This repair is scoped to the reported explanation. Other long mission strings
still need a separate audit of the native 302-byte input and 100-byte line
limits; the 0.5.5 width-only wrap did not enforce those byte limits.

Testing output: `work/output/iso/0.5.6/Tengoku-hen-English-0.5.6.iso`.
SHA-256: `4dbb286f5b89b9416dc0e99202fbc6b86d564be7c70cbef6c57d2cf1e4c023c1`.
All 82 files were verified through both ISO directory trees. Font readback
checks 211 glyphs on both pages and 211 advances; the 28 opening hooks and
29 name-reader cases also pass. This evidence is in `work/ui/startup_0.5.6.json`.
Runtime appearance remains pending user navigation. Use the matched ISO and
font cache from this build. The installed font cache was checked read-only and
does not match 0.5.6; refresh the game's installed data before testing.
Publishing and emulator-state changes are separate
actions; this build does neither.
