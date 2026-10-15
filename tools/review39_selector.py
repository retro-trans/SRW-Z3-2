"""One plural, centered Allies / Enemies label in both map-menu states."""
import argparse
import struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/review39_selector.json'
PAIRS=((0x978e4,0x97904),(0x97924,0x97944))
QUAD=26
PREFIX='Allies / '
SUFFIX='Enemies'


def plan():
    source=B.source();rows={a:r for r in U.fssa_strings(source) for a in r['widget_offsets']}
    expected=('味方部隊／','敵','味方','／敵部隊')
    prefix=sum(map(advance,PREFIX))*QUAD/32
    total=sum(map(advance,PREFIX+SUFFIX))*QUAD/32
    if total>216:raise ValueError('Side selector exceeds map command button')
    left=639.5-total/2;edits=[]
    for n,at in enumerate(a for pair in PAIRS for a in pair):
        row=rows[at]
        if row['text']!=expected[n]:raise ValueError('Map selector source changed')
        edits.append(dict(widget_offset=at,en=PREFIX if n%2==0 else SUFFIX,
            source_sha256=sha256(row['raw']),source_widget_sha256=sha256(source[at:at+32]),
            x=(left+(prefix if n%2 else 0)-640)/640,
            y=struct.unpack_from('>f',source,PAIRS[0][0]+8)[0],
            font_metrics=[QUAD,QUAD,QUAD-2,QUAD,QUAD],mode=source[at+23]&~0x40,
            notes='Same complete wording and measured positions in both choices; keep native blue/red and selection flags.'))
    return dict(schema=1,version='0.5.39',edits=edits,
        bounds=dict(center=639.5,left=left,right=left+total,width=total,prefix_width=prefix,
                    quad=QUAD,button_width=220,minimum_side_margin=(220-total)/2),runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),repr(e['en']),e['x'],e['font_metrics'])
    print(data['bounds'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')


if __name__=='__main__':main()
