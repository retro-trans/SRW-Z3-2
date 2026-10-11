"""Bind deployment and upgrade labels to their native value columns."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,native_labels as N
from tools.review19_layout import width

DEST=ROOT/'work/translation/en/ui/review24_layout.json'

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']}
    edits=[];bounds=[]
    def bind(at,jp,en,right=None,native=False,x=None):
        row=widgets[at]
        if row['text']!=jp:raise ValueError('Review 24 source changed: %#x'%at)
        edit=dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            notes='Preserve native colors, row pitch, numeric fields and upgrade bars.')
        if x is not None:edit['x']=(x-640)/640
        if native:edit['font_style']='native-label'
        if right is not None:
            left=x if x is not None else 640+struct.unpack_from('>f',source,at+4)[0]*640
            lines=en.split('\n');limits=right if isinstance(right,tuple)else (right,)*len(lines)
            for line,limit in zip(lines,limits):
                span=(N.width if native else width)(line,source[at+19])
                if left+span+6>limit:raise ValueError('Review 24 caption overlaps value/panel: '+line)
                bounds.append(dict(widget_offset=at,text=line,left=left,width=span,right=limit,gap=limit-left-span))
        edits.append(edit)
    # Both list variants share the same footer and upgrade columns.
    for at in (0x9ee24,0xa27c4):
        bind(at,'照準値\n武器','Accuracy\nWpn',right=(1003,940),native=True,x=863)
    for at in (0x9ee44,0xa27e4):
        bind(at,'ＲＡＮＫ','RANK',x=940,right=1017)
    for at in (0x9f3e4,0xa3ea4):
        bind(at,'機体改造度','Mech Upgrades',right=1060,native=True)
    for at in (0x9f404,0xa3ec4):
        bind(at,'武器改造度','Weapon Lv',right=1270,native=True)
    # Keep the original 48-pixel command pitch and native bullet icons.
    bind(0xab8a4,'\n・準備メニュー\n・作戦目的\n・マップ配置へ\n・途中セーブ',
         '\n・Prep Menu\n・Objectives\n・Map Deploy\n・Quick Save',right=278)
    bind(0x9a5c4,'ＳＲポイント\n出撃チーム','SR Pts\nTeams',right=165.5,native=True)
    # The caption already identifies teams. Suppress the redundant suffix,
    # which would otherwise cross the narrow panel after a two-digit count.
    bind(0x9a604,'隊','')
    return dict(schema=1,version='0.5.24',source_member_sha256=sha256(source),
        edits=edits,bounds=bounds,numeric_coordinates_changed=False,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),repr(e['en']),e.get('font_style'))
    print('Minimum panel/value gap:',min(b['gap']for b in data['bounds']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
