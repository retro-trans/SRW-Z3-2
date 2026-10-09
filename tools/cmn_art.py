"""Battle-screen art in DATA/BTLC/CMN.CPK: Maximum Break and battle action labels.

Dry run by default, in the style of ui_build / texture_art. Nothing here
writes an archive: plan() returns the member replacement set that game_build
passes to ONE cpkpatch.build call for CMN.CPK (docs/ART_CMN.md).

CMN.CPK has a single member (id 0, 3,880,448 bytes decoded): an effect
script block (0x0000-0xa3ff) followed by one GTF with 26 textures at 0xa400.
Three textures carry Japanese lettering; everything else is either already
English (ribbon t1, gauge t4, CRITICAL t14, word atlas t23) or has no text.

  t16 1472x176  マキシマムブレイク   gold Maximum Break banner, sampled by NINE
                                    animated quads in the effect script
  t10  192x48   合体攻撃             cyan Combo Attack banner
  t11  272x256  カウンター / 再攻撃 / 援護攻撃 / 援護防御   four 272x64 rows

All three source textures are pixel-identical to Jigoku's original CMN, and
the renderers below are ports of Jigoku tools/maximum_break_art.py that
reproduce Jigoku 0.6.24's shipped pixels byte for byte (calibration hashes
JIGOKU_SHIPPED_PIXELS, checked by the tests and by `compare-jigoku`).

The Maximum Break banner cannot be repainted in place: the native script
draws it from nine quads whose UVs cut the atlas into Japanese glyphs (one
glyph is sampled twice). Like Jigoku, nine whole-letter English cells are
packed into the atlas with transparent gutters and the nine records' signed
screen bounds and UV endpoints are rewritten together. In Tengoku the
records sit 0x688 bytes earlier than in Jigoku and their 16-bit fields are
BIG-endian (Jigoku's are little-endian); every value is otherwise identical
(see PIECES and docs/ART_CMN.md for the evidence).

    python -m tools.cmn_art plan
    python -m tools.cmn_art inventory      [--apply]   contact sheets + cmn_inventory.json
    python -m tools.cmn_art preview        [--apply]   before/after sheets
    python -m tools.cmn_art compare-jigoku             evidence vs Jigoku original/0.6.24 (read only)

Fonts are read (never written) from the RPCS3 dev_flash folder next to
ui_build.FACE. Requires numpy and Pillow (bundled Python).
"""
import argparse
import json
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from tools import gtf
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK

CMN = '/PS3_GAME/USRDIR/DATA/BTLC/CMN.CPK'
MEMBER = 0
CATALOG = ROOT / 'work/translation/en/ui/cmn_art.json'
PREVIEWS = ROOT / 'work/ui/textures/cmn'
JIGOKU_ORIGINAL = Path('E:/Projects/SRW Z3/work/orig/CMN.CPK')
JIGOKU_SHIPPED = Path('E:/Projects/SRW Z3/releases/0.6.24/CMN.CPK')
FACE = 'SCE-PS3-RD-BI-LATIN.TTF'

# ---------------------------------------------------------------- guards ---
ARCHIVE_SHA256 = 'cdef558527205e0bf55ac98f12b51d96d02ac06fbabab9af7bb5ac7705278757'
MEMBER_SHA256 = 'cd834f502b60a72ffa4c3397f1b8d72b75a0a198fd97bcc434305c179cc42635'
MEMBER_SIZE = 3880448
GTF_BASE = 0xa400
LAYOUT = [(128, 128, 0x85), (512, 40, 0xa5), (224, 224, 0xa5), (80, 32, 0xa5), (488, 72, 0xa5),
          (16, 40, 0xa5), (8, 8, 0x85), (64, 288, 0xa5), (8, 8, 0x85), (32, 16, 0x85), (192, 48, 0xa5),
          (272, 256, 0xa5), (800, 112, 0xa5), (800, 112, 0xa5), (384, 40, 0xa5), (160, 120, 0xa5),
          (1472, 176, 0xa5), (512, 280, 0xa5), (256, 256, 0x85), (104, 104, 0xa5), (64, 8, 0x85),
          (16, 32, 0x85), (80, 80, 0xa5), (96, 112, 0xa5), (144, 48, 0xa5), (384, 48, 0xa5)]
# Pixel bytes of the lettered textures; identical in Tengoku and Jigoku's original CMN.
SOURCE_PIXELS = {
    10: '230a7c51b03deec1e47cd2736f32b5b144bf63d955bdcab6834261df1704e1ca',
    11: '4a031abc1518acd7578be811467a6322b34caf6b96070f22dffd98b5e3142585',
    16: '39143a652080ab87e3b74b5472f7843cbc91a89963b301c1c00db672d8d70615',
}
# Jigoku 0.6.24's shipped pixels for the same textures (Counter / Attack Again /
# Support Attack / Support Defend; Combo Attack; MAXIMUM BREAK). Our renderers
# reproduce these exactly when given Jigoku's wording.
JIGOKU_SHIPPED_PIXELS = {
    10: 'c52d7ba1544a11873f9fe8e52b175ce0a16e6f2a1554884bef5ca28b9ac1dc4a',
    11: '4f06add068ea90b90d0adea7b29369ce4e6f6d3f7b633161f55507ae18a3ad4c',
    16: '3b2254f8593e9577922440cad11e7bce8599bf5f58743f8c7efe9de07c0ad7c8',
}
JIGOKU_MEMBER_SHA256 = '1359e4fa6b1adb2ab711a5e7c88960d82d37ae4d927ac9f737fd0e263247e2cc'
JIGOKU_SHIPPED_MEMBER_SHA256 = '812607ea887b270f10ce8f691516048853d3fe417817901bc714307c9ef9604d'
JIGOKU_GTF_BASE = 0x9de0
RECORD_SHIFT = 0x688          # Jigoku record offset - Tengoku record offset

# Maximum Break: the nine quads that sample t16, left to right on screen.
# (record offset, anchor offset, anchor (x, y), original record as
#  (x0, y0, x1, y1 signed screen bounds relative to the anchor; u0, v0, u1, v1
#  unsigned texel endpoints)). All fields BIG-endian. Jigoku: offset + 0x688,
# little-endian, same values. Piece 3 re-samples piece 0's glyph.
PIECES = (
    (0x3b14, 0x3b04, (-632, 0), (-88, -88, 88, 88, 1, 0, 175, 176)),
    (0x39f8, 0x39ec, (-504, 0), (-84, -88, 84, 88, 177, 0, 343, 176)),
    (0x38e8, 0x38dc, (-344, 4), (-96, -96, 96, 80, 345, 0, 535, 176)),
    (0x37d8, 0x37cc, (-160, 0), (-88, -88, 88, 88, 1, 0, 175, 176)),
    (0x36d0, 0x36c4, (-56, 0), (-84, -88, 84, 88, 537, 0, 703, 176)),
    (0x35c0, 0x35b4, (176, 0), (-96, -92, 96, 84, 705, 0, 895, 176)),
    (0x34b0, 0x34a4, (332, 0), (-92, -84, 92, 92, 897, 0, 1079, 176)),
    (0x339c, 0x3390, (496, 0), (-100, -86, 100, 90, 1081, 0, 1279, 176)),
    (0x3288, 0x327c, (624, 0), (-96, -84, 96, 92, 1281, 0, 1471, 176)),
)
RECORD = '>4h4H'
BANNER_W, BANNER_H = 1472, 176
# The settled phrase spans screen x -736..736, y -88..88 around the effect origin.
SCREEN_X0, SCREEN_Y0 = -736, -88

# Label geometry and style are owned by the code (measured on the source);
# the catalog owns the wording.
LABELS = {
    'maximum_break': {'texture': 16, 'rect': (0, 0, 1472, 176), 'jp': 'マキシマムブレイク', 'style': 'gold_banner'},
    'combo_attack': {'texture': 10, 'rect': (0, 0, 192, 48), 'jp': '合体攻撃', 'style': 'cyan'},
    'counter': {'texture': 11, 'rect': (0, 0, 272, 64), 'jp': 'カウンター', 'style': 'pink'},
    'attack_again': {'texture': 11, 'rect': (0, 64, 272, 64), 'jp': '再攻撃', 'style': 'purple'},
    'support_attack': {'texture': 11, 'rect': (0, 128, 272, 64), 'jp': '援護攻撃', 'style': 'purple'},
    'support_defense': {'texture': 11, 'rect': (0, 192, 272, 64), 'jp': '援護防御', 'style': 'gold'},
}
TINTS = {'cyan': (0, 210, 215), 'pink': (232, 40, 167), 'purple': (121, 73, 238), 'gold': (224, 161, 18)}
# The nine banner cells; joined they must spell the catalog English without spaces.
BANNER_CHUNKS = ('MA', 'XI', 'M', 'U', 'M', 'B', 'R', 'EA', 'K')
BANNER_WORD_GAP_AFTER = 4     # extra gutter after the fifth cell (end of MAXIMUM)
SQUEEZE_REVIEW = 0.55         # flag action labels condensed below this (Jigoku 0.6.24
                              # shipped Combo Attack at 0.567, Support Attack at 0.641)

# Texture notes for the inventory (reviewed against the contact sheet).
TEXTURE_NOTES = {
    0: ('none', 'sparkle particles'), 1: ('english', 'red MAXIMUM BREAK ribbon'),
    2: ('none', 'SRW emblem ring (Latin logo)'), 3: ('none', 'wave panel'),
    4: ('english', 'HP / EN gauge frame'), 5: ('none', 'chevron'), 6: ('none', 'white 8x8'),
    7: ('none', 'coloured unit icons'), 8: ('none', 'white 8x8'), 9: ('none', 'dots'),
    10: ('japanese', '合体攻撃 Combo Attack banner'),
    11: ('japanese', 'カウンター / 再攻撃 / 援護攻撃 / 援護防御 banners'),
    12: ('none', 'blue digits 0-9'), 13: ('none', 'gold digits 0-9'), 14: ('english', 'CRITICAL'),
    15: ('none', 'button prompts (skip / fast-forward / return)'),
    16: ('japanese', 'マキシマムブレイク gold banner (nine animated quads)'),
    17: ('none', 'hit / spark / splash effect sprites'), 18: ('none', 'soft glow'), 19: ('none', 'ring'),
    20: ('none', 'gradient bar'), 21: ('none', 'bar'), 22: ('none', 'dotted ring'),
    23: ('english', 'word atlas Center / Wide / ALL / MAXIMUM / Main / Assist / BREAK'),
    24: ('none', 'frame corners'), 25: ('none', 'digits / ? 0-9'),
}


def font_path():
    from tools.ui_build import FACE as UI_FACE
    return UI_FACE.parent / FACE


def _settings():
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


# ---------------------------------------------------------------- source ---
def source_member(settings=None):
    """Decoded member 0 of the verified pristine CMN.CPK."""
    from tools.pipeline import verified_source
    path = verified_source(settings or _settings(), CMN)
    with CPK(path) as archive:
        if [e['id'] for e in archive.files] != [MEMBER]:
            raise ValueError('CMN.CPK member layout changed')
        data = archive.read(archive.files[0])
    check_source(data)
    return data


def textures(blob):
    found = gtf.gtfs(blob)
    if len(found) != 1 or found[0][0] != GTF_BASE:
        raise ValueError('CMN GTF is not the single GTF at 0x%x' % GTF_BASE)
    tex = found[0][1]
    if [(t['width'], t['height'], t['fmt']) for t in tex] != LAYOUT:
        raise ValueError('CMN texture layout changed')
    return tex


def check_source(blob):
    if len(blob) != MEMBER_SIZE or sha256(blob) != MEMBER_SHA256:
        raise ValueError('CMN member 0 is not the guarded Tengoku source')
    tex = textures(blob)
    for index, want in SOURCE_PIXELS.items():
        t = tex[index]
        if sha256(blob[t['offset']:t['offset'] + t['size']]) != want:
            raise ValueError('CMN texture %d differs from the Jigoku-identical source' % index)
    for offset, anchor_offset, anchor, record in PIECES:
        if read_record(blob, offset) != record or struct.unpack_from('>2h', blob, anchor_offset) != anchor:
            raise ValueError('Maximum Break record drift at 0x%x' % offset)
    return tex


def read_record(blob, offset):
    return struct.unpack_from(RECORD, blob, offset)


def strip_quads(blob, end=GTF_BASE, fmt=RECORD):
    """Every quad record in the effect block that samples a full-height
    (v 0..176) strip of the banner atlas: [(offset, record)]. Used as
    evidence that PIECES are the only consumers of t16."""
    out = []
    for p in range(0, end - 16, 2):
        x0, y0, x1, y1, u0, v0, u1, v1 = struct.unpack_from(fmt, blob, p)
        if (v0, v1) == (0, BANNER_H) and 0 <= u0 < u1 <= BANNER_W and -400 < x0 < x1 < 400 and -200 < y0 < y1 < 200:
            out.append((p, (x0, y0, x1, y1, u0, v0, u1, v1)))
    return out


# ------------------------------------------------------------- catalog ---
def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('labels'), dict):
        raise ValueError('cmn_art.json: expected schema 1 with "labels"')
    if set(data['labels']) != set(LABELS):
        raise ValueError('cmn_art.json: labels must be exactly %s' % sorted(LABELS))
    for key, row in data['labels'].items():
        spec = LABELS[key]
        if row.get('jp') != spec['jp'] or row.get('texture') != spec['texture'] or \
                tuple(row.get('rect') or ()) != spec['rect']:
            raise ValueError('cmn_art.json: %s does not match the source geometry' % key)
        en = row.get('en')
        if en is not None and (not isinstance(en, str) or not en.strip() or not en.isascii() or '\n' in en):
            raise ValueError('cmn_art.json: %s English must be one ASCII line' % key)
    en = data['labels']['maximum_break'].get('en')
    if en is not None and en.replace(' ', '') != ''.join(BANNER_CHUNKS):
        raise ValueError('cmn_art.json: the Maximum Break banner is cut into nine animated cells %s; '
                         'new wording needs a new cell plan' % (BANNER_CHUNKS,))
    return data


# ------------------------------------------------------------ renderers ---
def _font(size):
    from PIL import ImageFont
    return ImageFont.truetype(str(font_path()), size)


def action_label(rect, text, style):
    """RGBA (h, w, 4) for one cyan/pink/purple/gold action banner.

    Port of Jigoku maximum_break_art.action_tile: Rodin Bold Italic drawn at
    4x the cell height, fitted to the cell (condensed only when too wide),
    a 3x3-dilated blurred tint edge, then a white-to-tint vertical gradient
    fill. 24-px cells get a dark plate; taller cells stay transparent."""
    from PIL import Image, ImageDraw, ImageFilter
    _, _, w, h = rect
    face = _font(h * 4)
    l, t, r, b = face.getbbox(text)
    mask = Image.new('L', (r - l, b - t))
    ImageDraw.Draw(mask).text((-l, -t), text, font=face, fill=255)
    border = 3 if h == 24 else 6
    natural = mask.width / mask.height * (h - border * 2)
    mask = mask.resize((min(w - border * 2, round(natural)), h - border * 2), Image.Resampling.LANCZOS)
    canvas = Image.new('L', (w, h))
    canvas.paste(mask, ((w - mask.width) // 2, border))
    out = Image.new('RGBA', (w, h), (0, 8, 8, 255) if h == 24 else (0, 0, 0, 0))
    tint = TINTS[style]
    edge = Image.new('RGBA', (w, h), tint + (255,))
    edge.putalpha(canvas.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.7)))
    out.alpha_composite(edge)
    fill = Image.new('RGBA', (w, h))
    draw = ImageDraw.Draw(fill)
    for y in range(h):
        ratio = y / max(1, h - 1)
        draw.line((0, y, w - 1, y), fill=tuple(round(255 * (1 - ratio) + v * ratio) for v in tint) + (255,))
    fill.putalpha(canvas)
    out.alpha_composite(fill)
    info = {'text': text, 'squeeze': round(min(1.0, (w - border * 2) / natural), 3), 'ink_width': mask.width}
    info['needs_review'] = info['squeeze'] < SQUEEZE_REVIEW
    return np.asarray(out, dtype=np.uint8).copy(), info


def banner_cells():
    """Nine whole-letter cells: [(x, width, label, bbox, pad)], common
    baseline and font scale, widths summing to the atlas width."""
    font = _font(210)
    boxes = [font.getbbox(s) for s in BANNER_CHUNKS]
    top = min(b[1] for b in boxes)
    bottom = max(b[3] for b in boxes)
    pads = [16] * len(BANNER_CHUNKS)          # transparent gutters against bilinear bleed
    pads[BANNER_WORD_GAP_AFTER] += 24
    scale = (BANNER_W - sum(pads)) / sum(b[2] - b[0] for b in boxes)
    widths = [round((b[2] - b[0]) * scale) + pad for b, pad in zip(boxes, pads)]
    widths[-1] += BANNER_W - sum(widths)
    cells, x = [], 0
    for label, box, width, pad in zip(BANNER_CHUNKS, boxes, widths, pads):
        cells.append((x, width, label, box, pad))
        x += width
    return font, top, bottom, cells


def banner_pixels(source_rgba):
    """RGBA (176, 1472, 4) Maximum Break banner. Port of Jigoku
    maximum_break_art.banner: Rodin Bold Italic cells, dark / cream / brown
    dilated outlines, and the gold stripe palette sampled row by row from
    the original Japanese banner."""
    from PIL import Image, ImageDraw, ImageFilter
    font, top, bottom, cells = banner_cells()
    original = gtf.to_image(source_rgba)
    canvas = Image.new('L', (BANNER_W, BANNER_H))
    for x, w, label, (l, _t, r, _b), pad in cells:
        mask = Image.new('L', (r - l, bottom - top))
        ImageDraw.Draw(mask).text((-l, -top), label, font=font, fill=255)
        canvas.paste(mask.resize((w - pad, 144), Image.Resampling.LANCZOS), (x + 8, 16))
    out = Image.new('RGBA', canvas.size)
    for radius, color in ((5, (30, 25, 16, 255)), (4, (246, 245, 228, 255)), (2, (85, 49, 12, 255))):
        layer = Image.new('RGBA', canvas.size, color)
        layer.putalpha(canvas.filter(ImageFilter.MaxFilter(radius * 2 + 1)))
        out.alpha_composite(layer)
    fill = Image.new('RGBA', canvas.size)
    draw = ImageDraw.Draw(fill)
    previous = (190, 116, 20)
    src = np.asarray(original)
    for y in range(BANNER_H):
        row = src[y]
        r, g, b, a = (row[:, i].astype(int) for i in range(4))
        keep = (a > 240) & (r > g) & (g > 40) & (g > b * 1.3)
        if keep.any():
            # most common gold colour of the row, first-seen order on ties (as Counter does)
            previous = Counter(map(tuple, row[keep, :3].tolist())).most_common(1)[0][0]
        draw.line((0, y, BANNER_W - 1, y), fill=tuple(previous) + (255,))
    fill = fill.filter(ImageFilter.GaussianBlur(.8))
    fill.putalpha(canvas)
    out.alpha_composite(fill)
    alpha = out.getchannel('A').getbbox()
    if alpha is None or alpha[0] <= 0 or alpha[2] >= BANNER_W:
        raise ValueError('Maximum Break lettering touches the atlas edge')
    return np.asarray(out, dtype=np.uint8).copy(), cells


def banner_records(cells):
    """New (offset, record) for the nine pieces: contiguous screen cells
    covering x -736..736, y -88..88, each sampling its own atlas cell inset
    by one texel."""
    out = []
    for (offset, _ao, (ax, ay), _orig), (x, w, _label, _box, _pad) in zip(PIECES, cells):
        out.append((offset, (x + SCREEN_X0 - ax, SCREEN_Y0 - ay, x + w + SCREEN_X0 - ax, -SCREEN_Y0 - ay,
                             x + 1, 0, x + w - 1, BANNER_H)))
    return out


# ---------------------------------------------------------------- member ---
def build_member(blob, catalog):
    """(new member bytes, {texture key: RGBA}, {offset: record}, report)."""
    tex = check_source(blob)
    labels = catalog['labels']
    data = bytearray(blob)
    intended, records = {}, {}
    report = {'rendered': {}, 'pending': [], 'records': {}}
    pixels = {i: gtf.decode(blob, tex[i]) for i in SOURCE_PIXELS}
    touched = set()
    for key, spec in LABELS.items():
        en = labels[key].get('en')
        if not en:
            report['pending'].append(key)
            continue
        x, y, w, h = spec['rect']
        if spec['style'] == 'gold_banner':
            rgba, cells = banner_pixels(pixels[spec['texture']])
            for offset, record in banner_records(cells):
                records[offset] = record
                struct.pack_into(RECORD, data, offset, *record)
            report['records'] = {'0x%x' % o: list(r) for o, r in sorted(records.items())}
            info = {'text': en, 'cells': [c[2] for c in cells], 'squeeze': None, 'needs_review': False}
        else:
            rgba, info = action_label(spec['rect'], en, spec['style'])
        pixels[spec['texture']][y:y + h, x:x + w] = rgba
        touched.add(spec['texture'])
        info.update(texture=spec['texture'], rect=list(spec['rect']), jp=spec['jp'],
                    jigoku_wording=labels[key].get('jigoku_en') == en)
        report['rendered'][key] = info
    for index in sorted(touched):
        intended[tex[index].key] = pixels[index]
        data[:] = gtf.replace(bytes(data), tex[index], pixels[index])
    return bytes(data), intended, records, report


def verify_member(original, built, intended, records):
    """Decode `built` and compare with the intended pixels and records.

    Each intended texture must decode to exactly its pixels and every other
    texture must be byte-identical; the nine records must hold their new
    values (anchors and all other script bytes unchanged); headers and
    every other byte must be identical."""
    from tools.texture_art import verify_member as verify_textures
    if len(original) != len(built):
        raise ValueError('member length changed')
    if built == original:
        raise ValueError('member unchanged')
    allowed = {o for o, _a, _p, _r in PIECES}
    if set(records) - allowed:
        raise ValueError('record outside the Maximum Break pieces')
    restored = bytearray(built)
    for offset, record in records.items():
        if read_record(built, offset) != tuple(record):
            raise ValueError('record at 0x%x is not the intended value' % offset)
        restored[offset:offset + 16] = original[offset:offset + 16]
    for offset, anchor_offset, anchor, _r in PIECES:
        if struct.unpack_from('>2h', built, anchor_offset) != anchor:
            raise ValueError('anchor at 0x%x changed' % anchor_offset)
    restored = bytes(restored)
    if restored[:GTF_BASE] != original[:GTF_BASE]:
        raise ValueError('effect-script bytes changed outside the nine records')
    if intended:
        verify_textures(original, restored, intended)
    elif restored != original:
        raise ValueError('texture bytes changed without intended pixels')
    return True


def verify_archive(path, art):
    """Decode the art member of a built CMN.CPK and re-verify it."""
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        if set(by_id) != {MEMBER}:
            raise ValueError('built CMN.CPK member layout changed')
        for mid, data in art['members'].items():
            built = archive.read(by_id[mid])
            if built != data:
                raise ValueError('archive member %d differs from the plan' % mid)
            verify_member(art['sources'][mid], built, art['intended'][mid], art['records'][mid])
    return len(art['members'])


# ------------------------------------------------------------------ plan ---
def plan(settings=None, catalog=None, source=None):
    """CMN.CPK replacement set.

    Returns {'members': {0: bytes} (empty when no label has English),
    'sources', 'intended', 'records', 'report'}. Verification runs here."""
    catalog = catalog if catalog is not None else load_catalog()
    source = source if source is not None else source_member(settings)
    data, intended, records, report = build_member(source, catalog)
    report = dict(report, schema=1, archive=CMN, runtime_verified=False)
    if data == source:
        report['members'] = {}
        return {'members': {}, 'sources': {}, 'intended': {}, 'records': {}, 'report': report}
    verify_member(source, data, intended, records)
    report['members'] = {MEMBER: {'input_sha256': sha256(source), 'output_sha256': sha256(data)}}
    report['review'] = sorted(k for k, v in report['rendered'].items() if v.get('needs_review'))
    return {'members': {MEMBER: data}, 'sources': {MEMBER: source}, 'intended': {MEMBER: intended},
            'records': {MEMBER: records}, 'report': report}


# ------------------------------------------------------- jigoku evidence ---
def jigoku_members():
    out = {}
    for label, path in (('original', JIGOKU_ORIGINAL), ('shipped', JIGOKU_SHIPPED)):
        with CPK(path) as archive:
            out[label] = archive.read(archive.files[0])
    if sha256(out['original']) != JIGOKU_MEMBER_SHA256 or sha256(out['shipped']) != JIGOKU_SHIPPED_MEMBER_SHA256:
        raise ValueError('Jigoku CMN members are not the recorded versions')
    return out


def compare_jigoku(source, catalog=None):
    """Evidence that the Tengoku edit is Jigoku 0.6.24's, re-located.

    - texture-by-texture pixel matches between Tengoku and Jigoku original
    - the nine records: Jigoku LE at offset+0x688 == Tengoku BE at offset
    - the whole Maximum Break script block is word-equivalent after the
      0x688 shift (u32/u16 byte order only)
    - Jigoku's shipped member differs from its original only inside its nine
      records and textures 6, 10, 11 and 16
    - our renderers given Jigoku's wording reproduce the shipped pixels and
      records exactly."""
    j = jigoku_members()
    jo, js = j['original'], j['shipped']
    t_tex = textures(source)
    j_tex = gtf.gtfs(jo)[0][1]
    pix = lambda b, t: sha256(b[t['offset']:t['offset'] + t['size']])
    j_sha = {pix(jo, t): t['index'] for t in j_tex}
    matches = {t['index']: j_sha.get(pix(source, t)) for t in t_tex}
    shipped_changed = [t['index'] for t, s in zip(j_tex, gtf.gtfs(js)[0][1]) if pix(jo, t) != pix(js, s)]
    records = []
    for offset, anchor_offset, anchor, record in PIECES:
        jo_off = offset + RECORD_SHIFT
        records.append({'tengoku': '0x%x' % offset, 'jigoku': '0x%x' % jo_off,
                        'jigoku_le': list(struct.unpack_from('<4h4H', jo, jo_off)),
                        'tengoku_be': list(read_record(source, offset)),
                        'jigoku_anchor_le': list(struct.unpack_from('<2h', jo, anchor_offset + RECORD_SHIFT)),
                        'tengoku_anchor_be': list(struct.unpack_from('>2h', source, anchor_offset)),
                        'jigoku_shipped_le': list(struct.unpack_from('<4h4H', js, jo_off))})
    block = (0x38d8, 0x4278)          # Jigoku: first piece header .. end of the ninth piece
    odd = []
    for w in range(block[0], block[1], 4):
        a, b = jo[w:w + 4], source[w - RECORD_SHIFT:w - RECORD_SHIFT + 4]
        if not (a == b or a == b[::-1] or (a[:2] == b[1::-1] and a[2:] == b[:1:-1])
                or (a[:2] == b[:2] and a[2:] == b[:1:-1])):
            odd.append('0x%x' % w)
    head = [i for i in range(JIGOKU_GTF_BASE) if jo[i] != js[i]]
    piece_bytes = {o + RECORD_SHIFT + k for o, *_ in PIECES for k in range(16)}
    # Renderer calibration with Jigoku's own wording.
    jt = {i: gtf.decode(jo, j_tex[i]) for i in (10, 11, 16)}
    want = {i: gtf.decode(js, gtf.gtfs(js)[0][1][i]) for i in (10, 11, 16)}
    calib = {}
    for key, text in (('combo_attack', 'Combo Attack'), ('counter', 'Counter'), ('attack_again', 'Attack Again'),
                      ('support_attack', 'Support Attack'), ('support_defense', 'Support Defend')):
        spec = LABELS[key]
        x, y, w, h = spec['rect']
        rgba, _ = action_label(spec['rect'], text, spec['style'])
        calib[key] = bool(np.array_equal(rgba, want[spec['texture']][y:y + h, x:x + w]))
    banner, cells = banner_pixels(jt[16])
    calib['maximum_break'] = bool(np.array_equal(banner, want[16]))
    calib['records'] = all(list(r) == rec['jigoku_shipped_le'] for (_o, r), rec in zip(banner_records(cells), records))
    return {
        'tengoku_textures': len(t_tex), 'jigoku_textures': len(j_tex),
        'pixel_identical_to_jigoku_original': {k: v for k, v in matches.items() if v is not None},
        'jigoku_shipped_changed_textures': shipped_changed,
        'jigoku_shipped_script_bytes_changed': len(head),
        'jigoku_shipped_script_changes_only_in_records': set(head) <= piece_bytes,
        'records': records,
        'records_equal': all(r['jigoku_le'] == r['tengoku_be'] and r['jigoku_anchor_le'] == r['tengoku_anchor_be']
                             for r in records),
        'block_jigoku': ['0x%x' % block[0], '0x%x' % block[1]],
        'block_tengoku': ['0x%x' % (block[0] - RECORD_SHIFT), '0x%x' % (block[1] - RECORD_SHIFT)],
        'block_words_not_byte_order_equivalent': odd,
        'tengoku_strip_quads': ['0x%x' % p for p, _r in strip_quads(source)],
        'jigoku_strip_quads': ['0x%x' % p for p, _r in strip_quads(jo, JIGOKU_GTF_BASE, '<4h4H')],
        'renderer_reproduces_jigoku_0.6.24': calib,
    }


# --------------------------------------------------------------- preview ---
def project(blob, records=None):
    """CPU projection of the nine pieces' initial keyframe (screen space
    1472x176 around the effect origin), sampling t16 at their UVs.
    Diagnostic only, not effect playback."""
    from PIL import Image
    atlas = gtf.to_image(gtf.decode(blob, textures(blob)[16]))
    canvas = Image.new('RGBA', (BANNER_W, BANNER_H))
    for offset, anchor_offset, _a, _r in PIECES:
        ax, ay = struct.unpack_from('>2h', blob, anchor_offset)
        x0, y0, x1, y1, u0, v0, u1, v1 = read_record(blob, offset)
        tile = atlas.crop((u0, v0, u1, v1)).resize((x1 - x0, y1 - y0), Image.BILINEAR)
        canvas.alpha_composite(tile, (ax + x0 - SCREEN_X0, ay + y0 - SCREEN_Y0))
    return canvas


def _panel(rgba, scale, background=(24, 28, 40)):
    from PIL import Image
    image = gtf.preview(np.asarray(rgba, dtype=np.uint8), background)
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST if scale > 1 else Image.LANCZOS)


def preview(settings=None, apply=False):
    """cmn_before_after.png (each lettered texture, source | built) and
    cmn_maximum_break_projection.png (pieces as drawn, before | after)."""
    from PIL import Image, ImageDraw
    art = plan(settings)
    source = art['sources'][MEMBER]
    built = art['members'][MEMBER]
    tex = textures(source)
    rows = []
    for index, scale in ((16, 1), (10, 2), (11, 2)):
        rows.append(('t%d source' % index, _panel(gtf.decode(source, tex[index]), scale)))
        rows.append(('t%d built' % index, _panel(gtf.decode(built, tex[index]), scale)))
    width = max(p.width for _l, p in rows) + 20
    sheet = Image.new('RGB', (width, sum(p.height + 24 for _l, p in rows) + 30), (40, 16, 56))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 8), 'CMN.CPK lettering: source vs built (t10/t11 at 2x). Texture previews are not in-game evidence.',
              fill=(255, 255, 160))
    y = 30
    for label, panel in rows:
        draw.text((10, y + 4), label, fill=(255, 255, 160))
        sheet.paste(panel, (10, y + 20))
        y += panel.height + 24
    proj = Image.new('RGB', (BANNER_W + 20, 2 * (BANNER_H + 30) + 30), (40, 16, 56))
    draw = ImageDraw.Draw(proj)
    draw.text((10, 8), 'Maximum Break, nine quads at their initial keyframe (CPU projection of anchor + XY bounds + UVs)',
              fill=(255, 255, 160))
    for i, (label, blob) in enumerate((('before: Japanese, piece 3 re-samples piece 0', source),
                                       ('after: nine English cells, contiguous bounds', built))):
        y = 30 + i * (BANNER_H + 30)
        draw.text((10, y + 4), label, fill=(255, 255, 160))
        base = Image.new('RGBA', (BANNER_W, BANNER_H), (24, 28, 40, 255))
        base.alpha_composite(project(blob))
        proj.paste(base.convert('RGB'), (10, y + 22))
    targets = (PREVIEWS / 'cmn_before_after.png', PREVIEWS / 'cmn_maximum_break_projection.png')
    if apply:
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        sheet.save(targets[0])
        proj.save(targets[1])
    return targets, art['report']


def inventory(settings=None, apply=False, jigoku=True):
    """Contact sheets of every texture (Tengoku, plus Jigoku original and
    shipped) and cmn_inventory.json with per-texture text classification."""
    from PIL import Image, ImageDraw
    source = source_member(settings)
    tex = textures(source)
    evidence = compare_jigoku(source) if jigoku else None
    rows = []
    for t in tex:
        kind, note = TEXTURE_NOTES[t['index']]
        rows.append({'texture': t['index'], 'size': [t['width'], t['height']], 'format': gtf.FORMATS[t['fmt']],
                     'offset': '0x%x' % t['offset'], 'pixel_sha256': sha256(source[t['offset']:t['offset'] + t['size']]),
                     'text': kind, 'content': note,
                     'jigoku_original_texture': (evidence or {}).get('pixel_identical_to_jigoku_original', {}).get(t['index'])})

    def sheet(blob, items, title):
        panels = []
        for t in items:
            rgba = gtf.decode(blob, t)
            scale = 1 if max(t['width'], t['height']) > 300 else 2
            panels.append(('t%d %dx%d %s' % (t['index'], t['width'], t['height'],
                                              TEXTURE_NOTES.get(t['index'], ('', ''))[0] if blob is source else ''),
                           _panel(rgba, scale)))
        width = 1500
        x = y = 0
        line_h = 0
        placed = []
        for label, p in panels:
            span = max(p.width, 6 * len(label))       # keep labels of tiny textures apart
            if x + span + 10 > width:
                x, y, line_h = 0, y + line_h + 26, 0
            placed.append((label, p, x + 10, y + 30))
            x += span + 14
            line_h = max(line_h, p.height)
        image = Image.new('RGB', (width + 20, y + line_h + 60), (40, 16, 56))
        draw = ImageDraw.Draw(image)
        draw.text((10, 8), title, fill=(255, 255, 160))
        for label, p, px, py in placed:
            draw.text((px, py), label, fill=(255, 255, 160))
            image.paste(p, (px, py + 16))
        return image
    images = {'cmn_tengoku_textures.png': sheet(source, tex, 'Tengoku CMN.CPK member 0: 26 textures '
                                                 '(text: japanese / english / none)')}
    if jigoku:
        j = jigoku_members()
        jt = gtf.gtfs(j['original'])[0][1]
        st = gtf.gtfs(j['shipped'])[0][1]
        images['cmn_jigoku_original_textures.png'] = sheet(j['original'], jt, 'Jigoku original CMN: 20 textures')
        images['cmn_jigoku_shipped_changed.png'] = sheet(j['shipped'], [st[i] for i in evidence['jigoku_shipped_changed_textures']],
                                                         'Jigoku 0.6.24 shipped CMN: changed textures')
    report = {'schema': 1, 'archive': CMN, 'archive_sha256': ARCHIVE_SHA256, 'member_sha256': MEMBER_SHA256,
              'gtf_offset': '0x%x' % GTF_BASE, 'textures': rows,
              'japanese_textures': [r['texture'] for r in rows if r['text'] == 'japanese'],
              'english_textures': [r['texture'] for r in rows if r['text'] == 'english'],
              'jigoku': evidence, 'runtime_verified': False}
    if apply:
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        for name, image in images.items():
            image.save(PREVIEWS / name)
        write_json(PREVIEWS / 'cmn_inventory.json', report)
    return report, sorted(images)


# ------------------------------------------------------------------- CLI ---
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['plan', 'inventory', 'preview', 'compare-jigoku'])
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    settings = _settings()
    if a.command == 'plan':
        art = plan(settings)
        print(json.dumps(art['report'], ensure_ascii=False, indent=2))
        print('CMN members: %s (dry run; game_build writes the archive)' % sorted(art['members']))
    elif a.command == 'compare-jigoku':
        print(json.dumps(compare_jigoku(source_member(settings)), ensure_ascii=False, indent=2))
    elif a.command == 'inventory':
        report, names = inventory(settings, a.apply)
        print(json.dumps({k: report[k] for k in ('japanese_textures', 'english_textures')}, indent=2))
        print('wrote %s to %s' % (names + ['cmn_inventory.json'], PREVIEWS) if a.apply else
              'DRY RUN: pass --apply to write %s' % (names + ['cmn_inventory.json']))
    else:
        targets, report = preview(settings, a.apply)
        print(json.dumps({k: v for k, v in report['rendered'].items()}, ensure_ascii=False, indent=2))
        print('wrote %s' % ', '.join(str(t) for t in targets) if a.apply else 'DRY RUN: pass --apply to write previews')
    return 0


if __name__ == '__main__':
    sys.exit(main())
