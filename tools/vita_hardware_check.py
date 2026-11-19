"""Exercise Retro Trans PKG + work.bin → physical-Vita overlay, locally only."""
import argparse,hashlib,json,time,zipfile
from tools.common import ROOT,sha256,write_json
from tools import vita_source as V,vita_build as B,vita_release as R,vita_auth as A
from retro_trans import vita_repatch as hardware

PARENT=ROOT/'work/output/vita/hardware/0.1.0'
OUTPUT=PARENT/'verified-overlay'
PATCH=R.OUTPUT/'SRW-Z3-Tengoku-v0.1.0-Vita-rePatch-patches.zip'
ZIP=PARENT/'Tengoku-hen-English-0.1.0-physical-Vita.zip'


def run(apply=False):
    V.need(not OUTPUT.exists() and not ZIP.exists(),'Preserve an existing hardware overlay')
    with hardware.archive_description(PATCH) as (profile,_,__):
        V.need(profile['title_id']==V.TITLE and profile['build']==B.VERSION,'Wrong hardware profile')
        for row in profile['files']:
            V.need(B.describe(B.OUTPUT/'components'/row['path'])==row['target'],'Native target changed')
    auth,proof=A.plan()
    V.need(sha256(auth)==profile['auth']['sha256'] and bytes.fromhex(profile['auth']['hex'])==auth,
           'Package permissions differ from original source extraction')
    license_before=V.LICENSE.read_bytes();stat_before=V.PKG.stat()
    print('Original PKG + existing work.bin → Retro Trans overlay;',len(profile['files']),'component hashes; sanitized original permissions.',flush=True)
    if not apply:print('DRY RUN: no overlay or ZIP written.');return
    PARENT.mkdir(parents=True,exist_ok=True);last=['',0]
    def progress(message,fraction=None):
        stage=message.split(':')[0]
        if stage!=last[0] and time.monotonic()-last[1]>3:
            print(stage,flush=True);last[:]=[stage,time.monotonic()]
    hardware.apply(V.PKG,OUTPUT,description=PATCH,work_bin=V.LICENSE,
                   cache=V.WORK/'retro_trans_cache',progress=progress)
    tree=OUTPUT/'rePatch'/V.TITLE
    wanted={r['path']:r['target'] for r in profile['files']}
    wanted['self_auth.bin']=dict(bytes=144,sha256=profile['auth']['sha256'])
    actual={p.relative_to(tree).as_posix():B.describe(p) for p in tree.rglob('*') if p.is_file()}
    V.need(actual==wanted,'Overlay inventory or file hashes differ')
    V.need((tree/'self_auth.bin').read_bytes()==auth,'Exported permissions changed')
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_STORED) as archive:
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file():archive.write(path,path.relative_to(OUTPUT).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        V.need(archive.testzip() is None,'Overlay ZIP CRC failed')
        for name,row in wanted.items():
            digest=hashlib.sha256();size=0
            with archive.open('rePatch/'+V.TITLE+'/'+name) as stream:
                for chunk in iter(lambda:stream.read(4<<20),b''):digest.update(chunk);size+=len(chunk)
            V.need(dict(bytes=size,sha256=digest.hexdigest())==row,'Overlay ZIP payload differs')
    stat_after=V.PKG.stat()
    V.need((stat_before.st_size,stat_before.st_mtime_ns)==(stat_after.st_size,stat_after.st_mtime_ns) and
           V.LICENSE.read_bytes()==license_before,'Original source/license changed')
    result=dict(schema=1,title_id=V.TITLE,version=B.VERSION,retro_trans_pkg_work_bin_route_verified=True,
        overlay_components=len(profile['files']),overlay_auth_files=1,zip_stream_hashes_verified=True,
        auth_source_proof=proof,artifacts={ZIP.name:B.describe(ZIP),PATCH.name:B.describe(PATCH)},
        files=actual,original_inputs_unchanged=True,license_packaged=False,
        physical_gameplay_tested=False,user_device_modified=False)
    write_json(PARENT/'integration.json',result)
    print('Verified physical-Vita test overlay and copy-ready ZIP:',ZIP,flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.apply)


if __name__=='__main__':main()
