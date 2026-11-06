"""Source-bound Tengoku DLC inventory/extraction. Originals and licenses stay private."""
import argparse,json,re,struct,subprocess,zipfile
from pathlib import Path,PurePosixPath
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from tools.common import ROOT,sha256,sha256_file,write_json
from tools.cpk import CPK
from tools.pipeline import sfo_values
SOURCE=ROOT/'work/dlc/Z3.2-Tengoku-hen'
WORK=ROOT/'work/tengoku_dlc'
VERSION='0.5.49'
# Public retail PS3 package transport key; no per-user entitlement is embedded.
# Public key reference: RPCS3/rpcs3/Crypto/key_vault.h.
PKG_KEY=bytes.fromhex('2e7b71d7c9c9a14ea3221f188828b8f8')

def package(raw):
 if len(raw)<128:raise ValueError('Truncated PKG header')
 if raw[:8]!=bytes.fromhex('7f504b4780000001'):raise ValueError('Unsupported PKG revision/platform')
 count=struct.unpack_from('>I',raw,20)[0];size,off,length=struct.unpack_from('>QQQ',raw,24)
 if size!=len(raw)or off+length>size or not 0<count<10000:raise ValueError('Invalid PKG bounds')
 cid=raw[48:96].split(b'\0')[0].decode('ascii')
 if not re.fullmatch(r'JP0700-NPJB00692_00-SRWZ3OF2DLC02\d{3}',cid):raise ValueError('Not Tengoku DLC')
 if length<count*32:raise ValueError('Truncated PKG entry table')
 plain=Cipher(algorithms.AES(PKG_KEY),modes.CTR(raw[112:128])).decryptor().update(raw[off:off+length]);entries=[];seen=set()
 for i in range(count):
  no,nl,do,dl,flags,_=struct.unpack_from('>IIQQII',plain,i*32)
  if no+nl>len(plain)or do+dl>len(plain):raise ValueError('PKG entry outside payload')
  name=plain[no:no+nl].decode('utf8');p=PurePosixPath(name)
  if not name or p==PurePosixPath('.')or p.is_absolute()or '..'in p.parts or ':'in name or '\\'in name or name in seen:raise ValueError('Unsafe PKG path')
  seen.add(name);entries.append(dict(name=name,flags=flags,data=plain[do:do+dl]))
 return cid,entries

def sources():
 result=[]
 for path in sorted(SOURCE.glob('*.zip')):
  with zipfile.ZipFile(path)as z:
   names=z.namelist();pkgs=[n for n in names if n.endswith('.pkg')];raps=[n for n in names if n.endswith('.rap')]
   if len(pkgs)!=1 or len(raps)!=1:raise ValueError('Expected one PKG and matching RAP')
   raw=z.read(pkgs[0]);cid,entries=package(raw)
   if PurePosixPath(raps[0]).stem!=cid or z.getinfo(raps[0]).file_size!=16:raise ValueError('Entitlement/content mismatch')
   edats=[r for r in entries if r['name'].endswith('.EDAT')]
   if len(edats)!=1 or PurePosixPath(edats[0]['name']).stem!='DLC'+cid[-4:]:raise ValueError('Expected matching DLC payload')
   sfo=next(r['data']for r in entries if r['name']=='PARAM.SFO')
   result.append(dict(path=path,cid=cid,pkg_name=pkgs[0],pkg_sha256=sha256(raw),zip_sha256=sha256_file(path),
    entries=entries,rap_name=raps[0],edat=edats[0],sfo=sfo_values(sfo)))
 if len(result)!=32 or len({r['cid']for r in result})!=32:raise ValueError('Expected 32 distinct supplied DLCs')
 return result

def extract(items):
 if WORK.exists():raise ValueError('Preserve existing DLC workset')
 tool=json.loads((ROOT/'config/tengoku.json').read_text('utf8'))['offline_sdat_tool'];WORK.mkdir(parents=True)
 inventory=[]
 for item in items:
  code=Path(item['edat']['name']).stem;folder=WORK/code;folder.mkdir()
  for r in item['entries']:
   if not r['data']:continue
   p=folder/'package'/r['name'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r['data'])
  # Keep user-supplied entitlement local, never in logs, catalogs or delivery assets.
  with zipfile.ZipFile(item['path'])as z:(folder/'license.rap').write_bytes(z.read(item['rap_name']))
  source=folder/'package'/item['edat']['name'];dest=folder/(code+'.cpk')
  run=subprocess.run([tool,'-d',str(source),str(dest),'1',str(folder/'license.rap')],capture_output=True,timeout=60,
   creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),cwd=folder)
  if run.returncode or not dest.exists()or dest.read_bytes()[:4]!=b'CPK ':raise ValueError('DLC decode failed: '+code+'; originals preserved')
  members=[]
  with CPK(dest)as arc:
   for entry in arc.files:
    data=arc.read(entry);p=folder/'members'/('%05d.bin'%entry['id']);p.parent.mkdir(exist_ok=True);p.write_bytes(data)
    members.append(dict(id=entry['id'],path=p.relative_to(ROOT).as_posix(),bytes=len(data),sha256=sha256(data),head=data[:8].hex()))
  record=dict(code=code,content_id=item['cid'],source_zip=item['path'].relative_to(ROOT).as_posix(),zip_sha256=item['zip_sha256'],
   pkg_name=item['pkg_name'],pkg_sha256=item['pkg_sha256'],edat_sha256=sha256(item['edat']['data']),
   cpk_sha256=sha256_file(dest),sfo=item['sfo'],members=members)
  inventory.append(record);print(code,len(members),'members',flush=True)
 write_json(WORK/'inventory.json',dict(schema=1,version=VERSION,packages=inventory,tool_sha256=sha256_file(tool),delivery_status='inventory_only'))

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();items=sources()
 for r in items:print(r['cid'],[(s['name'],len(s['data']))for s in r['entries']if s['name'].endswith('.EDAT')])
 if a.apply:extract(items)
 else:print('DRY RUN: 32 private packages will be decoded into work/tengoku_dlc; originals unchanged; no entitlement published.')
if __name__=='__main__':main()
