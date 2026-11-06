"""Prepare and seal narration-alignment delivery; no GitHub writes."""
import argparse,json,os,re,subprocess,sys
from tools.common import ROOT,sha256_file,write_json
from tools import narration_alignment as N,verify_review50 as V

VERSION=N.VERSION;FOLDER=ROOT/'work/output/releases'/VERSION;SDK=ROOT/'work/output/release-tools-v0.5.4'
PUBLIC=ROOT/'work/output/iso/0.5.44/Tengoku-hen-English-0.5.44.iso'
READY=ROOT/'work/ui'/('local_release_'+VERSION+'.json')

def restore_public(apply=False):
 m=json.loads((ROOT/'work/output/releases/0.5.44/artifacts/BUILD-MANIFEST.json').read_text('utf8'))
 row=next(p for p in m['patches']if p['source_version']=='original');cfg=json.loads((ROOT/'config/tengoku.json').read_text('utf8'))
 source=ROOT/cfg['iso'];patch=ROOT/'work/output/releases/0.5.44/artifacts'/row['patch']
 if sha256_file(source)!=row['source_sha256']or sha256_file(patch)!=row['patch_sha256']:raise ValueError('Published original/patch identity differs')
 if PUBLIC.exists():
  if sha256_file(PUBLIC)!=row['target_sha256']:raise ValueError('Existing public image differs')
  print('Exact public 0.5.44 already available.');return
 print('Restore exact public 0.5.44 from its verified original-image patch:',row['target_sha256'])
 if not apply:print('DRY RUN: no public image restored.');return
 sys.path.insert(0,str(SDK));from retro_trans.core import engine_context,decode
 PUBLIC.parent.mkdir(parents=True,exist_ok=True);temp=PUBLIC.with_suffix('.iso.part')
 if temp.exists():raise ValueError('Preserve prior reconstruction attempt')
 with engine_context()as engine:decode(engine,source,patch,temp,row['target_bytes'])
 if temp.stat().st_size!=row['target_bytes']or sha256_file(temp)!=row['target_sha256']:raise ValueError('Restored public image differs')
 os.rename(temp,PUBLIC)
 write_json(PUBLIC.parent/'restored-from-public-patch.json',dict(version='0.5.44',sha256=row['target_sha256'],patch_sha256=row['patch_sha256'],source_iso_sha256=row['source_sha256']))
 print('Public 0.5.44 reconstructed and verified.')

def tests():
 path=ROOT/f'work/output/scratch/startup-{VERSION}-tests.log';raw=path.read_bytes();text=raw.decode('utf-16'if raw[:2]in(b'\xff\xfe',b'\xfe\xff')else'utf-8-sig')
 match=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?',text)
 if not match:raise ValueError('Full successful regression run required')
 count,skip=int(match[1]),int(match[2]or 0)
 return dict(run=count,passed=count-skip,skipped=skip,log_sha256=sha256_file(path))

def config():
 proof=json.loads(V.PROOF.read_text('utf8'));image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso'
 if proof['source_rows']!=197 or len(proof['native_caption_origins'])!=394 or not proof['font_codes_artwork_and_advances_unchanged']:raise ValueError('Narration proof incomplete')
 if sha256_file(image)!=proof['iso_verification']['sha256']:raise ValueError('Final image changed')
 tests();published=json.loads((ROOT/'work/output/releases/0.5.44/artifacts/BUILD-MANIFEST.json').read_text('utf8'));origin=next(p for p in published['patches']if p['source_version']=='original')
 if sha256_file(PUBLIC)!=origin['target_sha256']:raise ValueError('Exact public upgrade source required')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();cfg=json.loads((ROOT/'config/tengoku.json').read_text('utf8'))
 result={k:published[k]for k in ('game_id','game_name','platform')};result.update(version=VERSION,source_commit=commit,patches=[])
 for version,source in [('original',ROOT/cfg['iso']),('0.5.44',PUBLIC)]:
  result['patches'].append(dict(patch=f'SRW-Z3-2-PS3-English-{VERSION}-from-{version}.xdelta',edition='jp-bljs10299',language='en',
   source_version=version,source_format='iso',target_format='iso',source=str(source),target=str(image)))
 return result

def seal():
 sys.path.insert(0,str(SDK));from retro_trans.release import validate_directory
 assets=FOLDER/'artifacts';m=validate_directory(assets);proof=json.loads(V.PROOF.read_text('utf8'));image=proof['iso_verification']
 if len(m['patches'])!=2 or {p['source_version']for p in m['patches']}!={'original','0.5.44'}:raise ValueError('Both original/public release routes required')
 if any(p['target_sha256']!=image['sha256']or p['target_bytes']!=image['bytes']for p in m['patches']):raise ValueError('Patch targets differ from verified image')
 tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SDK,text=True).strip()
 return dict(schema=1,version=VERSION,publication='pending_explicit_user_consent',github_release_created=False,runtime_verified=False,
  source_commit=m['source_commit'],release_tool_version='0.5.4',release_tool_commit=tool_commit,iso=image,
  manifest=m,validation=json.loads((assets/'VALIDATION.json').read_text('utf8')),final_readback_sha256=sha256_file(V.PROOF),
  regression_tests=tests(),assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha256_file(p))for p in sorted(assets.iterdir())])

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=('restore-public','config','seal'));p.add_argument('--apply',action='store_true');a=p.parse_args()
 if a.action=='restore-public':restore_public(a.apply);return
 if a.action=='config':
  data=config();print('Two complete-image Retro Trans routes; source commit:',data['source_commit'])
  print('Target:',data['patches'][0]['target'])
  if a.apply:
   if FOLDER.exists():raise ValueError('Preserve existing release candidate')
   write_json(FOLDER/'release-local.json',data)
 else:
  data=seal();print('Both complete-image round trips verified. Tests:',data['regression_tests'])
  if a.apply:write_json(READY,data)
 if not a.apply:print('DRY RUN: no release metadata written; publication is not authorized.')
if __name__=='__main__':main()
