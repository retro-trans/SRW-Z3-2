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
                for key,value in list(obj.items()):
                    if key=='en' and isinstance(value,str):
                        examined+=1;new=corrected(value)
                        if new!=value:
                            obj[key]=new;local.append(dict(field=trail+'/en',old=value,new=new))
                            if path.parent==ROOT/'work/glossary':obj['source']=NOTE
                        if path.parent==ROOT/'work/glossary' and new in REPLACEMENTS.values() and obj.get('jp')in ('ヒイロ・ユイ','クロウ・ブルースト'):
                            for field,wanted in [('status','confirmed'),('source',NOTE)]+(
                                [('user_approved',True),('override_approved',True)]if path.name=='library_settled.json'else []):
                                if obj.get(field)!=wanted:
                                    old=obj.get(field);obj[field]=wanted
                                    local.append(dict(field=trail+'/'+field,old=old,new=wanted))
                    elif isinstance(value,(dict,list)):visit(value,trail+'/'+key)
            elif isinstance(obj,list):
                for i,value in enumerate(obj):visit(value,trail+'/'+str(i))
        visit(data)
        if path.name=='library_settled.json':
            for jp,kind,token,en in [('ヒイロ・ユイ','pilot','ヒイロ・ユイ#pilot','Heero Yuy'),
                                      ('クロウ・ブルースト','pilot','クロウ・ブルースト','Crowe Bluest')]:
                if not any(t.get('token')==token for t in data['terms']):
                    row=dict(jp=jp,kind=kind,token=token,en=en,status='confirmed',source=NOTE,
                             user_approved=True,override_approved=True)
                    data['terms'].append(row);local.append(dict(field='/terms/'+str(len(data['terms'])-1),old=None,new=row))
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
        for row in file['changes']:print(row['field'],repr(row['old'])[:220],'->',repr(row['new'])[:220])
    if not a.apply:print('DRY RUN: no data written.');return
    if not outputs:raise ValueError('Canonical spellings already applied; preserve the original audit')
    for path,data in outputs.items():
        if path.name=='library_settled.json':
            # Preserve the hand-maintained one-term-per-line layout.
            text=path.read_text(encoding='utf8');lines=text.splitlines();seen=set()
            for i,line in enumerate(lines):
                if not line.lstrip().startswith('{"jp":'):continue
                old=json.loads(line.strip().rstrip(','));token=old.get('token')
                match=next((t for t in data['terms']if t.get('token')==token and t['jp']==old['jp']),None)if token else None
                if match:
                    seen.add(token)
                    if match!=old:lines[i]='    '+json.dumps(match,ensure_ascii=False)+(','if line.rstrip().endswith(',')else '')
            additions=[t for t in data['terms']if t.get('token')in ('ヒイロ・ユイ#pilot','クロウ・ブルースト')and t['token']not in seen]
            if additions:
                end=next(i for i,line in enumerate(lines)if line.strip()==']')
                last=end-1
                while not lines[last].strip():last-=1
                lines[last]=lines[last].rstrip(',')+','
                lines[end:end]=['    '+json.dumps(row,ensure_ascii=False)+(','if i<len(additions)-1 else '')for i,row in enumerate(additions)]
            new='\n'.join(lines)+'\n'
            if json.loads(new)!=data:raise ValueError('Compact glossary formatting changed data')
            path.write_bytes(new.encode('utf8'))
        else:write_json(path,data)
    dest=ROOT/'work/ui/review21_name_audit.json'
    if dest.exists():
        original=json.loads(dest.read_text(encoding='utf8'));original.setdefault('subsequent_passes',[]).append(report);report=original
    write_json(dest,report)

if __name__=='__main__':main()
