# Screenshot corrections — 0.5.47

Prepared on 2026-10-17 from the complete active translations. Public delivery
must use a verified Retro Trans patch from the original Japanese image or the
exact public 0.5.44 image. The prepared 0.5.45 and 0.5.46 changes are included.
Publication requires explicit consent for 0.5.47.

## Reported behavior and corrections

1. The linked character name Leben becomes **Lowen**, including the full-name
   aliases レーベン・ゲネラール and the game's typo レーベル・ゲネラール.
2. Schran becomes **Schlan**, including Schlan Opel. Glossary expansion supplies
   both spellings to dialogue, Library descriptions and linked-keyword popups.
   Japanese link tokens, record IDs and controls remain unchanged.
   The affected dialogue records are `688:t_3:68`, `688:t_3:70` and
   `688:t_10:22`; all retain their speaker and link controls.
3. The D-Trader purchase message is assembled before drawing. Translating only
   its suffix does not translate the complete mixed string. The added whole-key
   translations cover all 78 Power Part records, using either original Japanese
   or relocated English names. Example: `Buy "Paladium Reactor".` The separate
   `Are you sure?` row and the native Yes/No purchase behavior are preserved.
4. The third and fourth submitted screenshots are identical; one correction
   covers both reports.
5. The map command uses **Sphere Act**, measuring 152.25 pixels at the
   conservative 28-pixel quad against a 208-pixel text budget. The full wording
   in explanatory ability descriptions remains unchanged.

## Choice alignment

All twelve generic question widgets now store explicit English. The grey
`Yes / No` row and colored selected word share measured left origins:

| Text | Left | Right | Quad |
| --- | ---: | ---: | ---: |
| Yes / No | 588.71875 | 690.28125 | 25 |
| Yes | 588.71875 | 631.68750 | 25 |
| No | 655.90625 | 690.28125 | 25 |

The raw native count-centering bit is cleared consistently. Existing colors,
row heights, selection flags, parent transforms and input handling remain.
This also covers the previously unbound grey/Yes variants at 0x8bd24,
0x8bd44, 0x98f84, 0x98fa4 and the grey row at 0x99364. The other seven
question widgets are synchronized to the same coordinates and text.

## Source bindings and verification

- `review47_messages.py` binds the real D-Trader constructor at 0x31720c,
  its TOC pool pointer and its source quote/suffix fragments. The suffix is
  accessed through pool-relative offsets, not a direct pointer.
- Instruction-level execution follows the native constructor through string
  assembly to its two-row confirmation consumer. Only standard allocation and
  copy calls are modeled. All 156 original/translated name paths must match an
  installed English lookup; live item names are retained.
- The real centered-caption renderer measures each complete purchase sentence
  and both native/preloaded Sphere captions in both font modes. These 316
  cases verify English origins and caller-state preservation.
- The complete build decodes all translated output assets. The additional
  verifier compares affected stages and Library members with their 0.5.46
  sources, reads the actual keyword popup, checks native keyword consumers,
  and rejects changes to unrelated UI widget geometry or styles.
- Both font pages, the font archive, mapping and glyph advances are preserved.
  Native no-pilot fallback checks are carried forward.
- Four focused regression tests cover all purchase constructors, source drift,
  both choice states and the five canonical name aliases.

Evidence is recorded in `work/ui/review47_verified_0.5.47.json`; test output is
`work/output/scratch/startup-0.5.47-tests.log`. Reported images are copied into
`work/ui/screenshots/reported-review47-*.png`. Final delivery readiness is
recorded separately in `work/ui/local_release_0.5.47.json`.

Final readback passed for all 156 installed purchase keys, 156 native purchase
constructors, 316 centered captions, 24 choice origins, six native name lookups
and all 4,803 widgets. The three affected Library keyword entries are 129,
136 and 137; all other Library members match 0.5.46. All 572 native keyword
consumer cases and twelve carried no-pilot/live-name cases pass. The complete
regression suite passes 353 tests, with one optional check skipped. Both ISO
trees verify all 82 files. Target SHA-256:
`7d8c0842d2a7f4602c160cf268c359fa62b4ed7e4da9b2d630213a80c4cf5359`.

Official Retro Trans 0.5.4 validated both full-image patch routes. The original
route is 204,182,093 bytes and the exact public 0.5.44 route is 21,388,535 bytes.
Both reconstructed images match the target hash above. All five delivery assets
are sealed in `work/ui/local_release_0.5.47.json`; no release or draft was
created on GitHub.

In-game visual confirmation remains pending. Native execution and archive
readback do not establish a completed RPCS3 visual playtest.
