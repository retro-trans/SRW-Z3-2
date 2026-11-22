"""0.5.53 hardware isolation: restore only the original disc trophy package.

The complete 0.5.52 image is the source. Its program, version artwork and
other 81 game files are preserved. No trophy bypass or installed-data edits.
"""
import argparse
import json
import re
from pathlib import Path

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import cfw_package as B, iso_write as I, trophy_text as T
from tools.isoread import ISO9660
from tools.pipeline import config

VERSION = '0.5.53'
OUTPUT = ROOT/'work/output/builds'/VERSION
IMAGE = ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}-original-trophies-CFW-test.iso'
PROOF = ROOT/f'work/ui/cfw_trophy_verified_{VERSION}.json'
ORIGINAL_SHA = '0da66f959beb04ef0a1e60bb9838bdf55c7003f4b4342383e812061af7f46e52'
PATCHED_SHA = '2521580590639e78a5e8f0d9705a7cd3f8dbc3158d740748bac076b1364e805c'


def load(path):
    return json.loads(path.read_text('utf8'))


def parent():
    seal = load(ROOT/'work/ui/local_release_0.5.52.json')
    if sha256_file(B.PROOF) != seal['final_readback_sha256']:
        raise ValueError('Parent delivery proof changed')
    proof = load(B.PROOF)
    if proof['build_sha256'] != sha256_file(B.OUTPUT/'build.json'):
        raise ValueError('Parent build changed')
    build = load(B.OUTPUT/'build.json')
    for name, digest in build['outputs'].items():
        if sha256_file(B.OUTPUT/name) != digest:
            raise ValueError('Parent asset changed: '+name)
    if seal['version'] != '0.5.52' or Path(seal['iso']['image']) != B.IMAGE:
        raise ValueError('Wrong parent image')
    return seal, build


def audit():
    original, patched = T.source(), (B.OUTPUT/'TROPHY.TRP').read_bytes()
    if sha256(original) != ORIGINAL_SHA or sha256(patched) != PATCHED_SHA:
        raise ValueError('Unexpected original/translated trophy package')
    old = {r['name']:r for r in T.unpack(original)}
    new = {r['name']:r for r in T.unpack(patched)}
    changed = [name for name in old if old[name]['data'] != new[name]['data']]
    if changed != ['TROP.SFM', 'TROP_00.SFM']:
        raise ValueError('Trophy changes exceed expected metadata')
    comments = []
    for name in changed:
        source = re.findall(rb'<!--.*?-->', old[name]['data'], re.S)
        after = re.findall(rb'<!--.*?-->', new[name]['data'], re.S)
        comments.append(dict(name=name, original_comment_bytes=[len(c) for c in source],
                             original_comment_sha256=[sha256(c) for c in source],
                             translated_comment_count=len(after)))
    return original, dict(original_sha256=ORIGINAL_SHA, translated_sha256=PATCHED_SHA,
        original_bytes=len(original), translated_bytes=len(patched), changed_members=changed,
        comments=comments, original_member_count=len(old), original_trophy_count=35,
        both_container_sha1_checks_pass=True, physical_signature_validation_not_proven=True)


def plan():
    seal, build = parent()
    original, report = audit()
    settings = config(ROOT/'config/tengoku.json')
    manifest = load(settings['work']/'source_manifest.json')
    replacements = {path:B.OUTPUT/name for path, name in seal['iso']['replaced'].items()}
    for path, local in replacements.items():
        if sha256_file(local) != build['outputs'][local.name]:
            raise ValueError('Unexpected source mapping: '+path)
    expected = I.expected_files(replacements, manifest['files'])
    if len(expected) != 82 or expected[T.DISC]['sha256'] != PATCHED_SHA:
        raise ValueError('Wrong parent inventory')
    print('0.5.53 trophy control: restore original TROPHY.TRP;', len(original), 'bytes.', flush=True)
    print('Only one logical game file changes. EBOOT and all other 81 files stay identical.', flush=True)
    print('The title artwork deliberately still says 0.5.52; identify test by filename/checksum.', flush=True)
    print('No installed trophy data, saves, emulator registration or firmware changes.', flush=True)
    return original, report, seal, expected


def build(state):
    original, audit_report, seal, expected = state
    if OUTPUT.exists() or IMAGE.exists() or PROOF.exists():
        raise ValueError('Preserve existing 0.5.53 candidate')
    if sha256_file(B.IMAGE) != seal['iso']['sha256']:
        raise ValueError('0.5.52 source ISO differs from delivery seal')
    with ISO9660(B.IMAGE) as iso:
        paths = {path.upper():entry for path,entry in iso.walk()}
        if set(paths) != set(expected) or sha256(iso.read(paths[T.DISC])) != PATCHED_SHA:
            raise ValueError('Source ISO trophy/inventory mismatch')
    OUTPUT.mkdir(parents=True)
    with (OUTPUT/'TROPHY.TRP').open('xb') as stream:
        stream.write(original)
    write_json(OUTPUT/'build.json', dict(schema=1, version=VERSION, parent_version='0.5.52',
        type='single-file trophy restoration control', parent_iso_sha256=seal['iso']['sha256'],
        changed_game_files=[T.DISC], unchanged_game_files=81, title_artwork_version='0.5.52',
        executable_byte_identical=True, trophy_package_sha256=ORIGINAL_SHA, audit=audit_report,
        hardware_verified=False, runtime_verified=False, installed=False))
    IMAGE.parent.mkdir(parents=True, exist_ok=True)
    manifest = [dict(path=r['path'], size=r['bytes'], sha256=r['sha256']) for r in expected.values()]
    result = I.write(B.IMAGE, IMAGE, {T.DISC:OUTPUT/'TROPHY.TRP'}, manifest)
    result.update(version=VERSION, parent_version='0.5.52', source_iso_sha256=seal['iso']['sha256'],
        changed_game_files=[T.DISC], title_artwork_version='0.5.52', cfw_test_candidate=True,
        hardware_verified=False, runtime_verified=False)
    verify(result)
    write_json(IMAGE.with_suffix('.json'), result)
    write_json(PROOF, dict(schema=1, version=VERSION, build_sha256=sha256_file(OUTPUT/'build.json'),
        parent_delivery_sha256=sha256_file(ROOT/'work/ui/local_release_0.5.52.json'),
        changed_game_files=[T.DISC], unchanged_game_files=81, executable_byte_identical=True,
        original_trophy_package_restored=True, original_trophy_ids_icons_and_metadata_restored=True,
        title_artwork_version='0.5.52', audit=audit_report, iso_verification=result,
        parent_tests=seal['regression_tests'], hardware_verified=False, runtime_verified=False))
    print('Verified single-file trophy-control ISO:', result['sha256'], flush=True)


def verify(result):
    if result['files_verified_each_tree'] != 82:
        raise ValueError('Incomplete disc verification')
    for joliet in (True, False):
        with ISO9660(IMAGE, joliet=joliet) as iso:
            paths = dict(iso.walk())
            data = iso.read(paths[T.DISC])
            if sha256(data) != ORIGINAL_SHA or data != T.source():
                raise ValueError('Original trophy package not restored exactly')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    state = plan()
    if args.apply:
        build(state)
    else:
        print('DRY RUN: no image or game files written.', flush=True)


if __name__ == '__main__':
    main()
