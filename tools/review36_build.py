"""Build only the three guarded Funds coordinates and the new title stamp.

All other game bytes are copied from the fully verified 0.5.35 candidate.
The canonical UI planner must produce precisely the same coordinate-only diff.
"""
import argparse
import copy
import json
import shutil
import struct
from tools.common import ROOT, contained, sha256, sha256_file, write_json
from tools import review36_funds as F, ui_layout_text as U, title_screen as T, eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

BASE = ROOT/'work/output/builds/0.5.35'


def plan():
    from tools.pipeline import config
    from tools.game_build import VERSION
    if VERSION != '0.5.36':
        raise ValueError('This incremental builder is bound to 0.5.36')
    if json.loads(F.DEST.read_text('utf8')) != F.plan():
        raise ValueError('Funds plan is stale')
    prior = json.loads((BASE/'build.json').read_text('utf8'))
    ready = json.loads((ROOT/'work/ui/local_release_0.5.35.json').read_text('utf8'))
    proof = ROOT/'work/ui/review35_verified_0.5.35.json'
    if sha256_file(proof) != ready['final_readback_sha256']:
        raise ValueError('Certified parent proof changed')
    for name, digest in prior['outputs'].items():
        if sha256_file(BASE/name) != digest:
            raise ValueError('Certified parent output changed: '+name)
    art = U.plan(config(ROOT/'config/tengoku.json'), prior['mapping'])
    with CPK(BASE/'AIDDATAPACK.CPK') as arc:
        old = arc.read(next(r for r in arc.files if r['id'] == 0))
    new = art['members'][0]
    if len(old) != len(new):
        raise ValueError('Coordinate-only fix changed the UI pool size')
    from tools.battle_layout import source
    grow = len(new)-len(source()); restored = bytearray(new)
    for row in F.plan()['edits']:
        at = row['widget_offset']+grow+4
        restored[at:at+4] = old[at:at+4]
    if restored != old:
        raise ValueError('Canonical UI plan changes more than three Funds coordinates')
    raw = E.source_members(E._settings(), [T.MEMBER], {T.MEMBER: T.SOURCE_SHA})[T.MEMBER]
    title, pixels, _, info = T.render(raw, VERSION)
    T.verify(raw, title, pixels)
    return dict(prior=prior, ui=art, ui_bytes=new, title_bytes=title, title_info=info,
                parent_proof_sha256=sha256_file(proof))


def build(planned):
    folder = contained(ROOT/'work/output/builds', ROOT/'work/output/builds/0.5.36')
    if folder.exists():
        raise ValueError('Preserve existing candidate; 0.5.36 already exists')
    folder.mkdir(parents=True)
    report = copy.deepcopy(planned['prior'])
    for name in report['outputs']:
        if name not in ('AIDDATAPACK.CPK', 'EFFPS3.CPK'):
            shutil.copyfile(BASE/name, folder/name)
    for name in ('font_1.bin', 'font_3.bin', 'rpw.bin', 'STGZ3OF2.cpk'):
        shutil.copyfile(BASE/name, folder/name)
    aid = BASE/'AIDDATAPACK.CPK'
    build_cpk(aid, folder/aid.name, {0: planned['ui_bytes']})
    aid_report = compare(aid, folder/aid.name, {0: planned['ui_bytes']})
    ui_verified = U.verify_archive(folder/aid.name, planned['ui'])
    eff = BASE/'EFFPS3.CPK'
    with CPK(eff) as arc:
        row = next(r for r in arc.files if r['id'] == T.MEMBER)
        compressed = {T.MEMBER} if row['size'] != row['extract'] else set()
    build_cpk(eff, folder/eff.name, {T.MEMBER: planned['title_bytes']}, compress=compressed)
    title_report = compare(eff, folder/eff.name, {T.MEMBER: planned['title_bytes']})
    report.update(version='0.5.36', runtime_verified=False, layout_verified=False,
                  title_screen=planned['title_info'], ui_context_text=planned['ui']['report']['context_text'])
    report['extra_art']['AIDDATAPACK.CPK'] = dict(archive=aid_report, members_verified=ui_verified)
    report['extra_art']['EFFPS3.CPK'] = dict(archive=title_report, title=planned['title_info'])
    for name in report['outputs']:
        actual = sha256_file(folder/name)
        if name not in ('AIDDATAPACK.CPK', 'EFFPS3.CPK') and actual != planned['prior']['outputs'][name]:
            raise ValueError('Copied game file differs: '+name)
        report['outputs'][name] = actual
    report['incremental_build'] = dict(parent_version='0.5.35',
        parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=planned['parent_proof_sha256'], changed_ui_coordinates=3,
        unchanged_executable=True, unchanged_fonts=True, unchanged_stage_wrapper=True)
    write_json(folder/'build.json', report)
    print('Built 0.5.36: three Funds coordinates and title stamp; every other game file unchanged.')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true'); args = p.parse_args()
    planned = plan()
    print('Canonical UI diff: exactly three x coordinates; pool, labels, metrics and counters unchanged.')
    print('Title:', planned['title_info']['version'])
    if args.apply:
        build(planned)
    else:
        print('DRY RUN: no game files written.')


if __name__ == '__main__':
    main()
