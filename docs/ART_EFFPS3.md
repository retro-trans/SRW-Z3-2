# Text art in EFFPS3.CPK

`/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK` (275,166,380 bytes, sha256 `3f64c2de…`,
489 members) holds the effect animations: map location captions, episode
headings, battle cut-ins and the title screen. This document covers its
Japanese text art. Tool: `tools/eff_art.py`. Catalog:
`work/translation/en/ui/effps3_art.json`. Previews: `work/ui/textures/effps3/`.

Nothing here has been checked in game. A texture preview is not in-game
evidence.

| File | Purpose |
|---|---|
| `tools/eff_art.py` | catalog loader, renderers, `plan()`, `verify_member()`, `verify_archive()`, `inventory` / `preview` / `jigoku-berserk` CLI |
| `work/translation/en/ui/effps3_art.json` | every text-bearing texture: Japanese, English, source of the English, status, member SHA-256 guards |
| `work/ui/textures/assets/eff_m276_t0_jigoku_0.6.24_berserk.png` (+ `.json`) | Jigoku's shipped Berserk lettering, hash-guarded |
| `work/ui/textures/effps3/inventory_*.png` | original pixels of every catalogued texture, one sheet per family |
| `work/ui/textures/effps3/preview_*.png` | original / English pairs decoded from the planned member bytes |
| `work/tengoku/cache/effps3_members/` | decoded members (`NNN.bin` + `NNN.raw_sha256`), git-ignored, can be deleted |
| `tests/test_eff_art.py` | 17 tests (synthetic + the real archive when present) |

```
python -m tools.eff_art inventory [--apply]       # contact sheets of the originals
python -m tools.eff_art plan                      # render + verify everything, print the report (dry run)
python -m tools.eff_art preview  [--apply]        # before/after sheets + preview_report.json
python -m tools.eff_art jigoku-berserk [--apply]  # re-extract the Berserk asset (reads Jigoku, read only)
```
(bundled Python: numpy + Pillow). `plan` takes about 3 s with a warm cache; the
first run decodes the 95 source members in pure Python (about a minute).

## 1. Formats

- **CPK**: ITOC-only, Align 16, 486 of 489 members CRILAYLA-compressed
  (unpacked total 1.95 GB). Members 229 and 232 (title screen) are stored raw.
  `tools/cpk.py` memory-maps it (over 64 MiB); `tools/cpkpatch.build` streams
  the rebuild.
- **Member**: a little-endian effect header, an effect script, then exactly one
  embedded GTF (`tools/gtf.py` finds and decodes all 1,127 textures; formats
  0x85 swizzled and 0xA5 linear ARGB only, so `gtf.py` needed no change).
  Members 1-19 and 241-256 are scripts without textures.
- **Quad records** (56 bytes, one per animation keyframe; the header is at the
  end, as in Jigoku):

  ```
  -40  4 x RGBA vertex colours
  -24  8 zero bytes
  -16  4 x (s16 x, s16 y)  TL, TR, BL, BR in screen units (1024x576 space)
    0  u16 0, x, y, w, h (texel rect), flags (0x5000...), mode (0x101/0x201/0x301), texture
  ```
  `eff_art.find_quads` matches the exact 16 header bytes; `rect_records`
  matches any flags/mode. Every edit asserts the record count first.

## 2. What is in the archive (all 489 members reviewed)

| Family | Members / texture | Japanese | Action |
|---|---|---|---|
| Location captions | 92 members, 512x160 linear t0 (81 distinct images; 141-144, 221-223, 122/123, 146/147, 153/154, 166/167, 170/171, 176/177 are copies) | 90 place names + 2 `？？？` | **translated** (79 catalog entries, 90 members); `？？？` (120, 165) kept |
| Episode headings | 104 t2 `Prologue`, 105 t2 / 106 t2 `第 話` (one/two-digit), 107 t2 `最終話` + `果てなき世界`, 108 t2 `Bonus scenario` | 105, 106, 107 | **translated**; 104/108 are already English |
| Title-card slot | 104/105/106/108 t3 (1536x256) | none | alpha is 0 everywhere: the game draws the TPACK card into it at run time. **No fallback title copies exist** (unlike Jigoku 87-91) |
| Berserk cut-in | 276 t0 `暴走` | yes | **Jigoku art reused** |
| Library submenu | 232 t11 / t13 / t23 (three states) | 5 labels | **translated** |
| Title logo | 229 t1 `第3次スーパーロボット大戦`, t2/t12 `天獄篇` | yes | **pending**: new logo art needs the user's approval |
| Sound Select | 233 t1 header plate, t0 `作品名` label | yes | pending: baked into a 1280x720 background (needs inpainting) |
| Scenario Chart | 234/235/236 t1 header plate | yes | pending: same |
| Domination HUD | 239 t1 `新地球皇国　支配率` | yes | **translated in 0.5.19**: bounded caption rectangle; percentage and digit art and all effect records preserved |
| Logos / decoration | 234 t2 / 236 t2 (`天獄篇`/`時獄篇` backgrounds), 281 t6 (game logo), 480 t5-t7 (Gurren Lagann logo), 378 t4 (Macross 7 Chinese lettering) | yes | kept (logo / source art) |

All the other text art (system cut-ins ZERO SYSTEM, NT-D, TENGENTOPPA…,
PLAYER/ENEMY PHASE, GAME OVER, now loading, Start/Load/…, press any button)
is already English.

## 3. Families

### 3.1 Location captions (`caption_member`)

Measured on all 92 members:

- Texture 0 is 512x160. Rows 0-71 are the `JAPAN MAP` / `WORLD MAP` / `SPACE MAP`
  header and are never touched.
- Three quads sample the caption area, each with its full rectangle:
  - the slanted bar `(0,72,448,32)` (flags 0x5400);
  - the caption `(0,104,392,24)`;
  - the checker strip `(0,128,392,32)`.

  The quad geometry is not edited.
- Encoding: constant RGB `(218,232,253)` on every pixel, alpha = coverage in
  16 levels (`n*17`). Alignment: ink starts at x≈7 (left) or ends at x≈384
  (right; Japanese x0 > 20).
- The bar and checker are baked to the caption's width:
  - checker = ink + 33 px, never under 119 px;
  - bar end = checker end + 50 (left) or 50 + checker width (right).

The renderer:
- draws the English in Rodin Bold (`SCE-PS3-RD-B-LATIN`), cap height 15, cap
  line at row 4;
- condenses long names horizontally (down to 0.8) and refuses anything longer;
- **splices** the bar inside its run of identical columns (the plain line), and
  the checker in whole 6-px periods inside its periodic plateau. The slanted
  start, the gradient/chevron end and both checker fades keep their original
  pixels.

Captions are left/right-aligned exactly like the Japanese one they replace.
Only rows 72-159, x 0-447 change.

### 3.2 Episode headings (`episode_member`, `final_member`)

Texture 2 uses the TPACK title-card encoding:
- binary alpha;
- R=G=B coverage;
- crisp layer quantised to the 16 card levels;
- the glow is a separate cell, `screen(crisp, 255*(min(255, 1.5*gauss(crisp,2))/255)^0.4)`,
  fitted on 第 / Prologue with a mean error of about 9/255.

The face is the Matisse serif (`SCE-PS3-MT-R-LATIN`, as for the TPACK cards), at
the cap height of the game's own `Prologue` (72 px).

- **105 / 106** (`第N話` → `Episode N`; eboot.json 第 = "Episode ", 話 = " "):
  - The cells `第` (576,88) and `話` (720,88), plus their glows at y=200, become
    one 360-px cell at x 536-896. Columns 424-896 below row 88 are empty in the
    source.
  - Script edits:
    - the 第 crisp and glow quads (775 + 1549 records) get texel x=536, w=360,
      and every keyframe's right edge scaled x2.5 about its own left edge.
      That keeps each keyframe's zoom anchor, so the glow still zooms from the
      same point;
    - the digit quads (texture 4, and 5 in 106; crisp and glow) move right by
      94 units times that keyframe's zoom;
    - the 話 quads are hidden (vertex colours zeroed; Jigoku's method).
  - `Episode` is condensed to 0.915.
- **107** (`最終話` → `Final Episode`, `果てなき世界` → `World Without End`, both
  eboot.json):
  - crisp cell (0,88,512,112), glow cell (512,88,512,112);
  - 最 quads widened x3.56 (the glow quad's texel x moves 432→512);
  - 終 / 話 quads hidden (721 records each);
  - the heading is 0.85 condensed and 0.89 scaled;
  - the title is redrawn in the 1024x128 crisp/glow rows like a title card
    (ascender-to-descender 108 px, centred on the Japanese ink centre).
  - This is the "果てなき世界 card missing from TPACK" from `textures.md`.

### 3.3 Berserk (`berserk_member`)

- Tengoku member 276 is raw-identical to Jigoku original member 307 (sha256
  `1885d0c3…`).
- Jigoku 0.6.24 changed only texture 0 rows 8-79 (`BERSERK`, solid plus
  outline).
- `jigoku-berserk --apply` extracts those 512x72 pixels and refuses if Jigoku
  changed anything else.
- `berserk_member` paints the asset and asserts that the result **equals
  Jigoku's shipped member byte for byte** (sha256 `517e4726…`).

### 3.4 Library submenu (`library_member`)

- Textures 11 (highlighted: white core, teal glow), 13 (dark core, white glow)
  and 23 (white/white) share one core coverage. This was proven by decomposing
  texture 13: C = A(1-R), and texture 11's alpha is identical.
- The glow model `glow = 0.78*min(1, 3*gauss(core, 7))`, core over glow, matches
  all three states to about 1.5%.
- The game's own English buttons (textures 7/8/22: Start, Load…) set the face:
  Times New Roman Bold (`C:/Windows/Fonts/timesbd.ttf`, the closest match, also
  used by Jigoku), cap 26.
- One letter spacing is used for all five labels: 0.5 px, the widest that fits
  them all.
- The rows are right-aligned on screen (every quad ends at x=-165), so each
  label keeps the Japanese 13-px right margin and its cap height is centred on
  the Japanese ink centre. The sprite rectangles (differing by 1-8 px per state)
  are not edited.
- English: `Robot Library`, `Character Library`, `Glossary` (eboot.json),
  `Sound Select`, `Scenario Chart` (Jigoku).

## 4. Verification

- **Source guards**:
  - every catalogued member has a decoded SHA-256 (`member_sha256`);
  - quad-record counts are asserted before any edit;
  - texture layout asserts (size, format, GTF offset).
- **`verify_member`** (run in `plan()` for every member) checks that:
  - the length is unchanged and the member actually changed;
  - the texture headers are identical;
  - every non-texture byte is identical except the declared script edits
    (`art['edits'][id]`, all before the GTF);
  - each intended texture decodes to exactly the planned pixels;
  - every other texture is byte-identical.
- **`verify_archive(path, art)`**:
  - the built archive has 489 members;
  - each replaced member reads back as the plan's bytes and passes
    `verify_member` again.
- **Rehearsal** (2026-10-02, scratch output deleted afterwards):
  - `plan` 2.4 s, 95 members;
  - `cpkpatch.build(..., compress=art['compress'])` 24 s, 275,029,804 bytes
    (smaller than the source);
  - `verify_archives.compare` 17 s (489 members, 95 replaced, 94 compressed);
  - `verify_archive` 14 s.

## 5. Integration (game_build + iso_write)

`game_build.plan()` already builds a list of extra art archives that
`build()` writes and checks and that `iso_write` picks up through
`build.json['disc_files']`. EFFPS3 needs one more entry (not applied here):

```python
# tools/game_build.py, plan(): next to cmn_art / op_art / aid_art
from tools import eff_art
eff_plan = eff_art.plan(settings)           # 95 members, every one verified
extra_art.append(('EFFPS3.CPK', eff_art.ARCHIVE, eff_plan, eff_art, eff_plan['compress']))
```

What this does:
- **Disc path replaced**: `/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK` (= `eff_art.ARCHIVE`).
  `iso_write` needs no change; it reads `disc_files` from `build.json`.
- **Compression**: `eff_plan['compress']` holds the 94 replaced members that the
  original stores CRILAYLA-compressed. Member 232, stored raw on the disc, stays
  raw. The archive comes out at 275.0 MB.
  - `False` gives the Jigoku-style raw layout: 344,840,732 bytes, also rehearsed and verified
    through the mmap path.
  - Use `False` if the PS3/RPCS3 decoder rejects our streams.
- **Verification**: `build()` already runs `compare(source, output, members)` and
  `module.verify_archive(output, plan)` for each extra archive and records both
  in `build.json['extra_art']['EFFPS3.CPK']`.
- `summary['extra_art']['EFFPS3.CPK']` gets the scalar report fields;
  `replaced_members` is 95.
- **Ownership**: EFFPS3 must have exactly one owner. `op_art` only reads members
  229-232; the Library labels (232) are built here. Version, changelog and
  `--apply` stay with the orchestrator.

## 6. Risks and in-game checks

1. **CRILAYLA streams**: 94 members now use our compressor. Check:
   - any map intro (caption slide-in);
   - Episode 1 (105);
   - an episode ≥ 10 (106);
   - the final episode (107);
   - EVA Berserk;
   - the title screen → Library.

   If anything is garbled, rebuild with `compress=False`.
2. **Episode heading geometry**: `Episode` is 2.5x the width of 第, and the
   digit moves 94 units. Check that:
   - `Episode 1` / `Episode 12` read as one line with normal spacing;
   - the glow zoom stays registered with the crisp text;
   - nothing collides with the title card below.

   The hidden 話 quads must not leave a flash.
3. **Final episode**: the heading quad now spans 228 units (was 3 x 64). Check
   that it does not overlap the `World Without End` title.
4. **Captions**: check the bar/checker animation at the new lengths, the
   readability of the Rodin Bold cap-15 text at 720p, and the condensed
   `Outer-Space Mothership Celestial Being` (0.88).
5. **Library labels**: check the right-aligned column and the three states
   (cursor on/off, confirm). They use a Windows font, which must exist on the
   build machine (the plan fails loudly otherwise).
6. **Wording to confirm**:
   - `Chinese Federation, Kaihe`: 開河 appears in no glossary or corpus; this is
     a Mandarin romanisation. **Verify.**
   - `Northern Eurasia`, `Orbit of Planet Neo Lux` (大気圏外),
     `Mars, Insaraum Settlement`, `Alaska, Anchorage`, `Onogoro Island`,
     `Japan, Suruga Bay`, `Sea of Japan`, `Arctic Ocean`, `Moon`,
     `Near Jupiter`, `Outer Mars Sphere`: these are new. Every other name comes
     from the glossary, eboot.json, story banners or Jigoku (recorded per entry).
   - Abbreviated to fit: `Merida Island, Mithril W. Pacific Fleet Base` and
     `S. Central Continent, Central Base`.
   - Several glossary terms are still `proposed`: Neo Tokyo-2, Nikero, Amerria,
     Neo Lux, White Palace, Meganebula.
7. **Pending** (not built):
   - title logo / 天獄篇 (229): user approval needed;
   - Sound Select and Scenario Chart header plates (233-236);
   - the `作品名` label (233 t0);
   - the domination-rate HUD (239).
8. Fonts are read from `E:/RPCS3/dev_flash/data/font` and `C:/Windows/Fonts`
   (read only). Rendering depends on the Pillow/FreeType version, so re-render
   on the build machine. `plan()` always verifies against its own rendering.
