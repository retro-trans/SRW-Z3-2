"""Seal Retro Trans delivery for the experimental 0.5.52 CFW ISO; never publish."""
import argparse
import json
import re
import subprocess
import sys
from tools.common import ROOT, sha256_file, write_json
from tools import cfw_package as B
from tools.release_prepare51 import inputs

VERSION = B.VERSION
FOLDER = ROOT/'work/output/releases'/VERSION
SDK = ROOT/'work/output/release-tools-v0.5.4'
READY = ROOT/f'work/ui/local_release_{VERSION}.json'


def tests():
    path = ROOT/f'work/output/scratch/startup-{VERSION}-tests.log'
    raw = path.read_bytes()
    text = raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig')
    found = re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)', text)
    if not found:
        raise ValueError('Successful full regression required')
    count, skipped = int(found[1]), int(found[2] or 0)
    if count < 379:
        raise ValueError('CFW tests missing from full regression')
    return dict(run=count, passed=count-skipped, skipped=skipped, log_sha256=sha256_file(path))


def proof():
    data = json.loads(B.PROOF.read_text('utf8'))
    if data['build_sha256'] != sha256_file(B.OUTPUT/'build.json'):
        raise ValueError('Candidate build differs from final readback')
    if not data['self_checks']['payload_byte_identical'] or not data['other_game_files_and_fonts_unchanged']:
        raise ValueError('Incomplete wrapper isolation')
    image = data['iso_verification']
    if image['version'] != VERSION or image['image'] != str(B.IMAGE) or image['files_verified_each_tree'] != 82:
        raise ValueError('Incorrect final image proof')
    if B.IMAGE.stat().st_size != image['bytes']:
        raise ValueError('Final image size differs')
    return data


def config():
    data = proof()
    tests()
    prior, sources = inputs()
    result = {k:prior[k] for k in ('game_id', 'game_name', 'platform')}
    result.update(version=VERSION, source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), patches=[])
    for source in sources:
        if source['path'].stat().st_size != source['bytes']:
            raise ValueError('Incorrect source size')
        result['patches'].append(dict(patch=f"SRW-Z3-2-PS3-English-{VERSION}-CFW-test-from-{source['version']}.xdelta",
            edition='jp-bljs10299', language='en', source_version=source['version'],
            source_format='iso', target_format='iso', source=str(source['path']), target=str(B.IMAGE)))
    return result


def seal():
    sys.path.insert(0, str(SDK))
    from retro_trans.release import validate_directory
    assets = FOLDER/'artifacts'
    manifest = validate_directory(assets)
    final = proof()
    _, sources = inputs()
    expected = {r['version']:r for r in sources}
    if len(manifest['patches']) != 2 or {p['source_version'] for p in manifest['patches']} != set(expected):
        raise ValueError('Both complete-image delivery routes required')
    for row in manifest['patches']:
        source = expected[row['source_version']]
        if row['source_sha256'] != source['sha256'] or row['source_bytes'] != source['bytes']:
            raise ValueError('Source differs from published identity')
        if row['target_sha256'] != final['iso_verification']['sha256'] or row['target_bytes'] != final['iso_verification']['bytes']:
            raise ValueError('Patch target differs from verified image')
    return dict(schema=1, version=VERSION, publication='pending_explicit_user_consent',
        github_release_created=False, experimental_cfw_candidate=True, hardware_verified=False,
        runtime_verified=False, source_commit=manifest['source_commit'], release_tool_version='0.5.4',
        release_tool_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=SDK, text=True).strip(),
        iso=final['iso_verification'], manifest=manifest,
        validation=json.loads((assets/'VALIDATION.json').read_text('utf8')), regression_tests=tests(),
        final_readback_sha256=sha256_file(B.PROOF),
        assets=[dict(name=p.name, bytes=p.stat().st_size, sha256=sha256_file(p)) for p in sorted(assets.iterdir())])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('config','seal'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = config() if args.action == 'config' else seal()
    print('Two complete-image Retro Trans routes; CFW candidate remains hardware-unverified.')
    if args.action == 'seal':
        print('Regression:', data['regression_tests'])
    if args.apply:
        if args.action == 'config':
            if FOLDER.exists():
                raise ValueError('Preserve existing candidate delivery')
            write_json(FOLDER/'release-local.json', data)
        else:
            write_json(READY, data)
    else:
        print('DRY RUN: no release metadata written; publication is not authorized.')


if __name__ == '__main__':
    main()
