"""Validate patch-only delivery through Retro Trans's isolated Vita3K installer.

No user's emulator installation, firmware, settings or saves are changed.
The original license is read locally; values are never printed or packaged.
"""
import argparse,json,time
from tools.common import ROOT,write_json
from tools import vita_release as R,vita_build as B,vita_source as V
from retro_trans import vita_translation as pkg

OUTPUT=ROOT/'work/output/vita/packages'/B.VERSION
PATCH=R.OUTPUT/f'SRW-Z3-Tengoku-v{B.VERSION}-Vita-PKG-patches.zip'
TARGET=OUTPUT/f'Tengoku-hen-English-{B.VERSION}-Vita3K.pkg'


def run(apply=False):
    V.need(PATCH.is_file() and not TARGET.exists(),'Missing patch ZIP or target already exists')
    with pkg.archive_description(PATCH) as (profile,_):
        V.need(profile['title_id']==V.TITLE and profile['build']==B.VERSION,'Wrong patch profile')
        V.need(B.describe(V.PKG)==profile['package'],'Original package changed')
        count=len(profile['source_files'])
    license_data=V.LICENSE.read_bytes()
    V.need(len(license_data)==512 and license_data[0x10:0x40].split(b'\0')[0].decode('ascii')==profile['content_id'],
           'Matching local license required')
    print('Verify original PKG → local patch ZIP → translated PKG → isolated native installation;',count,'file hashes.',flush=True)
    if not apply:print('DRY RUN: no translated package or emulator workspace created.');return
    OUTPUT.mkdir(parents=True,exist_ok=True);before=V.LICENSE.read_bytes();last=['',0]
    def progress(message,fraction=None):
        stage=message.split(':')[0]
        if stage!=last[0] and time.monotonic()-last[1]>3:
            print(stage,flush=True);last[:]=[stage,time.monotonic()]
    pkg.apply(V.PKG,V.LICENSE,TARGET,description=PATCH,cache=V.WORK/'retro_trans_cache',progress=progress)
    check=json.loads(TARGET.with_suffix('.validation.json').read_text('utf8'))
    V.need(check['native_pkg_install_verified'] and check['verified_files']==count and
           V.LICENSE.read_bytes()==before,'Native installer validation did not pass')
    check.update(patch_only_zip=B.describe(PATCH),title_id=V.TITLE,version=B.VERSION,
                 no_user_emulator_installation_changed=True,gameplay_tested=False)
    write_json(OUTPUT/'integration.json',check)
    audit=json.loads((R.OUTPUT/'PATCH_AUDIT.json').read_text('utf8'))
    audit.update(native_pkg_install_verified=True,verified_files=count,gameplay_tested=False)
    write_json(R.OUTPUT/'PATCH_AUDIT.json',audit)
    print('Native installation and all',count,'target file hashes verified.',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.apply)


if __name__=='__main__':main()
