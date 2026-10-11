# Focus terminology and native outlined font — 0.5.14

The reported Spirit screen used Morale in a narrow native stat field. It now
uses **Foc**, matching `../SRW Z3/translation/ui_hook.json`. Descriptions use
**Focus**, as in Z3's ability and Spirit descriptions. The Focus Spirit
command keeps its existing name.

`tools/focus_terminology.py` updates only English UI fields with source-bound
Ki context, including three continuation rows checked against their adjacent
stat sentences. It updates 358 English fields in menus, help, skills, parts,
the executable catalogue, Spirit descriptions and compact name/art fields.
The source-bound status and battle plans also replace their old Will
overrides with Foc, and the weapon requirement uses Foc Req. Ordinary prose
will and historical review notes are unchanged. The selected terminology is
recorded in `work/glossary/ui_stats.json`.

The plain-looking yellow lettering had a texture-format problem. Font pages
use two-byte G8B8 cells: their high byte contains the outer coverage mask and
their low byte contains the letter fill. The old writer treated these bytes
as RGBA4444 and repeated the same nibble through both channels. Native Lv/SP
cells have a separate outline extending about two texels outside the fill.

The new writer preserves the exact Z3 Rodin Bold fill raster and advances,
and adds a two-texel outer mask in the correct channel. This enables the
native renderer's outlined label treatment. The shared generated cells are
corrected on both font pages; original Lv/SP and all cells outside the
allocation remain byte-identical. The mask comparison preview is
`work/ui/font/focus-outline-preview-0.5.14.png`. It is a font-mask simulation,
not an in-game capture.

Foc uses 58 advance units, or 50.75 px at a 28 px quad, fitting the original
two-cell 56 px field with four pixels of outline allowance. The crowded
Spirit caption Effect becomes Eff. at widget `0x8f864`. Native stat values,
positions, font pitch, renderer colors and gameplay logic are unchanged.

Regression: 241 tests run, 240 passed and one optional check skipped. Tests
check independent fill/outer masks, exact Z3 letter shapes and widths, compact
Foc fit and source-bound terminology. The cumulative final-artifact verifier
also checks all 23 native Ki widgets, the Eff. caption, both font pages and
all earlier UI, Library, title and narration fixes.

Final-file dry verification passed for all 23 native Ki labels and all 249
allocated cells on each font page. Of those cells, 241 have visible outer
coverage; the other eight contain whitespace. Both native font headers and
every cell outside the allocation remain unchanged.

The title footer shows v0.5.14 with the existing retro-trans credit. This is
a local testing build; public release 0.5.2 is unchanged. In-game appearance
remains pending user navigation.

The testing image is `work/output/iso/0.5.14/Tengoku-hen-English-0.5.14.iso`,
5,284,167,680 bytes. All 82 files passed readback through both ISO directory
trees. SHA-256: `08a8c897991644aba1755f0e19e816a6d74944e26d1b06baab186b3c78961a5c`.
Final verification is recorded in `work/ui/focus_style_0.5.14.json`; the
reported screenshot is saved as
`work/ui/screenshots/reported-0.5.14-focus-style.png`.

```powershell
& $py -m tools.focus_terminology
& $py -m tools.focus_terminology --apply
& $py -m tools.focus_font_preview
& $py -m tools.focus_font_preview --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -m unittest discover -s tests
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_focus_style --version 0.5.14
& $py -m tools.verify_focus_style --version 0.5.14 --apply
```
