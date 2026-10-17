"""Read back the final names, purchase constructor/lookups and menu geometry."""
import argparse,copy,json,struct,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review47_text as T,review47_messages as M,ui_hook as H,eboot_text as E
from tools import library_text as LT,library_build as L,dialogue_build as D,dialogue as DR
from tools import ui_catalog as U,ui_layout_text as UI,library_runtime as LR,keyword_popup as K
from tools.ui_description_layout import advance
from tools.pipeline import config,verified_source
from tools.cpk import CPK
from tools.verify_review34 import members_equal
VERSION=T.VERSION;BASE=ROOT/'work/output/builds/0.5.46'
SHOTS=(('Lowen','bbd216d9-5aaf-484d-8f00-a5e646529072'),('Schlan','4901503c-3e7c-4cb4-89f6-28ab6b6e2817'),
 ('purchase','ac3bf217-fc0c-4560-b130-5a04927bce42'),('purchase-duplicate','6b3bbeb7-1f20-4170-9bbd-ba4d994eb059'),
 ('sphere','1b35da07-c298-4981-b930-2c242c097cc5'))

def terms():
 current=json.loads(LT.GLOSSARY.read_text('utf8'))['terms'];old=copy.deepcopy(current)
 for t in old:
  for a,z in T.NAMES.items():
   if t.get('en','').startswith(z):t['en']=a+t['en'][len(z):]
 return current,old

def names(folder,b):
 current,old=terms();res=LT.Resolver(current);before_res=LT.Resolver(old)
 active=D.translations();rendered=D.plan(advance);previous=dict(rendered);changed=[]
 records={r['id']:r for r in DR.plan_rows()}
 tokens=['$$'+t['token']+'$$'for t in current if t.get('en','').startswith(('Lowen','Schlan'))]
 for rid,row in active.items():
  if not any(token in row['en']for token in tokens):continue
  previous[rid]=D.render(row,records[rid],before_res,advance)
  if rendered[rid]!=previous[rid]:changed.append(dict(id=rid,english=rendered[rid]))
 mids={int(r['id'].split(':')[0])for r in changed}
 with CPK(BASE/'STGZ3OF2.cpk')as a,CPK(folder/'STGZ3OF2.cpk')as z:
  ai={r['id']:r for r in a.files};zi={r['id']:r for r in z.files}
  for mid in mids:
   if D.rebuild_member(mid,previous,b['mapping'])!=a.read(ai[mid]):raise ValueError('Parent dialogue differs')
   if D.rebuild_member(mid,rendered,b['mapping'])!=z.read(zi[mid]):raise ValueError('Final dialogue differs')
 unchanged=len(members_equal(BASE/'STGZ3OF2.cpk',folder/'STGZ3OF2.cpk',mids))
 lib=LT.load_library();entries,errors=LT.load_translations()
 if errors:raise ValueError(errors)
 a=L.plan(lib,entries,old);z=L.plan(lib,entries,current);library_changes={}
 from tools.game_build import LIBRARY
 for kind,path in LIBRARY.items():
  ids={mid for mid in a[kind]if a[kind][mid]!=z[kind][mid]};name=Path(path).name
  with CPK(verified_source(config(ROOT/'config/tengoku.json'),path))as src,CPK(BASE/name)as prior,CPK(folder/name)as final:
   si={r['id']:r for r in src.files};pi={r['id']:r for r in prior.files};fi={r['id']:r for r in final.files}
   for mid in ids:
    for values,arc,index in ((a[kind][mid],prior,pi),(z[kind][mid],final,fi)):
     payload={tag:L.encode(L.wrap(text,advance)if tag in ('DSCR','DSC2')else text,b['mapping'])for tag,text in values.items()}
     if L.rebuild(src.read(si[mid]),payload)!=arc.read(index[mid]):raise ValueError('Library canonical name differs')
  members_equal(BASE/name,folder/name,ids);library_changes[name]=sorted(ids)
 popup=K.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
 with CPK(folder/'MTV_ALL_KEYWORD_DEF.CPK')as arc:
  if arc.read(arc.files[0])!=popup['members'][0]:raise ValueError('Actual keyword popup differs')
 return dict(dialogue_records=changed,changed_members=sorted(mids),unchanged_members=unchanged,
  all_records=len(rendered),libraries=library_changes,keyword_popup=popup['report'])

def origins(elf,b,ui):
 from tools import ppc_exec as P
 mem=P.Memory()
 for i,s in enumerate(H._headers(elf)[2][:2]):mem.map(s[3],elf[s[2]:s[2]+s[5]],writable=i==1)
 mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000));mem.map(0x42000000,bytes(0x1000))
 mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000));cases=[]
 for row in T.plan()['bounds']:
  raw=E.encode(row['en'],b['mapping'])
  for mode in (0,1):
   mem.write(0x42000000,raw+b'\0');mem.write(0x41000000,bytes(0x2000))
   for at in (0x54,0x5c):mem.write(0x41000000+at,struct.pack('>f',25))
   mem.write(0x410000ac,struct.pack('>H',mode));vm=P.Machine(mem)
   vm.r=[0x770000+i for i in range(32)];vm.r[1]=0x40003f00;vm.r[2]=H.TOC;vm.r[3]=0x42000000;vm.r[7]=1;vm.r[8]=0
   vm.f[1]=row['left'];vm.f[2]=361.;vm.f[3]=1.;vm.lr=0x152000;vm.pc=0x14ae4
   vm.run({0x14158},limit=50000)
   if abs(vm.f[1]-row['left'])>.0001:raise ValueError('Selected/grey choice origin moved')
   if mem.read(vm.r[3],len(raw)+1)!=raw+b'\0':raise ValueError('Choice drawer receives wrong English')
   cases.append(dict(widget_offset=row['widget_offset'],mode=mode,left=vm.f[1],right=row['right'],steps=vm.steps))
 return cases

def centered_cases(elf,b,rows):
 """Measure installed English through the real native centered-caption path."""
 from tools import ppc_exec as P
 mem=P.Memory()
 for i,s in enumerate(H._headers(elf)[2][:2]):mem.map(s[3],elf[s[2]:s[2]+s[5]],writable=i==1)
 mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000));mem.map(0x42000000,bytes(0x1000))
 mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000));cases=[]
 for ident,key,text,quad in rows:
  for mode in (0,1):
   mem.write(0x42000000,key+b'\0');mem.write(0x41000000,bytes(0x2000))
   for at in (0x54,0x5c):mem.write(0x41000000+at,struct.pack('>f',quad))
   mem.write(0x410000ac,struct.pack('>H',mode));vm=P.Machine(mem)
   vm.r=[0x770000+i for i in range(32)];vm.r[1]=0x40003f00;vm.r[2]=H.TOC;vm.r[3]=0x42000000;vm.r[7]=1;vm.r[8]=0
   vm.f[1]=639.5;vm.f[2]=360.;vm.f[3]=1.;vm.lr=0x152000;vm.pc=0x149bc
   before=(vm.r[1],vm.r[2],vm.r[27:32],vm.lr);vm.run({0x14158},limit=50000)
   width=sum(map(advance,text))*quad/32
   if abs(vm.f[1]+width/2-639.5)>.001:raise ValueError('Native English caption center differs: '+ident)
   if (vm.f[2],vm.f[3])!=(360.,1.)or(vm.r[1],vm.r[2],vm.r[27:32],vm.lr)!=before:raise ValueError('Caption loses caller state')
   cases.append(dict(id=ident,mode=mode,left=vm.f[1],width=width,quad=quad,steps=vm.steps))
 return cases

def components():
 folder=ROOT/'work/output/builds'/VERSION;b=json.loads((folder/'build.json').read_text('utf8'));old=json.loads((BASE/'build.json').read_text('utf8'))
 for name,digest in b['outputs'].items():
  if sha256_file(folder/name)!=digest:raise ValueError('Final asset differs: '+name)
 if b['mapping']!=old['mapping']or b['widths']!=old['widths']:raise ValueError('Font allocation or spacing changed')
 for fid in (1,3):
  if (folder/f'font_{fid}.bin').read_bytes()!=(BASE/f'font_{fid}.bin').read_bytes():raise ValueError('Font artwork changed')
 elf=(folder/'EBOOT.BIN').read_bytes();hook=b['executable']['ui_hook'];rd=H._reader(elf,H._headers(elf)[2]);centering=[]
 runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);lookups=[]
 for row in M.hook_entries(H.PREPARED.read_bytes(),b['mapping']):
  ptr,steps=runner.run(row['key']+b'\0');wanted=row['english']+b'\0'
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Installed purchase translation differs')
  lookups.append(dict(id=row['id'],steps=steps))
 constructor=[]
 for row in M.source_rows(H.PREPARED.read_bytes()):
  for kind,name in (('original',row['jp'].encode('cp932')),('translated',E.encode(row['en'],b['mapping']))):
   lines,steps=M.native_compose(elf,name);ptr,n=runner.run(lines[0]+b'\0');wanted=E.encode(row['question'],b['mapping'])+b'\0'
   if rd(ptr,len(wanted))!=wanted:raise ValueError('Native purchase constructor has no English match')
   constructor.append(dict(record=row['record'],path=kind,english=row['question'],steps=steps))
   centering.append((str(row['record'])+':'+kind,lines[0],row['question'],31))
 grouped,rows=U.checked();sphere=[];name_lookups=[]
 entries,_=E.hook_entries(H.PREPARED.read_bytes(),b['mapping'],H.utf8_key);entries,_=U.hook_entries(H.PREPARED.read_bytes(),b['mapping'],entries)
 keyset={s['raw']if s['encoding']=='cp932'else H.utf8_key(s['raw'])for s in grouped[T.SPHERE]}
 for row in entries:
  if any(E.encode(name,b['mapping'])in row['english']for name in T.NAMES.values()):
   ptr,n=runner.run(row['key']+b'\0');wanted=row['english']+b'\0'
   if rd(ptr,len(wanted))!=wanted:raise ValueError('Native canonical name lookup differs')
   name_lookups.append(dict(id=row['id'],steps=n))
  if row['key']not in keyset:continue
  ptr,n=runner.run(row['key']+b'\0');wanted=E.encode('Sphere Act',b['mapping'])+b'\0'
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Sphere command differs')
  sphere.append(dict(id=row['id'],pixels=T.plan()['sphere']['width']))
  centering.append((row['id'],row['key'],'Sphere Act',28))
  centering.append((row['id']+':preloaded',wanted[:-1],'Sphere Act',28))
 if not sphere:raise ValueError('Sphere menu binding missing')
 ui=UI.plan(config(ROOT/'config/tengoku.json'),b['mapping']);UI.verify_archive(folder/'AIDDATAPACK.CPK',ui)
 with CPK(BASE/'AIDDATAPACK.CPK')as a,CPK(folder/'AIDDATAPACK.CPK')as z:
  au=a.read(next(r for r in a.files if r['id']==0));zu=z.read(next(r for r in z.files if r['id']==0))
 source=T.B.source();ag=len(au)-len(source);zg=len(zu)-len(source)
 before={at-ag:r for r in U.fssa_strings(au,decode=lambda x:x.hex())for at in r['widget_offsets']}
 after={at-zg:r for r in U.fssa_strings(zu,decode=lambda x:x.hex())for at in r['widget_offsets']}
 edits={r['widget_offset']:r for r in T.plan()['edits']}
 if set(before)!=set(after):raise ValueError('UI identity changed')
 for at,row in before.items():
  edit=edits.get(at);wanted=E.encode(edit['en'],b['mapping'])if edit else row['raw']
  if after[at]['raw']!=wanted:raise ValueError('Unrelated widget text changed')
  a=bytearray(au[at+ag+4:at+ag+32]);z=bytearray(zu[at+zg+4:at+zg+32])
  if edit:a[:4]=z[:4];a[19]=z[19]
  if a!=z:raise ValueError('Unrelated widget state or geometry changed')
 members_equal(BASE/'AIDDATAPACK.CPK',folder/'AIDDATAPACK.CPK',{0})
 native=LR.plan(H.PREPARED.read_bytes(),b['mapping'],advance)
 fast=LR.verify_fastpath(elf,native,hook['table']['payload_vas'],b['executable']['library_runtime']['conversion'])
 from tools import review46_fallback as F
 return dict(schema=1,version=VERSION,parent_version='0.5.46',previous_public_version='0.5.44',
  purchase_lookups=lookups,purchase_constructor_cases=constructor,sphere=sphere,name_lookups=name_lookups,widgets_checked=len(before),
  native_caption_origins=centered_cases(elf,b,centering),
  choice_origin_cases=origins(elf,b,ui),no_pilot_cases=F.native_cases(elf),names=names(folder,b),
  native_keyword_descriptions=fast,font_codes_artwork_and_advances_unchanged=True,runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');p.add_argument('--components-only',action='store_true');a=p.parse_args()
 if a.preview:print('DRY RUN: final assets, all native purchase constructors, choice origins, names and ISO.');return
 result=components()
 if not a.components_only:
  image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso';report=json.loads(image.with_suffix('.json').read_text('utf8'))
  if report['version']!=VERSION or report['files_verified_each_tree']!=82 or sha256_file(image)!=report['sha256']:raise ValueError('Final ISO differs')
  result['iso_verification']=report
 result['screenshots']=[]
 for label,ident in SHOTS:
  source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dest=ROOT/'work/ui/screenshots'/('reported-review47-'+label+'.png')
  if not source.exists():source=dest
  result['screenshots'].append(dict(source=str(source),saved_path=str(dest),sha256=sha256_file(source)))
 print('Purchase lookups:',len(result['purchase_lookups']),'Native constructors:',len(result['purchase_constructor_cases']),
  'Choice origins:',len(result['choice_origin_cases']),'Changed dialogue:',len(result['names']['dialogue_records']),flush=True)
 if a.apply:
  for r in result['screenshots']:
   source,dest=Path(r['source']),Path(r['saved_path'])
   if dest.exists()and sha256_file(dest)!=r['sha256']:raise ValueError('Screenshot evidence collision')
   if source!=dest:shutil.copyfile(source,dest)
  write_json(ROOT/f'work/ui/review47_verified_{VERSION}.json',result)
 else:print('DRY RUN: no evidence written.')
if __name__=='__main__':main()
