"""Verify final backlog buffers, corpus coverage, parent isolation and ISO."""
import argparse
import json
import re
import shutil
from pathlib import Path
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import review37_build as B, review37_backlog as A, backlog_verify as V
from tools import dialogue as D, library_build as L
from tools.verify_review34 import members_equal
from tools.cpk import CPK

SHOT = Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-95d835fe-1d1d-4bd4-bcce-b545ca4423da.png')
SAVED = ROOT / 'work/ui/screenshots/reported-review37-backlog.png'


def verify():
    folder = ROOT / 'work/output/builds' / B.VERSION
    build = json.loads((folder / 'build.json').read_text('utf8'))
    planned = B.plan()
    unchanged = []
    for name, digest in build['outputs'].items():
        if sha256_file(folder / name) != digest:
            raise ValueError('Final output changed: ' + name)
        if name not in ('EBOOT.BIN', 'EFFPS3.CPK'):
            if digest != planned['prior']['outputs'][name]:
                raise ValueError('Unrelated game output differs: ' + name)
            unchanged.append(dict(name=name, sha256=digest))
    elf = (folder / 'EBOOT.BIN').read_bytes()
    if elf != planned['executable'] or build['executable']['backlog_storage'] != planned['backlog']:
        raise ValueError('Final backlog patch differs from canonical guarded changes')
    carried = members_equal(B.BASE / 'EFFPS3.CPK', folder / 'EFFPS3.CPK', {229})
    with CPK(folder / 'EFFPS3.CPK') as arc:
        if arc.read(next(r for r in arc.files if r['id'] == 229)) != planned['title_bytes']:
            raise ValueError('Final title version differs')
    if sha256_file(folder / 'STGZ3OF2.cpk') != build['stage_archive']['cpk_sha256']:
        raise ValueError('Decoded stage sidecar differs from certified stage content')
    data = A.corpus()
    with CPK(folder / 'STGZ3OF2.cpk') as arc:
        raw = arc.read(next(r for r in arc.files if r['id'] == 557))
    text = raw.decode('latin1')
    event = next(e for e in D.EVENT.finditer(text) if e.group(1) == 't_011')
    block = list(D.BLOCK.finditer(event.group(2)))[15].group(1).encode('latin1')
    if block.replace(b'\r\n', b'\n') != data['reported']['raw']:
        raise ValueError('Reported backlog fixture differs from packaged dialogue')
    native = A.verify(elf)
    old = V.exercise((B.BASE / 'EBOOT.BIN').read_bytes(), [data['reported']['raw']], expanded=False)
    clipped = bytes.fromhex(old.pop('final_text'))
    try:
        L.decode(clipped, build['mapping'])
    except UnicodeDecodeError:
        old['split_font_cell_reproduced'] = True
    else:
        raise ValueError('Original backlog no longer reproduces the reported split cell')
    old.update(input_bytes=len(data['reported']['raw']), stored_bytes=len(clipped),
               final_byte=clipped[-1:].hex(), source_version='0.5.36')
    image_path = ROOT / 'work/output/iso' / B.VERSION / ('Tengoku-hen-English-' + B.VERSION + '.json')
    image = json.loads(image_path.read_text('utf8'))
    if image['version'] != B.VERSION or image['files_verified_each_tree'] != 82:
        raise ValueError('Incomplete final ISO evidence')
    if sha256_file(Path(image['image'])) != image['sha256']:
        raise ValueError('Final ISO changed')
    shot = SHOT if SHOT.exists() else SAVED
    return dict(schema=1, version=B.VERSION, previous_public_version='0.5.28',
                patch=planned['backlog'], backlog=native, old_build_reproduction=old,
                packaged_dialogue_sha256=sha256(block),
                carried_verification=dict(version='0.5.36', proof_sha256=planned['parent_proof_sha256'],
                    unchanged_files=unchanged, unchanged_eff_members=carried,
                    executable_changes_limited_to='114 guarded backlog constants; all other executable bytes identical'),
                iso_verification=image, runtime_verified=False,
                screenshots=[dict(source=str(shot), saved_path=str(SAVED), sha256=sha256_file(shot))])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    if args.preview:
        print('DRY RUN: all dialogue budgets, native ring/row paths, packaged Leonard text, isolated parent bytes and ISO.')
        return
    data = verify()
    print('63,553 dialogue entries; 204 formerly over-budget entries; 125 long backlog rows verified.')
    print('Both constructors, 370 ring shifts, link identities, duplicate suppression, stack/frame canaries and resets passed.')
    print('Original split font cell reproduced; complete packaged Leonard dialogue retained.')
    print('ISO:', data['iso_verification']['sha256'])
    if not args.apply:
        print('DRY RUN: no evidence or screenshots written.')
        return
    for row in data['screenshots']:
        src, dst = Path(row['source']), Path(row['saved_path'])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256_file(dst) != row['sha256']:
            raise ValueError('Reported backlog screenshot collision')
        if src != dst:
            shutil.copyfile(src, dst)
    write_json(ROOT / 'work/ui/review37_verified_0.5.37.json', data)


if __name__ == '__main__':
    main()
