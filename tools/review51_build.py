"""Carry 0.5.50; add complete DLC menu consumers without changing fonts."""
import argparse,copy,json,struct,shutil
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import ui_hook as H,review51_text as T,review51_native as N,eboot_text as E,ui_runtime as R
from tools import ui_layout_text as U,title_screen as TS,eff_art as EF
from tools.pipeline import config
from tools.cpk import CPK
from tools.cpkpatch import build as cpk_build
from tools.verify_archives import compare
VERSION=T.VERSION;BASE=ROOT/'work/output/builds/0.5.50';OUTPUT=ROOT/'work/output/builds'/VERSION
CHANGED={'EBOOT.BIN','AIDDATAPACK.CPK','EFFPS3.CPK'}
RX_VA=0x1800000

def executable(elf,b):
 phoff,shoff,phs,shs=H._headers(elf);p=phs[1];end=p[2]+p[5];grow=0x10000
 if phs[2][0]!=1 or phs[2][5:7]!=(0,0):raise ValueError('No unused ELF LOAD for DLC native adapters')
 if p[3]+p[6]+grow>=RX_VA:raise ValueError('DLC code/data overlap')
 out=bytearray(elf[:end])+bytearray(grow)+bytearray(elf[end:]);spans=[]
 struct.pack_into('>Q',out,40,shoff+grow)
 H.PH.pack_into(out,phoff+H.PH.size,*(p[:5]+(p[5]+grow,p[6]+grow,p[7])))
 for i,s in enumerate(shs):
  row=list(s)
  if s[1]!=8 and s[5]and not s[2]&2:row[4]+=grow
  H.SH.pack_into(out,shoff+grow+i*H.SH.size,*row)
 original=H.PREPARED.read_bytes();rd=H._reader(elf,phs);mask,slots=struct.unpack('>II',rd(H.EXT_VA+8,8));prior=H.slot_map(rd)
 table=b['executable']['ui_hook']['table'];cursor=(table['used_bytes']+15)&~15;maximum=table['ext_size']+grow;locations={};occupied=set()
 for i in range(mask+1):
  _,key,ptr,n,_=struct.unpack('>IIIHH',rd(slots+i*16,16))
  if key:locations[rd(key,n)]=slots+i*16;occupied.add(i)
 def put(va,raw):
  at=p[2]+va-p[3]
  if not p[3]<=va< p[3]+p[5]+grow or at+len(raw)>end+grow:raise ValueError('DLC edit outside data LOAD')
  out[at:at+len(raw)]=raw;spans.append([at,at+len(raw)])
 def allocate(raw):
  nonlocal cursor
  if cursor+len(raw)>maximum:raise ValueError('DLC relocated text exceeds reserved extension')
  ptr=H.EXT_VA+cursor;at=p[2]+ptr-p[3]
  if any(out[at:at+len(raw)]):raise ValueError('DLC allocation overwrites existing data')
  put(ptr,raw);cursor+=len(raw);return ptr
 entries,bounds=T.entries(b['mapping']);cases=[];changed=set();added=0
 for row in entries:
  key,en=row['key'],row['english']
  if H.extent(key+b'\0')!=len(key)or H.check_english(key,en):raise ValueError('Invalid DLC draw key')
  if key in prior:location=locations[key];changed.add(key)
  else:
   h=H.fnv1a(key);i=h&mask
   while i in occupied:i=(i+1)&mask
   occupied.add(i);kp=allocate(key+b'\0');location=slots+i*16;put(location,struct.pack('>IIIHH',h,kp,0,len(key),0));added+=1
  ep=allocate(en+b'\0');put(location+8,struct.pack('>I',ep));cases.append(dict(id=row['id'],key_hex=key.hex(),encoded_hex=en.hex()))
 if len(occupied)/(mask+1)>.5:raise ValueError('DLC dictionary load exceeds certified limit')
 prompts=[]
 source={r['va']:r for r in E.records()}
 for va,row in T.checked()['rows'].items():
  if row['kind']!='prompt':continue
  r=source[va];raw=row['en'].encode('utf8')+b'\0';payload=raw+bytes(max(0,len(r['jp'].encode('utf8'))+1-len(raw)))
  refs=R.toc_references(original,int(va,16))
  if not refs:raise ValueError('DLC prompt lacks native consumer: '+va)
  pointer=allocate(payload)
  for ref in refs:put(ref['va'],struct.pack('>I',pointer))
  prompts.append(dict(va=va,en=row['en'],pointer=pointer,bytes=len(payload),consumer_loads=[a for ref in refs for a in ref['consumer_loads']]))
 titles={r['source_pointer']:allocate(r['en'].encode('ascii')+b'\0')for r in N.titles()}
 parts={i:allocate(en.encode('ascii')+b'\0')for i,en in N.parts().items()}
 code=N.part_stub(RX_VA,parts);title_va=(RX_VA+len(code)+15)&~15;code+=bytes(title_va-RX_VA-len(code))+N.title_stub(title_va,titles)
 rx_offset=(len(out)+0xffff)&~0xffff
 out+=bytes(rx_offset-len(out))+code
 H.PH.pack_into(out,phoff+2*H.PH.size,1,phs[0][1],rx_offset,RX_VA,RX_VA,len(code),len(code),0x10000)
 for sites,old,target in ((N.PART_SITES,0x15d6a4,RX_VA),(N.TITLE_SITES,0x15161c,title_va)):
  for va in sites:
   at=va-0x10000
   if elf[at:at+4]!=struct.pack('>I',H.branch(va,old)|1):raise ValueError('Native DLC call site differs')
   out[at:at+4]=struct.pack('>I',H.branch(va,target)|1);spans.append([at,at+4])
 # Restore every permitted change to independently prove byte isolation.
 restored=bytearray(out[:end]+out[end+grow:len(elf)+grow])
 for a,z in spans:
  if a<end:restored[a:z]=elf[a:z]
 restored[40:48]=elf[40:48]
 restored[phoff+H.PH.size:phoff+3*H.PH.size]=elf[phoff+H.PH.size:phoff+3*H.PH.size]
 restored[shoff:shoff+len(shs)*H.SH.size]=elf[shoff:shoff+len(shs)*H.SH.size]
 if restored!=elf:raise ValueError('DLC executable edits escape approved spans')
 final=bytes(out);read=H._reader(final,H._headers(final)[2]);after=H.slot_map(read)
 for key,ptr in prior.items():
  if key not in changed and after[key]!=ptr:raise ValueError('Unrelated DLC lookup moved')
  size=H.extent(rd(ptr,min(H.MAX_ENGLISH_EXTENT+2,p[3]+p[5]-ptr)),cap=H.MAX_ENGLISH_EXTENT)+1
  if read(ptr,size)!=rd(ptr,size):raise ValueError('Original lookup payload overwritten')
 return final,dict(draw_cases=cases,bounds=bounds,prompts=prompts,titles=len(titles),parts=len(parts),added_keys=added,
  entries=len(after),old_entries=len(prior),changed_old_keys=len(changed),unrelated_keys_preserved=len(prior)-len(changed),
  used_bytes=cursor,ext_size=maximum,headroom_bytes=maximum-cursor,modified_file_ranges=spans,
  data_growth=grow,old_data_end=end,new_code_va=RX_VA,new_code_offset=rx_offset,new_code_bytes=len(code),title_adapter_va=title_va,
  original_payloads_preserved=True,fonts_and_renderer_unchanged=True,source_records_and_mission_logic_unchanged=True)

def plan():
 b=json.loads((BASE/'build.json').read_text('utf8'));ready=json.loads((ROOT/'work/ui/local_release_0.5.50.json').read_text('utf8'))
 if ready['iso']['version']!= '0.5.50':raise ValueError('Wrong parent seal')
 proof=ROOT/'work/ui/review50_verified_0.5.50.json'
 if sha256_file(proof)!=ready['final_readback_sha256']or json.loads(proof.read_text('utf8'))['build_sha256']!=sha256_file(BASE/'build.json'):
  raise ValueError('Certified parent build/proof changed')
 for name,digest in b['outputs'].items():
  if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
 elf,report=executable((BASE/'EBOOT.BIN').read_bytes(),b)
 ui=U.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
 raw=EF.source_members(EF._settings(),[TS.MEMBER],{TS.MEMBER:TS.SOURCE_SHA})[TS.MEMBER]
 title,pixels,_,info=TS.render(raw,VERSION);TS.verify(raw,title,pixels)
 return dict(prior=b,elf=elf,report=report,ui=ui,title=title,title_info=info)

def build(p):
 if OUTPUT.exists():raise ValueError('Preserve existing 0.5.51 candidate')
 OUTPUT.mkdir(parents=True);b=copy.deepcopy(p['prior'])
 for name in b['outputs']:
  if name not in CHANGED:shutil.copyfile(BASE/name,OUTPUT/name)
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,OUTPUT/name)
 (OUTPUT/'EBOOT.BIN').write_bytes(p['elf']);archives={}
 for name,members in {'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},'EFFPS3.CPK':{TS.MEMBER:p['title']}}.items():
  with CPK(BASE/name)as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
  cpk_build(BASE/name,OUTPUT/name,members,compress=compressed);archives[name]=compare(BASE/name,OUTPUT/name,members)
 b.update(version=VERSION,title_screen=p['title_info'],dlc_menu=p['report'],runtime_verified=False,layout_verified=False)
 b['executable']['output_sha256']=sha256(p['elf'])
 for key in ('entries','used_bytes','ext_size','headroom_bytes'):b['executable']['ui_hook']['table'][key]=p['report'][key]
 b['executable']['ui_hook']['table']['load_factor']=p['report']['entries']/b['executable']['ui_hook']['table']['slots']
 for name in b['outputs']:b['outputs'][name]=sha256_file(OUTPUT/name)
 b['incremental_build']=dict(parent_version='0.5.50',parent_build_sha256=sha256_file(BASE/'build.json'),unchanged_fonts=True,archive_isolation=archives)
 write_json(OUTPUT/'build.json',b)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');a=parser.parse_args();p=plan();r=p['report']
 print('DLC menu:',len(r['draw_cases']),'draw keys;',len(r['prompts']),'native prompts;',r['titles'],'titles;',r['parts'],'reward names.')
 print('Data growth:',r['data_growth'],'new RX code:',r['new_code_bytes'],'bytes. Fonts/renderer unchanged.')
 if a.apply:build(p);print('Built 0.5.51.')
 else:print('DRY RUN: no game assets written.')
if __name__=='__main__':main()
