"""Carry sealed 0.5.48, adding narration markers without changing renderer code."""
import argparse,copy,json,shutil,struct
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import narration_alignment as N,ui_hook as H,title_screen as T,eff_art as EF
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION=N.VERSION;BASE=ROOT/'work/output/builds/0.5.48';OUTPUT=ROOT/'work/output/builds'/VERSION
CHANGED={'EBOOT.BIN','EFFPS3.CPK'}

def dictionary(elf,b):
 rd=H._reader(elf,H._headers(elf)[2]);before=H.slot_map(rd);mask,slots=struct.unpack('>II',rd(H.EXT_VA+8,8));locations={}
 for i in range(mask+1):
  _,key,ptr,n,_=struct.unpack('>IIIHH',rd(slots+i*16,16))
  if key:locations[rd(key,n)]=slots+i*16
 out=bytearray(elf);spans=[];table=b['executable']['ui_hook']['table'];cursor=(table['used_bytes']+15)&~15;values={};cases=N.rows(b['mapping'])
 def put(va,data):
  seg=next(p for p in H._headers(elf)[2]if p[3]<=va<p[3]+p[5]);at=seg[2]+va-seg[3]
  out[at:at+len(data)]=data;spans.append([at,at+len(data)])
 for row in cases:
  key=row['key'];old=row['old']+b'\0';new=row['encoded']+b'\0';ptr=before[key]
  if rd(ptr,len(old))!=old:raise ValueError('Parent narration binding differs: '+row['id'])
  if new not in values:
   if cursor+len(new)>table['ext_size']or rd(H.EXT_VA+cursor,len(new))!=bytes(len(new)):raise ValueError('Reserved dictionary space unavailable')
   values[new]=H.EXT_VA+cursor;put(values[new],new);cursor+=len(new)
  put(locations[key]+8,struct.pack('>I',values[new]))
 restored=bytearray(out)
 for a,z in spans:restored[a:z]=elf[a:z]
 if restored!=elf:raise ValueError('Executable changed outside narration dictionary edits')
 result=bytes(out);final=H._reader(result,H._headers(result)[2]);after=H.slot_map(final);targets={r['key']for r in cases}
 if set(before)!=set(after):raise ValueError('Dictionary identities changed')
 for key,ptr in before.items():
  size=H.extent(rd(ptr,H.MAX_ENGLISH_EXTENT+2),cap=H.MAX_ENGLISH_EXTENT)+1
  if final(ptr,size)!=rd(ptr,size):raise ValueError('Original English payload overwritten')
  if key not in targets and after[key]!=ptr:raise ValueError('Unrelated lookup moved')
 return result,dict(rows=[{k:v.hex()if type(v)is bytes else v for k,v in r.items()}for r in cases],
  modified_file_ranges=spans,updated_keys=len(targets),unrelated_keys_preserved=len(before)-len(targets),
  original_payloads_preserved=len(before),used_bytes=cursor,headroom_bytes=table['ext_size']-cursor,
  source_timing_and_text_unchanged=True,renderer_code_unchanged=True)

def plan():
 b=json.loads((BASE/'build.json').read_text('utf8'));ready=json.loads((ROOT/'work/ui/local_release_0.5.48.json').read_text('utf8'))
 if sha256_file(ROOT/'work/ui/review48_verified_0.5.48.json')!=ready['final_readback_sha256']:raise ValueError('Parent proof changed')
 for name,digest in b['outputs'].items():
  if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
 elf,report=dictionary((BASE/'EBOOT.BIN').read_bytes(),b)
 raw=EF.source_members(EF._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
 title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
 return dict(prior=b,elf=elf,narration=report,title=title,title_info=info)

def build(p):
 if OUTPUT.exists():raise ValueError('Preserve existing candidate')
 OUTPUT.mkdir(parents=True);b=copy.deepcopy(p['prior'])
 for name in b['outputs']:
  if name not in CHANGED:shutil.copyfile(BASE/name,OUTPUT/name)
 for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,OUTPUT/name)
 (OUTPUT/'EBOOT.BIN').write_bytes(p['elf'])
 members={T.MEMBER:p['title']}
 with CPK(BASE/'EFFPS3.CPK')as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
 build_cpk(BASE/'EFFPS3.CPK',OUTPUT/'EFFPS3.CPK',members,compress=compressed)
 isolation=compare(BASE/'EFFPS3.CPK',OUTPUT/'EFFPS3.CPK',members)
 b.update(version=VERSION,title_screen=p['title_info'],narration_alignment=p['narration'],runtime_verified=False,layout_verified=False)
 b['executable']['output_sha256']=sha256(p['elf'])
 for k in ('used_bytes','headroom_bytes'):b['executable']['ui_hook']['table'][k]=p['narration'][k]
 for name in b['outputs']:
  digest=sha256_file(OUTPUT/name)
  if name not in CHANGED and digest!=p['prior']['outputs'][name]:raise ValueError('Carried asset differs')
  b['outputs'][name]=digest
 b['incremental_build']=dict(parent_version='0.5.48',parent_build_sha256=sha256_file(BASE/'build.json'),unchanged_fonts=True,
  unchanged_mapping=True,unchanged_advances=True,archive_isolation={'EFFPS3.CPK':isolation})
 write_json(OUTPUT/'build.json',b)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan();r=data['narration']
 print('Center',len(r['rows']),'timed captions;',r['updated_keys'],'keys;',r['unrelated_keys_preserved'],'unrelated keys unchanged.')
 for row in r['rows']:
  if row['member']==30:print(row['id'],repr(row['en']),'bounds',row['left'],row['right'])
 print('Dictionary headroom:',r['headroom_bytes'],'bytes. Fonts, renderer and narration timing unchanged.')
 if a.apply:build(data);print('Built 0.5.50.')
 else:print('DRY RUN: no game assets changed.')
if __name__=='__main__':main()
