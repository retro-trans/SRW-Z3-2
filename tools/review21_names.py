"""Preview/apply user-approved full-name spellings across active English data."""
import argparse,json,re
from tools.common import ROOT,sha256_file,write_json

REPLACEMENTS={'Heero Yui':'Heero Yuy','Crowe Bluste':'Crowe Bluest'}
NOTE='User 2026-10-12: canonical spelling Heero Yuy / Crowe Bluest; proofreading agents must not change these names.'
FOLDERS=('dialogue','library','ui','voice_text')

def corrected(text):
    for old,new in REPLACEMENTS.items():
        text=re.sub(r'\b'+re.escape(old)+r'\b',new,text)
    return text

def plan():
    changes=[];outputs={};examined=0
    paths=sorted({p for folder in FOLDERS for p in (ROOT/'work/translation/en'/folder).rglob('*.json')})
    paths += [ROOT/'work/glossary'/f for f in ('library_terms.json','library_settled.json')]
    for path in paths:
        data=json.loads(path.read_text(encoding='utf8'));local=[]
        def visit(obj,trail=''):
            nonlocal examined
            if isinstance(obj,dict):
                for key,value in obj.items():
                    if key=='en' and isinstance(value,str):
                        examined+=1;new=corrected(value)
                        if new!=value:
                            obj[key]=new;local.append(dict(field=trail+'/en',old=value,new=new))
                            if path.parent==ROOT/'work/glossary':obj['source']=NOTE
                    elif isinstance(value,(dict,list)):visit(value,trail+'/'+key)
            elif isinstance(obj,list):
                for i,value in enumerate(obj):visit(value,trail+'/'+str(i))
        visit(data)
        if path.name=='rpw_names.json':
            for slot,wanted in {'pilot-nw:214:1':'Yuy','pilot-nw:215:1':'Yuy','pilot-nw:1022:1':'Bluest'}.items():
                row=data['slots'][slot];old=row['en']
                if old not in (wanted,{'Yuy':'Yui','Bluest':'Bluste'}[wanted]):raise ValueError('Unexpected bound surname: '+slot)
                if old!=wanted:
                    row['en']=wanted;row['source']=NOTE
                    local.append(dict(field='/slots/'+slot+'/en',old=old,new=wanted))
        if local:
            name=str(path.relative_to(ROOT)).replace('\\','/')
            outputs[path]=data;changes.append(dict(file=name,source_sha256=sha256_file(path),changes=local))
    return dict(schema=1,version='0.5.21',english_fields_examined=examined,files_changed=len(changes),
        replacements=REPLACEMENTS,changes=changes,
        historical_reference_and_prior_exports_modified=False,unrelated_Yui_names_preserved=True),outputs

def coverage():
    """Audit rendered player text, including names expanded from glossary tokens."""
    from collections import Counter
    from tools import dialogue_build as D,voice_build as V,library_build as L,eboot_text as E
    from tools.library_text import load_translations
    resolver=E.resolver();counts=Counter();hits=Counter()
    def examine(category,text):
        if not isinstance(text,str):return
        text=L.expand(text,resolver);counts[category]+=1
        for old,new in REPLACEMENTS.items():
            if re.search(r'\b'+re.escape(old)+r'\b',text):raise ValueError('Old player-visible spelling in '+category+': '+text[:160])
            hits[new]+=text.count(new)
    for row in D.translations().values():examine('dialogue',row['en'])
    for row in V.translations().values():examine('battle_voice',row['en'])
    entries,errors=load_translations()
    if errors:raise ValueError(errors)
    for table in entries.values():
        for _,entry in table.values():
            for key in ('DSCR','DSC2','CHFN','CHSN','ROFN','ROSN','WORD'):examine('library',entry.get(key))
    for row in E.load()['strings'].values():examine('executable_ui',row.get('en'))
    if any(not hits[name]for name in REPLACEMENTS.values()):raise ValueError('Corrected full names absent from active player text')
    return dict(fields_examined=dict(counts),corrected_full_name_occurrences=dict(hits),obsolete_player_spellings=0)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    report,outputs=plan()
    print('English fields examined:',report['english_fields_examined'],'files changed:',len(outputs))
    for file in report['changes']:
        print(file['file'],len(file['changes']))
        for row in file['changes'][:2]:print(row['field'],repr(row['old'][:220]),'->',repr(row['new'][:220]))
    if not a.apply:print('DRY RUN: no data written.');return
    if not outputs:raise ValueError('Canonical spellings already applied; preserve the original audit')
    for path,data in outputs.items():write_json(path,data)
    write_json(ROOT/'work/ui/review21_name_audit.json',report)

if __name__=='__main__':main()
