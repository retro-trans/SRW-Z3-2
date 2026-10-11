# Building a test ISO

Current build: **0.5.18**, RPCS3 only. It repairs the two enemy Spirit-band
separator cells and carries forward the native map-name fallback repair.
Use `tools.verify_enemy_ui --version 0.5.18` for cumulative final verification.
The user tests public releases: complete Retro Trans release packaging and
public catalog verification after building the ISO. It translates the assembled
stage, terrain and Spirit target families and repairs stat/training columns;
see [category and stat fixes](CATEGORY_UI_0.5.17.md). It connects all 197 timed
narration records across 34 members; see [full narration](NARRATION_0.5.16.md).
It retains the repairs to stray kanji from
the native centering fallback, enlarges level-up stat labels, aligns
intermission/settings captions and translates the concluding narration. See
[reported UI fixes](UI_REVIEW_0.5.15.md). It uses Focus/Foc for the Ki
stat and restores the native outlined font masks used by Lv/SP. See
[Focus and font changes](FOCUS_STYLE_0.5.14.md). It includes the missing enemy-fleet
narration; see [fleet narration](FLEET_NARRATION_0.5.13.md). It verifies the centered
date drawer, translates the briefing and cleans up level-up labels and Score.
See [date and level-up](BRIEFING_LEVELUP_0.5.12.md). It also fixes intermission and
Library menus, connects all native linked-term descriptions to English and
translates the scenario chart. It retains the English title,
chapter subtitle, retro-trans credit and matching build version, compact battle and
map labels, Spirit indicators, Debris Field, result-score cleanup and the Fast
caption to the cumulative translation and layout fixes. See
[intermission and Library](INTERMISSION_LIBRARY_0.5.11.md),
[title screen](TITLE_SCREEN_0.5.10.md), [battle layouts](BATTLE_LAYOUT_0.5.9.md),
[status layouts](STATUS_LAYOUT_0.5.8.md), [menu layouts](MENU_LAYOUT_0.5.7.md),
[link layout](LINK_LAYOUT_0.5.6.md) and [font profile](FONT_0.5.5.md).

The 63,553 fresh dialogue drafts were promoted for this build. Sixteen source-bound
records use additional condensed alphabets, preserving their complete wording
within three lines: fifteen at 85% width and the full eleven-Sphere list at 80%.
`tools/dialogue_layout.py` pins each record's source fingerprint. Both font
pages and the VWF advance table contain the same extra glyphs; other text keeps
its regular glyphs. The builder now rejects any rendered speech block over
three lines. Live readability and the new build's runtime remain unverified.

Use the bundled Python, which has Pillow, numpy and cryptography:
`C:\Users\Binh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
(called `$py` below). The plain `python` (3.8) runs `library_text` and the tests.

```powershell
python -m tools.library_text check                 # translations must pass
& $py -m tools.game_build                          # dry run: summary + sample
& $py -m tools.menu_layout                         # preview screenshot-bound widget edits
& $py -m tools.menu_layout --apply                 # update checked translation/layout plan
& $py -m tools.status_layout                      # preview save/status widget edits
& $py -m tools.status_layout --apply              # save source-bound status plan
& $py -m tools.battle_layout                      # preview battle/map widget edits
& $py -m tools.battle_layout --apply               # save source-bound battle plan
& $py -m tools.intermission_layout                 # preview intermission / Library edits
& $py -m tools.intermission_layout --apply         # save checked plan
& $py -m tools.chart_art                           # preview chart lettering scope
& $py -m tools.chart_art --apply                   # save native texture previews
& $py -m tools.briefing_narration                  # preview three military-report translations
& $py -m tools.briefing_narration --apply          # save source-bound translation plan
& $py -m tools.fleet_narration                     # preview two enemy-fleet translations
& $py -m tools.fleet_narration --apply             # save source-bound translation plan
& $py -m tools.focus_terminology                   # preview source-bound Focus/Foc replacements
& $py -m tools.focus_terminology --apply           # save terminology and glossary
& $py -m tools.focus_font_preview                  # preview native font-mask comparison
& $py -m tools.focus_font_preview --apply          # save comparison image
& $py -m tools.ui_review_fixes                     # preview compact settings/stat captions
& $py -m tools.ui_review_fixes --apply             # save checked wording
& $py -m tools.endless_narration                   # preview concluding narration
& $py -m tools.endless_narration --apply           # save fingerprinted bindings
& $py -m tools.settings_layout                    # preview explicit ON/OFF widgets
& $py -m tools.settings_layout --apply            # save checked settings plan
& $py -m tools.category_ui                        # preview source-bound stat/category plan
& $py -m tools.category_ui --apply                # save checked layout data
& $py -m tools.title_screen --version 0.5.17        # preview title packing and footer
& $py -m tools.title_screen --version 0.5.17 --apply # save title metadata and previews
& $py -m tools.game_build                          # dry run: review the matched build
& $py -m tools.game_build --apply                  # work/output/builds/0.5.17
& $py -m tools.iso_write                           # dry run: file mapping
& $py -m tools.iso_write --apply                   # work/output/iso/0.5.17/*.iso (+ .json)
& $py -m tools.iso_write --verify-only             # re-check an existing image
& $py -m tools.verify_category_ui --version 0.5.17
& $py -m tools.verify_category_ui --version 0.5.17 --apply
```

## What the build does

- `tools/library_build.py`: expands `$$tokens$$` from the glossary (sentence-
  initial capitals for lower-case English), fills name fields from the terms
  bound to each library field, converts HEIT/WEIT to ASCII, wraps DSCR/DSC2 to
  38 fullwidth cells (1216 VWF units, measured from the Japanese lines), keeps
  the Japanese paragraph indent, and rebuilds each record in its original order.
- `tools/game_build.py`: one font allocation for the Spirit UI and the library
  (249 cells in 0.5.14, including condensed alphabets and compact badges),
  glyphs from the Z3 Rodin Bold face with separate native G8B8 outline/fill masks, the VWF
  width table in the EBOOT, RPW Spirit text, and the three library CPKs. Every
  library record is read back, decoded and compared; untouched fields and
  members must keep their original bytes. `library_preview.png` shows samples.
- RPW names (`tools/rpw_text.py`, `docs/UI_RPW.md`): English appended after the
  j-string pool; only the verified name columns and Spirit cells are repointed.
- Battle voice (`tools/voice_build.py` + `tools/voice_write.py`): the English of
  every `work/translation/en/voice/gNNN.json` line, tokens expanded, encoded with
  the same font mapping (the literal `
` break stays raw bytes 5C 6E, 「」 stay
  cp932). SRVC.BIN is rebuilt and the 369-entry block table in the VWF-patched
  EBOOT is rewritten in the same run; `srvc_check` reads both back
  independently. SRVC.BIN and EBOOT.BIN only work as a pair.
- `tools/iso_write.py`: copies the original ISO, appends the changed files (twelve)
  on sector boundaries, repoints them in both the primary and Joliet trees,
  zeroes the stale UDF tree, writes one whole-disc plaintext region with
  BLJS-10299, then hashes all 82 files through each tree. The primary tree uses
  shortened ISO9660 names, so the trees are paired by extent.

## Limits

- **RPCS3 only.** The EBOOT is a plain ELF; a console needs a fake-SELF wrapper
  (Jigoku's `platforms/ps3/cfw_package.py`), untested for Tengoku.
- **Runtime unverified.** The Library archives and native linked-term descriptions
  pass complete final-byte readback. Both owned prose consumers and their native
  conversion fallback execute in the harness. Live pagination, long-name widths
  and the newly adjusted captions still need confirmation in game.
- **Install cache.** RPCS3 keeps copies of RPW, the font and the battle voice in
  `dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0014.DAT`, `DATA0141.DAT` and
  `DATA0046.DAT` (SRVC.BIN). They must match the selected build or be
  removed so the game reinstalls them, otherwise the font, Spirit text and
  battle text will not match the new EBOOT (an old DATA0046 with a new EBOOT
  gave blank battle text in Jigoku).
- **Battle voice runtime unverified.** SRVC.BIN grows from 3,499,808 to
  4,946,576 bytes; four blocks exceed the largest original block (54,016 B):
  217 Hibiki, 275 Rand, 295 Ledo, 336 Sousuke (largest 76,048 B). Whether the
  game has a block-size cap, uses the same font/VWF path in battle, and how
  wide the battle text box is are all untested; 695 segments exceed the
  estimated 36 characters.

## Public releases: Retro Trans Tools (AGENTS.md rule)

The ISOs in `work/output/iso/` are local playtest builds and are never
published. A public release must follow Retro Trans Tools' Game Release
Standard v1 (`docs/RELEASE_STANDARD.md` in retro-trans/retro-trans-tools),
read 2026-09-30:

- Publish only `BUILD-MANIFEST.json`, `SHA256SUMS.txt`, `VALIDATION.json` and
  the xdelta patch(es); never a game image.
- Patches work on exact file bytes of the unpacked ISO (`source_format` /
  `target_format` = `iso`), SHA-256, with full sizes; full patch from
  `original`, optional upgrade patches from earlier translated versions.
- Manifest needs `game_id` (stable slug), `version` (= git tag, e.g. v0.3.0),
  and `source_commit`: a full 40-character commit of this project's sources.
  The project is tracked in public `retro-trans/SRW-Z3-2`; commit the actual
  build inputs before stamping release provenance.
- Built with `python -m retro_trans.release build release-local.json --out
  release-vX.Y.Z` then `... validate`, config copied from the tool's
  `examples/release-config.json`.
