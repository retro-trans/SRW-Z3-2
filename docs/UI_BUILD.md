# Spirit UI game build

This page records the earlier **ui-0.1.0 pair-cell build**. The current
ui-0.1.1-vwf implementation, ELF acceptance evidence, commands and activation
state are documented in [UI_VWF.md](UI_VWF.md). The deployer's defaults now
select VWF; pass explicit `--build` and `--output` to deploy the earlier build.

The first scoped game patch is built under `work/output/builds/ui-0.1.0`.
`tools/ui_deploy.py` applies the two verified archives to a fresh complete disc
folder under `work/tengoku/game-ui-0.1.0`. It refuses existing destinations and
verifies all 82 copied files. This is a local test build, not a published release.

## Content and preservation

All 129 reviewed Spirit name, abbreviation and description occurrences are
encoded. The three record-0 sentinel fields remain original. The writer appends
2,476 bytes to the j-string body and repoints only the 129 audited Spirit fields.
It preserves every original string byte and ordinal, every other chunk body,
all record metadata, and updates only the file/chunk size fields. An independent
readback reverses the allowed changes and requires byte equality with the source.
Soul's name and badge now have different appended strings despite sharing a
Japanese source string. Shared descriptions may reuse identical appended bytes.

The font build independently found 469 blank, cp932-unassigned cells across
both original target pages in the verified 0x81–0x88 lead ranges. It allocates
296 pair cells for the current English corpus. Two letters occupy one cell;
effect abbreviations occupy one cell. No assigned Japanese character is replaced.
Font members 1 and 3 change together, and the other 133 members retain their
original stored payloads. The builder also restores every allocated cell to its
original contents and checks that all other header/pixel bytes are identical.

English letterforms are generated from the locally installed PS3 Rodin face,
`E:/RPCS3/dev_flash/data/font/SCE-PS3-RD-R-LATIN.TTF`, SHA-256
`9b11a63b39539d25c3ab9a15f41e5721dc927b294fb83225743d6825838b638f`.
The bitmap contact sheet is a texture preview, not in-game evidence. Widget
advance, clipping and all display states still require runtime measurement.
In particular, the long Fighting Spirit name needs a real menu fit check.

No executable, SDAT, dialogue, voice, gameplay value or original ISO is changed.
The 291 related-source classification candidates remain outside this patch.

## Target executable evidence

The investigation used the original Tengoku SELF, with an offline research
reader following RPCS3's [SELF structures](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Crypto/unself.h),
[decryption logic](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Crypto/unself.cpp)
and public APP keyset. All five program-section HMACs pass. The reconstructed
research ELF omits non-program metadata payloads; its whole-file digest does
not match the embedded original ELF digest. It is **analysis-only**, not an
executable to deploy. The source's signed EBOOT remains unchanged in the build.
Research scripts and output are in `work/ui_apply_probe/`.

Tengoku virtual addresses below were derived from this executable. Jigoku byte
signatures were used only to locate candidates, which were then disassembled
and followed in the target; no legacy numeric address is applied by the build.

- The target ELF entry descriptor gives TOC `0x99fe70`.
- Drawer `0x14158` walks double-byte codes, handles LF and NUL separately, and
  derives the 32px cell index at `0x1483c`; the 0x81–0x88 dispatch branches are
  algebraically equivalent to `(lead-0x81)*192 + trail-0x40`.
- Setter `0x13884` writes quad width/height and advance into the text state.
  The drawer reads those values; it does not have a universal English budget.
- The RPW chunk dispatcher at `0x2a9e3c` resolves the exact `spirit` tag via
  `0xa260a0`, and its callback descriptor `0x977b48` points to `0x2b66e0`.
  The typed dispatcher `0x6f3cd0` divides the recorded body size by 20.
- The Spirit loader at `0x704b08` calls `0x6fe0f8`, which allocates/copies
  `count*20` bytes. The conversion at `0x70495c` walks at 20-byte intervals
  and swaps the three text-offset words at +4, +8 and +12.
- The j-string callback at `0x2b44ac` passes the supplied body size through
  `0x6ff41c` to allocation at `0x6e4b60`, then copies that many bytes. The pool
  resides at the owner's +0x204 field. This supports appending inside the
  resized pool; it is not permission to append outside the loader's data.

These checks establish storage and font-index behavior. They do not establish
every Spirit display consumer, temporary name buffer, runtime fit, or draw state.

## Reproduction

Use the bundled Python reported by `load_workspace_dependencies` for the font
build (Pillow and numpy); the original Python 3.8 can run the tests/deployer.
All writing entry points default to dry run. Read the printed English/paths
before repeating with `--apply`. Existing outputs are never overwritten.

```powershell
python -m tools.ui_spirits check
python -m unittest discover -s tests -v
# With the bundled Python executable:
python -m tools.ui_build
python -m tools.ui_build --apply
python -m tools.ui_deploy
python -m tools.ui_deploy --apply
```

32 tests pass, including new checks for separate roles sharing one source
string, missing/duplicate/foreign pointers, unchanged unrelated integers,
redirected output pointers, and odd-length encoding with symbols/newlines.
CPK readback uses the independent ITOC reader already tested in the pipeline.

Built archive SHA-256:

- RPW_DATA.CPK: `67f18002bb4e08c6101d3f228eed4b20382b4966ee5ced21fd577c37d40872f9`
- TPACKPS3.CPK: `a9f408f302d48db3a92d09d4ae80b64673330778c299fc7aa5aeb2ee2dd4365e`

`build.json` records the pair mapping, occurrence offsets, output hashes and
explicit unverified runtime/layout flags. `ui_patch_manifest.json` in an applied
game folder records all 82 copied-file hashes. Original/reference assets remain
immutable. Nothing in `work/` should be committed or published as game content.
