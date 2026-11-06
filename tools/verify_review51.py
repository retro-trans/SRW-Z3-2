"""Execute the final DLC menu lookups and native confirmation paths."""
import argparse,json,struct,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review51_build as B,review51_text as T,review51_native as N,ui_hook as H,eboot_text as E
from tools import review32_content as C,ui_layout_text as U,ui_runtime as R
from tools.cpk import CPK
from tools.ui_description_layout import advance
from tools.pipeline import config
VERSION=T.VERSION;PROOF=ROOT/f'work/ui/review51_verified_{VERSION}.json'
SHOTS=('94406709-2397-4bd9-bf98-1eb52431f0f5','f62610b0-abe1-48b5-9ef5-5a0edef7e976','a751992a-84cf-484e-b5bf-488463df5d8e')

def components():
 b=json.loads((B.OUTPUT/'build.json').read_text('utf8'));old=json.loads((B.BASE/'build.json').read_text('utf8'))
 for name,digest in b['outputs'].items():
  if sha256_file(B.OUTPUT/name)!=digest:raise ValueError('Final DLC menu asset changed')
  if name not in B.CHANGED and digest!=old['outputs'][name]:raise ValueError('Unrelated asset changed')
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):
  if sha256_file(B.OUTPUT/name)!=sha256_file(B.BASE/name):raise ValueError('Font/content changed')
 if b['mapping']!=old['mapping']or b['widths']!=old['widths']:raise ValueError('Font allocation or advances changed')
 prior=(B.BASE/'EBOOT.BIN').read_bytes();elf=(B.OUTPUT/'EBOOT.BIN').read_bytes();expected,report=B.executable(prior,old)
 if elf!=expected or b['dlc_menu']!=report:raise ValueError('Final executable differs from isolated DLC plan')
 phs=H._headers(elf)[2]
 if any(p[0]==1 and p[5]and p[1]&3==3 for p in phs):raise ValueError('Writable executable memory')
 entries,bounds=T.entries(b['mapping']);rd=H._reader(elf,phs);hook=b['executable']['ui_hook'];runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
 for row in entries:
  ptr,steps=runner.run(row['key']+b'\0')
  if rd(ptr,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Final split-row DLC lookup differs')
 source_rows={r['va']:r for r in E.records()};states=[]
 for row in report['prompts']:
  wanted=row['en'].encode('utf8')+b'\0'
  if rd(row['pointer'],len(wanted))!=wanted:raise ValueError('Final native UTF-8 prompt differs')
  for ref in R.toc_references(H.PREPARED.read_bytes(),int(row['va'],16)):
   if struct.unpack('>I',rd(ref['va'],4))[0]!=row['pointer']:raise ValueError('Native prompt consumer misses relocated English')
 for va,row in T.checked()['rows'].items():
  if row['kind']!='state':continue
  key=H.utf8_key(source_rows[va]['jp'].encode('utf8'));wanted=E.encode(row['en'],b['mapping'])+b'\0';ptr,steps=runner.run(key+b'\0')
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Untranslated DLC menu state: '+va)
  states.append(dict(va=va,en=row['en'],steps=steps))
 rules=[(row['id'],row['english'],sum(map(advance,bound['en'])),False)
  for row in entries for bound in bounds if row['id']=='review51:'+bound['va']+':'+str(bound['row'])and bound['va']==hex(T.RULES)]
 origins=C.origin_cases(elf,b['mapping'],{},only_rows=rules,quads=(28,))
 source=next(r for r in E.records()if int(r['va'],16)==T.RULES)['jp'].encode('utf8');lines,steps=N.report_lines(elf,source)
 bykey={r['key']:r['english']for r in entries}
 for raw in lines:
  key=H.utf8_key(raw);ptr,_=runner.run(key+b'\0')
  wanted=bykey[key]+b'\0'
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Native rules report misses English lookup')
 cases=[N.compose(elf,row,report['title_adapter_va'],claim)for row in N.titles()if row['index']<35 for claim in (False,True)]
 pack_labels=[]
 for row in N.titles()[35:]:
  vm,string=N.machine(elf);vm.r[3:6]=[row['source_pointer'],0x41001000,128];vm.pc=report['title_adapter_va'];vm.run({vm.lr},limit=1000)
  if string(0x41001000)!=row['en'].encode('ascii'):raise ValueError('Native pack title is untranslated')
  raw=rd(row['description_pointer'],256).split(b'\0')[0];wanted=E.encode(row['en'],b['mapping'])+b'\0';ptr,steps=runner.run(raw+b'\0')
  if rd(ptr,len(wanted))!=wanted:raise ValueError('Pack description label is untranslated')
  pack_labels.append(dict(index=row['index'],en=row['en'],steps=steps))
 vm,string=N.machine(elf);vm.mem.write(0x41000000,b'Unlisted title\0');vm.r[3:6]=[0x41000000,0x41001000,128];vm.pc=report['title_adapter_va']
 vm.run({vm.lr},limit=1000)
 if string(0x41001000)!=b'Unlisted title':raise ValueError('Unknown title no longer uses original converter')
 vm,string=N.machine(elf);seen=[]
 def fallback(v):seen.append(v.r[3]);v.r[3]=0x123456;v.pc=v.lr
 vm.hooks[0x15d6a4]=fallback;vm.r[3]=255;vm.pc=B.RX_VA;vm.run({vm.lr},limit=1000)
 if seen!=[255]or vm.r[3]!=0x123456:raise ValueError('Unknown part no longer uses original lookup')
 ui=U.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
 U.verify_archive(B.OUTPUT/'AIDDATAPACK.CPK',ui)
 with CPK(B.BASE/'AIDDATAPACK.CPK')as a,CPK(B.OUTPUT/'AIDDATAPACK.CPK')as z:
  aa={r['id']:r for r in a.files};zz={r['id']:r for r in z.files}
  for mid in aa:
   if mid!=0 and a.read(aa[mid])!=z.read(zz[mid]):raise ValueError('Unrelated narration/UI member changed')
 return dict(schema=1,version=VERSION,parent_version='0.5.50',category_entries=74,synopses=35,prompts=29,menu_states=9,rules_notices=1,
  draw_keys=len(entries),draw_bounds=bounds,centered_rules_origins=origins,native_rules_rows=len(lines),native_rules_steps=steps,
  menu_state_lookups=states,
  native_utf8_prompts_verified=len(report['prompts']),
  native_confirmation_cases=cases,native_titles=report['titles'],native_reward_names=report['parts'],
  native_pack_title_and_description_cases=pack_labels,
  unrelated_dictionary_entries_preserved=report['unrelated_keys_preserved'],fonts_and_narration_unchanged=True,
  no_writable_executable_load=True,new_rx_load=dict(va=B.RX_VA,bytes=report['new_code_bytes']),
  unknown_title_and_reward_fallbacks_preserved=True,
  build_sha256=sha256_file(B.OUTPUT/'build.json'),runtime_verified=False)

def verify():
 data=components();image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso';iso=json.loads(image.with_suffix('.json').read_text('utf8'))
 if iso['version']!=VERSION or iso['files_verified_each_tree']!=82 or sha256_file(image)!=iso['sha256']:raise ValueError('Final DLC menu image proof differs')
 data['iso_verification']=iso
 return data

def main():
 p=argparse.ArgumentParser();p.add_argument('--components',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
 data=components()if a.components else verify()
 print('Category:',data['category_entries'],'draw keys:',data['draw_keys'],'native dialogs:',len(data['native_confirmation_cases']))
 print('Native rules rows:',data['native_rules_rows'],'English titles/reward names:',data['native_titles'],data['native_reward_names'])
 print('Reported confirmation:',next(r['en']for r in data['native_confirmation_cases']if r['index']==3 and not r['claim']))
 if a.apply:
  if a.components:raise ValueError('Full image proof required')
  shots=[]
  for i,ident in enumerate(SHOTS,1):
   source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
   dest=ROOT/f'work/ui/screenshots/reported-0.5.51-dlc-{i}.png'
   if dest.exists()and sha256_file(dest)!=sha256_file(source):raise ValueError('Screenshot collision')
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);shots.append(dict(path=dest.relative_to(ROOT).as_posix(),sha256=sha256_file(dest)))
  data['reported_screenshots']=shots;write_json(PROOF,data)
 else:print('DRY RUN: no final evidence written.')
if __name__=='__main__':main()
