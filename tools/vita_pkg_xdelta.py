"""Make and round-trip a direct original-PKG to Vita3K-PKG xdelta.

This is the explicitly requested whole-file alternative to the smaller
component patch ZIP. It does not read a license or change either package.
"""
import argparse
import json
import os
import shutil
import subprocess
from tools.common import ROOT,sha256_file,write_json
from tools import vita_source as V,vita_build as B,vita_release as R,vita_integration as I

OUTPUT=ROOT/'work/output/vita/direct-xdelta'/B.VERSION
CHECK=V.WORK/'direct_xdelta_check'/B.VERSION
NAME=f'SRW-Z3-Tengoku-v{B.VERSION}-Vita3K-from-original-PKG.xdelta'


def identity(path):return dict(bytes=path.stat().st_size,sha256=sha256_file(path))


def run(apply=False,retry=False):
    source=json.loads((V.WORK/'source_identity.json').read_text('utf8'))
    expected_source=dict(bytes=source['pkg_bytes'],sha256=source['pkg_sha256'])
    target=json.loads((I.OUTPUT/'integration.json').read_text('utf8'))
    expected_target={k:target[k] for k in ('bytes','sha256')}
    V.need(target['version']==B.VERSION and target['native_pkg_install_verified'] and
           target['verified_files']==141,'Missing verified Vita3K target')
    V.need(sha256_file(R.XD)==R.XD_SHA,'Patch engine changed')
    V.need(identity(V.PKG)==expected_source and identity(I.TARGET)==expected_target,'Package identity differs')
    if retry:
        V.need(OUTPUT.is_dir() and CHECK.is_dir() and
               {p.name for p in OUTPUT.iterdir()}=={NAME} and
               {p.name for p in CHECK.iterdir()}=={'encode.log'},'Retry requires only this task\'s incomplete encode')
    else:V.need(not OUTPUT.exists() and not CHECK.exists(),'Preserve existing direct-patch outputs')
    V.need(shutil.disk_usage(ROOT).free>=7*1024**3,'At least 7 GiB free is required')
    print('Original:',V.PKG.name,expected_source,flush=True)
    print('Target:',I.TARGET.name,expected_target,flush=True)
    print('Direct xdelta:',OUTPUT/NAME,flush=True)
    if not apply:print('DRY RUN: no patch or reconstructed package written.');return
    before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in (V.PKG,I.TARGET)]
    if retry:
        V.need(ROOT.resolve() in OUTPUT.resolve().parents and ROOT.resolve() in CHECK.resolve().parents,
               'Retry files escaped workspace')
        (OUTPUT/NAME).rename(CHECK/'slow-attempt.partial.xdelta')
        (CHECK/'encode.log').rename(CHECK/'slow-attempt.encode.log')
    else:OUTPUT.mkdir(parents=True);CHECK.mkdir(parents=True)
    patch=OUTPUT/NAME;decoded=CHECK/'roundtrip.pkg'
    env=os.environ.copy();env.pop('XDELTA',None)
    print('Encoding direct whole-PKG patch...',flush=True)
    with (CHECK/'encode.log').open('wb') as log:
        subprocess.run([str(R.XD),'-e','-v','-0','-S','-N','-A','-D','-s',str(V.PKG),str(I.TARGET),str(patch)],
                       check=True,stdout=log,stderr=log,env=env)
    print('Encoded patch bytes:',patch.stat().st_size,'; decoding for verification...',flush=True)
    with (CHECK/'decode.log').open('wb') as log:
        subprocess.run([str(R.XD),'-d','-v','-D','-R','-s',str(V.PKG),str(patch),str(decoded)],
                       check=True,stdout=log,stderr=log,env=env)
    V.need(identity(decoded)==expected_target,'Reconstructed PKG differs from the verified target')
    after=[(p.stat().st_size,p.stat().st_mtime_ns) for p in (V.PKG,I.TARGET)]
    V.need(before==after,'An input package changed during verification')
    # Only this exact task-generated, verified temporary file is removed.
    V.need(decoded.parent.resolve()==CHECK.resolve() and ROOT.resolve() in decoded.resolve().parents,
           'Temporary verification file escaped workspace')
    decoded.unlink()
    report=dict(schema=1,version=B.VERSION,title_id=V.TITLE,source_name=V.PKG.name,source=expected_source,
        target_name=I.TARGET.name,target=expected_target,patch=dict(name=NAME,**identity(patch)),
        roundtrip_verified=True,original_inputs_unchanged=True,license_read=False,
        retro_trans_route='Apply xdelta',application_header_disabled=True,secondary_compression=False,
        github_published=False)
    write_json(OUTPUT/'verification.json',report)
    (OUTPUT/'SHA256SUMS.txt').write_text(report['patch']['sha256']+'  '+NAME+'\n',encoding='ascii')
    (OUTPUT/'README.txt').write_text(
        f'SRW Z3 Tengoku-hen English {B.VERSION} - direct Vita3K PKG patch\n\n'
        f'Source: original Japanese PCSG00494 v01.00 PKG ({expected_source["bytes"]:,} bytes).\n'
        f'Source SHA-256: {expected_source["sha256"]}\n\n'
        'In Retro Trans Tools, choose Apply xdelta. Select the original PKG as\n'
        'source, this .xdelta as patch, and a NEW .pkg output filename.\n'
        'Alternatively, with xdelta3:\n'
        f'xdelta3 -d -s "{V.PKG.name}" "{NAME}" "{I.TARGET.name}"\n\n'
        f'Output SHA-256: {expected_target["sha256"]}\n'
        f'Output size: {expected_target["bytes"]:,} bytes.\n\n'
        'Install the output PKG in Vita3K using your matching local license.\n'
        'For a physical Vita use the separate rePatch build.\n'
        'This whole-PKG delta can be much larger than the component patch ZIP.\n'
        'A full decode round trip reproduced the verified Vita3K package.\n',encoding='utf8')
    print('Direct xdelta round trip PASSED:',patch,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true')
    p.add_argument('--retry',action='store_true');a=p.parse_args();run(a.apply,a.retry)
