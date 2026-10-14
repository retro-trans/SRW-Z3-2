"""Read back all SR conditions in the real four-row panel and final drawer."""
import argparse, json, shutil
from pathlib import Path
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import mission_text as M, mission_display as D, mission_panel as P
from tools import ui_hook as H, library_build as L, review31_sr as A
from tools.cpk import CPK

SHOTS = (('episode21', '6dcc1263-f15a-453d-8e57-95c1ed7e9c93'),
         ('episode20', 'e8063e1c-8ac9-43a8-ae96-3ba24df7c071'))


def verify(version):
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text('utf8'))
    mapping = build['mapping']; elf = (folder/'EBOOT.BIN').read_bytes()
    rendered = M.plan(D.advance); cases = P.sr_cases(elf, rendered, mapping)
    if len(cases) != 210 or len({r['source_sha256'] for r in cases}) != 101:
        raise ValueError('Incomplete SR panel coverage')
    audit, edits = A.plan()
    if edits or json.loads(A.DEST.read_text('utf8')) != audit:
        raise ValueError('SR meaning/layout audit is stale')
    read = H._reader(elf, H._headers(elf)[2]); info = build['executable']['ui_hook']
    runner = H._Runner(elf, int(info['stub_va'], 16), info['stub_bytes'])
    wanted = {r['key']: r['english'] for r in D.hook_entries(H.PREPARED.read_bytes(), rendered, mapping)}

    def english(records):
        result = []
        for record in records:
            if not record['active']:
                continue
            key = record['text']; expected = wanted[key]
            pointer, _ = runner.run(key+b'\0')
            if read(pointer, len(expected)+1) != expected+b'\0':
                raise ValueError('Native SR panel key fails final draw lookup')
            result.append(L.decode(expected, mapping))
        return result

    for case in cases:
        if case['profile'] == 'static':
            actual = english([dict(active=1, text=bytes.fromhex(k)) for k in case['keys']])
            if actual != case['english']:
                raise ValueError('Final SR English differs')
    stage = D.stage_text(rendered); sr_literals = []; reported = []
    with CPK(folder/'STGZ3OF2.cpk') as arc:
        index = {r['id']: r for r in arc.files}
        for member in M.members():
            original = (M.dlg.MEMBERS/('%05d.bin' % member)).read_bytes()
            raw = arc.read(index[member]); source_tables = M.tables(original)
            compiled_tables = list(M.OP.finditer(raw))
            if len(source_tables) != len(compiled_tables):
                raise ValueError('SR source tables changed')
            for table_index, (source, compiled) in enumerate(zip(source_tables, compiled_tables)):
                strings = [M.unescape_bytes(r.group(1)) for r in M.LIT.finditer(compiled.group(1))]
                if len(strings) != len(source[1]) or compiled.group(2) != source[0].group(2):
                    raise ValueError('SR table IDs or string count changed')
                for ordinal, ((_, jp), roles, actual) in enumerate(zip(source[1], source[2], strings)):
                    if 'sr' not in roles or not M.needs_text(jp):
                        continue
                    expected = L.encode(stage[jp], mapping)
                    if actual != expected:
                        raise ValueError('SR compiled literal differs from reviewed source')
                    sr_literals.append(dict(member=member, table=table_index, index=ordinal,
                                            source_sha256=sha256(jp.encode('cp932')),
                                            bytes=len(actual), rows=actual.count(b'\n')+1))
                if member not in (234, 280):
                    continue
                for phase_index, phase in enumerate(P.phases(compiled)):
                    for changed in (False, True):
                        records, steps = P.assemble(elf, strings, phase, None if changed else phase)
                        text = english(records['sr'])
                        if text != ['None']:
                            complete = ' '.join(text)
                            required = 'any damage.' if member == 234 else '6 or more enemies.'
                            if required not in complete or len(text) != 2:
                                raise ValueError('Reported SR requirement is incomplete')
                        reported.append(dict(member=member, phase=phase_index, changed=changed,
                                             english=text, native_steps=steps))
    print('All 101 SR conditions / 210 native panel cases, final drawer keys and compiled SR literals passed.', flush=True)
    from tools.verify_review30 import verify as previous
    prior = previous(version)
    shots = []
    for label, identifier in SHOTS:
        src = Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+identifier+'.png')
        dst = ROOT/'work/ui/screenshots'/('reported-review31-'+label+'.png')
        if not src.exists():
            src = dst
        shots.append(dict(issue=label, source=str(src), saved_path=str(dst), sha256=sha256_file(src), runtime_confirmation=False))
    return dict(schema=1, version=version, previous_public_version='0.5.28', prior_verification=prior,
                iso_verification=prior['iso_verification'], sr_panel_cases=cases, sr_archive_literals=sr_literals,
                reported_native_phases=reported, meaning_audit=audit, screenshots=shots, runtime_verified=False)


def main():
    from tools.game_build import VERSION
    ap = argparse.ArgumentParser(); ap.add_argument('--version', default=VERSION)
    ap.add_argument('--apply', action='store_true'); ap.add_argument('--preview', action='store_true'); a = ap.parse_args()
    if a.preview:
        print('Preview: all 101 SR conditions, 210 native four-row panels, compiled literals, reported phases, carried fixes and ISO. DRY RUN: no evidence written.'); return
    data = verify(a.version); print('ISO:', data['iso_verification']['sha256'])
    if not a.apply:
        print('DRY RUN: no evidence written.'); return
    for shot in data['screenshots']:
        dst = Path(shot['saved_path']); dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256_file(dst) != shot['sha256']:
            raise ValueError('SR screenshot differs')
        if Path(shot['source']) != dst:
            shutil.copyfile(shot['source'], dst)
    write_json(ROOT/'work/ui'/('review31_verified_'+a.version+'.json'), data)


if __name__ == '__main__':
    main()
