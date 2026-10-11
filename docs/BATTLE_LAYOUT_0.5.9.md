# Battle and map layouts — 0.5.9

This local testing build addresses the five reported screens using the compact
labels and font-cell approach in the adjacent SRW Z3 repository. In-game
confirmation remains pending user navigation.

| Screen | Change |
| --- | --- |
| Battle preview | Fit Atk., Ctr., Evd., Def., S.D., Rnd. and EN in their native slots. Shorten bottom choices to Support, Action and Anim: ON/OFF. Use Will before live morale values. |
| Map popup and map data | Use narrow MV and AT/DF labels with Z3's font metrics; shorten defense, evasion and recovery captions. Translate the reported terrain to Debris Field. |
| Battle result | Remove the separate Units suffix from Score, leaving the score and level values intact. |
| Quick battle | Use Fast before the fixed Cancel icon, preserving both controls. |
| Transformation | Fit Will beside the pilot value; retain the translated compact movement types introduced in 0.5.8. |

Five Spirit-status templates use eighteen two-letter cells in place of the
overflowing full-name sequences. Their labels are Va, So, Ft, Al, Pe, Wa, Fo,
St, Ac, Ze, Me, Sn, As, Fy, Lu, Ga, Di and An. These follow this project's
settled Spirit names. The original slash, two-byte cell indices and 32-unit
advances are preserved so the game's individual status highlights keep their
positions. Full Spirit names remain available in the Spirit menus.

The normal face remains SRW Z3's Rodin Bold. The new Spirit cells adapt its
16-pixel cap height, baseline 23, two-pixel letter gap and 28-pixel ink budget.
Font codes and executable addresses are independently bound to Tengoku.

`tools/battle_layout.py` binds 53 text widgets to original string and widget
fingerprints. Eight narrow map labels change only five font-metric bytes;
line pitch, state flags, numeric styles and coordinates remain intact. The
combined build verifies 344 text-widget edits and the existing one numeric
coordinate change. All original FSSA strings remain in the source pool.

Two exact executable draw keys shorten EN and Space labels. A third key is
bound to the Debris Field attribute in map archive member 168, offset 0x84.
The terrain spelling matches Z3's terrain translation. Its source member hash
and 32-byte record geometry are guarded; map parameters and tiles are unchanged.
Eighteen guarded private Unicode converter entries support the tiny Spirit
cells. No new executable instruction helper is needed.

Validation: 223 tests, 222 passed and one optional check skipped. Tests cover
native converter execution, cell indices and pitch, ink bounds, caption
budgets, font-metric guards and byte isolation. Final-artifact checks read
both font pages, all 247 allocated glyphs and advance bytes, the three new
dictionary keys and the sixteen existing layout helpers. The opening and
name-reader checks also remain part of the matched build verification.

Evidence is saved in `work/ui/battle_layout_0.5.9.json` and
`work/ui/startup_0.5.9.json`. The battle report includes the prior status and
link verification and preserves all five original screenshots unchanged under
`work/ui/screenshots/`. These are issue reports, not screenshots of the fix.

Testing image: `work/output/iso/0.5.9/Tengoku-hen-English-0.5.9.iso`.
Size: 5,284,102,144 bytes; SHA-256
`6418570e925c94d54d141b49660545ecd2c4eaf95d79c3c556799b7f941634ef`.
Its adjacent JSON records the final hash and all 82 files verified through
both directory trees, with twelve matched replacement files. Emulator files
and public release assets are unchanged.
