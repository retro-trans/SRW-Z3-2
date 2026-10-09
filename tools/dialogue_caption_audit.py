"""Read-only caption layout audit, no dialogue text persisted."""
import json,re,argparse
from tools import dialogue as d
from tools import dialogue_retranslate as r
p=argparse.ArgumentParser();p.add_argument('--batches',type=int,nargs='+',default=list(range(1,13)));a=p.parse_args()
src={x['id']:x['jp'] for x in d.plan_rows()}
for b in a.batches:
 r.configure(b);n=0;bad=[]
 for path in sorted((r.RUN/'drafts').glob('*.json')):
  for rid,row in json.loads(path.read_text(encoding='utf-8'))['rows'].items():
   jp=src[rid];en=row['en']
   if jp.partition('\n')[0].strip():continue
   n+=1
   shape=lambda t:[re.findall('\u3000+',re.sub(r'\$\$[^$]+\$\$','TOKEN',x)) for x in t.split('\n')]
   if shape(jp)!=shape(en):
    bad.append(rid);print(json.dumps(dict(batch=b,file=path.name,id=rid,jp=jp,en=en),ensure_ascii=False),flush=True)
 print('Batch',b,'captions',n,'layout differences',len(bad),flush=True)

