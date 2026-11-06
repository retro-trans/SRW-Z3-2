"""Prepare and seal complete-image DLC-menu patches without publishing."""
import argparse,json,re,subprocess,sys
from tools.common import ROOT,sha256_file,write_json
from tools import review51_text as T,verify_review51 as V
VERSION=T.VERSION;FOLDER=ROOT/'work/output/releases'/VERSION;SDK=ROOT/'work/output/release-tools-v0.5.4'
PUBLIC=ROOT/'work/output/iso/0.5.44/Tengoku-hen-English-0.5.44.iso'
READY=ROOT/f'work/ui/local_release_{VERSION}.json'

def tests():
 path=ROOT/f'work/output/scratch/startup-{VERSION}-tests.log';raw=path.read_bytes()
 text=raw.decode('utf-16'if raw[:2]in(b'\xff\xfe',b'\xfe\xff')else'utf-8-sig')
 m=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?',text)
 if not m:raise ValueError('Successful full regression required')
 count,skip=int(m[1]),int(m[2]or 0)
 return dict(run=count,passed=count-skip,skipped=skip,log_sha256=sha256_file(path))

def inputs():
 prior=json.loads((ROOT/'work/ui/local_release_0.5.44.json').read_text('utf8'))['manifest']
 original=next(p for p in prior['patches']if p['source_version']=='original')
 cfg=json.loads((ROOT/'config/tengoku.json').read_text('utf8'))
 return prior,[(dict(version='original',path=ROOT/cfg['iso'],sha256=original['source_sha256'],bytes=original['source_bytes'])),
  dict(version='0.5.44',path=PUBLIC,sha256=original['target_sha256'],bytes=original['target_bytes'])]

def config():
 proof=json.loads(V.PROOF.read_text('utf8'));image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso'
 if proof['category_entries']!=74 or len(proof['native_confirmation_cases'])!=70 or not proof['fonts_and_narration_unchanged']:raise ValueError('Incomplete final DLC menu proof')
 if str(image)!=proof['iso_verification']['image']or image.stat().st_size!=proof['iso_verification']['bytes']:raise ValueError('Final image identity differs')
 tests();prior,sources=inputs();result={k:prior[k]for k in ('game_id','game_name','platform')}
 result.update(version=VERSION,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),patches=[])
 for source in sources:
  if source['path'].stat().st_size!=source['bytes']:raise ValueError('Incorrect patch source size')
  result['patches'].append(dict(patch=f"SRW-Z3-2-PS3-English-{VERSION}-from-{source['version']}.xdelta",edition='jp-bljs10299',language='en',
   source_version=source['version'],source_format='iso',target_format='iso',source=str(source['path']),target=str(image)))
 # The official SDK hashes every complete input; seal() checks all resulting
 # identities against the published sources and independently verified target.
 return result

def seal():
 sys.path.insert(0,str(SDK));from retro_trans.release import validate_directory
 assets=FOLDER/'artifacts';manifest=validate_directory(assets);proof=json.loads(V.PROOF.read_text('utf8'));iso=proof['iso_verification'];_,sources=inputs()
 if len(manifest['patches'])!=2 or {r['source_version']for r in manifest['patches']}!={'original','0.5.44'}:raise ValueError('Both public delivery routes required')
 expected={r['version']:r for r in sources}
 for row in manifest['patches']:
  source=expected[row['source_version']]
  if row['source_sha256']!=source['sha256']or row['source_bytes']!=source['bytes']:raise ValueError('Patch source differs from published identity')
  if row['target_sha256']!=iso['sha256']or row['target_bytes']!=iso['bytes']:raise ValueError('Patch target differs from final proof')
 return dict(schema=1,version=VERSION,publication='pending_explicit_user_consent',github_release_created=False,runtime_verified=False,
  source_commit=manifest['source_commit'],release_tool_version='0.5.4',release_tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SDK,text=True).strip(),
  iso=iso,manifest=manifest,validation=json.loads((assets/'VALIDATION.json').read_text('utf8')),regression_tests=tests(),
  final_readback_sha256=sha256_file(V.PROOF),assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha256_file(p))for p in sorted(assets.iterdir())])

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=('config','seal'));p.add_argument('--apply',action='store_true');a=p.parse_args()
 if a.action=='config':
  data=config();print('Two complete-image routes; source commit:',data['source_commit']);print('Target:',data['patches'][0]['target'])
  if a.apply:
   if FOLDER.exists():raise ValueError('Preserve existing candidate delivery')
   write_json(FOLDER/'release-local.json',data)
 else:
  data=seal();print('Both published-source round trips verified. Tests:',data['regression_tests'])
  if a.apply:write_json(READY,data)
 if not a.apply:print('DRY RUN: no release metadata written; publication is not authorized.')
if __name__=='__main__':main()
