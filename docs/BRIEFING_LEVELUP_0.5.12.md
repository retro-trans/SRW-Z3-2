# Date, briefing and level-up — 0.5.12

This local testing build addresses the three reported screens and retains the
earlier title, Library, dialogue-link, font and menu repairs. The title footer
shows v0.5.12 with the existing retro-trans credit. The public release stays 0.5.2.

The date caption reads **New Multidimensional Century 0001 - November 12**.
The earlier VWF centering fix already covers its CP932 drawer. Verification now
enters the real native function at `0x149bc` using the date caller at `0x1541c8`,
then executes the installed measurement helper. At the native 40 px glyph size,
the English width is 1022.5 px and its left edge is 128.75 px: center 640 px.
Both native style modes and a 30 px size also pass. The original date caller,
calendar text, x=640, y=360, size and scale remain byte-identical. No additional
date adjustment is applied on top of the existing VWF centering.

The three static military-report lines now read:

- Earth Federation forces: 34.8% of founding strength remaining.
- The chain of command is disrupted.
- Enemy Sidereal: strength, organization size, all else unknown.

`tools/briefing_narration.py` binds all three source strings to AIDDATAPACK
member 26 and its full source fingerprint. `ui_catalog` adds their exact keys
to the existing draw-time dictionary. Original fixed rows and timing stay
unchanged. The first and third lines use the existing condensed Rodin alphabet
within the conservative 900-unit single-line budget. All three source rows
were reviewed together; Sidereal follows the glossary. The remaining-strength
comparison explicitly refers to the Earth Federation's founding.

The level-up panel uses the Z3 compact labels CQB, RNG, DEF, SKL, EVD and HIT.
The reversed DEF/SKL pair at `0x99f04` was missing from the earlier compact
pair rules; its native line order is retained. The shared Score suffix at
`0x8f044` is empty, leaving the numeric kill count intact. The existing compact
glyphs are reused without changing their font or pitch. Numeric fields,
rating fields, coordinates and gameplay data retain their original bytes.

Build and verification:

```powershell
& $py -m tools.briefing_narration
& $py -m tools.briefing_narration --apply
& $py -m tools.status_layout
& $py -m tools.status_layout --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -m unittest discover -s tests
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_briefing_levelup --version 0.5.12
& $py -m tools.verify_briefing_levelup --version 0.5.12 --apply
```

The verification report is `work/ui/briefing_levelup_0.5.12.json`. It executes
the final date drawer and the three briefing dictionary keys, checks the
unchanged briefing source member and runs the cumulative final-artifact checks.
The harness supports the native floating-point move used by the date drawer;
this is verification code, not a game patch. Reported screenshots remain
evidence of the original issues; runtime confirmation still needs user navigation.

Regression: 237 tests run, 236 passed and one optional check skipped. The
matched font allocation has 249 cells; the two additions are condensed 4 and 8
for the briefing's 34.8% figure. Both font pages, every encoded archive and the
executable use the same new mapping.

The testing image is `work/output/iso/0.5.12/Tengoku-hen-English-0.5.12.iso`,
5,284,167,680 bytes. All 82 files were read back through both ISO directory
trees. SHA-256: `6aa696d9652603fa8f69c641acff92bf2ad536b8b80ac95f272cf370a64aba32`.
