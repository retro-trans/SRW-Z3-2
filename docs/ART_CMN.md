# Battle art in BTLC/CMN.CPK

`/PS3_GAME/USRDIR/DATA/BTLC/CMN.CPK` holds the battle-screen lettering:
the Maximum Break banner and the Combo Attack / Counter / Attack Again /
Support Attack / Support Defense banners. This document covers
`tools/cmn_art.py`. Nothing here has been checked in game. A texture
preview is not in-game evidence.

| File | Purpose |
|---|---|
| `tools/cmn_art.py` | Guards, renderers, record relocation, `plan()`, `verify_archive()`, previews, Jigoku evidence |
| `work/translation/en/ui/cmn_art.json` | Catalog: 6 labels, Japanese, English, evidence for the wording |
| `work/ui/textures/cmn/cmn_tengoku_textures.png` | Contact sheet: all 26 Tengoku textures, tagged japanese / english / none |
| `work/ui/textures/cmn/cmn_jigoku_original_textures.png`, `cmn_jigoku_shipped_changed.png` | Jigoku's original 20 textures and the 4 that 0.6.24 changed |
| `work/ui/textures/cmn/cmn_inventory.json` | Per-texture inventory (size, format, offset, pixel SHA-256, text, Jigoku match) and the evidence below |
| `work/ui/textures/cmn/cmn_before_after.png` | Before/after for t16, t10 and t11 |
| `work/ui/textures/cmn/cmn_maximum_break_projection.png` | The nine Maximum Break quads drawn at their initial keyframe, before and after |
| `tests/test_cmn_art.py` | 15 tests (see section 6) |

```
python -m tools.cmn_art plan                      # dry run: report only
python -m tools.cmn_art inventory      [--apply]  # contact sheets + cmn_inventory.json
python -m tools.cmn_art preview        [--apply]  # before/after sheets
python -m tools.cmn_art compare-jigoku            # evidence against Jigoku (read only)
```

## 1. Format

- The archive is ITOC-only, with one member (id 0). It is stored
  CRILAYLA-compressed: 502,008 bytes stored, 3,880,448 decoded. Archive
  SHA-256 `cdef5585…`, member SHA-256 `cd834f50…`.
- Member 0 has two parts:
  - `0x0000-0xa3ff`: an effect/animation script block. Its header words are
    little-endian (`3, 0x10, 0x20, …, 0xa3e0`), and Jigoku's header is the
    same apart from sizes.
  - `0xa400`: one GTF with **26** textures (Jigoku has 20 at `0x9de0`). Pixel
    formats are `0xA5` linear ARGB and `0x85` swizzled. `tools/gtf.py` finds
    this GTF by scanning for it.
- Text in the 26 textures (review the contact sheet):

| tex | size | content | text | Jigoku original |
|---|---|---|---|---|
| 10 | 192x48 | `合体攻撃` cyan banner | **Japanese** | identical to J t10 |
| 11 | 272x256 | `カウンター` (pink), `再攻撃`, `援護攻撃` (purple), `援護防御` (gold), 4 rows of 64 px | **Japanese** | identical to J t11 |
| 16 | 1472x176 | `マキシマムブレイク` gold banner, sampled by 9 animated quads | **Japanese** | identical to J t16 |
| 1 | 512x40 | red `MAXIMUM BREAK` ribbon | English | identical to J t1 |
| 4 | 488x72 | HP / EN gauge frame | English | differs |
| 14 | 384x40 | `CRITICAL` | English | J t14 is 384x48 and differs |
| 23 | 96x112 | word atlas `Center / Wide / ALL / MAXIMUM / Main / Assist / BREAK` | English | **new**. It takes the place of Jigoku's Japanese badge atlas t6 (136x192: `全体攻撃`, `センター攻撃`, …, `マキシマム ブレイク`), which Tengoku no longer has |
| others | | particles, emblem ring (Latin `SRW`), digits, icons, button prompts, effect sprites, frames | none | 6, 7, 8 and 17 are identical to J 9, 7, 9 and 17 |

So the Japanese art is **3 textures with 6 labels**. Jigoku's red `MAX BREAK`
badge and its four cyan attack badges have no Tengoku counterpart. Tengoku's
own t23 is already English.

## 2. Jigoku comparison and record relocation (evidence)

All of the following is reproduced by `compare-jigoku` and stored in
`cmn_inventory.json` under `jigoku`.

1. **Textures.** The pixel bytes of Tengoku t10, t11 and t16 are identical to
   Jigoku's original t10, t11 and t16 (SHA-256 `230a7c51…`, `4a031abc…`,
   `39143a65…`).
2. **What Jigoku 0.6.24 changed.** Its shipped CMN (stored uncompressed,
   4,145,488 bytes) differs from its original in four places:
   - textures 6, 10, 11 and 16
   - 53 script bytes, all inside the nine 16-byte records at Jigoku
     `0x3910…0x419c`

   Nothing else changed.
3. **The records in Tengoku.** Searching Tengoku for Jigoku's
   little-endian records finds nothing. Searching for their UV values finds
   them **big-endian** at `0x3288, 0x339c, 0x34b0, 0x35c0, 0x36d0, 0x37d8,
   0x38e8, 0x39f8, 0x3b14`. That is Jigoku's offset minus `0x688` (the
   header grew with the six extra texture descriptors and other script
   changes).
   - Every record value and every anchor (`>2h` at record − 12, or − 16 for
     the first) is equal to Jigoku's.
   - Layout of a record: `>4h4H`, which is signed `x0, y0, x1, y1` relative
     to the anchor, then texel `u0, v0, u1, v1`.
4. **The surrounding script is the same.**
   - Jigoku `0x361c-0x9b60` maps onto Tengoku `0x2f94-0x94d8` (25,924
     bytes).
   - Word for word, each pair is either identical, u32 byte-swapped, u16
     byte-swapped, or `u8 u8 u16` with the u16 swapped. The u8/u16 opcode
     headers are things like `09 02 000e` against `09 02 0e00`.
   - Only 3 words at the very edges of the range do not match.
   - The nine-record block `0x3250-0x3bf0` has no exceptions.

   So Tengoku stores the same effect grammar with big-endian fields.
5. **Only these nine quads sample t16.**
   - `strip_quads` scans the whole script for any `>4h4H` record whose UV
     covers a full-height strip of the 1472x176 atlas (`v 0..176`).
   - It finds exactly the nine, both before and after the patch. The same
     scan on Jigoku (`<4h4H`) finds Jigoku's nine.
6. **Native duplication.** Piece 3 re-samples piece 0's UV (`1,0,175,176`,
   the `マ` glyph). That is why a continuous English repaint came out
   sliced in Jigoku (`screenshot bdaa22e9`, Jigoku changelog 2026-09-29).
7. **The renderers are faithful ports.**
   - `action_label` and `banner_pixels` are ports of Jigoku
     `tools/maximum_break_art.py` (`action_tile`, `banner`, `banner_layout`).
   - With Jigoku's wording they reproduce Jigoku 0.6.24's shipped t10, t11
     and t16 **byte for byte** (`JIGOKU_SHIPPED_PIXELS`).
   - `banner_records` reproduces all nine shipped record values.
   - Measured here with Pillow 12.3.0 and the dev_flash `SCE-PS3-RD-BI-LATIN.TTF`.

## 3. What is built

| label | texture / rect | Japanese | English | source of the pixels |
|---|---|---|---|---|
| maximum_break | t16 full | マキシマムブレイク | MAXIMUM BREAK | = Jigoku 0.6.24, plus 9 records |
| combo_attack | t10 full | 合体攻撃 | Combo Attack | = Jigoku 0.6.24 |
| counter | t11 y0 | カウンター | Counter | = Jigoku 0.6.24 |
| attack_again | t11 y64 | 再攻撃 | Attack Again | = Jigoku 0.6.24 |
| support_attack | t11 y128 | 援護攻撃 | Support Attack | = Jigoku 0.6.24 |
| support_defense | t11 y192 | 援護防御 | **Support Defense** | rendered fresh in the same style. Jigoku said "Support Defend"; this project uses "Support Defense" (eboot `（援護防御ＯＮ／ＯＦＦ）`, voice corpus) |

- **Maximum Break.**
  - The banner is repacked into nine whole-letter cells
    `MA|XI|M|U|M|B|R|EA|K`. Each cell has a 16 px transparent gutter, plus
    an extra 24 px after `MAXIMUM`.
  - The nine records are rewritten so that:
    - their screen cells are contiguous from x −736 to 736 and y −88 to 88
      around the effect origin
    - each piece samples only its own cell, inset by one texel
  - Anchors and all keyframe, timing and motion bytes are unchanged.
  - The new values, big-endian at Tengoku offsets, are exactly Jigoku's
    shipped values (`tests/test_cmn_art.py::SHIPPED_RECORDS`).
- **Action labels.**
  - Rodin Bold Italic, fitted to the cell height minus a 6 px border, and
    condensed only when too wide.
  - A blurred tint edge, then a white-to-tint vertical gradient.
  - Condensing is reported as `squeeze`. Below 0.55 the label is listed under
    `report['review']`. Jigoku shipped Combo Attack at 0.567, and Support
    Defense comes out at 0.576. Nothing is flagged today.
- **Catalog.**
  - Geometry and style are owned by the code; the catalog owns only the
    wording.
  - `en: null` leaves that label's Japanese untouched and lists it under
    `pending`. If every label is null, no member is replaced.
  - Changing the Maximum Break wording is refused, because it needs a new
    nine-cell plan.
  - `attack_again` has a note: the skill name elsewhere is "Re-Attack". The
    Jigoku banner wording is kept and the orchestrator can switch it.

Result: member 0 output SHA-256 `11522509…` (input `cd834f50…`).

## 4. `plan()`, verification, game_build and iso_write integration

`cmn_art.plan(settings=None, catalog=None, source=None)` returns
`{'members': {0: bytes}, 'sources', 'intended', 'records', 'report'}`.

- **Source guards:**
  - member length and SHA-256
  - the 26-texture layout at `0xa400`
  - the pixel SHA-256 of t10, t11 and t16
  - all nine records and anchors
- **`verify_member`**, inside `plan()`:
  - the nine records hold their intended values
  - the anchors are unchanged
  - every other script byte is identical
  - via `texture_art.verify_member`:
    - t10, t11 and t16 decode to exactly the intended pixels
    - every other texture and every header byte is identical
    - the member actually changed
- **`verify_archive(path, art)`** decodes member 0 from the built CMN.CPK,
  compares it with the plan and runs `verify_member` again.

**Exact change for `tools/game_build.py`** (not applied here). `iso_write.py`
needs **no change**: it already reads `report['disc_files']` and checks
`report['outputs'][name]`.

```python
# plan(): next to `art = texture_art.plan(pages, settings)`
from tools import cmn_art
cmn = cmn_art.plan(settings)
# summary dict
'cmn_art': {k: v for k, v in cmn['report'].items() if k != 'records'},
# return dict(...)
..., cmn=cmn)

# build(): after the TPACK block (texture_art.verify_archive)
from tools import cmn_art
disc_files, cmn_extra = {}, {}          # shared with the other art packs: merge, never overwrite
if p['cmn']['members']:
    cmn_source = verified_source(p['settings'], cmn_art.CMN)
    build_cpk(cmn_source, output / 'CMN.CPK', p['cmn']['members'], compress=False)
    cmn_extra = dict(
        cmn_archive=compare(cmn_source, output / 'CMN.CPK', p['cmn']['members']),
        cmn_art=dict(p['cmn']['report'], archive_members_verified=cmn_art.verify_archive(output / 'CMN.CPK', p['cmn'])))
    disc_files[cmn_art.CMN] = 'CMN.CPK'

# build(): right after the existing `outputs = [...]` / SRVC lines, before `report = dict(...)`
outputs += sorted(disc_files.values())
# report = dict(p['summary'], ..., **cmn_extra, disc_files=disc_files,
#               outputs={name: sha256_file(output / name) for name in outputs})   # unchanged line
```

Notes on the snippet:
- `outputs += …` has to run after the existing `outputs = [...]` line and
  before `report` is built, so that `report['outputs']['CMN.CPK']` exists for
  `iso_write`.
- `disc_files` is a single dict. If the EFFPS3, AIDDATAPACK and OP agents
  also add entries, **merge** them into one dict, keyed by disc path. Don't
  let one overwrite another.
- Version, changelog, `--apply` and the ISO stay with the orchestrator.

**`compress`: recommend `False`.**
- `compress=False`:
  - CMN.CPK is 3.9 MB, against 0.5 MB pristine. That is the layout Jigoku
    shipped in 0.6.24 (4,145,488 bytes, member stored raw).
  - It is the proven path, and it costs only about 3.4 MB in the ISO and
    the patch.
- `compress=True`:
  - It also builds and verifies: our CRILAYLA stream round-trips through
    the reader, and `compare` reports `replaced_compressed: 1`. The tests
    cover both forms.
  - Use it only if patch size matters. It adds the same "real CRI decoder"
    risk as TPACK.

## 5. Risks / in-game checks (RPCS3, record screenshots in `work/ui/`)

1. **Maximum Break playback** (the main risk). The records are byte-for-byte
   what Jigoku shipped, but nobody has seen them animate in Tengoku. Trigger
   a Maximum Break and check:
   - all of `MAXIMUM BREAK` is legible
   - no letters are duplicated or sliced
   - letters do not overlap during the fly-in. The keyframes still move each
     piece from its old Japanese anchor, so the motion during the animation
     is the native one and only the settled phrase was laid out.

   Jigoku's 0.6.24 version of this fix was also built without playback
   confirmation (Jigoku changelog: "in-game playback confirmation pending").
2. **Byte order.** We write big-endian because Tengoku's copy of the block
   is big-endian word for word (section 2.4). If the banner comes out
   garbled or the effect does not show, suspect this first. The pristine
   values read sensibly only as BE.
3. **Banner meaning / trigger screens:**
   - Combo Attack: a combination attack
   - Counter: the Counter skill
   - Attack Again: the Re-Attack skill
   - Support Attack and Support Defense: support actions in battle

   Check fit and that the banner still reads after its in-game scaling.
   The labels are condensed 0.58-0.99, the same range as Jigoku.
4. **Wording calls for the orchestrator:**
   - "Support Defense" differs from Jigoku's "Support Defend" on purpose.
   - "Attack Again" against the skill name "Re-Attack".
5. **Fonts and renderer.** Pixels depend on Pillow/FreeType and the dev_flash
   font, read only.
   - `test_renderers_reproduce_jigoku_shipped_pixels` fails loudly if a
     different Pillow version changes the output.
   - `plan()` always verifies against its own rendering.
6. **Other agents.** Only `CMN.CPK` is touched here. EFFPS3, AIDDATAPACK and
   OP are separate archives.

## 6. Tests

`& $py -m unittest tests.test_cmn_art` (15 tests, about 10 s; the real-data
classes are skipped without the pristine CMN, the fonts or the Jigoku files).

- **Catalog:**
  - the shipped catalog is valid and complete
  - it rejects a wrong Japanese, a wrong rect, non-ASCII or multi-line
    English, changed Maximum Break wording, and a missing label
- **`verify_member` (synthetic member):**
  - accepts the intended member
  - rejects a wrong record, a changed anchor, a changed script byte, a
    changed pixel, a record outside the allow-list, and an unchanged member
  - `strip_quads` finds exactly the pieces
- **Real data:**
  - the native duplicate glyph
  - the records equal Jigoku's shipped values, relocated
  - the cells are contiguous, unclipped and use 9 distinct UVs, and are the
    only strip quads
  - only the nine records and t10, t11 and t16 change
  - the renderers reproduce Jigoku 0.6.24's pixel hashes
  - Support Defense changes only its row
  - pending labels leave the art untouched, and no English means no member
  - source drift fails closed
  - archive round trip with `compress=False` and `True`, through
    `verify_archive` and `verify_archives.compare`
- **Jigoku evidence** (needs `E:/Projects/SRW Z3`, read only): record
  equality, block equivalence, the shipped diff being confined to the
  records, strip-quad counts, and renderer calibration.
