"""TPACKPS3.CPK art: map badges (member 2) and episode title cards (6-134).

Dry run by default, in the style of ui_build. Nothing here writes an archive:
plan() returns the member replacement set that game_build merges with its
font pages (members 1 and 3) into ONE cpkpatch.build call (docs/TEXTURES.md).

Families
  badges       member 2, nine linear ARGB textures. Texture 1 (support badge,
               4 tiles) takes Jigoku 0.6.24's shipped `AT` art; the Tengoku
               source pixels are byte-identical to Jigoku's original, so the
               shipped pixels are reused as they are (asset + SHA-256 guards).
               Textures 4 (搭載) and 5 (マルチアクション) were never translated
               in Jigoku: they are rendered fresh from map_badges.json once it
               has English, and listed as todo until then.
  title cards  members 6-134 except 88 (already English): 1536x256 linear
               ARGB, rows 0-127 crisp title, rows 128-255 glow copy. Rendered
               from work/translation/en/ui/title_cards.json; cards whose "en"
               is null are left untouched and reported as pending.

Original title-card encoding, measured on all 129 cards: alpha is binary
(255 wherever the grey value is non-zero), R=G=B carries the coverage, the
crisp layer uses 16 grey levels (min 32), the glow layer ~31 levels. The glow
is a soft halo of about 6 px around the crisp ink. The renderer reproduces
that encoding exactly, so the game's blending sees the same kind of data.

    python -m tools.texture_art plan
    python -m tools.texture_art catalog  [--apply]   (Japanese side of title_cards.json)
    python -m tools.texture_art preview  [--apply]   (review sheets in work/ui/textures)
    python -m tools.texture_art jigoku-badge [--apply]  (re-extract the AT asset)

Fonts are read (never written) from the RPCS3 dev_flash folder next to
ui_build.FACE. Requires numpy and Pillow (bundled Python).
"""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

from tools import gtf
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK
from tools.inventory import FONT as TPACK

FONT_MEMBERS = frozenset({1, 3})
BADGE_MEMBER = 2
TITLE_MEMBERS = tuple(range(6, 135))
ENGLISH_CARD = 88
TITLE_W, TITLE_H = 1536, 256

CATALOG = ROOT / 'work/translation/en/ui/title_cards.json'
BADGE_CATALOG = ROOT / 'work/translation/en/ui/map_badges.json'
ASSETS = ROOT / 'work/ui/textures/assets'
AT_ASSET = ASSETS / 'm002_t1_jigoku_0.6.24_AT.png'
CACHE = ROOT / 'work/tengoku/cache/tpack_members'
PREVIEWS = ROOT / 'work/ui/textures'
EBOOT_STRINGS = ROOT / 'work/tengoku/research/eboot_strings.json'

JIGOKU_ORIGINAL = Path('E:/Projects/SRW Z3/work/TPACKPS3.CPK')
JIGOKU_SHIPPED = Path('E:/Projects/SRW Z3/releases/0.6.24/TPACKPS3.CPK')


def font_dir():
    from tools.ui_build import FACE
    return FACE.parent


# ---------------------------------------------------------------- guards ---
# Decoded member SHA-256 (work/tengoku/research/textures.json).
M2_SHA256 = '93955de0c34e65aa41a44a476c8b05d6b5ffa763200f0f4d70ae8e8bac22e6d4'
# Member 2 texture 1 pixel bytes: Tengoku source == Jigoku original.
M2_T1_SOURCE = '5ced93921b51330e3d256fd7474f2e2dab5fbe671c028d1c26333c1031ffb407'
# Jigoku 0.6.24 shipped texture 1 (the AT art), as ARGB pixel bytes.
M2_T1_JIGOKU_AT = '95d37c978e7f90b0637c7b9915629b7a6fccde802e07a64cec7ef70b75bc38c6'
# Jigoku's patch only touched the label box of each 80x80 tile.
AT_LABEL_BOX = (37, 2, 40, 22)          # x, y, w, h inside each tile
M2_LAYOUT = [(192, 640), (80, 320), (80, 240), (80, 160), (80, 80), (80, 80),
             (80, 400), (80, 80), (80, 240)]

# Badge textures still Japanese after the AT reuse; rendered from
# map_badges.json. Style measured from the source pixels.
BADGE_STYLES = {
    4: {'jp': '搭載', 'fill': (237, 165, 193), 'face': 'SCE-PS3-RD-B-LATIN.TTF',
        'box': (2, 38, 76, 30), 'note': 'pink label, lower-left of an 80x80 tile'},
    5: {'jp': 'マルチアクション', 'fill': (238, 200, 0), 'face': 'SCE-PS3-RD-BI-LATIN.TTF',
        'box': (1, 1, 78, 36), 'note': 'two lines, same yellow/black style as Combo (texture 6)'},
}

# ------------------------------------------------------------ title style ---
TITLE_STYLE = {
    'face': 'SCE-PS3-MT-R-LATIN.TTF',   # Matisse-style serif, closest PS3 face to
                                        # the Mincho cards and to card 88
    'case': 'as-is',                    # or 'upper' (card 88 is all caps)
    'extent': 108,                      # px from ascender top to descender bottom
    'cap_upper': 91,                    # cap height for case=upper (card 88: 91)
    'max_width': 1520,                  # card ink spans x 7..1528 at most
    'min_squeeze': 0.85,                # horizontal condensing before shrinking
    'center': (767.5, 64.5),            # ink centre of the Japanese cards
    'glow_sigma': 2.5, 'glow_gain': 1.25, 'glow_gamma': 0.5,
}
SUPERSAMPLE = 4
CRISP_LEVELS = (0, 32, 48, 64, 80, 96, 112, 127, 143, 159, 175, 191, 207, 223, 238, 255)
GLOW_LEVELS = (0, 4, 8, 16, 24, 33, 41, 49, 57, 66, 74, 82, 90, 99, 107, 115, 123, 132,
               140, 148, 156, 165, 173, 181, 189, 198, 206, 222, 239, 255)


def _quantizer(levels):
    lv = np.array(levels, dtype=np.int32)
    table = np.array([lv[np.abs(lv - v).argmin()] for v in range(256)], dtype=np.uint8)
    return lambda a: table[np.clip(np.rint(a), 0, 255).astype(np.uint8)]


CRISP_Q = _quantizer(CRISP_LEVELS)
GLOW_Q = _quantizer(GLOW_LEVELS)


# ---------------------------------------------------------------- sources ---
def _settings():
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


def source_members(settings, ids, expected=None):
    """{id: decoded bytes} from the verified pristine TPACK.

    Decoding is pure Python (about 0.4 s per card), so results are cached in
    work/tengoku/cache/tpack_members, keyed by member id and accepted only
    when they match `expected` ({id: sha256}) or the raw-member hash stored
    next to them."""
    from tools.pipeline import verified_source
    expected = expected or {}
    path = verified_source(settings, TPACK)
    out, todo = {}, []
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        for mid in ids:
            entry = by_id[mid]
            raw_sha = sha256(archive.buf[entry['offset']:entry['offset'] + entry['size']])
            cached = CACHE / ('%03d.bin' % mid)
            tag = CACHE / ('%03d.raw_sha256' % mid)
            if cached.exists() and tag.exists() and tag.read_text().strip() == raw_sha:
                data = cached.read_bytes()
                if mid not in expected or sha256(data) == expected[mid]:
                    out[mid] = data
                    continue
            todo.append((mid, entry, raw_sha))
        for mid, entry, raw_sha in todo:
            data = archive.read(entry)
            CACHE.mkdir(parents=True, exist_ok=True)
            (CACHE / ('%03d.bin' % mid)).write_bytes(data)
            (CACHE / ('%03d.raw_sha256' % mid)).write_text(raw_sha + '\n')
            out[mid] = data
    for mid, want in expected.items():
        if mid in out and sha256(out[mid]) != want:
            raise ValueError('TPACK member %d is not the guarded source' % mid)
    return out


# ------------------------------------------------------------- catalogs ---
def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('cards'), dict):
        raise ValueError('title_cards.json: expected schema 1 with "cards"')
    ids = {int(k) for k in data['cards']}
    if ENGLISH_CARD in ids or not ids <= set(TITLE_MEMBERS):
        raise ValueError('title_cards.json: card ids must be 6-134 without 88')
    for key, card in data['cards'].items():
        if not card.get('jp'):
            raise ValueError('title card %s has no Japanese' % key)
        en = card.get('en')
        if en is not None and (not isinstance(en, str) or not en.strip() or not en.isascii()
                               or '\n' in en):
            raise ValueError('title card %s: English must be one ASCII line' % key)
    return data


def load_badges(path=BADGE_CATALOG):
    if not Path(path).exists():
        return {'schema': 1, 'badges': {}}
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1:
        raise ValueError('map_badges.json: expected schema 1')
    for key, badge in data.get('badges', {}).items():
        if int(key) not in BADGE_STYLES:
            raise ValueError('map_badges.json: texture %s is not a translatable badge' % key)
        en = badge.get('en')
        if en is not None and (not en.isascii() or len(en.split('\n')) > 2):
            raise ValueError('map_badges.json: badge %s English must be ASCII, at most 2 lines' % key)
    return data


# --------------------------------------------------------- title renderer ---
def _font(name, size):
    from PIL import ImageFont
    return ImageFont.truetype(str(font_dir() / name), size)


def _ink(text, font):
    """Coverage image of `text` cropped to its ink, plus the crop's offset
    from the text origin (ascender line) and the font metrics."""
    from PIL import Image, ImageDraw
    left, top, right, bottom = font.getbbox(text)
    image = Image.new('L', (right - left + 8, bottom - top + 8))
    ImageDraw.Draw(image).text((4 - left, 4 - top), text, font=font, fill=255)
    box = image.getbbox()
    if box is None:
        raise ValueError('text renders no ink: %r' % text)
    return image.crop(box)


def _blur(a, sigma):
    r = int(3 * sigma) + 1
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2.0 * sigma * sigma))
    k /= k.sum()
    p = np.pad(a.astype(np.float64), r)
    p = sum(k[i] * p[:, i:i + p.shape[1] - 2 * r] for i in range(2 * r + 1))
    p = sum(k[i] * p[i:i + p.shape[0] - 2 * r, :] for i in range(2 * r + 1))
    return p


def title_layout(text, style=None):
    """Size, squeeze and scale used for `text` (no pixels)."""
    style = dict(TITLE_STYLE, **(style or {}))
    text = text.upper() if style['case'] == 'upper' else text
    probe = _font(style['face'], 400)
    if style['case'] == 'upper':
        l, t, r, b = probe.getbbox('H')
        size = 400.0 * style['cap_upper'] / (b - t)
    else:
        top = probe.getbbox('Hbdfhkl')[1]
        bottom = probe.getbbox('gjpqy')[3]
        size = 400.0 * style['extent'] / (bottom - top)
    ink = _ink(text, _font(style['face'], int(round(size * SUPERSAMPLE))))
    width = ink.width / SUPERSAMPLE
    height = ink.height / SUPERSAMPLE
    squeeze, shrink = 1.0, 1.0
    if width > style['max_width']:
        squeeze = max(style['min_squeeze'], style['max_width'] / width)
        if width * squeeze > style['max_width']:
            shrink = style['max_width'] / (width * squeeze)
    return dict(text=text, size=size, ink=ink, natural_width=width, height=height,
                squeeze=squeeze, shrink=shrink, style=style)


def title_pixels(text, style=None):
    """(RGBA (256, 1536, 4) uint8, info) for one English title."""
    from PIL import Image
    lay = title_layout(text, style)
    style = lay['style']
    w = max(1, int(round(lay['natural_width'] * lay['squeeze'] * lay['shrink'])))
    h = max(1, int(round(lay['height'] * lay['shrink'])))
    if w > style['max_width'] or h > 120:
        raise ValueError('title does not fit: %r (%dx%d)' % (text, w, h))
    ink = np.asarray(lay['ink'].resize((w, h), Image.BOX), dtype=np.float64)
    crisp = np.zeros((128, TITLE_W))
    cx, cy = style['center']
    x0 = int(round(cx - (w - 1) / 2.0))
    y0 = int(round(cy - (h - 1) / 2.0))
    if x0 < 7 or y0 < 4 or x0 + w > TITLE_W - 7 or y0 + h > 124:
        raise ValueError('title placement out of bounds: %r' % text)
    crisp[y0:y0 + h, x0:x0 + w] = ink
    halo = np.minimum(255.0, style['glow_gain'] * _blur(crisp, style['glow_sigma']))
    halo = 255.0 * (halo / 255.0) ** style['glow_gamma']
    glow = 255.0 - (255.0 - crisp) * (255.0 - halo) / 255.0
    grey = np.concatenate([CRISP_Q(crisp), GLOW_Q(glow)], axis=0)
    rgba = np.zeros((TITLE_H, TITLE_W, 4), np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = grey
    rgba[..., 3] = np.where(grey > 0, 255, 0)
    info = {'text': lay['text'], 'font_px': round(lay['size'], 2),
            'natural_width': round(lay['natural_width'], 1), 'squeeze': round(lay['squeeze'], 3),
            'shrink': round(lay['shrink'], 3), 'ink_box': [x0, y0, w, h],
            'needs_review': lay['shrink'] < 0.9}
    return rgba, info


def _title_texture(blob):
    tex = gtf.textures(blob)
    if len(tex) != 1 or len(gtf.gtfs(blob)) != 1:
        raise ValueError('title card is not a single-texture GTF')
    t = tex[0]
    if (t['fmt'], t['width'], t['height'], t['offset'], len(blob)) != \
            (gtf.LINEAR_ARGB, TITLE_W, TITLE_H, 0x80, 0x80 + TITLE_W * TITLE_H * 4):
        raise ValueError('title card layout changed')
    return t


def title_member(blob, text, style=None):
    """(new member bytes, {texture key: RGBA}, info) for one card."""
    tex = _title_texture(blob)
    rgba, info = title_pixels(text, style)
    return gtf.replace(blob, tex, rgba), {tex.key: rgba}, info


# ---------------------------------------------------------------- badges ---
def _m2_textures(blob):
    tex = gtf.textures(blob)
    if [(t['width'], t['height']) for t in tex] != M2_LAYOUT or \
            any(t['fmt'] != gtf.LINEAR_ARGB for t in tex):
        raise ValueError('member 2 layout changed')
    return tex


def _asset_sidecar():
    return AT_ASSET.with_suffix('.json')


def jigoku_badge():
    """Texture-1 RGBA from the stored Jigoku asset, guarded by its hashes."""
    from PIL import Image
    meta = json.loads(_asset_sidecar().read_text(encoding='utf-8'))
    rgba = gtf.from_image(Image.open(AT_ASSET))
    if rgba.shape != (320, 80, 4):
        raise ValueError('AT asset has the wrong size')
    argb = rgba[..., [3, 0, 1, 2]].tobytes()
    if sha256(argb) != M2_T1_JIGOKU_AT or meta['shipped_pixel_sha256'] != M2_T1_JIGOKU_AT \
            or meta['source_pixel_sha256'] != M2_T1_SOURCE:
        raise ValueError('AT asset does not match its recorded Jigoku hashes')
    return rgba, meta


def extract_jigoku_badge(apply=False):
    """Re-create the AT asset from Jigoku's packs (read only).

    Accepted only when Jigoku's ORIGINAL texture 1 equals Tengoku's source
    (M2_T1_SOURCE) and the shipped texture differs from it only inside the
    four label boxes."""
    rows = {}
    for label, path in (('original', JIGOKU_ORIGINAL), ('shipped', JIGOKU_SHIPPED)):
        with CPK(path) as archive:
            entry = next(e for e in archive.files if e['id'] == BADGE_MEMBER)
            blob = archive.read(entry)
        tex = gtf.textures(blob)[1]
        if (tex['width'], tex['height'], tex['fmt']) != (80, 320, gtf.LINEAR_ARGB):
            raise ValueError('Jigoku %s member 2 texture 1 layout differs' % label)
        rows[label] = (gtf.decode(blob, tex), sha256(blob[tex['offset']:tex['offset'] + tex['size']]))
    if rows['original'][1] != M2_T1_SOURCE:
        raise ValueError('Jigoku original texture 1 is not the Tengoku source')
    if rows['shipped'][1] != M2_T1_JIGOKU_AT:
        raise ValueError('Jigoku shipped texture 1 is not the recorded AT art')
    outside = np.ones((320, 80), bool)
    x, y, w, h = AT_LABEL_BOX
    for tile in range(4):
        outside[tile * 80 + y:tile * 80 + y + h, x:x + w] = False
    if (rows['original'][0][outside] != rows['shipped'][0][outside]).any():
        raise ValueError('Jigoku AT patch changed pixels outside the label boxes')
    meta = {'source': str(JIGOKU_SHIPPED), 'member': 2, 'texture': 1,
            'source_pixel_sha256': rows['original'][1], 'shipped_pixel_sha256': rows['shipped'][1],
            'label_box_per_tile': list(AT_LABEL_BOX),
            'meaning': 'remaining Support Attack uses (Jigoku tools/support_badge.py traced its EBOOT); '
                       'not yet re-traced in the Tengoku EBOOT'}
    print('Jigoku AT badge: source pixels identical to Tengoku; shipped sha %s' % rows['shipped'][1][:16])
    if apply:
        ASSETS.mkdir(parents=True, exist_ok=True)
        gtf.to_image(rows['shipped'][0]).save(AT_ASSET)
        write_json(_asset_sidecar(), meta)
        jigoku_badge()
        print('wrote %s' % AT_ASSET)
    return meta


def badge_pixels(index, text, source_rgba):
    """Fresh label for badge texture `index` in its measured style. The
    label box is cleared and redrawn; the rest of the texture is kept."""
    from PIL import Image, ImageDraw
    style = BADGE_STYLES[index]
    bx, by, bw, bh = style['box']
    ss = 4
    lines = text.split('\n')
    best = None
    for size in range(40, 6, -1):
        font = _font(style['face'], size * ss)
        stroke = 2 * ss
        boxes = [font.getbbox(line, stroke_width=stroke) for line in lines]
        lw = max(b[2] - b[0] for b in boxes) / ss
        lh = sum(b[3] - b[1] for b in boxes) / ss
        if lw <= bw and lh <= bh:
            best = (font, stroke, boxes)
            break
    if best is None:
        raise ValueError('badge %d text does not fit: %r' % (index, text))
    font, stroke, boxes = best
    total_h = sum(b[3] - b[1] for b in boxes)
    canvas = Image.new('RGBA', (bw * ss, bh * ss))
    draw = ImageDraw.Draw(canvas)
    y = (bh * ss - total_h) // 2
    for line, b in zip(lines, boxes):
        x = (bw * ss - (b[2] - b[0])) // 2
        draw.text((x - b[0], y - b[1]), line, font=font, fill=style['fill'] + (255,),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += b[3] - b[1]
    label = np.asarray(canvas.resize((bw, bh), Image.LANCZOS)).copy()
    label[label[..., 3] == 0] = 0
    out = source_rgba.copy()
    out[by:by + bh, bx:bx + bw] = label
    return out


def badge_member(blob, badges=None):
    """(new member 2 bytes, {texture key: RGBA}, report)."""
    if sha256(blob) != M2_SHA256:
        raise ValueError('member 2 is not the guarded Tengoku source')
    tex = _m2_textures(blob)
    t1 = tex[1]
    if sha256(blob[t1['offset']:t1['offset'] + t1['size']]) != M2_T1_SOURCE:
        raise ValueError('member 2 texture 1 differs from the Jigoku-identical source')
    at, meta = jigoku_badge()
    intended = {t1.key: at}
    data = gtf.replace(blob, t1, at)
    report = {'texture_1': 'Jigoku 0.6.24 AT art reused (pixel-identical source)',
              'todo': [], 'rendered': []}
    for index, style in sorted(BADGE_STYLES.items()):
        en = (badges or {}).get('badges', {}).get(str(index), {}).get('en')
        if not en:
            report['todo'].append({'texture': index, 'jp': style['jp'], 'reason': 'no English in map_badges.json'})
            continue
        rgba = badge_pixels(index, en, gtf.decode(blob, tex[index]))
        intended[tex[index].key] = rgba
        data = gtf.replace(data, tex[index], rgba)
        report['rendered'].append({'texture': index, 'en': en})
    return data, intended, report


# ---------------------------------------------------------- verification ---
def verify_member(original, built, intended):
    """Decode `built` and compare with the intended pixels.

    Every texture in `intended` must decode to exactly those pixels; every
    other texture must decode exactly as in `original`; header and
    non-texture bytes must be identical."""
    if len(original) != len(built):
        raise ValueError('member length changed')
    if built == original:
        raise ValueError('member unchanged')
    old, new = gtf.textures(original), gtf.textures(built)
    if [t.key for t in old] != [t.key for t in new] or \
            any(dict(a) != dict(b) for a, b in zip(old, new)):
        raise ValueError('texture headers changed')
    spans = sorted((t['offset'], t['offset'] + t['width'] * t['height'] * 4) for t in old)
    cursor = 0
    for start, end in spans + [(len(original), len(original))]:
        if original[cursor:start] != built[cursor:start]:
            raise ValueError('non-texture bytes changed at 0x%x' % cursor)
        cursor = max(cursor, end)
    for t in new:
        want = intended.get(t.key)
        if want is None:
            if built[t['offset']:t['offset'] + t['size']] != original[t['offset']:t['offset'] + t['size']]:
                raise ValueError('untouched texture changed: %s' % (t.key,))
        elif not np.array_equal(gtf.decode(built, t), want):
            raise ValueError('decoded texture differs from intended pixels: %s' % (t.key,))
    return True


def verify_archive(path, art):
    """Decode every art member of a built TPACK and re-verify it."""
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        for mid, data in art['members'].items():
            built = archive.read(by_id[mid])
            if built != data:
                raise ValueError('archive member %d differs from the plan' % mid)
            verify_member(art['sources'][mid], built, art['intended'][mid])
    return len(art['members'])


# ------------------------------------------------------------------ plan ---
def plan(pages_replacements, settings=None, catalog=None, badges=None, style=None):
    """Art member replacement set for TPACKPS3.

    pages_replacements: the font members game_build already replaces
    ({1: ..., 3: ...}); they must not overlap the art members. Returns
    {'members': {id: bytes}, 'sources', 'intended', 'report'}."""
    fonts = set(pages_replacements)
    if not fonts <= FONT_MEMBERS:
        raise ValueError('unexpected font members: %s' % sorted(fonts - FONT_MEMBERS))
    settings = settings or _settings()
    catalog = catalog if catalog is not None else load_catalog()
    badges = badges if badges is not None else load_badges()
    style = dict(TITLE_STYLE, **(catalog.get('style') or {}), **(style or {}))
    cards = {int(k): v for k, v in catalog['cards'].items()}
    ready = sorted(m for m, c in cards.items() if c.get('en'))
    expected = {BADGE_MEMBER: M2_SHA256}
    expected.update({m: cards[m]['member_sha256'] for m in ready if cards[m].get('member_sha256')})
    sources = source_members(settings, [BADGE_MEMBER] + ready, expected)

    members, intended, report = {}, {}, {'schema': 1, 'title_cards': {}, 'runtime_verified': False}
    data, pix, report['badges'] = badge_member(sources[BADGE_MEMBER], badges)
    members[BADGE_MEMBER], intended[BADGE_MEMBER] = data, pix
    for m in ready:
        data, pix, info = title_member(sources[m], cards[m]['en'], style)
        members[m], intended[m] = data, pix
        report['title_cards'][m] = info
    report['title_cards_pending'] = sorted(set(cards) - set(ready))
    report['title_cards_missing_from_catalog'] = sorted(set(TITLE_MEMBERS) - {ENGLISH_CARD} - set(cards))
    for mid in members:
        verify_member(sources[mid], members[mid], intended[mid])
    overlap = set(members) & (FONT_MEMBERS | fonts)
    if overlap:
        raise ValueError('art members overlap the font pages: %s' % sorted(overlap))
    report['members'] = {mid: {'input_sha256': sha256(sources[mid]), 'output_sha256': sha256(members[mid])}
                         for mid in sorted(members)}
    return {'members': members, 'sources': {m: sources[m] for m in members},
            'intended': intended, 'report': report}


# --------------------------------------------------------------- catalog ---
def _stage_titles():
    """Tengoku's own title rows in the EBOOT UTF-8 stage-title table: the main
    scenario block (0x89e828..0x89f1b8) then the bonus block
    (0x89f4b0..0x89f758), in table order."""
    rows = json.loads(EBOOT_STRINGS.read_text(encoding='utf-8'))['strings']
    rows = sorted((r for r in rows if r['family'] == 'stage_titles' and r['encoding'] == 'utf-8'),
                  key=lambda r: int(r['va'], 16))
    main = [r for r in rows if 0x89e828 <= int(r['va'], 16) <= 0x89f1b8]
    bonus = [r for r in rows if 0x89f4b0 <= int(r['va'], 16) <= 0x89f758]
    return main, bonus


def match_titles(sources, candidates, mincho='C:/Windows/Fonts/yumin.ttf'):
    """Normalised correlation of each card's crisp ink against every
    candidate title rendered in a Mincho face (both stretched to 384x32)."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(mincho, 100)

    def vec(image):
        box = image.getbbox()
        a = np.asarray(image.crop(box).resize((384, 32), Image.BILINEAR), dtype=np.float64).ravel()
        a = a - a.mean()
        return a / (np.linalg.norm(a) or 1)
    cand = []
    for text in candidates:
        im = Image.new('L', (120 * len(text) + 200, 160))
        ImageDraw.Draw(im).text((20, 20), text, font=font, fill=255)
        cand.append(vec(im))
    cand = np.stack(cand)
    scores = {}
    for mid, blob in sources.items():
        crisp = gtf.decode(blob, _title_texture(blob))[:128, :, 0]
        scores[mid] = cand @ vec(Image.fromarray(np.ascontiguousarray(crisp)))
    return scores


def build_catalog(settings, apply=False):
    """Japanese side of title_cards.json, with evidence; keeps any English."""
    main, bonus = _stage_titles()
    table = main + bonus
    textures = json.loads((ROOT / 'work/tengoku/research/textures.json').read_text(encoding='utf-8'))
    member_sha = {m['id']: m['sha256'] for m in textures['members']}
    sources = source_members(settings, TITLE_MEMBERS, {m: member_sha[m] for m in TITLE_MEMBERS})
    scores = match_titles(sources, [r['jp'] for r in table])
    old = load_catalog()['cards'] if CATALOG.exists() else {}
    cards, problems = {}, []
    # Order hypothesis: members 6..110 = main rows 0..104, 111..134 = bonus 0..23.
    order = {m: m - 6 for m in range(6, 111)}
    order.update({m: len(main) + m - 111 for m in range(111, 135)})
    for mid in TITLE_MEMBERS:
        row = table[order[mid]]
        s = scores[mid]
        best = int(s.argmax())
        ranked = sorted(s, reverse=True)
        if mid == ENGLISH_CARD:
            if row['jp'] != 'ＢＥＹＯＮＤ　ＴＨＥ　ＤＩＭＥＮＳＩＯＮ':
                problems.append('card 88 is not BEYOND THE DIMENSION in table order')
            continue
        if best != order[mid]:
            problems.append('card %d: best match %s, table order says %s' % (mid, table[best]['jp'], row['jp']))
        card = {'jp': row['jp'], 'en': (old.get(str(mid)) or {}).get('en'),
                'eboot_va': row['va'], 'table': 'main' if order[mid] < len(main) else 'bonus',
                'table_index': order[mid] if order[mid] < len(main) else order[mid] - len(main),
                'match_score': round(float(s[order[mid]]), 3),
                'runner_up_score': round(float(ranked[1] if best == order[mid] else ranked[0]), 3),
                'member_sha256': member_sha[mid]}
        if mid == 130:
            card['note'] = 'sequel of Jigoku "How Beautiful Is Strength" (強き事は美しき哉); keep the wording'
        if mid == 134:
            card['note'] = 'extends Jigoku "Ultimate Battle" (アルティメット・バトル); keep the wording'
        cards[str(mid)] = card
    unused = [r['jp'] for i, r in enumerate(table) if i not in order.values()]
    catalog = {
        'schema': 1,
        'about': 'Episode title-card textures in TPACKPS3.CPK (member id = texture id, not stage number). '
                 'Fill "en" (one ASCII line); tools/texture_art.py renders it. Member 88 is already English.',
        'evidence': 'jp = the EBOOT UTF-8 stage-title table (eboot_strings.json, family stage_titles) in '
                    'table order: members 6-110 = main rows 0x89e828.., 111-134 = bonus rows 0x89f4b0... '
                    'Each card was also matched by rendering every candidate in a Mincho face and '
                    'correlating with the card ink: the best candidate equals the table-order title for '
                    'all 128 Japanese cards (match_score vs runner_up_score).',
        'unused_titles': unused,
        'style': {},
        'cards': cards,
    }
    summary = {'cards': len(cards), 'identified': sum(1 for c in cards.values() if c['jp']),
               'order_disagreements': problems, 'unused_titles': unused,
               'min_margin': round(min(c['match_score'] - c['runner_up_score'] for c in cards.values()), 3)}
    if problems:
        raise ValueError('title identification disagrees: %s' % problems[:5])
    if apply:
        write_json(CATALOG, catalog)
    return catalog, summary


# --------------------------------------------------------------- preview ---
SAMPLES = ('A Hope Called Taboo', 'Here Comes the New Problem Boy', 'Fly into Space',
           'The Truth About Char Aznable', 'All the Lights in the Sky Are Stars', 'NT-D',
           'Showdown! Black Hole!', 'Gods, Devils, and Humans', 'Success Rate: 0.0001%',
           'Trespassing with Good Intentions', 'Time Begins to Move, and Then...', 'Zeal')


def _card_strip(rgba, scale=2):
    """A card as seen additively (grey on black): crisp over glow, scaled."""
    from PIL import Image
    grey = rgba[..., 0]
    image = Image.fromarray(np.ascontiguousarray(grey)).convert('RGB')
    return image.resize((TITLE_W // scale, TITLE_H // scale), Image.LANCZOS)


def preview(settings, apply=False, members=None):
    """preview_title_cards.png: original Japanese card | placeholder English,
    plus card 88 against its re-render as a calibration row."""
    from PIL import Image, ImageDraw
    catalog = load_catalog()
    ids = members or [6, 12, 20, 33, 47, 60, 75, 88, 99, 111, 118, 130, 134]
    textures = json.loads((ROOT / 'work/tengoku/research/textures.json').read_text(encoding='utf-8'))
    member_sha = {m['id']: m['sha256'] for m in textures['members']}
    sources = source_members(settings, ids, {m: member_sha[m] for m in ids})
    rows = []
    for i, mid in enumerate(ids):
        original = gtf.decode(sources[mid], _title_texture(sources[mid]))
        if mid == ENGLISH_CARD:
            text = 'BEYOND THE DIMENSION'
            label = 'm088 game English card | our renderer, case=upper (calibration)'
            rendered, info = title_pixels(text, dict(catalog.get('style') or {}, case='upper'))
        else:
            text = (catalog['cards'][str(mid)].get('en') or
                    '%03d %s' % (mid, SAMPLES[i % len(SAMPLES)]))
            label = 'm%03d %s | %s%s' % (mid, catalog['cards'][str(mid)]['eboot_va'], text,
                                         '' if catalog['cards'][str(mid)].get('en') else '  (PLACEHOLDER)')
            rendered, info = title_pixels(text, catalog.get('style'))
        rows.append((label, original, rendered, info))
    w, h = TITLE_W // 2, TITLE_H // 2
    sheet = Image.new('RGB', (2 * w + 12, len(rows) * (h + 22) + 26), (40, 16, 56))
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 6), 'left: original card (crisp over glow, grey = coverage); right: rendered English. '
                      'Half scale. Placeholder text unless title_cards.json has English.', fill=(255, 255, 160))
    y = 26
    for label, original, rendered, info in rows:
        draw.text((4, y + 4), '%s   [squeeze %.2f, shrink %.2f]' % (label, info['squeeze'], info['shrink']),
                  fill=(255, 255, 160))
        sheet.paste(_card_strip(original), (0, y + 20))
        sheet.paste(_card_strip(rendered), (w + 12, y + 20))
        y += h + 22
    target = PREVIEWS / 'preview_title_cards.png'
    badge_target = PREVIEWS / 'preview_map_badges.png'
    if apply:
        sheet.save(target)
        badge_preview(settings).save(badge_target)
    return target, badge_target, [(r[0], r[3]) for r in rows]


def badge_preview(settings):
    from PIL import Image, ImageDraw
    blob = source_members(settings, [BADGE_MEMBER], {BADGE_MEMBER: M2_SHA256})[BADGE_MEMBER]
    tex = _m2_textures(blob)
    # English from map_badges.json when it is filled; placeholders otherwise.
    catalog = load_badges().get('badges', {})
    placeholders = {4: 'Aboard', 5: 'Multi\nAction'}
    texts, labels = {}, {}
    for k, v in placeholders.items():
        en = (catalog.get(str(k)) or {}).get('en')
        texts[k] = en or v
        labels[k] = 't%d %s' % (k, en.replace('\n', ' / ') if en else 'PLACEHOLDER')
    data, intended, _ = badge_member(blob, {'badges': {str(k): {'en': v} for k, v in texts.items()}})
    scale = 3
    panels = [('t1 source', gtf.decode(blob, tex[1])), ('t1 Jigoku AT', intended[tex[1].key]),
              ('t4 source', gtf.decode(blob, tex[4])), (labels[4], intended[tex[4].key]),
              ('t5 source', gtf.decode(blob, tex[5])), (labels[5], intended[tex[5].key])]
    sheet = Image.new('RGB', (len(panels) * (80 * scale + 10) + 10, 320 * scale + 40), (40, 16, 56))
    draw = ImageDraw.Draw(sheet)
    for i, (label, rgba) in enumerate(panels):
        x = 10 + i * (80 * scale + 10)
        draw.text((x, 6), label, fill=(255, 255, 160))
        image = gtf.preview(rgba).resize((rgba.shape[1] * scale, rgba.shape[0] * scale), Image.NEAREST)
        sheet.paste(image, (x, 26))
    return sheet


# ------------------------------------------------------------------- CLI ---
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['plan', 'catalog', 'preview', 'jigoku-badge'])
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    if a.command == 'jigoku-badge':
        extract_jigoku_badge(a.apply)
        return 0
    settings = _settings()
    if a.command == 'catalog':
        _catalog, summary = build_catalog(settings, a.apply)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print('wrote %s' % CATALOG if a.apply else 'DRY RUN: pass --apply to write %s' % CATALOG)
    elif a.command == 'preview':
        target, badge_target, rows = preview(settings, a.apply)
        for label, info in rows:
            print(label, json.dumps({k: info[k] for k in ('squeeze', 'shrink', 'ink_box')}))
        print('wrote %s and %s' % (target, badge_target) if a.apply else 'DRY RUN: pass --apply to write previews')
    else:
        art = plan({1: None, 3: None}, settings)
        print(json.dumps({k: v for k, v in art['report'].items() if k != 'members'}, ensure_ascii=False, indent=2))
        print('art members: %s (dry run; game_build writes the archive)' % sorted(art['members']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
