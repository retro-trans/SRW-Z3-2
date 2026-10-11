"""Source-bound training and Z Crystal columns, preserving native values."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.review19_layout import width

DEST=ROOT/'work/translation/en/ui/review21_layout.json'
CRYSTALS=('Demon Eye of Lore','Undying Iron Chain','Dormant Dragon',
          'Gathering Spirit Q.','Greedy Gold Arm','Peerlessness Path',
          "War God's Rally","Divine Wind's Ward","Battle God's Hope")

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits=[]
    def bind(at,en,expected=None,x=None,quad=None,note='Fit English labels around unchanged values; preserve native row pitch and state.'):
        row=widgets[at]
        if expected is not None and row['text']!=expected:raise ValueError('Review21 widget source changed: %#x'%at)
        edit=dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
                  source_widget_sha256=sha256(source[at:at+32]),notes=note)
        if x is not None:edit['x']=(x-640)/640
        if quad is not None:
            metrics=list(source[at+16:at+21]);metrics[2]=quad-2;metrics[3]=quad
            edit['font_metrics']=metrics
        edits.append(edit)
    # Each native state has four text pieces. A single caption per button
    # gives an ordinary English word order and a measured visual center.
    tabs=[]
    for start in (0x96c24,0x96ca4,0x96d24,0x96da4):
        for delta,text,expected,center in ((0,'Raise Stats','パラメータ',726),(32,'','上昇',None),
                                          (64,'Learn Skills','スキル',1007),(96,'','修得',None)):
            x=None if center is None else center-width(text,31)/2
            bind(start+delta,text,expected,x=x)
            if text:tabs.append(dict(widget_offset=start+delta,text=text,left=x,width=width(text,31),center=center))
    bind(0x9e304,'Owned\nCost\nLeft','所持\n必要\n残り')
    bind(0x9e324,'PP\nPP\nPP','ＰＰ\nＰＰ\nＰＰ',x=176)
    # The first two rows use shared dynamic-origin widgets; the following
    # four have fixed origins. Restore normal glyphs in all native variants.
    for at,label in ((0x8ed84,'CQB'),(0x8eda4,'RNG'),(0x8ee44,'CQB'),(0x8ee64,'RNG'),
                     (0x9e164,'SKL'),(0x9e184,'DEF'),(0x9e1a4,'EVD'),(0x9e1c4,'HIT')):
        bind(at,label,quad=28)
    for at,label in ((0x9e1e4,'Air'),(0x9e204,'Grd'),(0x9e224,'Wtr'),(0x9e244,'Spc')):
        bind(at,label,quad=28)
    for at in (0x94ec4,0x95184):bind(at,'Cost','強化費用',x=1178)
    for at in (0x94ee4,0x951a4):bind(at,'Effect','効果名')
    # All nine names, including hidden Grade 5, fit before the four-digit
    # cost column. Both grouped and all-grades layouts retain native pitch.
    crystal_rows=[]
    for at,labels in ((0x94f24,CRYSTALS[:3]),(0x94f44,CRYSTALS[3:6]),
                      (0x94f64,CRYSTALS[6:]),(0xa9444,CRYSTALS)):
        bind(at,'\n'.join(labels),x=925,quad=24)
        for text in labels:
            span=width(text,24)
            if 925+span+12>1167.5:raise ValueError('Z Crystal name collides with cost: '+text)
            crystal_rows.append(dict(widget_offset=at,text=text,left=925,width=span,cost_left=1167.5,gap=1167.5-925-span))
    for text in ('Owned','Cost','Left'):
        if 71.5+width(text,28)+8>176:raise ValueError('Training PP label collides')
    if 176+width('PP',28)+8>239:raise ValueError('Training PP collides with amount')
    for text in ('CQB','RNG','SKL','DEF','EVD','HIT'):
        if 465.5+width(text,28)+8>555:raise ValueError('Training stat collides with value')
    for text in ('Air','Grd','Wtr','Spc'):
        if 481.5+width(text,28)+8>571:raise ValueError('Training terrain collides with rank')
    return dict(schema=1,version='0.5.21',source_member_sha256=sha256(source),edits=edits,
        tabs=tabs,crystal_rows=crystal_rows,crystal_names=list(CRYSTALS),
        proofreading=dict(reviewer='upgrade20_wording',examined=9,in_scope=9),
        numeric_coordinates_changed=False,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),repr(row['en']),row.get('x'),row.get('font_metrics'))
    print('Minimum effect/cost clearance:',min(row['gap']for row in data['crystal_rows']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
