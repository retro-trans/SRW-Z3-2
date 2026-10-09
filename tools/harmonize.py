# Give every record the English of the first record (in play order) with identical Japanese.
import json,glob,io,os,sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from tools import dialogue as dlg
apply='--apply' in sys.argv
rows=dlg.plan_rows()
order=[r['id'] for r in rows]
jp={r['id']:(dlg.chapter(r['stage']),r['jp']) for r in rows}  # same scene group only
files={}; en={}
for p in glob.glob('work/translation/en/dialogue/*.json'):
    d=json.load(io.open(p,encoding='utf-8')); files[p]=d
    for k,e in d['rows'].items(): en[k]=(p,e)
first={}
for k in order:
    if k in en and jp[k] not in first: first[jp[k]]=k
changed=set(); n=0
for k in order:
    if k not in en: continue
    src=first[jp[k]]
    if src!=k and en[src][1]['en']!=en[k][1]['en']:
        n+=1
        if n<=8: print(k,'<-',src,'|',en[src][1]['en'].replace('\n',' ')[:80])
        if apply:
            en[k][1]['en']=en[src][1]['en']; changed.add(en[k][0])
print('rows to harmonize:',n,'files:',len(changed))
if apply:
    for p in changed: json.dump(files[p],io.open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
