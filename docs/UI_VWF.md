# Tengoku VWF test build

`ui-0.1.1-vwf` is built under `work/output/builds/ui-0.1.1-vwf` and applied to
the complete folder `work/output/game-ui-0.1.1-vwf`. All 82 files pass readback.
It has not been booted or visually verified in-game. Nothing is published.

## Port and scope

The reference is `../SRW Z3/tools/eboot.py` (`vwf_stub`, `apply_vwf`) and
`tools/digraph.py` (`encode_letters`, `raster_letter`, compact badges). The
target implementation uses the same ordinary-letter advance rule:

- Width 32: keep the original caller pitch, including Japanese and badges.
- Narrow letter: width / 32 times the live glyph quad width.

The target drawer is independently located at VA 0x14158; its advance load at
0x147dc is `lfs f13,0x94(r1)`. The hook branches to VA 0x93eb10, reads the cell
index from the caller's stack +0xc2, and uses a 4,480-byte table at 0x93d990.
Out-of-range indices use original pitch. The 132-byte stub owns a 112-byte
stack frame, preserves touched registers and CR, leaves LR untouched, and
branches back to 0x147e0 with only f13 changed. It preserves f0, the live pen X.

The table/stub occupy the originally unmapped 9,848-byte gap after the first
LOAD. That LOAD's file and memory sizes grow through the stub; the second LOAD
does not move. Only this program-header size pair, one branch and the allocated
gap bytes change relative to the reviewed program ELF. Restoring those ranges
must reproduce the complete baseline byte for byte.

There are 62 individual Latin glyphs and 20 separately encoded one-cell badges,
allocated from 469 cells verified blank on both target pages and unassigned in
cp932. Other widths stay 32. Names/descriptions use two encoded bytes per letter;
badges remain two bytes total. The original Japanese pool stays intact, with
4,696 appended bytes and exactly 129 changed Spirit pointers. Three sentinel
fields remain original. All 133 other font members are preserved. Dialogue,
voice, gameplay data and terminology authoring are unchanged.

Latin uses the same local PS3 Rodin face recorded in UI_BUILD.md, natural
advances, 22px capitals, 25px baseline and a 9px space. Badges are centered in a
32px cell with 12px capitals. All glyphs pass cell-bound checks. The baseline
leaves room for Rodin descenders. These are atlas texels, not measured widget
pixels; the longest name and every display context still need game testing.

## Executable baseline acceptance

The initial research reader was marked analysis-only because its whole-file
SHA-1 did not match the developer ELF digest embedded in the SELF. That remains
true. It must not be described as byte-exact recovery of the developer ELF.

For this local runtime test, `tools/self_elf.py` instead verifies the program
image used by RPCS3's `SELFDecrypter::WriteElf`: reconstruct header/program
segments and section headers, omitting non-program payloads. Every program
section HMAC passes (indices 0–4), and every file-backed allocated ELF section
is checked to lie inside an authenticated LOAD with matching file/VA mapping.
The two excluded metadata entries are reported explicitly; their HMACs are not
claimed verified. Source and reviewed output SHA-256 are pinned. This resolves
the earlier restriction for a program-ELF test build only; it is not a boot test.

The reference algorithm was inspected from local copies of RPCS3
[unself.h](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Crypto/unself.h) and
[unself.cpp](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Crypto/unself.cpp).
An isolated copy of the installed RPCS3 executable was tried as a CLI oracle;
it produced no decrypted output and was stopped. No CLI-oracle agreement is
claimed. The user's emulator was not stopped or controlled.

## Reproduction and evidence

Use the bundled Python with Pillow, numpy and cryptography for the build.
Use the system Python with Capstone for all tests; without Capstone the stub
execution test is explicitly skipped, not a verified pass.

```powershell
python -m unittest discover -s tests -v
# Run with the bundled Python executable:
python -m tools.ui_vwf_build
python -m tools.ui_vwf_build --apply
python -m tools.ui_deploy
python -m tools.ui_deploy --apply
```

Review dry-run English and destinations before `--apply`. Existing output
folders are refused. The old pair builder remains `tools.ui_build`, with
explicit old-build arguments required when calling the updated deployer.

All 36 tests passed, with none skipped. New tests cover lossless single-letter
encoding (including spaces/newlines), separate badges, all Spirit fields and
unrelated RPW bytes. A Capstone-based instruction interpreter executes the
actual generated stub across narrow, full-width and invalid indices, checks
quad width rather than pitch is used for letters, and verifies GPRs, CR, other
FPRs and caller memory are preserved. This is bounded instruction testing,
not full PS3 emulation or proof of every calling context.

Built SHA-256:

| File | SHA-256 |
| --- | --- |
| EBOOT.BIN | `a6e099283d7d28254f92da45e0d39da94260cab9c5af1d9ca2c06875c9696b2b` |
| RPW_DATA.CPK | `84a06e2178ef95f1c21a176494720ffa3cfe04dcc2950ee241bea28afee73852` |
| TPACKPS3.CPK | `7423a76b3708598dddd44e58f3bee6f34371551643d03bf96e6cd42edbb63e24` |

`build.json` records widths, encoded occurrence offsets, executable ranges and
archive preservation checks. `font_preview_sample.png` was inspected as a
texture preview; it is not an in-game screenshot.

## Activation completed — 2026-09-11

The user authorized activation with “Do it.” RPCS3 was confirmed closed before
staging and replacing files. `tools/ui_activate.py` was dry-run and reviewed,
then applied. RPCS3 still registers `game-ui-0.1.0`; that folder now contains
VWF ui-0.1.1-vwf and its matching deployment manifest. The user can launch the
existing game entry normally. A fresh full VWF copy also remains available.

These actual Tengoku installed paths were independently discovered and
hash-matched before activation (the hashes below identify their backups):

- `BLJS10299_DATA/USRDIR/INSCO/DATA0014.DAT`: old pair-build RPW_DATA.CPK,
  SHA-256 `67f18002bb4e08c6101d3f228eed4b20382b4966ee5ced21fd577c37d40872f9`.
- `BLJS10299_DATA/USRDIR/INSCO/DATA0141.DAT`: old pair-build TPACKPS3.CPK,
  SHA-256 `a9f408f302d48db3a92d09d4ae80b64673330778c299fc7aa5aeb2ee2dd4365e`.

Installed root: `E:/RPCS3/dev_hdd0/game/`. Both cache files now match the VWF
RPW/font hashes in the table above. The three registered-game binaries and
deployment manifest were updated together; all six destinations passed hash
readback. Source ISO, extracted data, saves, install UPDATE.LOG and RPCS3
registration were not modified. No emulator launch or navigation was performed.

Backups and before/after hashes are recorded under
`work/tengoku/activations/ui-0.1.1-vwf/activation.json` with state `activated`.
The activator verifies backups before staging, rejects unknown source states,
requires RPCS3 closed, and rolls back committed files if replacement fails.
If manual rollback is needed, close RPCS3 and restore all six recorded files
as a matched set. Do not restore only the executable or only the cache.

Activation commands were `python -m tools.ui_activate` followed by
`python -m tools.ui_activate --apply` with the bundled Python. Cache writes
require filesystem permission outside this repository. The command is a
one-time old-build-to-VWF transition and refuses an already activated build.
VWF boot and visual layout remain unverified; the user retains navigation.
