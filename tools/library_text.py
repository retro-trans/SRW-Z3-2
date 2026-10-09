"""Tengoku library (encyclopedia) translation: glossary, reuse, briefs, checks.

Names are glossary terms bound to Tengoku library fields; prose refers to a
term as `$$<token>$$` (optionally `$$<token>|lc$$`) and the build expands it,
as in Jigoku (see its docs/TRANSLATING.md "The key is the Japanese").

    python -m tools.library_text seed    [--apply]  # glossary + Jigoku reuse
    python -m tools.library_text export  [--apply]  # translator briefs
    python -m tools.library_text check              # validate translations
    python -m tools.library_text names              # proposals to settle

`seed` writes `work/glossary/library_terms.json` and one `<kind>_reuse.json`
per archive: descriptions whose Japanese is unchanged from Jigoku keep
Jigoku's English. Everything else is translated from briefs into
`work/translation/en/library/<kind>_<first id>.json`. Translation files hold
English and source hashes only; the Japanese stays in the ignored briefs.
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from tools.common import ROOT, sha256, write_json
from tools import library_compare as lc
from tools.pipeline import config, verified_source

GLOSSARY = ROOT / 'work/glossary/library_terms.json'
TRANSLATIONS = ROOT / 'work/translation/en/library'
BRIEFS = ROOT / 'work/tengoku/library_briefs'
SOURCES = ROOT / 'work/glossary/reference/sources'
JIGOKU_GLOSSARY = ROOT / 'work/glossary/reference/jigoku_glossary.json'
# Orchestrator-researched names, each with its source; applied after seeding.
SETTLED = ROOT / 'work/glossary/library_settled.json'
# Per-group name research (names and character profiles), merged after SETTLED.
RESEARCH = ROOT / 'work/glossary/research'
RESEARCH_BRIEFS = ROOT / 'work/tengoku/name_research'
CHARACTERS = ROOT / 'work/glossary/library_characters.json'
PREFIX = {'keyword': 'kw', 'pilot': 'pt', 'robot': 'rt'}
NAME_FIELDS = {'keyword': ('WORD',), 'pilot': ('CHFN', 'CHNN'), 'robot': ('RBTN', 'RBN2')}
SERIES_FIELD = {'keyword': 'SRCE', 'pilot': 'PRDC', 'robot': 'PRDC'}
BATCH = {'keyword': 20, 'pilot': 40, 'robot': 40}
TOKEN = re.compile(r'\$\$([^$|]+)(\|lc)?\$\$')
REUSABLE = ('identical', 'same_description')


def placeholder(text):
    return not text or set(text) <= set('－-ー　 ')


def normal(text):
    return unicodedata.normalize('NFKC', text or '').replace(' ', '').strip('「」')


def load_library():
    """{kind: (tengoku records by id, jigoku records by id, report rows by tengoku id)}"""
    settings = config(ROOT / 'config/tengoku.json')
    report = json.loads(lc.REPORT.read_text(encoding='utf-8'))
    result = {}
    for kind, (code, _) in lc.KINDS.items():
        name = 'MTZKN_%s.CPK' % code
        tengoku = {r['id']: r for r in lc.records(verified_source(settings, lc.MTDATA + name))}
        jigoku = {r['id']: r for r in lc.records(lc.jigoku_archive(name))}
        rows = {r['tengoku_id']: r for r in report['archives'][kind]['entries']}
        if set(rows) != set(tengoku):
            raise ValueError('match report is stale for ' + kind)
        result[kind] = (tengoku, jigoku, rows)
    return result


def source_hashes(record):
    return {t: sha256(record['fields'][t]) for t in lc.TEXT}


def akurasu_table(path, jp_column, en_column):
    table = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        cells = [c.strip() for c in line.strip().lstrip('|').split('||')]
        if len(cells) > max(jp_column, en_column) and line.startswith('|') and not line.startswith('|-'):
            en = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', cells[en_column]).strip()
            jp = cells[jp_column]
            if jp and en and re.search(r'[぀-ヿ一-鿿]', jp):
                table.setdefault(normal(jp), set()).add(en)
    return table


# ----------------------------------------------------------------- glossary

def seed_terms(library):
    jigoku_terms = json.loads(JIGOKU_GLOSSARY.read_text(encoding='utf-8'))['terms']
    by_slot = {(t['kind'], t['zukan_id'], t['field']): t for t in jigoku_terms if t.get('zukan_id') is not None}
    by_jp = defaultdict(list)
    for t in jigoku_terms:
        by_jp[(t['kind'], t['jp'])].append(t)
    mechs = akurasu_table(SOURCES / 'akurasu_z3.2_mech_list.wiki', 2, 1)
    series = akurasu_table(SOURCES / 'akurasu_z3.2_series.wiki', 1, 2)

    # One occurrence per Tengoku name field; English decided per occurrence.
    occurrences = []
    for kind, (tengoku, jigoku, rows) in library.items():
        for tid, record in sorted(tengoku.items()):
            row = rows[tid]
            fields = [(f, kind) for f in NAME_FIELDS[kind]] + [(SERIES_FIELD[kind], 'series')]
            for field, term_kind in fields:
                jp = (record['text'][field] or '').strip()
                if term_kind == 'series':
                    jp = jp.strip('「」')
                if placeholder(jp):
                    continue
                en, status, source = None, 'pending', None
                jid = row.get('jigoku_id')
                inherited = by_slot.get((kind, jid, field)) if term_kind != 'series' else None
                if inherited and inherited['jp'] == jp and inherited['en']:
                    en, status, source = inherited['en'], inherited['status'], 'jigoku_glossary:%s:%s:%s' % (kind, jid, field)
                elif len({t['en'] for t in by_jp.get((term_kind, jp), []) if t['en']}) == 1:
                    t = by_jp[(term_kind, jp)][0]
                    en, status, source = t['en'], t['status'], 'jigoku_glossary_by_name'
                if term_kind == 'series' and len(series.get(normal(jp), ())) == 1:
                    wiki = next(iter(series[normal(jp)]))
                    # The user's own corrections ('confirmed') outrank the wiki.
                    if en is None or status not in ('official', 'confirmed'):
                        en, status, source = wiki, 'official', 'akurasu_z3.2_series'
                if term_kind == 'robot' and en is None and len(mechs.get(normal(jp), ())) == 1:
                    en, status, source = next(iter(mechs[normal(jp)])), 'official', 'akurasu_z3.2_mech_list'
                occurrences.append({'jp': jp, 'kind': term_kind, 'en': en, 'status': status, 'source': source,
                                    'target': {'archive': kind, 'tengoku_id': tid, 'field': field}})

    # Merge occurrences that agree; different English for one name = different terms.
    grouped = defaultdict(list)
    for o in occurrences:
        grouped[(o['kind'], o['jp'])].append(o)
    terms = []
    for (kind, jp), items in sorted(grouped.items()):
        english = {o['en'] for o in items if o['en']}
        entries = {o['target']['tengoku_id'] for o in items}
        # Same English is not same person: Jigoku marks ドロシー 'ambiguous'
        # because Dorothy Catalonia and R. Dorothy Waynewright share it.
        if len(english) > 1 or (len(entries) > 1 and any(o['status'] == 'ambiguous' for o in items)):
            for o in items:
                terms.append(term(jp, kind, o['en'], 'ambiguous', o['source'], [o['target']]))
        else:
            known = [o for o in items if o['en']]
            best = known[0] if known else items[0]
            terms.append(term(jp, kind, best['en'], best['status'], best['source'], [o['target'] for o in items]))
    return terms, by_jp


def settled_records():
    """SETTLED first, then researched files; a later file never beats an earlier one."""
    files = ([SETTLED] if SETTLED.exists() else []) + sorted(RESEARCH.glob('*.json'))
    for path in files:
        data = json.loads(path.read_text(encoding='utf-8'))
        for s in data.get('terms', []) + data.get('names', []):
            yield path.name, s


def apply_settled(terms, report=None):
    """Apply researched decisions. A user-confirmed term is never overridden, and
    an official one only when the orchestrator approved it (`override_approved`)."""
    seen = set()
    for origin, s in settled_records():
        key = (s['jp'], s['kind'], json.dumps(s.get('target'), sort_keys=True), s.get('token'))
        if key in seen or not s.get('en'):
            continue
        seen.add(key)
        if s.get('token') and not s.get('target'):
            # An explicit token names one term, whatever kind the record says.
            matches = [t for t in terms if t.get('token') == s['token']]
        else:
            # A record without a token never touches a researched variant
            # (地球連邦 must not overwrite 地球連邦#awgx).
            matches = [t for t in terms if t['jp'] == s['jp'] and t['kind'] == s['kind']
                       and not t.get('researched_token')
                       and (s.get('target') is None or s['target'] in t['targets'])]
        for t in matches:
            if t['en'] == s['en'] and t['status'] in ('confirmed', 'official'):
                t.setdefault('profile', s.get('profile'))
                continue
            # `user_approved`: the user explicitly decided to change a confirmed term (record why in source).
            if (t['status'] == 'confirmed' and not s.get('user_approved')) or \
                    (t['status'] == 'official' and not s.get('override_approved')):
                if report is not None:
                    report.append('%s: %s %r stays %r (%s)' % (origin, s['jp'], s['en'], t['en'], t['status']))
                continue
            t.update(en=s['en'], status=s['status'], source=s['source'])
            if s.get('profile'):
                t['profile'] = s['profile']
        if not matches:
            t = term(s['jp'], s['kind'], s['en'], s['status'], s['source'], [])
            if s.get('token'):
                t['token'], t['researched_token'] = s['token'], True
            if s.get('profile'):
                t['profile'] = s['profile']
            terms.append(t)


def collect_characters(library, terms):
    """Profiles by pilot entry id from the research files, with the entry's name tokens."""
    by_target = {(tg['archive'], tg['tengoku_id'], tg['field']): t for t in terms for tg in t['targets']}
    result = {}
    for path in sorted(RESEARCH.glob('*.json')):
        for c in json.loads(path.read_text(encoding='utf-8')).get('characters', []):
            pid = c.get('pilot_id')
            if pid in library['pilot'][0] and str(pid) not in result:
                names = {f: by_target[('pilot', pid, f)]['token'] for f in NAME_FIELDS['pilot']
                         if ('pilot', pid, f) in by_target}
                result[str(pid)] = dict(c, tokens=names, research=path.name)
    return result


def term(jp, kind, en, status, source, targets):
    return {'jp': jp, 'kind': kind, 'en': en, 'status': status if en else 'pending',
            'source': source, 'targets': targets}


def assign_tokens(terms):
    by_jp = defaultdict(list)
    for t in terms:
        by_jp[t['jp']].append(t)
    for jp, items in by_jp.items():
        # A researched variant (地球連邦#00) must not take the plain token
        # away from the general term, so only automatic terms compete.
        items = [t for t in items if not t.get('researched_token')]
        kinds = Counter(t['kind'] for t in items)
        for t in items:
            if t.get('token'):
                continue
            if len(items) == 1:
                t['token'] = jp
            elif kinds[t['kind']] == 1:
                t['token'] = jp + '#' + t['kind']
            else:
                target = t['targets'][0] if t['targets'] else None
                t['token'] = '%s#%s%s' % (jp, PREFIX[target['archive']], target['tengoku_id']) if target else jp + '#' + t['kind']
    tokens = Counter(t['token'] for t in terms)
    duplicate = [k for k, n in tokens.items() if n > 1]
    if duplicate:
        raise ValueError('duplicate glossary tokens: %s' % duplicate[:5])
    return terms


class Resolver:
    def __init__(self, terms):
        self.token = {t['token']: t for t in terms}
        self.bare = defaultdict(list)
        for t in terms:
            self.bare[t['jp']].append(t)

    def resolve(self, name):
        if name in self.token:
            return self.token[name], None
        items = self.bare.get(name, [])
        if len(items) == 1:
            return items[0], None
        if items:
            return None, "'%s' is ambiguous; use one of %s" % (name, ', '.join('$$%s$$' % t['token'] for t in items))
        return None, "'%s' is not in the library glossary" % name


# -------------------------------------------------------------------- reuse

def jigoku_english(kind):
    entries = {}
    for path in sorted((lc.JIGOKU_PROJECT / 'translation/library').glob(PREFIX[kind] + '_*.json')):
        for key, value in json.loads(path.read_text(encoding='utf-8'))['ENTRIES'].items():
            entries[int(key)] = value if isinstance(value, dict) else {'DSCR': value}
    return entries


def remap_tokens(text, jigoku_by_jp, library, terms_by_target, resolver):
    """Rewrite Jigoku tokens so each still means what it meant in Jigoku.

    `$$jp#<jigoku id>$$` becomes the Tengoku term for that entry. A bare token
    that Tengoku made ambiguous (アイム is now a keyword and a pilot) takes the
    kind Jigoku's glossary gave it, when that kind is unique there.
    """
    def replace(match):
        name, suffix = match.group(1), match.group(2) or ''
        jp, _, disc = name.partition('#')
        if not disc:
            if resolver.resolve(jp)[0]:
                return match.group(0)
            kinds = {k for (k, term_jp), items in jigoku_by_jp.items() if term_jp == jp and items}
            options = [t for t in resolver.bare.get(jp, []) if t['kind'] in kinds]
            if len(kinds) == 1 and len(options) == 1:
                return '$$%s%s$$' % (options[0]['token'], suffix)
            return match.group(0)
        if not disc.isdigit():
            return match.group(0)
        for (kind, term_jp), items in jigoku_by_jp.items():
            if term_jp == jp and any(t.get('zukan_id') == int(disc) for t in items) and kind in library:
                rows = library[kind][2]
                tid = next((r['tengoku_id'] for r in rows.values() if r.get('jigoku_id') == int(disc)), None)
                t = terms_by_target.get((kind, tid, jp))
                if t:
                    return '$$%s%s$$' % (t['token'], suffix)
        raise ValueError('cannot remap Jigoku token ' + match.group(0))
    return TOKEN.sub(replace, text)


def seed(apply):
    library = load_library()
    terms, jigoku_by_jp = seed_terms(library)
    by_target = {}
    for t in terms:
        for target in t['targets']:
            by_target[(target['archive'], target['tengoku_id'], t['jp'])] = t

    sources, prose_terms = {}, set()
    for kind, (tengoku, jigoku, rows) in library.items():
        english = jigoku_english(kind)
        for tid, row in sorted(rows.items()):
            if row['status'] not in REUSABLE:
                continue
            jid, record = row['jigoku_id'], tengoku[tid]
            source = english.get(jid, {})
            needs_dsc2 = record['fields']['DSC2'] != record['fields']['DSCR']
            if not source.get('DSCR') or (needs_dsc2 and not source.get('DSC2')):
                continue
            sources[(kind, tid)] = (jid, source['DSCR'], source['DSC2'] if needs_dsc2 else None)
            for text in (source['DSCR'], source.get('DSC2') or ''):
                prose_terms |= {m.group(1).partition('#')[0] for m in TOKEN.finditer(text)}

    # Prose may name things with no Tengoku library field (Jigoku-only people,
    # Sphere names): inherit every other Jigoku term unbound, one per (kind, jp).
    known = {t['jp'] for t in terms}
    for (kind, jp), items in sorted(jigoku_by_jp.items()):
        english = {t['en'] for t in items if t['en']}
        if jp in known or len(english) != 1:
            continue
        terms.append(term(jp, kind, english.pop(), items[0]['status'], 'jigoku_glossary_unbound', []))
    known = {t['jp'] for t in terms}
    for name in sorted(prose_terms - known):
        terms.append(term(name, 'term', None, 'pending', None, []))
    # Tokens first, so research records that name a token (シンヤ#keyword)
    # update that term instead of adding a duplicate; then token any new terms.
    assign_tokens(terms)
    apply_settled(terms)
    assign_tokens(terms)

    reuse, resolver = {kind: {} for kind in library}, Resolver(terms)
    for (kind, tid), (jid, dscr, dsc2) in sorted(sources.items()):
        reuse[kind][str(tid)] = {
            'source_sha256': source_hashes(library[kind][0][tid]), 'origin': 'jigoku_reuse:%d' % jid,
            'DSCR': remap_tokens(dscr, jigoku_by_jp, library, by_target, resolver),
            'DSC2': remap_tokens(dsc2, jigoku_by_jp, library, by_target, resolver) if dsc2 else None}

    counts = Counter((t['kind'], t['status']) for t in terms)
    print('glossary terms: %d' % len(terms))
    for kind in ('keyword', 'pilot', 'robot', 'series', 'term'):
        row = {s: n for (k, s), n in counts.items() if k == kind}
        if row:
            print('  %-8s %s' % (kind, json.dumps(row, sort_keys=True)))
    for kind, files in reuse.items():
        print('reuse %-8s %d entries' % (kind, len(files)))
    sample = next(iter(reuse['pilot'].values()))
    print('sample reuse entry: ' + json.dumps(sample, ensure_ascii=False)[:300])
    blocked = []
    apply_settled(terms, blocked)  # second pass only to collect the review list
    for line in blocked:
        print('REVIEW ' + line)
    characters = collect_characters(library, terms)
    print('character profiles: %d / %d pilot entries' % (len(characters), len(library['pilot'][0])))
    if apply:
        write_json(CHARACTERS, {'schema': 1, 'purpose': 'Researched pilot profiles (BASE_RULES ground work)',
                                'characters': characters})
        write_json(GLOSSARY, {'schema': 1, 'purpose': 'Tengoku library names and prose terms',
                              'token_syntax': '$$<token>$$ or $$<token>|lc$$; bare Japanese resolves when unique',
                              'statuses': 'official (akurasu/Jigoku verified), proposed, ambiguous (decide per entry), pending (needs research)',
                              'terms': terms})
        for kind, files in reuse.items():
            # Reuse files are edited after seeding (retoken, proofreading), so
            # only missing entries are added; an existing entry is never reset.
            path = TRANSLATIONS / ('%s_reuse.json' % PREFIX[kind])
            existing = json.loads(path.read_text(encoding='utf-8'))['entries'] if path.exists() else {}
            merged = dict(files, **existing)
            write_json(path, {'schema': 1, 'kind': kind, 'entries': merged})
        print('Wrote ' + str(GLOSSARY) + ' and reuse files')
    else:
        print('DRY RUN: no files written')


# ------------------------------------------------------------ translations

def load_translations():
    entries, errors = {kind: {} for kind in PREFIX}, []
    for path in sorted(TRANSLATIONS.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        kind = data.get('kind')
        if kind not in PREFIX or not path.name.startswith(PREFIX[kind] + '_'):
            errors.append('%s: kind/file name mismatch' % path.name)
            continue
        for key, entry in data.get('entries', {}).items():
            if key in entries[kind]:
                errors.append('%s: %s %s already defined in %s' % (path.name, kind, key, entries[kind][key][0]))
            entries[kind][key] = (path.name, entry)
    return entries, errors


def check_entry(where, entry, record, resolver):
    """Return (errors, tokens whose term has no English yet, names not in the glossary)."""
    errors, pending, missing = [], set(), set()
    hashes = source_hashes(record)
    if entry.get('source_sha256') != hashes:
        errors.append(where + ': Japanese source changed (source_sha256 mismatch)')
    needs_dsc2 = record['fields']['DSC2'] != record['fields']['DSCR']
    if not isinstance(entry.get('DSCR'), str) or not entry['DSCR'].strip():
        errors.append(where + ': DSCR missing')
    if needs_dsc2 != isinstance(entry.get('DSC2'), str):
        errors.append(where + (': DSC2 required (Japanese DSC2 differs)' if needs_dsc2 else ': DSC2 must be null (same as DSCR)'))
    for field in lc.TEXT:
        text = entry.get(field)
        if not isinstance(text, str):
            continue
        bare = TOKEN.sub('', text)
        if '$$' in bare:
            errors.append('%s %s: malformed $$ token' % (where, field))
        odd = sorted({c for c in bare if ord(c) > 126 or (ord(c) < 32 and c != '\n')})
        if odd:
            errors.append('%s %s: non-ASCII %s' % (where, field, ''.join(odd)[:10]))
        for m in TOKEN.finditer(text):
            t, problem = resolver.resolve(m.group(1))
            if problem and 'not in the library glossary' in problem:
                missing.add(m.group(1))
            elif problem:
                errors.append('%s %s: %s' % (where, field, problem))
            elif not t['en']:
                pending.add(t['token'])
    return errors, pending, missing


def check(only=None):
    """Validate translation files. Missing names are research work, not errors."""
    library = load_library()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    entries, errors = load_translations()
    pending, missing = set(), set()
    for kind, (tengoku, _, _) in library.items():
        done = entries[kind]
        for key, (name, entry) in sorted(done.items(), key=lambda x: int(x[0]) if x[0].isdigit() else -1):
            if only and name != only:
                continue
            if not key.isdigit() or int(key) not in tengoku:
                errors.append('%s: unknown %s id %s' % (name, kind, key))
                continue
            e, p, m = check_entry('%s %s %s' % (name, kind, key), entry, tengoku[int(key)], resolver)
            errors += e
            pending |= p
            missing |= m
        print('%-8s translated %3d / %3d' % (kind, len(done), len(tengoku)))
    name_terms = [t for t in terms if t['targets']]
    print('names with English: %d / %d; referenced terms pending English: %d' % (
        sum(1 for t in name_terms if t['en']), len(name_terms), len(pending)))
    if missing:
        print('names not in the glossary (%d): %s' % (len(missing), ', '.join(sorted(missing))))
    for e in errors[:40]:
        print('ERROR ' + e)
    if len(errors) > 40:
        print('... %d more errors' % (len(errors) - 40))
    print('OK' if not errors else '%d errors' % len(errors))
    return not errors


def names():
    """Collect translators' name proposals; show agreement and conflicts to settle."""
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    proposals = defaultdict(list)
    for path in sorted(TRANSLATIONS.glob('*.json')):
        for jp, p in json.loads(path.read_text(encoding='utf-8')).get('names', {}).items():
            if isinstance(p, dict) and p.get('en'):
                proposals[jp.strip('$')].append((path.stem, p['en'], p.get('kind'), p.get('evidence', '')))
    settled = {s['jp'] for s in json.loads(SETTLED.read_text(encoding='utf-8'))['terms']} if SETTLED.exists() else set()
    rows = []
    for jp, items in sorted(proposals.items()):
        t, _ = resolver.resolve(jp)
        if jp in settled or (t and t['status'] in ('confirmed', 'official')):
            continue
        english = Counter(en for _, en, _, _ in items)
        rows.append((len(english) > 1, jp, t['token'] if t else None, items))
    print('%d names proposed and not yet settled; %d with conflicting English' % (
        len(rows), sum(1 for r in rows if r[0])))
    for conflict, jp, token, items in sorted(rows, key=lambda r: (not r[0], r[1])):
        print('%s %s%s' % ('CONFLICT' if conflict else 'agreed  ', jp, '' if token else '  (not in glossary)'))
        for batch, en, kind, evidence in items:
            print('    %-8s %-30s %-8s %s' % (batch, en, kind or '', evidence[:90]))


RETOKEN = ROOT / 'work/glossary/library_retoken.json'


def retoken(apply):
    """Re-point prose tokens after a name split, per RETOKEN rules. Dry run by default."""
    library = load_library()
    rules = json.loads(RETOKEN.read_text(encoding='utf-8'))['rules']
    changed_files, total, hits = {}, 0, Counter()
    for path in sorted(TRANSLATIONS.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        kind = data['kind']
        tengoku = library[kind][0]
        dirty = False
        for key, entry in data['entries'].items():
            record = tengoku[int(key)]
            series = record['text'][SERIES_FIELD[kind]] or ''
            japanese = (record['text']['DSCR'] or '') + (record['text']['DSC2'] or '')
            for i, rule in enumerate(rules):
                if rule.get('kind') and rule['kind'] != kind:
                    continue
                if rule.get('ids') and int(key) not in rule['ids']:
                    continue
                if rule.get('series_contains') and rule['series_contains'] not in series:
                    continue
                if rule.get('jp_contains') and rule['jp_contains'] not in japanese:
                    continue
                if rule.get('jp_lacks') and rule['jp_lacks'] in japanese:
                    continue
                for field in lc.TEXT:
                    text = entry.get(field)
                    if not isinstance(text, str):
                        continue
                    if 'text_from' in rule:
                        new = text.replace(rule['text_from'], rule['text_to'])
                    else:
                        new = TOKEN.sub(lambda m: '$$%s%s$$' % (rule['to'], m.group(2) or '')
                                        if m.group(1) == rule['from'] else m.group(0), text)
                    if new != text:
                        count = text.count('$$%s' % rule.get('from', '')) if 'from' in rule else 1
                        hits[i] += count
                        total += count
                        print('%-14s %s %s %s: %s' % (path.name, kind, key, field, rule['why']))
                        entry[field], dirty = new, True
        if dirty:
            changed_files[path] = data
    for i, rule in enumerate(rules):
        if not hits[i]:
            print('NO MATCH: rule %d (%s)' % (i, rule['why']))
    print('%d replacements in %d files' % (total, len(changed_files)))
    if apply:
        for path, data in changed_files.items():
            write_json(path, data)
        print('Wrote %d files' % len(changed_files))
    else:
        print('DRY RUN: no files written')


def name_script(apply, sample=12):
    """Turn literal English names into glossary tokens (BASE_RULES: scripts fix names).

    A literal is replaced only where the entry's own Japanese contains the
    term's Japanese, so common words ('Union', 'Mars', 'Element') are safe.
    Variants caught: the current English, earlier glossary English (Jigoku
    snapshot) and translators' proposals. Longest names first. Also drops a
    duplicated article before a token whose English starts with 'the', and
    rewrites 'Earth $$スフィア$$' to $$地球圏$$ where the Japanese says 地球圏.
    """
    library = load_library()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    old = json.loads((ROOT / 'work/glossary/reference/jigoku_glossary_20260911.json').read_text(encoding='utf-8'))['terms']
    variants = defaultdict(set)   # English form -> set of tokens it may stand for
    by_token = {t['token']: t for t in terms}
    for t in terms:
        if t['en'] and t['status'] != 'pending' and len(t['en']) >= 3:
            variants[t['en']].add(t['token'])
    jp_to_tokens = defaultdict(set)
    for t in terms:
        jp_to_tokens[t['jp']].add(t['token'])
    for o in old:
        if o.get('en') and len(o['en']) >= 3:
            for token in jp_to_tokens.get(o['jp'], ()):
                variants[o['en']].add(token)
    for path in sorted(TRANSLATIONS.glob('*.json')):
        for jp, p in json.loads(path.read_text(encoding='utf-8')).get('names', {}).items():
            if isinstance(p, dict) and p.get('en') and len(p['en']) >= 3:
                for token in jp_to_tokens.get(jp.strip('$').partition('#')[0], ()):
                    variants[p['en']].add(token)
    forms = sorted(variants, key=len, reverse=True)
    pattern = re.compile(r'(?<![A-Za-z0-9$\'-])(%s)(?![A-Za-z0-9-])' % '|'.join(re.escape(f) for f in forms))
    the_tokens = {t['token'] for t in terms if (t['en'] or '').lower().startswith('the ')}
    changes, per_form, examples, files = 0, Counter(), [], {}
    for path in sorted(TRANSLATIONS.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        kind, dirty = data['kind'], False
        for key, entry in data['entries'].items():
            record = library[kind][0][int(key)]
            japanese = (record['text']['DSCR'] or '') + (record['text']['DSC2'] or '')
            for field in lc.TEXT:
                text = entry.get(field)
                if not isinstance(text, str):
                    continue
                pieces = re.split(r'(\$\$[^$]+\$\$)', text)
                for i in range(0, len(pieces), 2):   # even indexes are outside tokens
                    def swap(m):
                        form = m.group(1)
                        # A lower-case variant is a common word ('messenger'):
                        # only its exact current English may become a token.
                        options = [tk for tk in variants[form]
                                   if by_token[tk]['jp'] in japanese
                                   and (form[0].isupper() or by_token[tk]['en'] == form)]
                        if len(options) != 1:
                            return m.group(0)
                        per_form[m.group(1)] += 1
                        return '$$%s$$' % options[0]
                    pieces[i] = pattern.sub(swap, pieces[i])
                new = ''.join(pieces)
                if '地球圏' in japanese:
                    new = new.replace('Earth $$スフィア$$', '$$地球圏$$')
                for token in the_tokens:
                    new = re.sub(r'\b[Tt]he \$\$%s(\|lc)?\$\$' % re.escape(token), '$$%s\\1$$' % token, new)
                if new != text:
                    changes += 1
                    if len(examples) < sample:
                        examples.append((path.name, key, field, text, new))
                    entry[field], dirty = new, True
        if dirty:
            files[path] = data
    print('fields changed: %d in %d files; literal names tokenized: %d' % (changes, len(files), sum(per_form.values())))
    print('most frequent: ' + ', '.join('%s x%d' % kv for kv in per_form.most_common(25)))
    for name, key, field, before, after in examples:
        sm = __import__('difflib').SequenceMatcher(None, before, after)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op != 'equal':
                print('%s %s %s: %r -> %r' % (name, key, field, before[max(0, a1 - 15):a2 + 15], after[max(0, b1 - 15):b2 + 15]))
    if apply:
        for path, data in files.items():
            write_json(path, data)
        print('Wrote %d files' % len(files))
    else:
        print('DRY RUN: no files written')


PROOF_BRIEFS = ROOT / 'work/tengoku/proofread_briefs'
PROOF_FIXES = ROOT / 'work/translation/en/library_proofread'
PROOF_BATCH = 40


def proofread(apply):
    """Export meaning-proofreading briefs: Japanese, current English, genders, notes."""
    library = load_library()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    characters = json.loads(CHARACTERS.read_text(encoding='utf-8'))['characters']
    gender = {}
    for c in characters.values():
        for token in c.get('tokens', {}).values():
            gender[token] = (c.get('gender'), (c.get('gender_evidence') or '')[:100])
    for t in terms:
        if t.get('profile') and t['profile'].get('gender'):
            gender.setdefault(t['token'], (t['profile']['gender'], (t['profile'].get('gender_evidence') or '')[:100]))
    entries, _ = load_translations()
    notes = defaultdict(list)
    # 'pilot 12', 'kw 12/13', '12:' at the start; never a stray '00' in 'Gundam 00'.
    cited = re.compile(r'(?:^|(?:kw|keyword|pilot|pilots|robot|robots|entry|entries|pt|rt)\s+)(\d{1,3})(?=[\s:,/)-])', re.I)
    for path in sorted(TRANSLATIONS.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        own = set(data.get('entries', {}))
        for note in data.get('report', {}).get('uncertain', []):
            head = note[:80]
            ids = {m.group(1).lstrip('0') or '0' for m in cited.finditer(head)}
            ids |= {n.lstrip('0') or '0' for m in re.finditer(r'^(\d{1,3}(?:\s*[/,]\s*\d{1,3})+)', head)
                    for n in re.split(r'\s*[/,]\s*', m.group(1))}
            for key in ids & own:
                if note not in notes[(data['kind'], int(key))]:
                    notes[(data['kind'], int(key))].append(note)
    batches = []
    for kind in ('keyword', 'pilot', 'robot'):
        ids = sorted(int(k) for k in entries[kind])
        for start in range(0, len(ids), PROOF_BATCH):
            chunk = ids[start:start + PROOF_BATCH]
            name = 'proof_%s_%03d' % (PREFIX[kind], chunk[0])
            out = ['# Proofread %s: %s entries %d-%d' % (name, kind, chunk[0], chunk[-1]), '',
                   'Write `work/translation/en/library_proofread/%s.json`. Read `docs/LIBRARY_PROOFREAD.md` first.' % name, '']
            for tid in chunk:
                file, entry = entries[kind][str(tid)]
                record = library[kind][0][tid]
                out += ['## %s %d' % (kind, tid), '', '- file: `%s`' % file]
                for field in NAME_FIELDS[kind]:
                    jp = (record['text'][field] or '').strip()
                    if jp and not placeholder(jp):
                        t, _ = resolver.resolve(jp)
                        g = gender.get(t['token']) if t else None
                        out.append('- %s: %s = %s%s' % (field, jp, t['en'] if t else '?',
                                                          ' (gender: %s; %s)' % g if g else ''))
                used = sorted({m.group(1) for f in lc.TEXT for m in TOKEN.finditer(entry.get(f) or '')})
                people = []
                for name_ in used:
                    t, _ = resolver.resolve(name_)
                    if t:
                        g = gender.get(t['token'])
                        people.append('`$$%s$$` = %s%s' % (name_, t['en'], ' [%s]' % g[0] if g else ''))
                if people:
                    out.append('- tokens: ' + '; '.join(people))
                for note in notes.get((kind, tid), [])[:4]:
                    out.append('- translator note: ' + note[:400])
                for field in lc.TEXT:
                    if field == 'DSC2' and entry.get('DSC2') is None:
                        out += ['', '### DSC2: same as DSCR (null)']
                        continue
                    out += ['', '### %s' % field, '', 'Japanese:', '', '```', record['text'][field] or '', '```', '',
                            'English (sha256 `%s`):' % sha256((entry[field] or '').encode('utf-8'))[:16], '',
                            '```', entry[field] or '', '```']
                out.append('')
            batches.append((name, '\n'.join(out) + '\n'))
    print('%d proofreading briefs' % len(batches))
    if apply:
        PROOF_BRIEFS.mkdir(parents=True, exist_ok=True)
        for name, text in batches:
            with (PROOF_BRIEFS / (name + '.md')).open('w', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print('Wrote briefs to ' + str(PROOF_BRIEFS))
    else:
        print('DRY RUN: no briefs written')


def proofread_apply(apply):
    """Apply proofreaders' fixes; a fix is rejected if the English changed since its brief."""
    library = load_library()
    entries, _ = load_translations()
    resolver = Resolver(json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms'])
    changed, applied, rejected = {}, 0, []
    for path in sorted(PROOF_FIXES.glob('*.json')):
        for fix in json.loads(path.read_text(encoding='utf-8')).get('fixes', []):
            kind, key, field = fix['kind'], str(fix['id']), fix['field']
            file, entry = entries[kind][key]
            where = '%s %s %s %s' % (path.stem, kind, key, field)
            current = entry.get(field) or ''
            if sha256(current.encode('utf-8'))[:16] != fix.get('english_sha256', '')[:16]:
                rejected.append(where + ': English changed since the brief')
                continue
            errors, _, missing = check_entry(where, dict(entry, **{field: fix['new']}),
                                             library[kind][0][int(key)], resolver)
            if errors or missing:
                rejected.append(where + ': ' + '; '.join(errors + sorted(missing))[:200])
                continue
            entry[field] = fix['new']
            entry.setdefault('proofread', []).append({'field': field, 'by': path.stem, 'reason': fix.get('reason', '')})
            changed[file] = kind
            applied += 1
    print('fixes applied %d, rejected %d' % (applied, len(rejected)))
    for r in rejected:
        print('REJECTED ' + r)
    if apply:
        for file, kind in changed.items():
            path = TRANSLATIONS / file
            data = json.loads(path.read_text(encoding='utf-8'))
            for key, (name, entry) in entries[kind].items():
                if name == file:
                    data['entries'][key] = entry
            write_json(path, data)
        print('Wrote %d files' % len(changed))
    else:
        print('DRY RUN: no files written')


# --------------------------------------------------------- name research

# Official terms that translators reported as doubtful or clashing; each is
# re-checked, and any change needs `override_approved` from the orchestrator.
FLAGGED = {
    'ガンダムサバーニャ': "glossary 'Gundam Zanbanya'; official English may be Gundam Sabernya",
    'ラケージ・ユンボロ': "glossary 'Rackage Yunboro' vs akurasu pilot database 'Lukkage'",
    'アリシア': "glossary 'Alicia' vs akurasu 'Silvia de Alisia'",
    'サザンカ・ビアンカ': "sheet 'Sazanke' vs akurasu 'Sazanka Bianca'",
    '宇宙航行母艦ソレスタルビーイング': "English 'Celestial Being (mothership)' has brackets mid-sentence",
    '第１０の使徒': "English '10th Angel' vs 'the Ninth Angel' article style",
    '至高神Ｚ': "English 'Supreme God Z / Hypsistos Z' reads oddly in prose",
    '脳量子波': "Title Case English breaks |lc mid-sentence",
    'ムウ': 'Mu La Flaga (SEED) and Mu (Orguss) are different people',
    'シリウス': 'Aquarion pilot vs the star system Sirius',
    '黒い太陽': 'Sphere treasure (Z original) vs an Aquarion phenomenon',
    'ＵＮ': 'Tengoku Universal Network vs United Nations (国連) in Jigoku prose',
    '早乙女': 'Alto Saotome family (Macross F) vs Professor Saotome (Getter)',
    'インベーダー': 'pilot and robot terms; creatures vs units',
    'ＥＬＳ': 'keyword and robot terms should agree',
    'Ｄ．Ｏ．Ｍ．Ｅ．': 'keyword and pilot terms should agree',
    'ブールーズ・ゴウト': 'Tengoku name order is ゴウト・ブールーズ',
    'エルガン': "Jigoku 'Elgan Roadick' vs glossary 'Elgan Roddick'",
}
RESEARCH_CAP = 90


def entry_series(library, terms_by_target):
    series = {}
    for kind, (tengoku, _, _) in library.items():
        for tid, record in tengoku.items():
            jp = (record['text'][SERIES_FIELD[kind]] or '').strip().strip('「」')
            t = terms_by_target.get((kind, tid, SERIES_FIELD[kind]))
            series[(kind, tid)] = (jp, t['en'] if t and t['en'] else jp)
    return series


FRANCHISES = [('ガンダム', 'gundam'), ('マクロス', 'macross'), ('エヴァンゲリオン', 'evangelion'),
              ('ヱヴァンゲリヲン', 'evangelion'), ('トップをねらえ', 'gunbuster'), ('ダイ・ガード', 'super'),
              ('アクエリオン', 'aquarion'), ('ボトムズ', 'votoms'), ('ギアス', 'geass'),
              ('フルメタル', 'fmp'), ('グレンラガン', 'gurren_lagann'), ('ゲッター', 'super'),
              ('マジン', 'super'), ('ザンボット', 'super'), ('ダイターン', 'super'), ('トライダー', 'super'),
              ('鉄人', 'super'), ('ゴッドマーズ', 'super'), ('ダイガード', 'super'), ('ダンクーガ', 'super'),
              ('ビッグオー', 'super'), ('オーガス', 'orguss'), ('バスター', 'gunbuster'),
              ('ガルガンティア', 'gargantia'), ('オリジナル', 'original')]


def franchise(series_jp):
    return next((name for key, name in FRANCHISES if key in series_jp), 'other')


def research(apply):
    library = load_library()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    by_target = {(tg['archive'], tg['tengoku_id'], tg['field']): t for t in terms for tg in t['targets']}
    series = entry_series(library, by_target)
    entries, _ = load_translations()

    usage, proposals = defaultdict(list), defaultdict(list)
    for kind, done in entries.items():
        for key, (name, entry) in done.items():
            for field in lc.TEXT:
                for m in TOKEN.finditer(entry.get(field) or ''):
                    usage[m.group(1)].append((kind, int(key), field, entry[field], m.start()))
    for path in sorted(TRANSLATIONS.glob('*.json')):
        for jp, p in json.loads(path.read_text(encoding='utf-8')).get('names', {}).items():
            if isinstance(p, dict) and p.get('en'):
                proposals[jp.strip('$')].append('%s: %s (%s) - %s' % (
                    path.stem, p['en'], p.get('kind', '?'), (p.get('evidence') or '')[:160]))

    items = {}
    def add(key, **info):
        item = items.setdefault(key, {'name': key, 'reasons': [], 'series': Counter()})
        item['reasons'].append(info.pop('reason'))
        item.update(info)
    for t in terms:
        if t['status'] in ('pending', 'proposed', 'ambiguous') and (t['targets'] or t['token'] in usage):
            add(t['token'], term=t, reason='status ' + t['status'])
    for name in usage:
        t, problem = resolver.resolve(name)
        if problem:
            add(name, term=None, reason='not in glossary' if 'not in' in problem else problem)
    for t in terms:
        if t['jp'] in FLAGGED:
            add(t['token'], term=t, reason='flagged: ' + FLAGGED[t['jp']])

    for key, item in items.items():
        t = item.get('term')
        for target in (t['targets'] if t else []):
            item['series'][series[(target['archive'], target['tengoku_id'])]] += 3
        for kind, tid, _, _, _ in usage.get(key, []) + usage.get(key.partition('#')[0], []):
            item['series'][series[(kind, tid)]] += 1

    characters = []
    for tid, record in sorted(library['pilot'][0].items()):
        characters.append({'pilot_id': tid, 'series': series[('pilot', tid)], 'record': record})

    groups = defaultdict(lambda: {'items': [], 'characters': []})
    for key, item in sorted(items.items()):
        top = item['series'].most_common(1)[0][0] if item['series'] else ('', 'unknown')
        item['top'] = top
        groups[franchise(top[0])]['items'].append(item)
    for c in characters:
        groups[franchise(c['series'][0])]['characters'].append(c)
    # Split oversized franchises by series so each researcher has a manageable list.
    final = {}
    for name, g in sorted(groups.items()):
        size = len(g['items']) + len(g['characters']) // 3
        if size <= RESEARCH_CAP:
            final[name] = g
            continue
        by_series = defaultdict(lambda: {'items': [], 'characters': []})
        for item in g['items']:
            by_series[item['top'][1]]['items'].append(item)
        for c in g['characters']:
            by_series[c['series'][1]]['characters'].append(c)
        part, count, index = {'items': [], 'characters': []}, 0, 1
        for s_name, sg in sorted(by_series.items()):
            s_size = len(sg['items']) + len(sg['characters']) // 3
            if count and count + s_size > RESEARCH_CAP:
                final['%s_%d' % (name, index)] = part
                part, count, index = {'items': [], 'characters': []}, 0, index + 1
            part['items'] += sg['items']
            part['characters'] += sg['characters']
            count += s_size
        final['%s_%d' % (name, index)] = part
    # A single oversized series (the Z original cast) is chunked by names.
    for name in [n for n, g in final.items() if len(g['items']) > RESEARCH_CAP * 1.4]:
        g = final.pop(name)
        chunks = -(-len(g['items']) // RESEARCH_CAP)
        size = -(-len(g['items']) // chunks)
        for i in range(chunks):
            final['%s%s' % (name, 'abcdefgh'[i])] = {
                'items': g['items'][i * size:(i + 1) * size],
                'characters': g['characters'][i::chunks]}

    for name, g in sorted(final.items()):
        print('%-18s names %3d  characters %3d' % (name, len(g['items']), len(g['characters'])))
    print('total names %d, characters %d, groups %d' % (
        sum(len(g['items']) for g in final.values()), sum(len(g['characters']) for g in final.values()), len(final)))
    if not apply:
        print('DRY RUN: no research briefs written')
        return
    RESEARCH_BRIEFS.mkdir(parents=True, exist_ok=True)
    for name, g in sorted(final.items()):
        out = ['# Name research: %s' % name, '',
               'Write `work/glossary/research/%s.json`. Read `docs/NAME_RESEARCH.md` first.' % name, '',
               '## Names (%d)' % len(g['items']), '']
        for item in g['items']:
            t = item.get('term')
            out.append('### `%s`' % item['name'])
            out.append('- why: ' + '; '.join(item['reasons']))
            if t:
                out.append('- glossary: kind %s, English %s, status %s, source %s' % (
                    t['kind'], t['en'] or '-', t['status'], t['source'] or '-'))
                for target in t['targets']:
                    out.append('- own library entry: %s %d field %s (series %s)' % (
                        target['archive'], target['tengoku_id'], target['field'], series[(target['archive'], target['tengoku_id'])][1]))
            out.append('- series seen with: ' + ', '.join('%s x%d' % (s[1], n) for s, n in item['series'].most_common(3)))
            for line in proposals.get(item['name'], []) + proposals.get(item['name'].partition('#')[0], [])[:0]:
                out.append('- proposed by ' + line)
            for kind, tid, field, text, pos in (usage.get(item['name'], []))[:3]:
                snippet = text[max(0, pos - 100):pos + 140].replace('\n', ' ')
                out.append('- used in %s %d %s: ...%s...' % (kind, tid, field, snippet))
            out.append('')
        out += ['## Characters to profile (%d pilot entries)' % len(g['characters']), '']
        for c in g['characters']:
            r = c['record']
            names = []
            for field in NAME_FIELDS['pilot']:
                t = by_target.get(('pilot', c['pilot_id'], field))
                if t:
                    names.append('%s `%s` = %s' % (field, t['token'], t['en'] or 'PENDING'))
            out += ['### pilot %d (%s)' % (c['pilot_id'], c['series'][1]), '- ' + '; '.join(names),
                    '- Japanese DSCR: ' + (r['text']['DSCR'] or '').replace('\n', '')[:420], '']
        with (RESEARCH_BRIEFS / (name + '.md')).open('w', encoding='utf-8', newline='\n') as stream:
            stream.write('\n'.join(out) + '\n')
    print('Wrote research briefs to ' + str(RESEARCH_BRIEFS))


# ----------------------------------------------------------------- briefs

def english_names(record, kind, resolver_by_target):
    lines = []
    for field in NAME_FIELDS[kind] + (SERIES_FIELD[kind],):
        jp = (record['text'][field] or '').strip()
        if placeholder(jp):
            continue
        t = resolver_by_target.get((kind, record['id'], field))
        en = t['en'] if t and t['en'] else 'PENDING - propose one in NAMES'
        token = t['token'] if t else '?'
        lines.append('- %s: `%s` -> **%s** (token `$$%s$$`, %s)' % (field, jp, en, token, t['status'] if t else '?'))
    return lines


def export(apply):
    library = load_library()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    by_target = {(tg['archive'], tg['tengoku_id'], tg['field']): t for t in terms for tg in t['targets']}
    done, _ = load_translations()
    batches = []
    for kind, (tengoku, jigoku, rows) in library.items():
        english = jigoku_english(kind)
        todo = [tid for tid in sorted(tengoku) if str(tid) not in done[kind]]
        for start in range(0, len(todo), BATCH[kind]):
            ids = todo[start:start + BATCH[kind]]
            name = '%s_%03d' % (PREFIX[kind], ids[0])
            out = ['# Brief %s: %s entries %s' % (name, kind, ', '.join(map(str, ids))), '',
                   'Write `work/translation/en/library/%s.json`. Read `docs/LIBRARY_STYLE.md` and '
                   '`work/tengoku/library_briefs/GLOSSARY.md` first.' % name, '']
            for tid in ids:
                record, row = tengoku[tid], rows[tid]
                out += ['## %s %d' % (kind, tid), ''] + english_names(record, kind, by_target) + ['']
                out += ['source_sha256: `%s`' % json.dumps(source_hashes(record)), '', '### DSCR (Japanese)', '',
                        '```', record['text']['DSCR'] or '', '```', '']
                if record['fields']['DSC2'] == record['fields']['DSCR']:
                    out += ['### DSC2: same as DSCR -> write `"DSC2": null`', '']
                else:
                    out += ['### DSC2 (Japanese, differs from DSCR; translate it in full)', '',
                            '```', record['text']['DSC2'] or '', '```', '']
                if row.get('jigoku_id') is not None and english.get(row['jigoku_id']):
                    ref = english[row['jigoku_id']]
                    jrec = jigoku[row['jigoku_id']]
                    out += ['### Jigoku reference (entry %d, %s, DSCR similarity %.2f)' % (
                        row['jigoku_id'], row['status'], row['description_similarity']), '',
                        'Jigoku Japanese DSCR:', '', '```', jrec['text']['DSCR'] or '', '```', '',
                        'Jigoku English DSCR:', '', '```', ref.get('DSCR', ''), '```', '']
                    if ref.get('DSC2'):
                        out += ['Jigoku English DSC2:', '', '```', ref['DSC2'], '```', '']
                else:
                    out += ['### No Jigoku entry: new in Tengoku', '']
            batches.append((name, '\n'.join(out) + '\n'))
    characters = json.loads(CHARACTERS.read_text(encoding='utf-8'))['characters'] if CHARACTERS.exists() else {}
    gender = {}
    for c in characters.values():
        for token in c.get('tokens', {}).values():
            gender[token] = c.get('gender')
    for t in terms:
        if t.get('profile') and t['profile'].get('gender'):
            gender.setdefault(t['token'], t['profile']['gender'])
    sheet = ['# Library glossary sheet (generated; do not edit)', '',
             'Use `$$token$$` in prose for every name below. Status `pending` has no English yet:',
             'still use the token, and propose English in your NAMES block.',
             'Gender is researched (see work/glossary/library_characters.json); use he/she only',
             'when it says male/female, otherwise the name or they/them.', '',
             '| token | kind | English | status | gender |', '|---|---|---|---|---|']
    for t in sorted(terms, key=lambda t: (t['kind'], t['token'])):
        sheet.append('| `%s` | %s | %s | %s | %s |' % (
            t['token'], t['kind'], t['en'] or '-', t['status'], gender.get(t['token'], '')))
    print('%d briefs: %s' % (len(batches), ', '.join(n for n, _ in batches)))
    if apply:
        BRIEFS.mkdir(parents=True, exist_ok=True)
        for name, text in batches + [('GLOSSARY', '\n'.join(sheet) + '\n')]:
            with (BRIEFS / (name + '.md')).open('w', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print('Wrote briefs to ' + str(BRIEFS))
    else:
        print('DRY RUN: no briefs written')


def main():
    # Windows consoles default to cp1252/cp932 and fail on names such as ・.
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('seed', 'export', 'check', 'names', 'research', 'retoken',
                                            'proofread', 'proofread-apply', 'name-script'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--file', help='check: only this translation file name, e.g. kw_000.json')
    args = parser.parse_args()
    if args.command == 'seed':
        seed(args.apply)
    elif args.command == 'export':
        export(args.apply)
    elif args.command == 'names':
        names()
    elif args.command == 'research':
        research(args.apply)
    elif args.command == 'retoken':
        retoken(args.apply)
    elif args.command == 'proofread':
        proofread(args.apply)
    elif args.command == 'proofread-apply':
        proofread_apply(args.apply)
    elif args.command == 'name-script':
        name_script(args.apply)
    else:
        raise SystemExit(0 if check(args.file) else 1)


if __name__ == '__main__':
    main()
