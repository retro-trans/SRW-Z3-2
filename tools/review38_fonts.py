"""Separate ordinary lettering from source-bound native outlined labels."""
import argparse
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U, native_labels as N

DEST = ROOT/'work/translation/en/ui/review38_fonts.json'
WORDS = {'タッグ': 'Team', '機体': 'Mech', '撃墜数': 'Kills'}


def plan():
    source = B.source()
    edits = []
    for row in U.fssa_strings(source):
        if row['text'] not in WORDS:
            continue
        for at in row['widget_offsets']:
            # Unit-list column headers, including their alternate pages.
            # Other uses of these words retain ordinary lettering.
            if not 0x9ef44 <= at <= 0xa42c4 or source[at+22:at+24] != b'\x31\0':
                continue
            en = WORDS[row['text']]
            size = source[at+19]
            width = N.width(en, size)
            if width > 100:
                raise ValueError('Native unit-list header exceeds its column')
            edits.append(dict(widget_offset=at, en=en, font_style='native-label',
                source_sha256=sha256(row['raw']),
                source_widget_sha256=sha256(source[at:at+32]),
                notes='Separate original Latin glyphs for this yellow unit-list heading; preserve coordinates, colors and metrics.'))
    if len(edits) != 19:
        raise ValueError('Unit-list header coverage changed: '+str(len(edits)))
    return dict(schema=1, version='0.5.38', edits=sorted(edits,key=lambda e:e['widget_offset']),
        original_latin_font_page=1, ordinary_outline_radius=0,
        ordinary_shapes_and_advances_unchanged=True, runtime_verified=False)


def merge(edits, additions):
    """Add font selection without discarding earlier geometry repairs."""
    by_widget = {e['widget_offset']:dict(e) for e in edits}
    for extra in additions:
        at = extra['widget_offset']
        previous = by_widget.get(at,{})
        if 'en' in previous and previous['en'] != extra['en']:
            raise ValueError('Font selection would change reviewed wording')
        by_widget[at] = dict(previous, **extra)
    return list(by_widget.values())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
    data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),e['en'],e['font_style'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')


if __name__=='__main__':main()
