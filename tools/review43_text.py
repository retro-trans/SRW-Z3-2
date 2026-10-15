"""Source-bound phase, map-panel, article and command corrections."""
import argparse,json,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,status_layout as S
from tools.ui_coverage import member,ui_string_table

DEST=ROOT/'work/translation/en/ui/review43_layout.json'


def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']}
    edits=[]
    for at,jp,en in ((0x8a144,'搭載中','Aboard:'),(0x8a164,'チ　ム：',''),(0x8a184,'ー','')):
        row=widgets[at]
        if row['text']!=jp:raise ValueError('Map aboard source changed')
        edits.append(dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),font_style='native-label',
            notes='One Aboard caption; retain the separately drawn live team count and native state.'))
    from tools import native_labels as N
    left=640+struct.unpack_from('>f',source,0x8a148)[0]*640
    right=left+N.width('Aboard:',source[0x8a144+19])
    if right>835:raise ValueError('Aboard touches its live count')
    from tools.pipeline import config,verified_source
    from tools.aid_art import ARCHIVE
    sb=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),5);rows=ui_string_table(sb)
    prior=json.loads((ROOT/'work/translation/en/ui/expanded_fragments.json').read_text('utf8'))
    prefix=next(e for e in prior['table_fragments']if e['table_row_id']==3).copy()
    prefix.update(center_marker=True,notes='Center the complete composed sentence, including its native live count, by actual glyph widths.')
    tables=[prefix]
    terrain={91:'空',92:'陸',93:'水',94:'地',95:'空専用',96:'陸専用',97:'空水専用',98:'水専用',
             117:'空',118:'陸',119:'海',120:'宇'}
    for rid,jp in terrain.items():
        row=rows[rid]
        if row['text']!=jp:raise ValueError('Composed movement source changed')
        en=''.join(S.TERRAIN[c]for c in jp.replace('専用',''))
        if jp.endswith('専用'):en+=S.CELL['Only']
        tables.append(dict(table_row_id=rid,en=en,source_sha256=sha256(row['raw']),
            notes='Translate component cells before the game composes movement/rating text; preserve one native cell per terrain.'))
    return dict(schema=1,version='0.5.43',source_member_sha256=sha256(source),edits=edits,
        table_fragments=tables,aboard_bounds=dict(left=left,right=right,count_left=835),runtime_verified=False)


def corrections():
    out=[]
    path=ROOT/'work/translation/en/ui/expanded/help.json';data=json.loads(path.read_text('utf8'))
    row=data['strings']['879e79654d74f5106f5e']
    if row['en']not in ('Activate Trans-Am','Trans-Am'):raise ValueError('Command translation changed')
    row.update(en='Trans-Am',reviewed=True);out.append((path,data))
    changed=0
    for path in sorted((ROOT/'work/translation/en/dialogue').glob('*.json')):
        data=json.loads(path.read_text('utf8'));n=0
        for row in data.get('rows',{}).values():
            old=row['en'];new=old.replace('An $$テンシ$$','A $$テンシ$$').replace('an $$テンシ$$','a $$テンシ$$')
            if new!=old:row['en']=new;n+=1
        if n:out.append((path,data));changed+=n
    print('Tenshi article corrections:',changed)
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    layout=plan();changes=corrections();print(json.dumps(layout,ensure_ascii=True,indent=2))
    if a.apply:
        for path,data in changes:write_json(path,data)
        write_json(DEST,layout)
    else:print('DRY RUN: no data written.')

if __name__=='__main__':main()
