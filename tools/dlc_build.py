"""Rebuild all authored DLC into licensed EDAT files; dry run by default."""
import argparse,json,struct
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import dlc,dlc_text as T,dlc_ui as U,dlc_edat as ED
from tools import dialogue_build as D,library_build as L,squad_text as S,mission_text as M,ui_hook as H
from tools.ui_description_layout import advance
from tools.library_text import GLOSSARY,Resolver
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare
from tools.pipeline import sfo_values
BASE=ROOT/'work/output/builds/0.5.48'
OUTPUT=ROOT/'work/output/dlc'/dlc.VERSION

def apply_spans(raw,edits):
 out=bytearray();pos=0
 for start,end,data in sorted(edits):
  if start<pos or end<start:raise ValueError('Overlapping DLC text changes')
  out+=raw[pos:start]+data;pos=end
 out+=raw[pos:];return bytes(out)

def rebuild_script(p,m,rendered,mapping,ui,res):
 raw=(ROOT/m['path']).read_bytes()
 if b'\0'in raw:return raw,dict(dialogue=0,missions=0,names=0)
 text=raw.decode('cp932');edits=[];dialogue=0;missions=0;names=0
 for r in T.records(p['code'],m['id']):
  encoded=T.encode_record(r['id'],rendered[r['id']],mapping)
  if not D.lua_safe(encoded):raise ValueError('English would break Lua string: '+r['id'])
  a=len(text[:r['start']].encode('cp932'));z=len(text[:r['end']].encode('cp932'))
  edits.append((a,z,encoded));dialogue+=1
 for table,lits,roles in M.tables(raw):
  for lit,jp in lits:
   en=L.expand(ui['missions'][jp]['en'],res)
   en=M.wrap_live(en,advance)if any(t in jp for t in M.PLACEHOLDERS)else M.wrap(en,advance)
   a=table.start(1)+lit.start(1);z=table.start(1)+lit.end(1);encoded=L.encode(en,mapping)
   edits.append((a,z,M.lua_literal(encoded)));missions+=1
 for lit,jp in S.literals(raw):
  en=L.expand(ui['names'][jp]['en'],res);encoded=L.encode(en,mapping)
  if len(encoded)>S.MAX_BYTES:raise ValueError('DLC team name exceeds save field: '+jp)
  edits.append((lit['start'],lit['end'],M.lua_literal(encoded)));names+=1
 result=apply_spans(raw,edits)
 # Every quoted literal is read back with the native Lua escape rules.
 old_lits,new_lits=S.scan(raw),S.scan(result)
 if len(old_lits)!=len(new_lits):raise ValueError('DLC Lua literal count changed')
 wanted={a:data for a,z,data in edits}
 for a,z in zip(old_lits,new_lits):
  expected=M.unescape_bytes(wanted[a['start']])if a['start']in wanted else M.unescape_bytes(a['raw'])
  if M.unescape_bytes(z['raw'])!=expected:raise ValueError('DLC literal readback mismatch')
 if [v.group(2)for v in M.OP.finditer(raw)]!=[v.group(2)for v in M.OP.finditer(result)]:raise ValueError('DLC mission logic changed')
 # Program bytes are copied directly between the approved, disjoint text spans.
 return result,dict(dialogue=dialogue,missions=missions,names=names,approved_text_spans=len(edits),outside_text_preserved=True)

def title_member(raw,row,mapping):
 before=raw[40:168].split(b'\0')[0].decode('cp932');other=raw[168:296].split(b'\0')[0].decode('utf8')
 if before!=row['jp']or other!=row['jp']:raise ValueError('DLC native title changed')
 encoded=L.encode(row['en'],mapping);utf8=row['utf8_source'].encode('utf8')
 if max(len(encoded),len(utf8))>=128:raise ValueError('DLC title exceeds the native fixed field')
 result=apply_spans(raw,[(40,168,encoded+bytes(128-len(encoded))),(168,296,utf8+bytes(128-len(utf8)))])
 if result[:40]!=raw[:40]or result[296:]!=raw[296:]:raise ValueError('DLC member binding table changed')
 return result

def english_sfo(raw):
 if raw[:4]!=b'\0PSF':raise ValueError('Bad source DLC metadata')
 _,_,_,count=struct.unpack_from('<4I',raw,4);entries=[];keys=bytearray();values=bytearray()
 for i in range(count):
  ko,fmt,size,maximum,vo=struct.unpack_from('<HHIII',raw,20+i*16);kb,vb=struct.unpack_from('<II',raw,8)
  key=raw[kb+ko:raw.index(b'\0',kb+ko)].decode('ascii');value=raw[vb+vo:vb+vo+size]
  if key in ('TITLE','TITLE_00'):value=b'Super Robot Taisen Z3: Tengoku-hen DLC (English 0.5.49)\0'
  key_at=len(keys);keys+=key.encode()+b'\0';values+=bytes(-len(values)%4);value_at=len(values)
  limit=max(maximum,(len(value)+3)&~3);values+=value+bytes(limit-len(value));entries.append((key_at,fmt,len(value),limit,value_at))
 keybase=20+16*count;valuebase=(keybase+len(keys)+3)&~3
 out=bytearray(struct.pack('<4s4I',b'\0PSF',0x101,keybase,valuebase,count))
 for e in entries:out+=struct.pack('<HHIII',*e)
 out+=keys+bytes(valuebase-len(out)-len(keys))+values
 old,new=sfo_values(raw),sfo_values(out)
 for k,v in old.items():
  if k not in ('TITLE','TITLE_00')and new[k]!=v:raise ValueError('DLC install identity changed')
 return bytes(out)

def plan():
 rendered,coverage=T.check()
 if coverage['errors']or coverage['missing']:raise ValueError(coverage['errors'][:10])
 ui=json.loads(U.DEST.read_text('utf8'))
 if ui!=U.plan():raise ValueError('DLC UI catalog is stale')
 build=json.loads((BASE/'build.json').read_text('utf8'));mapping=build['mapping'];res=Resolver(json.loads(GLOSSARY.read_text('utf8'))['terms'])
 # Both the public patch and the prepared build must interpret these glyphs identically.
 public=ROOT/'work/output/builds/0.5.44';pb=json.loads((public/'build.json').read_text('utf8'))
 if mapping!=pb['mapping']or build['outputs']['TPACKPS3.CPK']!=pb['outputs']['TPACKPS3.CPK']:raise ValueError('Required English font versions differ')
 elf=(public/'EBOOT.BIN').read_bytes();rd=H._reader(elf,H._headers(elf)[2]);slots=H.slot_map(rd);packages=[]
 for p in sorted(T.inventory()['packages'],key=lambda p:p['code']):
  folder=dlc.WORK/p['code'];source=folder/(p['code']+'.cpk')
  if sha256_file(source)!=p['cpk_sha256']:raise ValueError('DLC source archive changed')
  originals={};members={};reports={}
  for m in p['members']:
   raw=(ROOT/m['path']).read_bytes()
   if sha256(raw)!=m['sha256']:raise ValueError('DLC source member changed')
   if m['id']==0:
    row=ui['titles'][p['code']];new=title_member(raw,row,mapping)
    key=H.utf8_key(row['utf8_source'].encode('utf8'),H.PREPARED.read_bytes());en=L.encode(row['en'],mapping)
    if key not in slots or rd(slots[key],len(en)+1)!=en+b'\0':raise ValueError('Public English build lacks DLC UTF-8 title')
    report=dict(title=row['en'],native_utf8_lookup_verified=True)
   else:new,report=rebuild_script(p,m,rendered,mapping,ui,res)
   originals[m['id']]=raw;reports[str(m['id'])]=report
   if new!=raw:members[m['id']]=new
  sfo=english_sfo((folder/'package/PARAM.SFO').read_bytes())
  packages.append(dict(source=p,originals=originals,members=members,member_reports=reports,sfo=sfo))
 return dict(packages=packages,coverage=coverage,font_sha256=build['outputs']['TPACKPS3.CPK'],mapping=mapping,
  supported_base_versions=['0.5.44','0.5.48'],condensed_profile=dict(id=T.CONDENSED_ID,source_sha=T.CONDENSED_SHA,scale=.85,existing_glyphs_only=True))

def build(plan):
 if OUTPUT.exists():raise ValueError('Preserve immutable DLC candidate; choose a new version')
 OUTPUT.mkdir(parents=True);report={k:v for k,v in plan.items()if k not in ('packages','mapping')};report.update(schema=1,version=dlc.VERSION,packages=[],runtime_verified=False)
 for item in plan['packages']:
  p=item['source'];code=p['code'];source=dlc.WORK/code;folder=OUTPUT/code;folder.mkdir()
  cpk=folder/(code+'.cpk');build_cpk(source/(code+'.cpk'),cpk,item['members'],compress=True)
  isolation=compare(source/(code+'.cpk'),cpk,item['members']);name=code+'.EDAT';original=(source/'package/USRDIR/DLC'/name).read_bytes();rap=(source/'license.rap').read_bytes()
  output,auth=ED.rebuild(original,cpk.read_bytes(),rap,name);edat=folder/name;edat.write_bytes(output)
  plain,_=ED.decode(edat.read_bytes(),rap,name,True)
  if plain!=cpk.read_bytes():raise ValueError('Final DLC EDAT readback failed')
  with CPK(cpk)as arc:
   for f in arc.files:
    expected=item['members'].get(f['id'],item['originals'][f['id']])
    if arc.read(f)!=expected:raise ValueError('Final DLC member differs')
  (folder/'PARAM.SFO').write_bytes(item['sfo'])
  report['packages'].append(dict(code=code,content_id=p['content_id'],source_edat_sha256=p['edat_sha256'],
   edat_sha256=sha256(output),edat_bytes=len(output),cpk_sha256=sha256(plain),sfo_sha256=sha256(item['sfo']),
   changed_members=sorted(item['members']),members=item['member_reports'],archive_isolation=isolation,authentication=auth))
  print(code,'verified',len(output),'bytes',flush=True)
 write_json(OUTPUT/'build.json',report)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
 print('DLC packages',len(data['packages']),'Dialogue',data['coverage']['rendered'],'all player-text plans verified')
 if a.apply:build(data)
 else:print('DRY RUN: 32 licensed EDATs and English system metadata; no originals, licenses or installed games changed.')
if __name__=='__main__':main()
