# Expanded UI translation — 0.5.3

All 2,499 distinct IDs in the source-bound expansion catalogue have reviewed
English/dispositions, covering 4,197 source occurrences. This follows the
0.5.2 comparison with `../SRW Z3`, then independently reads Tengoku's actual
widget pointers, string tables, description columns and executable sources.
Counts include duplicated views, development layouts and inactive menus;
they are not counts of visible screens or proof of whole-game UI coverage.

| Translation file in `work/translation/en/ui/expanded/` | IDs |
| --- | ---: |
| menus.json | 1,295 |
| lua_team.json | 1 |
| help.json | 523 |
| skills.json | 150 |
| parts.json | 391 |
| system.json | 99 |
| generated.json | 40 |

Meaning reviews are in `work/ui/menus_review.json`, `help_review.json` and
`descriptions_review.json`. Existing correct translations remain; new wording
preserves mechanics, numbers, DLC flags, main/sub-unit scope, printf argument
order and named substitution keys. Shinka and Erosion follow established target
terminology; Corrosion is a different skill.

Source-free counts, translation fingerprints, build output hashes and pending
bindings are recorded in `work/ui/expansion_0.5.3.json`. The focused suite passed
66 tests. The related library/dialogue/voice/art/archive/ISO suites ran 103 tests,
with one optional test skipped and no failures. All 12 built file hashes match
the build report. These checks do not replace an in-game playtest.

The local 0.5.3 ISO is 5,284,036,608 bytes; all 82 files pass content checks
through both directory trees. SHA-256:
`8858cd8f7d3496eda0366ad5625ba45ebd25cb3558f6fe7c78d4a4400f3b7303`.

## Implementation

- `tools/ui_catalog.py` adds 2,309 reviewed source keys to the exact draw hook,
  including FSSA, SB2T, UB2T, RPW descriptions and the visible Lua team name.
  Shared single-character fragments are excluded from global replacements.
- `tools/ui_layout_text.py` binds 139 individual FSSA widgets to complete
  labels, blanking sibling word fragments only within reviewed widget bindings.
  It appends 752 bytes to the pool, preserves the original pool and other
  section contents, and relocates header section offsets. Two SB2T fragments
  preserve the inserted count in sortie confirmation.
- `tools/ui_description_layout.py` wraps all 541 description IDs with actual
  VWF advances. Conservative reference budgets are 740/540 pixels at a 28-pixel
  live glyph size, at most three lines. Agents revised 50 overflow rows without
  dropping mechanics. These bounds still need Tengoku screenshots.
- `tools/ui_runtime.py` edits 116 checked native UTF-8 sites and relocates 15
  formatter/reward strings through verified TOC loads. Native system dialogs
  keep real UTF-8; CP932 formatter literals use the matched VWF alphabet.
  Printf argument bytes stay ASCII. Unicode converter cells remain unchanged.
- Tutorial color operands are retained, including the UTF-8 converter's
  operand adjustment. The 4,943-byte English Sphere explanation now passes
  the output gate; source keys remain capped at 4,096 bytes.

The font, executable and archives are built together with the existing fresh
dialogue, library, mission, team-name, voice and artwork translations. Skill
and part description data pointers remain pristine; English is supplied at
draw time.

## Deliberate exceptions and remaining work

Eleven Japanese character-picker grids remain functional input data. One
malformed prototype name-list row is review-only, so invented identities are
not shipped. All 67 split-label IDs have context-bound dispositions; absence
from the global dictionary is intentional.

Twenty-three executable fragment/template occurrences still need bindings to
their assembly consumers. Reviewed English is saved, and standalone draws
are covered where valid, but complete assembled messages are not proved
translated. They include purchase/sale and skill-learning suffixes, upgrade
and scenario-bonus messages, selection suffixes and ability activation clauses.
The duplicate `After clearing Episode %d` template needs consumer evidence
before relocation. Exact addresses/reasons are recorded under
`executable.runtime_ui.unresolved` in the build report. Some are duplicate views;
do not count them as 23 independently visible Japanese screens.

Source inconsistencies are recorded in the reviews, including Decisive Mode's
full/compact Morale thresholds. No speculative mechanic correction is applied.
Runtime geometry, parent visibility, centering and Combine/Solo/Spirit badges
need in-game checks. **No UI family is closed by source/build checks.**
The user handles emulator navigation.

## Reproduce

With configured local source data and bundled Python:

```powershell
python -m unittest tests.test_ui_expansion tests.test_ui_hook tests.test_vwf tests.test_aid_art tests.test_ui_build tests.test_ui_spirits tests.test_rpw_text -q
python -m tools.game_build
python -m tools.game_build --apply
python -m tools.iso_write
python -m tools.iso_write --apply
```

Inspect each preview before `--apply`. Outputs use `work/output/builds/0.5.3`
and `work/output/iso/0.5.3`. This is a local RPCS3 testing build. The public
0.5.2 release is unchanged. A future release still needs the documented
Retro Trans manifest, xdelta and round-trip validation workflow.
