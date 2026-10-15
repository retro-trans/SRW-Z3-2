"""Check the reported Episode 41 SR in an already prepared build.

No game assets are changed. --apply records evidence and the reported image.
"""
import argparse
import json
import shutil
from pathlib import Path

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import mission_text as M, mission_display as D, mission_panel as P
from tools import ui_hook as H, library_build as L
from tools.cpk import CPK

TARGET = 'b8053eef6cae48f466a846c5e5a8f77d7ce852856551b0c8c30d17e9c1474242'
SHOT = Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-890a8621-c080-40c8-9608-fb7793acdc7c.png')
SAVED = ROOT / 'work/ui/screenshots/reported-sr-followup-episode41.png'


def verify(version):
    folder = ROOT / 'work/output/builds' / version
    build = json.loads((folder / 'build.json').read_text('utf8'))
    hashes = {}
    for name in ('EBOOT.BIN', 'STGZ3OF2.SDAT', 'STGZ3OF2.cpk'):
        hashes[name] = sha256_file(folder / name)
        expected = (build['stage_archive']['cpk_sha256'] if name.endswith('.cpk')
                    else build['outputs'][name])
        if hashes[name] != expected:
            raise ValueError('Prepared asset changed: ' + name)
    elf = (folder / 'EBOOT.BIN').read_bytes()
    mapping = build['mapping']
    rendered = M.plan(D.advance)
    row = next(r for r in D.rows(rendered) if sha256(r['jp'].encode('cp932')) == TARGET)
    lines = D.line_texts(row)
    widths = [sum(D.advance(c) for c in line) for line in lines]
    if len(lines) > P.SR_ROWS or max(widths) > M.LINE_UNITS - 64:
        raise ValueError('Episode 41 SR exceeds the panel')
    info = build['executable']['ui_hook']
    runner = H._Runner(elf, int(info['stub_va'], 16), info['stub_bytes'])
    read = H._reader(elf, H._headers(elf)[2])
    wanted = {r['key']: r['english'] for r in D.hook_entries(H.PREPARED.read_bytes(), rendered, mapping)}
    cases = []
    original = (M.dlg.MEMBERS / '00554.bin').read_bytes()
    with CPK(folder / 'STGZ3OF2.cpk') as archive:
        raw = archive.read(next(r for r in archive.files if r['id'] == 554))
    source_tables = M.tables(original)
    compiled_tables = list(M.OP.finditer(raw))
    if len(source_tables) != len(compiled_tables):
        raise ValueError('Episode 41 table inventory changed')
    for table_index, (source, compiled) in enumerate(zip(source_tables, compiled_tables)):
        strings = [M.unescape_bytes(r.group(1)) for r in M.LIT.finditer(compiled.group(1))]
        if len(strings) != len(source[1]) or compiled.group(2) != source[0].group(2):
            raise ValueError('Episode 41 condition IDs changed')
        selected = [i for i, (_, jp) in enumerate(source[1]) if sha256(jp.encode('cp932')) == TARGET]
        if not selected:
            continue
        for index in selected:
            if strings[index] != D.stage_key(row).encode('cp932'):
                raise ValueError('Packaged Episode 41 SR differs from the shortened text')
        for phase_index, phase in enumerate(P.phases(compiled)):
            for changed in (False, True):
                records, steps = P.assemble(elf, strings, phase, None if changed else phase)
                sr = [r for r in records['sr'] if r['active']]
                if not sr or sr[0]['text'] != D.line_key(row, 0).encode('cp932'):
                    continue
                actual = []
                for record in sr:
                    key = record['text']
                    expected = wanted[key]
                    pointer, _ = runner.run(key + b'\0')
                    if read(pointer, len(expected) + 1) != expected + b'\0':
                        raise ValueError('Episode 41 final draw lookup failed')
                    actual.append(L.decode(expected, mapping))
                if actual != lines or any(r['state'] != int(changed) for r in sr):
                    raise ValueError('Native panel clips the SR or changes its color state')
                cases.append(dict(table=table_index, phase=phase_index, changed=changed,
                                  native_steps=steps, english=actual))
    if not cases or {r['changed'] for r in cases} != {False, True}:
        raise ValueError('Reported SR was not exercised in both native color states')
    shot = SHOT if SHOT.exists() else SAVED
    return dict(schema=1, version=version, episode=41, member=554,
                source_sha256=TARGET, game_assets_changed=False, asset_sha256=hashes,
                english_lines=lines, line_width_units=widths,
                maximum_line_units=M.LINE_UNITS - 64, maximum_rows=P.SR_ROWS,
                native_phases=cases, runtime_verified=False,
                screenshot=dict(source=str(shot), saved_path=str(SAVED), sha256=sha256_file(shot)),
                verifier_sha256=sha256_file(Path(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='0.5.36')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = verify(args.version)
    print('\n'.join(data['english_lines']))
    print('%d native phases passed; four complete rows fit.' % len(data['native_phases']))
    if not args.apply:
        print('DRY RUN: no assets, evidence or screenshots written.')
        return
    shot = data['screenshot']
    source, target = Path(shot['source']), Path(shot['saved_path'])
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and sha256_file(target) != shot['sha256']:
        raise ValueError('Reported screenshot collision')
    if source != target:
        shutil.copyfile(source, target)
    write_json(ROOT / 'work/ui' / ('sr_followup_' + args.version + '.json'), data)


if __name__ == '__main__':
    main()
