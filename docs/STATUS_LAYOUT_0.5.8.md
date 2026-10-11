# Save and status screens — 0.5.8

The six reported screens are addressed in a separate local testing build.
The user handles emulator navigation; in-game confirmation is pending.

| Reported screen | Change |
| --- | --- |
| New save confirmation | Translate the separately drawn question to `Create a new save?`; center both lines and the shared Yes / No row, including its colored selection states. |
| Unit Stats | Compact combat-stat and terrain labels; shorten Will, Move, Mob. and Hit to keep the live values clear. Translate the assembled movement types. |
| Pilot Stats | Compact six combat-stat labels and four terrain labels. Insert spaces in constructed full names while retaining native name order. |
| Mech Stats | Shorten labels and the Name caption; compact terrain labels; translate normal and restricted movement types. |
| Weapon Stats: costs | Fit Type, Attr., Power, Range and Hit in their columns; retain the separate CR + T widgets. Shorten requirements, terrain and effect captions. |
| Weapon Stats: types | Fit Cat:, Type:, IFF:, Form:, Attr: and Name before their icons/values. Replace the original Assi sprite with Asst inside its existing rectangle. |

The normal face remains SRW Z3's Rodin Bold. Twelve additional cells follow
Z3's compact terrain/training profile: 11-pixel caps, baseline 20, horizontal
stem dilation and a maximum 28-pixel ink width. The cells retain a 32-unit
advance, which preserves each caller's original pitch and the rating columns.
They read Air, Grd, Wtr, Spc, Und, Only, CQB, RNG, SKL, DEF, EVD and HIT.
No Z3 addresses or allocated font codes are copied.

`tools/status_layout.py` binds 138 widgets to original string and record
fingerprints. These override earlier edits where necessary; the complete
build has 295 relocated text widgets and the existing single numeric-element
move. Original FSSA strings, font metrics, colors, line breaks, numeric values
and terrain-grade positions remain intact. The complete archive is read back
and checked for changes outside the approved fields and appended text.

The movement tables at Tengoku VAs 0x8da518 and 0x8da778 use UTF-8 eight-byte
slots. Three restricted-movement strings use the same compact glyphs.
Twelve private Unicode entries originally mapped to the unsupported-character
square are bound to this build's font allocation. Conversion is checked using
the original converter instructions for every combination of movement flags.
The fixed slot sizes and native movement mechanics are preserved.

The two split save captions receive invisible markers. The drawer-origin
helper removes the marker and compensates for the original Japanese width
used by the caller, using the live font quad. Tests exercise three sizes and
check preserved registers, CR, LR and the link-width origin. Ordinary text
keeps the existing path. The Yes / No gray row and all four selection states
share the measured center at native x=639.5.

Constructed pilot names are translated at display time, after the native join
uses the translated RPW pieces. This inserts a space or replaces the middle
dot with a space. It preserves surname-first and given-first orders, RPW
columns, order flags, join buffers and saved custom names. The final dictionary
checks cover 1,622 save/name keys.

Validation: 219 tests, 218 passed and one optional Capstone check skipped;
six executed save-centering cases; all 16 existing layout helpers;
228 cells on each font page and their advance bytes. Final evidence is in
`work/ui/status_layout_0.5.8.json`, `work/ui/startup_0.5.8.json` and
`work/ui/link_layout_0.5.8.json`. The six original screenshots are copied
unchanged under `work/ui/screenshots/`, with approximate issue bounds in the
status evidence. `work/output/builds/0.5.8/status_font_preview.png` is an
atlas preview, not an in-game result.

The testing image is `work/output/iso/0.5.8/Tengoku-hen-English-0.5.8.iso`.
Its adjacent JSON contains the final image hash and the verification of all
82 files through both directory trees. Keep the matched EBOOT, UI and font
together. Refresh installed game data through RPCS3 before testing if its
cached files came from an earlier build. Emulator files are not modified.
Public release assets are unchanged.
