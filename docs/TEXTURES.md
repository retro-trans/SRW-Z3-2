# Texture art in TPACKPS3.CPK

`/PS3_GAME/USRDIR/DATA/TABATA/TPACKPS3.CPK` holds 135 members. The font pages
(members 1 and 3) are already built by `tools/game_build.py`. This document
covers the art members: the map badges (member 2) and the episode title cards
(members 6-134). Research background: `work/tengoku/research/textures.md`.

Nothing here has been checked in game yet. A texture preview is not in-game
evidence.

| Tool | Purpose |
|---|---|
| `tools/gtf.py` | GTF parse / decode / encode / paint |
| `tools/cpkpatch.py` | CPK rebuild. Now has CRILAYLA compression and streams large archives |
| `tools/cpk.py` | CPK reader. Archives over 64 MiB are memory-mapped |
| `tools/verify_archives.py` | `compare()`. Uses mmap and accepts compressed replacements |
| `tools/texture_art.py` | Badge and title-card art, the `plan()` entry point, catalog, previews |
| `work/translation/en/ui/title_cards.json` | Title-card catalog (Japanese side done, `en` empty) |
| `work/translation/en/ui/map_badges.json` | English for badges 4 (Aboard) and 5 (Multi-Action) |
| `work/ui/textures/assets/m002_t1_jigoku_0.6.24_AT.png` (+ `.json`) | Jigoku's shipped AT badge pixels, with hashes |
| `work/ui/textures/preview_title_cards.png` | Style review sheet (placeholder English) |
| `work/ui/textures/preview_map_badges.png` | Badge review sheet (placeholder English for 4 and 5) |
| `work/tengoku/cache/tpack_members/` | Decoded source members (about 200 MB, git-ignored), each checked against the raw-member hash and the catalog guard. It can be deleted. |

## 1. GTF (`tools/gtf.py`)

- Formats:
  - `0xA5`: linear A8R8G8B8 (bytes A,R,G,B).
  - `0x85`: the same in Morton / Z order (member 5).
  - `0xAB`: G8B8 font pages. Decoded read-only as BE u16; `encode` refuses them.
- `gtfs(blob)` follows a chain of GTF files (member 0 has five) or scans a
  container for embedded GTFs (member 5).
- `decode` returns RGBA `(h, w, 4)`. `encode` and `replace` write back only the
  pixel bytes of one texture. `paint` writes only one rectangle.
- Round trip: decoding and re-encoding gives byte-identical output for all 165
  textures of the pristine pack (`TENGOKU_FULL_TEXTURES=1` test, see §6).
  Member 5 has **19** textures, not 20. `textures.md` miscounts it; its total of
  165 is right.

```
python -m tools.gtf list    <member.bin>
python -m tools.gtf preview <member.bin> <outdir> --apply
```

## 2. Archive size: CRILAYLA compression, plus mmap as a fallback

Problem: `cpkpatch` stored replacements uncompressed. With all 128 cards
replaced, TPACK would grow from 16.7 MB to about 227 MB, and `CPK` refused
anything over 64 MiB.

### CRILAYLA compression (preferred)

- `cpkpatch.compress_crilayla(data)` is a greedy LZ77 encoder for the format
  that `cpk.decompress_crilayla` reads:
  - 13-bit distance + 3
  - 2/3/5/8(/8…) bit length VLE
  - reversed bit stream
  - 0x100-byte raw prefix
  - The stream is zero-padded to a multiple of 4 bytes at its low end. All 135
    original members have that alignment.
- `build(src, dst, replacements, compress=...)`:
  - `compress=True` compresses every replacement; a set of ids compresses only
    those.
  - Each compressed member is decompressed with the **existing** reader
    decompressor and compared before it is used.
  - A member that does not shrink stays raw.
  - Compression runs in a process pool (Windows spawn; callers need an
    `if __name__ == '__main__'` guard, which `game_build` has).
- `verify_archives.compare()` independently locates each replacement and checks
  it:
  - A compressed one is decoded once from those bytes.
  - A raw one is compared by hash.
  - The result has a `replaced_compressed` count.
- Proof on real data:
  - Every one of the 135 pristine members re-compresses and decodes
    byte-identically (`RealPackCompressionTests`).
  - A rehearsal TPACK with font pages 1/3 plus member 2 plus all 128 cards
    (placeholder English) is **15.5 MB** compressed.
  - Measured times: `plan` 8-13 s, build 20 s, `compare` 26 s,
    `verify_archive` 22 s.
  - Our cards come out 5-10% smaller than CRI's own (member 6: 58,412 vs
    61,764 bytes).

### Large-archive reading (fallback, and needed for EFFPS3 anyway)

- `CPK` memory-maps archives over `MMAP_THRESHOLD` (64 MiB) instead of
  refusing them.
  - `close()` and context-manager support release the map.
  - Small archives still load into memory as before.
- `cpkpatch.build` copies only the header region. Untouched members are
  streamed from the source in 16 MiB chunks.
- `compare()` mmaps both files and hashes them in a streaming pass.
- The uncompressed rehearsal pack (226.9 MB) builds and verifies this way.
  This also works under the 32-bit Python 3.8 (tests pass there).

## 3. Map badges (member 2)

| tex | content | action |
|---|---|---|
| 1 | `援護` support-use badge, 4 tiles | **Jigoku 0.6.24 `AT` art reused** |
| 4 | `搭載` (pink) | todo: English from `map_badges.json`, rendered fresh |
| 5 | `マルチアクション` (yellow/black, same style as texture 6 "Combo") | todo: as above |

Texture 1 guards:
- member SHA-256 `93955de0…`
- texture-1 pixel SHA-256 `5ced9392…`. This is the Tengoku source and equals
  Jigoku's original.
- the asset pixel SHA-256 `95d37c97…`. This is Jigoku 0.6.24, in code as
  `M2_T1_JIGOKU_AT`.

`python -m tools.texture_art jigoku-badge --apply` re-extracts the asset from
`E:/Projects/SRW Z3/releases/0.6.24/TPACKPS3.CPK` (read only). It refuses
unless:
- Jigoku's original texture equals the Tengoku source, and
- the shipped texture differs only inside the four 40x22 label boxes.

No Japanese badge in member 2 differs from Jigoku. Textures 4 and 5 are
identical to Jigoku, but Jigoku never translated them. To translate them,
create `work/translation/en/ui/map_badges.json`:

```json
{"schema": 1, "badges": {"4": {"jp": "搭載", "en": "..."}, "5": {"jp": "マルチアクション", "en": "Multi\nAction"}}}
```

Each label is drawn in its measured style (fill colour, 2 px black outline,
Rodin Bold / Bold Italic) and fitted to its box. Nothing else in the texture
changes. The wording must come from the glossary; nothing is filled yet.

## 4. Episode title cards (members 6-134)

### Catalog

`work/translation/en/ui/title_cards.json`:

```json
{"schema": 1, "style": {}, "cards": {"6": {"jp": "時獄の果てに", "en": null, "eboot_va": "0x89e828", ...}}}
```

- 128 cards are identified. Card 88 (`BEYOND THE DIMENSION`) is already
  English and is not in the catalog.
- Evidence, built by `python -m tools.texture_art catalog --apply`:
  1. **Table order.** The EBOOT UTF-8 stage-title table lists Tengoku's titles
     (`eboot_strings.json`, family `stage_titles`):
     - main block: 106 rows from `0x89e828` (`時獄の果てに`)
     - bonus block: 24 rows from `0x89f4b0` (`スズネ、ストレス発散`)
     - The mapping is: members 6-110 = main rows 0-104, and members 111-134 =
       bonus rows 0-23.
  2. **Pixel match.** Every candidate title was rendered in a Mincho face and
     correlated with each card's crisp ink.
     - For all 128 Japanese cards, the best match is the table-order title.
     - The smallest margin over the runner-up is 0.206; a typical match is
       0.6-0.9 against a runner-up of 0.1-0.3.
     - Card 88 is `ＢＥＹＯＮＤ　ＴＨＥ　ＤＩＭＥＮＳＩＯＮ` in table order, which
       is consistent with that.
     - Each card records `match_score` and `runner_up_score`.
  3. One main title has **no card**: `果てなき世界` (main row 105, last). It
     probably uses an episode effect like Jigoku's Final Episode (EFFPS3). It
     is listed in `unused_titles`.
- Card fields:
  - `jp`
  - `en`: null. The orchestrator fills it with one ASCII line, the same wording
    as the UI scenario name.
  - `eboot_va`, `table`, `table_index`
  - `match_score`, `runner_up_score`
  - `member_sha256`: the source guard
  - `note` on cards 130 and 134 (keep Jigoku's "How Beautiful Is Strength" and
    "Ultimate Battle" wording).
- `catalog --apply` keeps any English that is already filled in.

### Original style (measured on all 129 cards)

- Rows 0-127 hold the crisp title; rows 128-255 hold a glow copy.
- Alpha is **binary**: 255 wherever the pixel is non-zero.
- R=G=B carries the coverage:
  - The crisp layer uses 16 grey levels (32…255; coverage below 2/16 is
    dropped).
  - The glow layer uses about 31 levels, a halo of about 6 px.
  - The game most likely composites these additively. Jigoku wrote ordinary
    straight-alpha white text instead.
- Japanese ink spans y≈9-120, centred at x≈767.5. The widest cards use
  x 7-1528.
- Card 88 is the game's own English lettering: a serif face, cap height 91,
  width 1521 px.

### Renderer (`texture_art.title_pixels`)

- Face: `SCE-PS3-MT-R-LATIN.TTF`, the PS3 Matisse serif and the closest PS3
  face to both the Mincho cards and card 88. Fonts are read from the RPCS3
  dev_flash font folder (read only).
- Size: ascender-to-descender height of 108 px; letters are as tall as the
  Japanese.
  - `"case": "upper"` uses card 88's cap height of 91 instead.
  - Calibration: re-rendering `BEYOND THE DIMENSION` gives a 0.919 horizontal
    condense against 0.917 measured on card 88.
- Rendered at 4x and box-filtered to coverage. The ink is centred on the
  Japanese ink centre (767.5, 64.5).
- Over 1520 px wide: condensed horizontally down to 0.85, then shrunk. Each
  card's `squeeze` / `shrink` is reported, and `needs_review` is set when
  `shrink` is below 0.9.
- Glow: `screen(crisp, 255·(min(255, 1.25·gauss(crisp, σ=2.5))/255)^0.5)`. This
  is fitted to the originals with a mean error of about 9/255 on the ink area.
- Output: quantised to the original grey levels, alpha = 255 where the grey
  value is non-zero, and R=G=B.
- Overrides go in the catalog's `"style"` object (any key of
  `TITLE_STYLE`).
- Review sheet: `python -m tools.texture_art preview --apply` writes
  `work/ui/textures/preview_title_cards.png`.
  - It shows 12 original cards next to placeholder English (`NNN <sample
    title>`).
  - It includes a calibration row: card 88 against our upper-case re-render.

## 5. `plan()` and game_build integration

- Call: `texture_art.plan(pages_replacements, settings=None, catalog=None, badges=None)`.
  - It asserts that `pages_replacements` ⊆ {1, 3} and that no art member
    overlaps {1, 3}.
- Returns `{'members': {id: bytes}, 'sources': {id: bytes}, 'intended': {id: {tex key: RGBA}}, 'report': {...}}`.
- Contents:
  - Member 2 always. Today that is texture 1 = `AT`; textures 4/5 are listed as
    todo.
  - Every card whose `en` is filled. Cards with `en: null` are untouched and
    listed under `title_cards_pending`.
- Per-member verification (`verify_member`) runs inside `plan()`. Each written
  member is decoded and compared with the intended pixels:
  - Every other texture must be byte-identical.
  - Headers and non-texture bytes must be unchanged.
  - The member must actually change.
- After the archive is written, `verify_archive(path, art)` decodes every art
  member from the built TPACK and repeats the check.

**One TPACK build, font + art.** This is the exact change to make in
`tools/game_build.py` (not applied here):

```python
# imports
from tools import texture_art

# plan(): after `pages = {...}` is read and checked
art = texture_art.plan(pages, settings)          # asserts art ∩ {1, 3} = ∅
# ... and in the summary / return value
summary['texture_art'] = {k: v for k, v in art['report'].items() if k != 'title_cards'}
summary['title_cards_rendered'] = sorted(art['report']['title_cards'])
return dict(..., art=art)

# build(): replace the single TPACK line
#   build_cpk(p['font_path'], output / 'TPACKPS3.CPK', font_members)
tpack_members = dict(font_members)                         # {1: path, 3: path}
if set(tpack_members) & set(p['art']['members']):
    raise ValueError('font and art members overlap')
tpack_members.update(p['art']['members'])                  # bytes are accepted directly
build_cpk(p['font_path'], output / 'TPACKPS3.CPK', tpack_members,
          compress=set(p['art']['members']))              # or True to compress the font pages too
texture_report = texture_art.verify_archive(output / 'TPACKPS3.CPK', p['art'])

# build(): the report
font_archive=compare(p['font_path'], output / 'TPACKPS3.CPK',
                     {fid: (v.read_bytes() if isinstance(v, Path) else v)
                      for fid, v in tpack_members.items()}),
texture_art=dict(p['art']['report'], archive_members_verified=texture_report),
```

Notes on the snippet:
- The "unallocated font changed" check is unchanged.
- `build.json` gains per-member input and output SHA-256
  (`report['members']`).
- Version, changelog and `--apply` stay with the orchestrator.

**Choosing `compress`:**
- `compress=set(art ids)`:
  - The font pages stay stored raw, exactly as in today's builds.
  - Only the new art members use the new compressor.
  - TPACK size is 31.1 MB (rehearsal: build 11 s, `compare` 25 s).
- `compress=True`:
  - Also compresses the two font pages.
  - TPACK is about 15.5 MB; the build takes about 15 s more.
- `compress=False`:
  - The Jigoku-proven uncompressed layout, about 227 MB.
  - Works through the mmap path.
  - Use it if the PS3/RPCS3 CRI decoder rejects our streams.

## 6. Tests

```
& $py -m unittest discover -s tests                     # default: synthetic + subset of the real pack
$env:TENGOKU_FULL_TEXTURES='1'; & $py -m unittest test_gtf test_cpk_compress   # (from tests/ with PYTHONPATH=.)
```

- `tests/test_gtf.py` covers:
  - linear/swizzled/multi-texture round trips, ARGB byte order and the Z-order
    pattern
  - `paint` touching only its rectangle
  - chained and embedded GTFs
  - read-only font pages
  - the real pack: members 0/2/4/5/6/88 by default, all 165 textures with the
    environment variable
- `tests/test_cpk_compress.py` covers:
  - compressor round trips through the reader's decompressor: runs, VLE
    boundaries, the window edge, incompressible data
  - compressed builds and `compare` (including rejection of wrong content)
  - compressing only selected members
  - the mmap path, and a 65 MiB+ archive built, verified and rebuilt from
  - every real member recompressing (with the environment variable)
- `tests/test_texture_art.py` covers:
  - the renderer's encoding invariants (binary alpha, grey levels, glow halo,
    bounds, centring)
  - condense/shrink
  - the card-88 calibration
  - badge rendering
  - `verify_member` catching wrong pixels and header changes
  - catalog validation
  - `plan()` font-overlap refusal
  - a real-pack `plan()` with one card

## 7. Risks: check in game

1. **CRILAYLA streams in the real decoder.** Our streams decode with our
   decompressor, but RPCS3 and the PS3 CRI library are the real consumers.
   - First boot: title screen, dialogue (if fonts were compressed), the map
     with a support unit (badge), and an episode start (title card).
   - If anything is garbled or hangs, rebuild with `compress=False` (227 MB,
     the Jigoku layout) or keep `compress=set(art ids)`.
2. **The ISO/patch size** if the uncompressed fallback is used:
   - `iso_write` appends replaced files.
   - Check that the Retro Trans Tools patch handles the larger delta, per
     AGENTS.md.
3. **Title-card blending.** We copy the original encoding (binary alpha, grey
   coverage), so the card should look exactly like a Japanese one. Check:
   - the glow intensity
   - that no dark box shows around the text
   - the size compared with the screen
4. **The AT badge's meaning.** Jigoku traced its EBOOT; in Tengoku the trace has
   not been redone.
   - Confirm that the badge counts **support attack** uses (Jigoku
     `support_badge.verify_attack_reader` addresses will differ).
   - Screen: a unit with Support Attack on the map.
5. **Badges 4/5:**
   - English wording is pending (glossary).
   - Check how much of the 80x80 tile the game shows. The `搭載` art sits at
     x 3-46, y 42-64; the box allows 76x30.
6. **Card ↔ stage mapping.** The catalog's Japanese is checked by pixels and by
   table order, but the card → stage pairing is not. Confirm the episode 1 card
   (member 6) and one bonus scenario card (111+) in game.
7. **Episode fallbacks / the final card.** Like Jigoku's EFFPS3 87-91, Tengoku
   may keep fallback title copies and the `果てなき世界` card in EFFPS3. Those
   are not covered here.
8. Fonts are read from `E:/RPCS3/dev_flash/data/font` (read only). The output
   depends on the Pillow/FreeType version, so re-render on the build machine
   and do not commit rendered bytes. `plan()` always verifies against its own
   rendering.
