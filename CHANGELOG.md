# Changelog

## Unreleased

- Record the user's release policy: prepare fixes locally, but create or publish a GitHub release only with explicit consent for that release. Acceptance of 0.5.18 is a one-time exception.
- Reported on public 0.5.18: the result screen's team-name field displays malformed text resembling `1l,`. The exact runtime cause and intended team name remain unverified.

## 0.5.19 - 2026-10-12 (prepared; publication requires consent)

- Shorten and align the Link question labels and choices across all six Clears/Chart layouts. Compact the Link Bonus PP header, completion labels and replay multiplication suffix; preserve all separate values.
- Repair the independent mission-condition name substitution routine. Translate the default protagonist's nickname, first name, surname and full name before display; preserve custom names, name order, save bytes and script lookup keys.
- Shorten the Library's shared Full Name caption to Name while retaining complete official names.
- Align the colored SR Point subject with the black earned sentence. Move the bonus-funds/Z-Chip prefix before the unchanged highlighted amount, removing duplicate literal numbers.
- Translate the world-map domination caption to New Earth Empire Control. Preserve the complete digit row, decimal/percent symbols, bar and all animation records.
- Retain prior translations and fixes; update the retro-trans title-screen footer to v0.5.19. Full regression suite: 252 passed, two optional checks skipped (full texture recompression and Capstone execution). Local archive/ISO and Retro Trans patch validation is recorded in the release evidence; in-game visual confirmation remains pending.
- Verify all 82 files through both ISO directory trees, all 34 bound captions and 15 mission-name execution cases. Both original and public 0.5.18 upgrade patches passed complete ISO round trips; Retro Trans 0.5.4 validated all five local assets. Record readiness in `work/ui/local_release_0.5.19.json`. No GitHub release or draft has been created; explicit consent remains required.

## 0.5.18 - 2026-10-11

- Replace the two enemy Spirit bands' leftover Japanese slash with an allocated English slash cell. Preserve all five bands' slot order, flag state, native pitch and geometry; the enemy sequence is Fy / Di An.
- Carry forward the native fallback repair that prevents blank captions drawing stray kanji over map names, and verify Daimon Police, Genion and the blank overlay through the installed centered renderer in both font modes.
- Publish a public release containing the accumulated 0.5.3–0.5.17 translation and layout fixes. The user always tests public releases; local testing images alone did not update the copy they were using.
- Retain full dialogue, narration, stage, terrain, target and library translation work, Focus/Foc terminology and matching outlined fonts. Update the retro-trans title footer to v0.5.18.
- Run 251 regression tests: 250 passed, one optional skip. Verify all 82 files through both ISO directory trees; ISO size 5,284,429,824 bytes, SHA-256 `1139b7c2dbe8d7ce0de50e73f5480e2f2f19aff06b053a6855281e3772e34db4`.
- Publish original and public 0.5.2 upgrade patches after complete ISO round trips. Download and verify all five hosted assets with Retro Trans 0.5.4; refresh the public catalog through the official workflow.
- Verify actual original and public 0.5.2 ISO recognition and one-step Automatic Latest routes to 0.5.18. Record public release evidence in `work/ui/public_release_0.5.18.json`; runtime visual confirmation remains pending.

## 0.5.17 - 2026-10-11

- Translate complete ordinary episode headings using the actual stage number/title table: 104 variants across 126 records, including route branches. Add default Hibiki display-name bindings for all 19 relevant compiled mission conditions.
- Translate all 83 terrain names across 128 map attribute members / 1,105 named records. Retain map parameters and source records; cover digit conversion in Industrial 7 and all 16 movement-flag combinations.
- Translate the assembled Spirit target category, including One Ally, All Allies, One Foe and Own Team; preserve each enum's scope and fit every defensive combination into the native target field.
- Use readable normal stat labels, shorten Training to Train and remove training colons that intruded into live values. Increase terrain badge cap height from 11 to 16 pixels while retaining native cell advance and rating positions. Bind all 23 Ki widgets to Foc and retain outlined Lv/SP-style masks and the native fallback repair.
- Carry forward complete narration, library and dialogue work and the Retro Trans Tools-compatible pipeline. Update the retro-trans title footer to v0.5.17 and prepare a separate testing ISO. In-game appearance remains pending user testing.
- Run 251 regression tests: 250 passed and one optional check skipped.
- Verify all 82 ISO files through both directory trees. Testing image size: 5,284,429,824 bytes; SHA-256: `ee3b1069d4e3196e9126821238d44c9426b13c98320e5bf50c70c1b83bde5840`.
- Final cumulative verification passed, including all 137 category lookups, 865 episode-heading bindings, 23 Foc widgets, stat widths and preserved native value positions. Save evidence in `work/ui/category_ui_verified_0.5.17.json`.

## 0.5.16 - 2026-10-11

- Replace the individual narration offset lists with a complete, fingerprint-bound catalogue of all 34 narration members, including later story introductions. All 197 timed records / 189 unique captions now have reviewed English; add 154 missing unique translations.
- Translate the reported Sidereal introduction, invasion, occupation and Leyline cards. Preserve full meaning, deliberate continuations, page order and timing. Measure every English line and retain all original narration members byte-for-byte.
- Add complete-corpus regression coverage and final executable checks for all narration bindings, plus native centering checks for the four reported cards.
- Carry forward previous fixes, supplementary glossary research and the Retro Trans Tools-compatible build pipeline. Update the retro-trans title footer to v0.5.16. Prepare a separate testing ISO; live appearance remains pending in-game testing.
- Run 246 regression tests: 245 passed and one optional check skipped.
- Verify all 82 ISO files through both directory trees. Testing image size: 5,284,167,680 bytes; SHA-256: `e38ea9bc3bc45f16f0373eda67aaec55dc4f83ef2a00fd55bfc6542ce9bde5fd`.

## 0.5.15 - 2026-10-11

- Repair the centered drawer's native fallback source pointer. Blank captions and native settings no longer draw executable bytes as stray kanji. Verify the installed fallback through the original renderer entry in eight caption/style cases.
- Use CQB on level-up and enlarge DEF/SKL/EVD/HIT with normal outlined glyphs. Preserve numeric positions, row spacing and display state; verify the final Focus skill labels.
- Translate both concluding narration rows, preserving the new battle / battle without end continuation, original archive member and timing.
- Separate Ep and Clear in the intermission footer, correct Rengoku Link's doubled centering offset, shorten settings captions and add explicit ON/OFF bindings. Correct two Focus terms adjoining color controls.
- Carry forward earlier fixes and update the retro-trans title footer to v0.5.15. Run 244 tests: 243 passed and one optional check skipped. Prepare a separate local testing image; in-game appearance remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,167,680 bytes; SHA-256 is `4f65bed87b05ba45d5e0d9e8d068a9c847fc46dc7d329bd8138b07e368a0e900`.

## 0.5.14 - 2026-10-11

- Follow Z3's Focus terminology for the Ki stat: use Foc in compact labels and Focus in descriptions. Update 358 English UI fields, the source-bound Will label overrides and the weapon requirement caption. Preserve the separate Focus Spirit command and ordinary English will.
- Restore native G8B8 font masks: separate the black outline coverage from the letter fill, matching the native Lv/SP treatment. Keep the Z3 Rodin Bold letter shapes, advances and all original font cells unchanged.
- Shorten the crowded Spirit Effect caption to Eff. Preserve numeric positions, native widget geometry and gameplay values. Carry forward all earlier fixes and update the retro-trans title footer to v0.5.14.
- Run 241 tests: 240 passed and one optional check skipped. Prepare a separate local testing image; in-game appearance remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,167,680 bytes; SHA-256 is `08a8c897991644aba1755f0e19e816a6d74944e26d1b06baab186b3c78961a5c`.

## 0.5.13 - 2026-10-11

- Translate the two missing enemy-fleet narration rows: the fleet breaches absolute defense lines on all fronts and descends toward Earth. Preserve the sentence continuation, original timing and complete meaning.
- Bind both draw-time replacements to the fingerprinted AIDDATAPACK member 27. Keep the original archive member byte-identical; reuse the Z3 Rodin font and existing condensed alphabet for the first row.
- Carry forward all earlier fixes and update the retro-trans title footer to v0.5.13. Prepare a separate local testing image; runtime confirmation remains pending user navigation.
- Run 238 tests: 237 passed and one optional check skipped. Execute both translated captions from the final executable, check their widths and confirm the source narration member remains unchanged.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,167,680 bytes; SHA-256 is `030050b0a79abfd6319982dee999f0fd567a9889db4efad5d8c09047bfbe935a`.

## 0.5.12 - 2026-10-11

- Translate all three missing military briefing lines, preserving the 34.8% remaining-strength figure, its comparison with the Earth Federation's founding, the disrupted command structure and the unknown Sidereal information.
- Bind the briefing to AIDDATAPACK member 26; exact draw-time replacements retain the original fixed rows and timing. Use the existing condensed Z3 Rodin alphabet where needed, including two additional digit cells.
- Verify the full-screen date through the actual native centered drawer and installed VWF helper. Both style modes center the complete English caption at x=640, with the original date geometry intact; the earlier centering fix is retained.
- Compact the missing reversed DEF/SKL pair on level-up and remove the shared Score Units suffix. Preserve native label order, numeric fields, font pitch and gameplay values.
- Update the title footer to v0.5.12 with the existing retro-trans credit. Run 237 tests: 236 passed, one optional check skipped. Prepare a separate local testing ISO with all cumulative fixes; runtime confirmation remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,167,680 bytes; SHA-256 is `6aa696d9652603fa8f69c641acff92bf2ad536b8b80ac95f272cf370a64aba32`.

## 0.5.11 - 2026-10-11

- Center intermission buttons and shorten crowded captions to Training, Upgrades, Team Setup and D-Trader. Keep both selection states, native counters and control IDs; use compact Ep / Clear / turns and Ships footer labels, removing separate score and deployment unit suffixes.
- Consolidate the fragmented Rengoku-hen / Link Bonus caption into Rengoku Link. Hide its old suffix widgets and center Options, Network and Library captions. Remove quotation marks from all six Library caption states, preserving their special renderer mode.
- Connect all 143 native keyword descriptors and both description variants to the complete English Library prose. Preserve original lookup names, series, flags and stable IDs. Execute a guarded conversion path for owned prose instead of overflowing the native UTF-16 stack buffer; retain the original converter for other text and wrapped line copies.
- Audit all 1,013 Library records, 5,838 rendered display fields, 2,026 description variants and 500 executable Library display occurrences: no untranslated display fields found. Verify all 286 native keyword description pointers, 572 consumer executions, a substring and fallback cases.
- Translate four native scenario-chart header states and both chapter backgrounds. Add exact spaced prologue headings, quoted stage-title and episode-number bindings. Preserve animation records, atlas descriptors and pixels outside the declared lettering rectangles.
- Update the title footer to v0.5.11 with the existing retro-trans credit and Z3 font. Run 234 tests: 233 passed, one optional check skipped. Save the five reported screenshots and final artifact evidence; in-game confirmation remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,167,680 bytes; SHA-256 is `91496c15987e8c24efa5b870041f8b7e2e89b05c224e054587eb94fccc383922`.

## 0.5.10 - 2026-10-11

- Translate the title to 3rd Super Robot Wars Z: Heavenly Prison Chapter, following Z3's metallic English wordmark and smaller Chapter subtitle. Retain Tengoku's red subtitle outline and native fiery Z.
- Add the version and github.com/retro-trans credit to the title backgrounds, matching Z3's bottom-right placement, outlined white Rodin Bold lettering and font size. Tie the displayed version to the build version.
- Pack both the whole subtitle and its three animated cells; preserve original UVs, animation records, unused atlas gaps, the prompt and unrelated pixels. Bind all edits to Tengoku member 229 and generated artwork hashes.
- Inset the footer on the background with a native ten-percent zoom, preventing clipping throughout its original keyframes.
- Run 228 tests (227 passed, one optional check skipped). Save artwork provenance, packed texture previews, the reported screenshot and final title/version readback evidence. Prepare a separate 0.5.10 testing image; in-game confirmation remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,102,144 bytes; SHA-256 is `c5dac335998eeb328fb5bf122b81af3d269bb187e8337294f6653e23166f9807`.

## 0.5.9 - 2026-10-11

- Follow Z3's compact battle-preview and map-popup labels: Atk., Ctr., Evd., Def., S.D., Rnd., EN, Will, MV, AT/DF and recovery captions. Fit Support, Action and Anim: ON/OFF in the bottom choices.
- Replace five overflowing Spirit-status strings with eighteen two-letter Rodin Bold cells. Preserve native two-byte indices, the slash, 32-unit pitch and individual status-highlight positions.
- Remove the separate Units suffix from battle-result Score; fit Fast before the quick-battle Cancel icon. Keep the native numeric values, controls and transformation mechanics.
- Translate Debris Field through a source-bound map attribute draw key. Retain the verified 0.5.8 movement tables and compact terrain labels.
- Verify 53 battle widget bindings, eight guarded font-metric changes, eighteen private converter entries and three exact draw keys. The combined build reads back 344 text widgets, the existing numeric-coordinate edit, sixteen layout helpers and 247 font cells/advances on each page.
- Run 223 tests (222 passed, one optional check skipped). Preserve five original screenshots and save final-artifact evidence under `work/ui/`. Prepare a separate 0.5.9 testing image with twelve matched files; in-game confirmation remains pending user navigation.
- Verify all 82 files through both ISO directory trees. Testing image size is 5,284,102,144 bytes; SHA-256 is `6418570e925c94d54d141b49660545ecd2c4eaf95d79c3c556799b7f941634ef`.

## 0.5.8 - 2026-10-11

- Translate and center the separately drawn new-save question and its first line. Center the gray Yes / No row and align its four native selection states.
- Adapt Z3's compact Rodin Bold terrain/stat cells to independently verified Tengoku widgets. Preserve native pitch, terrain grades and numeric values; shorten crowded Unit, Pilot, Mech and Weapon Stats captions.
- Translate two UTF-8 movement tables and three restricted-movement strings through twelve guarded private Unicode mappings. Test every combination of movement flags with the native converter instructions.
- Add display-only spaces to constructed pilot full names without changing native name order or saved names. Shorten weapon requirements, effect/type labels and Name captions; replace the truncated Assi sprite with Asst within its original rectangle.
- Run 219 tests (218 passed, one optional check skipped). Read back 1,622 save/name dictionary keys, six save-centering executions, 295 text-widget edits, all 16 layout helpers, and 228 glyph/advance cells on each matched font page.
- Preserve the six reported screenshots and layout evidence under `work/ui/`. Prepare a separate testing ISO with 12 matched replacement files; in-game confirmation remains pending user navigation. Public release assets and emulator files are unchanged.
- Verify all 82 ISO files through both directory trees. Testing image size is 5,284,102,144 bytes; SHA-256 is `6cbb61840e1200088507e5674b4aca247eec0772114c220625763d9b5e838134`.

## 0.5.7 - 2026-10-11

- Center CP932 and UTF-8 captions using the live font quad in both native font modes. Correct Spirit-list names, Spirit/Skills/Abilities tabs and save-destination choices; preserve unknown/native fallbacks and the existing Yes/No selectors.
- Center each of the six map-menu captions independently, preserving blank lines, font size, pitch and selection flags. Add three transparent spacing cells while retaining SRW Z3's Rodin Bold glyph profile.
- Shorten all eight settings-tab states to Settings 1 / Settings 2 and both Spirit-screen ability tabs to Abilities. Use Teams Defeated for the cumulative team statistic and move the live team count 64 pixels left into its background, allowing three digits.
- Bind the translated prologue heading at the native formatter return before the Tactical Situation widget draws it; retain native format fragments, buffer and stage identities.
- Guard target executable spans and widget fingerprints, verify FSSA byte isolation, and add instruction/geometry regression cases. Prepare a separate testing ISO; runtime confirmation remains pending user navigation.
- Move both the separate type-15 team number and its text suffix together; preserve numeric style, values and adjacent kill/loss counters. Verify all 159 text-widget edits and the single numeric-element coordinate without unrelated FSSA changes.
- Run 213 regression tests (212 passed, one optional check skipped), execute 36 caption-centering cases in both font modes and verify six independent map-menu line centers. Read back 214 glyph cells on each font page and all 214 advances; verify 28 opening hooks, 29 name-reader cases and all 16 installed layout helpers.
- Verify all 82 ISO files through both directory trees, with 12 matched replacement files. Final testing ISO SHA-256 is `70b32536eac05b854eb4ae1212a7a5d96d9de5be7906df234ef46c7a29224c64`. Save final evidence in `work/ui/link_layout_0.5.7.json` and `work/ui/startup_0.5.7.json`; public release assets remain unchanged.

## 0.5.6 - 2026-10-10

- Adapt SRW Z3's link geometry fixes to independently verified Tengoku code: use the drawer's actual pen movement for dialogue/backlog link positions and selected backgrounds, and proportional font widths for linked speaker names. Match both scene and glossary identities; preserve link metadata, colors and navigation.
- Translate both assembled prologue headings through exact draw keys, including `Prologue 1: At the End of the Time Prison`, while retaining native title fragments and formatting.
- Fix the reported SR Point explanation overflow: the native splitter has 103-byte slots with only 100 bytes available for text. Preserve the full meaning in three safe lines.
- Center UTF-8 command captions using the live font quad and English advances. Keep the CP932 startup-widget path and its existing anchors. Retain SRW Z3's Rodin Bold font.
- Allocate aligned private link scratch, guard source consumers and verify byte isolation. Prepare a separate local testing build; in-game confirmation remains pending user navigation.
- Run 208 regression tests (207 passed, one optional check skipped). Execute 14 name/command width cases and both assembled prologue keys against the final executable; verify all 15 installed layout helpers and preserve the five reported screenshots with approximate UI bounds in `work/ui/link_layout_0.5.6.json`.
- Verify all 82 ISO files through both directory trees; final font readback checks 211 glyphs on each page and 211 advance bytes, plus 28 opening hooks and 29 name-reader cases. Save matched artifact evidence in `work/ui/startup_0.5.6.json`; testing ISO SHA-256 is `4dbb286f5b89b9416dc0e99202fbc6b86d564be7c70cbef6c57d2cf1e4c023c1`. Other mission text retains a pending byte-limit audit.

## 0.5.5 - 2026-10-10

- Match SRW Z3's Latin font: SCE-PS3-RD-B-LATIN.TTF (Rodin Bold), 22px cap height, baseline 26, 0.5px horizontal stem dilation, four-times supersampling and BOX downsampling. All 95 ASCII coverage cells and advances match the reference raster geometry exactly.
- Rebuild both font pages and the proportional advance table from this shared profile. Keep Tengoku's verified font allocation and executable hooks; add font provenance to the build report.
- Recalculate wrapping and No anchors for the bold advances. Preserve complete wording with 85% condensed glyphs for 27 UI descriptions, five opening narration lines and 15 source-bound dialogue records; the full Sphere list uses 80% width. Other text uses the reference's normal glyph geometry.
- Add reference-font comparison tests and final-artifact atlas/advance readback. Prepare a separate 0.5.5 testing build; previous outputs and public release assets are preserved. In-game appearance remains pending user navigation.
- Verify all 211 allocated glyphs on both built pages and all 211 advance bytes. Run 200 tests (199 passes, one skip), execute 28 opening hooks and 29 name-reader cases, and verify the testing ISO's 82 files through both directory trees. Evidence is saved in `work/ui/startup_0.5.5.json`; the installed RPCS3 font cache still matches 0.5.4 and needs refreshing before testing.

## 0.5.4 - 2026-10-10

- Fix the three startup link-data explanation variants: preserve every word and wrap to five measured VWF lines within the panel. Align the selected No label with its grey background label without changing selector state or input behavior.
- Replace the overlapping naming-screen caption with `Squad:` and move it 16 pixels left, leaving space before the editable name.
- Add all 28 opening narration rows from AIDDATAPACK member 19 to the draw dictionary. Preserve the original six pages, fixed records, timings and backgrounds; reviewed English fits each 900-unit line.
- Translate default Hibiki/Kamishiro names at the verified Tengoku `$n/$f/$l/$F` display getters. Preserve custom names, saved buffers and name order; abbreviate the default surname to `K.` only when a long custom nickname would overflow the 41-byte full-name field.
- Save the five user screenshots, source fingerprints and layout bindings. New tests execute the name-reader instructions, check register/CR preservation and read-only save buffers, guard source drift, and verify layout isolation and complete wrapping. Runtime confirmation of these fixes is pending user navigation; no public release is changed.
- Build and verify all 12 matched files and the testing ISO (82 files in both trees). Run 197 regression tests: 196 passes, one skip. Execute all 28 opening keys and 29 name-reader cases against the final executable; save evidence in `work/ui/startup_0.5.4.json`.

## 0.5.3 - 2026-10-10

- Review the complete 2,499-ID UI expansion catalogue (4,197 source occurrences): menus, tutorial/settings text, skills, parts, native system dialogs, generated messages and the visible Lua team name. Preserve functional input grids and flag one malformed prototype row.
- Add 2,309 source-aware draw keys and context-bind 139 split-label widgets plus two sortie-count fragments. Preserve RPW description pointers and original FSSA strings; verify relocated UI sections and untouched members.
- Wrap 541 descriptions using measured VWF advances and conservative reference panel budgets; revise all 50 overflowing rows without losing effects, conditions or DLC flags. Match Shinka/Erosion terminology to target names.
- Preserve tutorial color controls; allow the full Sphere explanation as relocated output while retaining the 4,096-byte source-key cap. Add guarded native UTF-8 and CP932 formatter patches with payload readback/isolation checks.
- Build and verify all 12 local game files and a 0.5.3 testing ISO (82 files verified through both directory trees); 169 tests run with one skip and no failures. Runtime remains unverified; 23 generated-text occurrences still require assembly consumer bindings. Published 0.5.2 assets remain unchanged.

## 2026-10-10 - Audit remaining UI against current Jigoku

- Compare 82 current canonical reference groups with verified 0.5.2 EBOOT, RPW and UI archive outputs; save source fingerprints, occurrence locators and English reuse candidates without Japanese script dumps.
- Confirm 463 member-0 dictionary gaps, 97/479 gaps in the independently parsed SB2T/UB2T tables, 151 skill and 391 part description gaps, 40 skipped format/fragment strings, one oversized Sphere explanation and 99 distinct excluded OS-dialog candidates. Counts overlap by rendering path.
- Add a read-only audit tool and prioritized UI plan. Game inputs, published patch, build version and emulator state are unchanged.

## 2026-10-10 - Enable Retro Trans Automatic discovery

- Publish v0.5.2 as a regular public GitHub release at the user's request; retain playtest limitations in the notes.
- Refresh Retro Trans's scoped catalog successfully and add Tengoku-hen's verified original-to-0.5.2 route. Update installation instructions; patch bytes and game build are unchanged.

## 2026-10-10 - Public repository

- Make SRW-Z3-2 public at the user's request and update release download instructions. Version 0.5.2 remains an RPCS3 playtest prerelease; game artifacts are unchanged.

## 0.5.2 - 2026-10-10

- Promote all 63,553 fresh dialogue records across 857 slices, preserving the previous active inputs in a local backup and recording exact file hashes.
- Merge six shared route-choice filenames by record ID into 851 active files; reject duplicate or incomplete build coverage.
- Fit five source-bound long records with a separate 85% horizontal VWF alphabet, retaining every word and all eleven Sphere names.
- Match glyph cells, advances, wrapping and encoding; reject rendered speech blocks longer than three lines.
- Publish the first private Tengoku release, v0.5.2, using SRW-Z3's manifest, xdelta, checksums and round-trip validation format. All four hosted assets match the verified local package and pass the Retro Trans 0.5.4 validator and release reader. RPCS3 playtest prerelease; runtime remains unverified.

## 2026-10-09 - Prepare private SRW-Z3-2 repository

- Follow SRW-Z3's source-only approach while retaining this project's layout.
- Add current translation status, source setup, portable configuration and Retro Trans release guidance.
- Preserve voice translations in English-only exports with IDs and fingerprints; keep source-bearing working files local.
- Exclude game data, raw textures, personal configuration and recovery files. Add synthetic fresh-clone checks.
- Repository administration only; no translation promotion, game build, release or version change.

## 2026-10-09 - Complete full fresh dialogue retranslation

- Completed all 63,553 player-facing records across 12 batches; verified exact coverage, source fingerprints, draft hashes and current checks.
- Preserved caption layouts and all five original source-only U+0431 characters; source-glyph tests pass.
- Kept the documented batch5 eleven-Sphere list intact; its four-line layout requires review before build.
- Saved completion evidence and updated handoff. No promotion, build, deployment or release version.

## 2026-10-09 — Complete fresh retranslation batch 12

- Scope: remaining dialogue: ace pilot talks, guidance scenario, and next-episode previews.
- Six GPT-6.1 Sol / medium agents completed 2,369 records in 31 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 16 glossary terms and normalized 1 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 88 rows in all 31 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch12`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 - Late full-name and command corrections; final batch underway

- Corrected three batch4 Element Change rows, including two source-reviewed transfer commands, and normalized both Adnachiel the General occurrences across batches6/11. Exact edits and refreshed hashes retained in audit ledgers. Affected earlier slices pass strict checks.
- Started final batch12: 2,369 ace-talk, guidance and preview rows across31 slices, assigned to six GPT-6.1 Sol / medium translators in concurrency-limited waves. Glossary baseline captured after batch11 closed. No build or deployment.

## 2026-10-09 — Complete fresh retranslation batch 11

- Scope: alternate routes: Crowe and Char stage 43, Macross Quarter stages 52-54, despair stage 57.
- Six GPT-6.1 Sol / medium agents completed 3,019 records in 42 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 18 glossary terms and normalized 15 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 120 rows in all 42 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch11`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 - Carry late Macross terminology into earlier fresh batches

- Updated eight source-reviewed records in batches5,6,9 for Queen of Roses, Fold Wave and Fold Wave System; one Nicola assessment now has the agent-reviewed full subject and verb.
- All six affected slices pass strict checks. Exact before/after edits are in `work/translation/en/late_macross_terms_audit.json`; current manifest hashes refreshed, original snapshots preserved.
- Added a name-normalization guard distinguishing four ordinary lion/machine-shape references from the Macross song Lion.
- Batch11 glossary baseline captured after batch10 completion; researched terms are append-only. No promotion or build.

## 2026-10-09 — Complete fresh retranslation batch 10

- Scope: alternate routes: Neo Zeon stages 36-40 and Amalgam stages 36-40.
- Six GPT-6.1 Sol / medium agents completed 6,085 records in 81 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 34 glossary terms and normalized 7 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 238 rows in all 81 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch10`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 — Begin isolated batch11 drafting

- Started two of the six GPT-6.1 Sol / medium translators on the prepared batch11 source while the last batch10 assignment finishes.
- Batch11 missing terms are queued until batch10 closes and the batch11 glossary baseline is captured. Drafts remain isolated; no promotion or build.

## 2026-10-09 — Consolidate Proto-Ple Twelve alias

- Replaced five previously composed aliases with the exact full glossary token after a six-occurrence source scan. English text and Marida identity are unchanged.
- Saved exact edits in work/translation/en/proto_ple_audit.json and per-run corrections; refreshed hashes and passed strict checks for all five affected slices.

## 2026-10-09 — Consolidate the Skull 1 callsign

- Exact-source scan found five occurrences. Three completed earlier rows now use the full Ozma callsign token; current batch10 and future batch12 owners use the same identity.
- Exact edits and hashes recorded in work/translation/en/skull_one_audit.json and per-run ledgers. All three affected slices pass strict checks.

## 2026-10-09 — Normalize the full Ultimate Coordinator term

- Researched the exact compound and scanned the entire source corpus: three occurrences. Two earlier batch8 rows now use the full glossary token and matching article; the third is in active batch10.
- Exact changes in work/translation/en/ultimate_coordinator_audit.json; both earlier slices pass strict checks. Names remain do-not-touch after this pass.

## 2026-10-09 — Review two earlier settled dialogue subjects

- Source and neighboring-row review confirmed the restored subjects at628:t_1:51 and136:t_102:0. Both Zero references are Lelouch; no identity change.
- Exact corrections are in work/translation/en/final_grammar_repairs_second.json and per-batch ledgers; current hashes refreshed, original snapshots retained. Both affected slices pass strict validation.

## 2026-10-09 — Preserve an original decorative glyph

- Found five source uses of U+0431. Preserve the original code point and CP932 bytes; its appearance has not been verified in-game.
- Added a narrow validator exception requiring the original count, while still rejecting newly introduced or other unsupported Unicode. Five regression tests pass, including the encoder check.
- Restored the one affected completed-batch line (467:t_10:19); its strict check passes. Active and future owners received the remaining four IDs.

## 2026-10-09 — Apply late glossary names to completed batches

- Reviewed and normalized 70 literal name/term references across completed batches 1–8 using the expanded glossary and each row's Japanese source.
- Kept weapon/shout Fire, generic messenger, Mechanical Angel, and Getter Reactor exceptions distinct from unrelated glossary identities.
- Exact changes are recorded in `work/translation/en/final_name_audit.json` and each affected batch's correction ledger. Refreshed current hashes while preserving original snapshots.
- Added a reusable dry-run audit for later glossary additions. No game build or promotion.

## 2026-10-09 — Complete fresh retranslation batch 9

- Scope: alternate routes: Sousuke rescue stages 17-22, Left-Behind Sea stages 26-29, and remaining choice D-Traders.
- Six GPT-6.1 Sol / medium agents completed 5,583 records in 79 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 35 glossary terms and normalized 9 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 219 rows in all 79 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch9`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 — Narrow source review of earlier grammar

- Corrected three previously flagged lines after a translator and coordinator checked their Japanese context: Misato's acknowledgment and two statements about the ancient VOTOMS Overmen.
- Restored complete English clauses and the context-supported plural Overmen identity. Both affected slices pass strict checks.
- Preserved original snapshots; recorded exact edits and refreshed draft hashes. No full second proofread or game build is claimed.

## 2026-10-09 — Prepare remaining route and supplemental batches

- Prepared isolated assignments and preserved 42 prior files for batch 11 (3,019 rows) and 31 for batch 12 (2,369 rows).
- Their glossary baselines will be captured when translation starts, after preceding batch terminology is settled.
- Guarded three earlier weapon/shout uses of Fire from being mistaken for Noin's newly added call sign during name normalization.
- No translation promotion or game build.

## 2026-10-09 — Prepare fresh retranslation batch 10

- Preserved 81 prior slices and prepared six assignments for 6,085 records on the Neo Zeon and Amalgam routes.
- Batch 9 translation and review remain in progress. Batch 10 glossary baseline/additions will follow batch 9 completion; no promotion or build.

## 2026-10-09 — Restore earlier caption layouts

- Audited caption whitespace across completed batches 1-8 and restored 117 captions in batches 1-7 to source field separators and line layout. All 374 completed captions now pass the whitespace audit.
- Retained exact before/after edits in the caption audit and per-batch correction ledgers; refreshed draft hashes. Current strict checks pass apart from the existing batch 5 Sphere-name overflow.

## 2026-10-09 — Research batch 9 terminology

- Added 23 source-checked names and terms after preserving the batch 9 glossary baseline, including Preventer aliases, AS model short forms, arena team names, Brussels, the ELS expansion and ZONE Breaker. Kept VOTOMS Overman distinct from Abnormal Survivor.
- Recorded sources and provisional English decisions in the glossary research file; preserved all existing entries. Coordinator sampling and translator review continue before normalization.
- A cross-batch scan found two earlier VOTOMS references in batches 4/7; normalized them to Overman/Overmen, recorded exact edits and refreshed hashes. Both affected strict checks pass.

## 2026-10-09 — Complete fresh retranslation batch 8

- Scope: alternate routes: Blue Earth stages 4-11, Dragons Hive stages 17-20, and associated choices.
- Six GPT-6.1 Sol / medium agents completed 7,116 records in 98 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 30 glossary terms and normalized 28 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 272 rows in all 98 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch8`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 — Record prior choice-scene coverage gaps

- The batch8 completion audit found 19 fresh source records absent from the preserved prior choice-scene files. The fresh drafts cover them and pass source-bound checks.
- Updated the report generator to count these as newly covered rows and record their exact IDs separately. Prior files and source validation remain unchanged.

## 2026-10-09 — Prepare fresh retranslation batch 9

- Archived 79 prior slices and prepared six assignments for 5,583 dialogue records covering the Sousuke rescue and Left-Behind Sea routes plus remaining choice D-Traders.
- Started the first two GPT-6.1 Sol / medium assignments while batch8 finishes review. Work remains in isolated drafts; no promotion or build.
- Glossary additions for batch9 will begin only after batch8 is finalized and the batch9 glossary baseline is saved.

## 2026-10-09 — Distinguish generic Invaders from the fused boss

- Scanned all fresh and active dialogue references after batch8 identified an ambiguous glossary token. Corrected 39 generic-species references in completed batches2/4/5/6/7; retained boss-specific and nearby ambiguous references for the fused Cowen/Stinger token.
- Visible English is unchanged. Exact edits and refreshed draft hashes are recorded in each affected run and `work/translation/en/invader_identity_audit.json`; original completion counts remain historical.
- Current affected-batch checks pass except the already documented batch5 eleven-Sphere-name layout warning. Active translations, archived prior files and before-normalization backups remain unchanged.

## 2026-10-09 — Start fresh retranslation batch 8

- Prepared 7,116 records in 98 slices for the Blue Earth and Dragon's Hive routes.
- Archived prior drafts and glossary baseline; assigned six GPT-6.1 Sol / medium
  translators in two waves. Fresh translations remain isolated until reviewed.
- Disambiguated Patrick Colasour from Patrick Zala after a corpus scan. Corrected
  three token identities in fresh batches 6/7, preserved visible English and
  archived files, recorded exact corrections and refreshed hashes. Both pass.
- Likewise separated Relena Darlian from her father, correcting three fresh
  references in batches 5/6. Batch 6 passes; batch 5 retains its known Sphere-list
  fit warning. Exact edits are recorded in each run's post-review corrections.

## 2026-10-09 — Complete fresh retranslation batch 7

- Scope: stages 59 through the final stage and all ending scenes (2103-2106d).
- Six GPT-6.1 Sol / medium agents completed 5,515 records in 70 slices;
  all structural/fit checks PASS, zero untranslated rows or unknown tokens.
- Added 18 glossary terms and normalized 31 rows after meaning fixes.
  Preserved prior files and before-normalization drafts; recorded all exact changes.
- Coordinator source sampling covered 207 rows in all 70 slices.
- Saved reports under `work/translation/en/retranslation_2026-10-09_batch7`.
  No promotion/build/release; larger retranslation objective continues.

## 2026-10-09 — Continue fresh retranslation through the end

- Started batch 7: stages 59–final and ending, 5,515 rows in 70 slices,
  with six GPT-6.1 Sol / medium assignments in two waves.
- Preserved the 70 prior drafts and glossary baseline; new drafts stay isolated.
- Added configuration for the remaining alternate-route and bonus-dialogue
  batches 8–12 so the full 63,553-record plan can be freshly retranslated.
- The persistent objective includes all remaining planned dialogue. No promotion,
  build or release version; batch 5's known fit warning remains explicit.

## 2026-10-09 — Complete fresh retranslation of stages 49–58

- Six GPT-6.1 Sol / medium agents freshly translated 6,828 rows in 91 slices,
  continuing route A through Getter 52–54 and hope 57.
- All structural and measured-fit checks pass: no missing source IDs,
  untranslated rows, unknown tokens or overflows in this batch.
- Added 18 researched glossary entries; 0 existing-term corrections.
  Preserved glossary baseline and all 91 prior files with hashes verified.
- Corrected meaning before name normalization; retained fragments, context
  decisions and uncertainties are recorded. Coordinator sampling covered
  262 source/English records across all 91 slices.
- Reviewed normalization changed 82 rows; fresh English differs from the
  prior draft in 5,672 rows. Exact changes, original agent drafts and
  validation are saved under `work/translation/en/retranslation_2026-10-09_batch6/`.
- Added batch 6 source, validation and audit support. No promotion, build,
  deployment or release version. Batch 5's fit warning remains unresolved.

## 2026-10-09 — Complete fresh retranslation of stages 39–48

- Six GPT-6.1 Sol / medium agents freshly translated 7,096 records in 95 slices,
  continuing route A through Japan Defense 39–40, common 41–42, Shinji 43,
  common 44–48 and choices 2240/2241.
- Structural checks pass: zero untranslated rows, missing source IDs,
  unknown tokens or structural errors. 1 measured fit warning remains;
  the strict checker has not been weakened. Preserve all eleven Sphere names
  in 604:t_6:4 and resolve its four-line layout before promotion or build.
- Added 24 researched glossary entries; 0 existing-term corrections.
  Preserved glossary baseline and all 95 prior files, with starting hashes verified.
- Corrected meaning and grammar before name normalization. Saved retained
  omissions, source ambiguities and provisional slang/wordplay judgments.
  Coordinator source sampling covered 270 records across all 95 slices.
- Reviewed name normalization changed 52 rows; fresh English differs from
  the prior draft in 5602 rows. Saved original agent output before normalization,
  exact changes, validation log and review notes under
  `work/translation/en/retranslation_2026-10-09_batch5/`.
- Added batch 5 support to source, validation and audit tools. Drafts remain
  isolated: no promotion, game build, deployment or in-game verification.
  No new release version is issued for this translation-only pass.

## 2026-10-07 — Complete fresh retranslation of stages 29–38

- Six GPT-6.1 Sol / medium agents freshly translated 5,643 records in 75 slices,
  covering route A continent 29, common 30–35, Japan Defense 36–38 and choices.
- Preserved all 75 previous translation files and glossary baseline in
  `work/translation/en/retranslation_2026-10-07_batch4/prior/`. Drafts remain
  isolated. Both active previous files and archived copies match starting hashes.
- All six assignments and final combined checks pass: zero missing/untranslated
  rows, unknown glossary tokens, errors or measured text overflow.
- Added 24 terminology entries and corrected 3 existing name entries: Shizuko
  Myojin full/short and R. Dorothy Wayneright. Research sources and exact old/new
  values are recorded; all other existing glossary entries are unchanged.
- Translators restored missing English subjects/verbs, preserved the direction
  of requests, clarified a death threat and documented wordplay/ambiguities.
  Coordinator source sampling covers 225 records across all 75 slices.
- Final reviewed name normalization changed 53 rows; fresh English differs
  from the previous draft in 4470 rows. Preserved pre-normalization outputs and
  wrote manifest, validation log, review notes and exact row-change audit.
- Added batch 4 support to retranslation/audit helpers. No release version is
  issued: no promotion, build, deployment or in-game verification in this pass.

## 2026-10-07 — Complete fresh retranslation of stages 19–28

- Prepared six GPT-6.1 Sol / medium assignments for 4,609 source-bound records
  in 63 slices. Scope continues route A through Macross Quarter 19–20,
  joined MQ/Hive 21–22, common 23–25 and continent 26–28, including 2220/2221.
- Preserved all 63 previous files and the glossary baseline under
  `work/translation/en/retranslation_2026-10-07_batch3/prior/`; fresh outputs
  are isolated in `drafts/`. Added `--batch 3` to the retranslation helper.
- All six agents finished in two waves: 744 + 810 + 745 + 751 + 750 + 809 =
  4,609 freshly translated rows. Final combined validation passes with zero
  errors, unknown tokens, untranslated rows or measured text-length warnings.
- Added 19 researched glossary entries, including a distinct Feldt Grace
  surname token, Orguss II and full/short Moon Attack forms. Corrected the
  existing proposed Busupea entry to Ugly Duo to preserve the source insult;
  exact before/after values are recorded, and all other old terms are intact.
- Restored omitted English subjects and question auxiliaries in sampled
  complete sentences; kept an unidentified recipient gender-neutral in both
  Shikuu exchanges. Translators documented deliberate fragments, speaker
  variants and wordplay adaptations.
- Reviewed name normalization changed 29 rows (28 term replacements and one
  duplicated article); preserved original agent outputs. Verified all 63 active
  previous files and their archived copies against starting hashes. Fresh
  English differs from the previous draft in 3,660 rows.
- Saved final validation, coordinator edits, research and review notes in the
  batch3 run. No translation promotion, release, build, deployment or in-game
  check; coordinator meaning review was sampled.

## 2026-10-07 — Complete fresh retranslation of stages 9–18

- Continued with six GPT-6.1 Sol / medium assignments, in two waves of three.
  Scope follows route A: Green Earth 9–11, common 12–16, Macross Quarter
  17–18, and 2210/2211 choice scenes: 5,802 records in 78 slices.
- Preserved the 78 prior translation files and their hashes under
  `work/translation/en/retranslation_2026-10-07_batch2/prior/`. New output is
  isolated in `drafts/`; active translation inputs and game builds stay intact.
- Extended `tools/dialogue_retranslate.py` with `--batch 2` for source reading,
  assignments and validation; batch 1 remains the default.
- All six agents completed 953 + 992 + 971 + 971 + 936 + 979 = 5,802 rows.
  Full isolated validation passes with zero errors, unknown glossary tokens,
  untranslated records or measured text-length warnings. The earlier
  3,888-row batch also passes the updated checker.
- Added 20 researched glossary entries without changing existing terms.
  Reviewed name normalization changed 63 rows, including two Valles Marineris
  references; original agent outputs are preserved in `before_name_pass/`.
  Corrected an omitted English subject and excluded Bobby's address to Jeffrey
  at 201:t_033:0 from automatic matching to the character Boss.
- Verified all 78 active prior files and archived copies against their starting
  hashes. Fresh English differs from the prior draft in 4,553 rows. Saved
  final validation, exact coordinator edits and translator review notes in the
  run directory. Meaning review was sampled; in-game layout remains unchecked.
  This is an isolated translation draft, with no release, promotion or build.

## 2026-10-07 — Complete fresh draft of the first ten stages

- User requested six GPT-6.1 Sol agents with medium reasoning. Prepared six
  exclusive assignments covering the existing first-ten play-order scope:
  two prologues, stages 1–8 on Green Earth, and the 2200/2201 choice scenes.
  Exact coverage is 3,888 source-bound records in 54 slices of at most 80 rows.
- Preserved all 54 previous draft files under
  `work/translation/en/retranslation_2026-10-07/prior/`, with SHA-256 recorded
  in the run manifest. Fresh English goes in the sibling `drafts/` directory;
  active translations and game builds remain unchanged during drafting.
- Added `tools/dialogue_retranslate.py` for dry-run assignment preparation,
  source-only reading with neighbouring context, and isolated draft validation
  against exact assigned IDs and fingerprints. It creates no Japanese dumps.
- All six requested GPT-6.1 Sol / medium translators completed their assignments
  in two waves of three: 669 + 625 + 644 + 647 + 648 + 655 = 3,888 rows examined
  and freshly translated. Full isolated validation passes with no errors,
  missing glossary tokens, untranslated records or measured overflow warnings.
  The isolated checker now fails on unknown tokens and text-length warnings.
- Added 13 glossary entries with source evidence and explicit proposed status
  where the English is not settled. Existing glossary entries are unchanged.
  Disambiguated the Sirius faction from the Aquarion pilot; unified the food
  label as Grilled Trident and verified Pinion Halberd against a licensed listing.
- Reviewed name normalization changed 33 fresh-draft rows; preserved agent
  originals in `before_name_pass/` and exact edits in `coordinator_changes.json`.
  All 54 active old files and archived copies still match the starting hashes.
  The run's `REVIEW.md`, `review_notes.json` and `validation.log` record coverage,
  decisions and remaining review points. No promotion, build or release;
  independent full meaning proofreading and in-game layout checks remain future work.

## 2026-10-07 — Unbuilt: two name fixes

- 「ギアスの呪縛」 = "Curse of Geass" (skill, RPW + 2 EBOOT strings). Unleveled skills may use 30 bytes
  (`rpw_text.UNLEVELED_SKILLS`; Jigoku's skill overflow happened at 32 + NUL).
- クエント製センサー = "Quent Sensor" (part, matching glossary クエント = Quent).
- Found while reviewing Jigoku-hen screenshots; the rest of that feedback was for the other project.

## 2026-10-02 — Build 0.5.1: art outside the texture pack, user decisions

- **Test ISO:** `work/output/iso/0.5.1/Tengoku-hen-English-0.5.1.iso` (RPCS3 only, local), sha256
  `cf6bf7f6ae8d12d4c8bba0da28ac73cc2dfb97a3589dda844a1385934872ce3a`. Verified: 82 files through both
  trees, 12 replaced; 179 tests pass (2 skipped). Not booted.
- **New art archives** (`build.json` `extra_art` / `disc_files`; `iso_write` replaces whatever the build lists):
  - **`DATA/ANIME/EFFPS3.CPK`** (`tools/eff_art.py`, `docs/ART_EFFPS3.md`): 95 members.
    - 90 location captions (79 catalog entries).
    - Episode headings "Episode N" / "Final Episode", plus the missing "World Without End" title.
    - Jigoku's berserk banner (byte-identical to its shipped member).
    - The title Library submenu: Robot Library / Character Library / Glossary / Sound Select / Scenario Chart.
    - Members the original stores compressed stay compressed (275 MB).
  - **`DATA/BTLC/CMN.CPK`** (`tools/cmn_art.py`, `docs/ART_CMN.md`):
    - MAXIMUM BREAK lettering: Jigoku's art, with the 9 animation records re-located big-endian in Tengoku.
    - Combo Attack, Counter, Re-Attack, Support Attack, Support Defense. Stored raw.
  - **`DATA/BTLC/OP.CPK`** (`tools/op_art.py`, `docs/ART_OP.md`): 31 opening-demo series captions, named as in
    `rpw_names` series. Stored raw.
  - **`DATA/AIDDATA/AIDDATAPACK.CPK`** (`tools/aid_art.py`, `docs/ART_AIDDATA.md`): 65 member-1 sprite cells.
    - 26 Jigoku cells reused; 35 new ones (Sub Order, Sortie/Locked, Combine, Spirit icons, effect words,
      title/new-game headings).
    - Stored raw.
  - **TPACK map badges:** "Aboard" / "Multi-Action" (`map_badges.json`).
- **User decisions applied:**
  - 尽きぬ水瓶 = "Inexhaustible Water Gourd".
  - 超銀河 = "Super Galaxy" (official): Super Galaxy Gurren Lagann / Dai-Gurren. 28 literal replacements in 16
    files, including voice g134/g165 and the library.
  - 覚醒 stays "Zeal" in menus, with "Awakening" on its title card.
  - `library_text.apply_settled` now needs `user_approved` to change a user-confirmed term.
- **Wording:** "Re-Attack" in the battle label and the weapon-requirement line (was "Attack Again").
- **Pending:** the logo wordmark and 天獄篇 subtitle (new logo art needs approval), Sound Select / Scenario Chart
  header plates, the 作品名 label, the 新地球皇国 支配率 HUD.
- **Runtime checks:**
  - Compressed EFFPS3 / TPACK art: a map intro caption, Episode 1, Episode 10+, the final episode,
    the berserk cut-in, Title > Library.
  - Maximum Break playback (big-endian records).
  - Battle labels.
  - Opening demo captions.
  - D-Trader / effect popups.
- **Install cache:** all outputs differ from 0.5.0. Remove `INSCO/DATA0014.DAT`, `DATA0141.DAT` and `DATA0046.DAT`.

## 2026-10-02 — Build 0.5.0: executable UI text, team names, title cards

- **Test ISO:** `work/output/iso/0.5.0/Tengoku-hen-English-0.5.0.iso` (RPCS3 only, local), sha256
  `1b074c0013d9b5440a779f68227581113353b0cf13a3867b41207b8953ce0fcb`. Verified: 82 files through both
  trees; 123 tests pass (2 skipped). Not booted.
- **Executable UI text** (`tools/eboot_text.py`, `docs/UI_EBOOT.md`):
  - 3,535 distinct strings in English: menus, system and help text, rewards, D-Trader, abilities,
    library, stage titles, BGM titles, date/location cards, default team names, defeat quotes, DLC.
  - Sources: 2,195 reused (project tables first, then Jigoku's exact English); 1,340 from 26 agent briefs.
  - Inventory: `work/tengoku/research/eboot_strings.json`.
- **Draw-time hook** (`tools/ui_hook.py`, `tools/ppc_exec.py`, `docs/UI_HOOK.md`, research
  `work/tengoku/research/eboot_hook.md`):
  - **Site:** a branch at VA 0x141a0, where the cp932 and UTF-8 drawer paths join, to a 93-instruction
    stub after the VWF stub.
  - **Table:** FNV-1a open-addressing table (`UIH1`) at VA 0xF00000, folded into the data LOAD (Jigoku's
    hardware-proven layout). 3,494 entries; 40 format/fragment strings and 1 over-long entry deferred.
  - **UTF-8 keys:** produced by an emulation of the game's converter. It was validated by interpreting
    the real machine code on 4,466 UTF-8 strings (all identical).
  - **Gates:** byte isolation, readback, stub execution in the interpreter, and the SRVC table offset.
  - EBOOT grows to 16.4 MB.
- **Team / squad names** (`tools/squad_text.py`):
  - 296 names, 9,001 literals in 156 stage members, rewritten in place (all within 62 bytes).
  - Research showed they are display-only: teams are identified by number and nothing compares names.
  - Combined rebuild with the mission strings; every literal is read back byte-wise.
- **Textures** (`tools/gtf.py`, `tools/texture_art.py`, `docs/TEXTURES.md`):
  - All 128 Japanese episode title cards re-rendered in English in the original style. The catalog
    `work/translation/en/ui/title_cards.json` takes its English from the stage titles.
  - Jigoku's "AT" support badge reused (pixel-identical source).
  - Art members stored CRILAYLA-compressed (new compressor, round-trip checked); TPACK is 31 MB.
  - `tools/cpk.py` / `cpkpatch.py` / `verify_archives.py` handle archives over 64 MiB.
- **Consistency fixes:**
  - 気力 = "Morale" everywhere (63 reused Jigoku strings and 5 RPW skill names were "Focus"/"Foc").
  - Spirit names as in Tengoku ("Persist", "Wall", "Fighting Spirit"); "ZERO System".
  - Glossary Sphere names; private-use glyphs replaced by ASCII terrain labels.
- **Runtime checks needed:**
  - The hook: boot, menus, help text and UTF-8 labels.
  - Centred and right-aligned labels: they are still measured on the Japanese (phase 2).
  - Formatted messages stay Japanese (phase 3).
  - Compressed title cards and badges: does the game's decompressor accept them?
  - Fit of long help, date and synopsis lines; team names on the map panel.
- **Install cache:** every output differs from 0.4.3 (the font allocation shifted). Remove
  `INSCO/DATA0014.DAT`, `DATA0141.DAT` and `DATA0046.DAT` before testing.

## 2026-10-02 — Build 0.4.3: mission conditions in English

- **Test ISO:** `work/output/iso/0.4.3/Tengoku-hen-English-0.4.3.iso` (RPCS3 only, local), sha256
  `cfcdf589663d40cd9e3e206dcf4babe7d31502aec815e8f4e225eead9ef1cdad`. Verified: 82 files through both
  trees; 78 tests pass (1 skipped). Only STGZ3OF2.SDAT differs from 0.4.2.
- **New `tools/mission_text.py` and `docs/UI_MISSION.md`:**
  - Covers the victory / defeat / SR Point texts in each map script's `OPERATE_TBL` str_tbl: 287 distinct
    strings in 110 stage members, all translated (`work/translation/en/ui/mission.json`).
  - Roles come from `id_tbl` (groups of 8: flag, 3 victory, 3 defeat, SR), never from the wording.
  - Sources: 2 lines from Jigoku's hook, 285 from 5 agent briefs.
- **Runtime placeholders kept verbatim** (EBOOT table at 0x9E1198): 主人公フルネーム, ヒビキＡ,
  ヒビキＮ, カミシロＮ (the protagonist's changeable name, like `$n` in the story) and
  ローカルワーク０-２ (per-map counters). The checker enforces their count.
- **Build:**
  - Tokens are expanded and each paragraph is wrapped to 38 full-width cells.
  - The Lua literal is written byte-wise (`
`, 0x5C doubled).
  - Each member is read back; `id_tbl` and all bytes outside str_tbl stay unchanged.
  - 282 of 287 strings fit in the Japanese line count or fewer; 5 need one or two extra lines.
- **Harmonized wording:** "Turn N begins.", "by turn N's Player Phase", "Defeat all enemies.",
  "X is shot down." (defeat).
- **Not in scope:** team/squad names (TOUROKU / ENEMY_TBL / SC_ calls). They double as IDs; Jigoku
  translated them only at draw time.
- **Runtime untested:** the mission panel width and line count, and placeholder substitution inside
  English text.

## 2026-10-02 — Build 0.4.2: RPW name tables in English

- **Test ISO:** `work/output/iso/0.4.2/Tengoku-hen-English-0.4.2.iso` (RPCS3 only, local, not
  published), sha256 `57e1df433c59b9977a4f80b9aa1de85c1a3061976382aa204fe486f52cc15c92`. Verified:
  82 files through both trees; 74 tests pass (1 skipped).
- **New `tools/rpw_text.py` and `docs/UI_RPW.md`:** a verified pointer schema for the RPW name columns,
  covering:
  - pilot display / family / given names
  - robot short and full names
  - weapon short and full names
  - skill names, part names, series titles and shoot-down quotes
  
  This is 3,041 distinct strings in 11,472 cells; all now have English (`work/translation/en/ui/rpw_names.json`).
  - Reused: the glossary (pilot names split from glossary full names, record by record) and Jigoku's
    weapons/skills/parts/enemy_names/name_pieces tables.
  - New: 13 agent briefs (`work/tengoku/rpw_briefs/`, answers in `work/translation/en/ui/rpw_new/`).
- **Build:** `game_build` appends the English after the j-string pool and repoints only schema cells
  plus the Spirit cells, then reads every pointer back and checks that all other bytes are unchanged.
- **Out of scope:**
  - Skill and part descriptions: in Jigoku, part descriptions corrupted memory at boot.
  - Debug-only labels (パ・/ロ・, p-debug/r-debug).
- **Limits enforced:**
  - Display name 15 characters (Jigoku's 31-byte battle speaker overflow).
  - Skill names 13 characters (32-byte level-up slot).
  - Part names fit within the largest original boost-p record.
  - Robot/weapon short names 15/18 characters.
- **Consistency fixes:** 無限拳 family = "Infinity Punch" (not Jigoku's "Mugen Attack"), イナズマキック
  family = "Lightning Kick", 神来無限掌 = "Divine Infinity Palm", サスマタコレダー = "Sasumata Collider"
  (voice g195 aligned), 拡散構造相転移砲 = "Spread Phase-Shift Cannon" (voice g159 aligned), story
  "Miracle Triple Lightning Kick" (dlg_2099). Angel unit names drop the leading "the".
- **Runtime untested:**
  - Name fit on each screen.
  - Shoot-down quotes up to 143 bytes (original max 71; Jigoku never changed them).
  - Whether any other native buffer limits these names.
- **Before testing:** remove `INSCO/DATA0014.DAT` (RPW) and `DATA0046.DAT` (SRVC) from the RPCS3 install
  cache. The font (`DATA0141`) is unchanged from 0.4.1.

## 2026-10-02 — Build 0.4.1: battle voice in the game

- Test ISO `work/output/iso/0.4.1/Tengoku-hen-English-0.4.1.iso` (RPCS3 only,
  local, not published), sha256 `cb00aa05a1ed240b4aadf7f0006089a154108df2188b7d21ef8014fb1bcc75c6`.
  Verified: 82 files hashed through both trees; 69 tests pass (1 skipped).
- New `tools/voice_build.py`; `game_build` now rebuilds `DATA/BTLC/SRVC.BIN`
  with all 48,143 translated battle-voice strings (283 of 368 blocks edited)
  and rewrites the EBOOT block table after the VWF patch; `iso_write` carries
  SRVC.BIN. Independent readback (`srvc_check`) clean.
- SRVC.BIN 3,499,808 -> 4,946,576 bytes. Blocks 217 (Hibiki), 275 (Rand),
  295 (Ledo), 336 (Sousuke) are larger than any original block (up to 76,048 B
  vs 54,016 B): test those voice sets first in case the game caps block size.
- Every output differs from 0.4.0 (font allocation included), so the RPCS3
  install cache `INSCO/DATA0014.DAT`, `DATA0141.DAT` and `DATA0046.DAT` must be
  removed before testing.

## 2026-10-02 — Battle voice: all lines translated

- New `voice.py export` / `merge` and agent briefs (`work/tengoku/voice_briefs/`,
  302 briefs of up to 80 rows); answers in `work/translation/en/voice_new/`.
  All 302 briefs done and merged: 48,143 / 48,143 battle-voice block strings
  now have English (21,254 fresh, the rest reused from Jigoku). `voice check`
  OK; 69 tests pass (1 skipped).
- Speakers settled for 203 voice sets from the lines themselves; 112 differ
  from Jigoku's guess (e.g. g083 Garrod, g092 Girtar, g103 Clouseau, g106 Crowe,
  g117 Code: Blue, g118 Code: White, g158 Setsuko, g168 Chiko, g213 Heero,
  g179 Traia/AG, g292-g295 Ledo/Chamber). Jigoku's guess kept as `jigoku_token`.
- Reviewer fixes by hand to awkward or mistranslated lines, and project-wide
  consistency passes: 可能性 = "possibility", 強化人間 = "enhanced human",
  アホウドリ = "Dumbatross", Spirit Commands as in the story ('Gain', 'Vigor',
  'Alert', 'Persist', 'Valor'), the four-phrase refrain wording, "Invincible
  Robot(s)", Duo's 死神 = "Death", ZERO System = "ZERO", game title 'SRW Z3:
  Tengoku-hen', no "Lady"/"-chan"/"Senpai" where the story drops them.
- Glossary: Reccoa (レコア, proposed).
- Not yet built into the game. 695 segments exceed 36 characters (mostly long
  cut-in and suspend-screen lines with no break in the Japanese); they wait
  for the in-game width test. 497 Jigoku conflict rows still to review.

## 2026-10-01 — Battle voice: Jigoku English reused

- New `tools/voice.py` (`reuse`, `check`). 26,889 of 48,143 battle-voice block
  strings (56%) now have English from Jigoku-hen's shipped voice translation,
  in `work/translation/en/voice/` (228 voice-set groups); 21,254 remain for
  fresh translation. Same-speaker versions preferred where Jigoku had several;
  497 conflicts flagged for review. Names turned into glossary tokens (3,946)
  and Jigoku-only spellings fixed (Ryoma -> Ryouma, Koji -> Kouji, Shin ->
  Shinn, Zanbanya -> Zabanya). `check` OK. Not yet built into the game.

## 2026-10-01 — Battle voice (SRVC.BIN) phase 1: format, executable table, writer

- No translation, build or deployment; nothing ran in the game. Details and
  evidence: `docs/BATTLE_VOICE.md`.
- `tools/srvc.py prepare --apply` puts the pristine SRVC.BIN (3,499,808 B) and
  the reconstructed program ELF in `work/tengoku/prepared/`. The parser walks
  all 368 blocks as the game's parser (VA 0x1390fc) does: 283 with text,
  78,302 line references, 37,187 distinct strings; a no-op rebuild is
  byte-identical.
- Executable block table found from the code, not by integer matching: one
  TOC slot (r2-0x5b54) loaded once at 0x143574, start read 0x1390a0, partial
  read 0x13c164 (offset tab[id], length tab[id+1]-tab[id]). Table at file
  0x9db0a0 / VA 0x9eb0a0: 369 be32 entries = 368 blocks + end sentinel,
  agreeing block for block with the 368-header scan. No other consumer; the
  HDD install list (`DATA0046.DAT`) has no size. Jigoku's 0x830be0 / 276 are
  not used.
- Binding: every line is reached through exactly one of 74 situation slots
  (labels proposed from content; weapon call-outs in slots 35-52) and one
  rule (condition, weight). Speaker leads per block from Jigoku identity
  transfer (155 blocks with >= 50% shared lines, 121 resolved to glossary
  tokens), weapon names and spoken names; 242 voice-set groups.
- Translation memory vs Jigoku's shipped English: 20,193 of 37,186 distinct
  strings (42,598 of 78,136 references) have an exact Japanese match; 16,993
  distinct strings (35,538 references) need fresh translation; 2,047 matches
  carry conflicting Jigoku English.
- Writer `tools/voice_write.py`: growable pools, same block order/headers,
  rewrites only the table bytes in the executable, then the independent
  `tools/srvc_check.py` readback must pass. Synthetic scratch test: 283
  blocks edited, 254 grown, readback clean. New `tests/test_srvc.py`
  (16 tests); 69 tests pass (1 skipped).
- Open: runtime block-size tolerance (English estimate ~76 KB largest block
  vs 54,016 B original), battle font/encoding path, battle text width
  (unknown), not yet wired into `game_build.py`.

## 2026-10-01 — 0.4.0 playtest ISO: all stage dialogue

- `work/output/builds/0.4.0` + `work/output/iso/0.4.0/Tengoku-hen-English-0.4.0.iso`
  built and verified (82 files through both trees; sha256 de9ac80b…ca56):
  63,553 dialogue records in 281 rebuilt stage members, plus the 0.3.0 Spirit
  UI and library. Runtime not yet verified.
- **Archive fix:** with every stage translated, 54 more STGZ3OF2 members
  outgrew the 16-bit ITOC size columns. Each move to CpkItocH grows the ITOC by
  4 bytes, and the original archive has only 40 bytes before ContentOffset, so
  the first full build stopped ("ITOC would overrun ContentOffset moving id
  207"). `tools/cpkpatch.py` now moves ContentOffset forward (16-aligned, here
  by 176 bytes to 8096) when the ITOC needs the room; ITOC has no FileOffset, so
  readers place members from ContentOffset. `tools/verify_archives.py` accepts
  that move only when the ITOC needs it and the gap is zero-filled. New test
  `test_migration_moves_content_offset_when_padding_is_short` (53 tests pass).
  Independent check: 876 members, 281 replaced read back exactly, 595 untouched
  byte-identical. The stage archive grows from 5.7 MB to 20 MB because
  replacements are stored uncompressed.

## 2026-10-01 — Dialogue batch 12 (ace talks, guidance scenario, previews) translated — all dialogue done

- 2500 ace pilot talks, 2600 guidance scenario and 2700 next-episode / quit
  skits: 2,369 records in 31 slices. All stage dialogue is now translated:
  63,553 / 63,553 records, `check` OK (one known TOO LONG: 604:t_6:4, the
  eleven-Sphere list, which cannot be shortened without dropping names), 52
  tests OK (1 skipped), build dry run OK (281 stage members rebuilt).
- New proposed names: Amano, Rashid, Nene, Ralamia, Gunmarl.
- Settled: game title 『第３次スーパーロボット大戦Ｚ』 = '3rd Super Robot Wars Z'
  ('... Tengoku-hen' / 'Jigoku-hen'); スパロボ = "SRW"; ace-talk opener "Happy
  Ace Pilot! Congratulations, Mr./Miss X!"; preview closer "Next time on '3rd
  Super Robot Wars Z', 'TITLE'"; AG's heart glyph = "~"; Spirit Commands in
  speech use the Jigoku UI names (Valor, Alert, Strike, Gain, Vigor ...).
- Preview titles: The Forbidden Tag Team, The Stolen Earth, The Golden Galaxy,
  Song of the Distant Galaxy, Purgatory!! The Endless Battle!, Save the Earth!
  Young President!, Blast Away the Recession and the Enemies!, Sortie! Tetsujin
  and the Super Robot Army!, Long Live SRW, A Miracle Worth 12,000 Years.
- Consistency passes: 14 repeated lines harmonized, 5 heart/placeholder/title
  fixes, 56 literal names tokenized in 17 files (Aquarion's "Mars"/"Luna"
  Vector halves kept plain).
- Open questions: `work/translation/en/dialogue_proofread_notes.md` (batch 12).

## 2026-10-01 — Dialogue batch 11 (Crowe, Char, Macross Quarter and despair branches) translated

- Crowe route stage 43 (2082a/b), Char route stage 43 (2083), Macross Quarter /
  Vajra route stages 52-54 (2095-2097) and despair route stage 57 (2101a/b):
  3,019 records in 43 slices. Every story stage file is now translated: total
  61,184 records, `check` OK (still one TOO LONG: 604:t_6:4), 52 tests OK
  (1 skipped), build dry run OK (277 stage members rebuilt).
- New proposed names: Howard Glass; generic speaker N.U.N.S. Soldier.
- Settled: 新統合軍 = "N.U.N.S."; 銀河殴り込み艦隊 = "Galactic Raid Fleet";
  Mikage's epithets 若草色の髪の少女 = "girl with the spring-green hair",
  薄紅と金の髪の少女 = "girl with the pale pink and gold hair", 暗黒の翼 = "Wings
  of Darkness" (route-A 2026 rows aligned); 機械天使 = "Mechanical Angel".
- Consistency passes: 43 repeated lines harmonized, 10 Mikage epithet rows
  unified, 115 literal names tokenized in 30 files (Bobby's "Boss" for Jeffrey
  kept plain).
- Open questions: `work/translation/en/dialogue_proofread_notes.md` (batch 11).

## 2026-10-01 — Dialogue batch 10 (Neo Zeon and Amalgam branches) translated

- Neo Zeon route stages 36-40 (2069-2073) and Amalgam route stages 36-40
  (2074-2078): 6,085 records in 80 slices. Total 58,165 records, `check` OK
  (still one TOO LONG: 604:t_6:4), 52 tests OK (1 skipped), build dry run OK
  (261 stage members rebuilt).
- New proposed names: Harute, Katagiri, Trans-Am, Tallgeese, Gwadan, Monad,
  Bani Moraut / Bani, Dmitri Varov / Varov, Shin Getter Robo, Psycho-Field,
  Edward Sachs, Ed Bruiser Sachs; generic speaker Cardinal.
- Settled for these branches: ミネバ様 = "Lady $$ミネバ$$", 姫様 = "Princess";
  Neo Zeon 大佐 = "Colonel", Tessa's 大佐 = "Captain"; ハマーン閣下 = "Your/Her
  Excellency"; Marida's マスター = "Master"; ミスタ・Ａｇ/Ｋ = "Mr. Ag/K";
  法王 = "Pope", マーティアル教団 = "the Martial Church"; Pinion's 親方 for Sachs
  = "Boss" (not "the Boss").
- Consistency passes: 47 repeated lines harmonized, 323 literal names
  tokenized in 67 files. The names pass now skips "Pirate", "Queen" and
  "Someone" (generic tokens) and Dove's "Boss".
- Open questions: `work/translation/en/dialogue_proofread_notes.md` (batch 10).

## 2026-10-01 — Dialogue batch 9 (Sousuke rescue and Left-Behind Sea branches) translated

- Sousuke rescue route stages 17-22 (2041a/b/c-2046) and Left-Behind Sea route
  stages 26-29 (2054a/b-2057, +2222): 5,535 records in 75 slices; the 48
  choice D-Trader rows (2222/2232/2233/2242/2243/2252) were filled from
  identical translated lines. Total 52,080 records, `check` OK (still one TOO
  LONG: 604:t_6:4), 52 tests OK (1 skipped), build dry run OK (241 stage
  members rebuilt).
- New proposed names: Rick, Ogre Family, Melara, San Carlos, Scott SP; generic
  speakers Researcher, Newscaster, Mariemaia Soldier, Defense Force Member, AS
  Pilot, FB Member, AT Pilot, Kugel Fleet Crewman.
- Settled: 了解 = "Understood" (never "Roger"); おキツネ博士 = "Dr. Fox";
  Orb's 首長官邸 = "Orb Union Official Residence"; PLANT 議員 = "Councilwoman";
  クーゲル船団 = "$$クーゲル$$ Fleet"; Parinuri's ラケージ様 = "Lady $$ラケージ$$".
- Consistency passes: 14 repeated lines harmonized, 12 plain Hideauze /
  Left-Behind Sea mentions tokenized, 3 plain "Straus" rows tokenized, literal
  names tokenized in 50 files (Dove's "Boss" for Beck and Lukkage's "Great
  Pirate" title kept as plain text).
- Open questions: `work/translation/en/dialogue_proofread_notes.md` (batch 9).

## 2026-10-01 — Dialogue batch 8 (Blue Earth and Dragon's Hive branches) translated

- First branch batch after route A: Blue Earth route stages 4-11 (2202,
  2014-2025, including its North America / Japan split) and Dragon's Hive route
  stages 17-20 (2212/2213, 2035a/b-2038a/b): 7,116 records in 96 slices; the
  19 D-Trader variant rows were filled from identical translated lines. Total
  46,497 records, `check` OK (still one TOO LONG: 604:t_6:4), 52 tests OK
  (1 skipped), build dry run OK (208 stage members rebuilt).
- New proposed names: Schenberg, Peterson / Peterson Base, Jona, Gihren Zabi,
  Tokiwa, Guren, Nataku, Uzumi Nara Athha, A Baoa Qu, Aprilius City, Siegel
  Clyne, Cosmic Era, Ryuusuke; ZAFT Soldier (speaker).
- Settled: 総帥 = "leader"/"the Leader"; Federation 議員 = "Congressman";
  AG addresses Hibiki as plain "$n"; the Sidereal's ボス = lowercase "the boss";
  Takeru's 兄さん = "Brother"; Rand's 親方 stays "the Boss".
- Consistency passes: 79 repeated lines harmonized within their stage, 195
  literal names tokenized, 5 AG "Mr. $n" rows and 2 Sidereal "Boss" rows fixed.
  Route-A fix: 2013_02 93:t_2:116 (借りを返す) now reads as revenge.
- Open questions: `work/translation/en/dialogue_proofread_notes.md` (batch 8).

## 2026-10-01 — Dialogue batch 7 (stages 59-61 and the finale) translated

- Batch 7 = 2103 (59 邪神降臨), 2104 (60 永遠へ), 2105 (61 黒い太陽) and the
  final stage 2106a-d (果てなき世界, including the ending): 5,515 records in 70
  slices. Route A is now translated end to end: 39,381 records, `check` OK
  (still one TOO LONG: 604:t_6:4), 52 tests OK (1 skipped), build dry run OK
  (167 stage members rebuilt).
- New proposed names: the 12 ネオ・ angel speakers ("Neo Hamaliel" ...) and the
  bare zodiac angels (Malchidael, Asmodel, Muriel, Verchiel, Zuriel, Hanael,
  Cambiel, Barchiel); Jerid, Kimiko, Artesia, Tolle, the Barkoff Squad
  (Barkoff, Godan, Kochack, Zaki), Euphie, Idea, Milliardo, Clyne, Makiko,
  Tanaka; keywords Super Team Gurren, The Big, Megadeus, Rukbat System,
  Akihabara.
- Settled renderings added to `docs/DIALOGUE_STYLE.md` ("Endgame renderings"):
  Messenger of the Sun (Tetsujin exception to "emissary"), infinite power,
  offerings (贄), the Boss (Rand's 親方), Dad/Mom/Sis for Hibiki, Heavenly
  Prison, causal horizon, hyperdimensional world, Cartwheel Galaxy, and others.
- Consistency passes: 148 repeated lines harmonized within their stage, 150
  literal names tokenized, 1 Earth Sphere token. Manual fixes: Insaraum token,
  Book of Genesis, Zechs's sacrificial-stone lines, Advent's "Mere humans have
  no right to deny me!", Class 3-4 naming, speaker tokens in 2106_24.
- Open questions are in `work/translation/en/dialogue_proofread_notes.md`
  (batch 7 sections).

## 2026-10-01 — Dialogue batch 6 (stages 49-58) translated

- Batch 6 = 2089-2091, the 2250/2251 choice (route A = Shin Getter Dragon),
  2092-2094, 2098, 2099 (the hope/despair choice; route A = hope), 2100a/b,
  2102: 6,828 records in 91 slices. Total 33,866 records (all dialogue on
  route A through stage 58), `check` OK (still one TOO LONG: 604:t_6:4),
  52 tests OK (1 skipped), build dry run OK (155 stage members rebuilt).
- 23 new proposed names, among them Wing Zero, Quantum System, the Heavenly
  Pillar, Ambriel the Overriser, Verchiel the Heat, Zuriel the Unbreakable,
  Chaos Leo, Chaos Anguis, the Dimensional Generals Dhritara and Virupaksha,
  Adnachiel (Advent's name for Vildark), bare Hamaliel and Sol.
- Settled renderings added to `docs/DIALOGUE_STYLE.md`: psychic waves, the
  Heart of Space, the force that seeks to exist/vanish, emissary / emissary of
  God, great collapse, the void, degeneracy reactor, Spiral Man, Galactic Raid
  Fleet, the new Buster Machine No. 3, Shin Shine Spark, god-killing power,
  machine fusion, forerunner (先駆者), the Exalted Ones and "Salus" for the
  True Disciples (provisional), "Lord Advent" in their mouths vs White's
  "Captain Advent", The Edel's light "nya~".
- Consistency passes: 522 repeated lines harmonized to their first rendering
  within the same stage (mostly repeated scene variants in 2094/2099), 205
  literal names tokenized, 3 Earth Sphere tokens; 8 White "Lord Advent" rows
  set back to "Captain", 4 "pioneer" rows set to "forerunner".
- Open questions for proofreading are appended to
  `work/translation/en/dialogue_proofread_notes.md` (stages 56-58 sections).

## 2026-10-01 — Dialogue batch 5 (stages 39-48) translated

- Stage map extended past 38 (`docs/STAGE_ORDER.md`): Japan route runs 36-40
  (2064-2068), routes merge at 41 (2079); 2240/2241 choice after 42 (route A =
  Shinji, 2081); merge again at 44 (2084). Batch 5 = 2067, 2068a/b, 2079, 2080,
  2240/2241, 2081, 2084-2087, 2088a/b: 7,096 records in 95 slices. Total
  27,038 records, `check` OK (one TOO LONG: the eleven-Sphere list,
  604:t_6:4), 52 tests OK, build dry run OK (130 stage members).
- About 35 new proposed names (Dankuuken, Dancouga, Paradigm City, Yamsk,
  Melissa, Kashim, Irina, Marilyn, Buster Machine No. 2, Takaya, Ryu, Vist
  family, Ricardo, Super Singularity, Esper, ...); unverified spellings flagged
  (Nikero, Kurefushin, Chaos Kapel, Eliphas, Count Purin).
- New passes: `harmonize` (same Japanese inside one scene group -> the first
  English in play order; 261 branch-duplicate rows aligned), Earth Sphere
  tokenizing, name pass (`Princess` now skipped). Settled renderings added:
  Chrono Conservatives, Rainbow Wave, Kalinin's "Ikinasai", Senpai, psychic
  waves, the four-phrase refrain, "I mustn't run away", event control, FMP and
  Unicorn terms. Open items in `dialogue_proofread_notes.md` (様 handling,
  Carlos/Axion, Sardias "shot", D.O.M.E. pronoun).

## 2026-09-30 — Dialogue batch 4 (stages 29-38) translated

- Route A stages 29-38 translated: 2053 (continent 29), 2058-2063 (common
  30-35), 2230/2231 (Japan / Neo Zeon / Amalgam choice), 2064-2066 (Japan
  36-38); 5,643 records in 75 slices. Total 19,942 records, `check` OK, 52
  tests OK; build dry run OK (103 stage members, 465 blank cells left).
- About 20 more names/terms added as "proposed": Mazinger, Burnstraus, Soreil,
  Turn A, Lancerow Dahell / Lancerow, Earth Empire Space Force, Pierre, Planet
  Gabar, Sigma, Trider, Takeo, Michitaro Takeo, Great Knot Punisher, Rika,
  Kurogane Five, Q-chan, Olympus, Science Fortress Research Institute.
- New conventions in `docs/DIALOGUE_STYLE.md`: Megumi's "Mommy"/"Mom",
  `$f`/`$F` kept, Quarreling Twins always tokenized, D.O.M.E. `#pilot` (being)
  vs `#keyword` (facility), Black History, the three route-choice team names,
  Demon God of Light, Lord Hades, Photon Power, Getter Reactor, the Great Void.
- Fixes: literal "feuding twins" (also dlg_2012_02), bare Trider, Topless,
  Getter furnace, institute name tokenized; name pass tokenized 15 literals.
  Open items appended to `work/translation/en/dialogue_proofread_notes.md`.

## 2026-09-30 — Dialogue batch 3 (stages 19-28) translated

- Route A stages 19-28 translated: 2033, 2034a/b (Macross Quarter route
  19-20), 2039, 2040a/b (MQ+Hive 21-22), 2047-2049 (common 23-25), 2220/2221
  (continent / Left-Behind Sea choice), 2050-2052 (Central Continent 26-28);
  4,609 records in 63 slices. Total 14,299 records, `check` OK; build dry run
  OK (81 stage members, 465 blank cells left).
- About 45 more dialogue names/terms added as "proposed" (Links, Seiei,
  Zabi, Noriega, Kinryu, Katsuragi/Nagare, Lelouch vi Britannia, Zeta,
  Destiny, Zambot, Daitarn, Qan[T], V-Con, AS Member...). Several flagged
  unverified (Emilio, Eddie, Physica, Fee, Daita, Kyusaku, Axio Scott SP,
  Infinity Prison).
- Passes: 21 six-dot 「………」 rows -> nine dots, "Dark Legion" -> "army of
  darkness", name pass tokenized 272 literals. New conventions (the quiet
  type, Four-Eyes, Lilin, X-beauty, True War...) in `docs/DIALOGUE_STYLE.md`.

## 2026-09-30 — Dialogue batch 2 (stages 9-18) and batch 3 started

- Story order researched (akurasu flowchart + SRW Wiki, matched to files by
  cast and the choice texts): `docs/STAGE_ORDER.md`. Route A = first option at
  every choice. Batch 2 = stages 9-18: 2011-2013 (Green), 2026-2030 (common),
  2210/2211 (spacequake split), 2031-2032 (Macross Quarter route); 5,802
  records in 78 slices, all translated, `check` OK (9,690 records total).
- Briefs now show Tengoku English already written for identical Japanese.
  `chapter()` groups any 22x0 choice scene with its D-Trader variant.
- Glossary: about 40 dialogue names/terms added as "proposed" (Haran, Amerria,
  Quarter, Danaan, Mars, Top Squad, Neo Lux, O'Connor, Shinka, generic
  speakers...). Name pass tokenized 171 more literals; fixes for Amerria,
  Haran, Mars, Ranka-chan, Shinka applied. New conventions in
  `docs/DIALOGUE_STYLE.md`; open items in `dialogue_proofread_notes.md`.
- Batch 3 planned: stages 19-28 (2033, 2034a/b, 2039, 2040a/b, 2047-2049,
  2220/2221, 2050-2052), 4,609 records in 63 slices.

## 2026-09-30 — 0.3.0 playtest ISO: stage dialogue 1-10

- All 54 slices of stages 1-10 translated (3,888 records, route A), `check`
  OK. `work/output/builds/0.3.0` + `work/output/iso/0.3.0/Tengoku-hen-English-0.3.0.iso`
  built and verified (29 stage members; SDAT v2 round trip; 82 files in both
  trees; sha256 b2bdfd24…e1c230). Runtime not yet verified.
- New `python -m tools.dialogue names [--apply]`: literal English names in
  speech become tokens where the record's Japanese has the term (104 + 8
  applied); `NAME_SKIP` keeps generic "Gundam" and Bobby's "Boss" (= Jeffrey).
- Consistency passes: Tessa's 大佐殿 = "Captain" (Jigoku), "Miss $$スズネ$$",
  "Puppy", Lambda Driver / Double X tokens; Ledo's accented speech
  hyphen-split (69 rows). `tests/test_dialogue_build.py` added (52 pass).

## 2026-09-30 — Dialogue builder and stages 1-8 (toward 0.3.0)

- `tools/dialogue_build.py` writes translated records into the stage Lua
  members, rebuilds STGZ3OF2 and re-encrypts it (make_npdata v2); the build
  decrypts it back and compares. `game_build` (VERSION 0.3.0) includes it, and
  `iso_write` replaces `STGZ3OF2.SDAT` when the build has one. Trial build
  `work/output/builds/0.3.0-trial1` verified (9 members at the time).
- **Encoding fix:** font cells whose trail byte is 0x5B or 0x5D (`[` / `]`) are
  no longer allocated. Letter K had 0x825D: a record ending in K would have
  closed the Lua `[[...]]` string early. The builder now also refuses any
  block containing `[[`/`]]` or ending in `]`.
- Records with several separate 「」 blocks (route-branch lines) keep one
  block per line; checker and builder both handle it.
- Dialogue names settled into the glossary as "proposed" (surname/given-name
  forms such as Chidori, Sagara, Ikari, Ayanami, Katsuragi; call signs Skull,
  Pixie; Z-Chip, Lambda Driver, Third Impact, Central Dogma, Double X...).
  Shared renderings are listed in `docs/DIALOGUE_STYLE.md`; proofreading items
  collect in `work/translation/en/dialogue_proofread_notes.md`.

## 2026-09-30 — 0.2.1 ISO and dialogue stages 1-10 started

- Library voice-actor credits (ACTR) romanized: 199 credits in
  `work/glossary/library_voice_actors.json` (Jigoku's 140 plus 45 researched
  with sources); the builder fails closed on an unknown credit. Robot pilot
  names (PLTN) now come from the glossary (誰か = Someone); the 316 dash and
  developer-note placeholders stay untouched. `・` joins one katakana name and
  is never split (fixed after the dry run caught リディ・マーセナス).
- `work/output/iso/0.2.1/Tengoku-hen-English-0.2.1.iso` built and verified
  (82 files, both trees; sha256 da0215fa…c171f). 47 tests pass.
- New `tools/dialogue.py` (`map`, `export`, `check`) and `docs/DIALOGUE_STYLE.md`.
  Stages 1-10 in story order, route A after the 2200 choice: 2001, 2002,
  2003a/b, 2004, 2005, 2200/2201, 2006, 2007, 2008a/b, 2009, 2010a/b; 3,888
  records in 54 slices of up to 80 rows (never crossing a chapter). Records
  keyed by (member, event, ordinal) as in Jigoku's luarec; 265 rows show
  identical-source Jigoku English. Dialogue box measured at 30 fullwidth cells
  (the game's longest Japanese line), 3 speech lines; `check` wraps with real
  glyph advances (`work/ui/latin_advances.json`) and reports TOO LONG rows.
  Generic speakers added to the glossary (Imperial Soldier, Pirate, Citizen...).
- Translation running at most 6 agents at a time. Not yet built: the Lua
  writer, dialogue encoding in the font, keyword-link rendering and SDAT
  re-encryption (make_npdata -e, as Jigoku).

## 2026-09-30 — Build 0.2.0 and the first test ISO

- New `tools/library_build.py`, `tools/game_build.py`, `tools/iso_write.py`
  (dry run by default; see `docs/BUILD_ISO.md`) and 5 builder tests (45 pass).
- 0.2.0 = ui-0.1.1-vwf Spirit UI + all 1,013 translated library entries. One
  font allocation of 102 cells (82 characters, 20 badges) of 469 free; VWF
  width table and hook as in ui-0.1.1. Library text wrapped to 1216 units
  (38 fullwidth cells, measured from the Japanese); longest line exactly 1216.
  Every library record decoded back and compared; untouched fields and
  members byte-identical; RPW and font archives compared.
- `work/output/iso/0.2.0/Tengoku-hen-English-0.2.0.iso` (4,935,057,408 bytes,
  sha256 cee8c65e…aa03e18): original layout kept, six files appended and
  repointed in both trees, UDF zeroed, one plaintext region, BLJS-10299. All 82
  files verified by hash through the Joliet and primary trees. The first
  verification failed only because it compared primary-tree names to Joliet
  names (the primary tree shortens them); trees are now paired by extent.
- Not tested in game. RPCS3 only (plain ELF). The RPCS3 install cache still
  holds ui-0.1.1-vwf RPW/font copies and must be updated or cleared first.

## 2026-09-30 — Settle library names and character profiles

- 22 research groups (by franchise) settled names with cited sources and wrote
  BASE_RULES profiles (gender with evidence, nickname, position, personality)
  for all 539 pilot entries: `work/glossary/research/*.json`, merged into
  `work/glossary/library_characters.json`. The first run was lost to a usage
  limit (nothing saved); the rerun saved progress incrementally.
- Glossary now 2,415 terms; all 1,463 names used by the library have English
  (official with a source, or proposed where no source exists).
- Precedence fixed in `docs/NAME_RESEARCH.md`: user-confirmed, akurasu Z3.2,
  other akurasu, official English, then Jigoku glossary and shipped text.
- 16 challenges to official names approved in `library_settled.json` with the
  reason (e.g. Gundam Zabanya, Benkei Kuruma, Supreme God Z, Celestial Being
  mothership, quantum brainwaves); akurasu Z3.2 spellings kept where they are
  the source (Heero Yui, Zechs Marquise, Space Galaxy, Waynewright).
- Split same-name terms: ドロシー (per entry), ムウ#orguss, 地球連邦#00/#awgx,
  国連 vs ＵＮ, 黒い太陽#sol/#aquarion, 早乙女#macross, キッカ, 千葉, 水星,
  モニカ, アリシア#alisia. `retoken` applied 81 prose re-pointings from
  `work/glossary/library_retoken.json` (dry run reviewed first).
- Tool: `research`, `retoken`, `proofread`, `proofread-apply` commands; seeding
  keeps user-confirmed terms, blocks unapproved official changes, and gives
  researched variants their own tokens. `check` passes, all 40 tests pass.
- Meaning proofreading (27 batches, `docs/LIBRARY_PROOFREAD.md`): every entry
  compared with the Japanese; 288 field fixes applied by `proofread-apply`
  (hash-checked against the brief, 0 rejected). Categories: mistranslation and
  reversed direction/referent, omissions, additions carried over from Jigoku,
  restored subjects (pro-drop rule), pronouns from the researched genders.
- Per the user, at most 6 subagents run at once; 11 over-limit agents were
  stopped and rerun (they had saved nothing).
- Name script (`name-script`, dry run reviewed on 25 whole sentences first):
  1,124 literal English names in 468 fields turned into tokens, only where the
  entry's Japanese contains the name; also 'Earth $$スフィア$$' -> 地球圏 and the
  doubled article before 'the ...' tokens. Idempotent (second run: 0 changes).
- Added 四天王 = Four Supreme Generals (franchise English, correcting the old
  precedence) and 地球圏 = Earth Sphere. `seed` no longer resets reuse files.
- Open: 御使い English (user), one rank table for 少尉/准尉/曹長/二尉 and the
  like, remaining misspelled literals with no glossary variant (e.g.
  'Ruunamaria'), then the library builder and in-game checks.

## 2026-09-29 — Start the library translation

- Added `tools/library_text.py` (`seed`, `export`, `check`, `names`; dry run by
  default) and `docs/LIBRARY_STYLE.md`. Names are glossary terms bound to
  Tengoku library fields; prose refers to them as `$$token$$`, as in Jigoku.
- `work/glossary/library_terms.json`: 1,734 terms seeded from Jigoku's glossary
  (bound by the pairing report), the akurasu Z3.2 mech and series lists, and
  `work/glossary/library_settled.json` (researched decisions with sources).
  User-confirmed Jigoku terms are never overridden.
- Refreshed the Jigoku glossary reference to 1,176 terms to pick up the user's
  2026-09-28/29 corrections; the 2026-09-11 snapshot is kept alongside. Saved the
  akurasu Z3.2 pilot/mech/series pages and the SRW glossary page as sources.
- Reused Jigoku's English for 293 entries whose Japanese is unchanged
  (`kw_reuse`, `pt_reuse`, `rt_reuse`), remapping Jigoku entry-id tokens and
  keeping Jigoku's meaning where Tengoku made a bare name ambiguous (アイム).
- Trial batch kw_000 (20 keywords) translated by a subagent and reviewed:
  complete, validated, careful with gender; its name proposals showed that
  names must be settled centrally (9 of its Sphere names differed from akurasu).
  Style corrected to American spelling, which the Jigoku corpus actually uses.
- Remaining 22 batches (700 entries) translated by subagents. **Draft coverage:
  143/143 keywords, 539/539 pilots, 331/331 robots.** Every batch file holds
  exactly its brief's entries; every agent reports all entries examined and
  none left untranslated; `check` passes with no errors; all 40 tests pass.
- `kw_113.json` disappeared after its agent reported it written and checked;
  cause unknown. The agent restored it from context (2 of its 78 name
  proposals could not be recovered; no entry text lost). Agents shared one
  scratch folder and overwrote each other's `build.py`: give future agents
  per-batch scratch folders and verify outputs against briefs after every wave.
- Not done yet: 1,108 name proposals await settlement (40 conflict between
  batches) and 648 prose names are not yet glossary terms; proofreading;
  splitting same-English different-person terms (ドロシー, ムウ); a library
  builder, font coverage and in-game verification. The draft is not final.

## 2026-09-29 — Compare Tengoku library entries with Jigoku

- Added `tools/library_compare.py` (dry run by default) and 4 tests. It copies
  Jigoku's original library archives read-only from its ISO into ignored
  `work/jigoku_ref/` with hash checks, pairs entries one-to-one by name, then by
  description, and records the Jigoku English available for each pair.
- Wrote `work/glossary/library_jigoku_match.json` and `docs/LIBRARY_JIGOKU.md`.
  Of 1,013 Tengoku entries, 618 pair with Jigoku: 293 unchanged descriptions,
  83 minor edits, 209 partly rewritten and 33 rewritten; 395 are new.
- Spot checks rejected an automatic partial-name pairing (3 of 4 were wrong);
  those are now review hints only. All 40 tests pass. No game data changed.

## 2026-09-29 — Reorganize the repository to the AGENTS.md layout

- Removed the other project's release rules from `AGENTS.md` (user edit).
- Moved the target glossary, the Jigoku glossary reference and its README to
  `work/glossary/`. Moved the Jigoku UI pack, the Spirit RPW schema and audit to
  `work/ui/`, and the Spirit text to `work/translation/en/ui/`. Transfer
  manifests use folder-relative paths and still match.
- Moved the ui-0.1.0 and ui-0.1.1-vwf builds and the fresh VWF game copy to
  `work/output/`. `work/tengoku/game-ui-0.1.0` stays in place because RPCS3
  registers it. `activation.json` still records the copy's old source paths
  as history; its backups did not move.
- Updated tool paths and default outputs (`ui_spirits`, `inventory`,
  `ui_build`, `ui_vwf_build`, `ui_deploy`, `ui_activate`) and current docs.
  Historical changelog entries keep their original paths.
- `.gitignore` now tracks `work/glossary/`, `work/ui/` and `work/translation/`,
  and ignores the rest of `work/` and the new `incoming/` folder.
- `python -m tools.ui_spirits check` passes; all 36 tests pass. No game,
  cache, emulator or build bytes changed.

## 2026-09-11 — Activate VWF in the registered game and UI cache

- User authorized “Do it.” Verified RPCS3 was closed, the registered Tengoku
  folder was unchanged, and its three patch files plus both installed cache
  files matched the expected previous build.
- Added `tools/ui_activate.py`: dry-run by default, closed-emulator guard,
  source/build/hash validation, verified backups, staged replacements and
  rollback on failure. Reviewed the dry-run's six exact destinations.
- Applied ui-0.1.1-vwf EBOOT, RPW and font to the registered `game-ui-0.1.0`
  folder and matched RPW/font to Tengoku's `DATA0014.DAT` / `DATA0141.DAT` cache.
  Updated the existing game's deployment manifest to the new build version.
  The folder name and RPCS3 registry stay unchanged for the user's usual entry.
- All five binaries and the deployment manifest passed readback; all six
  prior files have verified recoverable backups recorded in
  `work/tengoku/activations/ui-0.1.1-vwf/activation.json`.
- No rendering changes or new runtime tests in this activation; the build's
  earlier 36 tests remain the reported test evidence. VWF boot/layout still
  await user navigation. No save changes, game input or publication.

## 2026-09-11 — Port Z3.1-style VWF to Tengoku

- Read Z3.1's `vwf_stub`, `apply_vwf`, single-letter encoding/raster code and
  badge handling. Implemented a target-specific hook at Tengoku VA 0x147dc,
  with independent allocation in its executable gap and no legacy addresses.
- Added `tools/self_elf.py`, `tools/vwf.py`, `tools/ui_vwf_build.py` and VWF
  encoding support in the scoped RPW writer. The original pair builder remains
  reproducible. The deployer handles the matched three-file VWF build.
- Resolved the former analysis-only ELF limitation by verifying every allocated
  section is covered by an authenticated program LOAD and matching RPCS3's
  program-ELF reconstruction algorithm. The five program HMACs pass; the
  developer ELF digest remains unmatched and runtime validation remains open.
  An isolated RPCS3 decrypt helper did not produce an output and was stopped;
  no independent RPCS3 CLI comparison or emulator boot is claimed.
- Dry-ran and reviewed all 129 intended fields, built ui-0.1.1-vwf, and read back
  its executable and two CPK archives. Allocated 62 letter cells and 20 badges
  from 469 target blank cells; appended 4,696 pool bytes. Inspected the font
  sample and checked clipping bounds for every generated glyph.
- **36 tests passed**, including Capstone-decoded stub execution covering
  proportional widths, unchanged Japanese pitch, table bounds, and register,
  CR and caller-memory preservation. VWF text/badge encoding and full-family
  RPW preservation pass; existing 32 tests still pass.
- Applied the build to `work/tengoku/game-ui-0.1.1-vwf`; all 82 copied disc files
  passed readback. Found and hash-matched the old installed Tengoku RPW/font
  cache files. Asked the user whether the game is stopped before activation.
  Registered game/cached files remain the old build. No game input, installed
  data changes, source changes, save changes or publication were performed.

## 2026-09-11 — User reports reaching the patched game

- User reports being in game. Read-only checks confirm RPCS3 registers BLJS10299
  to `work/tengoku/game-ui-0.1.0` and exposes a running Tengoku window near 60 FPS.
- No input was sent to the emulator. Screen capture returned a different
  foreground app, so translated Spirit names/descriptions/badges and layout
  remain visually unverified. Navigation continues to belong to the user.

## 2026-09-11 — Apply the Spirit UI patch to a game copy

- Added `tools/ui_build.py`: append-only RPW string storage, exact per-field
  repointing, separate name/badge roles, target-derived blank font allocation,
  paired Latin glyphs on both pages, and independent archive/text readback.
- Derived Tengoku's renderer mapping and RPW loader/record stride from its
  own executable. The analysis-only SELF reader verifies program-section
  HMACs; its incomplete whole-file reconstruction is never deployed.
- Built ui-0.1.0: 129 translated fields, three preserved sentinel fields,
  2,476 appended pool bytes and 296 allocated cells from 469 blank/unassigned
  target cells. All 133 unrelated font members and all unrelated RPW bytes
  remain intact. Inspected a generated font contact sheet, not a game screen.
- Added five meaningful writer/encoding regression tests; **32 tests passed**.
  Dry-ran and reviewed the complete English patch plan before building.
- Added and dry-ran `tools/ui_deploy.py`, then applied the verified RPW/font
  archives to `work/tengoku/game-ui-0.1.0`. Rehashed every pristine source and
  read back all 82 copied disc files. Original executable, ISO, stage scripts,
  voice data, reference assets and saves remain unchanged.
- The user took over RPCS3 navigation during Add Games. No registration,
  boot, installed-data update or in-game Spirit fit is claimed. Runtime and
  layout flags stay false; no release was published. See `docs/UI_BUILD.md`.

## 2026-09-11 — First UI translation batch: Spirit commands

- Derived and reviewed the target RPW Spirit table: 44 records of 20 bytes,
  three string fields each. Examined 132/132 fields; authored 129 translations
  and explicitly preserved three empty/no-command sentinel fields.
- Added a partial active target glossary containing only 42 Spirit terms,
  with Tengoku name-field identities, proposed naming status and explicit
  unverified binary integration. No legacy numeric IDs were adopted.
- Added per-occurrence names, descriptions and effect abbreviations in
  `translation/ui/spirit_commands.json`; quoted command names use the same
  glossary tokens as the command names. Plus and unknown variants are retained.
- Corrected/clarified Bonds' healing scope, Fury's abilities/skills and ALL
  attack penalties, final rates for Focus/Focus+, Accel's duration, and healing
  targets. Other valid reference wording remains unchanged.
- Added the target Spirit schema and an active audit separate from the imported
  reference. Font metrics, encoding, layout and draw consumers remain unverified.
- Added source-driven coverage, fingerprint, glossary identity, number, control,
  line-count and unknown-state checks. All 27 tests passed, including intentional
  missing/duplicate entries and same-English/wrong-identity regressions.
- Dry-ran and exported readable/structured text under `work/tengoku/ui/`. A
  bounded scan of 120,363 indexed candidates reverified 299 matching original
  spans; eight source strings are already bound and 291 need classification.
  This includes dialogue/design notes and is not UI coverage or missing totals.
- Recorded the inherited naming basis, a limited Tengoku wiki effect cross-check,
  an embedded target UI layout hint, and remaining work in `docs/UI_SPIRITS.md`.
  Updated glossary guidance, the handoff, UI checklist, pipeline guide and README.
- Documented why the inherited plus-variant/SP-cost-only note is not a Tengoku
  assumption. Final checks confirmed the export equals the validated authoring
  data and all 68 imported assets plus BASE_RULES remain unchanged.
- No dialogue/voice translation, game binary edit, font patch, deployment,
  emulator/installed-data/save change or release occurred.

## 2026-09-11 — First Tengoku source/archive pipeline

- Recorded the user's work allocation: primary agent owns ROM hacking,
  pipeline engineering and UI translation; dialogue/voice translation belongs
  to other agents after scoped source bindings and briefs are ready.
- Added generated-data exclusions, Tengoku-specific local configuration and
  dry-run-first source commands. No Git repository was initialized.
- Ported/reworked the ISO reader with Joliet names, bounds/path checks and
  streamed multi-extent aggregation. Extracted and hash-verified all 82 logical
  files, including the correctly joined 1,580,686,480-byte WP.CPK.
- Rechecked original PARAM.SFO (BLJS10299), recorded the whole ISO SHA-256 and
  later reverified the original ISO and every extracted file.
- Decrypted the combined stage SDAT offline, recording tool/input/output hashes.
  Indexed 876 members, 716 text members, 66,919 long literals and 283 source-comment
  scene hints without parse failures. These are not verified dialogue bindings.
- Added strict read-only RPW/library parsers: 24 chunks, 5,535 string slots,
  143 keyword, 539 pilot and 331 robot records. Generated 1,883 unreviewed glossary
  candidates without adopting legacy IDs or creating an active target glossary.
- Added initial UI/artwork discovery: 120,363 mixed-source candidates, 4,192
  exact-reference matches and 135 artwork member fingerprints. No UI family,
  actual consumer, display width or translation was marked verified.
- Hardened the ITOC writer and added an independent metadata verifier. Eight
  archives (2,088 members) rebuilt byte-identically. A 70,052-byte synthetic stage
  member migrated from DataL to DataH and preserved all other 875 payloads.
- Fixed cumulative ItocSize updates during multiple DataH moves. All 14 unit
  tests passed, including multi-extent and malformed ISO fixtures, Lua lexical
  boundaries, no-op preservation, multiple growth migrations and shrinking.
  Existing actual archive outputs also passed the final independent verifier.
- The archive CLI now performs independent readback after writing; its stage
  no-op smoke check preserved all 876 members. Final reference checks confirmed
  all 68 manifested assets and the original BASE_RULES remain unchanged.
- Updated the README, handoff and UI checklist; added `docs/PIPELINE.md` with
  commands, provenance, evidence and remaining work. Imported reference assets
  and BASE_RULES remain unchanged; generated source/game bytes stay under work/.
- No dialogue/voice/UI translations, executable/font patches, SDAT re-encryption,
  ISO packaging, game launch, deployment, save/cache changes or release performed.

## 2026-09-11 — Repository readiness review

- Read the required project guidance and inspected the starter workspace.
- Verified all 68 manifested reference assets against their SHA-256 hashes,
  including recorded UI file sizes; all 34 JSON files parsed successfully.
  Confirmed `BASE_RULES.md` remains byte-identical to the source project's copy.
- Recounted 1,141 glossary entries, 2,542 stored UI rows, 17 multiple-English
  groups, 27 translation files, 29 code reading references and 15 repair families.
  The empty target audit still has 41 unstarted categories with unknown totals.
- Confirmed the documented ISO exists with its recorded size and that candidate
  source tools, the SDAT utility and earlier probe reports are available.
- Updated the handoff with this evidence and the absence of Git metadata and
  generated-data ignore rules. No tools or active target inputs were added.
- Reference integrity and prerequisite checks only: no extraction, binary
  round trip, build or runtime test; no game, emulator, saves or release changed.

## 2026-09-11 — UI reference and discovery checklist

- Imported 27 unchanged Jigoku translation JSON files; indexed 2,542 stored
  rows and 2,469 distinct Japanese keys, preserving metadata and duplicates.
- Flagged 17 multiple-English Japanese-key groups for contextual review.
- Added 29 non-executable implementation reading references, five historical
  repair notes and a 15-family repair map, including artwork/layout examples.
- Added a source-driven Tengoku UI checklist and empty target audit template.
  Updated agent instructions and handoff so future UI work uses these guides.
- Recorded hashes for 65 reference assets. These counts are reference inventory,
  not target coverage. No Tengoku UI search, replacement or runtime test yet.
- No game, emulator, saves, runnable build tools or releases changed.

## 2026-09-11 — Imported glossary reference

- Copied the 1,141-entry Jigoku glossary unchanged, preserving English names,
  Japanese keys, series, source references, aliases, notes and statuses.
- Copied its existing pilot/mech source reference files and recorded SHA-256
  hashes in `analysis/reference/import_manifest.json`.
- Marked all numeric identities as Jigoku-only reference data. An active
  Tengoku glossary is not created until target records are matched/reviewed.
- Updated agent instructions and handoff to make the reference discoverable.
- No tools, game files, saves, emulator configuration or builds changed.

## 2026-09-11 — Translation rules and technical handoff

- Imported `BASE_RULES.md` unchanged from the Jigoku-hen project.
- Added `docs/Z3_LESSONS.md`, covering identity, terminology, message-family
  coverage, mission roles, placeholders, layout, storage safety, validation,
  release provenance and installed-cache consistency.
- Preserved the source project's detailed conventions as a historical
  reference, explicitly warning against reusing numeric IDs and stale claims.
- Imported the Tengoku source-format assessment and added discoverable
  project instructions and this starter handoff.
- Documentation only: no game, saves, emulator, builds or release changed.
