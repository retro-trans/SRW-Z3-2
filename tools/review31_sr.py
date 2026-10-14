"""Fit the six overflowing SR explanations without changing their requirements."""
import argparse, json, re
from tools.common import ROOT, sha256, write_json
from tools import mission_text as M, mission_display as D, library_build as L

DEST = ROOT/'work/ui/review31_sr_audit.json'
EDITS = (
    (375, '2e842c709c6ec6409a3746eaf360778c4b86abdd215757d20a0539554293a1f5',
     'd06dd4da5b5d3f511769db6da36196a4bac9bb1f8fcfa9b2f9b08f1891e923a6',
     'Shoot down the $$巨大円盤$$ in one attack (Attack/Maximum Break/Counter).\n'
     'Support Attacks may join it. Songs count as attacks.\n'
     'Guarding or evading its attack does not count as an attack.'),
    (554, 'b8053eef6cae48f466a846c5e5a8f77d7ce852856551b0c8c30d17e9c1474242',
     '9dff746a83205a8e10f3de5163acf7a2f2204676bf814e086a8aa2a0e0499968',
     'Shoot down either Angel in one attack (Attack/Maximum Break/Counter).\n'
     'Support Attacks may join it. Songs count as attacks.\n'
     "Guarding or evading an Angel's attack does not count as an attack."),
    (590, 'a087a60ed6200b3c5caf01032acdcd5d961200d4bc9c5b2e7f015fbf10277f29',
     '0b291ffce0e2a6502179d1ef873bd87959ae68f4e81a3a540ea7daff942d3ea9',
     'Within 3 turns, meet all 3 conditions in the same turn.\n'
     '1. Reach Tactical Combo MAX.\n2. Shoot down 20 or more enemies that turn.\n'
     '3. Shoot down $$ジェミニア#robot$$.'),
    (590, 'be692ba6340b58c775e041dcd26be70cc9bef0080099d2ad11475780ffde4b20',
     'cb07cc6a16a35184bc0faf160c583c47ff2292d5d55dae1bcfac8eedbd112a93',
     'Within 3 turns, meet all 3 conditions in the same turn.\n'
     '1. Reach Tactical Combo MAX.\n2. Shoot down 20 or more enemies that turn.\n'
     '3. Shoot down $$ジェミニア#robot$$ (void if $$ＥＬＳ#keyword$$ shoot it down or erode it).'),
    (608, '7a6dfe82cb5f6c259f27f2b5bf50081b0341e44adf7269fa64ab439b4024b691',
     'f0d4932b3c41ce52cc7497ebec49eaeccc1d63e676a41742f53e44c83df96087',
     'Defeat all enemies within 6 turns; before clearing, also:\n'
     '1. Reach Tactical Combo MAX.\n2. One allied pilot must shoot down 5 or more enemies.\n'
     '3. Shoot down 16 or more enemies in one turn.'),
    (855, '8fb7779aa1be96dff1da31030eec633881c85ea11bb8176752b5d25ab597d1c1',
     'b5a95d7cd261f861f0caaeafe5a5a8686972d65ddb124232c10ea2b85b727c9e',
     'Defeat all enemies within 4 turns.\n'
     '(Meeting the condition written here earns an SR Point.\n'
     'Each SR Point earned gives you 10000 bonus funds,\n'
     "but reaching a set SR Point total increases the game's difficulty.)"),
)


def plan():
    data = M.load(); items = M.inventory(); resolver = M.resolver()
    sources = {sha256(jp.encode('cp932')): jp for jp in items}
    outputs, changes = {}, []
    answers = {p: json.loads(p.read_text('utf8')) for p in sorted(M.NEW.glob('*.json'))}
    for member, fingerprint, old_en_sha, english in EDITS:
        jp = sources[fingerprint]
        if items[jp]['members'] != [member] or items[jp]['roles'] != {'sr'}:
            raise ValueError('SR source identity changed')
        old = data['strings'][jp]['en']
        if old != english and sha256(old.encode('utf8')) != old_en_sha:
            raise ValueError('Reviewed SR wording changed')
        errors = []; M.validate(fingerprint, jp, english, resolver, errors)
        if errors:
            raise ValueError(errors)
        expanded = L.expand(english, resolver)
        lines = M.wrap(expanded, D.advance, M.LINE_UNITS-64).split('\n')
        if len(lines) > 4:
            raise ValueError('Reviewed SR wording exceeds its four-row slot')
        record = dict(member=member, source_sha256=fingerprint, previous_english_sha256=old_en_sha,
                      english=expanded, rows=len(lines), lines=lines,
                      maximum_line_units=max(sum(map(D.advance, line)) for line in lines))
        changes.append(record)
        if old != english:
            data['strings'][jp]['en'] = english; outputs[M.TRANSLATION] = data
        matched = 0
        for path, answer in answers.items():
            key = M.key(jp)
            if key not in answer.get('rows', {}):
                continue
            matched += 1; old_answer = answer['rows'][key]['en']
            if old_answer != english:
                if sha256(old_answer.encode('utf8')) != old_en_sha:
                    raise ValueError('SR answer copy changed')
                answer['rows'][key]['en'] = english; outputs[path] = answer
        if matched != 1:
            raise ValueError('Expected one synchronized SR answer copy')
    audit = dict(schema=1, version='0.5.31', assigned_conditions=6, source_rows_examined=29,
                 meaning_reviewer='review29_live_conditions', changes=changes, runtime_verified=False,
                 reported_conditions=dict(assigned_conditions=2, source_rows_examined=9, meaning_changes=0,
                     episode20='Defeat all enemies within 3 turns without any allied battleship taking damage.',
                     episode21='One allied pilot must shoot down at least 6 enemies before clearing the map.'))
    return audit, outputs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
    audit, outputs = plan()
    for row in audit['changes']:
        print('Member', row['member'], row['rows'], 'rows:', '\n'.join(row['lines']))
    print('Translation files changed:', len(outputs))
    if not a.apply:
        print('DRY RUN: no translation or audit files written.'); return
    for path, data in outputs.items():
        old = path.read_bytes()
        indent = len(re.search(rb'\n( +)"', old)[1])
        newline = '\r\n' if b'\r\n' in old else '\n'
        text = json.dumps(data, ensure_ascii=False, indent=indent)+'\n'
        path.write_bytes(text.replace('\n', newline).encode('utf8'))
    write_json(DEST, audit)


if __name__ == '__main__':
    main()
