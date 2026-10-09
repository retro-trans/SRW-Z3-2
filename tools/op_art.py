"""Opening-demo series captions in BTLC/OP.CPK, plus the title-screen inventory.

OP.CPK (ITOC, 3 members) holds the series-name strips shown during the
opening demo: 31 linear ARGB 1280x64 textures (members 0 and 1: 10 each,
member 2: 11), one series per texture, inside a container whose GTF sits at
0x60 followed by the demo's effect scripts. Only texture pixel bytes are
rewritten; headers, scripts and every other byte stay identical.

Original encoding, measured on all 31 strips:
  * R=G=B = the white Mincho fill coverage, 16 levels (multiples of 17)
  * alpha = fill + a soft black halo about 5 px wide around it
    (fitted: dilate 1 px, gaussian sigma 1.25, gain 3, gamma 0.7;
     mean error about 5/255 on the halo), i.e. white text over a black
    halo, straight alpha, RGB = 0 wherever alpha = 0
  * centred on x = 639.5; the game's own Latin letters (UC, SEED DESTINY,
    Endless Waltz, A wakening of the Trailblazer) are a bold serif with a
    29 px cap height on baseline y = 47 (bottom pixel row 47).
The renderer reproduces that encoding with the PS3 Matisse Bold face.

English = the series names in work/translation/en/ui/rpw_names.json
(strings.series, the glossary's official names), recorded per texture in
work/translation/en/ui/op_art.json by `catalog --apply`.

    python -m tools.op_art plan
    python -m tools.op_art catalog          [--apply]
    python -m tools.op_art preview          [--apply]  (work/ui/textures/op)
    python -m tools.op_art title-inventory  [--apply]  (EFFPS3 title screen, read only)

game_build integration: docs/ART_OP.md. Requires numpy + Pillow (bundled
Python). Fonts are read (never written) from the RPCS3 dev_flash folder.
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

DISC = '/PS3_GAME/USRDIR/DATA/BTLC/OP.CPK'
EFFPS3 = '/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK'
CATALOG = ROOT / 'work/translation/en/ui/op_art.json'
RPW_NAMES = ROOT / 'work/translation/en/ui/rpw_names.json'
PREVIEWS = ROOT / 'work/ui/textures/op'

STRIP_W, STRIP_H = 1280, 64
GTF_BASE = 0x60
LAYOUT = {0: 10, 1: 10, 2: 11}            # member -> number of 1280x64 strips
# Decoded member SHA-256 of the pristine Tengoku OP.CPK
# (archive sha256 09d3fb03..., work/tengoku/source_manifest.json).
MEMBER_SHA256 = {
    0: 'd6104784515d6c9a024eb49c9a75b5631cd1778ef5ab80f1578e8bec36d6b737',
    1: '7bd56d102c791112aa0c34201425a20b76c8edf1a747a7838f60fce5adc73c65',
    2: '328e8bd92b71272e23a499e5d012782dc19a4d725682968d5b597360c8491964',
}

# Series shown by each strip, identified visually from the contact sheet
# (work/ui/textures/op/op_captions_original.png) and confirmed by `catalog`
# with a rendered-Mincho correlation against every series name. Keys are the
# rpw_names.json strings.series keys (the game's own series table).
IDENTIFIED = {
    (0, 0): '機動戦士ガンダムＵＣ',
    (0, 1): '真（チェンジ！！）ゲッターロボ\u3000世界最後の日',
    (0, 2): '超時空世紀オーガス',
    (0, 3): 'ヱヴァンゲリヲン新劇場版：Ｑ',
    (0, 4): '無敵超人ザンボット３',
    (0, 5): '機動戦士Ｚガンダム',
    (0, 6): '天元突破グレンラガン',
    (0, 7): 'フルメタル・パニック！',
    (0, 8): '太陽の使者\u3000鉄人２８号',
    (0, 9): '劇場版マクロスＦ～サヨナラノツバサ～',
    (1, 0): '翠星のガルガンティア',
    (1, 1): 'トップをねらえ！',
    (1, 2): '機動戦士ガンダムＳＥＥＤ\u3000ＤＥＳＴＩＮＹ',
    (1, 3): 'アクエリオンＥＶＯＬ',
    (1, 4): '地球防衛企業ダイ・ガード',
    (1, 5): '無敵鋼人ダイターン３',
    (1, 6): '∀ガンダム',
    (1, 7): 'ＴＨＥビッグオー',
    (1, 8): '無敵ロボ\u3000トライダーＧ７',
    (1, 9): '劇場版\u3000機動戦士ガンダム００\u3000－Ａ\u3000ｗａｋｅｎｉｎｇ\u3000ｏｆ\u3000ｔｈｅ\u3000Ｔｒａｉｌｂｌａｚｅｒ－',
    (2, 0): '創聖のアクエリオン',
    (2, 1): '機動戦士ガンダム\u3000逆襲のシャア',
    (2, 2): '六神合体ゴッドマーズ',
    (2, 3): '新機動戦記ガンダムＷ\u3000Ｅｎｄｌｅｓｓ\u3000Ｗａｌｔｚ',
    (2, 4): 'コードギアス\u3000反逆のルルーシュ\u3000Ｒ２',
    (2, 5): '獣装機攻ダンクーガノヴァ',
    (2, 6): 'マクロス７',
    (2, 7): '装甲騎兵ボトムズ\u3000孤影再び',
    (2, 8): '機動新世紀ガンダムＸ',
    (2, 9): '真マジンガー\u3000衝撃！Ｚ編',
    (2, 10): 'トップをねらえ２！',
}

STYLE = {
    'face': 'SCE-PS3-MT-B-LATIN.TTF',   # Matisse Bold: closest PS3 face to the strips' own Latin
    'cap_height': 29,                   # measured: E of "Endless Waltz", S of "SEED DESTINY"
    'baseline': 48,                     # pixel edge under row 47 (the Latin baseline)
    'center_x': 639.5,                  # fill-ink centre of the 31 originals
    'max_width': 1220,                  # widest original fill: x 30..1249 (m1 t9)
    'min_squeeze': 0.80,                # horizontal condensing before the size shrinks
    'halo_radius': 1, 'halo_sigma': 1.25, 'halo_gain': 3.0, 'halo_gamma': 0.7,
}
SUPERSAMPLE = 4
FILL_STEP = 17                          # 16 grey levels: 0, 17, ..., 255


def font_dir():
    from tools.ui_build import FACE
    return FACE.parent


def _settings():
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


def key(member, texture):
    return 'm%d_t%d' % (member, texture)


# ---------------------------------------------------------------- sources ---
def source_members(settings):
    """({member id: decoded bytes}, archive path) from the verified pristine OP.CPK."""
    from tools.pipeline import verified_source
    path = verified_source(settings, DISC)
    with CPK(path) as archive:
        members = {e['id']: archive.read(e) for e in archive.files}
    if set(members) != set(LAYOUT):
        raise ValueError('OP.CPK members changed: %s' % sorted(members))
    for mid, data in members.items():
        if sha256(data) != MEMBER_SHA256[mid]:
            raise ValueError('OP.CPK member %d is not the guarded Tengoku source' % mid)
    return members, path


def strips(blob, member):
    """The member's caption textures, after checking the layout."""
    found = gtf.gtfs(blob)
    if len(found) != 1 or found[0][0] != GTF_BASE:
        raise ValueError('OP member %d: expected one GTF at 0x%x' % (member, GTF_BASE))
    tex = found[0][1]
    if len(tex) != LAYOUT[member]:
        raise ValueError('OP member %d: expected %d strips' % (member, LAYOUT[member]))
    for i, t in enumerate(tex):
        if (t['fmt'], t['width'], t['height'], t['size'], t['index']) != \
                (gtf.LINEAR_ARGB, STRIP_W, STRIP_H, STRIP_W * STRIP_H * 4, i):
            raise ValueError('OP member %d texture %d layout changed' % (member, i))
    return tex


# ------------------------------------------------------------- catalogs ---
def series_names(path=RPW_NAMES):
    return {jp: row['en'] for jp, row in
            json.loads(Path(path).read_text(encoding='utf-8'))['strings']['series'].items()}


def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('captions'), dict):
        raise ValueError('op_art.json: expected schema 1 with "captions"')
    want = {key(m, t) for m, n in LAYOUT.items() for t in range(n)}
    if set(data['captions']) != want:
        raise ValueError('op_art.json: captions must be exactly %d strips' % len(want))
    for k, row in data['captions'].items():
        en = row.get('en')
        if en is not None and (not isinstance(en, str) or not en.strip() or not en.isascii()
                               or '\n' in en):
            raise ValueError('op_art.json %s: English must be one ASCII line' % k)
    return data


# -------------------------------------------------------------- renderer ---
def _font(name, size):
    from PIL import ImageFont
    return ImageFont.truetype(str(font_dir() / name), size)


def _blur(a, sigma):
    from tools.texture_art import _blur as blur
    return blur(a, sigma)


def _dilate(a, r):
    if r <= 0:
        return a
    p = np.pad(a, r)
    out = a.copy()
    h, w = a.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 0.5 * r:
                out = np.maximum(out, p[r + dy:r + dy + h, r + dx:r + dx + w])
    return out


def _cap_size(style):
    probe = _font(style['face'], 400)
    l, t, r, b = probe.getbbox('H')
    return 400.0 * style['cap_height'] / (b - t)


def _coverage(text, size, style):
    """Supersampled coverage (h*4, ink width*4) with the baseline on the
    row edge style['baseline']*4, plus the ink's left/right in that canvas."""
    from PIL import Image, ImageDraw
    font = _font(style['face'], int(round(size * SUPERSAMPLE)))
    l, t, r, b = font.getbbox(text, anchor='ls')
    width = r - l + 8 * SUPERSAMPLE
    image = Image.new('L', (width, STRIP_H * SUPERSAMPLE))
    ImageDraw.Draw(image).text((4 * SUPERSAMPLE - l, style['baseline'] * SUPERSAMPLE), text,
                               font=font, fill=255, anchor='ls')
    box = image.getbbox()
    if box is None:
        raise ValueError('caption renders no ink: %r' % text)
    return image.crop((box[0], 0, box[2], STRIP_H * SUPERSAMPLE))


def caption_layout(text, style=None):
    style = dict(STYLE, **(style or {}))
    size = _cap_size(style)
    ink = _coverage(text, size, style)
    natural = ink.width / SUPERSAMPLE
    squeeze, shrink = 1.0, 1.0
    if natural > style['max_width']:
        squeeze = max(style['min_squeeze'], style['max_width'] / natural)
        if natural * squeeze > style['max_width']:
            shrink = style['max_width'] / (natural * squeeze)
            ink = _coverage(text, size * shrink, style)
            natural = ink.width / SUPERSAMPLE
            squeeze = min(1.0, max(style['min_squeeze'], style['max_width'] / natural))
    return dict(text=text, size=size * shrink, ink=ink, natural_width=natural,
                squeeze=squeeze, shrink=shrink, style=style)


def encode(c, style=None):
    """RGBA strip from fill coverage c (64, 1280) in 0..1, in the original
    encoding: white fill over a soft black halo, straight alpha."""
    style = dict(STYLE, **(style or {}))
    halo = np.clip(style['halo_gain'] * _blur(_dilate(c, style['halo_radius']), style['halo_sigma']),
                   0.0, 1.0) ** style['halo_gamma']
    alpha = c + halo * (1.0 - c)
    a8 = np.rint(255.0 * alpha).astype(np.int32)
    grey = np.where(a8 > 0, np.rint(255.0 * c / np.maximum(alpha, 1e-9) / FILL_STEP) * FILL_STEP, 0)
    grey = np.clip(grey, 0, 255).astype(np.uint8)
    rgba = np.zeros(c.shape + (4,), np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = grey
    rgba[..., 3] = a8.astype(np.uint8)
    return rgba


def caption_pixels(text, style=None):
    """(RGBA (64, 1280, 4) uint8, info) for one English caption."""
    from PIL import Image
    lay = caption_layout(text, style)
    style = lay['style']
    w = max(1, int(round(lay['natural_width'] * lay['squeeze'])))
    if w > style['max_width']:
        raise ValueError('caption does not fit: %r (%d px)' % (text, w))
    big = lay['ink'].resize((w * SUPERSAMPLE, STRIP_H * SUPERSAMPLE), Image.LANCZOS) \
        if w * SUPERSAMPLE != lay['ink'].width else lay['ink']
    fill = np.asarray(big.resize((w, STRIP_H), Image.BOX), dtype=np.float64) / 255.0
    x0 = int(round(style['center_x'] - (w - 1) / 2.0))
    c = np.zeros((STRIP_H, STRIP_W))
    c[:, x0:x0 + w] = np.clip(fill, 0.0, 1.0)
    rgba = encode(c, style)
    ys, xs = np.nonzero(rgba[..., 3])
    if xs.min() < 16 or xs.max() > STRIP_W - 17 or ys.min() < 4 or ys.max() > STRIP_H - 2:
        raise ValueError('caption placement out of bounds: %r' % text)
    fy, fx = np.nonzero(rgba[..., 0])
    info = {'text': text, 'font_px': round(lay['size'], 2), 'natural_width': round(lay['natural_width'], 1),
            'squeeze': round(lay['squeeze'], 3), 'shrink': round(lay['shrink'], 3),
            'fill_box': [int(fx.min()), int(fy.min()), int(fx.max() - fx.min() + 1), int(fy.max() - fy.min() + 1)],
            'alpha_box': [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
            'needs_review': lay['shrink'] < 1.0 or lay['squeeze'] < 0.85}
    return rgba, info


def caption_member(blob, member, texts, style=None):
    """(new member bytes, {texture key: RGBA}, {texture index: info}).
    texts: {texture index: English}; other strips are left untouched."""
    tex = strips(blob, member)
    data, intended, infos = blob, {}, {}
    for index, text in sorted(texts.items()):
        rgba, info = caption_pixels(text, style)
        data = gtf.replace(data, tex[index], rgba)
        intended[tex[index].key] = rgba
        infos[index] = info
    return data, intended, infos


# ---------------------------------------------------------- verification ---
def verify_member(original, built, intended):
    from tools.texture_art import verify_member as verify
    return verify(original, built, intended)


def verify_archive(path, art):
    """Decode every replaced member of a built OP.CPK and re-verify it."""
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        if set(by_id) != set(LAYOUT):
            raise ValueError('built OP.CPK member identities changed')
        for mid, data in art['members'].items():
            built = archive.read(by_id[mid])
            if built != data:
                raise ValueError('OP.CPK member %d differs from the plan' % mid)
            verify_member(art['sources'][mid], built, art['intended'][mid])
    return len(art['members'])


# ------------------------------------------------------------------ plan ---
def plan(settings=None, catalog=None, style=None):
    """Replacement set for OP.CPK.

    Returns {'members': {id: bytes}, 'sources', 'intended', 'report',
    'source_path'}. Strips whose "en" is null stay untouched (pending);
    a member with no English at all is not replaced."""
    settings = settings or _settings()
    catalog = catalog if catalog is not None else load_catalog()
    style = dict(STYLE, **(catalog.get('style') or {}), **(style or {}))
    sources, path = source_members(settings)
    members, intended = {}, {}
    report = {'schema': 1, 'archive': DISC, 'captions': {}, 'pending': [], 'runtime_verified': False}
    for mid in sorted(LAYOUT):
        tex = strips(sources[mid], mid)
        texts = {}
        for i in range(LAYOUT[mid]):
            row = catalog['captions'][key(mid, i)]
            pix = sha256(sources[mid][tex[i]['offset']:tex[i]['offset'] + tex[i]['size']])
            if row.get('texture_sha256') and row['texture_sha256'] != pix:
                raise ValueError('%s: source strip differs from the catalog guard' % key(mid, i))
            if row.get('en'):
                texts[i] = row['en']
            else:
                report['pending'].append(key(mid, i))
        if not texts:
            continue
        data, pix, infos = caption_member(sources[mid], mid, texts, style)
        verify_member(sources[mid], data, pix)
        members[mid], intended[mid] = data, pix
        for i, info in infos.items():
            report['captions'][key(mid, i)] = info
    report['members'] = {mid: {'input_sha256': sha256(sources[mid]), 'output_sha256': sha256(members[mid])}
                         for mid in sorted(members)}
    report['needs_review'] = sorted(k for k, v in report['captions'].items() if v['needs_review'])
    return {'members': members, 'sources': {m: sources[m] for m in members}, 'intended': intended,
            'report': report, 'source_path': path}


# --------------------------------------------------------------- catalog ---
def _vec(image):
    from PIL import Image
    box = image.getbbox()
    a = np.asarray(image.crop(box).resize((384, 32), Image.BILINEAR), dtype=np.float64).ravel()
    a = a - a.mean()
    return a / (np.linalg.norm(a) or 1)


def _is_latin(c):
    return 'Ａ' <= c <= 'Ｚ' or 'ａ' <= c <= 'ｚ'


def _render_name(text, font, latin_gap=15):
    """A table name drawn as the strips set it: Latin letters half-width
    and letter-spaced (SEED DESTINY, EVOL), everything else as written."""
    from PIL import Image, ImageDraw
    image = Image.new('L', (120 * len(text) + 200, 160))
    draw, x = ImageDraw.Draw(image), 20.0
    for c in text:
        glyph = chr(ord(c) - 0xFEE0) if _is_latin(c) else c
        draw.text((x, 20), glyph, font=font, fill=255)
        x += font.getlength(glyph) + (latin_gap if _is_latin(c) else 0)
    return image


def match_series(fills, candidates, mincho='C:/Windows/Fonts/yumin.ttf'):
    """Normalised correlation of each strip's fill ink against every
    candidate name rendered in a Mincho face (both stretched to 384x32).
    A coarse cross-check only: names that differ in one glyph score close."""
    from PIL import Image, ImageFont
    font = ImageFont.truetype(mincho, 100)
    cand = np.stack([_vec(_render_name(text, font)) for text in candidates])
    return {k: cand @ _vec(Image.fromarray(np.ascontiguousarray(fill))) for k, fill in fills.items()}


def build_catalog(settings, apply=False):
    """op_art.json from the pristine strips. The visual identification
    (IDENTIFIED) is the contract; the correlation must rank it first among
    the 31 identified names (texture order not permuted), and its rank among
    every series name in the table is recorded."""
    sources, _path = source_members(settings)
    names = series_names()
    every = sorted(names)
    order = [jp for _k, jp in sorted(IDENTIFIED.items())]
    problems = ['%s: %s is not in rpw_names series' % (key(*k), jp)
                for k, jp in sorted(IDENTIFIED.items()) if jp not in names]
    if problems or len(set(order)) != len(order):
        raise ValueError('caption identification invalid: %s' % (problems[:5] or 'duplicate names'))
    fills, pixels = {}, {}
    for mid in sorted(LAYOUT):
        for t in strips(sources[mid], mid):
            rgba = gtf.decode(sources[mid], t)
            fills[(mid, t['index'])] = rgba[..., 0]
            pixels[(mid, t['index'])] = (rgba, sources[mid][t['offset']:t['offset'] + t['size']])
    scores = match_series(fills, order)
    scores_all = match_series(fills, every)
    old = load_catalog()['captions'] if CATALOG.exists() else {}
    captions, margins, not_first_overall = {}, [], []
    for (mid, i), jp in sorted(IDENTIFIED.items()):
        s = scores[(mid, i)]
        ranked = np.argsort(-s)
        want = order.index(jp)
        best = int(ranked[0])
        runner = float(s[ranked[1]] if best == want else s[best])
        if best != want:
            problems.append('%s: best match %s, identified %s' % (key(mid, i), order[best], jp))
        margins.append(float(s[want]) - runner)
        rank_all = int(np.nonzero(np.argsort(-scores_all[(mid, i)]) == every.index(jp))[0][0]) + 1
        if rank_all != 1:
            not_first_overall.append('%s (%s ranks %d)' % (key(mid, i), jp, rank_all))
        rgba, raw = pixels[(mid, i)]
        ys, xs = np.nonzero(rgba[..., 3])
        fy, fx = np.nonzero(rgba[..., 0])
        prev = old.get(key(mid, i)) or {}
        en = names[jp]
        row = {'member': mid, 'texture': i, 'jp': jp, 'en': en,
               'en_source': 'rpw_names.json strings.series (glossary)',
               'match_score': round(float(s[want]), 3), 'runner_up_score': round(runner, 3),
               'rank_among_all_series': rank_all,
               'fill_box': [int(fx.min()), int(fy.min()), int(fx.max() - fx.min() + 1), int(fy.max() - fy.min() + 1)],
               'alpha_box': [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
               'texture_offset': '0x%x' % strips(sources[mid], mid)[i]['offset'],
               'texture_sha256': sha256(raw)}
        if prev.get('en') and prev['en'] != en:
            row['en_previous'] = prev['en']
        captions[key(mid, i)] = row
    if problems:
        raise ValueError('caption identification disagrees: %s' % problems[:5])
    candidates = every
    catalog = {
        'schema': 1,
        'about': 'Series-name strips of the opening demo, BTLC/OP.CPK (31 linear ARGB 1280x64 textures; '
                 'GTF at 0x60 of each member). English = rpw_names.json strings.series, rendered by '
                 'tools/op_art.py. Edit English in rpw_names / the glossary, then rerun `op_art catalog --apply`.',
        'evidence': 'jp: visual identification of each strip (tools/op_art.IDENTIFIED; contact sheet '
                    'work/ui/textures/op/op_captions_original.png). Cross-check: each of the 31 names rendered '
                    'in a Mincho face (Latin half-width, letter-spaced) and correlated with the strip ink; the '
                    'identified name ranks first among the 31 for every strip (match_score vs runner_up_score), '
                    'so the texture order is not permuted. rank_among_all_series is the rank among all %d '
                    'table names (coarse: names differing by one glyph, e.g. Evangelion Q vs Jo, score close).'
                    % len(candidates),
        'archive': DISC,
        'members': {str(m): {'sha256': sha256(sources[m]), 'strips': LAYOUT[m]} for m in sorted(LAYOUT)},
        'style': {},
        'captions': captions,
    }
    summary = {'captions': len(captions), 'with_english': sum(1 for r in captions.values() if r['en']),
               'min_margin': round(min(margins), 3), 'problems': problems,
               'not_first_among_all_series': not_first_overall}
    if apply:
        write_json(CATALOG, catalog)
    return catalog, summary


# --------------------------------------------------------------- preview ---
def _strip_image(rgba, background=(18, 22, 40)):
    return gtf.preview(rgba, background)


def preview(settings, apply=False):
    """op_captions_original.png and op_captions_english.png (original above,
    English below, per strip) in work/ui/textures/op."""
    from PIL import Image, ImageDraw
    catalog = load_catalog()
    sources, _ = source_members(settings)
    art = plan(settings, catalog)
    rows = []
    for mid in sorted(LAYOUT):
        tex = strips(sources[mid], mid)
        built = art['members'].get(mid, sources[mid])
        for i in range(LAYOUT[mid]):
            row = catalog['captions'][key(mid, i)]
            info = art['report']['captions'].get(key(mid, i), {})
            rows.append(('%s  %s' % (key(mid, i), row['en'] or '(pending)'), info,
                         gtf.decode(sources[mid], tex[i]), gtf.decode(built, tex[i])))
    original = Image.new('RGB', (STRIP_W, len(rows) * (STRIP_H + 16)), (40, 16, 56))
    english = Image.new('RGB', (STRIP_W, len(rows) * (2 * STRIP_H + 20)), (40, 16, 56))
    do, de = ImageDraw.Draw(original), ImageDraw.Draw(english)
    for n, (label, info, src, out) in enumerate(rows):
        y = n * (STRIP_H + 16)
        do.text((4, y + 2), label.split('  ')[0], fill=(255, 255, 160))
        original.paste(_strip_image(src), (0, y + 16))
        y = n * (2 * STRIP_H + 20)
        extra = '  [squeeze %.2f, shrink %.2f]' % (info['squeeze'], info['shrink']) if info else ''
        de.text((4, y + 4), label + extra, fill=(255, 255, 160))
        english.paste(_strip_image(src), (0, y + 18))
        english.paste(_strip_image(out), (0, y + 18 + STRIP_H))
    targets = [PREVIEWS / 'op_captions_original.png', PREVIEWS / 'op_captions_english.png']
    if apply:
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        original.save(targets[0])
        english.save(targets[1])
        write_json(PREVIEWS / 'op_inventory.json', {
            'schema': 1, 'archive': DISC, 'texture_size': [STRIP_W, STRIP_H], 'format': 'A8R8G8B8 linear (0xA5)',
            'note': 'one series-name strip per texture; boxes are [x, y, w, h] in texture pixels',
            'strips': [{'id': k, 'member': r['member'], 'texture': r['texture'], 'offset': r['texture_offset'],
                        'jp': r['jp'], 'en': r['en'], 'original_fill_box': r['fill_box'],
                        'original_alpha_box': r['alpha_box'],
                        'english_fill_box': art['report']['captions'].get(k, {}).get('fill_box')}
                       for k, r in catalog['captions'].items()]})
    return targets, art['report']


# ------------------------------------------------- title-screen inventory ---
# LUACPK member 1: ScAnime_Z3TITLE_2D = 228 (title), _BUTTON_2D = 229,
# _HAGURUMA_2D = 230 (gears), _MENU_2D = 231. EFFPS3 member = constant + 1
# (member 0 is shared), as in Jigoku (ScAnime_Z3TITLE = 295 -> member 296).
TITLE_MEMBERS = {229: 'title (logo, Z, backgrounds)', 230: 'PRESS ANY BUTTON',
                 231: 'gears', 232: 'title menu + Library submenu'}
TITLE_TEXT = {   # texture -> what it shows (visual review of the contact sheet)
    (229, 1): ('Japanese', 'main wordmark 第3次スーパーロボット大戦 (864x304)'),
    (229, 2): ('Japanese', 'subtitle 天獄篇, one sprite (536x192)'),
    (229, 12): ('Japanese', 'subtitle 天獄篇 cut into three per-character cells (648x192)'),
    (230, 3): ('English', '"press any button" (568x168)'),
    (232, 7): ('English', 'Start / Load / Continue / Library / Download / PlayStation Store'),
    (232, 8): ('English', 'same menu, highlighted state'),
    (232, 22): ('English', 'same menu, third state'),
    (232, 11): ('Japanese', 'Library submenu: ロボット大図鑑 / キャラクター事典 / 用語事典 / サウンドセレクト / シナリオチャート'),
    (232, 13): ('Japanese', 'Library submenu, second state'),
    (232, 23): ('Japanese', 'Library submenu, third state'),
}


def sprite_rects(blob, base, textures):
    """{(tex, x, y, w, h): count} of the 16-byte sprite records
    (u16 z=0, x, y, w, h, flags 0x5000/0x5800, mode, texture) before the GTF."""
    sizes = {t['index']: (t['width'], t['height']) for t in gtf.textures(blob)}
    found = {}
    for p in range(0, base - 16, 2):
        z, x, y, w, h, flags, _mode, tex = struct.unpack_from('>8H', blob, p)
        if z == 0 and tex in textures and w and h and flags in (0x5000, 0x5800) \
                and x + w <= sizes[tex][0] and y + h <= sizes[tex][1]:
            found[(tex, x, y, w, h)] = found.get((tex, x, y, w, h), 0) + 1
    return {k: v for k, v in found.items() if v > 3}


def title_inventory(settings, apply=False):
    """Contact sheets + JSON of the EFFPS3 title-screen members (read only)."""
    from PIL import Image, ImageDraw
    from tools.pipeline import verified_source
    path = verified_source(settings, EFFPS3)
    out = {'schema': 1, 'archive': EFFPS3, 'source': 'LUACPK member 1 ScAnime_Z3TITLE_* constants + 1',
           'runtime_verified': False, 'members': {}}
    panels = []
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        for mid, role in TITLE_MEMBERS.items():
            entry = by_id[mid]
            blob = archive.read(entry)
            found = gtf.gtfs(blob)
            base = found[0][0]
            rows = []
            for t in gtf.textures(blob):
                if t['width'] <= 8:
                    continue
                lang, what = TITLE_TEXT.get((mid, t['index']), (None, None))
                rect = sprite_rects(blob, base, (t['index'],))
                rows.append({'texture': t['index'], 'size': [t['width'], t['height']],
                             'format': '0x%02x' % t['fmt'], 'offset': '0x%x' % t['offset'],
                             'text': lang, 'content': what,
                             'sprite_rects': [{'rect': list(k[1:]), 'records': v} for k, v in sorted(rect.items())]})
                if lang:
                    panels.append(('EFFPS3 m%d t%d %s' % (mid, t['index'], lang), gtf.decode(blob, t)))
            out['members'][str(mid)] = {'role': role, 'stored_sha256': sha256(
                archive.buf[entry['offset']:entry['offset'] + entry['size']]), 'gtf': '0x%x' % base,
                'textures': rows}
    width = 900
    scaled = []
    for label, rgba in panels:
        im = gtf.preview(rgba, (60, 0, 60))
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        scaled.append((label, im))
    sheet = Image.new('RGB', (width + 8, sum(im.height + 22 for _, im in scaled) + 8), (20, 20, 20))
    draw, y = ImageDraw.Draw(sheet), 4
    for label, im in scaled:
        draw.text((4, y), label, fill=(255, 255, 0))
        sheet.paste(im, (4, y + 16))
        y += im.height + 22
    targets = [PREVIEWS / 'title_screen_text.png', PREVIEWS / 'title_screen_inventory.json']
    if apply:
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        sheet.save(targets[0])
        write_json(targets[1], out)
    return targets, out


# ------------------------------------------------------------------- CLI ---
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['plan', 'catalog', 'preview', 'title-inventory'])
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    settings = _settings()
    if a.command == 'catalog':
        _catalog, summary = build_catalog(settings, a.apply)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print('wrote %s' % CATALOG if a.apply else 'DRY RUN: pass --apply to write %s' % CATALOG)
    elif a.command == 'preview':
        targets, report = preview(settings, a.apply)
        for k, info in report['captions'].items():
            print(k, json.dumps({f: info[f] for f in ('text', 'squeeze', 'shrink', 'fill_box')}))
        print('wrote %s' % ', '.join(map(str, targets)) if a.apply else 'DRY RUN: pass --apply to write previews')
    elif a.command == 'title-inventory':
        targets, out = title_inventory(settings, a.apply)
        for mid, m in out['members'].items():
            for t in m['textures']:
                if t['text']:
                    print('EFFPS3 m%s t%d %s: %s' % (mid, t['texture'], t['text'], t['content']))
        print('wrote %s' % ', '.join(map(str, targets)) if a.apply else 'DRY RUN: pass --apply to write')
    else:
        art = plan(settings)
        print(json.dumps({k: v for k, v in art['report'].items() if k != 'captions'}, indent=2))
        print('replaced members: %s (dry run; game_build writes the archive)' % sorted(art['members']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
