"""Preview/apply the user's Emperor Zuul spelling throughout active text."""
import argparse,json,re
from tools.common import ROOT,sha256_file,write_json

FIELDS={'en','DSCR','DSC2','CHFN','CHSN','ROFN','ROSN','WORD','position','personality','nickname'}
NOTE='User 2026-10-13: canonical Zuul / Emperor Zuul; proofreading must preserve this spelling.'
DEST=ROOT/'work/ui/review27_name_audit.json'

def corrected(text):return re.sub(r'\b(?:Xul|Zul)\b','Zuul',text)

def plan():
    changes=[];outputs={};examined=0
    paths=sorted({p for family in ('dialogue','library','ui','voice_text')
                  for p in (ROOT/'work/translation/en'/family).rglob('*.json')})
    paths += [ROOT/'work/glossary'/f for f in ('library_terms.json','library_settled.json','library_characters.json')]
    paths += sorted((ROOT/'work/glossary/research').glob('*.json'))
    for path in paths:
        data=json.loads(path.read_text(encoding='utf8'));local=[]
        def visit(obj,trail=''):
            nonlocal examined
            if isinstance(obj,dict):
                for key,value in list(obj.items()):
                    if key in FIELDS and isinstance(value,str):
                        examined+=1;new=corrected(value)
                        if new!=value:
                            obj[key]=new;local.append(dict(field=trail+'/'+key,old=value,new=new))
                            if key=='en'and 'work/glossary' in path.relative_to(ROOT).as_posix():
                                obj.update(source=NOTE,status='confirmed',user_approved=True,override_approved=True)
                    elif isinstance(value,(dict,list)):visit(value,trail+'/'+key)
            elif isinstance(obj,list):
                for i,value in enumerate(obj):visit(value,trail+'/'+str(i))
        visit(data)
        if local:
            outputs[path]=data;changes.append(dict(file=path.relative_to(ROOT).as_posix(),
                source_sha256=sha256_file(path),changes=local))
    return dict(schema=1,version='0.5.27',fields_examined=examined,replacement='Zuul',
                files_changed=len(outputs),changes=changes,historical_exports_modified=False),outputs

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();report,outputs=plan()
    print('Fields examined:',report['fields_examined'],'files changed:',len(outputs))
    for file in report['changes']:
        print(file['file'])
        for row in file['changes']:print(row['field'],repr(row['old'])[:160],'->',repr(row['new'])[:160])
    if not a.apply:print('DRY RUN: no data written.');return
    for path,data in outputs.items():
        if path.name=='library_settled.json':
            lines=path.read_text(encoding='utf8').splitlines()
            for i,line in enumerate(lines):
                if not line.lstrip().startswith('{"jp":'):continue
                old=json.loads(line.strip().rstrip(','))
                if corrected(old.get('en',''))==old.get('en',''):continue
                new=next(t for t in data['terms']if t.get('jp')==old.get('jp')and t.get('token')==old.get('token'))
                lines[i]='    '+json.dumps(new,ensure_ascii=False)+(','if line.rstrip().endswith(',')else '')
            text='\n'.join(lines)+'\n'
            if json.loads(text)!=data:raise ValueError('Compact glossary readback differs')
            path.write_bytes(text.encode('utf8'))
        else:write_json(path,data)
    if outputs:write_json(DEST,report)

if __name__=='__main__':main()
