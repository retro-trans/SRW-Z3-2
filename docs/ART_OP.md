# Opening-demo series captions (OP.CPK) and the title screen

This document covers two things:
- The series-name captions of the opening demo, `/PS3_GAME/USRDIR/DATA/BTLC/OP.CPK`.
  They are built by `tools/op_art.py`.
- An inventory of the title-screen art (logo, footer, menus) in
  `ANIME/EFFPS3.CPK`. This part is research only; nothing is patched.

Nothing here has been checked in game. A texture preview is not in-game
evidence.

| File | Purpose |
|---|---|
| `tools/op_art.py` | Caption catalog, renderer, `plan()`, `verify_archive()`, previews, title inventory |
| `tests/test_op_art.py` | 11 tests (synthetic + real source) |
| `work/translation/en/ui/op_art.json` | Caption catalog: 31 strips, JP/EN, guards, evidence |
| `work/ui/textures/op/op_captions_original.png` | The 31 original strips |
| `work/ui/textures/op/op_captions_english.png` | Each original strip above its English render |
| `work/ui/textures/op/op_inventory.json` | Per strip: member, texture, offset, JP/EN, ink boxes |
| `work/ui/textures/op/title_screen_text.png` + `title_screen_inventory.json` | Title-screen textures that carry text, with their sprite rectangles |
| `work/ui/textures/op/title_screen_sprites.png`, `title_screen_backgrounds.png` | All title-screen textures (contact sheets) |

```
python -m tools.op_art plan                       # dry run: report only
python -m tools.op_art catalog [--apply]          # (re)build op_art.json from the pristine strips
python -m tools.op_art preview [--apply]          # contact sheets + op_inventory.json
python -m tools.op_art title-inventory [--apply]  # EFFPS3 title screen, read only
```

Run these with the bundled Python 3.12 (numpy + Pillow).

## 1. OP.CPK

### Container
- ITOC-only CPK: 3 members, `Align` 16, `ContentOffset` 2432.
- All three members are stored CRILAYLA-compressed.
  - Archive: 756,716 bytes on disc.
  - Decoded: 3,279,248 + 3,279,280 + 3,607,312 bytes.
- Archive sha256 is `09d3fb03…` (source manifest).
- Decoded member hashes are pinned in `op_art.MEMBER_SHA256`.
- Jigoku's OP.CPK had 4 members x 6 strips. None of them match Tengoku.

Each member holds:
- a 0x60-byte container prefix (LE `u32 count, 0x10, 0x50…`)
- one GTF at **0x60**
- the demo's effect scripts after the pixel data

The GTF layout:

| member | strips | first pixel offset |
|---|---|---|
| 0 | 10 | 0x1e0 |
| 1 | 10 | 0x1e0 |
| 2 | 11 | 0x260 |

Every strip is 1280x64 `0xA5` (linear A8R8G8B8), 327,680 bytes.

### What the strips show (31)

All 31 strips are series names. The texture order is the demo's order and is
not alphabetical.

| member | strips |
|---|---|
| 0 | Gundam UC, Getter Robo Armageddon, Orguss, Evangelion 3.0, Zambot 3, Zeta Gundam, Gurren Lagann, Full Metal Panic!, Tetsujin-28, Macross F Wings of Goodbye |
| 1 | Gargantia, Gunbuster, SEED Destiny, Aquarion EVOL, Dai-Guard, Daitarn 3, Turn A, The Big O, Trider G7, Gundam 00 the Movie |
| 2 | Genesis of Aquarion, Char's Counterattack, Godmars, Gundam W Endless Waltz, Code Geass R2, Dancouga Nova, Macross 7, VOTOMS Alone Again, Gundam X, Mazinger Edition Z, Diebuster |

**Identification.** Each strip was read visually from the contact sheet; the
result is `op_art.IDENTIFIED`, keyed by the rpw_names series key. As a
cross-check, `catalog` renders the 31 names in a Mincho face (Latin
half-width and letter-spaced, as on the strips) and correlates them with the
strip ink.
- Every strip's identified name ranks first among the 31. This shows the
  texture order is not permuted. The smallest margin is 0.013, so this is a
  coarse check.
- Among all 45 series names in the table, only `m0_t3` (Evangelion **Q**) is
  not first. It ranks 3rd behind `序`, a name that differs by one glyph. The
  strip visibly reads `：Q`.

**English** comes from `work/translation/en/ui/rpw_names.json` →
`strings.series`, which holds the glossary's official names
(`work/tengoku/library_briefs/GLOSSARY.md`). The catalog stores it with
`en_source`. Test `test_catalog_english_is_the_glossary_series_name` fails if
the catalog and rpw_names drift apart. To change a name, change the glossary /
rpw_names, then run `op_art catalog --apply`.

### Original encoding (measured on all 31 strips)

- R = G = B = the white fill coverage, in 16 levels (multiples of 17).
- Alpha = the fill plus a soft **black halo** about 5 px wide on every side.
  There is no drop-shadow offset: the fill and halo centroids agree.
  - That is white text over a black halo, straight alpha, with RGB = 0
    wherever alpha = 0.
- Fitted halo model:
  `halo = (clip(3 · gauss(dilate(fill, 1 px), σ=1.25)))^0.7`
  and `alpha = fill + halo·(1 − fill)`.
  - Re-encoding each original's own fill with this model reproduces its alpha
    with a mean error of 5.4/255 (worst strip 8.0) on the halo region.
  - Wherever alpha = 255, the grey matches exactly. This is a test.
- Fill centre is x ≈ 639.5. Japanese ink spans y 12–52; halo y 8–57.
- The widest original fill is x 30–1249 (Gundam 00).
- The strips' own Latin letters (`UC`, `SEED DESTINY`, `Endless Waltz`,
  `A wakening of the Trailblazer`) are a bold serif:
  - cap height 29 px
  - baseline under row 47

### Renderer (`op_art.caption_pixels`, `STYLE`)

- Face: `SCE-PS3-MT-B-LATIN.TTF` (PS3 Matisse Bold). Compared with Matisse
  Regular, the PS3 sans faces and Times Bold, it is the closest to the strips'
  own Latin. It is read from the RPCS3 dev_flash font folder, read only.
- Size: cap height 29 px on baseline row 47, the same as the game's Latin.
  Rendered at 4x and box-filtered to coverage.
- Placement: centred on x = 639.5.
- Width limit: a fill wider than 1220 px is first condensed horizontally down
  to 0.80, then the size shrinks. `needs_review` is set when the squeeze is
  below 0.85 or any shrink is applied.
- Encoding: `op_art.encode` applies the fitted halo and quantises the grey to
  the 16 original levels.
- Result for all 31 names:
  - Only `m1_t9` (Mobile Suit Gundam 00 The Movie: A Wakening of The
    Trailblazer) is condensed, to 0.907. It fills x 30–1249, exactly the
    original's extent.
  - Nothing is shrunk and nothing needs review.
- Overrides go in `op_art.json` → `"style"` (any `STYLE` key).

### `plan()` and verification

`op_art.plan(settings=None, catalog=None, style=None)` returns
`{'members': {id: bytes}, 'sources', 'intended', 'report', 'source_path'}`.

1. **Source guards:**
   - the full decoded-member SHA-256
   - the GTF at 0x60
   - the strip count, format, size and texture index
   - a per-strip pixel SHA-256 from the catalog (`texture_sha256`)
2. **Rendering:** each strip whose `en` is set is rendered. A strip with
   `en: null` is left untouched and listed in `report['pending']`; a member
   with no English is not replaced at all.
3. **Per-member check:** `texture_art.verify_member` decodes the new member.
   - Every rendered strip must equal the intended pixels.
   - Every other strip must be byte-identical.
   - The container prefix, GTF header and scripts must be unchanged.
   - The length must be equal and the member must actually change.
4. **Archive check:** after the archive is written,
   `op_art.verify_archive(path, art)` reads each replaced member back from the
   built OP.CPK and repeats step 3.

`plan` takes under 4 s.

## 2. Integration (exact change, not applied)

The orchestrator applies this; version, changelog and `--apply` stay with the
orchestrator.

`tools/game_build.py`:

```python
# plan(): next to the texture_art.plan(...) call
from tools import op_art
op = op_art.plan(settings)
summary['op_art'] = {k: v for k, v in op['report'].items() if k != 'captions'}
# ... and add op=op to the returned dict:  return dict(..., art=art, op=op)

# build(): after the TPACKPS3 lines
op_report = None
if p['op']['members']:
    build_cpk(p['op']['source_path'], output / 'OP.CPK', p['op']['members'])   # raw members, see below
    op_report = op_art.verify_archive(output / 'OP.CPK', p['op'])
# outputs list: append 'OP.CPK' when it was built
if op_report is not None:
    outputs.append('OP.CPK')
# report = dict(...): add
                  op_archive=(compare(p['op']['source_path'], output / 'OP.CPK', p['op']['members'])
                              if op_report is not None else None),
                  op_art=dict(p['op']['report'], archive_members_verified=op_report),
                  disc_files=disc_files,
# with, before the report:
disc_files = {}                       # {disc path: output name}; other art archives add theirs here
if op_report is not None:
    disc_files[op_art.DISC] = 'OP.CPK'
```

- `build_cpk` is `tools.cpkpatch.build` and `compare` is
  `tools.verify_archives.compare`; both are already imported there.
- `p['op']['members']` maps member id to bytes, which `cpkpatch.build` and
  `compare` accept directly.

`tools/iso_write.py` needs **no change**:
- `main()` already adds every `report['disc_files']` entry (disc path → output
  name) to the replacements.
- It refuses a file whose sha256 differs from `report['outputs'][name]`. That
  is why `OP.CPK` must be in `outputs`.
- The file is appended on a sector boundary like the others, and
  `verify()` reads it back through both trees.

If several art tools add `disc_files` (EFFPS3, CMN, AIDDATAPACK), build the
dict once and add each archive with an "already listed" check. `iso_write`
also refuses duplicates.

### Compress or not

| option | OP.CPK size | build time | evidence |
|---|---|---|---|
| `compress=False` (default, **recommended**) | 10,168,272 bytes (from 756,716) | 0.1 s | Jigoku 0.6.24 shipped its OP.CPK with raw (uncompressed) replacement members, 7.9 MB |
| `compress=True` | 736,732 bytes | about 13 s with one worker | Round trip checked by our decompressor only |

- Recommendation: `compress=False`.
  - The archive is small either way, and this is the layout Jigoku released.
  - The ISO grows by about 10 MB.
- Use `compress=True` only if the TPACK CRILAYLA streams are confirmed in game
  first, or to keep the Retro Trans Tools delta smaller.
- Both options are exercised by `test_plan_and_archive_round_trip`
  (build → `compare` → `verify_archive`).

## 3. Title screen (EFFPS3, research only)

Location: LUACPK member 1 defines the title animations. The EFFPS3 member is
the constant + 1, the same rule as Jigoku (`ScAnime_Z3TITLE = 295` → member
296).

| constant | value | EFFPS3 member |
|---|---|---|
| `ScAnime_Z3TITLE_2D` | 228 | **229** |
| `ScAnime_Z3TITLE_BUTTON_2D` | 229 | **230** |
| `ScAnime_Z3TITLE_HAGURUMA_2D` (gears) | 230 | **231** |
| `ScAnime_Z3TITLE_MENU_2D` | 231 | **232** |

None of these members is raw-identical to Jigoku's. Members 229 and 232 are
stored uncompressed, so they read instantly.

| member / tex | size | text | sprite rects (x, y, w, h; record count) |
|---|---|---|---|
| 229 t1 | 864x304 | **JP** main wordmark 第3次スーパーロボット大戦 | (0,0,861,300) ×428 |
| 229 t2 | 536x192 | **JP** subtitle 天獄篇, whole | (0,0,536,187) ×832 |
| 229 t12 | 648x192 | **JP** subtitle 天獄篇 as **three per-character cells** | (0,0,208,192), (216,0,216,192), (440,0,208,192), ×410 each |
| 229 t0/t6/t10 | 1280x720 | none (space / sun backgrounds) | |
| 229 t4/t5/t14–t20 | | none (the Z frame and its fiery fill frames) | |
| 230 t3 | 568x168 | English `press any button` | |
| 232 t7/t8/t22 | 464x368 | English Start / Load / Continue / Library / Download / PlayStation®Store (3 states) | 6 rows each |
| 232 t11/t13/t23 | 352x304 | **JP** Library submenu: ロボット大図鑑 / キャラクター事典 / 用語事典 / サウンドセレクト / シナリオチャート (3 states) | t11: (0,0,312,64) (0,64,351,56) (0,120,192,64) (0,184,344,56) (0,248,344,48); t13/t23 differ by a few px |

Findings:
- **There is no native footer.** No title texture carries a copyright or
  version line; the boot copyright screens are TPACK member 0.
  - Jigoku's "title footer" (`title_footer.py`) was a build stamp it added
    itself: `v<version>` / `github.com/retro-trans` painted into the bottom
    right of the stationary 1280x720 background.
  - Porting it needs:
    - deciding which of t0/t6/t10 stays on screen behind
      "press any button" (unverified; t0 is the galaxy, t6/t10 are sun
      frames)
    - the version string from game_build
- **Logo.** The wordmark (t1) and the subtitle (t2, t12) are the only Japanese
  logo art.
  - Jigoku replaced its wordmark and subtitle with a user-approved generated
    English wordmark (`docs/TITLE_LOGO.md` there). That art is a Jigoku asset
    and does not fit Tengoku's 864x304 / 536x192 sprites.
  - Tengoku needs new, approved art.
  - t12 is sliced into three character cells that animate separately. An
    English subtitle there must be repacked into three cells (or the record
    rectangles edited); a continuous repaint would come out sliced. This is
    the Maximum Break pitfall.
- **Library submenu** (232 t11/t13/t23) is Japanese and still needs
  translating.
  - Five labels in three states; each label must fit its sprite rectangle,
    and those differ slightly per state.
  - Jigoku's `title_library_buttons.py` (720x512 atlas in member 296) is a
    method reference only; the layout differs.
- These members belong to the EFFPS3 archive build, so they should be patched
  by the EFFPS3 owner in that one `cpkpatch.build` call. `op_art` only reads
  them (`title-inventory`).

## 4. Risks and checks in game

1. **The caption ↔ series pairing.** Each strip's English is tied to its own
   texture, so a demo order mismatch is impossible. The identification itself
   is visual plus a coarse correlation; see the contact sheet.
2. **Style.** The English uses the game's own Latin size and the original
   halo encoding. Check in the opening demo:
   - the halo strength on bright backgrounds
   - that no dark box shows
   - that the long Gundam 00 line (condensed to 0.907, full 1220 px) reads
     well
3. **Name wording.** Names come from the glossary as they are. Two to check:
   - `m1_t9` uses the glossary's "A Wakening of The Trailblazer". The strip
     itself reads "A wakening of the Trailblazer" (official capitalisation:
     lower-case "wakening" and "the"). If the glossary changes, rerun
     `catalog --apply`.
   - `m0_t1` "Getter Robo Armageddon" is the official English title for
     真（チェンジ！！）ゲッターロボ 世界最後の日, so it is shorter than the
     Japanese.
4. **Storage.** Raw members (`compress=False`) are the Jigoku-released layout.
   The compressed form relies on our CRILAYLA encoder (see `docs/TEXTURES.md`
   §7.1).
5. **Retro Trans Tools.** OP.CPK becomes a new replaced file in the
   whole-ISO patch: +10 MB raw or −20 KB compressed. Confirm the patch still
   applies, per AGENTS.md.
6. **Fonts** are read from `E:/RPCS3/dev_flash/data/font`, and the output
   depends on the Pillow/FreeType version. Re-render on the build machine.
   `plan()` verifies against its own rendering, so do not commit rendered
   bytes.

## 5. Map badges (TPACK member 2, textures 4 and 5)

`work/translation/en/ui/map_badges.json` now exists, so `texture_art.plan()`
renders both badges and `report['badges']['todo']` is empty.

| texture | JP | EN | reasoning |
|---|---|---|---|
| 4 | 搭載 | `Aboard` | The badge marks a ship carrying units. Jigoku's map command for the verb is "Board"; the badge shows the state. "Loaded" reads like ammunition. |
| 5 | マルチアクション | `Multi-` / `Action` | The hyphenated term on two lines, like マルチ / アクション. A single line `Multi-Action` fits only at about half height. |

- `texture_art.badge_preview` now shows the catalog English (placeholders only
  when the JSON is empty). Sheet: `work/ui/textures/preview_map_badges.png`.
- Check in game:
  - "Aboard" spans almost the whole 76 px box, while the Japanese sat at
    x 3–46. Check how much it covers the ship sprite.
  - Check that the Multi-Action badge is readable at map zoom.
- `docs/TEXTURES.md` §3 still says map_badges.json is "not created yet". That
  doc belongs to another workstream; update it when merging.
