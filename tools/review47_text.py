"""Canonical Lowen/Schlan names, aligned questions and a compact Sphere command."""
import argparse,json,re,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance
VERSION='0.5.47'
DEST=ROOT/'work/translation/en/ui/review47_layout.json'
NAMES={'Leben':'Lowen','Schran':'Schlan'}
SPHERE='c1d47ec9c607350f8f6e'

def corrections():
 out=[];audit=[]
 paths=[ROOT/'work/glossary/library_terms.json']
 for family in ('dialogue','voice','library'):
  paths+=sorted((ROOT/'work/translation/en'/family).glob('*.json'))
 ui=ROOT/'work/translation/en/ui'
 paths+=list(ui.glob('*.json'))+list((ui/'expanded').glob('*.json'))+list((ui/'eboot_new').glob('*.json'))
 for path in paths:
  data=json.loads(path.read_text('utf8'));edits=[]
  def walk(value,key='',rid=''):
   if isinstance(value,dict):
    for k,v in value.items():
     if isinstance(v,str)and k in ('en','DSCR','DSC2'):
      new=re.sub(r'\b(Leben|Schran)\b',lambda m:NAMES[m[0]],v)
      if path.name=='help.json'and rid==SPHERE:new='Sphere Act'
      if path.parent.name=='eboot_new'and rid=='スフィア発動':new='Sphere Act'
      if new!=v:value[k]=new;edits.append(dict(id=rid,field=k,before=v,after=new))
     else:walk(v,k,k if isinstance(v,dict)else rid)
   elif isinstance(value,list):
    for v in value:walk(v,key,v.get('token',rid)if isinstance(v,dict)else rid)
  walk(data)
  if edits:
   raw=path.read_text('utf8')
   for e in edits:raw=raw.replace(json.dumps(e['before'],ensure_ascii=False),json.dumps(e['after'],ensure_ascii=False))
   if json.loads(raw)!=data:raise ValueError('Unrelated JSON field would change: '+str(path))
   out.append((path,raw));audit.extend(dict(file=path.relative_to(ROOT).as_posix(),**e)for e in edits)
 return out,audit

def plan():
 s=B.source();widgets={a:r for r in U.fssa_strings(s)for a in r['widget_offsets']}
 width=lambda text:sum(map(advance,text))*25/32
 left=639.5-width('Yes / No')/2;no=left+width('Yes / ');edits=[];bounds=[]
 for at,row in widgets.items():
  if row['text']not in ('はい　／　いいえ','はい','いいえ'):continue
  text={'はい　／　いいえ':'Yes / No','はい':'Yes','いいえ':'No'}[row['text']]
  x=no if text=='No'else left
  edits.append(dict(widget_offset=at,en=text,x=(x-640)/640,mode=s[at+23]&~0x40,
   source_sha256=sha256(row['raw']),source_widget_sha256=sha256(s[at:at+32]),
   notes='Explicit English in grey and selected states; identical measured origins, native colors and row geometry.'))
  bounds.append(dict(widget_offset=at,en=text,left=x,right=x+width(text),quad=25))
 sphere=sum(map(advance,'Sphere Act'))*28/32
 if sphere>208:raise ValueError('Sphere command exceeds native button')
 return dict(schema=1,version=VERSION,source_member_sha256=sha256(s),edits=edits,bounds=bounds,
  sphere=dict(english='Sphere Act',width=sphere,available=208,quad=28),runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
 edits,audit=corrections();layout=plan()
 print('Changed files:',len(edits),'English fields:',len(audit),'Choice widgets:',len(layout['edits']))
 for c in audit:print(c['file'],c['id'],repr(c['before'][:85]),'=>',repr(c['after'][:85]))
 print('Sphere button:',layout['sphere'])
 if not a.apply:print('DRY RUN: no data written.');return
 ap=ROOT/'work/ui/review47_text_changes.json'
 if ap.exists():
  saved=json.loads(ap.read_text('utf8'))['changes']
  if audit and audit!=saved:raise ValueError('Preserve the parent source audit')
  if not audit:audit=saved
 for path,raw in edits:
  original=path.read_bytes();new=raw.encode('utf8')
  if original.count(b'\r\n')==original.count(b'\n')and b'\r\n'in original:new=new.replace(b'\n',b'\r\n')
  path.write_bytes(new)
 write_json(DEST,layout);write_json(ap,dict(version=VERSION,changes=audit))
if __name__=='__main__':main()
