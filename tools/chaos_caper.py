"""Preview/apply the user's Chaos Caper spelling and verify both compiled references."""
import argparse
import copy
import json

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import dialogue as D, dialogue_build as DB, dialogue_layout as DL
from tools import library_text as LT
from tools.cpk import CPK

TOKEN = 'カオス・カペル'
OLD, NEW = 'Chaos Kapel', 'Chaos Caper'
PARENT = ROOT / 'work/output/builds/0.5.44'


def plan():
    changes = []
    for name in ('library_terms.json', 'library_settled.json'):
        path = ROOT / 'work/glossary' / name
        data = json.loads(path.read_text('utf8'))
        rows = [r for r in data['terms'] if r.get('token', r['jp']) == TOKEN]
        if len(rows) != 1 or rows[0]['en'] not in (OLD, NEW):
            raise ValueError('Unexpected glossary spelling or alias count: ' + name)
        row = rows[0]
        if row['en'] == OLD:
            old_source = row['source']
            row.update(en=NEW, status='confirmed',
                source='User correction 2026-10-16: Chaos Caper. Preserve this spelling during proofreading.')
            raw = path.read_text('utf8')
            updated = raw.replace('"en": "' + OLD + '"', '"en": "' + NEW + '"')
            updated = updated.replace('"source": "' + old_source + '"',
                                      '"source": "' + row['source'] + '"')
            # Restrict status replacement to this exact parsed entry.
            if name == 'library_terms.json':
                before = '"en": "' + NEW + '",\n      "status": "proposed"'
                after = '"en": "' + NEW + '",\n      "status": "confirmed"'
            else:
                before = '"en": "' + NEW + '", "status": "proposed"'
                after = '"en": "' + NEW + '", "status": "confirmed"'
            updated = updated.replace(before, after)
            if json.loads(updated) != data:
                raise ValueError('Text edit differs from the scoped glossary change')
            changes.append((path, updated))
    return changes


def verify(changes):
    glossary = next((json.loads(text) for path, text in changes if path.name == 'library_terms.json'),
                    json.loads(LT.GLOSSARY.read_text('utf8')))
    terms = glossary['terms']
    if next(t for t in terms if t.get('token') == TOKEN)['en'] != NEW:
        raise ValueError('Canonical term did not change')
    before = copy.deepcopy(terms)
    next(t for t in before if t.get('token') == TOKEN)['en'] = OLD
    resolver, old_resolver = LT.Resolver(terms), LT.Resolver(before)
    active = DB.translations()
    affected = {rid for rid, row in active.items() if '$$' + TOKEN + '$$' in row['en']}
    if affected != {'611:t_016:2', '688:t_3:67'}:
        raise ValueError('Dialogue reference inventory changed')
    b = json.loads((PARENT / 'build.json').read_text('utf8'))
    width = lambda c: b['widths'].get(c, 32)
    references, compiled = [], []
    with CPK(PARENT / 'STGZ3OF2.cpk') as archive:
        for mid in sorted({int(rid.split(':')[0]) for rid in affected}):
            previous, updated = {}, {}
            for record in D.records(mid):
                rid = record['id']
                if rid not in active:
                    continue
                entry = active[rid]
                if entry['sha'] != record['sha']:
                    raise ValueError('Dialogue fingerprint changed: ' + rid)
                old = previous[rid] = DB.render(entry, record, old_resolver, width)
                new = updated[rid] = DB.render(entry, record, resolver, width)
                if rid not in affected:
                    if new != old:
                        raise ValueError('Unrelated dialogue changed: ' + rid)
                    continue
                if ' '.join(new.split()) != ' '.join(old.replace(OLD, NEW).split()):
                    raise ValueError('Change exceeds the requested name')
                if len(new.split('\n')) > 4:
                    raise ValueError('Corrected dialogue exceeds its three-line box')
                if sorted(D.CODES.findall(new)) != sorted(D.CODES.findall(record['jp'])):
                    raise ValueError('Control codes changed')
                if (new.count('《'), new.count('》')) != (record['jp'].count('《'), record['jp'].count('》')):
                    raise ValueError('Keyword link counts changed')
                widths = [D.speech_units(line, lambda c: 0 if c in DB.LINK_MARKS else width(c))
                          for line in new.split('\n')[1:]]
                if max(widths) > D.BOX_UNITS:
                    raise ValueError('Corrected dialogue row is too wide')
                references.append(dict(id=rid, english=new, speech_widths=widths))
            old = DB.rebuild_member(mid, previous, b['mapping'])
            parent = archive.read(next(r for r in archive.files if r['id'] == mid))
            if old != parent:
                raise ValueError('Source differs from public 0.5.44 beyond this correction')
            new = DB.rebuild_member(mid, updated, b['mapping'])
            for rid in affected & updated.keys():
                if DB.encode(updated[rid], DL.mapping_for(rid, b['mapping'])) not in new:
                    raise ValueError('Corrected encoded record is missing')
            compiled.append(dict(member=mid, parent_sha256=sha256(old), corrected_sha256=sha256(new)))
    return dict(schema=1, correction=NEW, previous_spelling=OLD, parent_version='0.5.44',
        parent_build_sha256=sha256_file(PARENT / 'build.json'), references=references,
        compiled_members=compiled, controls_links_and_unrelated_records_preserved=True,
        publication='source_correction_pending_next_build', runtime_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    changes = plan()
    evidence = verify(changes)
    for path, _ in changes:
        print(str(path.relative_to(ROOT)), OLD, '->', NEW, '(confirmed)')
    for row in evidence['references']:
        print(row['id'], row['english'], 'widths:', row['speech_widths'])
    if not args.apply:
        print('DRY RUN: no files written; both corrected stage members compile and parent contents match.')
        return
    for path, text in changes:
        with path.open('w', encoding='utf8', newline='\n') as stream:
            stream.write(text)
    write_json(ROOT / 'work/ui/chaos_caper_correction.json', evidence)
    print('Glossaries corrected; compiled-reference evidence recorded. No release created.')


if __name__ == '__main__':
    main()
