"""Preview/promote the bounded live-condition meaning review."""
import argparse,json,re
from collections import Counter
from tools.common import ROOT,write_json,sha256,sha256_file
from tools import mission_text as M,mission_display as D,library_build as L
SOURCE=ROOT/'work/output/scratch/review29-live-wording.json'
DEST=ROOT/'work/ui/review29_live_audit.json'

def plan():
    review=json.loads(SOURCE.read_text('utf8'));active=M.load();outputs={};changes=[]
    assert review['assigned_rows_examined']==25
    for digest,row in review['proposals'].items():
        jp=next(j for j in active['strings']if sha256(j.encode('utf8'))==digest)
        if active['strings'][jp]['en']not in (row['old_en'],row['new_en']):raise ValueError('Stale live wording')
        old,new=row['old_en'],row['new_en'];errors=[]
        M.validate(digest,jp,new,M.resolver(),errors)
        if errors:raise ValueError(errors)
        if old.count('\n')!=new.count('\n')or Counter(re.findall(r'\d+',old))!=Counter(re.findall(r'\d+',new)):
            raise ValueError('Live condition paragraphs/numbers changed')
        if Counter(M.TOKEN.findall(old))!=Counter(M.TOKEN.findall(new)):raise ValueError('Live condition names changed')
        wrapped=M.wrap_live(L.expand(new,M.resolver()),D.advance)
        changes.append(dict(source_sha256=digest,old=old,new=new,
            worst_bytes=M.live_budget(wrapped,D.advance)[0],rows=len(wrapped.split('\n'))))
        if active['strings'][jp]['en']!=new:
            active['strings'][jp]['en']=new;outputs[M.TRANSLATION]=active
        for path in M.NEW.glob('*.json'):
            data=json.loads(path.read_text('utf8'));answer=data.get('rows',{}).get(M.key(jp))
            if answer is None or answer.get('en')==new:continue
            if answer.get('en')!=old:raise ValueError('Stale live-condition answer')
            answer['en']=new;outputs[path]=data
    return dict(schema=1,version='0.5.29',review=review,changes=changes,
        input_sha256=sha256_file(SOURCE),runtime_verified=False),outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data,outputs=plan()
    for row in data['changes']:print(row['old'],'=>',row['new'],'worst bytes',row['worst_bytes'],'rows',row['rows'])
    print('Changed files:',[p.relative_to(ROOT).as_posix()for p in outputs])
    if not a.apply:print('DRY RUN: no live text changed.');return
    for path,data_out in outputs.items():write_json(path,data_out)
    if outputs or not DEST.exists():write_json(DEST,data)

if __name__=='__main__':main()
