"""EFFPS3.CPK text art: map location captions, episode headings, the Berserk
cut-in and the title screen's Library submenu.

Dry run by default. Nothing here writes an archive: plan() returns the member
replacement set that game_build hands to ONE cpkpatch.build call for
/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK (docs/ART_EFFPS3.md).

Member layout (all 489 members): a little-endian effect header, an effect
script of 56-byte quad records, then ONE embedded GTF (tools/gtf.py decodes
every texture: 0x85 swizzled and 0xA5 linear ARGB). A quad record is

    -40 colour[4]  4 x RGBA vertex colours        (16 bytes)
    -24 8 bytes    zero
    -16 xy[8]      4 x (s16 x, s16 y) TL, TR, BL, BR in screen units
      0 header     u16 0, x, y, w, h (texel rect), flags, mode, texture

(offsets relative to the header; each animation keyframe repeats the record).
Records are matched by their exact header bytes, never by guessed offsets.

Families (work/translation/en/ui/effps3_art.json)
  location_captions  92 members, 512x160 linear texture 0. The caption quad
                     samples (0,104,392,24); the slanted bar (0,72,448,32)
                     and the checker strip (0,128,392,32) are baked to the
                     caption's width. All three are redrawn: English in the
                     original flat colour (218,232,253) with 16-level alpha,
                     bar and checker spliced to the new width (bar: inside its
                     run of identical columns; checker: whole 6-px periods).
  episode_headings   105 (one digit), 106 (two digits): texture 2 cells
                     第 / 話 -> one 360-px "Episode" cell (x 536..896); the 第 quads are
                     widened, the digit quads shifted right, the 話 quads
                     hidden (vertex colours zeroed, Jigoku's method).
                     107 (final episode): 最終話 -> "Final Episode" (512-px
                     cells, 終/話 quads hidden) and the baked 果てなき世界
                     title -> its eboot.json English. Crisp/glow encoding is
                     the TPACK title-card one (binary alpha, grey coverage).
  berserk            276 texture 0 rows 8..80: Jigoku 0.6.24's shipped art
                     (source member raw-identical to Jigoku member 307),
                     reused from a hash-guarded asset; the result must equal
                     Jigoku's shipped member byte for byte.
  library_labels     232 textures 11/13/23 (Library submenu, 3 states): the
                     five labels are rendered once as a core coverage and
                     styled per state with the glow model measured on the
                     originals (core over glow, glow = cap*min(1, gain*blur)).

    python -m tools.eff_art inventory [--apply]   contact sheets of every text-bearing texture
    python -m tools.eff_art plan                  dry run: render + verify, print the report
    python -m tools.eff_art preview  [--apply]    before/after sheets -> work/ui/textures/effps3/
    python -m tools.eff_art jigoku-berserk [--apply]   re-extract the Berserk asset (reads Jigoku)

Fonts are read (never written) from the RPCS3 dev_flash folder and
C:/Windows/Fonts. Requires numpy and Pillow (bundled Python).
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

ARCHIVE = '/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK'
ARCHIVE_SHA256 = '3f64c2deb9fe1218e2bd8024720f9c32e702526e50f4ae894889497d90729efa'
MEMBERS = 489
CATALOG = ROOT / 'work/translation/en/ui/effps3_art.json'
CACHE = ROOT / 'work/tengoku/cache/effps3_members'
PREVIEWS = ROOT / 'work/ui/textures/effps3'
ASSETS = ROOT / 'work/ui/textures/assets'
BERSERK_ASSET = ASSETS / 'eff_m276_t0_jigoku_0.6.24_berserk.png'
JIGOKU_ORIGINAL = Path('E:/Projects/SRW Z3/work/orig/EFFPS3.CPK')
JIGOKU_SHIPPED = Path('E:/Projects/SRW Z3/releases/0.6.24/EFFPS3.CPK')
WINDOWS_FONTS = Path('C:/Windows/Fonts')
FAMILIES = ('location_captions', 'episode_headings', 'berserk', 'library_labels')
RECORD = 56


def font_dir():
    from tools.ui_build import FACE
    return FACE.parent


def _font(name, size):
    from PIL import ImageFont
    path = Path(name) if Path(name).is_absolute() else font_dir() / name
    return ImageFont.truetype(str(path), size)


# ---------------------------------------------------------------- sources ---
def _settings():
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


def source_members(settings, ids, expected=None):
    """{id: decoded bytes} from the verified pristine EFFPS3 (mmap read).

    Decoded members are cached in work/tengoku/cache/effps3_members as
    NNN.bin + NNN.raw_sha256 (the stored-bytes hash); a cache entry is used
    only when that tag matches the archive and, when given, the decoded
    SHA-256 matches `expected` ({id: sha256})."""
    from tools.pipeline import verified_source
    expected = expected or {}
    path = verified_source(settings, ARCHIVE)
    out = {}
    with CPK(path) as archive:
        by_id = {e['id']: e for e in archive.files}
        for mid in ids:
            entry = by_id[mid]
            raw_sha = sha256(archive.buf[entry['offset']:entry['offset'] + entry['size']])
            cached, tag = CACHE / ('%03d.bin' % mid), CACHE / ('%03d.raw_sha256' % mid)
            if cached.exists() and tag.exists() and tag.read_text().strip() == raw_sha:
                data = cached.read_bytes()
                if mid not in expected or sha256(data) == expected[mid]:
                    out[mid] = data
                    continue
            data = archive.read(entry)
            CACHE.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(data)
            tag.write_text(raw_sha + '\n')
            out[mid] = data
    for mid, want in expected.items():
        if mid in out and sha256(out[mid]) != want:
            raise ValueError('EFFPS3 member %d is not the guarded source' % mid)
    return out


# ----------------------------------------------------------- quad records ---
def gtf_base(blob):
    found = gtf.gtfs(blob)
    if len(found) != 1:
        raise ValueError('expected exactly one embedded GTF, found %d' % len(found))
    return found[0][0]


def quad_key(texture, rect, flags=0x5000, mode=0x301):
    x, y, w, h = rect
    return struct.pack('>8H', 0, x, y, w, h, flags, mode, texture)


def find_quads(blob, key, limit=None):
    """Header offsets of every record whose header equals `key` (script only)."""
    limit = gtf_base(blob) if limit is None else limit
    out, p = [], blob.find(key, RECORD - 16, limit)
    while p >= 0:
        if p % 2 == 0:
            out.append(p)
        p = blob.find(key, p + 2, limit)
    return out


def quad_xy(blob, p):
    return list(struct.unpack_from('>8h', blob, p - 16))


def rect_records(blob, texture, rect):
    """All records (any flags/mode) sampling `rect` of `texture`."""
    limit = gtf_base(blob)
    head = struct.pack('>5H', 0, *rect)
    out, p = [], blob.find(head, RECORD - 16, limit)
    while p >= 0:
        if p % 2 == 0 and p + 16 <= limit and struct.unpack_from('>H', blob, p + 14)[0] == texture:
            out.append(p)
        p = blob.find(head, p + 2, limit)
    return out


# ------------------------------------------------------------- catalogs ---
def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('archive') != ARCHIVE or not isinstance(data.get('entries'), list):
        raise ValueError('effps3_art.json: expected schema 1 with "entries" for %s' % ARCHIVE)
    seen = {}
    for e in data['entries']:
        where = 'effps3_art.json %s' % e.get('id')
        if e.get('family') not in FAMILIES + ('other',):
            raise ValueError(where + ': unknown family')
        if e.get('status') not in ('translate', 'keep', 'pending'):
            raise ValueError(where + ': status must be translate, keep or pending')
        if not e.get('jp') or not e.get('members'):
            raise ValueError(where + ': needs jp and members')
        if e['status'] == 'translate':
            en = e.get('en')
            texts = en if isinstance(en, list) else [en]
            if not all(isinstance(t, str) and t.strip() and t.isascii() and '\n' not in t for t in texts):
                raise ValueError(where + ': English must be one ASCII line per label')
            if not e.get('source'):
                raise ValueError(where + ': record where the English comes from')
            for m in e['members']:
                key = (m, e.get('texture'))
                if key in seen:
                    raise ValueError(where + ': member %d texture %s also in %s' % (m, e.get('texture'), seen[key]))
                seen[key] = e['id']
            if set(map(str, e['members'])) != set(e.get('member_sha256', {})):
                raise ValueError(where + ': member_sha256 must guard every member')
    return data


def _english(text):
    """Expand glossary $$tokens$$ (none are used today; kept for parity)."""
    if '$$' not in text:
        return text
    from tools import eboot_text
    from tools.library_build import expand
    return expand(text, eboot_text.resolver())


# --------------------------------------------------------- coverage text ---
SUPERSAMPLE = 4


def coverage(text, face, cap, track=0.0, squeeze=1.0):
    """(float coverage array 0..1, info) of `text`: cap height `cap` px,
    `track` px extra advance per letter (0 = the font's own spacing and
    kerning), horizontal scale `squeeze`. Row info['cap_line'] of the array
    is the top of an 'H'; ascenders may rise above it."""
    from PIL import Image, ImageDraw
    probe = _font(face, 400)
    l, t, r, b = probe.getbbox('H')
    size = 400.0 * cap / (b - t)
    font = _font(face, int(round(size * SUPERSAMPLE)))
    cap_top = font.getbbox('H')[1]
    head = int(np.ceil(size * 0.4))
    width = int(font.getlength(text) + track * SUPERSAMPLE * len(text) + size * SUPERSAMPLE)
    height = int((head + size * 1.4) * SUPERSAMPLE)
    image = Image.new('L', (width, height))
    draw = ImageDraw.Draw(image)
    x, y = 4 * SUPERSAMPLE, -cap_top + head * SUPERSAMPLE
    if not track:
        draw.text((x, y), text, font=font, fill=255)
    else:
        for ch in text:
            draw.text((x, y), ch, font=font, fill=255)
            x += font.getlength(ch) + track * SUPERSAMPLE
    box = image.getbbox()
    if box is None:
        raise ValueError('text renders no ink: %r' % text)
    if box[1] == 0 or box[3] == height:
        raise ValueError('text ink clipped while rendering: %r' % text)
    image = image.crop((box[0], 0, box[2], image.height))
    w = max(1, int(round(image.width * squeeze / SUPERSAMPLE)))
    h = int(round(image.height / SUPERSAMPLE))
    image = image.resize((w, h), Image.BOX)
    a = np.asarray(image, dtype=np.float64) / 255.0
    rows = np.nonzero(a.max(axis=1) > 0)[0]
    a = a[:rows[-1] + 1]
    return a, {'font_px': round(size, 2), 'cap_line': head, 'ink_rows': [int(rows[0]), int(rows[-1])],
               'width': w, 'track': track, 'squeeze': round(squeeze, 3)}


def fitted(text, face, cap, max_width, track=0.0, min_track=0.0, min_squeeze=0.8, min_scale=1.0):
    """Coverage of `text` at most `max_width` px wide: tracking is reduced
    first (down to min_track), then the letters are condensed horizontally
    (down to min_squeeze), then (only when min_scale < 1) the whole word is
    made smaller, down to min_scale x cap; anything wider raises. The info
    records track, squeeze and scale for review."""
    tracks = [track] if track <= min_track else list(np.arange(track, min_track - 1e-9, -0.5))
    for tr in tracks:
        a, info = coverage(text, face, cap, tr)
        if info['width'] <= max_width:
            info['scale'] = 1.0
            return a, info
    squeeze = max_width / float(info['width'])
    scale = 1.0
    if squeeze < min_squeeze:
        scale = squeeze / min_squeeze
        if scale < min_scale:
            raise ValueError('%r does not fit %d px (needs squeeze %.2f < %.2f)'
                             % (text, max_width, squeeze, min_squeeze))
        squeeze = min_squeeze
    a, info = coverage(text, face, cap * scale, min_track, squeeze)
    while info['width'] > max_width:
        squeeze -= 0.005
        a, info = coverage(text, face, cap * scale, min_track, squeeze)
    info['scale'] = round(scale, 3)
    return a, info


def _place(canvas_hw, a, x0, y0):
    """`a` pasted at (x0, y0) on a zero canvas; empty margins of `a` may
    hang outside the canvas, ink may not."""
    h, w = canvas_hw
    rows = np.nonzero(a.max(axis=1) > 0)[0]
    cols = np.nonzero(a.max(axis=0) > 0)[0]
    a = a[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    x0, y0 = x0 + int(cols[0]), y0 + int(rows[0])
    ah, aw = a.shape
    if x0 < 0 or y0 < 0 or x0 + aw > w or y0 + ah > h:
        raise ValueError('text ink %s outside %dx%d' % ((x0, y0, aw, ah), w, h))
    out = np.zeros((h, w))
    out[y0:y0 + ah, x0:x0 + aw] = a
    return out


def _blur(a, sigma):
    from tools.texture_art import _blur as blur
    return blur(a, sigma)


# ------------------------------------------------------ location captions ---
CAPTION_SIZE = (512, 160)
BAR_RECT = (0, 72, 448, 32)
TEXT_RECT = (0, 104, 392, 24)
CHECKER_RECT = (0, 128, 392, 32)
CAPTION_REGION = (0, 72, 448, 88)        # everything the captions redraw
CAPTION_STYLE = {
    'face': 'SCE-PS3-RD-B-LATIN.TTF',     # Rodin Bold: the Latin partner of the gothic captions
    'fill': (218, 232, 253),              # measured: constant RGB on every caption pixel
    'cap': 15, 'cap_top': 4,              # Japanese ink spans rows 3..21 of the 24-px strip
    'left': 7, 'right': 384,              # measured ink anchors (left / right aligned)
    'max_width': 350, 'min_squeeze': 0.8,
    'checker_pad': 33, 'checker_min': 119,  # checker = ink + 33 px, never under 119 px
}


def _caption_texture(blob):
    tex = gtf.textures(blob)
    t = tex[0]
    if (t['fmt'], t['width'], t['height']) != (gtf.LINEAR_ARGB,) + CAPTION_SIZE:
        raise ValueError('caption member texture 0 is not 512x160 linear ARGB')
    return t


def caption_audit(blob):
    """Record counts proving the caption, bar and checker quads sample the
    rectangles this module redraws."""
    counts = {name: len(rect_records(blob, 0x100, rect))
              for name, rect in (('text', TEXT_RECT), ('bar', BAR_RECT), ('checker', CHECKER_RECT))}
    if not all(counts.values()):
        raise ValueError('caption quads not found: %s' % counts)
    return counts


def _extent(alpha):
    cols = np.nonzero(alpha.max(axis=0) > 8)[0]
    return (int(cols[0]), int(cols[-1])) if cols.size else None


def caption_layout(rgba):
    """Measured geometry of an original caption."""
    x, y, w, h = TEXT_RECT
    text = _extent(rgba[y:y + h, x:x + w, 3])
    x, y, w, h = CHECKER_RECT
    checker = _extent(rgba[y:y + h, x:x + w, 3])
    x, y, w, h = BAR_RECT
    bar = _extent(rgba[y:y + h, x:x + w, 3])
    if not (text and checker and bar):
        raise ValueError('caption without text, checker or bar')
    return {'align': 'right' if text[0] > 20 else 'left', 'text': text, 'checker': checker, 'bar': bar}


def _runs(flags):
    best, start = (0, 0), None
    for i, v in enumerate(list(flags) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    return best


def splice_bar(bar, delta):
    """Bar strip lengthened (delta > 0) or shortened by |delta| columns,
    inside its longest run of identical inked columns (the plain line), so
    the slanted start and the gradient/chevron end cap keep their pixels."""
    if delta == 0:
        return bar.copy()
    ink = bar[..., 3].max(axis=0) > 0
    flat = [bool(ink[i] and ink[i + 1] and np.array_equal(bar[:, i], bar[:, i + 1]))
            for i in range(bar.shape[1] - 1)]
    lo, hi = _runs(flat)
    if hi - lo < 4:
        raise ValueError('bar has no flat line to splice')
    at = (lo + hi) // 2
    if delta > 0:
        out = np.concatenate([bar[:, :at], np.repeat(bar[:, at:at + 1], delta, axis=1), bar[:, at:]], axis=1)
    else:
        if -delta > hi - lo - 2:
            raise ValueError('bar cannot shrink by %d (flat run %d)' % (-delta, hi - lo))
        cut = max(lo + 1, at - (-delta) // 2)
        out = np.concatenate([bar[:, :cut], bar[:, cut - delta:]], axis=1)
    return _fit_width(out, bar.shape[1], bar[:, -1:])


def splice_checker(checker, delta, period=6):
    """Checker strip grown/shrunk by `delta` (a multiple of the 6-px period)
    inside its periodic plateau, so the 3x3 checks stay continuous."""
    if delta % period:
        raise ValueError('checker delta must be a multiple of %d' % period)
    if delta == 0:
        return checker.copy()
    per = [np.array_equal(checker[:, i], checker[:, i + period]) for i in range(checker.shape[1] - period)]
    ink = checker[..., 3].max(axis=0) > 0
    lo, hi = _runs([per[i] and ink[i] and ink[i + period] for i in range(len(per))])
    if hi - lo < 2 * period:
        raise ValueError('checker has no periodic plateau')
    at = lo + period
    if delta > 0:
        reps = np.concatenate([checker[:, at:at + period]] * (delta // period), axis=1)
        out = np.concatenate([checker[:, :at], reps, checker[:, at:]], axis=1)
    else:
        if -delta > hi - at:
            raise ValueError('checker cannot shrink by %d' % -delta)
        out = np.concatenate([checker[:, :at], checker[:, at - delta:]], axis=1)
    return _fit_width(out, checker.shape[1], checker[:, -1:])


def _fit_width(strip, width, pad_col):
    if strip.shape[1] >= width:
        tail = strip[:, width:]
        if tail[..., 3].any():
            raise ValueError('spliced strip overflows its rectangle')
        return strip[:, :width].copy()
    return np.concatenate([strip, np.repeat(pad_col, width - strip.shape[1], axis=1)], axis=1)


def caption_text(en, align, style=CAPTION_STYLE):
    """(RGBA (24, 392, 4), info) of one caption in the original encoding:
    constant RGB, alpha = coverage quantised to 16 levels (n * 17)."""
    a, info = fitted(en, style['face'], style['cap'], style['max_width'], min_squeeze=style['min_squeeze'])
    x0 = style['left'] if align == 'left' else style['right'] + 1 - a.shape[1]
    y0 = style['cap_top'] - info['cap_line']
    h = a.shape[0]
    rows = np.nonzero(a.max(axis=1) > 0)[0]
    a = a[:rows[-1] + 1]
    cov = _place((TEXT_RECT[3], TEXT_RECT[2]), a, x0, y0)
    alpha = (np.clip(np.rint(cov * 15), 0, 15) * 17).astype(np.uint8)
    rgba = np.zeros(cov.shape + (4,), np.uint8)
    rgba[..., :3] = style['fill']
    rgba[..., 3] = alpha
    info.update({'ink': _extent(alpha), 'align': align, 'height_used': h})
    return rgba, info


def caption_pixels(source_rgba, en, style=CAPTION_STYLE):
    """(region RGBA for CAPTION_REGION, info) for one caption member."""
    lay = caption_layout(source_rgba)
    x, y, w, h = CAPTION_REGION
    region = source_rgba[y:y + h, x:x + w].copy()
    text, info = caption_text(en, lay['align'], style)
    ink0, ink1 = info['ink']
    c0, c1 = lay['checker']
    if lay['align'] == 'left':
        want = max(style['checker_min'], ink1 + style['checker_pad'])
        delta = want - c1
    else:
        want = min(CHECKER_RECT[2] - 1 - style['checker_min'], ink0 - style['checker_pad'])
        delta = c0 - want
    delta = int(round(delta / 6.0)) * 6
    cx, cy, cw, ch = CHECKER_RECT
    checker = region[cy - y:cy - y + ch, cx:cx + cw]
    if lay['align'] == 'right':
        checker = splice_checker(checker[:, ::-1], delta)[:, ::-1]
    else:
        checker = splice_checker(checker, delta)
    bx, by, bw, bh = BAR_RECT
    bar = splice_bar(region[by - y:by - y + bh, bx:bx + bw], delta)
    tx, ty, tw, th = TEXT_RECT
    region[by - y:by - y + bh, bx:bx + bw] = bar
    region[ty - y:ty - y + th, tx:tx + tw] = text
    region[cy - y:cy - y + ch, cx:cx + cw] = checker
    new = {'checker': _extent(checker[..., 3]), 'bar': _extent(bar[..., 3])}
    if lay['align'] == 'left' and new['checker'][1] < ink1 + 8:
        raise ValueError('checker shorter than the caption: %r' % en)
    if lay['align'] == 'right' and new['checker'][0] > ink0 - 8:
        raise ValueError('checker shorter than the caption: %r' % en)
    info.update({'source': lay, 'checker': new['checker'], 'bar_end': new['bar'][1], 'delta': delta})
    return region, info


def caption_member(blob, en, style=CAPTION_STYLE):
    """(new member bytes, {texture key: RGBA}, info)."""
    tex = _caption_texture(blob)
    counts = caption_audit(blob)
    rgba = gtf.decode(blob, tex)
    region, info = caption_pixels(rgba, en, style)
    full = rgba.copy()
    x, y, w, h = CAPTION_REGION
    full[y:y + h, x:x + w] = region
    info['records'] = counts
    return gtf.replace(blob, tex, full), {tex.key: full}, {}, info


# ------------------------------------------------------- episode headings ---
def _quantisers():
    from tools.texture_art import CRISP_Q, GLOW_Q
    return CRISP_Q, GLOW_Q


HEADING_STYLE = {
    'face': 'SCE-PS3-MT-R-LATIN.TTF',   # same Matisse serif as the TPACK title cards
    'cap': 72,                          # "Prologue" in the same texture: P stem rows 12..83
    'cell_top': 12,                     # cap line 12 px into the 112-px cell (descender ends at 102)
    'left': 8, 'margin': 8, 'min_squeeze': 0.85, 'min_scale': 0.85,
    'glow_sigma': 2.0, 'glow_gain': 1.5, 'glow_gamma': 0.4,   # fitted on 第 / Prologue (mean error ~9/255)
}
TITLE_STYLE = {'face': 'SCE-PS3-MT-R-LATIN.TTF', 'extent': 108, 'max_width': 1000,
               'min_squeeze': 0.85, 'center': (517.0, 66.0),
               'glow_sigma': 2.0, 'glow_gain': 1.25, 'glow_gamma': 0.4}

# member: digit textures, expected record counts (crisp, glow)
HEADINGS = {
    105: {'digits': (4,), 'counts': {'dai': (775, 1549), 'wa': (775, 1549), 4: (775, 1549)}},
    106: {'digits': (5, 4), 'counts': {'dai': (775, 1549), 'wa': (775, 1549), 4: (775, 1550), 5: (775, 1550)}},
}
EPISODE_TEXTURE = 2
DAI, DAI_GLOW, WA, WA_GLOW = (576, 88, 144, 112), (576, 200, 144, 112), (720, 88, 144, 112), (720, 200, 144, 112)
EPISODE_CELL, EPISODE_GLOW = (536, 88, 360, 112), (536, 200, 360, 112)   # x 424..896 is empty below row 88
DIGIT, DIGIT_GLOW = (0, 0, 96, 112), (0, 112, 96, 112)
FINAL = 107
FINAL_CELLS = {'crisp': [(0, 88, 144, 112), (144, 88, 144, 112), (288, 88, 144, 112)],
               'glow': [(432, 88, 144, 112), (576, 88, 144, 112), (720, 88, 144, 112)]}
FINAL_CELL, FINAL_GLOW = (0, 88, 512, 112), (512, 88, 512, 112)
FINAL_TITLE, FINAL_TITLE_GLOW = (0, 200, 1024, 128), (0, 328, 1024, 128)
FINAL_COUNT = 721


def heading_cell(text, cell_w, style=HEADING_STYLE):
    """(crisp grey (112, w), glow grey (112, w), info) for a heading word,
    left aligned like "Prologue"."""
    crisp_q, glow_q = _quantisers()
    a, info = fitted(text, style['face'], style['cap'], cell_w - style['left'] - style['margin'],
                     min_squeeze=style['min_squeeze'], min_scale=style['min_scale'])
    cov = _place((112, cell_w), a * 255.0, style['left'], style['cell_top'] - info['cap_line'])
    if (cov[105:] > 0).any():
        raise ValueError('heading descends past the cell: %r' % text)
    halo = np.minimum(255.0, style['glow_gain'] * _blur(cov, style['glow_sigma']))
    halo = 255.0 * (halo / 255.0) ** style['glow_gamma']
    glow = 255.0 - (255.0 - cov) * (255.0 - halo) / 255.0
    return crisp_q(cov), glow_q(glow), info


def title_cell(text, style=TITLE_STYLE):
    """(crisp (128,1024), glow (128,1024), info) for the 107 title, sized
    like the TPACK title cards (ascender-to-descender 108 px)."""
    crisp_q, glow_q = _quantisers()
    probe = _font(style['face'], 400)
    top, bottom = probe.getbbox('Hbdfhkl')[1], probe.getbbox('gjpqy')[3]
    cap_box = probe.getbbox('H')
    cap = style['extent'] * (cap_box[3] - cap_box[1]) / float(bottom - top)
    a, info = fitted(text, style['face'], cap, style['max_width'], min_squeeze=style['min_squeeze'], min_scale=0.8)
    rows = np.nonzero(a.max(axis=1) > 0)[0]
    a = a[rows[0]:rows[-1] + 1]
    cx, cy = style['center']                   # ink centre of the Japanese title
    x0 = int(round(cx - (a.shape[1] - 1) / 2.0))
    y0 = int(round(cy - (a.shape[0] - 1) / 2.0))
    cov = _place((128, 1024), a * 255.0, x0, y0)
    halo = np.minimum(255.0, style['glow_gain'] * _blur(cov, style['glow_sigma']))
    halo = 255.0 * (halo / 255.0) ** style['glow_gamma']
    glow = 255.0 - (255.0 - cov) * (255.0 - halo) / 255.0
    info['ink_box'] = [x0, y0, a.shape[1], a.shape[0]]
    return crisp_q(cov), glow_q(glow), info


def _grey_rgba(grey):
    rgba = np.zeros(grey.shape + (4,), np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = grey
    rgba[..., 3] = np.where(grey > 0, 255, 0)
    return rgba


def _paste(full, rect, rgba):
    x, y, w, h = rect
    full[y:y + h, x:x + w] = rgba


def _set_header(edits, blob, p, x=None, w=None):
    head = list(struct.unpack_from('>8H', blob, p))
    if x is not None:
        head[1] = x
    if w is not None:
        head[3] = w
    edits[p] = struct.pack('>8H', *head)


def _widen(edits, blob, positions, k, x=None, w=None):
    """Scale every keyframe's right edge by k about its own left edge (this
    keeps each keyframe's zoom anchor); optionally change the texel rect."""
    for p in positions:
        xy = quad_xy(blob, p)
        xy[2] = xy[0] + int(round((xy[2] - xy[0]) * k))
        xy[6] = xy[4] + int(round((xy[6] - xy[4]) * k))
        edits[p - 16] = struct.pack('>8h', *xy)
        _set_header(edits, blob, p, x, w)


def _shift(edits, blob, positions, d, rest_width):
    """Move every keyframe right by d screen units, scaled by that
    keyframe's zoom (its width / the resting width)."""
    for p in positions:
        xy = quad_xy(blob, p)
        f = (xy[2] - xy[0]) / float(rest_width)
        s = int(round(d * f))
        for i in (0, 2, 4, 6):
            xy[i] += s
        edits[p - 16] = struct.pack('>8h', *xy)


def _hide(edits, positions):
    for p in positions:
        edits[p - 40] = bytes(16)


def _expect(blob, texture, rect, count, mode=0x301):
    positions = find_quads(blob, quad_key(texture, rect, mode=mode))
    if len(positions) != count or len(rect_records(blob, texture, rect)) != count:
        raise ValueError('expected %d records for texture %d rect %s, found %d'
                         % (count, texture, rect, len(positions)))
    return positions


def _rest_width(blob, positions):
    widths = {quad_xy(blob, p)[2] - quad_xy(blob, p)[0] for p in positions}
    if len(widths) != 1:
        raise ValueError('crisp quad changes size during the animation: %s' % sorted(widths))
    return widths.pop()


def _episode_texture(blob):
    tex = gtf.textures(blob)
    t = tex[EPISODE_TEXTURE]
    if t['fmt'] != gtf.LINEAR_ARGB or (t['width'], t['height']) not in ((896, 312), (1024, 456)):
        raise ValueError('episode heading texture 2 layout changed')
    return t


def episode_member(blob, member, word, style=HEADING_STYLE):
    """第N話 -> "<word> N" for members 105/106."""
    spec = HEADINGS[member]
    tex = _episode_texture(blob)
    if (tex['width'], tex['height']) != (896, 312):
        raise ValueError('member %d texture 2 is not the 896x312 heading atlas' % member)
    counts = spec['counts']
    dai = _expect(blob, EPISODE_TEXTURE, DAI, counts['dai'][0])
    dai_glow = _expect(blob, EPISODE_TEXTURE, DAI_GLOW, counts['dai'][1])
    wa = _expect(blob, EPISODE_TEXTURE, WA, counts['wa'][0])
    wa_glow = _expect(blob, EPISODE_TEXTURE, WA_GLOW, counts['wa'][1])
    digits = {d: (_expect(blob, d, DIGIT, counts[d][0]), _expect(blob, d, DIGIT_GLOW, counts[d][1]))
              for d in spec['digits']}
    rest = _rest_width(blob, dai)
    k = EPISODE_CELL[2] / float(DAI[2])
    d = int(round(rest * (k - 1)))
    edits = {}
    _widen(edits, blob, dai, k, x=EPISODE_CELL[0], w=EPISODE_CELL[2])
    _widen(edits, blob, dai_glow, k, x=EPISODE_GLOW[0], w=EPISODE_GLOW[2])
    for digit, (crisp, glow) in digits.items():
        width = _rest_width(blob, crisp)
        _shift(edits, blob, crisp, d, width)
        _shift(edits, blob, glow, d, width)
    _hide(edits, wa + wa_glow)
    crisp_grey, glow_grey, info = heading_cell(word, EPISODE_CELL[2], style)
    full = gtf.decode(blob, tex)
    _paste(full, EPISODE_CELL, _grey_rgba(crisp_grey))
    _paste(full, EPISODE_GLOW, _grey_rgba(glow_grey))
    out = bytearray(gtf.replace(blob, tex, full))
    for p, data in edits.items():
        out[p:p + len(data)] = data
    info.update({'shift_units': d, 'widen': round(k, 4), 'records_edited': len(edits),
                 'hidden_records': len(wa) + len(wa_glow)})
    return bytes(out), {tex.key: full}, edits, info


def final_member(blob, word, title, style=HEADING_STYLE, title_style=TITLE_STYLE):
    """最終話 -> word, 果てなき世界 -> title (member 107)."""
    tex = _episode_texture(blob)
    if (tex['width'], tex['height']) != (1024, 456):
        raise ValueError('member 107 texture 2 is not the 1024x456 final atlas')
    crisp = [_expect(blob, EPISODE_TEXTURE, r, FINAL_COUNT) for r in FINAL_CELLS['crisp']]
    glow = [_expect(blob, EPISODE_TEXTURE, r, FINAL_COUNT) for r in FINAL_CELLS['glow']]
    for rect, count in ((FINAL_TITLE, FINAL_COUNT), (FINAL_TITLE_GLOW, FINAL_COUNT)):
        _expect(blob, EPISODE_TEXTURE, rect, count)
    k = FINAL_CELL[2] / float(FINAL_CELLS['crisp'][0][2])
    edits = {}
    _widen(edits, blob, crisp[0], k, w=FINAL_CELL[2])
    _widen(edits, blob, glow[0], k, x=FINAL_GLOW[0], w=FINAL_GLOW[2])
    _hide(edits, crisp[1] + crisp[2] + glow[1] + glow[2])
    c, g, info = heading_cell(word, FINAL_CELL[2], style)
    tc, tg, tinfo = title_cell(title, title_style)
    full = gtf.decode(blob, tex)
    _paste(full, FINAL_CELL, _grey_rgba(c))
    _paste(full, FINAL_GLOW, _grey_rgba(g))
    _paste(full, FINAL_TITLE, _grey_rgba(tc))
    _paste(full, FINAL_TITLE_GLOW, _grey_rgba(tg))
    out = bytearray(gtf.replace(blob, tex, full))
    for p, data in edits.items():
        out[p:p + len(data)] = data
    info.update({'widen': round(k, 4), 'records_edited': len(edits), 'title': tinfo,
                 'hidden_records': sum(len(x) for x in crisp[1:] + glow[1:])})
    return bytes(out), {tex.key: full}, edits, info


# ---------------------------------------------------------------- berserk ---
BERSERK_MEMBER, JIGOKU_BERSERK_MEMBER = 276, 307
BERSERK_SOURCE = '1885d0c317b381057a4bbe46e572ef251d18324b3138eef8b612da4c8204bdea'
BERSERK_SHIPPED = '517e4726087df8280ec4302248ba65af5c83bc039f4c951ae22a296de376b993'
BERSERK_RECT = (0, 8, 512, 72)          # Jigoku: solid lettering y 8..39, outline y 40..79


def _berserk_texture(blob):
    t = gtf.textures(blob)[0]
    if (t['fmt'], t['width'], t['height'], t['gtf']) != (gtf.SWIZZLED_ARGB, 512, 128, 0x7dd80):
        raise ValueError('Berserk texture 0 layout changed')
    return t


def berserk_asset():
    from PIL import Image
    meta = json.loads(BERSERK_ASSET.with_suffix('.json').read_text(encoding='utf-8'))
    rgba = gtf.from_image(Image.open(BERSERK_ASSET))
    if rgba.shape != (BERSERK_RECT[3], BERSERK_RECT[2], 4) or sha256(rgba.tobytes()) != meta['asset_rgba_sha256']:
        raise ValueError('Berserk asset does not match its recorded hash')
    if meta['source_member_sha256'] != BERSERK_SOURCE or meta['shipped_member_sha256'] != BERSERK_SHIPPED:
        raise ValueError('Berserk asset sidecar names other members')
    return rgba, meta


def berserk_member(blob):
    if sha256(blob) != BERSERK_SOURCE:
        raise ValueError('member 276 is not the Jigoku-identical Berserk source')
    tex = _berserk_texture(blob)
    rgba, meta = berserk_asset()
    out = gtf.paint(blob, tex, BERSERK_RECT, rgba)
    if sha256(out) != BERSERK_SHIPPED:
        raise ValueError('reused Berserk art does not reproduce Jigoku 0.6.24 member 307')
    full = gtf.decode(out, tex)
    return out, {tex.key: full}, {}, {'reused': 'Jigoku 0.6.24 EFFPS3 member 307 (byte-identical result)',
                                      'english': meta['english']}


def extract_jigoku_berserk(apply=False):
    """Re-create the Berserk asset from Jigoku's archives (read only)."""
    rows = {}
    for label, path in (('original', JIGOKU_ORIGINAL), ('shipped', JIGOKU_SHIPPED)):
        with CPK(str(path)) as archive:
            entry = next(e for e in archive.files if e['id'] == JIGOKU_BERSERK_MEMBER)
            rows[label] = archive.read(entry)
    if sha256(rows['original']) != BERSERK_SOURCE or sha256(rows['shipped']) != BERSERK_SHIPPED:
        raise ValueError('Jigoku member 307 is not the recorded original/shipped pair')
    tex = _berserk_texture(rows['original'])
    before, after = gtf.decode(rows['original'], tex), gtf.decode(rows['shipped'], tex)
    x, y, w, h = BERSERK_RECT
    outside = np.ones(before.shape[:2], bool)
    outside[y:y + h, x:x + w] = False
    if (before[outside] != after[outside]).any():
        raise ValueError('Jigoku changed Berserk pixels outside rows 8..80')
    o, n = tex['offset'], tex['size']
    if rows['original'][:o] != rows['shipped'][:o] or rows['original'][o + n:] != rows['shipped'][o + n:]:
        raise ValueError('Jigoku changed Berserk bytes outside texture 0')
    asset = after[y:y + h, x:x + w].copy()
    meta = {'source': str(JIGOKU_SHIPPED), 'jigoku_member': JIGOKU_BERSERK_MEMBER, 'tengoku_member': BERSERK_MEMBER,
            'texture': 0, 'rect': list(BERSERK_RECT), 'english': 'BERSERK',
            'source_member_sha256': BERSERK_SOURCE, 'shipped_member_sha256': BERSERK_SHIPPED,
            'asset_rgba_sha256': sha256(asset.tobytes()),
            'note': 'Jigoku tools/berserk_banner.py: solid + outline lettering of the canonical ability '
                    'label "Berserk" (eboot.json 暴走), upper case; every other byte unchanged.'}
    print('Jigoku Berserk: source identical to Tengoku member 276; shipped sha %s' % BERSERK_SHIPPED[:16])
    if apply:
        ASSETS.mkdir(parents=True, exist_ok=True)
        gtf.to_image(asset).save(BERSERK_ASSET)
        write_json(BERSERK_ASSET.with_suffix('.json'), meta)
        berserk_asset()
        print('wrote %s' % BERSERK_ASSET)
    return meta


# --------------------------------------------------------- library labels ---
LIBRARY_MEMBER = 232
LIBRARY_TEXTURES = (11, 13, 23)
LIBRARY_SIZE = (352, 304)
# Sprite rectangles per state (texture: five rows), from the script records.
LIBRARY_RECTS = {
    11: [(0, 0, 312, 64), (0, 64, 351, 56), (0, 120, 192, 64), (0, 184, 344, 56), (0, 248, 344, 48)],
    13: [(0, 7, 311, 48), (0, 63, 350, 55), (0, 118, 191, 65), (0, 183, 343, 56), (0, 247, 343, 48)],
    23: [(0, 7, 311, 48), (0, 63, 350, 56), (0, 119, 183, 64), (0, 183, 343, 56), (0, 247, 343, 48)],
}
# Core colour and glow colour per state; glow model fitted on the originals
# (all three states share one core coverage and glow = cap*min(1, gain*blur(core, sigma))).
LIBRARY_STATES = {11: ((255, 255, 255), (0, 133, 119)), 13: ((0, 0, 0), (255, 255, 255)),
                  23: ((255, 255, 255), (255, 255, 255))}
# Ink centre (texture y) of each Japanese label, measured on texture 13.
LIBRARY_CENTERS = (30.5, 90.5, 150.5, 211.0, 271.0)
LIBRARY_STYLE = {
    'face': str(WINDOWS_FONTS / 'timesbd.ttf'),  # closest match to the game's own English buttons (t7)
    'cap': 26, 'track': 6.5, 'min_track': 0.0,   # game English buttons (texture 7): cap 27, track ~6.5
    'left': 14, 'right_margin': 13, 'min_squeeze': 0.78,
    'glow_sigma': 7.0, 'glow_gain': 3.0, 'glow_cap': 0.78,
}


def _library_textures(blob):
    tex = gtf.textures(blob)
    out = {}
    for i in LIBRARY_TEXTURES:
        t = tex[i]
        if (t['fmt'], t['width'], t['height']) != (gtf.LINEAR_ARGB,) + LIBRARY_SIZE:
            raise ValueError('Library texture %d layout changed' % i)
        out[i] = t
    return out


def library_audit(blob):
    counts = {}
    for i, rects in LIBRARY_RECTS.items():
        for r in rects:
            n = len(rect_records(blob, i, r))
            if not n:
                raise ValueError('no records sample texture %d rect %s' % (i, r))
            counts['%d:%s' % (i, ','.join(map(str, r)))] = n
    return counts


def _library_boxes():
    """Per row: (top, bottom, right) of the intersection of the three
    states' sprite rectangles."""
    out = []
    for row in range(5):
        rects = [LIBRARY_RECTS[t][row] for t in LIBRARY_TEXTURES]
        out.append((max(r[1] for r in rects), min(r[1] + r[3] for r in rects), min(r[0] + r[2] for r in rects)))
    return out


def library_core(labels, style=LIBRARY_STYLE):
    """Core coverage (304, 352) for the five labels.

    One letter spacing for all five (the widest that lets every label fit,
    never more than the game's own English buttons use); a label that still
    does not fit is condensed. Each label ends 13 px inside its sprite
    rectangle like the Japanese (the rows are right-aligned on screen) and
    its cap height is centred on the Japanese ink centre of its row."""
    boxes = _library_boxes()
    widths = [x1 - style['left'] - style['right_margin'] for _y0, _y1, x1 in boxes]
    track = style['track']
    while track > style['min_track'] and any(
            coverage(t, style['face'], style['cap'], track)[1]['width'] > w for t, w in zip(labels, widths)):
        track = round(track - 0.5, 2)
    core = np.zeros(LIBRARY_SIZE[::-1])
    infos = []
    for row, (text, width) in enumerate(zip(labels, widths)):
        y0, y1, x1 = boxes[row]
        a, info = fitted(text, style['face'], style['cap'], width, track=track, min_track=track,
                         min_squeeze=style['min_squeeze'])
        top = int(round(LIBRARY_CENTERS[row] - style['cap'] / 2.0)) - info['cap_line']
        # the quads are right-aligned on screen (every row ends at x=-165), so
        # the ink keeps the Japanese right margin, not its left one
        placed = _place(core.shape, a, x1 - style['right_margin'] - a.shape[1], top)
        ink = np.nonzero(placed.max(axis=1) > 0)[0]
        if ink[0] < y0 + 2 or ink[-1] > y1 - 3:
            raise ValueError('library label %r leaves its sprite rows %d..%d' % (text, y0, y1))
        core = np.maximum(core, placed)
        info.update({'text': text, 'row_box': [0, y0, x1, y1 - y0], 'ink_rows': [int(ink[0]), int(ink[-1])]})
        infos.append(info)
    return core, infos


def library_state(core, state, style=LIBRARY_STYLE):
    """RGBA of one state: core colour over glow colour (straight alpha)."""
    core_rgb, glow_rgb = (np.array(c, np.float64) for c in LIBRARY_STATES[state])
    glow = style['glow_cap'] * np.minimum(1.0, style['glow_gain'] * _blur(core, style['glow_sigma']))
    under = glow * (1 - core)
    alpha = core + under
    with np.errstate(invalid='ignore', divide='ignore'):
        rgb = (core[..., None] * core_rgb + under[..., None] * glow_rgb) / alpha[..., None]
    rgb = np.where(alpha[..., None] > 0, rgb, 0)
    out = np.zeros(core.shape + (4,), np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255)
    out[..., 3] = np.clip(np.rint(alpha * 255), 0, 255)
    out[out[..., 3] == 0] = (10, 10, 10, 0) if state != 23 else (10, 10, 10, 0)
    return out


def library_member(blob, labels, style=LIBRARY_STYLE):
    tex = _library_textures(blob)
    counts = library_audit(blob)
    core, infos = library_core(labels, style)
    data, intended = blob, {}
    for i, t in tex.items():
        rgba = library_state(core, i, style)
        intended[t.key] = rgba
        data = gtf.replace(data, t, rgba)
    return data, intended, {}, {'labels': infos, 'records': counts}


# ---------------------------------------------------------- verification ---
def verify_member(original, built, intended, edits=None):
    """Decode `built` and prove it is exactly the intended change:
    every texture in `intended` decodes to those pixels, every other texture
    and every non-texture byte is unchanged, except the declared script
    `edits` ({offset: bytes}, all before the GTF)."""
    edits = edits or {}
    if len(original) != len(built):
        raise ValueError('member length changed')
    if built == original:
        raise ValueError('member unchanged')
    old, new = gtf.textures(original), gtf.textures(built)
    if [t.key for t in old] != [t.key for t in new] or any(dict(a) != dict(b) for a, b in zip(old, new)):
        raise ValueError('texture headers changed')
    base = gtf_base(original)
    allowed = bytearray(original)
    for p, data in edits.items():
        if p < 0 or p + len(data) > base:
            raise ValueError('script edit at 0x%x outside the effect script' % p)
        allowed[p:p + len(data)] = data
    spans = sorted((t['offset'], t['offset'] + t['width'] * t['height'] * 4) for t in old)
    cursor = 0
    for start, end in spans + [(len(original), len(original))]:
        if bytes(allowed[cursor:start]) != built[cursor:start]:
            raise ValueError('non-texture bytes differ from the declared edits near 0x%x' % cursor)
        cursor = max(cursor, end)
    for t in new:
        want = intended.get(t.key)
        span = slice(t['offset'], t['offset'] + t['size'])
        if want is None:
            if built[span] != original[span]:
                raise ValueError('untouched texture changed: %s' % (t.key,))
        elif not np.array_equal(gtf.decode(built, t), want):
            raise ValueError('decoded texture differs from intended pixels: %s' % (t.key,))
    return True


def verify_archive(path, art):
    """Decode every replaced member of a built EFFPS3 and re-verify it."""
    with CPK(str(path)) as archive:
        by_id = {e['id']: e for e in archive.files}
        if len(by_id) != MEMBERS:
            raise ValueError('built EFFPS3 has %d members' % len(by_id))
        for mid, data in art['members'].items():
            built = archive.read(by_id[mid])
            if built != data:
                raise ValueError('archive member %d differs from the plan' % mid)
            verify_member(art['sources'][mid], built, art['intended'][mid], art['edits'].get(mid))
    return len(art['members'])


# ------------------------------------------------------------------ plan ---
def _render(entry, mid, blob):
    family = entry['family']
    if family == 'location_captions':
        return caption_member(blob, _english(entry['en']))
    if family == 'episode_headings':
        if mid in HEADINGS:
            return episode_member(blob, mid, _english(entry['en']).strip())
        if mid == FINAL:
            return final_member(blob, _english(entry['en'][0]), _english(entry['en'][1]))
    if family == 'berserk' and mid == BERSERK_MEMBER:
        return berserk_member(blob)
    if family == 'library_labels' and mid == LIBRARY_MEMBER:
        return library_member(blob, [_english(t) for t in entry['en']])
    raise ValueError('no renderer for %s member %d' % (family, mid))


def plan(settings=None, catalog=None, families=FAMILIES):
    """EFFPS3 replacement set.

    Returns {'members': {id: bytes}, 'sources', 'intended', 'edits',
    'compress', 'report'}; every member is verified (verify_member) before
    return. 'compress' lists the replaced members the original archive stores
    CRILAYLA-compressed (pass it to cpkpatch.build); members stored raw
    there (232) stay raw."""
    settings = settings or _settings()
    catalog = catalog if catalog is not None else load_catalog()
    work = [e for e in catalog['entries'] if e['status'] == 'translate' and e['family'] in families]
    expected = {m: e['member_sha256'][str(m)] for e in work for m in e['members']}
    sources = source_members(settings, sorted(expected), expected)
    members, intended, edits = {}, {}, {}
    report = {'schema': 1, 'archive': ARCHIVE, 'runtime_verified': False, 'entries': {},
              'pending': [e['id'] for e in catalog['entries'] if e['status'] == 'pending'],
              'kept': [e['id'] for e in catalog['entries'] if e['status'] == 'keep']}
    for e in work:
        infos = {}
        for mid in e['members']:
            if mid in members:
                raise ValueError('member %d rendered twice' % mid)
            data, pix, ed, info = _render(e, mid, sources[mid])
            verify_member(sources[mid], data, pix, ed)
            members[mid], intended[mid], edits[mid] = data, pix, ed
            infos[mid] = _jsonable(info)
        report['entries'][e['id']] = {'family': e['family'], 'en': e['en'], 'members': infos}
    report['members'] = {m: {'input_sha256': sha256(sources[m]), 'output_sha256': sha256(members[m]),
                             'script_edits': len(edits[m])} for m in sorted(members)}
    report['counts'] = {f: sum(1 for e in work if e['family'] == f) for f in families}
    report['replaced_members'] = len(members)
    compress = stored_compressed(settings, members)
    report['compress'] = sorted(compress)
    return {'members': members, 'sources': {m: sources[m] for m in members}, 'intended': intended,
            'edits': edits, 'compress': compress, 'report': report}


def stored_compressed(settings, ids):
    """The subset of `ids` that the pristine EFFPS3 stores CRILAYLA-compressed."""
    from tools.pipeline import verified_source
    with CPK(str(verified_source(settings, ARCHIVE))) as archive:
        return {e['id'] for e in archive.files if e['id'] in set(ids) and e['size'] != e['extract']}


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


# ------------------------------------------------------------- inventory ---
def text_textures(catalog=None):
    """[(entry, member, texture index)] for every catalogued text texture."""
    catalog = catalog if catalog is not None else load_catalog()
    out = []
    for e in catalog['entries']:
        texes = e.get('textures') or ([e['texture']] if e.get('texture') is not None else [0])
        for m in e['members'][:1]:
            for t in texes:
                out.append((e, m, t))
    return out


def _label_sheet(items, title, width=1600, cell=(392, 120), scale=None):
    from PIL import Image, ImageDraw
    cols = max(1, width // (cell[0] + 8))
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (cell[0] + 8) + 8, rows * (cell[1] + 22) + 30), (24, 28, 40))
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 8), title, fill=(255, 255, 160))
    for i, (label, image) in enumerate(items):
        x = 8 + (i % cols) * (cell[0] + 8)
        y = 30 + (i // cols) * (cell[1] + 22)
        draw.text((x, y), label, fill=(255, 255, 160))
        im = image.copy()
        im.thumbnail(cell)
        sheet.paste(im, (x, y + 16))
    return sheet


def inventory(settings, apply=False):
    """Contact sheets of every catalogued text-bearing texture (original
    pixels), one sheet per family, into work/ui/textures/effps3/."""
    catalog = load_catalog()
    items = text_textures(catalog)
    blobs = source_members(settings, sorted({m for _e, m, _t in items}))
    by_family = {}
    for e, m, t in items:
        blob = blobs[m]
        tex = gtf.textures(blob)[t]
        rgba = gtf.decode(blob, tex)
        if e['family'] == 'location_captions':
            rgba = rgba[72:160, 0:448]
        en = e.get('en')
        en = ' / '.join(en) if isinstance(en, list) else (en or '-')
        label = 'm%03d t%d [%s] %s' % (m, t, e['status'], en)
        by_family.setdefault(e['family'], []).append((label, gtf.preview(rgba)))
    written = []
    for family, rows in by_family.items():
        cell = (448, 88) if family == 'location_captions' else (512, 300)
        for n in range(0, len(rows), 60):
            sheet = _label_sheet(rows[n:n + 60], 'EFFPS3 %s (original pixels; entry ids match effps3_art.json)'
                                 % family, cell=cell)
            target = PREVIEWS / ('inventory_%s_%d.png' % (family, n // 60 + 1))
            written.append(target)
            if apply:
                PREVIEWS.mkdir(parents=True, exist_ok=True)
                sheet.save(target)
    return written


def preview(settings, apply=False, art=None):
    """Before/after sheets of every rendered member."""
    from PIL import Image
    art = art or plan(settings)
    written = []
    groups = {}
    catalog = load_catalog()
    family_of = {m: e['family'] for e in catalog['entries'] for m in e['members']}
    for mid in sorted(art['members']):
        src, out = art['sources'][mid], art['members'][mid]
        for key, rgba in art['intended'][mid].items():
            tex = next(t for t in gtf.textures(src) if t.key == key)
            before = gtf.decode(src, tex)
            after = rgba
            if family_of[mid] == 'location_captions':
                before, after = before[72:160, 0:448], after[72:160, 0:448]
            pair = Image.new('RGB', (before.shape[1] * 2 + 12, before.shape[0]), (60, 0, 60))
            pair.paste(gtf.preview(before), (0, 0))
            pair.paste(gtf.preview(after), (before.shape[1] + 12, 0))
            groups.setdefault(family_of[mid], []).append(('m%03d t%d  before | after' % (mid, key[1]), pair))
    for family, rows in groups.items():
        cell = (908, 88) if family == 'location_captions' else (1560, 520)
        per = 20 if family == 'location_captions' else 4
        for n in range(0, len(rows), per):
            sheet = _label_sheet(rows[n:n + per], 'EFFPS3 %s: original | English (decoded from the planned '
                                 'member bytes; not in-game evidence)' % family, width=cell[0] * 2, cell=cell)
            target = PREVIEWS / ('preview_%s_%d.png' % (family, n // per + 1))
            written.append(target)
            if apply:
                PREVIEWS.mkdir(parents=True, exist_ok=True)
                sheet.save(target)
    if apply:
        write_json(PREVIEWS / 'preview_report.json', _jsonable(art['report']))
    return written


# ------------------------------------------------------------------- CLI ---
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['inventory', 'plan', 'preview', 'jigoku-berserk'])
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    if a.command == 'jigoku-berserk':
        extract_jigoku_berserk(a.apply)
        return 0
    settings = _settings()
    if a.command == 'inventory':
        written = inventory(settings, a.apply)
        print('\n'.join(str(p) for p in written))
        print('wrote %d sheets' % len(written) if a.apply else 'DRY RUN: pass --apply to write %d sheets' % len(written))
    elif a.command == 'preview':
        written = preview(settings, a.apply)
        print('\n'.join(str(p) for p in written))
        print('wrote %d sheets' % len(written) if a.apply else 'DRY RUN: pass --apply to write %d sheets' % len(written))
    else:
        art = plan(settings)
        rep = art['report']
        print(json.dumps({k: rep[k] for k in ('counts', 'replaced_members', 'pending', 'kept')}, indent=2))
        print('replaced members: %s (dry run; game_build writes the archive)' % sorted(art['members']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
