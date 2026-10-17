"""Source-bound D-Command, palace caption, part name and narration fitting."""
import argparse
import json
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U
from tools.ui_description_layout import advance

VERSION = '0.5.45'
DEST = ROOT / 'work/translation/en/ui/review45_layout.json'
COMMANDS = ('Upper Field', 'Tension MAX', 'Keep Combo', 'Dimension Call', 'Revive Chance', 'Full Miracle')
FOOTER = {
    'ae8e934ffc4b1d6081d2': ('During this phase, the Combo Gauge,', 'For this phase, the Combo Gauge will not drop'),
    '23db5c6025b607a2f246': ('which normally falls if an attack fails to destroy an enemy, will not fall even if you fail to destroy one.', 'if an attack fails to destroy an enemy.'),
}
MENU_ID = '3d21025a378db270e22d'
NARRATION_ID = '684670dcfb9171831342'
NARRATION = "To honor the great contribution to the project's progress"
CAPTION_IDS = {'b6c0f0d117e01112db0f','1018d2c50157a31e5790','52253a6819f2dae028a2',
               '60b7d8788669b8045aa6','6233d9f88bdafb366cb4','db906cf4382c7491480c', MENU_ID}
PART_OLD, PART_NEW = 'Hyperdimensional Target Lock', 'Hyperdim. Target Lock'
CAPTION_ID = '628:t_1:3'
CAPTION = '　\n　　\n～ $$ラース・バビロン$$ Imperial Palace /\n$$霊子吸収システム$$ ～'


def help_changes():
    data = json.loads((ROOT / 'work/translation/en/ui/expanded/help.json').read_text('utf8'))
    out = {}
    for rid, row in data['strings'].items():
        if row['en'].lstrip('・　') in COMMANDS and row['en'].startswith(('・', '　')):
            name = row['en'][1:]
            out[rid] = ('・' + name, '　' + name)
    if len(out) != 6:
        raise ValueError('D-Command bullet caption inventory changed')
    return out


def menu_text(prefix):
    return '\n'.join(prefix + text for text in COMMANDS) + '\n'


def plan():
    source = B.source()
    row = next(r for r in U.fssa_strings(source) if 0x8d464 in r['widget_offsets'])
    edit = dict(widget_offset=0x8d464, en=menu_text('　'), blank_bullet=True,
        source_sha256=sha256(row['raw']), source_widget_sha256=sha256(source[0x8d464:0x8d484]),
        notes='Use the existing measurable 32-unit invisible prefix; preserve six rows, selection and disabled state.')
    bounds = []
    for text in COMMANDS:
        pixels = (32 + sum(map(advance, text))) * 28 / 32
        if pixels > 320:
            raise ValueError('D-Command caption exceeds its list')
        bounds.append(dict(text=text, width=pixels, available_pixels=320))
    for rid, (_, text) in FOOTER.items():
        pixels = sum(map(advance, text)) * 28 / 32
        if pixels > 900:
            raise ValueError('D-Command footer crosses the category label')
        bounds.append(dict(id=rid, text=text, width=pixels, available_pixels=900))
    part_width = sum(map(advance, PART_NEW)) * 28 / 32
    if 735 + part_width + 32 > 1120:
        raise ValueError('Part caption touches stock count')
    return dict(schema=1, version=VERSION, source_member_sha256=sha256(source), edits=[edit],
        help_captions={k:list(v) for k,v in help_changes().items()}, footer={k:list(v) for k,v in FOOTER.items()}, bounds=bounds,
        part=dict(english=PART_NEW, left=735, right=735+part_width, count_left=1120),
        narration=dict(id=NARRATION_ID, english=NARRATION, limit_units=800), runtime_verified=False)


def changes():
    out = []
    replacements = dict(help_changes(), **FOOTER)
    replacements[MENU_ID] = (menu_text('・'), menu_text('　'))
    for family in ('help', 'menus'):
        path = ROOT / 'work/translation/en/ui/expanded' / (family + '.json')
        data = json.loads(path.read_text('utf8')); changed = []
        for rid, (old, new) in replacements.items():
            if rid not in data['strings']: continue
            row = data['strings'][rid]
            if row['en'] not in (old, new): raise ValueError('UI wording changed: ' + rid)
            if row['en'] != new:
                row.update(en=new, reviewed=True); changed.append(rid)
        if changed: out.append((path, data)); print(family, changed)
    for name in ('rpw_names.json', 'rpw_new/r_part_00.json', 'upgrade_messages.json'):
        path = ROOT / 'work/translation/en/ui' / name
        raw = path.read_text('utf8')
        if PART_OLD in raw:
            data = json.loads(raw.replace(PART_OLD, PART_NEW)); out.append((path, data))
            print(name, PART_OLD, '->', PART_NEW)
    for path in sorted((ROOT / 'work/translation/en/dialogue').glob('*.json')):
        data = json.loads(path.read_text('utf8'))
        row = data.get('rows', {}).get(CAPTION_ID)
        if row is None: continue
        if row['en'] != CAPTION:
            if 'Imperial Palace' not in row['en'] or '$$霊子吸収システム$$' not in row['en']:
                raise ValueError('Palace caption source changed')
            print(CAPTION_ID, repr(row['en']), '->', repr(CAPTION))
            out.append((path, dict(data, rows=dict(data['rows'], **{CAPTION_ID:dict(row, en=CAPTION)}))))
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true'); args = p.parse_args()
    layout = plan(); edits = changes()
    print('Measured bounds:', layout['bounds'], layout['part'])
    if not args.apply: print('DRY RUN: no translation or layout data written.'); return
    for path, data in edits: write_json(path, data)
    write_json(DEST, layout)


if __name__ == '__main__': main()
