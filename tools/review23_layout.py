"""Short deployment captions and all repeated fixed movement templates."""
import argparse,re,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,status_layout as S,native_labels as N

DEST=ROOT/'work/translation/en/ui/review23_layout.json'

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits=[]
    def bind(at,en,native=False,x=None):
        row=widgets[at]
        e=dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            notes='Preserve live counts, row spacing, movement flag masks and native colors.')
        if native:e['font_style']='native-label'
        if x is not None:e['x']=(x-640)/640
        edits.append(e)
    for at in (0x9e4a4,0xa2024):bind(at,'Deploy Teams')
    bind(0xa2044,'Left:',native=True)
    bind(0xa31c4,'Sel.',native=True)
    bind(0xa4be4,'MV\nMV',native=True)
    # Multi-row templates were missed by the earlier one-row terrain filter.
    movement=[]
    for at,row in widgets.items():
        text=row['text']
        if '空陸水地' in text and '\n' in text and re.fullmatch(r'[空陸水地\n\u3000]+',text):
            bind(at,''.join(S.TERRAIN.get(c,c)for c in text));movement.append(at)
    if set(movement)!={0xa3644,0xa37e4,0xa3c24,0xa44c4,0xa4c24,0xac804,0xac864}:
        raise ValueError('Repeated movement template coverage changed')
    left=640+struct.unpack_from('>f',source,0xa2044+4)[0]*640
    gap=439.5-left-N.width('Left:',source[0xa2044+19])
    if gap<10:raise ValueError('Remaining count overlaps its caption')
    return dict(schema=1,version='0.5.23',source_member_sha256=sha256(source),edits=edits,
                repeated_movement_widgets=movement,remaining_count_gap=gap,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),repr(row['en']),row.get('font_style'))
    print('Remaining count gap:',data['remaining_count_gap'])
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no data written.')

if __name__=='__main__':main()
