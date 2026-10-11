# Match SRW Z3's font — 0.5.5

The user requested the same font as `../SRW Z3`. That project's current
PS3 builders select `SCE-PS3-RD-B-LATIN.TTF` with `use_letters(cap=22,
dilate=0.5)`. Tengoku previously selected Rodin Regular with a different
raster and baseline. The new shared profile uses the local RPCS3 Rodin Bold
font, SHA-256 `2f10428d9fc0bbc710df221c0b5b12ee2ff881fb1a26da0594aba840f822c873`.
No font binary is stored in the source repository.

`tools/latin_font.py` reproduces the reference's single-letter geometry:
22px cap height, baseline 26, 4× supersampling, half-pixel horizontal dilation,
BOX downsampling, one-pixel advance padding and a nine-pixel blank space.
All 95 ASCII coverage cells and widths match the reference
`tools/ttfglyph.py` natural raster / blit and `digraph.py` letter settings.
The comparison is a regression test, skipped only when the local reference
or system font is unavailable. A normal glyph is not horizontally squeezed.

The wider bold letters require recalculated wrapping. English source text
is unchanged. Twenty-seven skill/part descriptions and five opening lines
use 85% condensed glyphs of the same face to retain their full meaning in
the existing panels. Fifteen source-fingerprinted dialogue records use 85%;
the complete Sphere list uses 80%. Condensed coverage and advances are derived
from the normal bold glyphs together. Control codes, default/custom player
names and source page boundaries retain their existing behavior.

The link explanation still fits five lines. `tools.startup_layout` recalculates
its wrapping and the selected No anchors using the new font advances.
The `Squad:` caption retains its 16px left shift. Both font pages, executable
advance data, dictionaries, library, dialogue, mission and voice payloads are
built as a matched set; codes remain allocated against Tengoku's original
blank slots. No Jigoku executable addresses or font atlas are copied.

Build commands:

```powershell
& $py -m tools.startup_layout          # inspect wrapping and anchors
& $py -m tools.startup_layout --apply
& $py -m tools.game_build              # preview 0.5.5
& $py -m tools.game_build --apply
& $py -m tools.iso_write               # inspect matched-file mapping
& $py -m tools.iso_write --apply
& $py -m tools.verify_startup_ui --version 0.5.5 --apply
```

The final verifier compares every allocated coverage cell on both built font
pages and every allocated advance byte against the current raster, and
executes the opening hooks and default/custom name getters in the final
executable. This is file and instruction verification; live font appearance
and menu layout still need the user's in-game check. Public v0.5.2 assets
remain unchanged.

Verified image: `work/output/iso/0.5.5/Tengoku-hen-English-0.5.5.iso`,
5,284,036,608 bytes. SHA-256:
`0569e0ea9e4057d7a0258e777923713c023694cd8389ef6a4e33b7b6adde203a`.
All 82 files passed both directory-tree checks. The regression suite ran
200 tests (199 passes, one skip). Readback verified all 211 allocated glyphs
on each of the two font pages and all 211 corresponding advance bytes;
28 opening hooks and 29 name-reader cases also passed in the final executable.
Evidence is in `work/ui/startup_0.5.5.json`.

RPCS3's installed font cache was checked without changing it. Its
`E:/RPCS3/dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0141.DAT` still
matches 0.5.4. Before testing, close RPCS3 and move Tengoku's installed-data
folder `E:/RPCS3/dev_hdd0/game/BLJS10299_DATA` to a backup location. Boot
the 0.5.5 ISO and allow the game to reinstall its matched data. Preserve
the user saves under `dev_hdd0/home/`; no installed-data or save files were
modified by this font build. Reinstalling the complete cache also refreshes
the other text assets that use the new glyph allocation.
