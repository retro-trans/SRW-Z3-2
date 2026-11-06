"""DLC dialogue identity, private 80-row context briefs and English-only authoring."""
import argparse,json,re
from functools import lru_cache
from tools.common import ROOT,sha256,write_json
from tools import dialogue as D,dlc
from tools.library_text import GLOSSARY,Resolver
from tools import library_build as L
from tools import dialogue_build as DB
from tools.ui_description_layout import advance
ANSWERS=ROOT/'work/translation/en/dlc'
BRIEFS=dlc.WORK/'briefs'
JAPANESE=re.compile('[\u3040-\u30ff\u4e00-\u9fff]')
CONDENSED_ID='DLC2306:3:t_1:3'
CONDENSED_SHA='716d9e394d'

@lru_cache(None)
def inventory():return json.loads((dlc.WORK/'inventory.json').read_text('utf8'))

def records(code,member):
 p=next(p for p in inventory()['packages']if p['code']==code);m=next(m for m in p['members']if m['id']==member)
 raw=(ROOT/m['path']).read_bytes()
 if sha256(raw)!=m['sha256']:raise ValueError('DLC source member changed')
 try:text=raw.decode('cp932')
 except UnicodeDecodeError:return []
 if '\0'in text:return []
 ident={}
 for ev in D.EVENT.finditer(text):
  for n,b in enumerate(D.BLOCK.finditer(ev.group(2))):ident[ev.start(2)+b.start()]=(ev.group(1),n)
 out=[]
 for b in D.BLOCK.finditer(text):
  event,n=ident.get(b.start(),(None,None));head=D.HEAD.search(text,max(0,b.start()-160),b.start())
  if event is None or head is None:continue
  jp=b.group(1).replace('\r\n','\n')
  out.append(dict(id=f'{code}:{member}:{event}:{n}',code=code,member=member,event=event,n=n,pid=head.group(4),
   wpos=head.group(1),face=int(head.group(2)),jp=jp,sha=D.digest(jp),start=b.start(1),end=b.end(1)))
 return out

@lru_cache(None)
def all_rows():
 return [r for p in sorted(inventory()['packages'],key=lambda p:p['code'])for m in p['members']for r in records(p['code'],m['id'])]

def jobs():
 result=[]
 for p in sorted(inventory()['packages'],key=lambda p:p['code']):
  rows=[r for r in all_rows()if r['code']==p['code']]
  for start in range(0,len(rows),80):
   selected=rows[start:start+80];stem=f"{p['code']}_{start:04d}_{start+len(selected):04d}"
   result.append(dict(stem=stem,code=p['code'],start=start,count=len(selected),rows=selected,
    context_before=rows[max(0,start-8):start],context_after=rows[start+len(selected):start+len(selected)+8]))
 return result

def export(plan):
 if BRIEFS.exists():raise ValueError('Preserve existing briefs')
 BRIEFS.mkdir(parents=True);ANSWERS.mkdir(parents=True,exist_ok=True)
 terms=json.loads(GLOSSARY.read_text('utf8'))['terms']
 for j in plan:
  source='\n'.join(r['jp']for r in j['rows']+j['context_before']+j['context_after'])
  glossary=[dict(token=t['token'],jp=t['jp'],en=t.get('en'),kind=t.get('kind'))for t in terms if t.get('en')and t['jp']in source]
  write_json(BRIEFS/(j['stem']+'.json'),dict(schema=1,**j,glossary=glossary))
 write_json(dlc.WORK/'translation_jobs.json',dict(schema=1,jobs=[{k:v for k,v in j.items()if k not in ('rows','context_before','context_after')}for j in plan]))

def answers():
 result={}
 for p in sorted(ANSWERS.glob('*.json')):
  for rid,row in json.loads(p.read_text('utf8')).get('rows',{}).items():
   if rid in result:raise ValueError('Duplicate DLC translation: '+rid)
   result[rid]=row
 return result

def check(complete=True):
 source={r['id']:r for r in all_rows()};active=answers();errors=[];rendered={};res=Resolver(json.loads(GLOSSARY.read_text('utf8'))['terms'])
 if set(active)-set(source):raise ValueError('Unexpected DLC translation IDs')
 if complete and set(active)!=set(source):raise ValueError('DLC dialogue coverage incomplete: '+str(len(source)-len(active)))
 for rid,row in active.items():
  r=source[rid]
  try:
   if row.get('sha')!=r['sha']or not row.get('en'):raise ValueError('Wrong source fingerprint or empty English')
   if rid==CONDENSED_ID and r['sha']!=CONDENSED_SHA:raise ValueError('Condensed profile source changed')
   if JAPANESE.search(D.TOKEN.sub('',row['en'])):raise ValueError('Japanese prose outside glossary tokens')
   measure=measure_for(rid);text=DB.render(row,r,res,measure)
   if sorted(D.CODES.findall(text))!=sorted(D.CODES.findall(r['jp'])):raise ValueError('Runtime control codes changed')
   if text.count('《')!=r['jp'].count('《')or text.count('》')!=r['jp'].count('》'):raise ValueError('Linked-term count changed')
   if bool(r['jp'].partition('\n')[0].strip('　 '))!=bool(text.partition('\n')[0].strip('　 ')):raise ValueError('Speaker/caption role changed')
   if r['jp'].partition('\n')[0].strip()and len(text.split('\n'))-1>3:raise ValueError('Speech exceeds three rows')
   if any(D.speech_units(line,lambda c:0 if c in '《》'else measure(c))>D.BOX_UNITS for line in text.split('\n')[1:]if r['jp'].partition('\n')[0].strip()):raise ValueError('Speech exceeds measured row width')
   rendered[rid]=text
  except (ValueError,KeyError)as e:errors.append(dict(id=rid,error=str(e)))
 return rendered,dict(total=len(source),translated=len(active),rendered=len(rendered),errors=errors,missing=sorted(set(source)-set(active)))

def measure_for(rid):
 from tools.dialogue_layout import advance as narrow
 return (lambda c:narrow(advance(c))if ord(c)<128 else advance(c))if rid==CONDENSED_ID else advance

def encode_record(rid,text,mapping):
 if rid!=CONDENSED_ID:return DB.encode(text,mapping)
 # Only this complete six-triad speech uses the already shipped 85% alphabet.
 # The speaker header retains its ordinary profile.
 selected=dict(mapping)
 for token,value in mapping.items():
  if token.startswith('@condensed:'):selected[token[len('@condensed:'):]]=value
 head,sep,body=text.partition('\n')
 for c in body:
  if ord(c)<128 and c!='\n'and '@condensed:'+c not in mapping:raise ValueError('Condensed character not in shipped font')
 return DB.encode(head,mapping)+b'\r\n'+DB.encode(body,selected)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();plan=jobs()
 for j in plan:print(j['stem'],j['count'])
 print('Rows',len(all_rows()),'Slices',len(plan),'Packages',len(inventory()['packages']))
 if a.apply:export(plan)
 else:print('DRY RUN: private source/context briefs only; English answers will be authored separately.')
if __name__=='__main__':main()
