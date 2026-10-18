"""Add verified name/title keys in reserved space; carry the certified 0.5.47 assets."""
import argparse,copy,json,shutil,struct
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import review48_content as C,review48_text as R,ui_hook as H,ui_layout_text as U
from tools import title_screen as T,eff_art as EF
from tools.pipeline import config
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare
VERSION=R.VERSION;BASE=ROOT/'work/output/builds/0.5.47'
CHANGED={'EBOOT.BIN','AIDDATAPACK.CPK','EFFPS3.CPK'}

def extend_dictionary(elf,b):
 rd=H._reader(elf,H._headers(elf)[2]);mask,slots=struct.unpack('>II',rd(H.EXT_VA+8,8));prior=H.slot_map(rd)
 english={};occupied={};out=bytearray(elf);spans=[];cases=[];table=b['executable']['ui_hook']['table'];cursor=(table['used_bytes']+15)&~15
 for i in range(mask+1):
  raw=rd(slots+i*16,16);h,key,en,n,flags=struct.unpack('>IIIHH',raw)
  if not key:continue
  occupied[i]=raw;payload=rd(en,H.MAX_ENGLISH_EXTENT+2);size=H.extent(payload,cap=H.MAX_ENGLISH_EXTENT)
  english.setdefault(payload[:size],en)
 def put(va,raw):
  seg=next(p for p in H._headers(elf)[2]if p[3]<=va<p[3]+p[5]);at=seg[2]+va-seg[3];out[at:at+len(raw)]=raw;spans.append([at,at+len(raw)])
 def allocate(raw):
  nonlocal cursor
  if cursor+len(raw)>table['ext_size']or rd(H.EXT_VA+cursor,len(raw))!=bytes(len(raw)):raise ValueError('Reserved dictionary space unavailable')
  p=H.EXT_VA+cursor;put(p,raw);cursor+=len(raw);return p
 entries=C.hook_entries(H.PREPARED.read_bytes(),b['mapping']);probes=[];added=0
 for row in entries:
  key,en=row['key'],row['english']
  if H.extent(key+b'\0')!=len(key)or H.check_english(key,en):raise ValueError('Invalid heading/name lookup')
  if key in prior:
   if rd(prior[key],len(en)+1)!=en+b'\0':raise ValueError('Existing lookup has conflicting English: '+row['id'])
  else:
   h=H.fnv1a(key);i=h&mask;probe=0
   while i in occupied:i=(i+1)&mask;probe+=1
   kp=allocate(key+b'\0');vp=english.get(en)
   if vp is None:vp=allocate(en+b'\0');english[en]=vp
   raw=struct.pack('>IIIHH',h,kp,vp,len(key),0);put(slots+i*16,raw);occupied[i]=raw;added+=1;probes.append(probe)
  cases.append(dict(id=row['id'],key_hex=key.hex(),encoded_hex=en.hex()))
 if len(occupied)/(mask+1)>.5:raise ValueError('Dictionary load factor exceeds certified bound')
 restored=bytearray(out)
 for a,z in spans:restored[a:z]=elf[a:z]
 if restored!=elf:raise ValueError('Unrelated executable bytes changed')
 result=bytes(out);final=H._reader(result,H._headers(result)[2]);after=H.slot_map(final)
 if any(after.get(key)!=va for key,va in prior.items()):raise ValueError('Carried lookup addresses changed')
 hook=b['executable']['ui_hook'];runner=H._Runner(result,int(hook['stub_va'],16),hook['stub_bytes'])
 for row in entries:
  ptr,n=runner.run(row['key']+b'\0')
  if final(ptr,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Installed name/title lookup failed')
 return result,dict(cases=cases,added_keys=added,old_keys_preserved=len(prior),entries=len(after),slots=mask+1,
  load_factor=len(after)/(mask+1),max_added_probe=max(probes or[0]),used_bytes=cursor,
  headroom_bytes=table['ext_size']-cursor,modified_file_ranges=spans,existing_payload_addresses_preserved=True)

def plan():
 from tools.game_build import VERSION as active
 if active!=VERSION:raise ValueError('Wrong build version')
 b=json.loads((BASE/'build.json').read_text('utf8'));proof=ROOT/'work/ui/review47_verified_0.5.47.json';ready=json.loads((ROOT/'work/ui/local_release_0.5.47.json').read_text('utf8'))
 if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Certified parent proof changed')
 for name,digest in b['outputs'].items():
  if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
 elf,hook=extend_dictionary((BASE/'EBOOT.BIN').read_bytes(),b);ui=U.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
 raw=EF.source_members(EF._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
 title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
 return dict(prior=b,elf=elf,hook=hook,ui=ui,title=title,title_info=info,parent_proof_sha256=sha256_file(proof))

def build(p):
 folder=ROOT/'work/output/builds'/VERSION
 if folder.exists():raise ValueError('Preserve existing candidate')
 folder.mkdir(parents=True);b=copy.deepcopy(p['prior'])
 for name in b['outputs']:
  if name not in CHANGED:shutil.copyfile(BASE/name,folder/name)
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,folder/name)
 (folder/'EBOOT.BIN').write_bytes(p['elf']);archives={}
 for name,members in {'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},'EFFPS3.CPK':{T.MEMBER:p['title']}}.items():
  with CPK(BASE/name)as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
  build_cpk(BASE/name,folder/name,members,compress=compressed);archives[name]=compare(BASE/name,folder/name,members)
 b.update(version=VERSION,title_screen=p['title_info'],stage_heading_coverage=C.report(),runtime_verified=False,layout_verified=False,
  ui_context_text=p['ui']['report']['context_text'],review48=dict(hook=p['hook'],warning=R.plan()['bounds']))
 b['executable']['output_sha256']=sha256(p['elf']);b['executable']['review48_dictionary']=p['hook']
 for key in ('entries','slots','load_factor','used_bytes','headroom_bytes'):b['executable']['ui_hook']['table'][key]=p['hook'][key]
 b['executable']['ui_hook']['table']['max_probe']=max(b['executable']['ui_hook']['table']['max_probe'],p['hook']['max_added_probe'])
 b['extra_art']['AIDDATAPACK.CPK']=dict(archive=archives['AIDDATAPACK.CPK'],members_verified=U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui']))
 b['extra_art']['EFFPS3.CPK']=dict(archive=archives['EFFPS3.CPK'],title=p['title_info'])
 for name in b['outputs']:
  digest=sha256_file(folder/name)
  if name not in CHANGED and digest!=p['prior']['outputs'][name]:raise ValueError('Carried asset differs')
  b['outputs'][name]=digest
 b['incremental_build']=dict(parent_version='0.5.47',parent_build_sha256=sha256_file(BASE/'build.json'),parent_proof_sha256=p['parent_proof_sha256'],
  unchanged_fonts=True,unchanged_mapping=True,unchanged_advances=True,archive_isolation=archives)
 write_json(folder/'build.json',b)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
 print('New keys:',data['hook']['added_keys'],'Carried keys:',data['hook']['old_keys_preserved'],'Free bytes:',data['hook']['headroom_bytes'])
 print('Stages:',C.report());print('Warning:',R.plan()['bounds'])
 if a.apply:build(data);print('Built and read back 0.5.48.',flush=True)
 else:print('DRY RUN: no game assets written.')
if __name__=='__main__':main()
