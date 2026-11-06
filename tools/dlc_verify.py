"""Read back final licensed DLCs, including text, program bytes and source ZIPs."""
import argparse,json,re
from collections import Counter
from tools import dlc,dlc_text as T,dlc_build as B,dlc_edat as ED,squad_text as S,mission_text as M
from tools.common import ROOT,sha256,sha256_file,write_json
from tools.cpk import CPK
from tools.pipeline import sfo_values

PROOF=ROOT/'work/ui'/('dlc_verified_'+dlc.VERSION+'.json')
LONG=re.compile(rb'(?<!--)\[\[(.*?)\]\]',re.S)

def project_script(original,translated,records,rendered,mapping):
 """Locate output strings anew; compare all program and unapproved string bytes."""
 source=original.decode('cp932');by_start={len(source[:r['start']].encode('cp932')):r for r in records}
 a,b=list(LONG.finditer(original)),list(LONG.finditer(translated));old_spans=[];new_spans=[];count=0;assets=0
 if len(a)!=len(b):raise ValueError('DLC long-string count changed')
 for x,y in zip(a,b):
  r=by_start.get(x.start(1));expected=T.encode_record(r['id'],rendered[r['id']],mapping)if r else x.group(1)
  if y.group(1)!=expected:raise ValueError('DLC dialogue/asset readback differs')
  count+=r is not None;assets+=r is None
  old_spans.append((x.start(1),x.end(1),b'<TEXT>'));new_spans.append((y.start(1),y.end(1),b'<TEXT>'))
 allowed={lit['start']for lit,jp in S.literals(original)}
 for table,literals,roles in M.tables(original):allowed.update(table.start(1)+lit.start(1)for lit,jp in literals)
 old_quotes,new_quotes=S.scan(original),S.scan(translated)
 if len(old_quotes)!=len(new_quotes):raise ValueError('DLC short-string count changed')
 for x,y in zip(old_quotes,new_quotes):
  if x['start'] not in allowed:
   if x['raw']!=y['raw']:raise ValueError('Unapproved DLC string changed')
  else:
   old_spans.append((x['start'],x['end'],b'<TEXT>'));new_spans.append((y['start'],y['end'],b'<TEXT>'))
 if B.apply_spans(original,old_spans)!=B.apply_spans(translated,new_spans):raise ValueError('DLC program bytes changed')
 if count!=len(records):raise ValueError('DLC dialogue identity count differs')
 return dict(dialogue=count,internal_long_strings_preserved=assets,program_bytes_preserved=True)

def verify():
 plan=B.plan();rendered=T.check()[0];build=json.loads((B.OUTPUT/'build.json').read_text('utf8'));totals=Counter();packages=[]
 if build['version']!=dlc.VERSION or len(build['packages'])!=32:raise ValueError('DLC build identity differs')
 for item,record in zip(plan['packages'],build['packages']):
  p=item['source'];code=p['code'];name=code+'.EDAT';folder=B.OUTPUT/code;source=dlc.WORK/code
  if code!=record['code']or sha256_file(ROOT/p['source_zip'])!=p['zip_sha256']:raise ValueError('DLC source ZIP changed')
  old=(source/'package/USRDIR/DLC'/name).read_bytes();raw=(folder/name).read_bytes();rap=(source/'license.rap').read_bytes()
  if sha256(old)!=p['edat_sha256']or sha256(raw)!=record['edat_sha256']:raise ValueError('DLC EDAT fingerprint differs')
  original,original_auth=ED.decode(old,rap,name,True);payload,auth=ED.decode(raw,rap,name,True)
  if sha256(original)!=p['cpk_sha256']or sha256(payload)!=record['cpk_sha256']or payload!=(folder/(code+'.cpk')).read_bytes():raise ValueError('DLC decoded archive differs')
  if raw[:128]!=old[:128]or raw[176:256]!=bytes(80):raise ValueError('DLC identity/signature policy differs')
  reports={}
  with CPK(folder/(code+'.cpk'))as arc:
   if {f['id']for f in arc.files}!=set(item['originals']):raise ValueError('DLC members differ')
   for f in arc.files:
    mid=f['id'];data=arc.read(f);old_member=item['originals'][mid]
    if data!=item['members'].get(mid,old_member):raise ValueError('DLC rendered member differs')
    if mid==0:
     if data[:40]!=old_member[:40]or data[296:]!=old_member[296:]:raise ValueError('DLC binding table changed')
     totals['titles']+=1
    elif b'\0'not in old_member:
     report=project_script(old_member,data,T.records(code,mid),rendered,plan['mapping'])
     reports[str(mid)]=report;totals.update({k:v for k,v in report.items()if type(v)is int})
    else:
     if data!=old_member:raise ValueError('DLC non-text member changed')
    totals['members']+=1
  source_sfo=(source/'package/PARAM.SFO').read_bytes();final_sfo=(folder/'PARAM.SFO').read_bytes()
  if final_sfo!=item['sfo']or sha256(final_sfo)!=record['sfo_sha256']:raise ValueError('English DLC system metadata differs')
  values=sfo_values(final_sfo)
  if values['TITLE_ID']!='NPJB00692'or values['CATEGORY']!='GD':raise ValueError('DLC installation identity changed')
  packages.append(dict(code=code,source_zip_sha256=p['zip_sha256'],source_edat_sha256=p['edat_sha256'],edat_sha256=sha256(raw),
   cpk_sha256=sha256(payload),sfo_sha256=sha256(final_sfo),source_authentication=original_auth,authentication=auth,script_reports=reports))
 if totals['dialogue']!=4666 or totals['titles']!=32:raise ValueError('DLC coverage differs')
 ui=json.loads((ROOT/'work/translation/en/dlc_ui.json').read_text('utf8'))
 return dict(schema=1,version=dlc.VERSION,counts=dict(totals,packages=32,distinct_conditions=len(ui['missions']),distinct_names=len(ui['names'])),
  build_sha256=sha256_file(B.OUTPUT/'build.json'),packages=packages,condensed_profile=build['condensed_profile'],
  supported_base_versions=plan['supported_base_versions'],font_sha256=plan['font_sha256'],source_archives_preserved=True,
  runtime_verified=False,console_compatibility_verified=False,sony_signatures=False)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args();data=verify()
 print(json.dumps(data['counts'],sort_keys=True));print('All final files read back; gameplay remains unverified.')
 if args.apply:write_json(PROOF,data)
 else:print('DRY RUN: no proof written.')
if __name__=='__main__':main()
