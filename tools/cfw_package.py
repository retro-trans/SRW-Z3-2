"""Prepare Tengoku 0.5.52 CFW test packaging; dry run unless --apply.

Keep the sealed 0.5.51 executable byte-identical inside a disc fake-SELF.
Only the wrapper and title-version artwork change. Never install or publish.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import cfw_self as S, self_elf, title_screen as T, eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as cpk_build
from tools.verify_archives import compare
from tools.isoread import ISO9660, SECTOR
from tools.pipeline import config
from tools import iso_write as I

VERSION = '0.5.52'
BASE = ROOT/'work/output/builds/0.5.51'
OUTPUT = ROOT/'work/output/builds'/VERSION
IMAGE = ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}-CFW-test.iso'
PROOF = ROOT/f'work/ui/cfw_verified_{VERSION}.json'
FSELF = Path('E:/Projects/SRW Z3/work/cfw_psl1ght/fself.exe')
FSELF_SHA = 'b3bc066b39b69adff7fd59c849b14bb8754c4c306c549aa1ecd791b953799554'
UPSTREAM = 'https://github.com/ps3dev/PSL1GHT/tree/f649a08fd536a9e27c08c7db2d93a2d7ee4c3bbe/tools/fself'
CHANGED = {'EBOOT.BIN', 'EFFPS3.CPK'}
EXTRAS = ('font_1.bin', 'font_3.bin', 'rpw.bin', 'STGZ3OF2.cpk')


def load(path):
    return json.loads(path.read_text('utf8'))


def original():
    settings = config(ROOT/'config/tengoku.json')
    with ISO9660(settings['iso']) as iso:
        raw = iso.read(dict(iso.walk())[self_elf.EBOOT])
    S.need(sha256(raw) == self_elf.SELF_SHA256, 'Original Tengoku SELF differs')
    return raw


def parent():
    b = load(BASE/'build.json')
    seal = load(ROOT/'work/ui/local_release_0.5.51.json')
    proof = ROOT/'work/ui/review51_verified_0.5.51.json'
    S.need(b['version'] == '0.5.51' and sha256_file(proof) == seal['final_readback_sha256'],
           'Parent proof/seal differs')
    S.need(load(proof)['build_sha256'] == sha256_file(BASE/'build.json'), 'Parent build differs')
    for name, digest in b['outputs'].items():
        S.need(sha256_file(BASE/name) == digest, 'Parent output differs: '+name)
    S.program_headers((BASE/'EBOOT.BIN').read_bytes())
    return b


def preflight(fself):
    b = parent()
    S.need(sha256_file(fself) == FSELF_SHA, 'Unexpected fself tool; use pinned build')
    raw = original()
    source = E.source_members(E._settings(), [T.MEMBER], {T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title, pixels, _, title_info = T.render(source, VERSION)
    T.verify(source, title, pixels)
    print('Base: 0.5.51; all', len(b['outputs']), 'output hashes match its seal.', flush=True)
    print('ELF will be preserved byte for byte; original disc identity/capabilities retained.', flush=True)
    print('Only EBOOT wrapper and title-version artwork change; no install or publication.', flush=True)
    return b, raw, title, title_info


def build(state, fself):
    b, raw, title, title_info = state
    S.need(not OUTPUT.exists(), 'Preserve existing 0.5.52 build')
    OUTPUT.mkdir(parents=True)
    generated = OUTPUT/'fself-generated.bin'
    subprocess.run([str(fself), str(BASE/'EBOOT.BIN'), str(generated)], check=True)
    wrapped = S.retain_identity(generated.read_bytes(), raw)
    checks = S.verify(wrapped, (BASE/'EBOOT.BIN').read_bytes(), raw)
    with (OUTPUT/'EBOOT.BIN').open('xb') as stream:
        stream.write(wrapped)
    for name in b['outputs']:
        if name not in CHANGED:
            shutil.copyfile(BASE/name, OUTPUT/name)
    for name in EXTRAS:
        shutil.copyfile(BASE/name, OUTPUT/name)
    with CPK(BASE/'EFFPS3.CPK') as arc:
        compress = {r['id'] for r in arc.files if r['id'] == T.MEMBER and r['size'] != r['extract']}
    cpk_build(BASE/'EFFPS3.CPK', OUTPUT/'EFFPS3.CPK', {T.MEMBER:title}, compress=compress)
    isolation = compare(BASE/'EFFPS3.CPK', OUTPUT/'EFFPS3.CPK', {T.MEMBER:title})
    report = copy.deepcopy(b)
    report.update(version=VERSION, title_screen=title_info, runtime_verified=False, layout_verified=False)
    report['outputs'] = {name:sha256_file(OUTPUT/name) for name in b['outputs']}
    report['executable']['output_sha256'] = sha256(wrapped)
    report['cfw_packaging'] = dict(checks, source_elf_sha256=b['outputs']['EBOOT.BIN'],
        original_self_sha256=sha256(raw), fself_sha256=FSELF_SHA, fself_upstream=UPSTREAM,
        original_game_logic_and_memory_layout_preserved=True, installed=False)
    report['incremental_build'] = dict(parent_version='0.5.51', parent_build_sha256=sha256_file(BASE/'build.json'),
        unchanged_fonts=True, archive_isolation={'EFFPS3.CPK':isolation})
    write_json(OUTPUT/'build.json', report)
    print('Built', VERSION, 'CFW candidate:', len(wrapped), 'SELF bytes.', flush=True)


def components():
    b, after = parent(), load(OUTPUT/'build.json')
    S.need(after['version'] == VERSION and set(after['outputs']) == set(b['outputs']), 'Mixed candidate')
    changed = []
    for name, digest in after['outputs'].items():
        S.need(sha256_file(OUTPUT/name) == digest, 'Candidate output differs: '+name)
        if digest != b['outputs'][name]:
            changed.append(name)
    S.need(set(changed) == CHANGED, 'Changes exceed wrapper and version artwork')
    for name in EXTRAS:
        S.need(sha256_file(BASE/name) == sha256_file(OUTPUT/name), 'Supporting/font bytes differ')
    checks = S.verify((OUTPUT/'EBOOT.BIN').read_bytes(), (BASE/'EBOOT.BIN').read_bytes(), original())
    with CPK(OUTPUT/'EFFPS3.CPK') as arc:
        actual = arc.read(next(r for r in arc.files if r['id'] == T.MEMBER))
    source = E.source_members(E._settings(), [T.MEMBER], {T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    wanted, pixels, _, _ = T.render(source, VERSION)
    T.verify(source, actual, pixels)
    S.need(actual == wanted, 'Title-version artwork differs')
    isolation = compare(BASE/'EFFPS3.CPK', OUTPUT/'EFFPS3.CPK', {T.MEMBER:wanted})
    return dict(schema=1, version=VERSION, parent_version='0.5.51',
        build_sha256=sha256_file(OUTPUT/'build.json'), self_checks=checks,
        parent_native_proof_sha256=sha256_file(ROOT/'work/ui/review51_verified_0.5.51.json'),
        parent_regression_tests=load(ROOT/'work/ui/local_release_0.5.51.json')['regression_tests'],
        changed_outputs=sorted(changed), archive_isolation=isolation,
        other_game_files_and_fonts_unchanged=True, hardware_verified=False, runtime_verified=False)


def image(apply):
    components()
    b = load(OUTPUT/'build.json')
    settings = config(ROOT/'config/tengoku.json')
    manifest = load(settings['work']/'source_manifest.json')
    from tools.game_build import LIBRARY
    from tools.inventory import RPW, FONT
    from tools.dialogue_build import STAGE_ARCHIVE
    from tools.srvc import SRVC
    replacements = {self_elf.EBOOT:OUTPUT/'EBOOT.BIN', RPW:OUTPUT/'RPW_DATA.CPK', FONT:OUTPUT/'TPACKPS3.CPK'}
    replacements.update({p:OUTPUT/Path(p).name for p in LIBRARY.values()})
    replacements[STAGE_ARCHIVE] = OUTPUT/'STGZ3OF2.SDAT'
    replacements[SRVC] = OUTPUT/'SRVC.BIN'
    for path, name in b.get('disc_files', {}).items():
        S.need(path not in replacements, 'Duplicate disc replacement')
        replacements[path] = OUTPUT/name
    print('ISO replacements:', len(replacements), '; output:', IMAGE, flush=True)
    if not apply:
        return
    S.need(not IMAGE.exists(), 'Preserve existing hardware test image')
    S.need(sha256_file(settings['iso']) == manifest['iso_sha256'], 'Original disc image differs')
    IMAGE.parent.mkdir(parents=True, exist_ok=True)
    result = I.write(Path(settings['iso']), IMAGE, replacements, manifest['files'])
    result.update(version=VERSION, build=str(OUTPUT), source_iso_sha256=manifest['iso_sha256'],
        replaced={d:p.name for d,p in replacements.items()}, cfw_test_candidate=True,
        rpcs3_only=False, hardware_verified=False, runtime_verified=False)
    write_json(IMAGE.with_suffix('.json'), result)
    proof = components()
    proof['iso_verification'] = result
    write_json(PROOF, proof)
    print('ISO verified:', result['sha256'], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'iso', 'verify'))
    parser.add_argument('--fself', type=Path, default=FSELF)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.action == 'build':
        state = preflight(args.fself)
        if args.apply:
            build(state, args.fself)
    elif args.action == 'iso':
        image(args.apply)
    else:
        proof = components()
        print('SELF payload, all segments, application metadata and carried files verified.', flush=True)
        if args.apply:
            if PROOF.exists():
                proof['iso_verification'] = load(PROOF)['iso_verification']
            write_json(PROOF, proof)
    if not args.apply:
        print('DRY RUN: no game assets or metadata written.', flush=True)


if __name__ == '__main__':
    main()
