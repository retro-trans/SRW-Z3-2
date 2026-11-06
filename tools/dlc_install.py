"""Install verified English DLC locally, with exact file backups; preview first."""
import argparse,json,re,os,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
from tools import dlc,dlc_build as B,dlc_text as T,dlc_edat as ED
from tools.common import ROOT,contained,sha256,sha256_file,write_json

def plan(emulator,user):
 emulator=Path(emulator).resolve()
 if not (emulator/'rpcs3.exe').is_file()or not re.fullmatch(r'\d{8}',user):raise ValueError('Invalid RPCS3 installation/user')
 if (emulator/'config/vfs.yml').exists():raise ValueError('Custom VFS needs review before installing')
 home=emulator/'dev_hdd0/home'/user
 if not home.is_dir():raise ValueError('RPCS3 user not found')
 ready=json.loads((ROOT/'work/ui/local_dlc_release_0.5.49.json').read_text('utf8'))
 build=json.loads((B.OUTPUT/'build.json').read_text('utf8'))
 proof=json.loads((ROOT/'work/ui/dlc_verified_0.5.49.json').read_text('utf8'))
 if proof['build_sha256']!=sha256_file(B.OUTPUT/'build.json'):raise ValueError('DLC build drift')
 if ready['final_readback_sha256']!=sha256_file(ROOT/'work/ui/dlc_verified_0.5.49.json'):raise ValueError('DLC verification drift')
 installed=emulator/'dev_hdd0/game/NPJB00692';files=[];shared={}
 for p in build['packages']:
  code=p['code'];source=dlc.WORK/code;name=code+'.EDAT';file=B.OUTPUT/code/name;rap=source/'license.rap'
  if sha256_file(file)!=p['edat_sha256']:raise ValueError('English DLC changed: '+code)
  payload,auth=ED.decode(file.read_bytes(),rap.read_bytes(),name,True)
  if sha256(payload)!=p['cpk_sha256']or auth['content_id']!=p['content_id']:raise ValueError('DLC identity/authentication differs')
  files.append(dict(source=file,target=installed/'USRDIR/DLC'/name,sha256=p['edat_sha256'],kind='dlc'))
  files.append(dict(source=rap,target=home/'exdata'/(p['content_id']+'.rap'),sha256=sha256_file(rap),kind='license'))
  for name in ('ICON0.PNG','PIC1.PNG','PS3LOGO.DAT','PARAM.SFO'):
   path=B.OUTPUT/code/name if name=='PARAM.SFO'else source/'package'/name
   digest=sha256_file(path)
   if name in shared and shared[name]['sha256']!=digest:raise ValueError('Shared DLC metadata disagrees')
   shared[name]=dict(source=path,target=installed/name,sha256=digest,kind='metadata')
 if len(build['packages'])!=32:raise ValueError('Expected all 32 DLCs')
 files.extend(shared.values())
 base=ROOT/'work/output/iso/0.5.48/Tengoku-hen-English-0.5.48.iso'
 seal=json.loads((ROOT/'work/ui/local_release_0.5.48.json').read_text('utf8'))
 if sha256_file(base)!=seal['iso']['sha256']:raise ValueError('English base image differs from verified 0.5.48')
 registry=emulator/'config/games.yml';old=registry.read_bytes();text=old.decode('utf-8-sig');entry='BLJS10299: '+base.as_posix()
 if re.search(r'(?m)^BLJS10299:',text):text=re.sub(r'(?m)^BLJS10299:[^\r\n]*',lambda m:entry,text)
 else:text+=(''if text.endswith('\n')else'\n')+entry+'\n'
 data=text.encode('utf8');files.append(dict(target=registry,data=data,sha256=sha256(data),kind='game_registration'))
 for item in files:
  contained(emulator,item['target'])
  if item['target'].is_symlink():raise ValueError('Refusing symlink target')
  item['before_sha256']=sha256_file(item['target'])if item['target'].is_file()else None
  item['change']=item['before_sha256']!=item['sha256']
 return dict(version=dlc.VERSION,emulator=emulator,user=user,base_iso=base,files=files)

def install(data):
 # Require RPCS3 to be closed so no emulator process can overwrite configuration.
 running=subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name rpcs3 -ErrorAction SilentlyContinue).Count"],text=True).strip()
 if running!='0':raise ValueError('Close RPCS3 before installation')
 folder=ROOT/'work/output/dlc-install'/('0.5.49-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 folder.mkdir(parents=True,exist_ok=False);changed=[r for r in data['files']if r['change']];written=[]
 for r in changed:
  dest=r['target'];backup=folder/'before'/dest.relative_to(data['emulator'])
  if dest.exists():
   if sha256_file(dest)!=r['before_sha256']:raise ValueError('Installation target changed before backup')
   backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,backup)
   if sha256_file(backup)!=r['before_sha256']:raise ValueError('Backup readback failed')
  r['backup']=backup if dest.exists()else None
 try:
  for r in changed:
   dest=r['target'];dest.parent.mkdir(parents=True,exist_ok=True);temporary=dest.with_name(dest.name+'.dlc-0.5.49.tmp')
   with temporary.open('xb')as out:
    if 'data'in r:out.write(r['data'])
    else:
     with r['source'].open('rb')as source:shutil.copyfileobj(source,out)
   if sha256_file(temporary)!=r['sha256']:raise ValueError('Install staging hash mismatch')
   os.replace(temporary,dest);written.append(r)
  for r in data['files']:
   if sha256_file(r['target'])!=r['sha256']:raise ValueError('Installed file readback differs')
 except BaseException:
  for r in reversed(written):
   if r['backup']:shutil.copy2(r['backup'],r['target'])
   else:r['target'].unlink()
  raise
 report=dict(schema=1,version=data['version'],emulator=str(data['emulator']),user=data['user'],base_iso=str(data['base_iso']),
  dlc_files=32,license_files=32,shared_metadata=4,saves_modified=False,runtime_verified=False,files=[])
 for r in data['files']:
  row=dict(path=str(r['target']),kind=r['kind'],changed=r['change'],backup=str(r['backup'])if r.get('backup')else None)
  if r['kind']!='license':row.update(sha256=r['sha256'],before_sha256=r['before_sha256'])
  report['files'].append(row)
 write_json(folder/'installation.json',report)
 return folder

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--emulator',default='E:/RPCS3');parser.add_argument('--user',default='00000001');parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 data=plan(args.emulator,args.user)
 print('RPCS3:',data['emulator']);print('Install 32 English DLCs, 32 supplied licenses and 4 shared metadata files.')
 print('Game entry:',data['base_iso']);print('Files to change:',sum(r['change']for r in data['files']))
 print('Sample DLC:',next(r['target']for r in data['files']if r['kind']=='dlc'))
 if args.apply:print('Installed and read back all files. Backup/report:',install(data))
 else:print('DRY RUN: no emulator files, game files or saves changed.')
if __name__=='__main__':main()
