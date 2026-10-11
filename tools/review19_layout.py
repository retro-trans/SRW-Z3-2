"""Source-bound Link and reward captions, preserving separate value widgets."""
import argparse
import struct
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U
from tools.ui_description_layout import advance

DEST = ROOT/'work/translation/en/ui/review19_layout.json'


def width(text, quad=28):
    return sum(map(advance, text))*quad/32


def plan():
    source = B.source()
    widgets = {a:r for r in U.fssa_strings(source) for a in r['widget_offsets']}
    edits = []
    def bind(at, en, **fields):
        row = widgets[at]
        edits.append(dict(widget_offset=at, en=en,
            source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            notes='Short source-bound caption; preserve the separate values, states and row pitch.',
            **fields))
    def left(at, en, x):
        bind(at,en,x=(x-640)/640,mode=source[at+23]&~0x40)
    for at,row in widgets.items():
        jp = row['text']
        if jp.startswith('クリア周回') and jp.endswith('シナリオチャート：'):
            bind(at,'Clears:\nChart:')
        elif jp=='ゲームクリア　　：':bind(at,'Game Clear:')
        elif jp=='周クリア':bind(at,'clears')
        elif jp=='周ｘ':bind(at,' x ')
        elif jp.startswith('●') and 'クリア' in jp or jp.startswith('●：'):
            en=jp.replace('●『時獄篇』クリア','●Jigoku-hen Clear').replace(
                '●『連獄篇』クリア','●Rengoku-hen Clear').replace(
                '●：シナリオ・コンプリート','●: Chart Complete').replace('●：周回ボーナス','●: Replay')
            if en!=jp:bind(at,en)
        elif 'ネットワークに保存されているシステムデータとリンク' in jp:
            bind(at,'Link network data\nLink & Start')
    # This header has two layers, not two independent award messages.
    # Place the colored subject and black remainder on a single measured line.
    subject, tail = 'SR Point', ' earned.'
    start = 639.5-(width(subject)+width(tail))/2
    for at in (0x8bfc4,0x99d64):left(at,tail,start+width(subject))
    for at in (0x8bfe4,0x99d84):left(at,subject,start)
    # The yellow number is its own native widget. Keep it; translate only
    # the white prefix and anchor it to the left of that unchanged number.
    left(0x99da4,'Bonus funds:',500-width('Bonus funds:',31))
    # The same layout is used for Z Chip awards with a runtime numeric token.
    left(0x8c004,'Z Chips:',500-width('Z Chips:',31))
    bind(0x9cd64,'Name')
    return dict(schema=1,version='0.5.19',source_member_sha256=sha256(source),
        edits=edits,clear_label_width=width('Clears:'),
        reward_subject_x=start,reward_tail_x=start+width(subject),
        live_value_coordinates_changed=False,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=plan()
    for r in data['edits']:print(hex(r['widget_offset']),repr(r['en']),r.get('x'))
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')


if __name__=='__main__':main()
