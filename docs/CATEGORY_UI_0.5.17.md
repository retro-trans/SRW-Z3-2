# Stage, terrain, Spirit targets and stat columns — 0.5.17

This cumulative local test build addresses the five reported screens. It keeps
the original gameplay values, map attributes, movement capabilities and native
row pitch. In-game appearance remains pending the user's emulator testing.

## Category coverage

- Read the executable's actual 52-byte stage records, using its episode number
  and Tengoku title index. Add complete ordinary episode headings for 104
  number/title pairs across 126 stage records, including branching routes and
  episodes 1–62. Existing prologue and chart title handling remains included.
- Catalogue all 128 map attribute members: 1,105 named records and 83 unique
  terrain names. Bind every translation to its original name field and archive
  fingerprint. Preserve the attribute archive byte-for-byte; the display hook
  supplies English. Include the converted digit in Industrial 7.
- Cover all 16 combinations of the Spirit target prefix/suffix enums. Examples:
  One Ally, All Allies, One Foe and Own Team. Defensive combinations such as
  Self Area stay distinct; coverage does not imply each combination is used by
  a playable command. All labels fit the measured 150-unit field with outline
  clearance. Meaning was reviewed by the terrain reviewer.
- Cover all 16 movement flag combinations. Keep each terrain/movement label a
  single 32-unit cell, retaining the four rating columns and absent flags.
- Bind all 19 compiled mission conditions that substitute the default Hibiki
  name. Match complete display strings after substitution. Japanese placeholders
  remain unchanged in scripts and save buffers; custom player names are retained.

Terrain wording follows the Z3 reference and this project's primary glossary.
Space is the short full form used by the shared battle and map caption. The
two shortened debris labels occur in space maps and use Debris Field.

## Readability and spacing

Unit and Pilot Stats use CQB/RNG, SKL/DEF and EVD/HIT. Replace the small badges in
the fixed combined stat widgets with normal outlined letters at a 26-unit quad;
retain their positions and row pitch. Dynamic CQB/RNG labels fit their original
value clearance too. Training uses Train and enlarged one-cell stat labels at a
28-unit quad, removing the colons that
intruded into the separate live value fields. The native training labels have
20-unit pitch and two source cells before the parentheses, so require a
40-unit label budget instead of the wider ordinary stat-column budget.
Rating badges grow from an 11-pixel cap to 16 pixels without changing
their 32-unit advance. Every bound Ki widget explicitly displays Foc (23 widgets)
and the Spirit effect caption remains Eff.

The earlier native fallback pointer repair remains in this build. The observed
stray kanji is not a terrain name to translate: the source attribute catalogue
does not contain that character. Final cumulative verification exercises the
native fallback and the correct terrain/name lookups independently.

## Files and validation

Source-bound English: `work/translation/en/ui/terrain_names.json` and
`work/translation/en/ui/category_layout.json`. Source-free map inventory:
`work/ui/terrain_catalog.json`. Builder: `tools/game_build.py`. Final verifier:
`tools/verify_category_ui.py`, which includes the prior narration and UI checks,
executes every category lookup and measures the final stat columns. Evidence:
`work/ui/category_ui_verified_0.5.17.json`. Reported screenshots are copied under
`work/ui/screenshots` with hashes and the build version; they remain reports of
the earlier appearance, not screenshots of the new build.

Testing image: `work/output/iso/0.5.17/Tengoku-hen-English-0.5.17.iso`.
The retro-trans title footer identifies v0.5.17. The build retains the Retro
Trans Tools-compatible pipeline and all prior translation work. The public
release remains 0.5.2.

The ISO contains 5,284,429,824 bytes. All 82 files were verified through both
directory trees. SHA-256:
`ee3b1069d4e3196e9126821238d44c9426b13c98320e5bf50c70c1b83bde5840`.
The regression suite passed 250 tests with one optional skip; the five category
checks also passed after strengthening the training width assertion.
Final cumulative verification passed all 137 category lookups and the preceding
UI/narration checks. Ordinary episode headings passed all 865 bindings; the ten
revised stat columns fit their measured native fields and preserve value
positions and row pitch. The saved evidence explicitly leaves runtime visual
confirmation pending.
