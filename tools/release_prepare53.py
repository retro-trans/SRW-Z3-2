"""Prepare a Retro Trans 0.5.52 -> 0.5.53 single-variable trophy control."""
import argparse
import json
import re
import subprocess
import sys
from tools.common import ROOT, sha256_file, write_json
from tools import cfw_trophy_control as C

VERSION = C.VERSION
FOLDER = ROOT/'work/output/releases'/VERSION
SDK = ROOT/'work/output/release-tools-v0.5.4'
READY = ROOT/f'work/ui/local_release_{VERSION}.json'


def tests():
    path = ROOT/f'work/output/scratch/cfw-trophy-{VERSION}-tests.log'
    raw = path.read_bytes()
    text = raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    found = re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)', text)
    if not found or int(found[1]) < 21:
        raise ValueError('Focused CFW, trophy, native-message and ISO checks must pass')
    count, skipped = int(found[1]), int(found[2] or 0)
    return dict(run=count, passed=count-skipped, skipped=skipped, scope='CFW, trophies, native upgrade messages and ISO reader',
                log_sha256=sha256_file(path))


def checked():
    proof = C.load(C.PROOF)
    parent = C.load(ROOT/'work/ui/local_release_0.5.52.json')
    if proof['parent_delivery_sha256'] != sha256_file(ROOT/'work/ui/local_release_0.5.52.json'):
        raise ValueError('Parent release seal differs')
    if proof['build_sha256'] != sha256_file(C.OUTPUT/'build.json'):
        raise ValueError('Control build differs')
    if proof['changed_game_files'] != [C.T.DISC] or proof['unchanged_game_files'] != 81 or not proof['executable_byte_identical']:
        raise ValueError('Control is not isolated to trophy package')
    if not proof['original_trophy_package_restored'] or sha256_file(C.OUTPUT/'TROPHY.TRP') != C.ORIGINAL_SHA:
        raise ValueError('Original trophy package differs')
    if proof['iso_verification']['files_verified_each_tree'] != 82:
        raise ValueError('Incomplete final ISO readback')
    return proof, parent


def config():
    proof, parent = checked()
    tests()
    return dict(game_id=parent['manifest']['game_id'], game_name=parent['manifest']['game_name'],
        platform='PS3', version=VERSION, source_commit=subprocess.check_output(
            ['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        patches=[dict(patch=f'SRW-Z3-2-PS3-English-{VERSION}-original-trophies-from-0.5.52.xdelta',
            edition='jp-bljs10299', language='en', source_version='0.5.52', source_format='iso',
            target_format='iso', source=str(C.B.IMAGE), target=str(C.IMAGE))])


def seal():
    sys.path.insert(0, str(SDK))
    from retro_trans.release import validate_directory
    assets = FOLDER/'artifacts'
    manifest = validate_directory(assets)
    proof, parent = checked()
    if len(manifest['patches']) != 1:
        raise ValueError('One exact-0.5.52 diagnostic route required')
    row = manifest['patches'][0]
    for side, expected in (('source', parent['iso']), ('target', proof['iso_verification'])):
        if row[side+'_sha256'] != expected['sha256'] or row[side+'_bytes'] != expected['bytes']:
            raise ValueError('Incorrect '+side+' image identity')
    if row['source_version'] != '0.5.52' or manifest['version'] != VERSION:
        raise ValueError('Wrong diagnostic version route')
    return dict(schema=1, version=VERSION, publication='pending_explicit_user_consent',
        github_release_created=False, hardware_verified=False, runtime_verified=False,
        diagnostic='restore original trophy package; preserve other 81 game files',
        source_commit=manifest['source_commit'], iso=proof['iso_verification'],
        manifest=manifest, validation=C.load(assets/'VALIDATION.json'),
        focused_tests=tests(), inherited_parent_regression=parent['regression_tests'],
        final_readback_sha256=sha256_file(C.PROOF), release_tool_version='0.5.4',
        release_tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=SDK,text=True).strip(),
        assets=[dict(name=p.name, bytes=p.stat().st_size, sha256=sha256_file(p)) for p in sorted(assets.iterdir())])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('config','seal'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = config() if args.action == 'config' else seal()
    print('One complete-image route from exact 0.5.52; trophy-only restoration; hardware test pending.')
    if args.action == 'seal':
        print('Focused checks:', data['focused_tests'])
    if args.apply:
        if args.action == 'config':
            if FOLDER.exists():
                raise ValueError('Preserve existing diagnostic delivery')
            write_json(FOLDER/'release-local.json', data)
        else:
            write_json(READY, data)
    else:
        print('DRY RUN: no release metadata written. No GitHub release is authorized.')


if __name__ == '__main__':
    main()
