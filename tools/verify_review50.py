"""Execute every final narration origin and guard all carried game content."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review50_build as B,narration_alignment as N,ui_hook as H,review32_content as C
from tools.cpk import CPK

VERSION=N.VERSION;PROOF=ROOT/'work/ui'/('review50_verified_'+VERSION+'.json')
SHOT=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-f814b4ab-6b74-4524-ac22-1b1a56ec2eba.png')
SHOT_DEST=ROOT/'work/ui/screenshots/reported-0.5.50-dlc-narration.png'

def components():
 b=json.loads((B.OUTPUT/'build.json').read_text('utf8'));old=json.loads((B.BASE/'build.json').read_text('utf8'))
 for name,digest in b['outputs'].items():
  if sha256_file(B.OUTPUT/name)!=digest:raise ValueError('Final asset changed: '+name)
  if name not in B.CHANGED and digest!=old['outputs'][name]:raise ValueError('Carried asset changed')
 if b['mapping']!=old['mapping']or b['widths']!=old['widths']:raise ValueError('Font mapping/advances changed')
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):
  if sha256_file(B.OUTPUT/name)!=sha256_file(B.BASE/name):raise ValueError('Carried component differs')
 elf=(B.OUTPUT/'EBOOT.BIN').read_bytes();prior=(B.BASE/'EBOOT.BIN').read_bytes();rd=H._reader(elf,H._headers(elf)[2]);pr=H._reader(prior,H._headers(prior)[2])
 restored=bytearray(elf)
 for a,z in b['narration_alignment']['modified_file_ranges']:restored[a:z]=prior[a:z]
 if restored!=prior:raise ValueError('Executable changed outside certified narration dictionary edits')
 before,after=H.slot_map(pr),H.slot_map(rd);rows=N.rows(b['mapping']);keys={r['key']for r in rows};preserved=0
 if set(before)!=set(after):raise ValueError('Dictionary key inventory changed')
 for key,ptr in before.items():
  size=H.extent(pr(ptr,H.MAX_ENGLISH_EXTENT+2),cap=H.MAX_ENGLISH_EXTENT)+1
  if rd(ptr,size)!=pr(ptr,size):raise ValueError('Original English payload changed')
  if key not in keys:
   if after[key]!=ptr:raise ValueError('Unrelated lookup moved')
   preserved+=1
 hook=b['executable']['ui_hook'];runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);lookups=[]
 for row in rows:
  pointer,steps=runner.run(row['key']+b'\0');expected=row['encoded']+b'\0'
  if rd(pointer,len(expected))!=expected:raise ValueError('Final narration lookup failed: '+row['id'])
  lookups.append(dict(id=row['id'],steps=steps,english=row['en'],condensed=row['condensed']))
 native=C.origin_cases(elf,b['mapping'],{},only_rows=[(r['id'],r['encoded'],r['span_units'],False)for r in rows],quads=(28,40))
 if len(native)!=394:raise ValueError('Incomplete narration origin verification')
 for r in native:
  if r['left']<60 or 1280-r['left']>1220:raise ValueError('Narration exceeds safe screen bounds')
 with CPK(B.BASE/'AIDDATAPACK.CPK')as a,CPK(B.OUTPUT/'AIDDATAPACK.CPK')as z:
  aa={e['id']:e for e in a.files};zz={e['id']:e for e in z.files}
  for mid in set(r['member']for r in rows):
   if a.read(aa[mid])!=z.read(zz[mid]):raise ValueError('Narration timing/source data changed')
 # The remaining assets, including the complete UI archive, were hash-compared above.
 return dict(schema=1,version=VERSION,parent_version='0.5.48',source_rows=len(rows),unique_caption_keys=len(keys),
  installed_lookups=lookups,native_caption_origins=native,unrelated_lookup_payloads_and_pointers_preserved=preserved,
  font_codes_artwork_and_advances_unchanged=True,narration_source_text_and_timing_unchanged=True,renderer_code_unchanged=True,
  dialogue_and_dlc_unchanged=True,build_sha256=sha256_file(B.OUTPUT/'build.json'),runtime_verified=False)

def verify():
 data=components();image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso';proof=json.loads(image.with_suffix('.json').read_text('utf8'))
 if proof['version']!=VERSION or proof['files_verified_each_tree']!=82 or sha256_file(image)!=proof['sha256']:raise ValueError('Final ISO proof differs')
 data['iso_verification']=proof
 shot=SHOT if SHOT.exists()else SHOT_DEST
 if shot.exists():data['reported_screenshot']=dict(path=SHOT_DEST.relative_to(ROOT).as_posix(),sha256=sha256_file(shot))
 return data

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--components',action='store_true');a=p.parse_args();data=components()if a.components else verify()
 print('Final narration lookups:',len(data['installed_lookups']),'; native draw cases:',len(data['native_caption_origins']))
 print('Unrelated dictionary entries preserved:',data['unrelated_lookup_payloads_and_pointers_preserved'])
 for r in data['native_caption_origins']:
  if r['id'].startswith('aid:30:')and r['quad']==40:print(r)
 if a.apply:
  if a.components:raise ValueError('Full ISO proof required for final evidence')
  if SHOT.exists():
   if SHOT_DEST.exists()and sha256_file(SHOT_DEST)!=sha256_file(SHOT):raise ValueError('Screenshot collision')
   SHOT_DEST.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SHOT,SHOT_DEST)
  write_json(PROOF,data)
 else:print('DRY RUN: no proof or screenshots written.')
if __name__=='__main__':main()
