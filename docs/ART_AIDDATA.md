# Texture art in AIDDATAPACK.CPK

`/PS3_GAME/USRDIR/DATA/AIDDATA/AIDDATAPACK.CPK` (54 members, sha256 `6d94a1e2…`).
The tool is `tools/aid_art.py`, and its catalog is
`work/translation/en/ui/aiddata_art.json`. Nothing here has been checked in game.
A texture preview is not in-game evidence.

| File | Purpose |
|---|---|
| `tools/aid_art.py` | `plan()`, `verify_archive()`, `catalog`, `inventory`, `preview`, `jigoku` |
| `work/translation/en/ui/aiddata_art.json` | 65 cells: JP, EN, source, style, rect, measured ink box, source pixel SHA-256 |
| `work/ui/textures/assets/aid_m001_jigoku_0.6.24_cells.png` (+ `.json`) | Jigoku 0.6.24 pixels of its 28 cells, with per-cell hashes |
| `work/ui/textures/aiddata/inventory.json` | All 54 members: kind, sizes, SHA-256, Jigoku-identical members, art or not |
| `work/ui/textures/aiddata/aid_m001_t{0..3}_cells.png` | Atlas at 2x with every cell boxed and labelled (blue = Jigoku reuse, yellow = new, grey = keep) |
| `work/ui/textures/aiddata/aid_m001_vs_jigoku.png` | Each atlas texture: Tengoku, Jigoku original and Jigoku 0.6.24, side by side |
| `work/ui/textures/aiddata/aid_other_textures.png` | Members 2, 3 and 7-18 |
| `work/ui/textures/aiddata/aid_m001_cells_before_after.png`, `aid_m001_t{0,2,3}_before_after.png` | Review sheets of the plan output |
| `work/tengoku/cache/aiddata_members/` (and `aiddata_jorig/`, `aiddata_jship/`) | Decoded members, keyed by the stored-member SHA-256 (git-ignored, safe to delete) |
| `tests/test_aid_art.py` | 13 tests |

```
python -m tools.aid_art plan                 # dry run: report only
python -m tools.aid_art inventory --apply    # inventory.json + contact sheets
python -m tools.aid_art preview --apply      # before/after sheets
python -m tools.aid_art catalog [--apply]    # refresh measured fields; keeps the English in the file
python -m tools.aid_art jigoku [--apply]     # re-extract the Jigoku asset (reads Jigoku, never writes it)
```

## 1. Members (evidence: `inventory.json`)

| Member | Content | Art with text? |
|---|---|---|
| 0 | `FSSA` UI layout and cp932 string pool (1.04 MB): quads, menu captions, help lines | No. This is text, drawn by the font through the EBOOT hook path. **Not touched.** |
| 1 | GTF: 4 swizzled (0x85) 512x512 A8R8G8B8 atlases of word sprites and icons | **Yes**: textures 0, 2 and 3. Texture 1 has frames only (its one word, `X:Pilot`, is already English). |
| 2, 3 | GTF: 256x256 swizzled, fully black | No |
| 4 | Binary layout with internal part names | No |
| 5 / 6 | `SB2T` (cp932) / `UB2T` (UTF-8) string tables | No (text) |
| 7-18 | GTF: 1280x720 linear backgrounds (members 10 and Jigoku 6 are identical) | No |
| 19-53 | Chapter narration and staff credits (text records) | No (text) |

Compared with Jigoku's original member 1, the Tengoku atlas changes only in these places:
- t0 `V-UP!` and one small icon
- t2 `ゲーム スタート`, `データをリンクさせて` and `最大`
- t3 `Song`

Everything else in the atlas is pixel-identical to Jigoku's original.

### The "not located yet" items

- **PP-screen tabs.** These are text, not art. They sit in member 0 (FSSA) as cp932
  strings `パラメータ` / `上昇` / `スキル` / `修得`. The set appears four times, at
  `0x59c50`, `0x59c70`, `0x59c90` and `0x59cb0`: two-line tab captions, one set per
  tab state. `システム設定１/２` follows them. Jigoku's member 0 has the same block
  at `0x6342c`, and Jigoku translated it as hook text ("Raise Stats" / "Learn
  Skills"), not as a texture. These belong to the EBOOT hook / layout work, not to
  this tool.
- **Menu headers.** Most are text too: member 0 holds 71 `【…】` headers, for
  example `【機体一覧】` at `0x5d772`, `【パイロット養成】` at `0x5d7c8` and
  `【Ｄトレーダー：購入】` at `0x58fca`. Only these headers are images, all in member 1:
  - texture 0: `インターミッション` and `サブオーダー`
  - texture 2: `主人公設定`, `シナリオ選択`, `本編` / `ガイダンス` / `シナリオ`, `ゲーム` / `スタート` and `データをリンクさせて`

  This tool covers all of them.

## 2. Format

- Member 1 is one GTF with version `02020000` and 4 textures (format 0x85,
  512x512, pitch 0). Pixel data starts at 0x100 and steps by 0x100000. The member
  is 4,194,560 bytes decoded and 349,528 bytes stored (CRILAYLA).
- The textures are swizzled, so `gtf.decode` / `gtf.replace` go through the
  Morton index. Writing a whole texture re-encodes all of it. `verify_member` then
  proves that every pixel outside the cell rectangles is unchanged.
- No sub-image table exists in the GTF. The game's quads live in member 0, as
  5-vertex records (x, y, u, v floats, with UV = pixel/512). Some cell rectangles
  match those records exactly, for example the Shield Def. quad
  (0, 24)-(128, 48) at `0x406f8`. The texture binding is not in these records, so
  each cell rectangle was taken from the ink of the original glyph instead. Every
  rectangle was checked against its neighbours on the ASCII/pixel dumps and the
  `aid_m001_t*_cells.png` sheets.

## 3. Cells (`aiddata_art.json`)

| source | count | what happens |
|---|---|---|
| `jigoku-0.6.24` | 26 | Jigoku's shipped pixels are copied from the asset |
| `new` | 35 | Rendered from `en` in the measured original style |
| `keep` | 4 | Untouched: the 単 and 機 pictograms, the 35x30 合体 icon and the blank icon plate |

### Reuse (hash-guarded)

For every one of the 28 Jigoku cells, Tengoku's source pixels equal Jigoku's
original pixels. Jigoku's shipped member also differs from its original **only**
inside these 28 cells. `jigoku` refuses to extract otherwise. It checks:
- the member SHA-256 of Jigoku's original and shipped files
- the per-cell source and shipped hashes stored in the sidecar

Two of the 28 cells are not reused; they are rendered again for project wording:
- t2 `マップ`: Jigoku drew "Map". The project says "MAP Weapon".
- t2 `照準`: Jigoku drew "Sight". The project uses "Accuracy" (照準値▼ = "Accuracy Down"), so the cell becomes "Acc.".

The 26 reused cells are:
- texture 0: Shield Def., Parry, Dbl Img, Barrier, Intermission
- texture 2: ALL, Attack (heading), Center, Wide, Maximum, Break, Counter
- texture 2: Support, Attack, Defend, Re-, Wpn, Song
- texture 2: Mobi + lity (運動性), Armor, the blank `値` suffix
- texture 2: Scenario Select, Main, Tutorial, Scenario

### New wording (sources are in each cell's `term` field)

| Cells | English |
|---|---|
| t0 | Sub Order, Sortie + Locked (出撃不可), Combine |
| t0 Spirit icons 鉄幸集努必乱加分覚 | Wa Lu Fo Ga St Di Ac An Ze (`spirit_commands.json` abbreviation column) |
| t2 effect words | Morale, Stats, Combat, Regen, Up, Halved, Down, Disabled, Command, Spirit, Grant, Max |
| t2 effect words, in context | eboot.json pairs: 気力上昇 = Morale Up, 能力半減 = Stats Halved, ＨＰ回復 = HP Regen, 精神付与 = Spirit Grant, 最大気力上昇 = Max Morale Up |
| t2 title / new game | Pilot Setup (the Jigoku Vita art used the same), Game + Start, Link Data and + Start |
| t3 | Sortie, Locked, Combine (after the separate `SCORE:` sprite), Combo Attack |

To change wording, edit `en` in the catalog and run `preview --apply`.

### Rendering (measured on the originals)

- Words have a white fill, an opaque black outline of about 2 px, and a 1 px
  alpha fringe. RGB is grey. `サブオーダー` / `インターミッション` use the inverse
  style: black fill with a white outline. The renderer reproduces these styles
  with `SCE-PS3-RD-B-LATIN` (Rodin Bold), read only from RPCS3 dev_flash:
  - drawn at 4x and box-filtered
  - cap height = 0.78 x (original ink height - 2 outlines)
  - the cap band is centred on the original ink centre
  - text is condensed horizontally down to 0.52, then shrunk
- Spirit icons:
  - The base is the game's own blank plate, at t0 (48, 466).
  - The two letters are white, with the kanji icons' dark 3 px outline and a
    soft falloff.
  - The letters are centred on the original kanji's bright-stroke centre.
  - The row-0 icons begin at y 287, below the placeholder strip.
- Jigoku's reused words are white with no outline: Jigoku's tools assumed the
  game adds tint and shadow. That style was shipped and hardware-tested. A
  reused cell can be switched to the outlined style by setting its `source` to
  `new` with a `style`; `catalog --apply` keeps that choice.

## 4. Verification

1. **Source guards.** These checks run before anything is painted:
   - the decoded member 1 SHA-256 (`M1_SHA256`)
   - the source pixel SHA-256 of every cell (catalog `source_sha256`)
   - the source and shipped hashes of every Jigoku cell
   - the GTF layout: 4 swizzled 512x512 textures and the exact member size
2. **`verify_member`.** It checks that:
   - the member length is unchanged and the member did change
   - the GTF headers and every non-pixel byte are identical
   - texture 1 is byte-identical
   - each changed texture decodes to exactly the intended pixels
   - no pixel outside the cell rectangles changed
3. **`verify_archive(path, plan)`.** On the built CPK it checks that:
   - the member set is the same 54 members
   - member 1 reads back to the plan and passes `verify_member`
   - all 53 other members keep their stored bytes identical to the pristine source
4. **Rehearsal** (scratch output, not committed):
   - With `compress={1}`: the CPK is 24,315,600 bytes against 24,297,520 pristine (+18 KB). Build takes 4.9 s. `verify_archive` passes and `verify_archives.compare` passes (`replaced_compressed=1`, 53 untouched members verified).
   - Uncompressed: the CPK is 28,142,544 bytes and also passes.
5. **Tests.** `tests/test_aid_art.py` has 13 tests:
   - synthetic swizzled atlas: changes inside a rect accepted; changes outside, header changes, untouched-texture changes and wrong pixels rejected
   - catalog validation: overlap, unknown source, non-ASCII English, moved Jigoku rectangle
   - renderer fit, centring and style
   - icon plate preserved
   - real data: `plan()` changes only the rectangles, Jigoku cells equal the shipped pixels, and the output is deterministic

## 5. Compression

Store member 1 **compressed**: `compress={1}`. The member is 4 MB raw and about
360 KB compressed, so the archive and xdelta stay the same size. The writer
round-trips the CRILAYLA stream through `tools.cpk.decompress_crilayla` before
accepting it, and `compare` decodes it again independently.

Jigoku shipped this member **uncompressed** (ExtractSize == FileSize,
4,194,560), and that worked on hardware. If a compressed member 1 misbehaves in
RPCS3, fall back to `compress=False`, which costs +3.8 MB.

Member 1 is already in `CpkItocH` (its 32-bit sizes), so no row moves.

## 6. Integration (game_build.py + iso_write.py)

`iso_write.py` needs **no change**. It already replaces every entry of
`build.json["disc_files"]`, and it hash-checks that file against
`build.json["outputs"]`.

In `tools/game_build.py`:

```python
# plan(), next to texture_art.plan(...)
from tools import aid_art
aid = aid_art.plan(settings)
# ... summary['aiddata_art'] = {k: v for k, v in aid['report'].items() if k != 'cells'}
# return dict(..., aid=aid)

# build(), after the TPACKPS3 write
build_cpk(p['aid']['source_path'], output / 'AIDDATAPACK.CPK', p['aid']['members'],
          compress=set(p['aid']['members']))
aid_report = aid_art.verify_archive(output / 'AIDDATAPACK.CPK', p['aid'])
aid_compare = compare(p['aid']['source_path'], output / 'AIDDATAPACK.CPK', p['aid']['members'])
outputs.append('AIDDATAPACK.CPK')
# report = dict(..., aiddata_art=dict(p['aid']['report'], archive=aid_report, compare=aid_compare),
#               disc_files={aid_art.ARCHIVE: 'AIDDATAPACK.CPK'}, outputs=...)
```

If other work later needs another AIDDATAPACK member, merge its replacements
into the **same** `build_cpk` call, so the archive is written once. That covers,
for example, member 0 layout text from the EBOOT/UI path. The art plan touches
member 1 only; assert that the id sets are disjoint. Record the version bump and
changelog per AGENTS.md when this ships.

`verify_archives.compare` and `aid_art.verify_archive` both mmap or stream the
archive, so 32-bit Python 3.8 also works.

## 7. Risks and in-game checks

Risks:
- **Cell bounds.** These are inferred from the glyph ink, not from traced quads.
  If a quad samples a wider rectangle than the cell, a neighbour could show
  through. That cannot happen with the old Japanese, because nothing outside the
  cell changes, but clipped English could. Watch for clipped edges.
- **Word order of composed popups.** The order is fixed by the game: [Combat][Disabled],
  [Sortie][Locked], [Link Data and][Start], [Game][Start]. If スタート is not
  shared the way the FSSA string `この結果をリンクさせてスタート` suggests, the
  two start options may read oddly. Check the title menu.
- **Condensed words.** Long words in the 56 px popup cells are condensed to
  0.52-0.65: Combat, Disabled, Halved, Morale, Regen, Combine, Locked. They are
  readable on the sheets, but confirm them on the screen.
- **Mixed styles.** Jigoku's reused words have no outline; new words have one.
  The two styles do not share a word pair, but Armor (Jigoku) and Acc. (new) can
  appear in similar popups.
- **Untraced roles.** The meaning of 出撃不可, the `SCORE:` 合体 and the t0 合体
  was inferred from the atlas position and wording, not traced in code. The
  Spirit icons are assumed to be the per-Spirit status icons (the kanji match
  the abbreviation column exactly).
- **Compression.** Compressed storage of member 1 has not been tested in game.
  The fallback is in §5.

In-game checks (RPCS3):
1. New game:
   - the title menu start options (Game Start, Link Data and Start)
   - Scenario Select, Main/Tutorial Scenario
   - Pilot Setup heading
2. Intermission:
   - the heading
   - the Sub Order screen heading
3. Map deploy screen: a unit that cannot sortie (Sortie Locked).
4. Battle and map popups:
   - Support Attack / Defend
   - Re-Attack
   - Shield Def. / Parry / Dbl Img / Barrier activations
   - MAP weapon
   - an attack-type heading (ALL / Center / Wide / MAP Attack)
   - Maximum Break, Counter
5. Weapon-effect popups: Morale Down/Up, Stats Halved, Mobi-lity / Acc. / Armor ▼, HP Regen, Spirit Grant (song), Combat Disabled.
6. A unit with Spirits active, to see the icon plates (Wa, Fo, St …).
7. Combine and Combo Attack.

Record screenshots in `work/ui/`, and keep every changelog entry marked "in-game
verification pending" until these checks pass.
