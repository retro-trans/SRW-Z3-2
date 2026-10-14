"""Normalize the proper location Earth Sphere throughout active English."""
import argparse,json,re
from tools.common import ROOT,write_json,sha256_file
DEST=ROOT/'work/ui/review30_term_audit.json'
def plan():
    outputs={};changes=[]
    paths=sorted({p for family in ('ui','dialogue','library','voice','voice_text')
        for p in (ROOT/'work/translation/en'/family).rglob('*.json')})
    paths += [ROOT/'work/glossary/glossary.json',ROOT/'work/glossary/library_terms.json']
    for path in paths:
        data=json.loads(path.read_text('utf8'));edits=[]
        def walk(obj,trail=''):
            if isinstance(obj,dict):
                for key,value in list(obj.items()):
                    if key in ('en','DSCR','DSC2','ROFN','ROSN','WORD')and isinstance(value,str):
                        new=re.sub(r'\bEarth\s+sphere\b','Earth Sphere',value)
                        if new!=value:
                            obj[key]=new;edits.append(dict(field=trail+'/'+key,old=value,new=new))
                    elif isinstance(value,(dict,list)):walk(value,trail+'/'+key)
            elif isinstance(obj,list):
                for i,value in enumerate(obj):walk(value,trail+'/'+str(i))
        walk(data)
        if edits:outputs[path]=data;changes.append(dict(file=path.relative_to(ROOT).as_posix(),source_sha256=sha256_file(path),edits=edits))
    return dict(schema=1,version='0.5.30',canonical_location='Earth Sphere',changes=changes),outputs
def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();report,outputs=plan()
    for row in report['changes']:
        print(row['file'])
        for e in row['edits']:print(e['field'],repr(e['old'])[:130],'->',repr(e['new'])[:130])
    print('Changed fields:',sum(len(r['edits'])for r in report['changes']))
    if not a.apply:print('DRY RUN: no data changed.');return
    for path,data in outputs.items():
        newline='\r\n'if b'\r\n'in path.read_bytes()else '\n'
        encoded=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n',newline)
        path.write_bytes(encoded.encode('utf8'))
    if outputs:write_json(DEST,report)
if __name__=='__main__':main()
