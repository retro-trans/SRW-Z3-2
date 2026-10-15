"""Certify the Funds coordinate delta and retained two-line news headline."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools import review36_build as B, review36_funds as F, ui_hook as H
from tools import review32_content as C, battle_layout as A, ui_catalog as U, library_build as L
from tools.cpk import CPK
from tools.verify_review34 import members_equal


def verify(version):
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text('utf8'))
    if version != '0.5.36' or build['version'] != version:
        raise ValueError('Funds candidate version differs')
    planned = B.plan(); prior = planned['prior']; unchanged = []
    for name, digest in build['outputs'].items():
        if sha256_file(folder/name) != digest:
            raise ValueError('Final game file changed: '+name)
        if name not in ('AIDDATAPACK.CPK', 'EFFPS3.CPK'):
            if digest != prior['outputs'][name]:
                raise ValueError('Carried game file differs: '+name)
            unchanged.append(dict(name=name, sha256=digest))
    aid_members = members_equal(B.BASE/'AIDDATAPACK.CPK', folder/'AIDDATAPACK.CPK', {0})
    eff_members = members_equal(B.BASE/'EFFPS3.CPK', folder/'EFFPS3.CPK', {229})
    for name, mid, expected in (('AIDDATAPACK.CPK', 0, planned['ui_bytes']),
                                ('EFFPS3.CPK', 229, planned['title_bytes'])):
        with CPK(folder/name) as arc:
            if arc.read(next(r for r in arc.files if r['id'] == mid)) != expected:
                raise ValueError('Changed archive member differs: '+name)
    elf = (folder/'EBOOT.BIN').read_bytes()
    cases = F.native_cases(elf)
    read = H._reader(elf, H._headers(elf)[2]); hook = build['executable']['ui_hook']
    runner = H._Runner(elf, int(hook['stub_va'], 16), hook['stub_bytes'])
    row = next(r for r in C.headlines() if r['va'] == '0x8a0f70')
    entry = next(r for r in C.hook_entries(H.PREPARED.read_bytes(), build['mapping'])
                 if r['id'] == 'review32:headline:0x8a0f70')
    pointer, _ = runner.run(entry['key']+b'\0')
    if read(pointer, len(entry['english'])+1) != entry['english']+b'\0':
        raise ValueError('Reported two-line headline differs')
    centered = C.origin_cases(elf, build['mapping'], build['executable']['link_layout'],
        only_rows=[(entry['id'], entry['english'], max(row['spans']), True)])
    source = A.source(); widgets = {at: r for r in U.fssa_strings(source) for at in r['widget_offsets']}
    for at in F.WIDGETS:
        key = widgets[at]['raw']; pointer, _ = runner.run(key+b'\0')
        expected = L.encode('Funds.', build['mapping'])
        if read(pointer, len(expected)+1) != expected+b'\0':
            raise ValueError('Shared Funds translation changed')
    ready = json.loads((ROOT/'work/ui/local_release_0.5.35.json').read_text('utf8'))
    image = json.loads((ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.json')).read_text('utf8'))
    if image['version'] != version or image['files_verified_each_tree'] != 82:
        raise ValueError('ISO evidence incomplete')
    if sha256_file(Path(image['image'])) != image['sha256']:
        raise ValueError('Final ISO changed')
    shots = []
    for label, ident in (('funds', '8621f1fa-1aba-4bce-b507-914dc1365295'),
                        ('headline', 'a3a56696-8e31-460b-b7ab-235c56661c4d')):
        src = Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst = ROOT/'work/ui/screenshots'/('reported-review36-'+label+'.png')
        if not src.exists(): src = dst
        shots.append(dict(issue=label, source=str(src), saved_path=str(dst), sha256=sha256_file(src)))
    return dict(schema=1, version=version, funds=F.plan(), native_amount_cases=cases,
        headline=dict(lines=row['lines'], spans=row['spans'], origin_cases=centered, already_prepared_in='0.5.35'),
        carried_verification=dict(version='0.5.35', proof_sha256=planned['parent_proof_sha256'],
            unchanged_files=unchanged, aid_members=aid_members, eff_members=eff_members,
            regression_tests=ready['regression_tests']),
        iso_verification=image, screenshots=shots, runtime_verified=False)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true')
    p.add_argument('--preview', action='store_true'); args = p.parse_args()
    if args.preview:
        print('DRY RUN: three-coordinate isolation, native cap/digit/alignment cases, retained headline, parent hashes and ISO.')
        return
    data = verify('0.5.36')
    print('Three Funds coordinates, 12 native amount cases, both headline origins and all carried file/member hashes passed.')
    print('ISO:', data['iso_verification']['sha256'])
    if not args.apply:
        print('DRY RUN: no evidence or screenshots written.'); return
    for row in data['screenshots']:
        src, dst = Path(row['source']), Path(row['saved_path'])
        if dst.exists() and sha256_file(dst) != row['sha256']:
            raise ValueError('Screenshot collision')
        if src != dst: shutil.copyfile(src, dst)
    write_json(ROOT/'work/ui/review36_verified_0.5.36.json', data)


if __name__ == '__main__':
    main()
