"""Preview/apply the user's Z3 Focus/Foc terminology in active UI sources."""
import argparse
import json
import re
from tools.common import ROOT,write_json,sha256

NOTE='User-selected Z3 terminology: Focus for the Ki stat; Foc in compact labels. Spirit Focus remains unchanged.'
MORALE=re.compile(r'(?<![A-Za-z])Morale(?![A-Za-z])',re.I)
# These UI rows continue a stat sentence across native row boundaries. Their
# adjacent source rows carry 気力; preserve controls and the existing line cut.
CONTINUED_IDS=frozenset(('89c880af023ab84e35b1','1ba10f7c8cc98f6f1473','be23afd1faf014a7c099'))


def wording(jp,en,compact=False):
    if '気力' not in jp:return en
    if compact or jp=='気力':return MORALE.sub('Foc',en)
    en=re.sub(r'\bMorale(?=\+)', 'Foc',en)
    return MORALE.sub(lambda m:'focus' if m.group().islower() else 'Focus',en)


def plan():
    from tools import ui_catalog
    # Bind hashed catalogue IDs to their actual source, not an English search.
    jp_by_id={sha256(r['text'].encode('utf8'))[:20]:r['text'] for r in ui_catalog.sources()}
    pending=[]
    for path in sorted((ROOT/'work/translation/en/ui/expanded').glob('*.json')):
        data=json.loads(path.read_text(encoding='utf8'));changes=[]
        for rid,row in data.get('strings',{}).items():
            en=row.get('en')
            if not isinstance(en,str):continue
            jp=jp_by_id.get(rid,'');new=wording('continued 気力 sentence' if rid in CONTINUED_IDS else jp,en)
            if new!=en:row['en']=new;row['terminology_note']=NOTE;changes.append((rid,en,new))
        if changes:pending.append((path,data,changes))
    ui=ROOT/'work/translation/en/ui'
    for name in ('eboot.json','rpw_names.json','spirit_commands.json','aiddata_art.json'):
        path=ui/name;data=json.loads(path.read_text(encoding='utf8'));changes=[]
        def walk(v,source='',location=''):
            if isinstance(v,list):
                for n,x in enumerate(v):walk(x,source,location+'/'+str(n))
            elif isinstance(v,dict):
                jp=v.get('jp',source);en=v.get('en')
                if isinstance(en,str):
                    new=wording(jp,en,compact=name=='rpw_names.json')
                    if new!=en:v['en']=new;v['terminology_note']=NOTE;changes.append((location,en,new))
                for k,x in list(v.items()):
                    if isinstance(x,(dict,list)):walk(x,k if '気力' in k else jp,location+'/'+k)
        walk(data)
        if changes:pending.append((path,data,changes))
    return pending


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();pending=plan()
    for path,data,changes in pending:
        print(path.relative_to(ROOT),len(changes),'changed English fields')
        for rid,old,new in changes[:3]:print(' ',rid,repr(old[:100]),'->',repr(new[:100]))
    print('TOTAL',sum(len(c)for p,d,c in pending))
    if args.apply:
        for path,data,changes in pending:write_json(path,data)
        write_json(ROOT/'work/glossary/ui_stats.json',dict(schema=1,terms=[dict(jp='気力',en='Focus',
            compact='Foc',kind='stat',status='user-selected',notes=NOTE,
            reference='E:/Projects/SRW Z3/translation/ui_hook.json: 気力 = Foc; ability_hook.json: Focus thresholds')]))
    else:print('DRY RUN: no translations or glossary written.')


if __name__=='__main__':main()
