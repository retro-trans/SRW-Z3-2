"""Separate Team Setup from both native Next counter states."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.review19_layout import width
DEST=ROOT/'work/translation/en/ui/review25_layout.json'

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits=[];bounds=[]
    def bind(at,jp,en=None,x=None):
        row=widgets[at]
        if row['text']!=jp:raise ValueError('Team Setup widget source changed')
        edit=dict(widget_offset=at,source_sha256=sha256(row['raw']),source_widget_sha256=sha256(source[at:at+32]),notes='Preserve title size, color, counter contents and all movement field coordinates.')
        if en is not None:edit['en']=en
        if x is not None:edit['x']=(x-640)/640
        edits.append(edit)
    for title,next_,count in ((0xa48c4,0xa48e4,0xa4904),(0xa4d64,0xa4d84,0xa4da4)):
        bind(title,'タッグ編成','Team Setup')
        bind(next_,'ＮＥＸＴ．','Next:',227.5)
        bind(count,'１４',x=327.5)
        left=640+struct.unpack_from('>f',source,title+4)[0]*640
        gap=227.5-left-width('Team Setup',source[title+19])
        if gap<12 or 227.5+width('Next:',25)+12>327.5 or 327.5+2*source[count+20]+12>386:
            raise ValueError('Team Setup label/counter crosses its panel')
        bounds.append(dict(title=title,title_gap=gap,next_x=227.5,count_x=327.5,panel_right=386))
    return dict(schema=1,version='0.5.25',source_member_sha256=sha256(source),edits=edits,bounds=bounds,
                counter_shift_px=19,counter_values_changed=False,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),repr(row.get('en','<live count unchanged>')),row.get('x'))
    print('Minimum title gap:',min(row['title_gap']for row in data['bounds']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
