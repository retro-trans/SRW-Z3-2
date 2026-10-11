# Reported UI fixes — 0.5.15

The five reported screens are covered by this local test build. In-game
appearance remains pending user navigation. The saved screenshots are reports
of the earlier defects, not captures of the rebuilt image.

The stray kanji came from the native fallback in the centering helper. The
original CP932 drawer restores its source pointer from register r0. Our helper
had restored the caller's return address into r0 instead. Native captions that
missed the English dictionary, including blank suffixes and ON/OFF choices,
therefore reached the renderer with an address inside executable code. The
helper now restores the original source pointer before entering that fallback.
This repairs the stray text behind intermission help and native settings.

The regression executes the original native draw tail through its final
renderer entry, rather than stopping at the fallback branch. Final-file
verification exercises ON, OFF, whitespace and an unknown native caption in
both style modes. The alternate native formatter is modelled with checked
encoding/source arguments; the ordinary native tail executes instruction by
instruction. These are bounded execution checks, not emulator screenshots.

Level-up now uses Z3's CQB caption instead of the overlapping Melee label.
DEF/SKL and EVD/HIT use ordinary outlined Latin glyphs at a 28 px quad instead
of the undersized private badges. Their source coordinates, row spacing,
order and display state remain intact. Label advances at that size are
56.875/54.25 and 58.625/47.25 px, within the original two-cell fields.
The final RPW archive is also checked for the existing Foc skill terminology
in all 18 relevant name columns, including Foc+ Evade in its three columns.

The concluding narration reads:

> It was the beginning of a new battle...
>
> the beginning of a battle without end.

Both rows were reviewed with the preceding military briefing and fleet descent.
Exact draw-time bindings use fingerprinted member 27 at offsets 0x654 and
0x6a4. The original archive member, fixed rows and timing are byte-identical.

Intermission's Ep caption moves ten native pixels left, while Clear moves
eight right to separate the episode value from the clear status. Live counter
positions and the turns field's numeric reservation stay unchanged. Rengoku
Link keeps its native center: the old plan subtracted half the English width
even though its renderer mode already invokes the centered drawer.

Settings use Voice Vol., SE Vol. and BGM Vol. The voice caption ends at
native x=360.375, leaving 25.125 px before the reserved icon area at x=385.5.
The separate native triangle/Play controls remain intact. Remember Sort/Info fits before the
native choice brackets. Three fullwidth Latin ON/OFF widgets omitted by the
Japanese-text catalogue now have explicit, source-bound English bindings.
Two help sentences with Morale immediately followed by a color control are
also corrected to Focus without changing the controls.

The title retains the English logo and retro-trans credit with v0.5.15.
Public release 0.5.2 is unchanged. The build continues using the existing
Retro Trans Tools-compatible archive pipeline and cumulative translation.

Regression: 244 tests run, 243 passed and one optional check skipped.
Final evidence is written to `work/ui/ui_review_0.5.15.json` by
`tools.verify_ui_review`; it includes the cumulative font, Library, title,
UI, archive and ISO checks.

Testing image: `work/output/iso/0.5.15/Tengoku-hen-English-0.5.15.iso`,
5,284,167,680 bytes. All 82 files passed readback through both ISO directory
trees. SHA-256:
`4f65bed87b05ba45d5e0d9e8d068a9c847fc46dc7d329bd8138b07e368a0e900`.

```powershell
& $py -m tools.ui_review_fixes
& $py -m tools.ui_review_fixes --apply
& $py -m tools.endless_narration
& $py -m tools.endless_narration --apply
& $py -m tools.settings_layout
& $py -m tools.settings_layout --apply
& $py -m tools.status_layout
& $py -m tools.status_layout --apply
& $py -m tools.intermission_layout
& $py -m tools.intermission_layout --apply
& $py -m tools.title_screen --version 0.5.15
& $py -m tools.title_screen --version 0.5.15 --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -m unittest discover -s tests
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_ui_review --version 0.5.15
& $py -m tools.verify_ui_review --version 0.5.15 --apply
```
