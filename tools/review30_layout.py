"""Fit D-Trader and battleship captions around their unchanged live fields."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,native_labels as N
DEST=ROOT/'work/translation/en/ui/review30_layout.json'

def plan():
    source=B.source();widgets={at:r for r in U.fssa_strings(source)for at in r['widget_offsets']};edits=[];bounds=[]
    def bind(at,en,right=None,x=None):
        row=widgets[at];left=x if x is not None else 640+struct.unpack_from('>f',source,at+4)[0]*640
        edit=dict(widget_offset=at,en=en,font_style='native-label',source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),notes='Preserve native colors, row pitch, selection states and all separately drawn values.')
        if x is not None:edit['x']=(x-640)/640
        if right is not None:
            width=max(N.width(line,source[at+19])for line in en.split('\n'))
            if left+width+8>right:raise ValueError('Caption crosses adjacent field: '+en)
            bounds.append(dict(widget_offset=at,left=left,width=width,right=right,gap=right-left-width))
        edits.append(edit)
    # A single multiline widget shares a fixed colon column at x296.5.
    bind(0x95a64,'Move\nType\nHP\nEN\nArmor\nMob.\nAcc.\nRange\nTerr.\nOwned',right=296.5)
    bind(0x95ac4,'HP\nEN\nMove',right=155.5)
    # Allow the unchanged owned count its entire three-digit field.
    bind(0x95aa4,'items',x=428,right=615)
    bind(0x981e4,'Ship',right=850)
    bind(0x98204,'MV',right=916)
    bind(0x98224,'Pil.',right=994)
    bind(0x98244,'Sel.',right=415)
    bind(0x96a04,'Left:',x=1016,right=1103.5)
    bind(0x96a24,'Units',x=1168,right=1275)
    return dict(schema=1,version='0.5.30',source_member_sha256=sha256(source),edits=edits,
        bounds=bounds,numeric_coordinates_changed=False,runtime_verified=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),repr(row['en']),row.get('x'))
    print('Minimum gap:',min(r['gap']for r in data['bounds']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')
if __name__=='__main__':main()
