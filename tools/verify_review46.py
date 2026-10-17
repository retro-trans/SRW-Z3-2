"""Read final Herald, no-pilot, conversion, fundraising and indicator bytes."""
import argparse,copy,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import review46_text as R,review46_fallback as F,ui_hook as H,ui_catalog as U
from tools import library_text as LT,library_build as L,dialogue as D,dialogue_build as DB
from tools import ui_layout_text as UI,eboot_text as E,library_runtime as LR,keyword_popup as K
from tools.ui_description_layout import advance
from tools.pipeline import config,verified_source
from tools.cpk import CPK
VERSION=R.VERSION;BASE=ROOT/'work/output/builds/0.5.45'
SHOTS=(('Heralds','da69f126-c5fe-4d30-9541-907baac1b7f0'),('empty-pilot','47fc48e0-62b0-4e4b-8451-d4419b4cf9b9'),
 ('booster','2294275f-588c-4ea4-ad83-ccceb30daeab'),('configuration','01261d9c-12cf-409b-a271-30e8fe1b9443'),
 ('fundraising','39e0d730-5352-4735-adb8-0cf81eaacb6a'),('ability','8bda6312-d73b-471e-9a4a-7c5bbe113a03'))
def prior():
 audit=json.loads((ROOT/'work/ui/review46_text_changes.json').read_text('utf8'))['changes']
 terms=json.loads(LT.GLOSSARY.read_text('utf8'))['terms'];old=copy.deepcopy(terms)
 next(t for t in old if t.get('token')=='御使い')['en']='Angel'
 return audit,terms,old

def stages(folder,b):
 audit,terms,old=prior();current=DB.translations();before=copy.deepcopy(current)
 for c in audit:
  if c['file'].startswith('work\\translation\\en\\dialogue\\'):
   if before[c['id']]['en']!=c['after']:raise ValueError('Stale dialogue correction')
   before[c['id']]['en']=c['before']
 rendered=DB.plan(advance);old_rendered=dict(rendered);resolver=LT.Resolver(old)
 records={r['id']:r for r in D.plan_rows()};changed_rows=[]
 for rid,row in before.items():
  if '$$御使い' not in row['en']and row['en']==current[rid]['en']:continue
  text=DB.render(row,records[rid],resolver,advance);old_rendered[rid]=text
  if text!=rendered[rid]:changed_rows.append(dict(id=rid,english=rendered[rid]))
 changed=[];mids=sorted({int(r['id'].split(':')[0])for r in changed_rows})
 with CPK(BASE/'STGZ3OF2.cpk')as a,CPK(folder/'STGZ3OF2.cpk')as z:
  ai={r['id']:r for r in a.files};zi={r['id']:r for r in z.files}
  for mid in mids:
   if DB.rebuild_member(mid,old_rendered,b['mapping'])!=a.read(ai[mid]):raise ValueError('Parent dialogue source differs '+str(mid))
   if DB.rebuild_member(mid,rendered,b['mapping'])!=z.read(zi[mid]):raise ValueError('Final dialogue source differs '+str(mid))
   changed.append(mid)
 from tools import squad_text as S,mission_text as M,mission_display as MD
 squad=S.plan();old_squad=dict(squad);old_squad['御使い']='Angel';mission=MD.stage_text(M.plan(advance))
 with CPK(BASE/'STGZ3OF2.cpk')as a,CPK(folder/'STGZ3OF2.cpk')as z:
  ai={r['id']:r for r in a.files};zi={r['id']:r for r in z.files}
  for mid in S.stage_members():
   before_bytes=S.rebuild_member(mid,mission,old_squad,b['mapping']);after_bytes=S.rebuild_member(mid,mission,squad,b['mapping'])
   if before_bytes==after_bytes:continue
   if before_bytes!=a.read(ai[mid])or after_bytes!=z.read(zi[mid]):raise ValueError('Faction-name stage differs '+str(mid))
   changed.append(mid)
 from tools.verify_review34 import members_equal
 unchanged=members_equal(BASE/'STGZ3OF2.cpk',folder/'STGZ3OF2.cpk',set(changed))
 if rendered['641:t_013:15']!='Vildark\n「Heralds!」':raise ValueError('Reported faction declaration differs')
 return dict(dialogue_records=changed_rows,changed_members=sorted(changed),unchanged_members=len(unchanged),all_records=len(rendered))

def libraries(folder,b):
 audit,terms,old=prior();lib=LT.load_library();entries,errors=LT.load_translations()
 if errors:raise ValueError(errors)
 previous=copy.deepcopy(entries)
 for c in audit:
  if c['field']not in ('DSCR','DSC2')or 'library'not in c['file']:continue
  name=c['file'].split('\\')[-1];kind=json.loads((ROOT/c['file']).read_text('utf8'))['kind']
  entry=previous[kind][str(c['id'])][1]
  if entry[c['field']]!=c['after']:raise ValueError('Stale library correction')
  entry[c['field']]=c['before']
 before=L.plan(lib,previous,old);after=L.plan(lib,entries,terms);changed={};counts={}
 from tools.game_build import LIBRARY
 from tools.verify_review34 import members_equal
 for kind,disc in LIBRARY.items():
  name=Path(disc).name;ids=[]
  with CPK(verified_source(config(ROOT/'config/tengoku.json'),disc))as src,CPK(BASE/name)as a,CPK(folder/name)as z:
   si={r['id']:r for r in src.files}
   ai={r['id']:r for r in a.files};zi={r['id']:r for r in z.files}
   for mid,fields in after[kind].items():
    if fields==before[kind][mid]:continue
    def build(values):
     payload={tag:L.encode(L.wrap(text,advance)if tag in ('DSCR','DSC2')else text,b['mapping'])for tag,text in values.items()}
     return L.rebuild(src.read(si[mid]),payload)
    if build(before[kind][mid])!=a.read(ai[mid])or build(fields)!=z.read(zi[mid]):raise ValueError('Library member differs '+kind+' '+str(mid))
    ids.append(mid)
  unchanged=members_equal(BASE/name,folder/name,set(ids));changed[name]=ids;counts[name]=len(unchanged)
 popup=K.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
 with CPK(folder/'MTV_ALL_KEYWORD_DEF.CPK')as a:
  if a.read(a.files[0])!=popup['members'][0]:raise ValueError('Actual linked-keyword popup differs')
 return dict(changed=changed,unchanged_members=counts,keyword_popup=popup['report'])

def components():
 folder=ROOT/'work/output/builds'/VERSION;b=json.loads((folder/'build.json').read_text('utf8'));old=json.loads((BASE/'build.json').read_text('utf8'))
 for name,digest in b['outputs'].items():
  if sha256_file(folder/name)!=digest:raise ValueError('Final output changed: '+name)
 if b['mapping']!=old['mapping']or b['widths']!=old['widths']:raise ValueError('Letter shapes or spacing changed')
 for fid in (1,3):
  if (folder/('font_%d.bin'%fid)).read_bytes()!=(BASE/('font_%d.bin'%fid)).read_bytes():raise ValueError('Font artwork changed')
 elf=(folder/'EBOOT.BIN').read_bytes();lookups=[]
 entries,_=E.hook_entries(H.PREPARED.read_bytes(),b['mapping'],H.utf8_key);entries,_=U.hook_entries(H.PREPARED.read_bytes(),b['mapping'],entries)
 hook=b['executable']['ui_hook'];runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);rd=H._reader(elf,H._headers(elf)[2])
 from tools import review45_text as R45,review44_build as B44,review32_content as C,opening_narration as N
 grouped,rows=U.checked();keys=set()
 for rid in set(R.UI)|set(R45.help_changes())|{R45.NARRATION_ID,R45.MENU_ID}:
  for source in grouped[rid]:keys.add(source['raw']if source['encoding']=='cp932'else H.utf8_key(source['raw']))
 entries=[row for row in entries if row['key']in keys or L.encode('Herald',b['mapping'])in row['english']]
 for row in entries:
  ptr,steps=runner.run(row['key']+b'\0');wanted=row['english']+b'\0'
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Installed UI lookup differs '+row['id'])
  lookups.append(dict(id=row['id'],key_hex=row['key'].hex(),encoded_hex=row['english'].hex()))
 selected=[]
 for rid in R45.help_changes():
  for source in grouped[rid]:
   key=source['raw']if source['encoding']=='cp932'else H.utf8_key(source['raw'])
   selected.append(dict(english=rows[rid]['en'],key_hex=key.hex()))
 origins=[]
 for quad in (28,31):origins+=B44.caption_cases(elf,b,dict(cases=selected),expected_count=24,quad=quad)
 caption=L.expand(R45.CAPTION,E.resolver());lines,index=C.caption(caption);visible='\n'.join(lines[index:]);span=max(sum(map(advance,line))for line in lines[index:])
 raw=bytes.fromhex(b['mapping'][C.CAPTION_MARK])+L.encode(visible,b['mapping'])
 palace=C.origin_cases(elf,b['mapping'],b['executable']['link_layout'],only_rows=[(R45.CAPTION_ID,raw,span,False)],quads=(28,31,40))
 text,condensed=N.profile(R45.NARRATION)
 if text!=R45.NARRATION or not condensed:raise ValueError('Carried narration profile changed')
 if L.encode(R45.PART_NEW,b['mapping'])+b'\0'not in (folder/'rpw.bin').read_bytes():raise ValueError('Carried part name missing')
 fallback=F.native_cases(elf)
 for disp,va,count in F.CASES:
  p=struct.unpack('>I',rd(H.TOC+disp,4))[0]
  if rd(p,count*2+1)!=('ー'*count).encode('cp932')+b'\0':raise ValueError('Shipped fallback differs')
 ui=UI.plan(config(ROOT/'config/tengoku.json'),b['mapping']);UI.verify_archive(folder/'AIDDATAPACK.CPK',ui)
 from tools.verify_review34 import members_equal
 members_equal(BASE/'AIDDATAPACK.CPK',folder/'AIDDATAPACK.CPK',{0})
 with CPK(BASE/'AIDDATAPACK.CPK')as a,CPK(folder/'AIDDATAPACK.CPK')as z:
  old_ui=a.read(next(r for r in a.files if r['id']==0));new_ui=z.read(next(r for r in z.files if r['id']==0))
 original=R.B.source();ga=len(old_ui)-len(original);gz=len(new_ui)-len(original)
 before={at-ga:r for r in U.fssa_strings(old_ui,decode=lambda x:x.hex())for at in r['widget_offsets']}
 after={at-gz:r for r in U.fssa_strings(new_ui,decode=lambda x:x.hex())for at in r['widget_offsets']}
 edits={e['widget_offset']:e for e in R.plan()['edits']}
 if set(before)!=set(after):raise ValueError('Widget identities changed')
 from tools.menu_layout import encode
 for at,row in before.items():
  wanted=encode(edits[at],b['mapping'])if at in edits else row['raw']
  if after[at]['raw']!=wanted:raise ValueError('Unrelated widget text changed '+hex(at))
  a=bytearray(old_ui[at+ga+4:at+ga+32]);z=bytearray(new_ui[at+gz+4:at+gz+32])
  if at==0x96104:a[:4]=z[:4];a[19]=z[19]
  if a!=z:raise ValueError('Unrelated widget geometry or state changed '+hex(at))
 native=LR.plan(H.PREPARED.read_bytes(),b['mapping'],advance)
 addresses=hook['table']['payload_vas'];report=b['executable']['library_runtime']['conversion']
 fast=LR.verify_fastpath(elf,native,addresses,report)
 for pointer in native['pointers']:
  at=pointer['offset'];p=struct.unpack_from('>I',elf,at)[0]
  if p!=addresses[pointer['id']]:raise ValueError('Native keyword descriptor differs')
 return dict(schema=1,version=VERSION,previous_public_version='0.5.44',parent_version='0.5.45',
  ui_lookups_checked=len(entries),ui_lookup_cases=lookups,widgets_checked=len(before),no_pilot_cases=fallback,bounds=R.plan()['bounds'],
  stages=stages(folder,b),libraries=libraries(folder,b),native_keyword_descriptions=fast,
  carried_command_origins=origins,carried_palace_origins=palace,
  font_codes_artwork_and_advances_unchanged=True,runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');p.add_argument('--components-only',action='store_true');a=p.parse_args()
 if a.preview:print('DRY RUN: final source-bound archives, UI lookups, native fallback consumers, fonts and ISO.');return
 result=components()
 if not a.components_only:
  image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso';report=json.loads(image.with_suffix('.json').read_text('utf8'))
  if report['version']!=VERSION or report['files_verified_each_tree']!=82 or sha256_file(image)!=report['sha256']:raise ValueError('Final ISO differs')
  result['iso_verification']=report
 result['screenshots']=[]
 for label,ident in SHOTS:
  source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dest=ROOT/'work/ui/screenshots'/('reported-review46-'+label+'.png')
  if not source.exists():source=dest
  result['screenshots'].append(dict(source=str(source),saved_path=str(dest),sha256=sha256_file(source)))
 print('Verified UI lookups:',result['ui_lookups_checked'],'Native no-pilot cases:',len(result['no_pilot_cases']),'Herald dialogue:',len(result['stages']['dialogue_records']),flush=True)
 if a.apply:
  for row in result['screenshots']:
   source,dest=Path(row['source']),Path(row['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists()and sha256_file(dest)!=row['sha256']:raise ValueError('Screenshot evidence collision')
   if source!=dest:shutil.copyfile(source,dest)
  write_json(ROOT/f'work/ui/review46_verified_{VERSION}.json',result)
 else:print('DRY RUN: no evidence written.')
if __name__=='__main__':main()
