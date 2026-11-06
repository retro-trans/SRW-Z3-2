"""Prepare/verify local Retro Trans DLC delivery. Never contacts GitHub."""
import argparse,json,re,subprocess,sys,urllib.parse,zipfile
from tools import dlc,dlc_build as B,dlc_verify as V
from tools.common import ROOT,sha256_file,write_json

FOLDER=ROOT/'work/output/releases'/dlc.VERSION
SDK=ROOT/'work/output/release-tools-v0.5.4'
ARTIFACTS=FOLDER/'artifacts'
READY=ROOT/'work/ui'/('local_dlc_release_'+dlc.VERSION+'.json')

def config():
 proof=json.loads(V.PROOF.read_text('utf8'));build=json.loads((B.OUTPUT/'build.json').read_text('utf8'))
 if proof['build_sha256']!=sha256_file(B.OUTPUT/'build.json'):raise ValueError('DLC proof differs from build')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 rows=[]
 for p in build['packages']:
  code=p['code'];original=dlc.WORK/code/'package';target=B.OUTPUT/code
  for system in (False,True):
   name='PARAM.SFO'if system else code+'.EDAT';fmt='sfo'if system else'edat'
   source=original/name if system else original/'USRDIR/DLC'/name
   if sha256_file(target/name)!=p['sfo_sha256'if system else'edat_sha256']:raise ValueError('DLC candidate changed')
   title='DLC system title (source '+code+')'if system else code+': '+p['members']['0']['title']
   rows.append(dict(patch='SRW-Z3-2-'+code+('-System-Title'if system else'')+'-English-'+dlc.VERSION+'.xdelta',
    edition='jp-npjb00692-'+('metadata'if system else'dlc')+code[3:],game_name='Tengoku-hen '+title,
    language='en',source_version='original',source_format=fmt,target_format=fmt,source=str(source),target=str(target/name)))
 return dict(game_id='srw-z3-tengoku-dlc-ps3',game_name='Super Robot Taisen Z3: Tengoku-hen DLC (PS3)',platform='PS3',
  version=dlc.VERSION,source_commit=commit,patches=rows)

def sdk_check():
 sys.path.insert(0,str(SDK))
 from retro_trans.release import validate_directory
 from retro_trans.catalog import Catalog,recognize
 manifest=validate_directory(ARTIFACTS);cfg=json.loads((FOLDER/'release-local.json').read_text('utf8'))
 if len(manifest['patches'])!=64:raise ValueError('Expected all 32 DLC and 32 optional system-title routes')
 tag='v'+dlc.VERSION;base='https://github.com/retro-trans/SRW-Z3-2/releases/download/'+tag+'/'
 # Offline catalog: these future URLs are validated as strings, never requested.
 catalog=Catalog(dict(schema_version=1,releases=[dict(repo='retro-trans/SRW-Z3-2',tag=tag,manifest=manifest,
  assets={p['patch']:base+urllib.parse.quote(p['patch'])for p in manifest['patches']})]))
 for row,p in zip(cfg['patches'],manifest['patches']):
  if row['patch']!=p['patch']or sha256_file(row['source'])!=p['source_sha256']or sha256_file(row['target'])!=p['target_sha256']:raise ValueError('DLC delivery inputs differ')
  found=recognize(row['source'],catalog)
  if len(found)!=1 or found[0].edition!=row['edition']:raise ValueError('Retro Trans cannot identify DLC source uniquely')
  route=catalog.plan(found[0])
  if route.target.version!=dlc.VERSION or len(route.edges)!=1 or route.edges[0].asset.name!=p['patch']:raise ValueError('Incorrect DLC automatic route')
 return manifest

def seal():
 manifest=sdk_check();proof=json.loads(V.PROOF.read_text('utf8'))
 log=ROOT/'work/output/scratch'/('startup-'+dlc.VERSION+'-tests.log');raw=log.read_bytes()
 text=raw.decode('utf-16'if raw[:2]in(b'\xff\xfe',b'\xfe\xff')else'utf-8-sig')
 result=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)',text)
 if not result:raise ValueError('Full regression suite must pass before delivery sealing')
 count,skipped=int(result[1]),int(result[2]or 0)
 tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SDK,text=True).strip()
 assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha256_file(p))for p in sorted(ARTIFACTS.iterdir())]
 return dict(schema=1,version=dlc.VERSION,publication='pending_explicit_user_consent',github_release_created=False,
  source_commit=manifest['source_commit'],release_tool_version='0.5.4',release_tool_commit=tool_commit,
  patches=64,automatic_routes_verified=64,counts=proof['counts'],final_readback_sha256=sha256_file(V.PROOF),
  regression_tests=dict(run=count,passed=count-skipped,skipped=skipped,log_sha256=sha256_file(log)),
  assets=assets,runtime_verified=False,console_compatibility_verified=False)

def deliver():
 data=seal();bundle=FOLDER/('Tengoku-hen-DLC-English-'+dlc.VERSION+'-patches.zip')
 if bundle.exists():raise ValueError('Preserve sealed DLC delivery bundle')
 readme=ROOT/'docs'/('DLC_'+dlc.VERSION+'.md')
 with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED)as z:
  for p in sorted(ARTIFACTS.iterdir()):z.write(p,p.name)
  z.write(readme,'README.md')
 with zipfile.ZipFile(bundle)as z:
  if z.testzip()is not None or len(z.namelist())!=len(data['assets'])+1:raise ValueError('DLC patch bundle failed verification')
 data['bundle']=dict(path=bundle.relative_to(ROOT).as_posix(),bytes=bundle.stat().st_size,sha256=sha256_file(bundle))
 write_json(READY,data)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=('config','seal'));parser.add_argument('--apply',action='store_true');a=parser.parse_args()
 if a.action=='config':
  data=config();print('DLC EDAT patch routes: 32; optional system-title routes: 32; source commit:',data['source_commit'])
  print('Sample:',data['patches'][0]['patch'],'=>',data['patches'][0]['target'])
  if a.apply:
   if FOLDER.exists():raise ValueError('Preserve existing release workset')
   write_json(FOLDER/'release-local.json',data)
 else:
  data=seal();print('All 64 automatic routes and complete-file round trips verified. Tests:',data['regression_tests'])
  if a.apply:deliver()
 if not a.apply:print('DRY RUN: no release files written; no GitHub contact.')
if __name__=='__main__':main()
