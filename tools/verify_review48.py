"""Read back every carried lookup, new name/title key and warning widget."""
import argparse,json,struct,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review48_content as C,review48_text as R,review48_build as B
from tools import ui_hook as H,eboot_text as E,ui_catalog as U,ui_layout_text as UI,library_build as L
from tools.verify_review34 import members_equal
from tools.verify_review47 import centered_cases
from tools.cpk import CPK
from tools.pipeline import config
VERSION=R.VERSION;BASE=B.BASE
SHOTS=(('name','71294c1b-860a-4a8b-99a7-0b3925ed0fa2'),('warning','63bd57f6-6a8a-4142-8220-7afb43f12e7d'),('stage','839cbdb6-37fe-455c-a650-55a7c89fc102'))

def components():
 folder=ROOT/'work/output/builds'/VERSION;b=json.loads((folder/'build.json').read_text('utf8'));old=json.loads((BASE/'build.json').read_text('utf8'))
 for name,digest in b['outputs'].items():
  if sha256_file(folder/name)!=digest:raise ValueError('Final asset changed: '+name)
  if name not in B.CHANGED and digest!=old['outputs'][name]:raise ValueError('Carried asset changed: '+name)
 if b['mapping']!=old['mapping']or b['widths']!=old['widths']:raise ValueError('Font codes or advances changed')
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):
  if sha256_file(folder/name)!=sha256_file(BASE/name):raise ValueError('Carried component differs: '+name)
 elf=(folder/'EBOOT.BIN').read_bytes();prior=(BASE/'EBOOT.BIN').read_bytes();rd=H._reader(elf,H._headers(elf)[2]);pr=H._reader(prior,H._headers(prior)[2])
 before=H.slot_map(pr);after=H.slot_map(rd);restored=bytearray(elf)
 for a,z in b['review48']['hook']['modified_file_ranges']:restored[a:z]=prior[a:z]
 if restored!=prior:raise ValueError('Executable code changed outside reserved dictionary')
 for key,ptr in before.items():
  if after.get(key)!=ptr:raise ValueError('Existing lookup pointer changed')
  size=H.extent(pr(ptr,H.MAX_ENGLISH_EXTENT+2),cap=H.MAX_ENGLISH_EXTENT)+1
  if rd(ptr,size)!=pr(ptr,size):raise ValueError('Existing English payload changed')
 hook=b['executable']['ui_hook'];runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);lookups=[]
 entries=C.hook_entries(H.PREPARED.read_bytes(),b['mapping'])
 for row in entries:
  ptr,steps=runner.run(row['key']+b'\0')
  if rd(ptr,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('New name/title translation missing')
  lookups.append(dict(id=row['id'],steps=steps))
 native=[]
 for row in C.stage_rows():
  if not row['display']:continue
  for kind,codec in ((0,'utf8'),(1,'cp932')):
   prefix,steps=C.native_prefix(elf,row['index'],kind)
   if prefix.decode(codec)!=row['prefix']:raise ValueError('Final native stage prefix differs')
   key=H.utf8_key((row['prefix']+'『'+row['title']+'』').encode('utf8'),H.PREPARED.read_bytes())
   ptr,n=runner.run(key+b'\0');wanted=E.encode(row['caption'],b['mapping'])+b'\0'
   if rd(ptr,len(wanted))!=wanted:raise ValueError('Native complete stage heading missing')
   native.append(dict(stage=row['stage'],kind=kind,steps=steps+n,caption=row['caption']))
 titles=C.title_entries(H.PREPARED.read_bytes(),b['mapping'])
 captions=centered_cases(elf,b,[(r['id'],r['key'],E.unshow(L.decode(r['english'],b['mapping'])),28)for r in titles])
 ui=UI.plan(config(ROOT/'config/tengoku.json'),b['mapping']);UI.verify_archive(folder/'AIDDATAPACK.CPK',ui)
 with CPK(BASE/'AIDDATAPACK.CPK')as a,CPK(folder/'AIDDATAPACK.CPK')as z:
  au=a.read(next(r for r in a.files if r['id']==0));zu=z.read(next(r for r in z.files if r['id']==0))
 source=R.B.source();ag=len(au)-len(source);zg=len(zu)-len(source)
 widgets=lambda data,g:{at-g:r for r in U.fssa_strings(data,decode=lambda x:x.hex())for at in r['widget_offsets']}
 aw,zw=widgets(au,ag),widgets(zu,zg);edits={r['widget_offset']:r for r in R.plan()['edits']};warning=[]
 if set(aw)!=set(zw):raise ValueError('Widget inventory differs')
 for at,row in aw.items():
  edit=edits.get(at);wanted=E.encode(edit['en'],b['mapping'])if edit else row['raw']
  if zw[at]['raw']!=wanted:raise ValueError('Unrelated widget text changed')
  a=bytearray(au[at+ag+4:at+ag+32]);z=bytearray(zu[at+zg+4:at+zg+32])
  if edit:
   x=struct.unpack_from('>f',zu,at+zg+4)[0]
   if abs(x-edit['x'])>.000001 or zu[at+zg+23]!=edit['mode']:raise ValueError('Warning position differs')
   a[:4]=z[:4];a[19]=z[19];warning.append(dict(widget_offset=at,left=640+x*640,english=edit['en']))
  if a!=z:raise ValueError('Unrelated widget geometry/color/state changed')
 archives={}
 for name,changed in (('AIDDATAPACK.CPK',{0}),('EFFPS3.CPK',{229})):
  archives[name]=len(members_equal(BASE/name,folder/name,changed))
 # TPACK cards and final EFF heading are covered by byte-identical parent files/members.
 return dict(schema=1,version=VERSION,parent_version='0.5.47',previous_public_version='0.5.44',
  old_lookup_payloads_preserved=len(before),installed_lookups=lookups,native_stage_cases=native,
  native_caption_origins=captions,stage_coverage=C.report(),warning_widgets=warning,widgets_checked=len(aw),
  unchanged_archive_members=archives,font_codes_artwork_and_advances_unchanged=True,
  parent_proof_sha256=sha256_file(ROOT/'work/ui/review47_verified_0.5.47.json'),runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');p.add_argument('--components-only',action='store_true');a=p.parse_args()
 if a.preview:print('DRY RUN: all name/title keys, native stage prefixes, warning geometry, parent payloads and ISO.');return
 result=components()
 if not a.components_only:
  image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso';report=json.loads(image.with_suffix('.json').read_text('utf8'))
  if report['version']!=VERSION or report['files_verified_each_tree']!=82 or sha256_file(image)!=report['sha256']:raise ValueError('Final ISO differs')
  result['iso_verification']=report
 result['screenshots']=[]
 for label,ident in SHOTS:
  source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dest=ROOT/'work/ui/screenshots'/('reported-review48-'+label+'.png')
  if not source.exists():source=dest
  result['screenshots'].append(dict(source=str(source),saved_path=str(dest),sha256=sha256_file(source)))
 print('Lookups',len(result['installed_lookups']),'Preserved',result['old_lookup_payloads_preserved'],'Native stages',len(result['native_stage_cases']),'Captions',len(result['native_caption_origins']),'Widgets',result['widgets_checked'],flush=True)
 if a.apply:
  for r in result['screenshots']:
   source,dest=Path(r['source']),Path(r['saved_path'])
   if dest.exists()and sha256_file(dest)!=r['sha256']:raise ValueError('Screenshot evidence collision')
   if source!=dest:shutil.copyfile(source,dest)
  write_json(ROOT/f'work/ui/review48_verified_{VERSION}.json',result)
 else:print('DRY RUN: no evidence written.')
if __name__=='__main__':main()
