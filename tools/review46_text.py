"""Herald terminology and source-bound fixes for the six reported screens."""
import argparse, json, re, struct
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U
from tools.ui_description_layout import advance
VERSION='0.5.46'
DEST=ROOT/'work/translation/en/ui/review46_layout.json'
UI={
 '61bf7642dc13f9e1e871':('Special Ability Activated','Ability Active'),
 '18c9677154e10756061b':('/ Funds Raised','/ Funds'),
 'e52a9153ec64423ade4e':('Funds Raised','Funds'),
 'a48e36045063145003aa':('Lightweight Configuration','Light Config.'),
 '7287ee00b37ac5c26b4a':('Assault Configuration','Assault Config.'),
 '327dc6017a7a02e7df41':('Emergency Deployment Booster','Emerg. Deploy Booster'),
 '07d1b30005e1c6bd1422':('<Can select  more pilots.>','Left:'),
}
PLURAL={
 '641:t_013:15','671:t_112:1','671:t_113:0','671:t_113:4','671:t_114:2','671:t_115:1',
 '713:t_007:5','713:t_011:7','713:t_016:21','713:t_021:5','713:t_125:1','713:t_139:1',
 '731:t_022:1',
}
TOKEN='$$御使い$$'
def wording(text, rid=None):
 text=re.sub(r'\b([Aa])n(\s+)\$\$御使い\$\$',lambda m:m[1]+m[2]+TOKEN,text)
 if rid in PLURAL:text=re.sub(r'\$\$御使い\$\$(?!s)',TOKEN+'s',text)
 return text

def changes():
 out=[]; audit=[]
 for path in sorted((ROOT/'work/translation/en').rglob('*.json')):
  if path.relative_to(ROOT/'work/translation/en').parts[0]not in ('dialogue','library','ui','voice'):continue
  if any(s in path.parts for s in ('prior','reference','drafts','voice_text','voice_new','library_proofread')) or 'reuse' in path.name:continue
  data=json.loads(path.read_text('utf8')); edits=[]
  def walk(v,rid=None):
   if isinstance(v,dict):
    for k,a in v.items():
     if k in ('en','DSCR','DSC2')and isinstance(a,str):
      new=wording(a,rid)
      if 'library' in path.parts or ('ui' in path.parts and '$$御使い$$' in a):
       new=re.sub(r'(?<!a )(?<!an )(?<!An )(?<!A )\$\$御使い\$\$(?!s|-controlled)',TOKEN+'s',new)
      if path.parent.name=='expanded'and rid in UI:
       old,target=UI[rid]
       if a not in (old,target):raise ValueError('Stale UI '+rid)
       new=target
      # Keep both direct executable name catalogues synchronized with SB2T.
      if k=='en' and ('eboot' in path.name or path.parent.name=='eboot_new'):
       for old,new_name in UI.values():
        if a==old:new=new_name
      if path.name=='squad_names.json'and rid=='御使い':new='Heralds'
      if new!=a:v[k]=new;edits.append((rid,k,a,new))
     else:walk(a,k if isinstance(a,dict) and k not in ('rows','strings','entries')else rid)
   elif isinstance(v,list):
    for a in v:walk(a,rid)
  walk(data)
  if edits:
   raw=path.read_text('utf8')
   for rid,k,old,new in edits:
    a=json.dumps(old,ensure_ascii=False);z=json.dumps(new,ensure_ascii=False)
    if a not in raw:raise ValueError('JSON source spelling changed')
    raw=raw.replace(a,z)
    audit.append(dict(file=str(path.relative_to(ROOT)),id=rid,field=k,before=old,after=new))
   if json.loads(raw)!=data:raise ValueError('Text edit would change an unrelated field: '+str(path))
   out.append((path,raw))
 path=ROOT/'work/glossary/library_terms.json';data=json.loads(path.read_text('utf8'))
 t=next(t for t in data['terms']if t.get('token')=='御使い')
 if t['en']not in ('Angel','Herald'):raise ValueError('Canonical term changed')
 if t['en']!='Herald':
  t.update(en='Herald',source='User canonical correction, 2026-10-17: SRW 30 faction terminology Heralds; singular Herald. Preserve unrelated Angels.')
  out.append((path,json.dumps(data,ensure_ascii=False,indent=2)+'\n'))
 return out,audit

def plan():
 source=B.source();widgets={at:r for r in U.fssa_strings(source)for at in r['widget_offsets']};edits=[];bounds=[]
 # Exact widget uses of the shared captions, plus current SB2T conversion names.
 labels={0x8a964:'Ability Active',0x8a984:'Ability Active',0x96564:'/ Funds',0xa47a4:'/ Funds',0x96664:'Funds'}
 for at,en in labels.items():
  row=widgets[at];edits.append(dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
   source_widget_sha256=sha256(source[at:at+32]),notes='Fit the existing caption slot; preserve live values, font, colors and coordinates.'))
 row=widgets[0x96104];edits.append(dict(widget_offset=0x96104,en='Left:',x=(478-640)/640,mode=0,
  source_sha256=sha256(row['raw']),source_widget_sha256=sha256(source[0x96104:0x96124]),
  notes='Left-anchor the compact count caption before the unchanged native remaining-pilot number.'))
 for en,quad,available in [('Ability Active',25,224),('/ Funds',28,205),('Funds',28,205),
   ('Emerg. Deploy Booster',31,370),('Light Config.',31,370),('Assault Config.',31,370)]:
  w=sum(map(advance,en))*quad/32
  if w>available:raise ValueError('Caption exceeds measured box: '+en)
  bounds.append(dict(english=en,width=w,available=available,quad=quad))
 return dict(schema=1,version=VERSION,source_member_sha256=sha256(source),edits=edits,bounds=bounds,runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
 layout=plan();edits,audit=changes()
 print('Changed files:',len(edits),'Text rows:',len(audit),'Plural contexts:',len(PLURAL));print('Sample:',audit[:3]);print('Bounds:',layout['bounds'])
 if not a.apply:print('DRY RUN: no translation data changed.');return
 audit_path=ROOT/'work/ui/review46_text_changes.json'
 if audit_path.exists():
  saved=json.loads(audit_path.read_text('utf8'))['changes']
  if audit and audit!=saved:raise ValueError('Preserve the recorded parent-source correction audit')
  if not audit:audit=saved
 for path,raw in edits:
  original=path.read_bytes();encoded=raw.encode('utf8')
  if original.count(b'\r\n')==original.count(b'\n')and b'\r\n'in original:encoded=encoded.replace(b'\n',b'\r\n')
  path.write_bytes(encoded)
 write_json(DEST,layout);write_json(audit_path,dict(version=VERSION,changes=audit))
if __name__=='__main__':main()
