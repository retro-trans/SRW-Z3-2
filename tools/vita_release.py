"""Create round-tripped Retro Trans Vita patches; no upload or installation."""
import argparse
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import zipfile
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import vita_source as V,vita_build as B
from tools.vita import self_decrypt as S
from tools.vita.repatch_auth import sanitize

RETRO=ROOT.parent/'retro-trans-tools'
sys.path.insert(0,str(RETRO))
from retro_trans import vita_translation as pkg,vita_repatch as hardware

OUTPUT=ROOT/'work/output/vita/releases'/B.VERSION
XD=V.SIBLING/'work/xdelta3-3.1.0-x86_64.exe'
XD_SHA='6855c01cf4a1662ba421e6f95370cf9afa2b3ab6c148473c63efe60d634dfb9a'


def compact(data):return json.dumps(data,separators=(',',':'),ensure_ascii=True).encode()+b'\n'


def seal_zip(path,manifest,profile,files):
    with zipfile.ZipFile(path,'x',zipfile.ZIP_STORED) as archive:
        for name,raw in [(manifest,compact(profile))]+[(p.name,p.read_bytes()) for p in files]:
            info=zipfile.ZipInfo(name,(2026,11,19,0,0,0));info.external_attr=0o100644<<16;archive.writestr(info,raw)


def complete_hardware(auth_path,apply=False):
    """Add a hardware target later without replacing the sealed Vita3K files."""
    profile=pkg.read_description((OUTPUT/pkg.MANIFEST).read_bytes())
    V.need(profile['title_id']==V.TITLE and profile['build']==B.VERSION,'Foreign release candidate')
    eboot=B.OUTPUT/'components/eboot.bin'
    wanted=next(r['target'] for r in profile['files'] if r['path']=='eboot.bin')
    V.need(B.describe(eboot)==wanted,'Sealed executable changed')
    auth=sanitize(Path(auth_path).read_bytes(),S.parse(eboot.read_bytes())['ai'][0])
    original=V.PLAIN/'eboot.bin'
    V.need(B.describe(original)==next(r['source'] for r in profile['files'] if r['path']=='eboot.bin'),
           'Original executable changed')
    def boot_parameters(data):
        fields=struct.unpack_from('<12Q',data,32);at,total=fields[9:11];end=at+total;found=[]
        while at<end:
            typ,size,more=struct.unpack_from('<IIQ',data,at)
            V.need(size>=16 and at+size<=end,'Invalid boot parameter bounds')
            if typ==6:found.append(data[at:at+size])
            at+=size
        V.need(len(found)==1,'Missing unique native boot parameters');return found[0]
    V.need(boot_parameters(original.read_bytes())==boot_parameters(eboot.read_bytes()),
           'Original executable boot parameters differ')
    auth_proof=None;proof_path=Path(auth_path).parent/'proof.json'
    if proof_path.is_file():
        candidate=json.loads(proof_path.read_text('utf8'))
        V.need(candidate['title_id']==V.TITLE and candidate['sanitized_auth_sha256']==sha256(auth) and
               candidate['source_self_sha256']==sha256_file(original),'Derived permissions proof differs')
        auth_proof=candidate
    files=[r for r in profile['files'] if not r['path'].startswith('sce_module/')]
    hp=dict(schema=hardware.SCHEMA,title_id=V.TITLE,app_version='01.00',name='SRW Z3 Tengoku-hen - physical Vita',
        build=B.VERSION,minimum_app_version='0.5.19',package=dict(profile['package'],content_id=profile['content_id']),
        files=files,auth=dict(hex=auth.hex(),sha256=sha256(auth)))
    hardware.validate(hp)
    for row in files:V.need(B.describe(OUTPUT/row['patch']['name'])=={k:row['patch'][k] for k in ('bytes','sha256')},'Patch changed')
    manifest=OUTPUT/hardware.MANIFEST;path=OUTPUT/f'SRW-Z3-Tengoku-v{B.VERSION}-Vita-rePatch-patches.zip'
    V.need(manifest.exists()==path.exists(),'Incomplete existing hardware candidate')
    existing=path.exists()
    if existing:
        V.need(hardware.read_description(manifest.read_bytes())==hp,'Existing hardware manifest differs')
        with hardware.archive_description(path) as (readback,_,__):
            V.need(readback==hp,'Existing hardware archive differs')
    print('Matching original permissions validated;', 'audit existing' if existing else 'prepare',
          len(files),'physical-Vita component patches.',flush=True)
    if not apply:print('DRY RUN: no hardware release written.');return
    if not existing:
        write_json(manifest,hp);seal_zip(path,hardware.MANIFEST,hp,[OUTPUT/r['patch']['name'] for r in files])
    with hardware.archive_description(path) as (readback,_,__):V.need(readback==hp,'Hardware archive readback differs')
    audit=dict(title_id=V.TITLE,version=B.VERSION,auth_sanitized=True,
        raw_auth_included=False,retro_trans_archive_verified=True,gameplay_tested=False,
        original_boot_parameters_preserved=True,auth_source_proof=auth_proof,
        artifacts={p.name:B.describe(p) for p in (manifest,path)})
    audit_path=OUTPUT/'HARDWARE_AUDIT.json'
    if audit_path.exists():V.need(json.loads(audit_path.read_text('utf8'))==audit,'Existing hardware audit differs')
    else:write_json(audit_path,audit)


def run(apply=False,auth_path=None):
    V.need(not OUTPUT.exists(),'Preserve an existing release candidate')
    build=json.loads((B.OUTPUT/'build.json').read_text('utf8'));game=B.OUTPUT/'components'
    V.need(build['version']==B.VERSION and build['title_id']==V.TITLE,'Wrong sealed native build')
    sources=build['source_files'];targets=build['files']
    for name,row in sources.items():V.need(B.describe(V.PLAIN/name)==row,'Native source changed')
    for name,row in targets.items():V.need(B.describe(game/name)==row,'Sealed target changed')
    original=json.loads((V.WORK/'source_identity.json').read_text('utf8'))
    package=dict(bytes=original['pkg_bytes'],sha256=original['pkg_sha256'])
    V.need(B.describe(V.PKG)==package and sha256_file(XD)==XD_SHA,'Original package or patch engine changed')
    sanitized=None
    if auth_path:
        authority=S.parse((game/'eboot.bin').read_bytes())['ai'][0]
        sanitized=sanitize(Path(auth_path).read_bytes(),authority)
    print('Prepare',len(targets),'Vita3K deltas;',len(targets)-5,'physical-Vita components;',
          'matching auth available' if sanitized else 'hardware auth pending',flush=True)
    if not apply:print('DRY RUN: no patches written.');return
    OUTPUT.mkdir(parents=True);rows=[];patches=[]
    with tempfile.TemporaryDirectory(prefix='roundtrip-',dir=OUTPUT) as folder:
        decoded=Path(folder)/'decoded'
        for index,name in enumerate(sorted(targets),1):
            patch=OUTPUT/f'VITA-PCSG00494-{B.VERSION}-{index:03d}.xdelta'
            subprocess.run([str(XD),'-e','-s',str(V.PLAIN/name),str(game/name),str(patch)],check=True)
            subprocess.run([str(XD),'-d','-s',str(V.PLAIN/name),str(patch),str(decoded)],check=True)
            V.need(B.describe(decoded)==targets[name],'Delta roundtrip differs');decoded.unlink()
            rows.append(dict(path=name,source=sources[name],target=targets[name],patch=dict(name=patch.name,**B.describe(patch))))
            patches.append(patch);print('Verified delta',index,'/',len(targets),name,flush=True)
    profile=dict(schema=pkg.SCHEMA,name='SRW Z3 Tengoku-hen - Vita3K',build=B.VERSION,
        title_id=V.TITLE,content_id='JP0700-PCSG00494_00-SRWZ3OF2DLGPKG00',target='Vita3K',
        minimum_app_version='0.5.19',engine='pfs-v5-pkg-key2',package=package,
        source_files=[dict(path=name,**row) for name,row in sorted(sources.items())],files=rows,extras=[])
    pkg.validate(profile);write_json(OUTPUT/pkg.MANIFEST,profile)
    path=OUTPUT/f'SRW-Z3-Tengoku-v{B.VERSION}-Vita-PKG-patches.zip'
    seal_zip(path,pkg.MANIFEST,profile,patches)
    with pkg.archive_description(path) as (readback,_):V.need(readback==profile,'Retro Trans archive readback differs')
    physical=[r for r in rows if not r['path'].startswith('sce_module/')]
    if sanitized:
        hp=dict(schema=hardware.SCHEMA,title_id=V.TITLE,app_version='01.00',name='SRW Z3 Tengoku-hen - physical Vita',
            build=B.VERSION,minimum_app_version='0.5.19',package=dict(package,content_id=profile['content_id']),
            files=physical,auth=dict(hex=sanitized.hex(),sha256=sha256(sanitized)))
        hardware.validate(hp);write_json(OUTPUT/hardware.MANIFEST,hp)
        hp_zip=OUTPUT/f'SRW-Z3-Tengoku-v{B.VERSION}-Vita-rePatch-patches.zip'
        selected={r['patch']['name'] for r in physical}
        seal_zip(hp_zip,hardware.MANIFEST,hp,[p for p in patches if p.name in selected])
        complete_hardware(auth_path,True)
    else:
        write_json(B.OUTPUT/'hardware-pending.json',dict(title_id=V.TITLE,version=B.VERSION,components=physical,
            missing='Original PCSG00494 v01.00 console self_auth.bin; do not install these components alone',
            ready_for_hardware=False))
    artifacts={p.name:B.describe(p) for p in OUTPUT.iterdir() if p.is_file()}
    write_json(OUTPUT/'PATCH_AUDIT.json',dict(schema=1,title_id=V.TITLE,version=B.VERSION,
        roundtrip_components=len(rows),retro_trans_manifest_and_archive_verified=True,
        hardware_auth_available=bool(sanitized),native_pkg_install_verified=False,gameplay_tested=False,
        original_package_unchanged=B.describe(V.PKG)==package,license_packaged=False,artifacts=artifacts))
    print('Prepared patch-only candidate:',path,flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--auth',type=Path);a=p.parse_args()
    if a.auth and OUTPUT.exists():complete_hardware(a.auth,a.apply)
    else:run(a.apply,a.auth)


if __name__=='__main__':main()
