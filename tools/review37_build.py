"""Prepare the isolated backlog executable fix on the verified 0.5.36 candidate."""
import argparse
import copy
import json
import shutil
from tools.common import ROOT, contained, sha256, sha256_file, write_json
from tools import backlog_storage as B, title_screen as T, eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

BASE = ROOT / 'work/output/builds/0.5.36'
VERSION = '0.5.37'


def plan():
    from tools.game_build import VERSION as current
    if current != VERSION:
        raise ValueError('Backlog builder version differs')
    prior = json.loads((BASE / 'build.json').read_text('utf8'))
    ready = json.loads((ROOT / 'work/ui/local_release_0.5.36.json').read_text('utf8'))
    proof = ROOT / 'work/ui/review36_verified_0.5.36.json'
    if sha256_file(proof) != ready['final_readback_sha256']:
        raise ValueError('Certified parent proof changed')
    for name, digest in prior['outputs'].items():
        if sha256_file(BASE / name) != digest:
            raise ValueError('Certified parent output changed: ' + name)
    elf, report = B.apply((BASE / 'EBOOT.BIN').read_bytes())
    raw = E.source_members(E._settings(), [T.MEMBER], {T.MEMBER: T.SOURCE_SHA})[T.MEMBER]
    title, pixels, _, info = T.render(raw, VERSION)
    T.verify(raw, title, pixels)
    return dict(prior=prior, executable=elf, backlog=report, title_bytes=title,
                title_info=info, parent_proof_sha256=sha256_file(proof))


def build(planned):
    folder = contained(ROOT / 'work/output/builds', ROOT / 'work/output/builds' / VERSION)
    if folder.exists():
        raise ValueError('Preserve existing candidate: ' + VERSION)
    folder.mkdir(parents=True)
    report = copy.deepcopy(planned['prior'])
    for name in report['outputs']:
        if name not in ('EBOOT.BIN', 'EFFPS3.CPK'):
            shutil.copyfile(BASE / name, folder / name)
    for name in ('font_1.bin', 'font_3.bin', 'rpw.bin', 'STGZ3OF2.cpk'):
        shutil.copyfile(BASE / name, folder / name)
    (folder / 'EBOOT.BIN').write_bytes(planned['executable'])
    eff = BASE / 'EFFPS3.CPK'
    with CPK(eff) as arc:
        row = next(r for r in arc.files if r['id'] == T.MEMBER)
        compressed = {T.MEMBER} if row['size'] != row['extract'] else set()
    build_cpk(eff, folder / eff.name, {T.MEMBER: planned['title_bytes']}, compress=compressed)
    title_report = compare(eff, folder / eff.name, {T.MEMBER: planned['title_bytes']})
    report.update(version=VERSION, runtime_verified=False, layout_verified=False,
                  title_screen=planned['title_info'])
    report['extra_art']['EFFPS3.CPK'] = dict(archive=title_report, title=planned['title_info'])
    report['executable']['backlog_storage'] = planned['backlog']
    report['executable']['output_sha256'] = sha256(planned['executable'])
    for name in report['outputs']:
        actual = sha256_file(folder / name)
        if name not in ('EBOOT.BIN', 'EFFPS3.CPK') and actual != planned['prior']['outputs'][name]:
            raise ValueError('Copied game file differs: ' + name)
        report['outputs'][name] = actual
    report['incremental_build'] = dict(parent_version='0.5.36',
        parent_build_sha256=sha256_file(BASE / 'build.json'),
        parent_proof_sha256=planned['parent_proof_sha256'],
        changed_backlog_instructions=len(planned['backlog']['edits']),
        unchanged_fonts=True, unchanged_stage_wrapper=True)
    write_json(folder / 'build.json', report)
    print('Built 0.5.37: backlog storage/draw buffers and title stamp; other game files unchanged.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    planned = plan()
    print('Backlog entries: 308 -> 1076 bytes; rows: 128 -> 255 bytes.')
    print('Constructors, ring moves, resets and stack offsets:', len(planned['backlog']['edits']), 'guarded constants.')
    if args.apply:
        build(planned)
    else:
        print('DRY RUN: no game assets written.')


if __name__ == '__main__':
    main()
