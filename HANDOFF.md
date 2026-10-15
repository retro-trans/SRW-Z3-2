# Tengoku-hen handoff

## Current candidate — 0.5.44

The latest three screenshots are addressed in `docs/REWARD_MENUS_0.5.44.md`:
Colony Laser capitalization, separate Sub Order reward values, and deployment
command prefixes/upgrade-caption fitting. Use `tools/review44_build.py` and
`tools/verify_review44.py`. Public delivery still requires explicit consent
for this version. The prepared candidate inherits the preceding fixes.

Readback is recorded in `work/ui/review44_verified_0.5.44.json` and delivery
readiness in `work/ui/local_release_0.5.44.json`. The final run has 348 tests:
346 passed, two optional skips. All four focused checks pass, including
twenty selected/preloaded caption cases. Both official Retro Trans 0.5.4
complete-image round trips pass and all five assets are validated. The
original-image patch is 204,181,888 bytes; the 0.5.40 upgrade is 21,351,721
bytes. No GitHub release or draft is created; visual playtesting is pending.

## Previous prepared candidate — 0.5.43

The latest four screenshot corrections are described in
`docs/MAP_UI_0.5.43.md`: mixed-count end-phase centering, Aboard/terrain
components, `A Tenshi` and the compact `Trans-Am` command. The candidate
inherits the prepared 0.5.41/0.5.42 changes. Public testing still uses 0.5.40;
the upgrade patch must target that public image. Each release requires fresh
explicit consent before any GitHub release or draft is created.

The incremental builder is `tools/review43_build.py`; its final readback is
`tools/verify_review43.py`. Fonts, advances, widget geometry and states stay
unchanged. Only the reported stage article is changed in member 598.
See `work/ui/review43_verified_0.5.43.json` and
`work/ui/local_release_0.5.43.json` for final verification/readiness when
recorded. Both are now recorded: 344 regression tests ran (342 passed, two
optional skips), four focused tests passed without skips, and both official
Retro Trans 0.5.4 complete ISO patch round trips passed. All five delivery
assets are validated. The original-image patch is 204,181,528 bytes; the
0.5.40 upgrade is 21,351,215 bytes. Publication and in-game visual testing
remain pending. The following entries are historical.

## Six public screenshot reports — 0.5.19 preparation

See docs/UI_REVIEW_0.5.19.md. Shortened Link labels/replay suffixes, the shared
Library Name label, composed SR reward captions and the baked domination HUD
are source-bound fixes. The earlier mission-name dictionary matches missed a
separate substitution consumer; tools/mission_names.py translates its four
display-value pointers while preserving custom names and saved bytes.

The build/footer version is 0.5.19. The full suite passed 252 tests, with two
optional checks skipped. Both original-ISO and public 0.5.18 upgrade patches
are prepared and passed complete ISO decode round trips. Retro Trans 0.5.4
validated all five assets in work/output/releases/0.5.19/artifacts/.
See work/ui/local_release_0.5.19.json and docs/RELEASE_0.5.19.md. The matched
ISO is 5,284,429,824 bytes, SHA-256
`dde16f0bf9abb363265b765c8dd1a8803809a7cb9272b8b94cf3d51a0a91b65f`.
Build sources: `dbbc05c2e0a0926a836cc47205eb4ada86a4c4ef`.
No GitHub release or draft has been created and no catalog refresh was run.
The user must explicitly consent before creating or publishing this GitHub
release. In-game appearance remains unconfirmed.

## Release consent and new result-screen report

The user explicitly requires consent before creating or publishing any future
GitHub release. Public 0.5.18 was accepted as a one-time exception. Prepare
reviewable fixes and patches locally, then request release consent as the final
step. Public-release testing alone is not authorization to publish.

The new screenshot `codex-clipboard-0808f1c0-c7db-4275-8731-4fafdb8a216c.png`
shows malformed text resembling `1l,` in the result screen's top-left team-name
field, where an earlier screenshot displayed DEM. Do not treat this as a level
or reward value. The exact runtime cause and intended team name are unverified;
no game-code fix or new build has been made for this report.

## Public release delivery and enemy Spirit separator — 0.5.18

The user confirmed that every screenshot is from the public release. Public
0.5.2 did not contain the accumulated local 0.5.3–0.5.17 fixes. Public
0.5.18 now includes those fixes, with verified Retro Trans catalog routes
from the original ISO and public 0.5.2. This preference is recorded in
AGENTS.md. No emulator navigation is needed.

The enemy Spirit rows at 0xa7084 and 0xa70c4 use a slash instead of Luck/Gain.
Allocate U+E01E as a 32-unit slash glyph and replace their unconverted Japanese
slash. Keep all five source bands' slot order and widget geometry unchanged.
`tools.verify_enemy_ui` includes prior category/UI verification, checks the
five bands and executes Daimon Police, Genion and the empty overlay caption
through the installed centered renderer in both modes. Live appearance remains
pending the user's public-release playtest.

Build and full regression checks passed (250 tests, one optional skip). Final
ISO: 5,284,429,824 bytes, SHA-256
`1139b7c2dbe8d7ce0de50e73f5480e2f2f19aff06b053a6855281e3772e34db4`.
Both filesystem trees passed all 82 file checks. Original and 0.5.2 upgrade
patches passed full image round trips. All five hosted assets passed download,
size, checksum and official Retro Trans 0.5.4 validation. The scoped catalog
refresh succeeded in run 38111059033. Actual original and public 0.5.2 ISOs
were recognized by full hash; Automatic Latest chooses 0.5.18 in one patch
for each input. Evidence: `work/ui/public_release_0.5.18.json`.
Release: https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.18.

## Stage, terrain, Spirit targets and stat columns — 0.5.17

Current builder version is 0.5.17. See `docs/CATEGORY_UI_0.5.17.md`.
Use `tools.category_ui` for the source-bound layout plan and complete map/target
families. Ordinary episode headings use the executable's actual stage records,
not the order of title-card textures: 104 number/title variants in 126 records.
Terrain: 83 names, 128 attribute members, 1,105 named occurrences. Spirit targets
have 16 defensive combinations; enum coverage does not establish gameplay use.
Nineteen compiled conditions receive default Hibiki display-name substitutions
without changing script placeholders, custom names or save buffers.

Category layout overrides merge last in `tools.ui_layout_text`. Keep native
positions and row pitch, use 26-unit ordinary combined stat labels and 28-unit
training cells, Train, and no colons in those labels. Training labels fit
within the original two 20-unit cells before the live parentheses; do not use
the wider ordinary stat-column budget there. Compact terrain cells
have a 16-pixel cap and still advance 32 units. All 23 Ki widgets display Foc.
Final cumulative verifier: `tools.verify_category_ui --version 0.5.17`.
Regression: 251 tests, 250 passed and one optional skip. Testing image:
`work/output/iso/0.5.17/Tengoku-hen-English-0.5.17.iso`.
Evidence: `work/ui/category_ui_verified_0.5.17.json`.
ISO: 5,284,429,824 bytes; all 82 files verified through both directory trees.
SHA-256: `ee3b1069d4e3196e9126821238d44c9426b13c98320e5bf50c70c1b83bde5840`.
Appearance remains pending in-game testing; the user handles emulator navigation.

## Complete full-screen narration — 0.5.16

Current builder version is 0.5.16. See `docs/NARRATION_0.5.16.md`.
Use `tools.narration_catalog` for the complete 197-record family rather than
extending the old individual offset lists. It scans all archive members and
checks all 34 narration fingerprints. Member 25 is the separate staff credit
roll. All 189 unique narration captions have English, including 154 additions.
Raw source briefs stay ignored under `work/tengoku/narration_briefs`.
Final cumulative verifier: `tools.verify_narration --version 0.5.16`.
Native narration bytes and timing are unchanged. In-game appearance is pending.
Regression: 246 tests, 245 passed and one optional skip. Testing image:
`work/output/iso/0.5.16/Tengoku-hen-English-0.5.16.iso`.
ISO readback: 82 files in both trees. SHA-256:
`e38ea9bc3bc45f16f0373eda67aaec55dc4f83ef2a00fd55bfc6542ce9bde5fd`.
Narration execution: 197 bindings and 16 centered cases passed. Evidence:
`work/ui/narration_verified_0.5.16.json`.

## Reported UI fixes — 0.5.15

Current builder version is 0.5.15. See `docs/UI_REVIEW_0.5.15.md`.
The native centered fallback must set r0 to the original source pointer after
restoring caller state: the original CP932 draw tail loads r31 from r0.
Stopping a test at the fallback branch misses the stray-kanji defect.
The cumulative verifier is `tools.verify_ui_review --version 0.5.15`.

Level-up uses CQB and ordinary DEF/SKL, EVD/HIT glyphs at 28 px. Other compact
badges retain their existing profiles. Rengoku Link mode 3 is already centered;
keep its native center instead of subtracting half the caption width twice.
The two concluding narration bindings preserve member 27 byte-for-byte.
Settings have compact volume/Remember Sort captions and explicit ON/OFF widgets.

Regression: 244 tests, 243 passed and one optional skip. Evidence:
`work/ui/ui_review_0.5.15.json`. Local testing image:
`work/output/iso/0.5.15/Tengoku-hen-English-0.5.15.iso`.
The user handles emulator navigation; runtime appearance remains unverified.
Public release 0.5.2 remains unchanged.

All 82 files passed readback through both ISO trees. Image size is
5,284,167,680 bytes; SHA-256:
`4f65bed87b05ba45d5e0d9e8d068a9c847fc46dc7d329bd8138b07e368a0e900`.

## Focus terminology and outlined font — 0.5.14

Current builder version is 0.5.14. See `docs/FOCUS_STYLE_0.5.14.md`.
Use Focus for the Ki stat in descriptions, Foc for compact labels. The
separate Spirit command Focus is unchanged. `tools/focus_terminology.py`
applies source-bound terminology updates; `work/glossary/ui_stats.json`
records the user's choice without altering the Spirit glossary schema.

Generated font cells now contain native G8B8 masks: high byte for outer
coverage, low byte for fill, with a two-texel outline. Do not restore the
old RGBA4444 repeated-nibble encoding. The fill raster and advance table
still match Z3 Rodin Bold. Original Lv/SP and all other unallocated cells
must remain unchanged. Spirit Effect is shortened to Eff. at `0x8f864`.

Regression: 241 tests, 240 passed and one optional skip. The cumulative
verifier is `tools.verify_focus_style --version 0.5.14`; it checks every
native Ki label and both final font pages. Runtime appearance remains
pending user navigation. Public release 0.5.2 remains unchanged.

Testing image: `work/output/iso/0.5.14/Tengoku-hen-English-0.5.14.iso`.
Evidence: `work/ui/focus_style_0.5.14.json`. All 82 files were verified
through both ISO trees. Image size is 5,284,167,680 bytes; SHA-256
`08a8c897991644aba1755f0e19e816a6d74944e26d1b06baab186b3c78961a5c`.

## Enemy-fleet narration — 0.5.13

This section describes build 0.5.13. See `docs/FLEET_NARRATION_0.5.13.md`.
`tools/fleet_narration.py` covers two missing rows in source member 27 at
`0x1a4` and `0x1f4`; exact draw-time replacements preserve their fixed records
and timing. The first row uses the existing condensed Rodin alphabet.
The cumulative verifier now executes both final dictionary entries and checks
that member 27 remains byte-identical, alongside all earlier checks.
Runtime confirmation remains pending user navigation.

Testing image: `work/output/iso/0.5.13/Tengoku-hen-English-0.5.13.iso`.
Evidence: `work/ui/briefing_levelup_0.5.13.json`. Regression: 238 tests,
237 passed and one optional skip; 249 matched font cells. All 82 disc files
were verified through both trees. Image size is 5,284,167,680 bytes; SHA-256
`030050b0a79abfd6319982dee999f0fd567a9889db4efad5d8c09047bfbe935a`.

## Date, briefing and level-up — 0.5.12

This section describes build 0.5.12. See `docs/BRIEFING_LEVELUP_0.5.12.md`.
The full-screen date already uses the installed VWF centering helper. Its real
CP932 drawer at `0x149bc`, called at `0x1541c8`, executes with center 640 px
and y=360 in both native style modes. Do not add a second centering shift.

Three missing briefing captions are in AIDDATAPACK member 26, independently
fingerprinted and covered by `tools/briefing_narration.py` / `ui_catalog`.
Draw-time replacement leaves original fixed rows and timing intact. Compact
level-up DEF/SKL at `0x99f04`; blank the shared Score suffix at `0x8f044`.
Existing compact cells, numeric fields and native label order survive.

Final evidence: `work/ui/briefing_levelup_0.5.12.json`. The test image is
`work/output/iso/0.5.12/Tengoku-hen-English-0.5.12.iso`. Runtime confirmation
remains pending user navigation; this is a local testing build, not a release.
Regression: 237 tests, 236 passed and one optional skip. The matched font has
249 cells, including the two additional condensed digits in 34.8%. All 82
ISO files were verified through both directory trees. Image size is
5,284,167,680 bytes; SHA-256
`6aa696d9652603fa8f69c641acff92bf2ad536b8b80ac95f272cf370a64aba32`.

## Intermission, complete linked Library and chart — 0.5.11

This section describes build 0.5.11. See `docs/INTERMISSION_LIBRARY_0.5.11.md`.
The 79 source-bound widget edits shorten and center intermission buttons,
combine Rengoku Link, remove Library caption quotes and clean up the footer.
The linked-term popup had a separate native description table; its 143
keyword IDs now use both translated Library description variants.

Long prose uses checked owned UTF-8 ranges to select its pre-encoded English
pool, avoiding the native converter's fixed local/output buffers. Both callers,
substring offsets and native fallback execute in the verification harness.
Never overwrite the source lookup names or IDs. Keep the special Library
caption mode 0x01; its position correction is awaiting live confirmation.

All 1,013 Library records and 500 native Library display occurrences have
English renderings. Four native chart members now contain English header art;
the two chapter backgrounds read Heavenly Prison and Time of Hell. Full
spaced prologue heading variants cover the chart and intermission composers.
The title uses v0.5.11 and the existing retro-trans credit. Regression: 234
tests, 233 passed, one optional skip. Runtime confirmation remains pending.
Evidence: `work/ui/intermission_library_0.5.11.json`. Testing image:
`work/output/iso/0.5.11/Tengoku-hen-English-0.5.11.iso`, 5,284,167,680 bytes.
All 82 files verified through both directory trees; SHA-256
`91496c15987e8c24efa5b870041f8b7e2e89b05c224e054587eb94fccc383922`.

## English title and credits — 0.5.10

This section describes build 0.5.10. See `docs/TITLE_SCREEN_0.5.10.md` and
`tools/title_screen.py`. The title reads 3rd Super Robot Wars Z: Heavenly
Prison Chapter, with v0.5.10 / github.com/retro-trans in Z3's footer style.
EFFPS3 member 229 uses generated English wordmark/subtitle art, retaining
the native Z and animation geometry. The three animated subtitle cells
contain overlapping windows from the continuous English subtitle.

Preserve `work/ui/textures/assets/title/*-generated.png`: these hash-guarded
local assets are necessary to rebuild and are ignored by Git. Prompts and
provenance are recorded in the title document. The frame preview is a texture
composition, not an in-game screenshot. Regression: 228 tests, 227 passed,
one optional skip. Final evidence is `work/ui/title_screen_0.5.10.json`.
Testing image: `work/output/iso/0.5.10/Tengoku-hen-English-0.5.10.iso`.
Size: 5,284,102,144 bytes; SHA-256
`c5dac335998eeb328fb5bf122b81af3d269bb187e8337294f6653e23166f9807`.
Runtime confirmation remains pending user navigation.

## Battle preview, map popup, result and transformation — 0.5.9

This section describes builder version 0.5.9. See `docs/BATTLE_LAYOUT_0.5.9.md` and
`work/translation/en/ui/battle_layout.json`. The five reported screens use
compact Z3-style captions and eighteen tiny Spirit cells with their original
indices and pitch. Score's separate Units suffix is blank; Fast fits before
Cancel. Debris Field is an exact draw key bound to map member 168's attribute.
Movement types and command centering retain the verified previous fixes.

Testing image: `work/output/iso/0.5.9/Tengoku-hen-English-0.5.9.iso`.
Size: 5,284,102,144 bytes; SHA-256
`6418570e925c94d54d141b49660545ecd2c4eaf95d79c3c556799b7f941634ef`.
Its adjacent JSON contains the image hash and both directory-tree checks.
Regression: 223 tests, 222 passed and one optional skip. The combined layout
has 344 text widgets and one numeric-coordinate edit. Final evidence is in
`work/ui/battle_layout_0.5.9.json` and `work/ui/startup_0.5.9.json`, including
the sixteen existing helpers, eighteen new Spirit cells and all 247 font
cells/advances on each page. Five original screenshots are preserved.
In-game confirmation remains pending; the user handles navigation.

## Save and status screens — 0.5.8

This section describes builder version 0.5.8. See `docs/STATUS_LAYOUT_0.5.8.md` and
`work/translation/en/ui/status_layout.json`. The six new reported screens use
Z3 compact terrain/combat-stat cells and shorter field captions, while keeping
numeric and terrain-grade positions. Two target UTF-8 movement tables and
three restricted-movement labels are translated through private Unicode
converter entries. Pilot full-name spacing is handled by exact display keys,
preserving native name order. The two split new-save lines center through a
marked drawer-origin helper; the shared Yes / No row and its selection states
have matching anchors. Assi becomes Asst within its existing sprite rectangle.

Testing image: `work/output/iso/0.5.8/Tengoku-hen-English-0.5.8.iso`.
Size: 5,284,102,144 bytes; SHA-256
`6cbb61840e1200088507e5674b4aca247eec0772114c220625763d9b5e838134`.
Its adjacent JSON records the final hash and all 82 files checked in both
directory trees. Regression: 219 tests, 218 passed, one optional skip.
Evidence records 295 text-widget edits, 1,622 save/name keys, six save centers,
16 layout helpers and 228 cells/advances on each font page. Six new screenshots
and approximate issue bounds are in `work/ui/status_layout_0.5.8.json`.
The normal Rodin Bold font remains unchanged; the new cells use Z3's tiny
profile. Previous builds remain available. In-game confirmation is pending;
the user handles navigation. Refresh installed game data through RPCS3 if
its cached files differ from this matched build. No emulator files or public
release assets were changed.

## Map, Spirit, report and save-menu layouts — 0.5.7

This section describes builder version 0.5.7. See `docs/MENU_LAYOUT_0.5.7.md` and
`work/translation/en/ui/menu_layout.json`. Captions use proportional centering
for both encodings and font modes; existing CP932 Yes/No anchors keep their
old measurement. Six map-menu lines receive separate measured prefixes.
Settings tabs read Settings 1 / Settings 2; the Spirit-screen tab reads
Abilities. Teams Defeated replaces the long cumulative caption and the team
counter moves 64 native pixels left, with room for three digits. The prologue
heading is translated at its formatter return before widget drawing.
The font remains SRW Z3 Rodin Bold, with three transparent spacing cells added.
Runtime confirmation remains pending user navigation; preceding evidence is
historical and no public release or emulator state is changed.

Final testing ISO: `work/output/iso/0.5.7/Tengoku-hen-English-0.5.7.iso`,
5,284,036,608 bytes; SHA-256
`70b32536eac05b854eb4ae1212a7a5d96d9de5be7906df234ef46c7a29224c64`.
All 82 files verified through both trees. Regression: 213 tests, 212 passed,
one optional check skipped. Final evidence records 16 helpers, 36 caption
centers, six command lines, 214 glyphs per font page and 214 advance cells,
plus 28 opening and 29 name-reader cases. The live team number at element
0xb7fb8 and suffix widget 0x98544 both move left, preserving their gap;
zero through three-digit totals fit the measured background. Larger totals
retain a pending layout check. Final EBOOT SHA-256 is
`cf2759b2354ab18eee490701999265a61d47ee78bbc7bf87d9695b14a6712a06`.
The installed RPCS3 font cache still differs from the build; refresh installed
game data through the emulator before testing. No cache files were modified.

## Links and command captions — 0.5.6

This section describes builder version 0.5.6. See `docs/LINK_LAYOUT_0.5.6.md`.
The five reported paths now use guarded target-specific fixes. Link widths
come from actual drawer pen movement; primary rectangles match both scene and
glossary identity. Speaker names use proportional advances, with native-name
fallback. Only UTF-8 centered captions take the new English centering path;
the CP932 startup anchors remain applicable. All source strings, registration
records and user names retain their identities. Runtime confirmation is pending
user navigation. The font and previous testing builds below are historical.

Verified testing ISO: `work/output/iso/0.5.6/Tengoku-hen-English-0.5.6.iso`,
SHA-256 `4dbb286f5b89b9416dc0e99202fbc6b86d564be7c70cbef6c57d2cf1e4c023c1`.
All 82 files verified through both directory trees. Regression: 207 passed,
one optional check skipped. Final executable checks cover 15 layout helpers,
14 link/menu width cases, both assembled prologue headings, 28 opening hooks
and 29 name-reader cases. Font readback verifies 211 glyphs on each page and
211 advance bytes. Evidence: `work/ui/link_layout_0.5.6.json` and
`work/ui/startup_0.5.6.json`. Other mission descriptions still need the separate
302-byte input/100-byte line audit described in the layout document.
RPCS3's installed font cache was checked read-only and still differs from the
0.5.6 font pack. Refresh Tengoku's installed-data cache before testing this ISO;
no cache or emulator state was changed.

## SRW Z3 font — 0.5.5

This section describes builder version 0.5.5. See `docs/FONT_0.5.5.md` and
`tools/latin_font.py`. The normal Latin glyphs match the reference's Rodin
Bold cap22/base26/dilation0.5 geometry and widths, verified across 95 ASCII
characters. Both target font pages and EBOOT advance data use the same profile.
Source wording remains unchanged; 27 descriptions and five opening lines
use 85% condensed glyphs. Sixteen fingerprint-bound dialogue records use
condensed glyphs (15 at 85%, Sphere list at 80%). Startup wrapping and No
anchors have been regenerated for the new advances. Runtime remains pending
user navigation. Previous build evidence below is historical.

Verified testing ISO: `work/output/iso/0.5.5/Tengoku-hen-English-0.5.5.iso`,
SHA-256 `0569e0ea9e4057d7a0258e777923713c023694cd8389ef6a4e33b7b6adde203a`.
All 82 files verified in both directory trees; 199 tests passed and one skipped.
Final readback verified 211 glyphs on each page and 211 advance bytes, plus
28 opening hooks and 29 name-reader cases. Evidence: `work/ui/startup_0.5.5.json`.
RPCS3's installed `DATA0141.DAT` was checked read-only: it matches 0.5.4's
font pack, not 0.5.5. The user must refresh Tengoku's installed-data cache
before testing the new matched build; no cache or emulator state was changed.

## Startup screenshot fixes — 0.5.4

See `docs/STARTUP_UI_0.5.4.md`. Current `game_build` version is 0.5.4;
source-bound startup layout edits are in `work/ui/startup_layout.json`.
Opening narration adds 28 keys from pristine member 19 (all six pages), with
English in `work/translation/en/ui/expanded/opening.json`. The catalogue now
has 2,527 IDs. Three guarded runtime name getters translate default
Hibiki/Kamishiro for dialogue substitutions without writing save buffers.
The user supplied five actual screenshots, saved under `work/ui/screenshots/`;
post-fix live layout verification is pending user navigation.

Testing ISO: `work/output/iso/0.5.4/Tengoku-hen-English-0.5.4.iso`,
SHA-256 `a019288059acf6f64cb8e1ecf67bdacea39d95397816f24eabaf0333c97df29e`.
All 82 files verified through both trees; 196 tests passed with one skip.
Final-executable execution checked 28 opening keys and 29 name-reader cases,
with read-only name buffers. Evidence: `work/ui/startup_0.5.4.json`.
Stage CPK payload matches 0.5.3 exactly; its SDAT envelope differs on rebuild.

The 0.5.3 section below describes the preceding build and its own evidence.

## Expanded UI — 0.5.3

The user's request to translate all identified UI has reviewed English or an
explicit disposition for all 2,499 catalogue IDs / 4,197 source occurrences.
See `docs/UI_EXPANSION_0.5.3.md`, `work/translation/en/ui/expanded/` and the
three `work/ui/*_review.json` reports. All 541 skill/part descriptions fit the
conservative reference three-line panel budgets with normal VWF.

`game_build` now produces 0.5.3 with source-aware hook inputs, guarded native
UTF-8 dialogs/formatters and context-bound FSSA/SB2T fragments. Keep each
build's matched EBOOT/font/archive set. Public 0.5.2 assets are unchanged.
Local files use `work/output/builds/0.5.3`; runtime remains unverified, and
the user controls emulator navigation.

The testing ISO is `work/output/iso/0.5.3/Tengoku-hen-English-0.5.3.iso`;
both directory trees verified all 82 files. Aggregate evidence and translation
fingerprints are in `work/ui/expansion_0.5.3.json`. Focused/related suites ran
169 tests with one skip and no failures. No deployment or release was performed.

Remaining integration: 23 generated-text occurrences in
`build.json -> executable.runtime_ui.unresolved`. English is saved, but complete
assembly paths are not verified. Some TOC loads point to shared blocks and use
constant offsets; some compiler-generated copies have fixed lengths. Do not
globally patch Japanese fragments or import Jigoku addresses. Exact standalone
hooks do not prove joined text is translated. Keep 11 functional picker grids
and the malformed prototype's review-only disposition. Source inconsistencies
and badge/parent geometry questions are recorded in reviews. Live states need QA.

## Remaining UI comparison — 2026-10-10

The user requested a comparison with current `../SRW Z3`. The 0.5.2 executable
dictionary is not whole-game UI coverage: only executable-resident strings
feed the exact-match hook, and formats/fragments are skipped. Current Jigoku
canonical sources provide broader archive keys and specialized UI repairs.
See `docs/UI_COVERAGE_2026-10-10.md` and
`work/ui/coverage_2026-10-10.json`; reproduce with `tools.ui_coverage`.

Source-level gaps: 463 reference-matched member-0 strings; 97/479 missing keys
in AIDDATAPACK members 5/6; all 151 distinct skill descriptions and 391 of 392 part
description strings; 40 formatted/joined executable strings; one 4,943-byte Sphere
explanation refused by the 4,096-byte hook cap; 99 distinct OS-dialog candidates
excluded. Counts overlap across paths and do not form a total of missing screens.
82 current Jigoku groups / 3,633 records were consulted with file fingerprints;
157 lack extracted source. Reference local changes include unbuilt fixes.

Priority: extend source-aware hook inputs, then intermission/training/status/
parts/deployment/search/D-Trader labels, skill/part descriptions, generated
messages, tutorials/settings and specialized layout/artwork. Preserve target
terminology, full mechanics and source data keys. No translations, game build,
deployment, emulator navigation or release assets changed in this audit.

## Automatic catalog discovery — 2026-10-10

At the user's request, v0.5.2 is now a regular public GitHub release with the
prerelease flag disabled. Playtest limitations remain in the release notes.
Retro Trans's scoped catalog refresh passed:
https://github.com/retro-trans/retro-trans-tools/actions/runs/38052611269
Catalog commit `f7a396b19ea728374543623edb0ae6cd9389b99e` adds the unchanged
verified manifest and patch. Use Refresh catalog, select the matching original
Japanese ISO, and choose Latest. This supersedes earlier manual-only guidance.
Retro Trans 0.5.4 recognized the actual original ISO by size and full hash;
Automatic Latest selects 0.5.2 in one patch. The live Refresh catalog URL
includes this entry. No game binaries or translation inputs changed.

## Public repository — 2026-10-10

The user requested public visibility after the 0.5.2 release. GitHub confirms
`retro-trans/SRW-Z3-2` is public. Release downloads no longer require repository
access. The release remains a playtest prerelease; use manual Apply xdelta.
This instruction supersedes the earlier private-repository requirement.
Game sources and release artifacts are unchanged.

## Fresh-dialogue release 0.5.2 — 2026-10-10

Published private prerelease:
https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.2
The 198,690,589-byte original-to-English patch passes full ISO decode round
trip. All four hosted assets were downloaded and matched by size and SHA-256;
Retro Trans 0.5.4's validator and release reader passed. Game build sources
are commit `5e1f5083ce24b714f35a078627a32955bc44d857`; the release tag targets
`458fd31ee0fe9e3d2bca732e6ba54a3698ffd560`, which adds notes and metadata.
Use manual Apply xdelta after an authorized download. No emulator navigation,
cache removal, deployment or runtime playtest was performed.

The user requested a release with the fresh dialogue retranslation. All 857
fresh slices are promoted into 851 active files, covering 63,553 records. Six
route-choice filenames held disjoint records from different batches; their
fresh records and reports are merged by ID. Previous active inputs
remain in ignored `work/output/retranslation-promotion-0.5.2/prior_active/`;
`work/translation/en/retranslation_promotion_0.5.2.json` records exact hashes.
Historical batch reports describe their original completion state.

Five source-bound long records use the separate condensed alphabet in
`tools/dialogue_layout.py`. English wording and tokens are unchanged; the
eleven-Sphere list now measures three lines. Builder checks include brackets
and exact glyph advances. Runtime readability still needs playtesting.
Build/release evidence belongs under `work/output/` and `docs/RELEASE_0.5.2.md`.
This release targets RPCS3, not physical PS3/Vita.

## Private repository setup — 2026-10-09

Repository: `retro-trans/SRW-Z3-2`, private, administered with `binhlt0402`.
The local project is now a Git working tree on `master`, matching SRW-Z3's
default branch. Keep game data, source-bearing voice inputs and local paths
ignored. `voice_text/` contains source-free backup/review exports; it is not
an active voice build input. See `docs/LOCAL_SOURCE_DATA.md` for fresh-clone
limits and `docs/RETRO_TRANS_RELEASES.md` for future release preparation.
JSON line endings are preserved so recorded translation hashes remain valid.
The synthetic source checks passed 15 tests locally. No translation promotion,
game build, deployment or release is part of repository setup.

## Fresh batch 12 complete — 2026-10-09

Scope: remaining dialogue: ace pilot talks, guidance scenario, and next-episode previews. Six GPT-6.1 Sol / medium agents freshly translated
2,369 records in 31 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
88 source/English rows across all 31 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch12`. Name normalization changed 1
rows; fresh English differs from the prior draft in 2,152 rows. Added 16
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh batch 11 complete — 2026-10-09

Scope: alternate routes: Crowe and Char stage 43, Macross Quarter stages 52-54, despair stage 57. Six GPT-6.1 Sol / medium agents freshly translated
3,019 records in 42 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
120 source/English rows across all 42 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch11`. Name normalization changed 15
rows; fresh English differs from the prior draft in 2,526 rows. Added 18
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh batch 10 complete — 2026-10-09

Scope: alternate routes: Neo Zeon stages 36-40 and Amalgam stages 36-40. Six GPT-6.1 Sol / medium agents freshly translated
6,085 records in 81 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
238 source/English rows across all 81 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch10`. Name normalization changed 7
rows; fresh English differs from the prior draft in 4,877 rows. Added 34
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh batch 9 complete — 2026-10-09

Scope: alternate routes: Sousuke rescue stages 17-22, Left-Behind Sea stages 26-29, and remaining choice D-Traders. Six GPT-6.1 Sol / medium agents freshly translated
5,583 records in 79 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
219 source/English rows across all 79 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch9`. Name normalization changed 9
rows; fresh English differs from the prior draft in 4,553 rows. Added 35
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh batch 8 complete — 2026-10-09

Scope: alternate routes: Blue Earth stages 4-11, Dragons Hive stages 17-20, and associated choices. Six GPT-6.1 Sol / medium agents freshly translated
7,116 records in 98 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
272 source/English rows across all 98 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch8`. Name normalization changed 28
rows; fresh English differs from the prior draft in 5,847 rows. Added 30
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh batch 7 complete — 2026-10-09

Scope: stages 59 through the final stage and all ending scenes (2103-2106d). Six GPT-6.1 Sol / medium agents freshly translated
5,515 records in 70 slices. All structural and measured-fit checks PASS;
no untranslated rows or unknown glossary tokens remain. The coordinator sampled
207 source/English rows across all 70 slices; this was not
a second full independent proofread. Context decisions remain in the reports.

Run: `work/translation/en/retranslation_2026-10-09_batch7`. Name normalization changed 31
rows; fresh English differs from the prior draft in 4,586 rows. Added 18
glossary terms. Prior files and archived copies retain their starting hashes.
See `REVIEW.md`, `review_notes.json`, `coordinator_sampling.json` and `validation.log`.
No promotion, build, deployment or in-game check was performed.

## Fresh retranslation through the end completed - 2026-10-09

All 63,553 player-facing rows are freshly translated across 12 batches. Final coverage, fingerprints, hashes and structural checks audited. One known Sphere-list line in batch5 still requires layout review before build. Drafts are isolated; no promotion/build or in-game check. See docs/FRESH_RETRANSLATION_COMPLETION.md and work/translation/en/retranslation_progress.json.

## Fresh stages 49–58 retranslation complete — 2026-10-09

Run: `work/translation/en/retranslation_2026-10-09_batch6/`. Six GPT-6.1 Sol
agents at medium reasoning completed 6,828 rows in 91 slices, continuing route A:
common 49–51, Getter 52–54, common 55–56, hope 57, common 58 and 2250/2251 choices.
Assignments: 1,102 + 1,185 + 1,120 + 1,113 + 1,121 + 1,187 rows. All structural and measured-fit checks pass,
with no untranslated rows or unknown tokens. Recheck:
`python -m tools.dialogue_retranslate check --batch 6`.

All 91 prior active files and archived copies retain their starting hashes.
Fresh English differs in 5,672 records. Reviewed name normalization
changed 82 rows; pre-normalization drafts remain in `before_name_pass/`.
The glossary has 18 appended terms and 0 existing-term corrections.
See `REVIEW.md`, `review_notes.json`, `glossary_additions.json` and
`coordinator_sampling.json` for exact changes and context decisions.
Coordinator source review sampled 262 records across all 91 slices,
not a second independent full proofread.

No promotion, build, deployment or in-game check was performed. Batch 5's
eleven-Sphere-name overflow remains an unresolved issue before a game build.
Next scope starts at stage 59 and runs through the final stage.

## Fresh stages 39–48 retranslation complete — 2026-10-09

Run: `work/translation/en/retranslation_2026-10-09_batch5/`. Six GPT-6.1 Sol
agents at medium reasoning completed 7,096 records in 95 slices, continuing
route A: Japan Defense 39–40, common 41–42, Shinji 43, common 44–48 and
2240/2241 choices. Assignments: 1,212 + 1,210 + 1,139 + 1,190 + 1,140 + 1,205 rows.
There are no untranslated rows, unknown tokens or structural errors.
Structural checks pass; one known fit issue remains: 604:t_6:4 lists eleven full Sphere names and requires four lines. The strict checker still fails this row; layout must be resolved before promotion or build. Recheck:
`python -m tools.dialogue_retranslate check --batch 5`.

All 95 active prior files and archived copies retain their starting hashes.
Fresh English differs in 5602 records. Reviewed normalization changed 52 rows;
pre-normalization drafts remain in `before_name_pass/`. The glossary has
24 appended terms and 0 existing-term corrections; exact evidence is in
`glossary_additions.json` and
`work/glossary/research/retranslation_batch5_20261009.json`.

Read `REVIEW.md`, `review_notes.json` and `coordinator_sampling.json` for
context decisions, provisional terms and unresolved editorial judgments.
Coordinator source review sampled 270 records across all 95 slices; it was
not a second independent full proofread. Agent meaning fixes preceded names.
No promotion, build, deployment or in-game check was performed.
The next numbered ten-stage scope starts at stage 49.

## Fresh stages 29–38 retranslation complete — 2026-10-07

Run: `work/translation/en/retranslation_2026-10-07_batch4/`. Six GPT-6.1 Sol
agents at medium reasoning completed 5,643 records in 75 slices, continuing
route A: continent 29, common 30–35, Japan Defense 36–38 and 2230/2231 choices.
Assignments: 957 + 940 + 958 + 955 + 915 + 918 rows. Final validation passes with zero
errors, unknown tokens, untranslated rows or measured text-length warnings.
Recheck: `python -m tools.dialogue_retranslate check --batch 4`.

All 75 active previous files and archived copies retain their starting hashes.
Fresh English differs in 4470 rows. Reviewed normalization changed 53 rows;
original outputs before normalization remain in `before_name_pass/`.
The glossary has 24 appended entries and 3 reviewed corrections: Shizuko
Myojin (full/short) and R. Dorothy Wayneright. All other old terms are unchanged.
Exact before/after glossary values are in `glossary_additions.json`, sources in
`work/glossary/research/retranslation_batch4_20261007.json`.

Read `REVIEW.md`, `review_notes.json` and `coordinator_sampling.json` for
context decisions, provisional terms and remaining wordplay/interpretation
questions. Meaning corrections preceded name normalization. Parent meaning
review was sampled; this is not an independent full second proofread.
No promotion, game build, deployment or in-game check was performed.

## Fresh stages 19–28 retranslation complete — 2026-10-07

Run: `work/translation/en/retranslation_2026-10-07_batch3/`. Six GPT-6.1 Sol
agents at medium reasoning completed disjoint assignments of 744, 810, 745, 751,
750 and 809 rows (4,609 records, 63 slices). Route A continues through MQ
19–20, joined MQ/Hive 21–22, common 23–25 and continent 26–28, with 2220/2221.
All six assignments and the final combined draft pass validation with zero
errors, unknown tokens, untranslated rows or measured text-length warnings.
Recheck using `python -m tools.dialogue_retranslate check --batch 3`.

All 63 active prior files and their archived copies retain their starting
hashes; fresh English differs in 3,660 rows. Reviewed name normalization changed
29 rows; original agent outputs remain in `before_name_pass/`. Nineteen glossary
entries were appended and one existing proposed entry, Busupea, was corrected
to Ugly Duo to preserve the insult explained by the adjacent dialogue. All
other existing terms are unchanged. Exact old/new glossary values are recorded
in `glossary_additions.json`; terminology evidence is in
`work/glossary/research/retranslation_batch3_20261007.json`.

Read the run's `REVIEW.md`, `review_notes.json` and `coordinator_sampling.json`
for remaining interpretation questions and sampled meaning checks. In
particular, Daitarn/daring and bamboo/livestock jokes are adaptations requiring
editorial judgment. Coordinator meaning review was sampled, not repeated in
full. Drafts have not been promoted, built, deployed or checked in-game.
The next numbered ten-stage scope starts at stage 29.

## Fresh stages 9–18 retranslation complete — 2026-10-07

Run: `work/translation/en/retranslation_2026-10-07_batch2/`. Six GPT-6.1 Sol
agents at medium reasoning cover 5,802 records in 78 slices, following route A:
Green Earth 9–11, common 12–16, Macross Quarter 17–18, plus 2210/2211 choices.
All six agents finished in two waves: 953, 992, 971, 971, 936 and 979 rows.
The full isolated draft passes validation with zero errors, unknown tokens,
untranslated rows or measured text-length warnings. Recheck with
`python -m tools.dialogue_retranslate check --batch 2`.

All 78 active prior files and their archived copies retain their starting
hashes. The fresh English differs from the prior draft in 4,553 rows. Reviewed
name normalization changed 63 rows; `before_name_pass/` preserves the agents'
outputs. Twenty researched glossary entries were appended without altering
existing entries. Bobby's address to Jeffrey at 201:t_033:0 is excluded from
automatic matching to the character Boss.

Read the run's `REVIEW.md` and `review_notes.json` for context decisions,
retained omissions, proposed terminology and uncertain interpretations.
Research is in `work/glossary/research/retranslation_batch2_20261007.json`.
Coordinator meaning review covered samples and flagged issues, not a second
complete proofread. No fresh output has been promoted, built, deployed or
checked in-game. The next numbered ten-stage scope starts at stage 19.

## Fresh first-ten retranslation complete — 2026-10-07

The user requested six GPT-6.1 Sol translators using medium reasoning. The
scope follows the prior first-ten batch: two prologues, stages 1–8 on the Green
Earth route, and the 2200/2201 route choice (3,888 records, 54 slices).

Run directory: `work/translation/en/retranslation_2026-10-07/`. `manifest.json`
holds six disjoint assignments and exact row IDs/source fingerprints; `prior/`
preserves previous translation files; `drafts/` contains fresh agent outputs.
The translators read Japanese directly with `tools.dialogue_retranslate source`
and are told to translate afresh, overriding old guidance to reuse English.
They use the established glossary/voice conventions and report uncertain calls.

All six gpt-6.1-sol / medium agents finished in two waves: 669, 625, 644,
647, 648 and 655 examined rows. The complete 3,888-row draft passes isolated
validation with zero errors, unknown tokens, untranslated rows or measured
text-length warnings. Run `python -m tools.dialogue_retranslate check` to
recheck it; the isolated checker now fails on overflow or unknown-token warnings.

Reviewed name normalization changed 33 rows. Thirteen terminology entries were
appended without changing existing glossary entries; proposed forms remain
explicitly marked. Sirius at 51:t_1:37 now has a faction token separate from the
Aquarion pilot. Food references use Grilled Trident; Pinion Halberd was confirmed
against a licensed product listing. Research is recorded in
`work/glossary/research/retranslation_first10_20261007.json`.

Read the run's `REVIEW.md` and `review_notes.json` for validation and remaining
interpretation notes. `before_name_pass/` preserves original agent outputs;
all 54 active old translation files still match their starting hashes. No fresh
output has been promoted, built or deployed. Meaning review was sampled by the
coordinator, not independently repeated for every row; in-game layout remains
unchecked. Keep historical build counts below distinct from this fresh pass.

## Repository layout — 2026-09-29

The repo now follows `AGENTS.md`: glossary in `work/glossary/`, UI schemas,
audits and the Jigoku UI reference in `work/ui/`, target text in
`work/translation/en/`, builds and game copies in `work/output/`, outside files
in `incoming/`. The registered game folder remains `work/tengoku/game-ui-0.1.0`.
Older sections below and in `CHANGELOG.md` keep the paths used at the time.
See `README.md` for the full layout.

## Playtest ISO 0.3.0 — stage dialogue 1-10 — 2026-09-30

`work/output/iso/0.3.0/Tengoku-hen-English-0.3.0.iso` (sha256 b2bdfd24…e1c230):
library + Spirit UI + all 3,888 route-A dialogue records of stages 1-10
(2001-2010 incl. the 2200/2201 chapter), 29 stage members, STGZ3OF2.SDAT
re-encrypted v2 and round-trip verified; 82 files verified in both trees. Not
yet run: the dialogue box wrap (30 cells, 3 lines, `$n` budgeted at 144 units)
is measured, not seen. Same RPCS3 INSCO cache caveat as 0.2.0 (ask first).

Dialogue is a first draft: translated per slice, then mechanical passes
(Tessa = "Captain", "Miss Suzune", tokens for 104 literal names, Ledo's accent
hyphen-split). Next: meaning proofreading (BASE_RULES order), then the items
in `work/translation/en/dialogue_proofread_notes.md`, the rank table, and the
user's runtime check. Conventions live in `docs/DIALOGUE_STYLE.md`.

## Test ISO 0.2.0 — 2026-09-30

`work/output/iso/0.2.0/Tengoku-hen-English-0.2.0.iso`: Spirit UI + translated
library, verified by hash through both trees, not yet run. RPCS3 only. Before
the user boots it, the RPCS3 install cache (`BLJS10299_DATA/USRDIR/INSCO`
DATA0014/DATA0141, now holding ui-0.1.1-vwf) must be updated or cleared; ask
first, it is the user's emulator data. See `docs/BUILD_ISO.md`.

## Library status — 2026-09-30

Names settled (all 1,463 have English; sources in `work/glossary/research/`,
decisions in `library_settled.json`), 539 character profiles, meaning
proofreading applied (288 fixes), 1,124 literal names tokenized. `check` OK.
Open: 御使い English (awaiting the user; currently akurasu's "Angel"), a rank
table, stray misspelled literals, builder + font + in-game verification.
Run at most 6 subagents at once (user instruction).

## Library translation draft — 2026-09-29

All 1,013 library entries have draft English in `work/translation/en/library/`
(293 reused from Jigoku, 720 by subagent batches). Read `docs/LIBRARY_STYLE.md`,
`docs/LIBRARY_JIGOKU.md` and `tools/library_text.py`. `check` passes.

Next, in this order (BASE_RULES proofreading order):
1. Settle names: `python -m tools.library_text names` lists 1,108 proposals,
   40 conflicting. Precedence: user-confirmed Jigoku terms, akurasu Z3.2 pages,
   Jigoku glossary, Jigoku shipped English, cited official English. Record each
   decision with its source in `work/glossary/library_settled.json`, then `seed`.
2. Split same-English, different-person terms (ドロシー, ムウ, 黒い太陽,
   シリウス star vs pilot) and add plural/lower-case forms (Beastmen, `|lc`).
3. Meaning proofread by agents; then a script pass that tokenizes names still
   written as literal English (Neo Zeon, Londo Bell and others).
4. Open questions for the user: 時の牢獄 (Jigoku "Prison of Time" vs akurasu
   "Time Prison"), 御使い / テンシ English, keeping Jigoku pronouns for known
   characters when the Japanese has none.
5. Library builder, font/VWF coverage and in-game checks do not exist yet.

Agents found errors in Jigoku's shipped library English (wrong unit names in
pilot 150/153 references, 四天王 token bug, 中破 as heavy damage, and others);
their `report.uncertain` notes list them for back-porting to the Jigoku patch.

## Current VWF build — 2026-09-11

The user requested VWF like `../SRW Z3`. **ui-0.1.1-vwf** is built and applied
to a fresh complete game copy: `work/output/game-ui-0.1.1-vwf`.

- `tools/ui_vwf_build.py` produces a matched EBOOT, RPW_DATA.CPK and TPACKPS3.CPK.
  All 129 reviewed Spirit fields round-trip, using 62 individual Latin glyphs
  and 20 fixed-cell badges. The pool grows 4,696 bytes. Original text, other
  RPW fields, Japanese glyphs and the other 133 font members are preserved.
- `tools/vwf.py` hooks Tengoku's own drawer at VA 0x147dc. A bounded 4,480-cell
  width table and 132-byte stub occupy the verified executable gap; 4,418
  widths retain original spacing. No Jigoku addresses or RAM globals are used.
- `tools/self_elf.py` reconstructs the program ELF following RPCS3 WriteElf.
  All five program HMACs and all allocated sections are verified. The original
  developer ELF's whole-file digest does not match: non-program data is omitted.
  This limitation is explicitly resolved for a local program-ELF test build,
  not claimed as an exact reconstruction or successful runtime test.
- **36 tests passed**, including independent Capstone decoding and execution
  of the stub's proportional, original-width and out-of-range paths, with
  register/CR/caller-memory preservation checks. The font sample was inspected.
  Both archives and all 82 files in the fresh game copy passed hash readback.

**VWF is activated in the existing registered game and installed UI cache.**
The user said “Do it”; read-only process checks confirmed RPCS3 was closed.
`tools/ui_activate.py` was dry-run/reviewed, then applied the three matched
game files and two cache files, with verified backups and hash readback.

- Registered folder: `work/tengoku/game-ui-0.1.0`. Its directory name remains
  unchanged, but its executable, font, text and deployment manifest now carry
  **ui-0.1.1-vwf**. The existing RPCS3 game entry can be launched normally.
- Installed cache: `E:/RPCS3/dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/`;
  `DATA0014.DAT` and `DATA0141.DAT` now match the VWF RPW/font archives.
  Paths were independently discovered and hash-matched in Tengoku.
- Recovery: `work/tengoku/activations/ui-0.1.1-vwf/activation.json` records the
  six verified backups (five binaries plus the prior deployment manifest),
  before/after hashes and successful activation. Restore a complete matched
  set with RPCS3 closed if rollback is needed.

No emulator input, launch, stop, registration change, save change or release
was performed. Navigation belongs to the user. Let the user boot/navigate and
inspect Spirit names, help, badges, longest-name fit and unchanged Japanese
text. Runtime/layout verification remain false. See `docs/UI_VWF.md`.

## Earlier pair-cell game patch — 2026-09-11

The user requested applying the Spirit translations to the game. The first
local patch, **ui-0.1.0**, is built and applied to the complete Tengoku disc copy:

`E:/Projects/SRW Z3 2/work/tengoku/game-ui-0.1.0`

- All 129 reviewed Spirit text fields are encoded; three sentinel fields stay
  original. Only the 129 target pointers and required size fields change in
  RPW; the original string pool and all other record bytes are preserved.
- The pool grows 2,476 bytes. Font pages 1 and 3 receive 296 English pair cells
  selected from 469 independently verified blank/unassigned target cells.
  The remaining 133 font-archive members are unchanged.
- `tools/ui_build.py` builds and independently checks the two archives.
  `tools/ui_deploy.py` creates a fresh game folder, applies them and checks
  all 82 copied files against expected hashes. Both default to dry run.
- **32 tests pass.** Built text decodes back to the reviewed English, all
  unrelated RPW/font bytes pass preservation checks, and the texture preview
  was inspected. This is not in-game visual verification.
- Outputs: `work/output/builds/ui-0.1.0/build.json` and the game folder's
  `ui_patch_manifest.json`. See `docs/UI_BUILD.md` for target executable
  evidence, reproduction commands, archive hashes and limitations.

**The user reports reaching the game; Spirit display and layout remain
unverified.** RPCS3's game registry now points BLJS10299 at the applied folder,
and its running Tengoku window reports approximately 60 FPS. A read-only screen
capture returned a different foreground app, so it provides no Spirit UI
evidence. Ask the user to leave the game foreground on a selected Spirit.

RPCS3 initially ran Jigoku; it later
became idle without agent intervention. The agent opened Add Games, but the
user stopped Computer Use with Escape and said **“let me do the navigation.”**
Leave emulator navigation to the user. The user subsequently registered and
started Tengoku; no game launch, installed-data change, save alteration
or release was performed by the agent. Original EBOOT, ISO, stage/voice data,
Jigoku installation and references remain unchanged.

Next: obtain the user's runtime result, inspect Spirit list/help/badge fit and
the longest name, and audit any reported defect across the affected family.
Do not treat the applied test build as fully validated or close the UI family.

## Earlier UI authoring milestone — 2026-09-11

The first UI text batch is authored: all 42 Spirit commands plus unknown-state
text in the RPW `spirit` table. **132/132 text fields were examined; 129 are
translated and 3 empty-sentinel fields are explicitly preserved.** Names,
descriptions and effect abbreviations keep separate target occurrence bindings.

- `work/translation/en/ui/spirit_commands.json`: reviewed target-bound authoring text.
- `work/glossary/glossary.json`: partial target glossary with 42 Spirit terms only.
  No character, stage or voice identities have been accepted into it.
- `work/ui/schemas/rpw_spirit.json` and `work/ui/spirit_audit.json`: source
  bindings, scoped review counts and explicit unverified rendering states.
- `work/tengoku/ui/spirit_commands/review.md`: readable English review;
  `validated_text.json` beside it is the checked export.
- `python -m tools.ui_spirits check` passes; the suite now has **27 passing tests**.
- Corrected/clarified Bonds' all-allies healing, Fury's abilities/skills and ALL
  penalties, Focus's final rates, Accel's movement duration and healing targets.
- The broader index search reverified 299 matching source spans; 291 remain
  classification candidates beyond eight already-bound source strings. These
  include ordinary dialogue and design notes, not just UI. No whole family is
  marked complete. See `docs/UI_SPIRITS.md` for evidence and limits.

This is authored text, not an applied game patch. Font encoding, widget fit,
compact abbreviations, actual draw consumers and runtime tests remain pending.
The next UI engineering step is to establish those consumers and rendering
support while classifying the related menu/help records. Dialogue and voice
translation remain assigned to other agents; none was translated this session.

## Earlier source pipeline milestone — 2026-09-11

The first local source/archive pipeline is implemented and exercised against
the original Tengoku ISO. See `docs/PIPELINE.md` for commands and evidence.
This is not yet a bootable English build. The sections after this current-state
summary preserve the earlier starter/readiness history and its then-open work.

The primary agent owns ROM hacking, pipeline engineering and UI translation.
Dialogue and voice-line translation effort belongs to other agents. No such
assignments have started; their source bindings and glossary need review first.

Implemented and verified in this session:

- PARAM.SFO was reread and confirms BLJS10299. ISO SHA-256:
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Streamed ISO/Joliet extraction now joins multiple extents and checks paths,
  bounds and output hashes. All 82 logical files were extracted to
  `work/tengoku/source` and read back; a later pass rechecked the ISO and files.
  WP.CPK is correctly joined into 1,580,686,480 bytes.
- Offline SDAT decryption and read-only source inventories: 876 stage members,
  716 NUL-free cp932 members, 66,919 long literals, 283 members with source-comment
  scene hints, 24 RPW chunks / 5,535 string slots, and 143 keyword / 539 pilot /
  331 robot records. No parser failures. Stage/event/speaker bindings remain
  unresolved; these counts are not audited dialogue coverage.
- Generated 1,883 unreviewed glossary candidates and 120,363 mixed-source
  discovery candidates. Of the latter, 4,192 have exact Japanese UI-reference
  matches. This includes non-UI literals and heuristic binary text runs; no
  UI family or display consumer is verified. Inventoried 135 artwork members.
- Eight ITOC archives (2,088 members) rebuilt byte-identically. A 70,052-byte
  synthetic stage-member replacement migrated from DataL to DataH and preserved
  the other 875 payloads. An independent metadata reader verified the outputs.
- All 14 unit tests passed, including broken ISO extents, Lua lexical boundaries,
  archive preservation, multiple DataH migrations and shrinking replacements.
- Added `.gitignore`; there is still no Git metadata. Original/reference files
  remain unchanged, and all extracted/generated game data is under `work/`.

Evidence:

- `work/tengoku/source_manifest.json`: ISO and extracted-file fingerprints.
- `work/tengoku/prepared/inventory_summary.json`: source counts and SDAT tool
  provenance; detailed source inventories and decoded members are alongside it.
- `work/tengoku/verification/verification.json`: archive and growth checks.
  The synthetic growth archive contains test data and must never be deployed.

Next: independent executable/font analysis, verified combined-stage and record
bindings, UI consumer/RPW schema audits, reviewed target glossary, SDAT
re-encryption and an authorized minimal runtime round trip. The CPK reader
currently limits inputs to 64 MiB; larger CPKs were extracted but not unpacked.

Beyond the partial Spirit authoring glossary described above, there is still
no general translation merger, font/VWF patch, RPW writer, voice writer, ISO
packager or deployment pipeline. No dialogue, voice or UI binary patch was
applied. No original ISO, emulator, installed data
or saves changed; no runtime test, deployment or release was performed.

## Historical starter state — 2026-09-11, before pipeline implementation

The user requested transfer of the translation base rules and lessons learned
from Jigoku-hen, followed by the glossary and UI reference material. This folder
now contains the rules, an unchanged 1,141-entry Jigoku glossary reference with
its two source files, and a reference-only UI pack. The UI pack has 27 source
translation files (2,542 stored rows), 29 non-executable code reading references,
five repair notes, a repair map and an empty target audit template.
No active Tengoku glossary/ID map, translation corpus, runnable tools, game data,
executable patches or builds have been installed by these transfers.
No emulator or saves were changed.

Source project: `E:/Projects/SRW Z3`.
Target project: `E:/Projects/SRW Z3 2`.
Original ISO:
`E:/SRWZ3/iso/Dai-3-Ji Super Robot Taisen Z - Tengoku-hen (Japan).iso`.
PARAM.SFO identifies it as **BLJS10299**.

## Read order

- `BASE_RULES.md`: exact copy of the original user rules, not rewritten.
- `docs/Z3_LESSONS.md`: active transferable lessons and translation checks.
- `docs/TENGOKU_PORTING.md`: measured format similarities and differences.
- `docs/reference/JIGOKU_CONVENTIONS.md`: historical detailed terminology
  decisions. Read the active guide's caveats before using any example IDs.
- `AGENTS.md`: makes these documents discoverable to future coding agents.
- `work/glossary/README.md`: usage and legacy-ID warnings for the imported glossary
  at `work/glossary/reference/jigoku_glossary.json`; do not feed it directly to a
  Tengoku build. Preserve identities and match Tengoku's own records first.

## Most important cautions

Read `docs/UI_PORTING_CHECKLIST.md` and `work/ui/reference/jigoku_ui/README.md`
before UI work. The UI pack has not been searched or applied against Tengoku.
Its 17 multiple-English key groups need contextual review, and its row count
does not represent complete coverage in either game. Audit target occurrences,
generated variants and artwork independently; old IDs and patches are not
portable. Historical copied notes may describe superseded Jigoku behavior.

The ISO reader needs multi-extent support before a full extraction: WP.CPK
has two extents that the old extractor would overwrite instead of joining.
Stages now live in one STGZ3OF2.SDAT archive (876 members), not Jigoku's
individual stage files. CPK, Lua, RPW and encyclopedia readers have been
tested on Tengoku sources; executable patches and in-game writes have not.

Jigoku's old in-place-only voice guidance was superseded by a verified
block-rebuilding method there. That does not prove Tengoku's executable
table address, capacity, or buffer behavior. Establish those independently.

## Historical next implementation step

Port safe readers and glossary infrastructure, fix ISO multi-extent handling,
map the combined stage archive, and prove a minimal in-game translation
round trip. Do not start by running Jigoku's build/deploy scripts unchanged.

For UI work, create a target inventory from original Tengoku sources using the
UI checklist. Match reviewed reference wording to verified target occurrences,
then account for new, revised, absent and unresolved entries before replacement.

The technical assessment's probe outputs remain in the source project's
ignored `work/tengoku_probe/` directory. No probe game bytes were transferred.

## Historical readiness review — 2026-09-11, before pipeline implementation

- Read the active project rules, technical assessment, glossary/UI guidance
  and historical conventions. This session prepared context; no implementation
  or target discovery was started.
- Verified SHA-256 hashes for all 3 glossary/source-reference assets and all
  65 UI reference assets against their manifests; checked recorded UI sizes.
  All 34 JSON files parsed, and `BASE_RULES.md` matches the source copy exactly.
- Confirmed 1,141 glossary entries, 2,542 UI reference rows, 17 multiple-English
  groups, 27 translation reference files, 29 implementation reading references
  and 15 repair families. These checks establish reference integrity only.
- The target audit remains empty: all 41 categories are not started and their
  target inventory totals remain unknown.
- Confirmed the original ISO exists at the path above with the documented
  4,888,199,168-byte size. The source project's candidate ISO/CPK/Lua/glossary
  tools, `work/make_npdata.exe`, and both probe reports are present. Existence
  and size checks do not revalidate formats or runtime compatibility.
- This folder has no Git metadata or `.gitignore`. Establish source control
  and generated-data exclusions before adding extraction/build outputs.
- No extraction, writer round trip, build, in-game test, deployment or release
  was performed. Only this handoff and the changelog were updated.
