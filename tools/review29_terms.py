"""Preview/apply source-aware Spirit terms and canonical Inazuma Kick."""
import argparse,json,re
from tools.common import ROOT,write_json,sha256_file
DEST=ROOT/'work/ui/review29_term_audit.json'
SOURCE='https://www.akurasu.net/wiki/Super_Robot_Wars/Z3/Spirits'

def plan():
    outputs={};changes=[]
    paths=sorted({p for family in ('ui','dialogue','library','voice','voice_text')
        for p in (ROOT/'work/translation/en'/family).rglob('*.json')})
    paths += [ROOT/'work/glossary/glossary.json',ROOT/'work/glossary/library_terms.json']
    for path in paths:
        data=json.loads(path.read_text(encoding='utf8'));edits=[]
        def walk(obj,trail='',source=''):
            if isinstance(obj,dict):
                source=obj.get('jp',source)
                for key,value in list(obj.items()):
                    if key in ('en','DSCR','DSC2','ROFN','ROSN','WORD') and isinstance(value,str):
                        new=re.sub(r'\bLightning Kick\b','Inazuma Kick',value)
                        if path.name=='eboot.json':
                            if '闘志' in source:new=re.sub(r'\bFighting Spirit\b','Fury',new)
                            if '直撃' in source:new=re.sub(r'\bFury\b','Break',new)
                        elif path.name=='menus.json':
                            if 'Fighting Spirit' in value:
                                new=re.sub(r'\b(?:Fighting Spirit|Fury)\b',lambda m:
                                    {'Fighting Spirit':'Fury','Fury':'Break'}[m[0]],new)
                            elif '/d8a9fc66933d022fac52/' in trail+'/':new=re.sub(r'\bFury\b','Break',new)
                        if path.name=='glossary.json' and obj.get('kind')=='spirit':
                            if source=='闘志':new='Fury'
                            elif source=='直撃':new='Break'
                        if new!=value:
                            obj[key]=new;edits.append(dict(field=trail+'/'+key,old=value,new=new))
                    elif isinstance(value,(dict,list)):walk(value,trail+'/'+key,key)
            elif isinstance(obj,list):
                for i,value in enumerate(obj):walk(value,trail+'/'+str(i),source)
        walk(data)
        if path.name=='spirit_commands.json':
            for row in data['entries']:
                if row['occurrence_id']=='rpw:0:spirit:3:abbreviation':new='Fy'
                elif row['occurrence_id']=='rpw:0:spirit:24:abbreviation':new='Br'
                else:continue
                old=row['en']
                if old!=new:
                    row['en']=new;edits.append(dict(field=row['occurrence_id'],old=old,new=new))
        if edits:
            outputs[path]=data;changes.append(dict(file=path.relative_to(ROOT).as_posix(),
                source_sha256=sha256_file(path),edits=edits))
    return dict(schema=1,version='0.5.29',source=SOURCE,
        canonical_spirits={'闘志':'Fury','直撃':'Break'},canonical_weapon='Inazuma Kick',
        changes=changes,runtime_verified=False),outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    report,outputs=plan()
    for file in report['changes']:
        print(file['file'])
        for row in file['edits']:print(row['field'],repr(row['old'])[:110],'->',repr(row['new'])[:110])
    print('Changed files:',len(outputs))
    if not a.apply:print('DRY RUN: no data changed.');return
    for path,data in outputs.items():write_json(path,data)
    if outputs:write_json(DEST,report)

if __name__=='__main__':main()
