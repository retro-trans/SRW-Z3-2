"""Prepare an isolated, installed Vita3K gameplay test from the sealed PKG."""
import argparse,json,shutil,sys
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import vita_source as V,vita_integration as I,vita_build as B
from retro_trans import vita_pkg as P

OUTPUT=V.WORK/'runtimes'/B.VERSION
FIRMWARE=Path('E:/Emu/vita3k/fs')


def prepare(apply=False,debugger=False):
    V.need(not OUTPUT.exists(),'Preserve existing runtime workspace')
    identity=json.loads((V.WORK/'retro_trans_cache/vita3k-windows-latest.zip.json').read_text('utf8'))
    archive=V.WORK/'retro_trans_cache'/(identity['sha256']+'.download')
    V.need(sha256_file(archive)==identity['sha256'],'Cached runtime changed')
    for name in ('vs0','sa0'):V.need((FIRMWARE/name).is_dir(),'Missing local firmware')
    check=json.loads(I.TARGET.with_suffix('.validation.json').read_text('utf8'))
    V.need(check['native_pkg_install_verified'] and I.TARGET.stat().st_size==check['bytes'] and
           sha256_file(I.TARGET)==check['sha256'],'Missing or changed sealed test PKG')
    print('Isolated runtime:',OUTPUT)
    print('Install sealed English',B.VERSION,'PKG; copy only local vs0/sa0 firmware; preserve user emulator and saves.')
    if not apply:print('DRY RUN: no runtime copied or installed.');return
    OUTPUT.mkdir(parents=True)
    exe=P.extract_runtime(archive,OUTPUT/'engine');fs=P.portable_directory(exe)/'fs'
    print('Installing sealed test package in isolated runtime...',flush=True)
    license_data=P.license_bytes(V.PKG,V.LICENSE,V.TITLE)
    P.run_installer(exe,I.TARGET,P.encoded_license(license_data),fs)
    del license_data
    build=json.loads((B.OUTPUT/'build.json').read_text('utf8'))
    expected=dict(build['source_files']);expected.update(build['files'])
    app=fs/'ux0/app'/V.TITLE
    for rel,row in expected.items():
        target=app/rel
        V.need(target.stat().st_size==row['bytes'] and sha256_file(target)==row['sha256'],
               'Installed game file differs: '+rel)
    for name in ('vs0','sa0'):
        print('Copying firmware',name,flush=True)
        shutil.copytree(FIRMWARE/name,fs/name,dirs_exist_ok=True)
    config=P.portable_directory(exe)/'config.yml'
    config.write_text('pref-path: '+json.dumps(str(fs))+'\n'+
        'initial-setup: false\ncheck-for-updates: false\ncheck-for-updates-mode: 0\n'+
        'log-level: 0\narchive-log: true\nbackend-renderer: Vulkan\n'+
        'gdbstub: '+str(debugger).lower()+'\nwait-for-debugger: false\ndiscord-rich-presence: false\n'+
        'keyboard-button-start: Enter\nkeyboard-button-cross: KeyX\nkeyboard-button-circle: KeyC\n',encoding='utf8')
    write_json(OUTPUT/'runtime.json',dict(executable=str(exe),fs=str(fs),title_id=V.TITLE,
        test_version=B.VERSION,runtime_sha256=identity['sha256'],source_pkg_sha256=check['sha256'],
        verified_game_files=len(expected),debugger=debugger,user_emulator_modified=False))
    print('Prepared emulator:',exe,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true')
    p.add_argument('--debugger',action='store_true',help='Startup pauses until the guest debugger resumes it')
    a=p.parse_args();prepare(a.apply,a.debugger)
