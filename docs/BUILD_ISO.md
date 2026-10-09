# Building a test ISO

Current build: **0.5.1** (Spirit UI + RPW name tables + mission conditions + team names + executable UI text via the draw-time hook + title cards + battle/caption/menu art + translated library + all stage dialogue + all battle voice, VWF), RPCS3 only.

Use the bundled Python, which has Pillow, numpy and cryptography:
`C:\Users\Binh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
(called `$py` below). The plain `python` (3.8) runs `library_text` and the tests.

```powershell
python -m tools.library_text check                 # translations must pass
& $py -m tools.game_build                          # dry run: summary + sample
& $py -m tools.game_build --apply                  # work/output/builds/0.2.0
& $py -m tools.iso_write                           # dry run: file mapping
& $py -m tools.iso_write --apply                   # work/output/iso/0.2.0/*.iso (+ .json)
& $py -m tools.iso_write --verify-only             # re-check an existing image
```

## What the build does

- `tools/library_build.py`: expands `$$tokens$$` from the glossary (sentence-
  initial capitals for lower-case English), fills name fields from the terms
  bound to each library field, converts HEIT/WEIT to ASCII, wraps DSCR/DSC2 to
  38 fullwidth cells (1216 VWF units, measured from the Japanese lines), keeps
  the Japanese paragraph indent, and rebuilds each record in its original order.
- `tools/game_build.py`: one font allocation for the Spirit UI and the library
  (102 cells: 82 characters, 20 badges), glyphs from the PS3 Latin face, the VWF
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
- `tools/iso_write.py`: copies the original ISO, appends the changed files (eight)
  on sector boundaries, repoints them in both the primary and Joliet trees,
  zeroes the stale UDF tree, writes one whole-disc plaintext region with
  BLJS-10299, then hashes all 82 files through each tree. The primary tree uses
  shortened ISO9660 names, so the trees are paired by extent.

## Limits

- **RPCS3 only.** The EBOOT is a plain ELF; a console needs a fake-SELF wrapper
  (Jigoku's `platforms/ps3/cfw_package.py`), untested for Tengoku.
- **Runtime unverified.** The library is assumed to use the same text drawer as
  the Spirit UI (true in Jigoku, unverified here). The name/header field widths
  and long English names are not measured in game.
- **Install cache.** RPCS3 keeps copies of RPW, the font and the battle voice in
  `dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0014.DAT`, `DATA0141.DAT` and
  `DATA0046.DAT` (SRVC.BIN). They must match the current build (0.5.1) or be
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
  **This repo is not a git repository yet**, so a release needs one first.
- Built with `python -m retro_trans.release build release-local.json --out
  release-vX.Y.Z` then `... validate`, config copied from the tool's
  `examples/release-config.json`.
