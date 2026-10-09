"""Compare Tengoku library (encyclopedia) entries with Jigoku's originals.

Read-only against both ISOs. Jigoku's three MTZKN archives are copied once from
its original ISO into ignored `work/jigoku_ref/`; Tengoku's come from the
verified extraction. Entries are paired by name within each archive, then by
identical description for renamed entries. Entry ids are not assumed to match.

The report stores ids, short names and statuses only, never descriptions. It
also says whether Jigoku already has an English description or name for the
paired entry, so reuse candidates can be reviewed; nothing is copied.

    python -m tools.library_compare            # dry run: print the summary
    python -m tools.library_compare --apply    # also write the JSON report
"""
import argparse
import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools.cpk import CPK
from tools.isoread import ISO9660
from tools.pipeline import config, verified_source
from tools.source_text import library_fields

JIGOKU_ISO = Path('E:/SRWZ3/iso/Dai-3-Ji Super Robot Taisen Z - Jigoku-hen (Japan).iso')
JIGOKU_PROJECT = Path('E:/Projects/SRW Z3')
MTDATA = '/PS3_GAME/USRDIR/COMMONDATA/MTDATA/'
KINDS = {'keyword': ('KW', 'WORD'), 'pilot': ('PT', 'CHFN'), 'robot': ('RT', 'RBTN')}
TEXT = ('DSCR', 'DSC2')
REFERENCE = ROOT / 'work/jigoku_ref'
REPORT = ROOT / 'work/glossary/library_jigoku_match.json'
# Original archive hashes, recorded on first extraction from the Jigoku ISO.
JIGOKU_SHA256 = {
    'MTZKN_KW.CPK': 'ad39edee49819d0bb1a4efec8a9eddabeff8983c2943273b15cc5ccf6b6ae54c',
    'MTZKN_PT.CPK': '091e10f8d59ca3727b6a4adcfa61e19a42c19d8b03f6a0e39e3ef8dffdebad08',
    'MTZKN_RT.CPK': '9eae9d66d8595a82c20bdf03f64ec8f6fe0923d3d598ad62bad7175c0e8afa65',
}


def jigoku_archive(name):
    path = REFERENCE / name
    if not path.exists():
        REFERENCE.mkdir(parents=True, exist_ok=True)
        with ISO9660(JIGOKU_ISO) as iso:
            entries = {p: e for p, e in iso.walk()}
            iso.copy(entries[MTDATA + name], path)
    if sha256_file(path) != JIGOKU_SHA256[name]:
        raise ValueError('Jigoku reference archive changed: %s' % path)
    return path


def records(path):
    archive = CPK(path)
    result = []
    for entry in archive.files:
        raw = archive.read(entry)
        data = bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in raw)
        _, fields = library_fields(raw)
        # Compare payload bytes so non-text fields (image/voice ids) count too.
        result.append({'id': entry['id'], 'fields': {
            f['tag']: data[f['offset']:f['offset'] + f['bytes']] for f in fields},
            'text': {f['tag']: f['text'] for f in fields}})
    return result


def name_key(text):
    return (text or '').strip().strip('「」').replace('\u3000', '').replace(' ', '')


def similarity(a, b):
    if a == b:
        return 1.0
    return round(SequenceMatcher(None, a or '', b or '', autojunk=False).ratio(), 3)


RENAME_THRESHOLD = 0.6


def score(a, b):
    # Same-name variants (e.g. several ELS robots) differ by pilot and text.
    same = sum(a['fields'].get(t) == b['fields'].get(t) for t in a['fields'])
    return (similarity(a['text'].get('DSCR'), b['text'].get('DSCR')), same, -abs(a['id'] - b['id']))


def assign(pairs, paired, used):
    """Greedy one-to-one assignment, best score first."""
    for s, t, j in sorted(pairs, key=lambda p: (p[0], -p[1]['id']), reverse=True):
        if t['id'] not in paired and j['id'] not in used:
            paired[t['id']], used[j['id']] = j, t['id']


def pair(tengoku, jigoku, name_tag):
    """Return {tengoku id: (jigoku record, method)}. Ids are never assumed equal."""
    by_name, by_text = defaultdict(list), defaultdict(list)
    for record in jigoku:
        by_name[name_key(record['text'][name_tag])].append(record)
        by_text[record['fields'].get('DSCR')].append(record)
    paired, used, methods = {}, {}, {}

    def stage(method, pairs):
        before = set(paired)
        assign(pairs, paired, used)
        methods.update({i: method for i in set(paired) - before})

    stage('name', [(score(t, j), t, j) for t in tengoku
                   for j in by_name.get(name_key(t['text'][name_tag]), [])])
    stage('description', [(score(t, j), t, j) for t in tengoku if t['id'] not in paired
                          for j in by_text.get(t['fields'].get('DSCR'), []) if j['id'] not in used])
    pairs = []
    for t in tengoku:
        if t['id'] in paired:
            continue
        for j in jigoku:
            if j['id'] in used:
                continue
            matcher = SequenceMatcher(None, t['text'].get('DSCR') or '', j['text'].get('DSCR') or '', autojunk=False)
            if matcher.quick_ratio() >= RENAME_THRESHOLD and matcher.ratio() >= RENAME_THRESHOLD:
                pairs.append((score(t, j), t, j))
    stage('similar_description', pairs)
    # Extra same-name Tengoku variants share the closest Jigoku entry.
    for t in tengoku:
        if t['id'] not in paired:
            options = by_name.get(name_key(t['text'][name_tag]), [])
            if options:
                paired[t['id']] = max(options, key=lambda j: score(t, j))
                methods[t['id']] = 'name_shared'
    return {i: (paired[i], methods[i]) for i in paired}


def compare(tengoku, jigoku, name_tag):
    """Pair entries of one archive and classify each Tengoku entry."""
    pairs = pair(tengoku, jigoku, name_tag)
    rows, used = [], Counter()
    for record in tengoku:
        if record['id'] not in pairs:
            rows.append({'tengoku_id': record['id'], 'status': 'new'})
            continue
        best, method = pairs[record['id']]
        used[best['id']] += 1
        ratios = {t: similarity(record['text'].get(t), best['text'].get(t)) for t in TEXT}
        differing = sorted(t for t in set(record['fields']) | set(best['fields'])
                           if record['fields'].get(t) != best['fields'].get(t))
        if not differing:
            status = 'identical'
        elif not set(differing) & set(TEXT):
            status = 'same_description'
        elif min(ratios.values()) >= 0.9:
            status = 'minor_edit'
        elif min(ratios.values()) >= 0.5:
            status = 'partly_rewritten'
        else:
            status = 'rewritten'
        rows.append({'tengoku_id': record['id'], 'jigoku_id': best['id'], 'status': status,
                     'matched_by': method, 'name_changed': name_tag in differing,
                     'differing_fields': differing,
                     'description_similarity': ratios['DSCR'], 'dsc2_similarity': ratios['DSC2']})
    jigoku_only = sorted(r['id'] for r in jigoku if r['id'] not in used)
    shared = sorted(i for i, n in used.items() if n > 1)
    # Hints only: a title or family name added/dropped (法皇テオ８世 -> テオ８世)
    # looks the same as unrelated names (プラント / インプラント). Review by hand.
    names = {r['id']: name_key(r['text'][name_tag]) for r in jigoku}
    for row, record in zip(rows, tengoku):
        a = name_key(record['text'][name_tag])
        if row['status'] == 'new' and len(a) >= 3:
            hints = [i for i in jigoku_only if len(names[i]) >= 3 and (a in names[i] or names[i] in a)]
            if hints:
                row['review_partial_name_jigoku_ids'] = hints
    return rows, jigoku_only, shared


def jigoku_english(kind, name_tag):
    """Jigoku English descriptions (by entry id) and names (by glossary zukan id)."""
    descriptions = set()
    for path in sorted((JIGOKU_PROJECT / 'translation/library').glob(KINDS[kind][0].lower() + '_*.json')):
        descriptions |= {int(k) for k in json.loads(path.read_text(encoding='utf-8')).get('ENTRIES', {})}
    glossary = json.loads((ROOT / 'work/glossary/reference/jigoku_glossary.json').read_text(encoding='utf-8'))
    names = {t['zukan_id']: t['en'] for t in glossary['terms']
             if t.get('kind') == kind and t.get('field') == name_tag and t.get('zukan_id') is not None and t['en']}
    return descriptions, names


def run():
    settings = config(ROOT / 'config/tengoku.json')
    report = {'schema': 1, 'purpose': 'Tengoku vs Jigoku library pairing; ids, names and statuses only',
              'jigoku_iso': str(JIGOKU_ISO), 'jigoku_english_source': str(JIGOKU_PROJECT / 'translation/library'),
              'identities_reviewed': False, 'archives': {}}
    for kind, (code, name_tag) in KINDS.items():
        name = 'MTZKN_%s.CPK' % code
        tengoku_path = verified_source(settings, MTDATA + name)
        jigoku_path = jigoku_archive(name)
        tengoku, jigoku = records(tengoku_path), records(jigoku_path)
        rows, jigoku_only, shared = compare(tengoku, jigoku, name_tag)
        descriptions, names = jigoku_english(kind, name_tag)
        tengoku_names = {r['id']: r['text'][name_tag] for r in tengoku}
        jigoku_names = {r['id']: r['text'][name_tag] for r in jigoku}
        for row in rows:
            row['name_jp'] = tengoku_names[row['tengoku_id']]
            if 'jigoku_id' in row:
                row['jigoku_english_name'] = names.get(row['jigoku_id'])
                row['jigoku_english_description'] = row['jigoku_id'] in descriptions
        report['archives'][kind] = {
            'tengoku_sha256': sha256_file(tengoku_path), 'jigoku_sha256': JIGOKU_SHA256[name],
            'tengoku_entries': len(tengoku), 'jigoku_entries': len(jigoku),
            'status_counts': dict(Counter(r['status'] for r in rows)),
            'jigoku_only': [{'jigoku_id': i, 'name_jp': jigoku_names[i]} for i in jigoku_only],
            'jigoku_entries_paired_more_than_once': shared,
            'entries': rows}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report = run()
    for kind, archive in report['archives'].items():
        english = sum(1 for r in archive['entries'] if r.get('jigoku_english_description'))
        print('%-8s Tengoku %3d / Jigoku %3d  %s  Jigoku-only %d  with Jigoku English %d' % (
            kind, archive['tengoku_entries'], archive['jigoku_entries'],
            json.dumps(archive['status_counts'], sort_keys=True), len(archive['jigoku_only']), english))
    if args.apply:
        write_json(REPORT, report)
        print('Wrote ' + str(REPORT))
    else:
        print('DRY RUN: no report written')


if __name__ == '__main__':
    main()
