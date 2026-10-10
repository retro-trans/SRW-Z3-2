# Tengoku-hen handoff

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
Keep the repository private; this release targets RPCS3, not physical PS3/Vita.

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
