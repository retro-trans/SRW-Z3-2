"""AIDDATAPACK.CPK art: the UI word-sprite atlas (member 1).

Dry run by default. Nothing here writes an archive: plan() returns the member
replacement set that game_build turns into ONE cpkpatch.build call
(docs/ART_AIDDATA.md has the exact integration).

What is art in AIDDATAPACK (54 members; `inventory` writes the evidence):
  member 1      GTF, 4 swizzled (0x85) 512x512 ARGB atlases of UI word
                sprites and icons. Textures 0, 2 and 3 hold Japanese words;
                texture 1 holds frames only. This module edits member 1 only.
  members 2, 3  256x256 swizzled, fully black: no text.
  members 7-18  1280x720 linear backgrounds: no text.
  everything else is text or layout data (member 0 is the FSSA UI layout and
  string pool that the EBOOT hook path draws; 19-53 are narration/credits),
  which this module never touches.

Cells (work/translation/en/ui/aiddata_art.json, one rectangle each):
  jigoku-0.6.24  the Tengoku source pixels equal Jigoku's original atlas and
                 Jigoku 0.6.24 shipped English there: its pixels are reused
                 from a hash-guarded asset (`jigoku --apply` re-extracts it).
  new            rendered here from the catalog English in the measured
                 original style (white fill + 2 px black outline, the inverted
                 black-on-white header style, or the Spirit icon plate).
  keep           left as is (pictogram icons, blank plate); listed so the
                 inventory is complete.
Only pixels inside a cell rectangle ever change; headers, other textures and
every pixel outside the rectangles are verified byte/pixel identical.

    python -m tools.aid_art plan
    python -m tools.aid_art catalog   [--apply]  (measured fields of aiddata_art.json)
    python -m tools.aid_art inventory [--apply]  (contact sheets + inventory.json)
    python -m tools.aid_art preview   [--apply]  (before/after review sheets)
    python -m tools.aid_art jigoku    [--apply]  (re-extract the Jigoku cell asset)

Fonts are read (never written) from the RPCS3 dev_flash folder next to
ui_build.FACE. Requires numpy and Pillow (bundled Python).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools import gtf
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK, decompress_crilayla

ARCHIVE = '/PS3_GAME/USRDIR/DATA/AIDDATA/AIDDATAPACK.CPK'
ART_MEMBER = 1
MEMBER_COUNT = 54
SIZE = 512
# Decoded member 1 of the pristine Tengoku archive.
M1_SHA256 = 'db7ef062281e0f8f5ce7b72eb7d56db8ae2948ad673d8d4b9d61931c9c64a6a6'
M1_BYTES = 4194560

CATALOG = ROOT / 'work/translation/en/ui/aiddata_art.json'
ASSETS = ROOT / 'work/ui/textures/assets'
JIGOKU_ASSET = ASSETS / 'aid_m001_jigoku_0.6.24_cells.png'
CACHE = ROOT / 'work/tengoku/cache/aiddata_members'
PREVIEWS = ROOT / 'work/ui/textures/aiddata'

JIGOKU_ORIGINAL = Path('E:/Projects/SRW Z3/work/orig/AIDDATAPACK.CPK')
JIGOKU_SHIPPED = Path('E:/Projects/SRW Z3/releases/0.6.24/AIDDATAPACK.CPK')
JIGOKU_M1_ORIGINAL = 'a75633dc75a1c13fc4fa35830bb69bd671a43577858f9762f088c6253ef84358'
JIGOKU_M1_SHIPPED = 'e07b9532b389c30c19414639307068df8f16099562508ac4e42c3f85acba965d'

FACE = 'SCE-PS3-RD-B-LATIN.TTF'     # Rodin Bold, the PS3 gothic closest to the atlas
SUPERSAMPLE = 4
STROKE = 2                          # outline width measured on the Japanese words
CAP_RATIO = 0.78                    # Latin cap height / (Japanese ink height - 2 outlines)
MIN_SQUEEZE = 0.52                  # horizontal condensing before shrinking
STYLES = {'white': ((255, 255, 255), (0, 0, 0)),     # fill, outline
          'inverse': ((0, 0, 0), (255, 255, 255)),
          'icon': None}
SOURCES = ('jigoku-0.6.24', 'new', 'keep')

# Every cell Jigoku 0.6.24 rewrote in its member 1, with the module that did it
# (Jigoku tools/attack_heading.py, trader_art.py, startup_menu_layout.py).
# Rectangles are (x0, y0, x1, y1) in the 512x512 texture.
JIGOKU_CELLS = {
    't2.all': (2, (0, 0, 80, 40), 'ALL', 'attack_heading.py'),
    't2.attack_heading': (2, (80, 0, 160, 40), 'Attack', 'attack_heading.py'),
    't0.shield_def': (0, (0, 24, 128, 48), 'Shield Def.', 'trader_art.py'),
    't0.parry': (0, (0, 48, 88, 72), 'Parry', 'trader_art.py'),
    't0.double_image': (0, (88, 48, 136, 72), 'Dbl Img', 'trader_art.py'),
    't0.barrier': (0, (0, 72, 64, 96), 'Barrier', 'trader_art.py'),
    't0.intermission': (0, (0, 192, 296, 232), 'Intermission', 'trader_art.py'),
    't2.center': (2, (160, 0, 296, 40), 'Center', 'trader_art.py'),
    't2.wide': (2, (296, 0, 392, 40), 'Wide', 'trader_art.py'),
    't2.map': (2, (392, 0, 512, 40), 'Map', 'trader_art.py'),
    't2.support': (2, (0, 88, 72, 128), 'Support', 'trader_art.py'),
    't2.attack': (2, (72, 88, 144, 128), 'Attack', 'trader_art.py'),
    't2.defend': (2, (144, 88, 216, 128), 'Defend', 'trader_art.py'),
    't2.re': (2, (216, 88, 256, 128), 'Re-', 'trader_art.py'),
    't2.weapon': (2, (256, 88, 336, 128), 'Wpn', 'trader_art.py'),
    't2.song': (2, (336, 88, 384, 128), 'Song', 'trader_art.py'),
    't2.counter': (2, (320, 40, 512, 88), 'Counter', 'trader_art.py'),
    't2.maximum': (2, (0, 40, 176, 88), 'Maximum', 'trader_art.py'),
    't2.break': (2, (176, 40, 320, 88), 'Break', 'trader_art.py'),
    't2.mobi': (2, (56, 192, 112, 224), 'Mobi', 'trader_art.py'),
    't2.lity': (2, (56, 320, 88, 352), 'lity', 'trader_art.py'),
    't2.armor': (2, (56, 256, 112, 288), 'Armor', 'trader_art.py'),
    't2.accuracy': (2, (56, 224, 112, 256), 'Sight', 'trader_art.py'),
    't2.value': (2, (56, 352, 88, 384), '', 'trader_art.py'),
    't2.scenario_select': (2, (272, 432, 512, 472), 'Scenario Select', 'startup_menu_layout.py'),
    't2.main': (2, (136, 472, 208, 512), 'Main', 'startup_menu_layout.py'),
    't2.tutorial': (2, (208, 472, 376, 512), 'Tutorial', 'startup_menu_layout.py'),
    't2.scenario': (2, (376, 472, 512, 512), 'Scenario', 'startup_menu_layout.py'),
}


def _icon_rect(row, col):
    """Spirit icon cell: 48 px pitch from (0, 274); row 0 starts below the
    placeholder-box strip that ends at y 286."""
    top = 274 + 48 * row
    return (48 * col, max(top, 287), 48 * col + 48, top + 46)


SPIRIT_ICONS = [('鉄', 'Wa', 0, 0), ('幸', 'Lu', 0, 1), ('集', 'Fo', 1, 0), ('努', 'Ga', 1, 1),
                ('必', 'St', 2, 0), ('乱', 'Di', 2, 1), ('加', 'Ac', 3, 0), ('分', 'An', 3, 1),
                ('覚', 'Ze', 4, 0)]
SPIRIT_IDS = {'鉄': 'wall', '幸': 'luck', '集': 'focus', '努': 'gain', '必': 'strike',
              '乱': 'disrupt', '加': 'accel', '分': 'analyze', '覚': 'zeal'}
BLANK_PLATE = _icon_rect(4, 1)      # the game's own empty icon plate

TERMS = {
    'eboot': 'work/translation/en/ui/eboot.json',
    'spirit_abbreviation': 'work/translation/en/ui/spirit_commands.json (abbreviation column)',
    'skill': 'work/translation/en/ui/rpw_names.json (skill)',
}

# The catalog's starting content: (id, texture, rect, jp, en, source, style, role, term).
# `catalog --apply` writes it with measured fields; English already in the
# file is kept.
DEFAULT_CELLS = [
    # texture 0
    ('t0.shield_def', 0, None, 'シールド防御', 'Shield Def.', 'jigoku-0.6.24', None,
     'defensive skill activation word (map/battle popup)', 'eboot: シールド防御 = Shield Defense'),
    ('t0.parry', 0, None, '切り払い', 'Parry', 'jigoku-0.6.24', None,
     'defensive skill activation word', 'eboot: 切り払い = Parry'),
    ('t0.double_image', 0, None, '分身', 'Dbl Img', 'jigoku-0.6.24', None,
     'defensive skill activation word', 'eboot: 分身 = Double Image'),
    ('t0.barrier', 0, None, 'バリア', 'Barrier', 'jigoku-0.6.24', None,
     'defensive skill activation word', 'eboot: バリア = Barrier'),
    ('t0.intermission', 0, None, 'インターミッション', 'Intermission', 'jigoku-0.6.24', None,
     'Intermission menu heading', 'eboot: インターミッションを終了します。 = End the intermission.'),
    ('t0.sub_order', 0, (0, 232, 208, 273), 'サブオーダー', 'Sub Order', 'new', 'inverse',
     'Sub Order heading (same black-on-white style as Intermission)',
     'eboot: サブオーダー… = Sub Order'),
    ('t0.sortie', 0, (295, 88, 368, 128), '出撃', 'Sortie', 'new', 'white',
     'deploy marker; drawn with t0.locked as 出撃不可', 'eboot: 出撃準備画面 = Sortie Prep'),
    ('t0.locked', 0, (368, 88, 441, 128), '不可', 'Locked', 'new', 'white',
     'second half of 出撃不可 (unit cannot sortie)', 'new wording (no project string for 出撃不可)'),
    ('t0.combine', 0, (441, 104, 512, 145), '合体', 'Combine', 'new', 'white',
     'combine command word', 'eboot: 合体 = Combine'),
] + [('t0.spirit_' + SPIRIT_IDS[jp], 0, _icon_rect(r, c), jp, en, 'new', 'icon',
      'Spirit Command icon (kanji abbreviation on a grey plate)',
      'spirit abbreviation: %s = %s' % (jp, en)) for jp, en, r, c in SPIRIT_ICONS] + [
    ('t0.spirit_blank', 0, BLANK_PLATE, '', None, 'keep', None,
     'empty Spirit icon plate (used as the base of the English icons)', None),
    # texture 2
    ('t2.all', 2, None, '全体', 'ALL', 'jigoku-0.6.24', None,
     'attack-type heading (target selection)', 'eboot: 全体 = All; ALL weapons'),
    ('t2.attack_heading', 2, None, '攻撃', 'Attack', 'jigoku-0.6.24', None,
     'attack-type heading', 'eboot: 攻撃 = Attack'),
    ('t2.center', 2, None, 'センター', 'Center', 'jigoku-0.6.24', None, 'attack-type heading', None),
    ('t2.wide', 2, None, 'ワイド', 'Wide', 'jigoku-0.6.24', None, 'attack-type heading', None),
    ('t2.map', 2, (392, 0, 512, 40), 'マップ', 'MAP', 'new', 'white',
     'attack-type heading / MAP weapon (Jigoku drew "Map")', 'eboot: マップ兵器 = MAP Weapon'),
    ('t2.maximum', 2, None, 'マキシマム', 'Maximum', 'jigoku-0.6.24', None,
     'Maximum Break word', 'eboot: マキシマムブレイク = Maximum Break'),
    ('t2.break', 2, None, 'ブレイク', 'Break', 'jigoku-0.6.24', None, 'Maximum Break word', None),
    ('t2.counter', 2, None, 'カウンター', 'Counter', 'jigoku-0.6.24', None,
     'skill activation word', 'skill: カウンター = Counter'),
    ('t2.support', 2, None, '援護', 'Support', 'jigoku-0.6.24', None,
     'support attack / defend popup word', 'skill: 援護攻撃 = Support Atk, 援護防御 = Support Def'),
    ('t2.attack', 2, None, '攻撃', 'Attack', 'jigoku-0.6.24', None, 'popup word', None),
    ('t2.defend', 2, None, '防御', 'Defend', 'jigoku-0.6.24', None, 'popup word', None),
    ('t2.re', 2, None, '再', 'Re-', 'jigoku-0.6.24', None, 'Re-Attack prefix',
     'skill: 再攻撃 = Re-Attack'),
    ('t2.weapon', 2, None, '兵器', 'Wpn', 'jigoku-0.6.24', None, 'MAP weapon popup word',
     'eboot: マップ兵器 = MAP Weapon'),
    ('t2.song', 2, None, '歌', 'Song', 'jigoku-0.6.24', None, 'song command word', 'eboot: 歌 = Song'),
    ('t2.mobi', 2, None, '運動', 'Mobi', 'jigoku-0.6.24', None, 'first half of 運動性 (Mobility)',
     'eboot: 運動性▼ = Mobility Down'),
    ('t2.lity', 2, None, '性', 'lity', 'jigoku-0.6.24', None, 'second half of 運動性', None),
    ('t2.armor', 2, None, '装甲', 'Armor', 'jigoku-0.6.24', None, 'first half of 装甲値',
     'eboot: 装甲値▼ = Armor Down'),
    ('t2.value', 2, None, '値', '', 'jigoku-0.6.24', None,
     'shared suffix 値 of 装甲値/照準値; blank in English', None),
    ('t2.accuracy', 2, (56, 224, 112, 256), '照準', 'Acc.', 'new', 'white',
     'first half of 照準値 (Jigoku drew "Sight")', 'eboot: 照準値▼ = Accuracy Down'),
    ('t2.spirit', 2, (56, 128, 112, 160), '精神', 'Spirit', 'new', 'white', 'effect popup word',
     'eboot: 精神付与 = Spirit Grant'),
    ('t2.grant', 2, (56, 160, 112, 192), '付与', 'Grant', 'new', 'white', 'effect popup word',
     'eboot: 精神付与 = Spirit Grant'),
    ('t2.max', 2, (56, 384, 112, 416), '最大', 'Max', 'new', 'white', 'effect popup word',
     'eboot: 最大気力上昇 = Max Focus Up'),
    ('t2.morale', 2, (0, 224, 56, 256), '気力', 'Foc', 'new', 'white', 'effect popup word',
     'eboot: 気力上昇 = Focus Up'),
    ('t2.stats', 2, (0, 256, 56, 288), '能力', 'Stats', 'new', 'white', 'effect popup word',
     'eboot: 能力上昇 = Stats Up'),
    ('t2.combat', 2, (0, 288, 56, 320), '戦闘', 'Combat', 'new', 'white',
     'effect popup word (戦闘不能)', 'eboot: 戦闘不能 = Disabled'),
    ('t2.regen', 2, (0, 320, 56, 352), '回復', 'Regen', 'new', 'white', 'effect popup word',
     'eboot: ＨＰ回復 = HP Regen'),
    ('t2.up', 2, (0, 352, 56, 384), '上昇', 'Up', 'new', 'white', 'effect popup word',
     'eboot: 気力上昇 = Morale Up'),
    ('t2.halved', 2, (0, 384, 56, 416), '半減', 'Halved', 'new', 'white', 'effect popup word',
     'eboot: 能力半減 = Stats Halved'),
    ('t2.down', 2, (0, 416, 56, 448), '低下', 'Down', 'new', 'white', 'effect popup word',
     'eboot: 気力低下 = Morale Down'),
    ('t2.disabled', 2, (0, 448, 56, 480), '不能', 'Disabled', 'new', 'white', 'effect popup word',
     'eboot: 戦闘不能 = Disabled'),
    ('t2.command', 2, (0, 480, 80, 512), 'コマンド', 'Command', 'new', 'white', 'effect popup word',
     'eboot: コマンド選択 = Select Command'),
    ('t2.pilot_setup', 2, (304, 384, 512, 432), '主人公設定', 'Pilot Setup', 'new', 'white',
     'new-game protagonist setup heading', 'Jigoku Vita art: Pilot Setup'),
    ('t2.scenario_select', 2, None, 'シナリオ選択', 'Scenario Select', 'jigoku-0.6.24', None,
     'new-game scenario select heading', None),
    ('t2.main', 2, None, '本編', 'Main', 'jigoku-0.6.24', None, 'drawn with t2.scenario', None),
    ('t2.tutorial', 2, None, 'ガイダンス', 'Tutorial', 'jigoku-0.6.24', None,
     'drawn with t2.scenario', None),
    ('t2.scenario', 2, None, 'シナリオ', 'Scenario', 'jigoku-0.6.24', None,
     'Main / Tutorial Scenario', None),
    ('t2.game', 2, (330, 320, 410, 350), 'ゲーム', 'Game', 'new', 'white',
     'title menu: [Game][Start]', 'new (Tengoku-only title menu art)'),
    ('t2.start', 2, (410, 320, 512, 350), 'スタート', 'Start', 'new', 'white',
     'title menu: shared second word of both start options', 'FSSA: この結果をリンクさせてスタート'),
    ('t2.link_data', 2, (265, 352, 512, 384), 'データをリンクさせて', 'Link Data and', 'new', 'white',
     'title menu: [Link Data and][Start] (link Jigoku/Rengoku clear data)',
     'FSSA: データのリンクを行いますか？'),
    # texture 3
    ('t3.sortie', 3, (175, 224, 231, 255), '出撃', 'Sortie', 'new', 'white',
     'deploy marker (small copy)', 'eboot: 出撃準備画面 = Sortie Prep'),
    ('t3.locked', 3, (231, 224, 287, 255), '不可', 'Locked', 'new', 'white',
     'second half of 出撃不可 (small copy)', None),
    ('t3.combine_score', 3, (298, 177, 356, 207), '合体', 'Combine', 'new', 'white',
     'drawn after the separate "SCORE:" sprite', 'eboot: 合体 = Combine'),
    ('t3.assist', 3, (432, 176, 512, 209), 'Assi', 'Asst', 'new', 'white',
     'complete Assist abbreviation inside the existing weapon-type sprite', 'native English Assist weapon badge'),
    ('t3.combo_attack', 3, (47, 479, 142, 511), '合体攻撃', 'Combo Attack', 'new', 'white',
     'combination attack word', 'eboot: 合体攻撃 = Combo Attack'),
    ('t3.single_icon', 3, (140, 108, 190, 152), '単', None, 'keep', None,
     'pictogram icon (single unit); role not traced, left as is', None),
    ('t3.combine_icon', 3, (148, 169, 183, 199), '合体', None, 'keep', None,
     '35x30 icon next to the VR icon; too small for English, left as is', None),
    ('t3.unit_icon', 3, (34, 346, 78, 397), '機', None, 'keep', None,
     'pictogram icon (unit); role not traced, left as is', None),
]


def font_dir():
    from tools.ui_build import FACE as UI_FACE
    return UI_FACE.parent


def _settings():
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


# ---------------------------------------------------------------- sources ---
def decoded_members(path, cache, ids=None):
    """{id: decoded bytes} of a CPK, cached under `cache` and keyed by the
    SHA-256 of each stored member (stale cache entries are re-read)."""
    cache = Path(cache)
    out = {}
    with CPK(path) as archive:
        for entry in archive.files:
            if ids is not None and entry['id'] not in ids:
                continue
            raw = bytes(archive.buf[entry['offset']:entry['offset'] + entry['size']])
            raw_sha = sha256(raw)
            data_file, tag = cache / ('%03d.bin' % entry['id']), cache / ('%03d.raw_sha256' % entry['id'])
            if data_file.exists() and tag.exists() and tag.read_text().strip() == raw_sha \
                    and data_file.stat().st_size == (entry['extract'] or entry['size']):
                out[entry['id']] = data_file.read_bytes()
                continue
            data = decompress_crilayla(raw) if raw[:8] == b'CRILAYLA' else raw
            if len(data) != (entry['extract'] or entry['size']):
                raise ValueError('member %d decodes to the wrong size' % entry['id'])
            cache.mkdir(parents=True, exist_ok=True)
            data_file.write_bytes(data)
            tag.write_text(raw_sha + '\n')
            out[entry['id']] = data
    return out


def source_path(settings):
    from tools.pipeline import verified_source
    return verified_source(settings, ARCHIVE)


def source_member(settings):
    """Decoded member 1 of the verified pristine archive, guarded by SHA-256."""
    blob = decoded_members(source_path(settings), CACHE, {ART_MEMBER})[ART_MEMBER]
    if sha256(blob) != M1_SHA256:
        raise ValueError('AIDDATAPACK member 1 is not the guarded Tengoku source')
    return blob


def atlas_textures(blob):
    tex = gtf.textures(blob)
    if len(blob) != M1_BYTES or len(gtf.gtfs(blob)) != 1 or len(tex) != 4 or \
            any((t['fmt'], t['width'], t['height']) != (gtf.SWIZZLED_ARGB, SIZE, SIZE) for t in tex):
        raise ValueError('member 1 is not four 512x512 swizzled atlases')
    return tex


def rect_pixels(rgba, rect):
    x0, y0, x1, y1 = rect
    return np.ascontiguousarray(rgba[y0:y1, x0:x1])


def rect_sha(rgba, rect):
    return sha256(rect_pixels(rgba, rect).tobytes())


def ink_box(rgba, rect):
    """Alpha bounding box of the original lettering, relative to the rect."""
    a = rect_pixels(rgba, rect)[..., 3]
    ys, xs = np.nonzero(a)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


# ---------------------------------------------------------------- catalog ---
def _check_rect(rect, label):
    x0, y0, x1, y1 = rect
    if not (0 <= x0 < x1 <= SIZE and 0 <= y0 < y1 <= SIZE):
        raise ValueError('%s: rect %s outside the 512x512 atlas' % (label, rect))


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('member') != ART_MEMBER or not isinstance(data.get('cells'), dict):
        raise ValueError('aiddata_art.json: expected schema 1, member 1 and "cells"')
    painted = []
    for cid, cell in data['cells'].items():
        if cell.get('source') not in SOURCES:
            raise ValueError('%s: source must be one of %s' % (cid, SOURCES))
        if cell.get('texture') not in (0, 1, 2, 3):
            raise ValueError('%s: texture must be 0-3' % cid)
        rect = tuple(cell.get('rect') or ())
        if len(rect) != 4:
            raise ValueError('%s: rect must be [x0, y0, x1, y1]' % cid)
        _check_rect(rect, cid)
        en = cell.get('en')
        if cell['source'] == 'jigoku-0.6.24':
            want = JIGOKU_CELLS.get(cid)
            if want is None or (want[0], want[1]) != (cell['texture'], rect):
                raise ValueError('%s: not a Jigoku 0.6.24 cell with that rectangle' % cid)
        elif cell['source'] == 'new':
            if not isinstance(en, str) or not en.strip() or not en.isascii() or '\n' in en:
                raise ValueError('%s: English must be one non-empty ASCII line' % cid)
            if cell.get('style') not in STYLES:
                raise ValueError('%s: style must be one of %s' % (cid, sorted(STYLES)))
        if cell['source'] != 'keep':
            for other_id, other in painted:
                if other[0] == cell['texture'] and _overlap(other[1], rect):
                    raise ValueError('cells %s and %s overlap' % (other_id, cid))
            painted.append((cid, (cell['texture'], rect)))
    return data


def build_catalog(settings, apply=False):
    """aiddata_art.json from DEFAULT_CELLS plus measured source fields.

    English already present in the file is kept (the file is the source of
    truth for wording); the measured fields (rect for Jigoku cells, ink box,
    source pixel SHA-256) are recomputed from the pristine source."""
    blob = source_member(settings)
    tex = atlas_textures(blob)
    pixels = [gtf.decode(blob, t) for t in tex]
    old = load_catalog()['cells'] if CATALOG.exists() else {}
    cells = {}
    for cid, ti, rect, jp, en, source, style, role, term in DEFAULT_CELLS:
        if source == 'jigoku-0.6.24' or (rect is None and cid in JIGOKU_CELLS):
            ti, rect = JIGOKU_CELLS[cid][0], JIGOKU_CELLS[cid][1]
        prev = old.get(cid) or {}
        if prev.get('source') == 'new' or (prev and source != 'jigoku-0.6.24'):
            # The file is the source of truth for wording, style and the
            # reuse/new/keep decision (a Jigoku cell may be switched to new).
            source, en, style = prev['source'], prev.get('en'), prev.get('style')
            if source == 'new' and cid in JIGOKU_CELLS and rect is None:
                rect = JIGOKU_CELLS[cid][1]
        cell = {'texture': ti, 'rect': list(rect), 'jp': jp, 'en': en, 'source': source,
                'style': style, 'role': role}
        if prev.get('cap') is not None:
            cell['cap'] = prev['cap']
        if term:
            cell['term'] = term
        if source == 'jigoku-0.6.24':
            cell['jigoku_module'] = JIGOKU_CELLS[cid][3]
        if cid in JIGOKU_CELLS and source == 'new':
            cell['note'] = 'overrides the Jigoku 0.6.24 cell (%r) for project wording' % JIGOKU_CELLS[cid][2]
        box = ink_box(pixels[ti], rect)
        cell['ink_box'] = list(box) if box else None
        cell['source_sha256'] = rect_sha(pixels[ti], rect)
        cells[cid] = cell
    catalog = {
        'schema': 1,
        'archive': ARCHIVE,
        'member': ART_MEMBER,
        'about': 'UI word sprites in AIDDATAPACK member 1 (four 512x512 swizzled atlases). '
                 'Each cell is one rectangle; tools/aid_art.py repaints only inside it. '
                 'source: jigoku-0.6.24 = Jigoku shipped pixels reused (Tengoku source identical), '
                 'new = rendered from "en", keep = left as is. Edit "en" for new cells only.',
        'terms': TERMS,
        'face': FACE,
        'cells': cells,
    }
    counts = {s: sum(1 for c in cells.values() if c['source'] == s) for s in SOURCES}
    if apply:
        write_json(CATALOG, catalog)
        load_catalog()
    return catalog, counts


# --------------------------------------------------------------- rendering ---
def _font(size):
    from PIL import ImageFont
    return ImageFont.truetype(str(font_dir() / FACE), max(1, int(round(size))))


def _cap_size(cap):
    """Font pixel size whose 'H' is `cap` pixels tall."""
    probe = _font(400)
    l, t, r, b = probe.getbbox('H')
    return 400.0 * cap / (b - t)


def _layer(text, size, stroke, fill, edge):
    """Supersampled RGBA of `text` (fill + outline) and the cap band (top,
    bottom) of 'H' inside it, in supersampled pixels."""
    from PIL import Image, ImageDraw
    font = _font(size * SUPERSAMPLE)
    sw = int(round(stroke * SUPERSAMPLE))
    l, t, r, b = font.getbbox(text, stroke_width=sw)
    pad = SUPERSAMPLE
    image = Image.new('RGBA', (r - l + 2 * pad, b - t + 2 * pad))
    ImageDraw.Draw(image).text((pad - l, pad - t), text, font=font, fill=fill + (255,),
                               stroke_width=sw, stroke_fill=edge + (255,))
    hl, ht, hr, hb = font.getbbox('H')
    return image, (pad - t + ht, pad - t + hb)


def _straight(image):
    a = np.asarray(image.convert('RGBA'), dtype=np.uint8).copy()
    a[a[..., 3] == 0] = 0
    return a


def word_pixels(text, size_wh, box, style, cap=None):
    """RGBA (h, w, 4) for one cell: `text` in the measured outline style,
    sized from the original ink box `box` (relative x0, y0, x1, y1),
    centred on the original ink and condensed to fit the cell.

    Returns (rgba, info)."""
    from PIL import Image
    w, h = size_wh
    fill, edge = STYLES[style]
    ix0, iy0, ix1, iy1 = box
    if cap is None:
        cap = CAP_RATIO * ((iy1 - iy0) - 2 * STROKE)
    size = _cap_size(cap)
    avail = w - 2
    for _ in range(40):
        layer, (ctop, cbot) = _layer(text, size, STROKE, fill, edge)
        natural = layer.width / float(SUPERSAMPLE)
        squeeze = min(1.0, avail / natural)
        out_w = max(1, int(round(natural * squeeze)))
        out_h = max(1, int(round(layer.height / float(SUPERSAMPLE))))
        if squeeze >= MIN_SQUEEZE and out_h <= h:
            break
        size *= 0.95
    else:
        raise ValueError('cell text does not fit: %r in %dx%d' % (text, w, h))
    ink = layer.resize((out_w, out_h), Image.BOX)
    # Centre the cap band on the original ink centre; keep descenders inside.
    band = (ctop + cbot) / 2.0 / SUPERSAMPLE * (out_h / (layer.height / float(SUPERSAMPLE)))
    y0 = int(round((iy0 + iy1) / 2.0 - band))
    y0 = max(0, min(h - out_h, y0))
    x0 = int(round((ix0 + ix1) / 2.0 - out_w / 2.0))
    x0 = max(0, min(w - out_w, x0))
    canvas = Image.new('RGBA', (w, h))
    canvas.alpha_composite(ink, (x0, y0))
    info = {'font_px': round(size, 2), 'cap_px': round(cap, 2), 'squeeze': round(squeeze, 3),
            'ink': [x0, y0, x0 + out_w, y0 + out_h]}
    return _straight(canvas), info


def icon_pixels(text, plate, size_wh, centre, top=0):
    """RGBA for a Spirit icon: the game's blank plate with `text` in white
    and the dark soft outline the kanji icons use. `plate` is the 48x46
    blank icon cell; `top` crops the first rows (row 0 sits under a strip)."""
    from PIL import Image, ImageFilter
    w, h = size_wh
    full_h = plate.shape[0]
    base = Image.fromarray(np.ascontiguousarray(plate), 'RGBA')
    size = _cap_size(15)
    font = _font(size * SUPERSAMPLE)
    l, t, r, b = font.getbbox(text)
    pad = 6 * SUPERSAMPLE
    from PIL import ImageDraw
    mask = Image.new('L', (r - l + 2 * pad, b - t + 2 * pad))
    ImageDraw.Draw(mask).text((pad - l, pad - t), text, font=font, fill=255)
    hl, ht, hr, hb = font.getbbox('H')
    cy_ss = pad - t + (ht + hb) / 2.0
    sw = Image.new('L', mask.size)
    ImageDraw.Draw(sw).text((pad - l, pad - t), text, font=font, fill=255,
                            stroke_width=3 * SUPERSAMPLE, stroke_fill=255)
    small = (mask.width // SUPERSAMPLE, mask.height // SUPERSAMPLE)
    glyph = np.asarray(mask.resize(small, Image.BOX), dtype=np.float64) / 255.0
    core = np.asarray(sw.resize(small, Image.BOX), dtype=np.float64) / 255.0
    soft = np.asarray(sw.resize(small, Image.BOX).filter(ImageFilter.GaussianBlur(1.6)),
                      dtype=np.float64) / 255.0
    halo = np.clip(0.94 * core + 0.55 * soft, 0, 1)
    layer = np.zeros(small[::-1] + (4,), np.float64)
    # white glyph over black halo (straight alpha, "over")
    a = glyph + halo * (1 - glyph)
    layer[..., 3] = a
    with np.errstate(invalid='ignore', divide='ignore'):
        grey = np.where(a > 0, 255.0 * glyph / np.maximum(a, 1e-9), 0)
    layer[..., 0] = layer[..., 1] = layer[..., 2] = grey
    over = Image.fromarray(np.clip(np.rint(layer * [1, 1, 1, 255]), 0, 255).astype(np.uint8), 'RGBA')
    ox = int(round(centre[0] - small[0] / 2.0))
    oy = int(round(centre[1] - cy_ss / SUPERSAMPLE))
    canvas = Image.new('RGBA', (w, full_h))
    canvas.alpha_composite(base)
    canvas.alpha_composite(over, (ox, oy))
    out = _straight(canvas)[top:top + h]
    return out, {'cap_px': 15, 'origin': [ox, oy - top]}


# ------------------------------------------------------------- the member ---
def jigoku_cells():
    """{cell id: RGBA} from the stored Jigoku asset, every cell hash-checked."""
    from PIL import Image
    meta = json.loads(JIGOKU_ASSET.with_suffix('.json').read_text(encoding='utf-8'))
    sheet = gtf.from_image(Image.open(JIGOKU_ASSET))
    out = {}
    for cid, row in meta['cells'].items():
        ti, rect = JIGOKU_CELLS[cid][0], JIGOKU_CELLS[cid][1]
        if (row['texture'], tuple(row['rect'])) != (ti, rect):
            raise ValueError('Jigoku asset cell %s moved' % cid)
        x0, y0, x1, y1 = rect
        pix = np.ascontiguousarray(sheet[row['asset_y']:row['asset_y'] + y1 - y0, :x1 - x0])
        if sha256(pix.tobytes()) != row['shipped_sha256']:
            raise ValueError('Jigoku asset cell %s does not match its recorded hash' % cid)
        out[cid] = (pix, row)
    return out, meta


def member_art(blob, catalog, render=True):
    """(new member bytes, {texture key: RGBA}, {texture key: [rects]}, report)."""
    if sha256(blob) != M1_SHA256:
        raise ValueError('member 1 is not the guarded Tengoku source')
    tex = atlas_textures(blob)
    pixels = [gtf.decode(blob, t) for t in tex]
    work = [p.copy() for p in pixels]
    rects = {t.key: [] for t in tex}
    reused, cells_report = None, {}
    plate = rect_pixels(pixels[0], (BLANK_PLATE[0], 466, BLANK_PLATE[2], 512))
    for cid, cell in sorted(catalog['cells'].items()):
        ti, rect, source = cell['texture'], tuple(cell['rect']), cell['source']
        if source == 'keep':
            continue
        if rect_sha(pixels[ti], rect) != cell['source_sha256']:
            raise ValueError('%s: source pixels differ from the catalog guard' % cid)
        x0, y0, x1, y1 = rect
        if source == 'jigoku-0.6.24':
            if reused is None:
                reused, _meta = jigoku_cells()
            pix, row = reused[cid]
            if row['source_sha256'] != cell['source_sha256']:
                raise ValueError('%s: Jigoku original pixels differ from the Tengoku source' % cid)
            info = {'en': cell['en'], 'source': source}
        elif cell['style'] == 'icon':
            top = rect[1] - (rect[3] - 46)          # rows cropped off the top of the cell
            box = cell['ink_box']
            glyph = _glyph_centre(pixels[ti], rect)
            pix, info = icon_pixels(cell['en'], plate, (x1 - x0, y1 - y0),
                                    (glyph[0], glyph[1] + top), top)
            info.update(en=cell['en'], source=source)
        else:
            box = cell.get('ink_box') or [0, 0, x1 - x0, y1 - y0]
            pix, info = word_pixels(cell['en'], (x1 - x0, y1 - y0), box, cell['style'], cell.get('cap'))
            info.update(en=cell['en'], source=source)
        work[ti][y0:y1, x0:x1] = pix
        rects[tex[ti].key].append(rect)
        cells_report[cid] = info
    data, intended = blob, {}
    for t, before, after in zip(tex, pixels, work):
        if not np.array_equal(before, after):
            data = gtf.replace(data, t, after)
            intended[t.key] = after
    report = {
        'reused_jigoku': sorted(c for c, i in cells_report.items() if i['source'] == 'jigoku-0.6.24'),
        'rendered': sorted(c for c, i in cells_report.items() if i['source'] == 'new'),
        'kept': sorted(c for c, v in catalog['cells'].items() if v['source'] == 'keep'),
        'cells': cells_report,
    }
    return data, intended, {k: v for k, v in rects.items() if v}, report


def _glyph_centre(rgba, rect):
    """Centre of the bright kanji strokes of an icon, relative to the rect."""
    a = rect_pixels(rgba, rect)
    bright = (a[..., 3] > 200) & (a[..., 0] > 200)
    ys, xs = np.nonzero(bright)
    return (float(xs.min() + xs.max() + 1) / 2.0, float(ys.min() + ys.max() + 1) / 2.0)


# ---------------------------------------------------------- verification ---
def verify_member(original, built, intended, rects):
    """Header and non-pixel bytes identical; textures not in `intended`
    byte-identical; each intended texture decodes to exactly its pixels, and
    every pixel outside its cell rectangles equals the original."""
    if len(original) != len(built):
        raise ValueError('member length changed')
    if built == original:
        raise ValueError('member unchanged')
    old, new = gtf.textures(original), gtf.textures(built)
    if [dict(t) for t in old] != [dict(t) for t in new]:
        raise ValueError('texture headers changed')
    cursor = 0
    for start, end in sorted((t['offset'], t['offset'] + t['size']) for t in old) + \
            [(len(original), len(original))]:
        if original[cursor:start] != built[cursor:start]:
            raise ValueError('non-texture bytes changed at 0x%x' % cursor)
        cursor = max(cursor, end)
    for t in new:
        span = slice(t['offset'], t['offset'] + t['size'])
        if t.key not in intended:
            if built[span] != original[span]:
                raise ValueError('untouched texture changed: %s' % (t.key,))
            continue
        after = gtf.decode(built, t)
        if not np.array_equal(after, intended[t.key]):
            raise ValueError('decoded texture differs from intended pixels: %s' % (t.key,))
        keep = np.ones((t['height'], t['width']), bool)
        for x0, y0, x1, y1 in rects.get(t.key, ()):
            keep[y0:y1, x0:x1] = False
        if (gtf.decode(original, t)[keep] != after[keep]).any():
            raise ValueError('pixels outside the cell rectangles changed: %s' % (t.key,))
    return True


def verify_archive(path, art):
    """Re-read a built AIDDATAPACK: every art member decodes to the plan and
    passes verify_member; every other member's stored bytes equal the
    pristine source's."""
    checked, untouched = 0, 0
    with CPK(art['source_path']) as source, CPK(path) as built:
        src = {e['id']: e for e in source.files}
        out = {e['id']: e for e in built.files}
        if set(src) != set(out) or len(out) != MEMBER_COUNT:
            raise ValueError('member set changed')
        for mid, entry in out.items():
            if mid in art['members']:
                data = built.read(entry)
                if data != art['members'][mid]:
                    raise ValueError('archive member %d differs from the plan' % mid)
                verify_member(art['sources'][mid], data, art['intended'][mid], art['rects'][mid])
                checked += 1
            else:
                a, b = src[mid], entry
                if (a['size'], a['extract']) != (b['size'], b['extract']) or \
                        source.buf[a['offset']:a['offset'] + a['size']] != \
                        built.buf[b['offset']:b['offset'] + b['size']]:
                    raise ValueError('untouched member %d changed' % mid)
                untouched += 1
    return {'art_members_verified': checked, 'untouched_members_identical': untouched}


# ------------------------------------------------------------------ plan ---
def plan(settings=None, catalog=None):
    """Art member replacement set for AIDDATAPACK.CPK.

    Returns {'members': {1: bytes}, 'sources', 'intended', 'rects',
    'source_path', 'report'}. Store member 1 CRILAYLA-compressed
    (cpkpatch.build(..., compress={1})); see docs/ART_AIDDATA.md."""
    settings = settings or _settings()
    catalog = catalog if catalog is not None else load_catalog()
    path = source_path(settings)
    blob = source_member(settings)
    data, intended, rects, cells = member_art(blob, catalog)
    verify_member(blob, data, intended, rects)
    report = {'schema': 1, 'archive': ARCHIVE, 'runtime_verified': False,
              'members': {ART_MEMBER: {'input_sha256': sha256(blob), 'output_sha256': sha256(data)}},
              'textures_changed': sorted(k[1] for k in intended),
              'reused_jigoku': len(cells['reused_jigoku']), 'rendered': len(cells['rendered']),
              'kept': len(cells['kept']), 'cells': cells['cells']}
    return {'members': {ART_MEMBER: data}, 'sources': {ART_MEMBER: blob},
            'intended': {ART_MEMBER: intended}, 'rects': {ART_MEMBER: rects},
            'source_path': path, 'report': report}


# ------------------------------------------------------------ Jigoku asset ---
def extract_jigoku(settings, apply=False):
    """Pack the Jigoku 0.6.24 pixels of every JIGOKU_CELLS rectangle into
    one PNG (cells stacked vertically) with a hash sidecar.

    Accepted only when Jigoku's original member 1 has the recorded hash,
    its shipped member 1 differs from it ONLY inside JIGOKU_CELLS, and the
    Tengoku source equals Jigoku's original inside every cell."""
    from PIL import Image
    blobs = {}
    for label, path, want in (('original', JIGOKU_ORIGINAL, JIGOKU_M1_ORIGINAL),
                              ('shipped', JIGOKU_SHIPPED, JIGOKU_M1_SHIPPED)):
        with CPK(path) as archive:
            blobs[label] = archive.read(next(e for e in archive.files if e['id'] == ART_MEMBER))
        if sha256(blobs[label]) != want:
            raise ValueError('Jigoku %s member 1 is not the recorded file' % label)
    tengoku = source_member(settings)
    dec = {k: [gtf.decode(b, t) for t in atlas_textures(b)] for k, b in blobs.items()}
    ours = [gtf.decode(tengoku, t) for t in atlas_textures(tengoku)]
    for ti in range(4):
        inside = np.zeros((SIZE, SIZE), bool)
        for t2, rect, _en, _mod in JIGOKU_CELLS.values():
            if t2 == ti:
                inside[rect[1]:rect[3], rect[0]:rect[2]] = True
        changed = (dec['original'][ti] != dec['shipped'][ti]).any(-1)
        if (changed & ~inside).any():
            raise ValueError('Jigoku changed texture %d outside its recorded cells' % ti)
    rows, y, width = {}, 0, max(r[2] - r[0] for _t, r, _e, _m in JIGOKU_CELLS.values())
    for cid, (ti, rect, en, module) in JIGOKU_CELLS.items():
        src = rect_sha(dec['original'][ti], rect)
        if src != rect_sha(ours[ti], rect):
            raise ValueError('Tengoku source differs from Jigoku original in %s' % cid)
        rows[cid] = {'texture': ti, 'rect': list(rect), 'asset_y': y, 'en': en, 'module': module,
                     'source_sha256': src, 'shipped_sha256': rect_sha(dec['shipped'][ti], rect)}
        y += rect[3] - rect[1]
    sheet = np.zeros((y, width, 4), np.uint8)
    for cid, row in rows.items():
        x0, y0, x1, y1 = row['rect']
        sheet[row['asset_y']:row['asset_y'] + y1 - y0, :x1 - x0] = rect_pixels(dec['shipped'][row['texture']], row['rect'])
    meta = {'source': str(JIGOKU_SHIPPED), 'original': str(JIGOKU_ORIGINAL), 'member': ART_MEMBER,
            'original_member_sha256': JIGOKU_M1_ORIGINAL, 'shipped_member_sha256': JIGOKU_M1_SHIPPED,
            'tengoku_member_sha256': M1_SHA256,
            'about': 'Jigoku 0.6.24 pixels of each cell, stacked at asset_y (left aligned). '
                     'Tengoku source pixels equal Jigoku original in every cell.',
            'cells': rows}
    print('Jigoku cells: %d, all with Tengoku == Jigoku original; shipped changes stay inside them'
          % len(rows))
    if apply:
        ASSETS.mkdir(parents=True, exist_ok=True)
        gtf.to_image(sheet).save(JIGOKU_ASSET)
        write_json(JIGOKU_ASSET.with_suffix('.json'), meta)
        jigoku_cells()
        print('wrote %s' % JIGOKU_ASSET)
    return meta


# --------------------------------------------------------------- inventory ---
def _kind(data):
    head = data[:4]
    if head == b'FSSA':
        return 'FSSA UI layout + cp932 string pool (EBOOT hook path)'
    if head in (b'SB2T', b'UB2T'):
        return '%s string table (%s)' % (head.decode(), 'cp932' if head == b'SB2T' else 'UTF-8')
    if bytes(head) in gtf.VERSIONS:
        return 'GTF texture'
    return 'binary layout / text record'


def _japanese_strings(data, encoding='cp932'):
    count, i = 0, 0
    while i < len(data):
        if data[i] >= 0x81:
            end = data.find(b'\0', i)
            if end < 0:
                break
            try:
                text = data[i:end].decode(encoding)
                if any(ord(c) >= 0x3000 for c in text):
                    count += 1
            except UnicodeDecodeError:
                pass
            i = end
        i += 1
    return count


def inventory(settings, apply=False):
    """inventory.json + contact sheets in work/ui/textures/aiddata/."""
    from PIL import Image, ImageDraw
    path = source_path(settings)
    ours = decoded_members(path, CACHE)
    jig = decoded_members(JIGOKU_ORIGINAL, ROOT / 'work/tengoku/cache/aiddata_jorig')
    jig_sha = {}
    for jid, data in jig.items():
        jig_sha.setdefault(sha256(data), []).append(jid)
    catalog = load_catalog() if CATALOG.exists() else {'cells': {}}
    members = []
    with CPK(path) as archive:
        stored = {e['id']: e for e in archive.files}
    for mid, data in sorted(ours.items()):
        row = {'id': mid, 'stored_bytes': stored[mid]['size'], 'bytes': len(data),
               'crilayla': stored[mid]['size'] != stored[mid]['extract'], 'kind': _kind(data),
               'sha256': sha256(data), 'jigoku_identical': jig_sha.get(sha256(data), [])}
        if row['kind'] == 'GTF texture':
            tex = gtf.textures(data)
            row['textures'] = ['%dx%d %s' % (t['width'], t['height'], gtf.FORMATS.get(t['fmt'], hex(t['fmt'])))
                               for t in tex]
            if mid == ART_MEMBER:
                row['japanese_art'] = 'yes: textures 0, 2, 3 (see aiddata_art.json)'
            elif all(not gtf.decode(data, t)[..., :3].any() for t in tex if t['fmt'] in gtf.WRITABLE):
                row['japanese_art'] = 'no (all black)'
            else:
                row['japanese_art'] = 'no (background illustration)'
        else:
            enc = 'utf-8' if data[:4] == b'UB2T' else 'cp932'
            row['japanese_strings'] = _japanese_strings(data, enc)
            row['japanese_art'] = 'no (text/layout data, not art)'
        members.append(row)
    found = {
        'pp_screen_tabs': {
            'where': 'member 0 (FSSA) text, not art',
            'evidence': 'cp932 strings パラメータ/上昇/スキル/修得 four times at 0x59c50..0x59cca '
                        '(two-line tab captions, one set per tab state), followed by システム設定１/２. '
                        'Jigoku has the same block at 0x6342c and translated it as hook text '
                        '(ui_hook "Raise Stats" / "Learn Skills"), not as a texture.'},
        'menu_headers': {
            'where': 'member 0 (FSSA) text, plus the art headings of member 1',
            'evidence': '71 【…】 headers in member 0, e.g. 【機体一覧】 0x5d772, 【パイロット養成】 0x5d7c8, '
                        '【Ｄトレーダー：購入】 0x58fca (drawn by the font through the EBOOT hook path). '
                        'The only headings that are images are in member 1: インターミッション, サブオーダー '
                        '(t0), 主人公設定, シナリオ選択, 本編/ガイダンス/シナリオ, ゲーム/スタート, '
                        'データをリンクさせて (t2).'},
    }
    report = {'schema': 1, 'archive': ARCHIVE, 'members': members, 'located': found,
              'member1_cells': {s: sum(1 for c in catalog['cells'].values() if c['source'] == s)
                                for s in SOURCES}}
    if not apply:
        return report
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    write_json(PREVIEWS / 'inventory.json', report)
    blob = ours[ART_MEMBER]
    tex = atlas_textures(blob)
    colours = {'jigoku-0.6.24': (80, 200, 255), 'new': (255, 210, 60), 'keep': (160, 160, 160)}
    for t in tex:
        image = gtf.preview(gtf.decode(blob, t), (40, 0, 40)).resize((SIZE * 2, SIZE * 2), Image.NEAREST)
        draw = ImageDraw.Draw(image)
        for cid, cell in catalog['cells'].items():
            if cell['texture'] != t['index']:
                continue
            x0, y0, x1, y1 = cell['rect']
            draw.rectangle([x0 * 2, y0 * 2, x1 * 2 - 1, y1 * 2 - 1], outline=colours[cell['source']])
            draw.text((x0 * 2 + 3, y0 * 2 + 1), cid.split('.', 1)[1], fill=colours[cell['source']])
        image.save(PREVIEWS / ('aid_m001_t%d_cells.png' % t['index']))
    shipped = decoded_members(JIGOKU_SHIPPED, ROOT / 'work/tengoku/cache/aiddata_jship', {ART_MEMBER})[ART_MEMBER]
    sheet = Image.new('RGB', (SIZE * 3 + 40, 4 * (SIZE + 24) + 10), (16, 16, 24))
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(tex):
        y = 10 + i * (SIZE + 24)
        for j, (label, b) in enumerate((('Tengoku', blob), ('Jigoku original', jig[ART_MEMBER]),
                                        ('Jigoku 0.6.24', shipped))):
            x = 10 + j * (SIZE + 10)
            draw.text((x, y), 't%d %s' % (t['index'], label), fill=(255, 255, 160))
            sheet.paste(gtf.preview(gtf.decode(b, atlas_textures(b)[i]), (40, 0, 40)), (x, y + 14))
    sheet.save(PREVIEWS / 'aid_m001_vs_jigoku.png')
    thumbs = [m for m in members if m['kind'] == 'GTF texture' and m['id'] != ART_MEMBER]
    sheet = Image.new('RGB', (4 * 330 + 10, ((len(thumbs) + 3) // 4) * 200 + 10), (16, 16, 24))
    draw = ImageDraw.Draw(sheet)
    for i, m in enumerate(thumbs):
        data = ours[m['id']]
        t = gtf.textures(data)[0]
        img = gtf.preview(gtf.decode(data, t))
        img.thumbnail((320, 180))
        x, y = 10 + (i % 4) * 330, 10 + (i // 4) * 200
        sheet.paste(img, (x, y + 14))
        draw.text((x, y), 'm%03d %s  %s' % (m['id'], m['textures'][0], m['japanese_art']), fill=(255, 255, 160))
    sheet.save(PREVIEWS / 'aid_other_textures.png')
    return report


# ----------------------------------------------------------------- preview ---
def preview(settings, apply=False):
    """Before/after sheets of every painted cell and of the whole textures."""
    from PIL import Image, ImageDraw
    art = plan(settings)
    blob, built = art['sources'][ART_MEMBER], art['members'][ART_MEMBER]
    catalog = load_catalog()
    tex = atlas_textures(blob)
    before = [gtf.decode(blob, t) for t in tex]
    after = [gtf.decode(built, t) for t in tex]
    cells = [(cid, c) for cid, c in sorted(catalog['cells'].items(), key=lambda kv: (kv[1]['texture'], kv[1]['rect'][1], kv[1]['rect'][0]))
             if c['source'] != 'keep']
    scale = 2
    col_w = 2 * 300 * scale // 2 + 30
    heights = [(c['rect'][3] - c['rect'][1]) * scale + 18 for _cid, c in cells]
    half = (len(cells) + 1) // 2
    sheet_h = max(sum(heights[:half]), sum(heights[half:])) + 40
    sheet = Image.new('RGB', (2 * (2 * 300 * scale + 40), sheet_h), (16, 16, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 6), 'AIDDATAPACK member 1 cells: original | English (2x, on dark). blue = Jigoku 0.6.24 reuse, '
                      'yellow = rendered', fill=(255, 255, 160))
    y_cols, x_cols = [30, 30], [6, 2 * 300 * scale + 46]
    for i, (cid, c) in enumerate(cells):
        col = 0 if i < half else 1
        x, y = x_cols[col], y_cols[col]
        x0, y0, x1, y1 = c['rect']
        w, h = (x1 - x0) * scale, (y1 - y0) * scale
        colour = (80, 200, 255) if c['source'] == 'jigoku-0.6.24' else (255, 210, 60)
        draw.text((x, y), '%s -> %s' % (cid, c['en']), fill=colour)
        for k, src in enumerate((before, after)):
            img = gtf.preview(rect_pixels(src[c['texture']], c['rect']), (24, 28, 40)).resize((w, h), Image.NEAREST)
            sheet.paste(img, (x + k * (300 * scale + 10), y + 14))
        y_cols[col] += h + 18
    target = PREVIEWS / 'aid_m001_cells_before_after.png'
    targets = [target]
    if apply:
        PREVIEWS.mkdir(parents=True, exist_ok=True)
        sheet.save(target)
        for t in tex:
            if t.key in art['intended'][ART_MEMBER]:
                pair = Image.new('RGB', (2 * SIZE + 10, SIZE), (16, 16, 24))
                pair.paste(gtf.preview(before[t['index']], (40, 0, 40)), (0, 0))
                pair.paste(gtf.preview(after[t['index']], (40, 0, 40)), (SIZE + 10, 0))
                name = PREVIEWS / ('aid_m001_t%d_before_after.png' % t['index'])
                pair.save(name)
                targets.append(name)
    return targets, art['report']


# ------------------------------------------------------------------- CLI ---
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['plan', 'catalog', 'inventory', 'preview', 'jigoku'])
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    settings = _settings()
    if a.command == 'jigoku':
        extract_jigoku(settings, a.apply)
    elif a.command == 'catalog':
        _catalog, counts = build_catalog(settings, a.apply)
        print(json.dumps(counts))
        print('wrote %s' % CATALOG if a.apply else 'DRY RUN: pass --apply to write %s' % CATALOG)
    elif a.command == 'inventory':
        report = inventory(settings, a.apply)
        for m in report['members']:
            print('m%03d %-58s %s' % (m['id'], m['kind'][:58], m['japanese_art']))
        print('wrote %s' % PREVIEWS if a.apply else 'DRY RUN: pass --apply to write %s' % PREVIEWS)
    elif a.command == 'preview':
        targets, report = preview(settings, a.apply)
        for cid, info in report['cells'].items():
            if info['source'] == 'new':
                print('%-24s %-16s %s' % (cid, info['en'], json.dumps({k: v for k, v in info.items()
                                                                        if k in ('squeeze', 'font_px', 'ink')})))
        print('wrote %s' % ', '.join(str(t) for t in targets) if a.apply else
              'DRY RUN: pass --apply to write previews')
    else:
        art = plan(None)
        print(json.dumps({k: v for k, v in art['report'].items() if k != 'cells'}, indent=2))
        print('art members: %s (dry run; game_build writes the archive)' % sorted(art['members']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
