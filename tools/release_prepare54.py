"""Prepare/seal a verified Retro Trans 0.5.53 -> 0.5.54 diagnostic route."""
import argparse
import re
import subprocess
import sys
from tools.common import ROOT,sha256_file,write_json
from tools import cfw_voice_diagnostic_build as D,cfw_trophy_control as T

VERSION=D.VERSION
FOLDER=ROOT/'work/output/releases'/VERSION
SDK=ROOT/'work/output/release-tools-v0.5.4'
READY=ROOT/f'work/ui/local_release_{VERSION}.json'


def tests():
    path=ROOT/f'work/output/scratch/cfw-voice-{VERSION}-tests.log'
    raw=path.read_bytes()
    text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    match=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)',text)
    if not match or int(match[1])<25:raise ValueError('25 focused native/CFW/trophy/ISO checks required')
    return dict(run=int(match[1]),passed=int(match[1])-int(match[2] or 0),
        skipped=int(match[2] or 0),log_sha256=sha256_file(path))


def checked():
    proof=D.load(D.PROOF)
    parent=D.load(ROOT/'work/ui/local_release_0.5.53.json')
    if proof['parent_delivery_sha256']!=sha256_file(ROOT/'work/ui/local_release_0.5.53.json'):
        raise ValueError('Parent seal changed')
    if proof['build_sha256']!=sha256_file(D.OUTPUT/'build.json'):raise ValueError('Diagnostic build changed')
    if proof['iso_verification']['files_verified_each_tree']!=82:raise ValueError('Incomplete image verification')
    if set(proof['changed_game_files'])!={D.EBOOT,D.EFF} or proof['unchanged_game_files']!=80:
        raise ValueError('Unexpected diagnostic file scope')
    if not proof['original_trophies_preserved'] or not proof['fonts_and_audio_unchanged']:
        raise ValueError('Required carried assets not verified')
    return proof,parent


def config():
    proof,parent=checked()
    tests()
    return dict(game_id=parent['manifest']['game_id'],game_name=parent['manifest']['game_name'],
        platform='PS3',version=VERSION,source_commit=subprocess.check_output(
            ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        patches=[dict(patch=f'SRW-Z3-2-PS3-English-{VERSION}-voice-diagnostic-from-0.5.53.xdelta',
            edition='jp-bljs10299',language='en',source_version='0.5.53',source_format='iso',
            target_format='iso',source=str(T.IMAGE),target=str(D.IMAGE))])


def seal():
    sys.path.insert(0,str(SDK))
    from retro_trans.release import validate_directory
    assets=FOLDER/'artifacts'
    manifest=validate_directory(assets)
    proof,parent=checked()
    if len(manifest['patches'])!=1:raise ValueError('One exact-0.5.53 route required')
    row=manifest['patches'][0]
    for side,expected in (('source',parent['iso']),('target',proof['iso_verification'])):
        if row[side+'_sha256']!=expected['sha256'] or row[side+'_bytes']!=expected['bytes']:
            raise ValueError('Incorrect '+side+' identity')
    if row['source_version']!='0.5.53' or manifest['version']!=VERSION:raise ValueError('Wrong version route')
    return dict(schema=1,version=VERSION,publication='pending_explicit_user_consent',
        github_release_created=False,hardware_verified=False,runtime_verified=False,
        diagnostic='observe loaded bank and replace only fallback battle captions with measured values',
        source_commit=manifest['source_commit'],iso=proof['iso_verification'],manifest=manifest,
        validation=D.load(assets/'VALIDATION.json'),focused_tests=tests(),
        inherited_parent_regression=parent['inherited_parent_regression'],
        final_readback_sha256=sha256_file(D.PROOF),release_tool_version='0.5.4',
        release_tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SDK,text=True).strip(),
        assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha256_file(p)) for p in sorted(assets.iterdir())])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('config','seal'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    result=config() if args.action=='config' else seal()
    print('0.5.53 -> 0.5.54 Retro Trans diagnostic; no installation or GitHub publication.')
    if args.apply:
        if args.action=='config':
            if FOLDER.exists():raise ValueError('Preserve existing diagnostic delivery')
            write_json(FOLDER/'release-local.json',result)
        else:
            if READY.exists():raise ValueError('Preserve existing diagnostic seal')
            write_json(READY,result)
    else:print('DRY RUN: no release metadata written.')


if __name__=='__main__':main()
