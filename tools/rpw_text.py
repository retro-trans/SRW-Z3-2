"""RPW_DATA name tables: pilot / robot / weapon / skill / part names, series titles, shoot-down quotes.

    python -m tools.rpw_text slots                 # verified pointer schema + per-column caps
    python -m tools.rpw_text reuse [--apply]       # glossary + Jigoku English -> rpw_names.json
    python -m tools.rpw_text check                 # coverage, caps, characters
    python -m tools.rpw_text export [--apply]      # briefs for the untranslated strings

The binary chunks are record arrays whose name columns hold u32 offsets into
the j-string pool (docs/UI_RPW.md). Only the columns in SCHEMA are ever
repointed: every value in them must be a real string start, checked on every
load (Jigoku crashed after repointing coincidental values in index tables).
Descriptions (sk-pri 4-5, boost-p 3-8) are out of scope: in Jigoku, swapped
boost-part descriptions corrupted memory at boot, and skill descriptions
needed a draw-time hook.

Translation file work/translation/en/ui/rpw_names.json:
    {"schema": 1,
     "strings": {"<family>": {"<jp>": {"en", "source"}}},   # default per string
     "slots": {"<chunk>:<record>:<col>": {"en", "source"}}} # one cell (pilot name pieces)
English is plain ASCII text with glossary names already written out (no
tokens: these strings ARE the names). A slot's text = its slot entry, else
its family's string entry, else it stays Japanese.
"""
import argparse
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

from tools.common import ROOT, write_json
from tools.source_text import rpw_chunks

NAMES = ROOT / 'work/translation/en/ui/rpw_names.json'
BRIEFS = ROOT / 'work/tengoku/rpw_briefs'
NEW = ROOT / 'work/translation/en/ui/rpw_new'          # agents' answer slices
JIGOKU = Path('E:/Projects/SRW Z3/translation')        # read only

# chunk: (record stride in words, {column: family})
SCHEMA = {
    'pilot-nw': (8, {0: 'pilot', 1: 'pilot', 2: 'pilot'}),
    'robot': (24, {2: 'robot_short', 3: 'robot'}),
    'weapon': (13, {3: 'weapon_short', 4: 'weapon'}),
    'sk-pri': (13, {1: 'skill', 2: 'skill', 3: 'skill'}),
    'boost-p': (21, {1: 'part', 2: 'part'}),
    'pro-name': (2, {0: 'series'}),
    'deadmsg': (3, {0: 'quote'}),
}
FAMILIES = ('pilot', 'robot', 'robot_short', 'weapon', 'weapon_short', 'skill', 'part', 'series', 'quote')
SHORT = {'robot_short': 'robot', 'weapon_short': 'weapon'}   # short column falls back to the full name if it fits
PILOT_COLS = {0: 'display', 1: 'family', 2: 'given'}
# Byte limits (excluding NUL; each English letter is one 2-byte font cell).
# Known: battle speaker names (pilot-nw column 0) are strcpy'd into a 31-byte
# field (Jigoku 2026-09-26); level-up copies skill names into 32-byte slots and
# appends a level suffix (Jigoku). boost-p: Jigoku found the limit is per RECORD
# (all eight strings + NULs <= the largest original record), not per string;
# descriptions stay Japanese here. Robot/weapon short-name columns are held to
# their longest original for screen fit (the full name has its own column).
# Family/given names and the long columns are only reported: Jigoku shipped
# them at full English length without a fault.
HARD = {('pilot-nw', 0): 30, ('sk-pri', 1): 26, ('sk-pri', 2): 26, ('sk-pri', 3): 26}
CAPPED = {('robot', 2), ('weapon', 3)}
# Skills that never carry a level suffix may use the whole 32-byte slot minus the NUL (Jigoku's
# overflow: 32 bytes + NUL broke, so 31 is the edge; 30 keeps the 2-byte cell grid).
UNLEVELED_SKILLS = {'ギアスの呪縛'}      # unique, no PP costs, never shown with a level
JP = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff10-\uff5a]')


def load_rpw(settings=None):
    from tools.cpk import CPK
    from tools.inventory import RPW
    from tools.pipeline import config, verified_source
    settings = settings or config(ROOT / 'config/tengoku.json')
    archive = CPK(verified_source(settings, RPW))
    return archive.read(archive.files[0])


def pool_of(data):
    js = next(c for c in rpw_chunks(data) if c['name'] == 'j-string')
    return js, data[js['body_offset']:js['body_end']]


def slots(data):
    """[{'id', 'chunk', 'record', 'col', 'family', 'pointer_offset', 'string', 'jp'}]; raises on schema drift."""
    js, pool = pool_of(data)
    starts = {0} | {i + 1 for i, b in enumerate(pool) if b == 0 and i + 1 < len(pool)}
    chunks = {c['name']: c for c in rpw_chunks(data)}
    out = []
    for name, (stride, cols) in SCHEMA.items():
        c = chunks[name]
        size = c['body_end'] - c['body_offset']
        if size % (stride * 4):
            raise ValueError('%s: %d bytes is not a whole number of %d-word records' % (name, size, stride))
        for r in range(size // (stride * 4)):
            for col, family in cols.items():
                at = c['body_offset'] + (r * stride + col) * 4
                w = struct.unpack_from('<I', data, at)[0]
                if w not in starts:
                    raise ValueError('%s record %d column %d is not a string pointer' % (name, r, col))
                jp = pool[w:pool.index(b'\0', w)].decode('cp932')
                out.append({'id': '%s:%d:%d' % (name, r, col), 'chunk': name, 'record': r, 'col': col,
                            'family': family, 'pointer_offset': at, 'string': w, 'jp': jp})
    return out


def caps(rows):
    """{(chunk, col): byte cap} -- see HARD."""
    longest = defaultdict(int)
    for s in rows:
        longest[(s['chunk'], s['col'])] = max(longest[(s['chunk'], s['col'])], len(s['jp'].encode('cp932')))
    return {k: HARD.get(k, v - v % 2) for k, v in longest.items()}


def limit_for(slot, cap):
    if slot['chunk'] == 'sk-pri' and slot['jp'] in UNLEVELED_SKILLS:
        return 30
    return cap[(slot['chunk'], slot['col'])]


def limited(key):
    return key in HARD or key in CAPPED


def cost(text):
    return 2 * len(text.replace('\n', '')) + text.count('\n')


def boostp_budget(data):
    """(largest original record bytes, {record: bytes of its columns 3-8 + NULs})."""
    js, pool = pool_of(data)
    c = next(c for c in rpw_chunks(data) if c['name'] == 'boost-p')
    stride = SCHEMA['boost-p'][0]
    total, rest = 0, {}
    for r in range((c['body_end'] - c['body_offset']) // (stride * 4)):
        lens = []
        for col in range(1, 9):
            w = struct.unpack_from('<I', data, c['body_offset'] + (r * stride + col) * 4)[0]
            lens.append(pool.index(b'\0', w) - w + 1)
        total = max(total, sum(lens))
        rest[r] = sum(lens[2:])
    return total, rest


def needs_text(jp):
    return bool(JP.search(jp)) and jp not in ('－－',)


def unusual(text):
    """Characters the build cannot draw as English: kana/kanji, or anything outside ASCII and cp932.
    Symbols such as the ∀ of ∀ Gundam or a Greek letter stay as the game's own glyphs, as in the library."""
    bad = set()
    for c in text:
        if 32 <= ord(c) < 127 or c == '\n':
            continue
        try:
            c.encode('cp932')
        except UnicodeEncodeError:
            bad.add(c)
            continue
        if JP.search(c):
            bad.add(c)
    return sorted(bad)


def load_names():
    if NAMES.exists():
        return json.loads(NAMES.read_text(encoding='utf-8'))
    return {'schema': 1, 'strings': {f: {} for f in FAMILIES}, 'slots': {}}


def text_for(slot, names, cap=None):
    """The slot's English; a short column takes the full name when no short form exists and it fits."""
    e = names['slots'].get(slot['id']) or names['strings'].get(slot['family'], {}).get(slot['jp'])
    if not (e and e.get('en')) and slot['family'] in SHORT:
        e = names['strings'].get(SHORT[slot['family']], {}).get(slot['jp'])
        if e and e.get('en') and cap is not None and cost(e['en']) > cap:
            return None
    return e['en'] if e and e.get('en') else None


# --------------------------------------------------------------------------
# Reuse

def _jigoku(name):
    path = JIGOKU / name
    if not path.exists():
        return {}
    d = json.loads(path.read_text(encoding='utf-8'))
    return {k: v for k, v in d.items() if not k.startswith('_') and isinstance(v, str) and v}


def glossary_index():
    from tools.library_text import GLOSSARY
    by = defaultdict(set)
    for t in json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']:
        if t.get('en'):
            by[(t['kind'], t['jp'])].add(t['en'])
    return by


def split_full(full_en, given_jp, family_jp, gl):
    """English (given, family) from a glossary full name, using piece English to find the split."""
    words = full_en.split()
    if len(words) < 2:
        return None
    for g in gl.get(('pilot', given_jp), ()):
        if full_en.startswith(g + ' '):
            return g, full_en[len(g) + 1:]
        if full_en.endswith(' ' + g):                 # family-first English (rare)
            return g, full_en[:-len(g) - 1]
    for f in gl.get(('pilot', family_jp), ()):
        if full_en.endswith(' ' + f):
            return full_en[:-len(f) - 1], f
    if len(words) == 2:
        return words[0], words[1]
    return None


def reuse(apply):
    data = load_rpw()
    rows = slots(data)
    names = load_names()
    gl = glossary_index()
    jg = {'weapon': _jigoku('weapons.json'), 'skill': _jigoku('skills.json'), 'part': _jigoku('parts.json'),
          'enemy': _jigoku('enemy_names.json'), 'piece': _jigoku('name_pieces.json')}
    stats = Counter()

    def put(table, key, en, source):
        if key in table and table[key].get('source', '').startswith(('fresh', 'review')):
            return
        table[key] = {'en': en, 'source': source}

    def unique(kind, jp):
        found = gl.get((kind, jp), set())
        return next(iter(found)) if len(found) == 1 else None

    strings, slot_tab = names['strings'], names['slots']
    by_record = defaultdict(dict)
    for s in rows:
        if s['chunk'] == 'pilot-nw':
            by_record[s['record']][s['col']] = s
    for s in rows:
        jp, fam = s['jp'], s['family']
        if not needs_text(jp):
            continue
        table = strings.setdefault(fam, {})
        if jp in table and fam != 'pilot':
            continue
        if fam in SHORT:
            continue
        if fam == 'robot':
            en = unique('robot', jp)
            if en:
                put(table, jp, en, 'glossary'); stats['robot glossary'] += 1
        elif fam == 'series':
            en = unique('series', jp)
            if en:
                put(table, jp, en, 'glossary'); stats['series glossary'] += 1
        elif fam in ('weapon', 'skill', 'part'):
            en = jg[fam].get(jp) or (unique('robot', jp) if fam == 'weapon' else None)
            if en:
                put(table, jp, en, 'jigoku:%ss.json' % fam if jg[fam].get(jp) else 'glossary'); stats[fam + ' reuse'] += 1
    # Pilots: per record, from the full name where the glossary has it.
    for r, rec in sorted(by_record.items()):
        disp, fam_s, giv_s = rec[0], rec[1], rec[2]
        family, given = fam_s['jp'], giv_s['jp']
        pieces = {}
        if needs_text(family) and needs_text(given) and family != given:
            for full in (family + given, given + '・' + family, family + '・' + given):
                en = unique('pilot', full)
                if en:
                    split = split_full(en, given, family, gl)
                    if split:
                        pieces = {2: split[0], 1: split[1]}
                        break
        for col, s in ((1, fam_s), (2, giv_s)):
            if col in pieces:
                put(slot_tab, s['id'], pieces[col], 'glossary full name'); stats['pilot piece from full name'] += 1
        for col, s in ((0, disp), (1, fam_s), (2, giv_s)):
            if not needs_text(s['jp']) or s['id'] in slot_tab:
                continue
            if col == 0 and disp['jp'] == given and 2 in pieces:
                put(slot_tab, s['id'], pieces[2], 'glossary full name'); stats['pilot display = given'] += 1
                continue
            en = unique('pilot', s['jp'])
            source = 'glossary'
            if not en:
                en, source = jg['enemy'].get(s['jp']) or jg['piece'].get(s['jp']), 'jigoku'
            if en:
                put(strings['pilot'], s['jp'], en, source); stats['pilot string ' + source] += 1
    total = Counter(); done = Counter()
    for s in rows:
        if needs_text(s['jp']):
            total[s['family']] += 1
            done[s['family']] += bool(text_for(s, names))
    for f in FAMILIES:
        print('%-7s %5d / %5d slots have English' % (f, done[f], total[f]))
    print(dict(stats))
    if apply:
        write_json(NAMES, names)
        print('wrote', NAMES)
    else:
        print('DRY RUN (pass --apply)')


# --------------------------------------------------------------------------
# Check

def check(verbose=True):
    data = load_rpw()
    rows = slots(data)
    cap = caps(rows)
    names = load_names()
    budget, rest = boostp_budget(data)
    errors, long_, missing = [], Counter(), Counter()
    known = {s['id'] for s in rows}
    for sid in names['slots']:
        if sid not in known:
            errors.append('unknown slot ' + sid)
    part_names = defaultdict(int)
    for s in rows:
        if not needs_text(s['jp']):
            continue
        key = (s['chunk'], s['col'])
        en = text_for(s, names, cap[key])
        if not en:
            missing[s['family']] += 1
            continue
        odd = unusual(en)
        if odd:
            errors.append('%s %s: non-ASCII %r' % (s['id'], s['jp'], ''.join(odd)))
        if en.count('\n') != s['jp'].count('\n'):
            errors.append('%s: %d line breaks, the Japanese has %d' % (s['id'], en.count('\n'), s['jp'].count('\n')))
        if s['chunk'] == 'boost-p':
            part_names[s['record']] += cost(en) + 1
        elif cost(en) > limit_for(s, cap):
            if limited(key):
                errors.append('%s %s: "%s" is %d bytes, limit %d' % (s['id'], s['jp'], en, cost(en), limit_for(s, cap)))
            else:
                long_['%s:%d' % key] += 1
    for r, n in part_names.items():
        if n + rest[r] > budget:
            errors.append('boost-p record %d: %d bytes with its Japanese descriptions, record limit %d' % (r, n + rest[r], budget))
    if verbose:
        for e in errors:
            print('ERROR', e)
        print('missing English (slots):', dict(missing))
        print('longer than any original in an uncapped column:', dict(long_))
        print('%d errors' % len(errors))
    return errors, missing


# --------------------------------------------------------------------------
# Briefs and merge

SLICE = 80


def work_items():
    """Everything without acceptable English, grouped into translation items (one per distinct thing)."""
    data = load_rpw()
    rows = slots(data)
    cap = caps(rows)
    names = load_names()
    budget, rest = boostp_budget(data)
    errors, _ = check(verbose=False)
    bad = set()
    for e in errors:
        bad.add(e.split(' ')[0])
        if e.startswith('boost-p record'):
            bad.add('boost-p:%s' % e.split()[2].rstrip(':'))
    rec = defaultdict(dict)
    for s in rows:
        rec[(s['chunk'], s['record'])][s['col']] = s
    items = {}
    weapons = sorted((s for s in rows if s['chunk'] == 'weapon' and s['col'] == 4), key=lambda s: s['record'])
    windex = {w['record']: n for n, w in enumerate(weapons)}
    for s in rows:
        if not needs_text(s['jp']):
            continue
        key = (s['chunk'], s['col'])
        en = text_for(s, names, cap[key])
        broken = s['id'] in bad or (s['chunk'] == 'boost-p' and ('boost-p:%d' % s['record']) in bad)
        if en and not broken:
            continue
        if s['chunk'] == 'pilot-nw':
            r = rec[(s['chunk'], s['record'])]
            tup = (r[0]['jp'], r[1]['jp'], r[2]['jp'])
            k = 'pilot:' + '|'.join(tup)
            it = items.setdefault(k, {'kind': 'pilot', 'jp': {'display': tup[0], 'family': tup[1], 'given': tup[2]},
                                      'records': [], 'current': {},
                                      'max_chars': {'display': cap[('pilot-nw', 0)] // 2}})
            if s['record'] not in it['records']:
                it['records'].append(s['record'])
            for col, label in PILOT_COLS.items():
                cur = text_for(r[col], names, cap[('pilot-nw', col)])
                if cur and needs_text(r[col]['jp']):
                    it['current'][label] = cur
        elif s['chunk'] in ('robot', 'weapon'):
            kind = s['chunk']
            k = '%s:%s' % (kind, s['jp'])
            full = names['strings'].get(kind, {}).get(s['jp'], {}).get('en')
            it = items.setdefault(k, {'kind': kind, 'jp': s['jp'], 'current': full,
                                      'short_max_chars': cap[(kind, 2 if kind == 'robot' else 3)] // 2,
                                      'records': []})
            if s['record'] not in it['records']:
                it['records'].append(s['record'])
            if kind == 'weapon' and 'neighbors' not in it:
                i = windex[s['record']]
                it['neighbors'] = [w['jp'] for w in weapons[max(0, i - 3):i + 4] if w['record'] != s['record']]
            if kind == 'robot' and 'variant' not in it:
                it['variant'] = rdebug_name(data, s['record'])
        else:
            kind = s['family']
            k = '%s:%s' % (kind, s['jp'].replace('\n', '\\n'))   # one-line key: a break is written \\n
            it = items.setdefault(k, {'kind': kind, 'jp': s['jp'], 'current': text_for(s, names, cap[key]),
                                      'records': []})
            if s['record'] not in it['records']:
                it['records'].append(s['record'])
            if kind == 'skill':
                it['max_chars'] = cap[key] // 2
            elif kind == 'part':
                it['max_chars'] = min(it.get('max_chars', 99), (budget - rest[s['record']] - 2) // 4)
            elif kind == 'quote':
                code = struct.unpack_from('<I', data, s['pointer_offset'] + 4)[0]
                name = pilot_by_code(data, code)
                it.setdefault('speakers', [])
                if name and name not in it['speakers']:
                    it['speakers'].append(name)
    return items


def rdebug_name(data, record):
    js, pool = pool_of(data)
    c = next(c for c in rpw_chunks(data) if c['name'] == 'r-debug')
    w = struct.unpack_from('<I', data, c['body_offset'] + record * 8 + 4)[0]
    return pool[w:pool.index(b'\0', w)].decode('cp932')


_PILOT_CODES = {}


def pilot_by_code(data, code):
    """deadmsg column 1 holds a pilot id code (as in pilot-nw column 3): Japanese family+given name."""
    if not _PILOT_CODES:
        js, pool = pool_of(data)
        c = next(c for c in rpw_chunks(data) if c['name'] == 'pilot-nw')

        def get(w):
            return pool[w:pool.index(b'\0', w)].decode('cp932')
        for r in range((c['body_end'] - c['body_offset']) // 32):
            w0, w1, w2, w3 = struct.unpack_from('<4I', data, c['body_offset'] + r * 32)
            _PILOT_CODES.setdefault(w3, get(w1) + get(w2) if get(w1) != get(w2) else get(w0))
    return _PILOT_CODES.get(code)


ORDER = ('skill', 'part', 'series', 'pilot', 'robot', 'weapon', 'quote')


def export(apply):
    items = work_items()
    groups = defaultdict(list)
    for k, it in sorted(items.items(), key=lambda kv: (ORDER.index(kv[1]['kind']), min(kv[1]['records']))):
        groups[it['kind']].append((k, it))
    briefs = []
    for kind in ORDER:
        rows = groups.get(kind, [])
        for n in range(0, len(rows), SLICE):
            briefs.append(('r_%s_%02d' % (kind, n // SLICE), rows[n:n + SLICE]))
    print(', '.join('%s %d' % (k, len(v)) for k, v in groups.items()), '->', len(briefs), 'briefs')
    if not apply:
        print('DRY RUN (pass --apply)')
        return
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for name, rows in briefs:
        out = ['# %s' % name, '',
               'Answer file: work/translation/en/ui/rpw_new/%s.json (format: docs/UI_RPW.md).' % name, '']
        for k, it in rows:
            out += ['## ' + k, '```json', json.dumps({x: v for x, v in it.items() if x != 'kind'}, ensure_ascii=False),
                    '```', '']
        (BRIEFS / (name + '.md')).write_bytes('\n'.join(out).encode('utf-8'))
    print('wrote %d briefs to %s' % (len(briefs), BRIEFS))


def check_answer(path, items=None):
    """Validate one answer slice against the open items; returns error strings."""
    items = items if items is not None else work_items()
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    errors = []
    for k, row in data.get('rows', {}).items():
        it = items.get(k)
        if it is None:
            continue                                 # already merged or no longer needed
        texts = row.get('en')
        if it['kind'] == 'pilot':
            if not isinstance(texts, dict):
                errors.append('%s: en must be {"display", "family", "given"}' % k)
                continue
            for label in ('display', 'family', 'given'):
                jp = it['jp'][label]
                if needs_text(jp) and not texts.get(label):
                    errors.append('%s: no %s' % (k, label))
                elif texts.get(label) and len(texts[label]) > it['max_chars'].get(label, 99):
                    errors.append('%s: %s "%s" over %d chars' % (k, label, texts[label], it['max_chars'][label]))
            values = list(texts.values())
        else:
            if not texts:
                errors.append('%s: no en' % k)
                continue
            values = [texts]
            if it.get('max_chars') and len(texts) > it['max_chars']:
                errors.append('%s: "%s" over %d chars' % (k, texts, it['max_chars']))
            if it['kind'] in ('robot', 'weapon'):
                short = row.get('short') or texts
                if len(short) > it['short_max_chars']:
                    errors.append('%s: short form "%s" over %d chars' % (k, short, it['short_max_chars']))
                values.append(short)
            if it['kind'] == 'quote' and texts.count('\n') != it['jp'].count('\n'):
                errors.append('%s: %d line breaks, the Japanese has %d' % (k, texts.count('\n'), it['jp'].count('\n')))
        for v in values:
            odd = unusual(v or '')
            if odd:
                errors.append('%s: non-ASCII %r' % (k, ''.join(odd)))
    brief = BRIEFS / (Path(path).stem + '.md')
    if brief.exists():
        wanted = set(re.findall(r'^## (.+)$', brief.read_text(encoding='utf-8'), re.M))
        gone = [w for w in wanted if w in items and w not in data.get('rows', {})]
        if gone:
            errors.append('%d items of the brief are not answered, e.g. %s' % (len(gone), gone[0]))
    return errors


def merge(apply):
    items = work_items()
    names = load_names()
    by_rec = defaultdict(dict)
    for s in slots(load_rpw()):
        if s['chunk'] == 'pilot-nw':
            by_rec[s['record']][s['col']] = s
    merged, problems = 0, []
    for path in sorted(NEW.glob('*.json')):
        errs = check_answer(path, items)
        if errs:
            problems.append('%s: %s' % (path.name, errs[0]))
            continue
        ans = json.loads(path.read_text(encoding='utf-8'))
        src = 'fresh:' + path.stem
        for k, row in ans.get('rows', {}).items():
            it = items.get(k)
            if it is None:
                continue
            if it['kind'] == 'pilot':
                for r in it['records']:
                    for col, label in PILOT_COLS.items():
                        s = by_rec[r][col]
                        if needs_text(s['jp']) and row['en'].get(label):
                            names['slots'][s['id']] = {'en': row['en'][label], 'source': src}
            else:
                names['strings'].setdefault(it['kind'], {})[it['jp']] = {'en': row['en'], 'source': src}
                if it['kind'] in ('robot', 'weapon') and row.get('short') and row['short'] != row['en']:
                    names['strings'].setdefault(it['kind'] + '_short', {})[it['jp']] = {'en': row['short'], 'source': src}
            merged += 1
    for p in problems:
        print('SKIPPED', p)
    print('merged %d items%s' % (merged, '' if apply else ' (DRY RUN, pass --apply)'))
    if apply:
        write_json(NAMES, names)


# --------------------------------------------------------------------------
# Build: append English to the pool and repoint reviewed cells

def spirit_cells(data):
    """Pointer offsets of the reviewed Spirit table cells (docs/UI_SPIRITS.md)."""
    c = next(c for c in rpw_chunks(data) if c['name'] == 'spirit')
    return {c['body_offset'] + i * 20 + col * 4 for i in range(1, 44) for col in (1, 2, 3)}


def name_cells(data, names, encode):
    """[{'id', 'pointer_offset', 'old', 'raw', 'english'}] for every slot whose English passes the limits.

    Anything that fails check() (a hard limit, a part record over budget, an
    undrawable character) stays Japanese; the count is reported."""
    rows = slots(data)
    cap = caps(rows)
    budget, rest = boostp_budget(data)
    errors, _ = check(verbose=False)
    failed = {e.split(' ')[0] for e in errors}
    over = {int(e.split()[2].rstrip(':')) for e in errors if e.startswith('boost-p record')}
    cells, skipped = [], 0
    for s in rows:
        if not needs_text(s['jp']):
            continue
        en = text_for(s, names, cap[(s['chunk'], s['col'])])
        if not en:
            continue
        if s['id'] in failed or (s['chunk'] == 'boost-p' and s['record'] in over):
            skipped += 1
            continue
        cells.append({'id': s['id'], 'pointer_offset': s['pointer_offset'], 'old': s['string'],
                      'raw': encode(en), 'english': en})
    return cells, skipped


def patch(original, cells):
    """Append each distinct encoded string once after the pool and repoint the cells.

    Only Spirit cells and SCHEMA cells may change; every other byte of the
    original survives (checked by restoring the pointers and size fields)."""
    chunks = rpw_chunks(original)
    js = next(c for c in chunks if c['name'] == 'j-string')
    allowed = spirit_cells(original) | {s['pointer_offset'] for s in slots(original)}
    where = [c['pointer_offset'] for c in cells]
    if len(where) != len(set(where)):
        raise ValueError('a cell is patched twice')
    if not set(where) <= allowed:
        raise ValueError('cell outside the reviewed pointer columns')
    pool_size = js['body_end'] - js['body_offset']
    base, suffix, placed = bytearray(original), bytearray(), {}
    for c in cells:
        if struct.unpack_from('<I', original, c['pointer_offset'])[0] != c['old']:
            raise ValueError('pointer drift at %s' % c['id'])
        raw = c['raw']
        if not raw or b'\0' in raw:
            raise ValueError('%s encodes to an empty or NUL-bearing string' % c['id'])
        if raw not in placed:
            placed[raw] = pool_size + len(suffix)
            suffix += raw + b'\0'
        struct.pack_into('<I', base, c['pointer_offset'], placed[raw])
    suffix += bytes((-len(suffix)) % 4)
    grow = len(suffix)
    sizes = (24, 28, js['offset'] + 20, js['offset'] + 24)
    for off in sizes:
        struct.pack_into('<I', base, off, struct.unpack_from('<I', original, off)[0] + grow)
    out = bytes(base[:js['body_end']] + suffix + base[js['body_end']:])
    # Readback: structure, the old pool, every new pointer, and nothing else changed.
    new_chunks = rpw_chunks(out)
    if [c['name'] for c in new_chunks] != [c['name'] for c in chunks]:
        raise ValueError('RPW chunk list changed')
    nj = new_chunks[0]
    if out[nj['body_offset']:nj['body_offset'] + pool_size] != original[js['body_offset']:js['body_end']]:
        raise ValueError('original pool bytes changed')
    restored = bytearray(out[:js['body_end']] + out[js['body_end'] + grow:])
    for c in cells:
        at = c['pointer_offset'] + (grow if c['pointer_offset'] >= js['body_end'] else 0)
        ptr = struct.unpack_from('<I', out, at)[0]
        start = nj['body_offset'] + ptr
        if out[start:out.index(b'\0', start)] != c['raw']:
            raise ValueError('readback mismatch at %s' % c['id'])
        struct.pack_into('<I', restored, c['pointer_offset'], c['old'])
    for off in sizes:
        restored[off:off + 4] = original[off:off + 4]
    if bytes(restored) != original:
        raise ValueError('unrelated RPW bytes changed')
    return out, grow


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['slots', 'reuse', 'check', 'export', 'merge'])
    ap.add_argument('--file', help='check one answer slice in work/translation/en/ui/rpw_new/')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    if args.cmd == 'slots':
        rows = slots(load_rpw())
        cap = caps(rows)
        fam = Counter(s['family'] for s in rows if needs_text(s['jp']))
        dist = defaultdict(set)
        for s in rows:
            if needs_text(s['jp']):
                dist[s['family']].add(s['jp'])
        for f in FAMILIES:
            print('%-7s %5d slots, %5d distinct Japanese' % (f, fam[f], len(dist[f])))
        print('caps (bytes):', {'%s:%d' % k: v for k, v in sorted(cap.items())})
    elif args.cmd == 'reuse':
        reuse(args.apply)
    elif args.cmd == 'check' and args.file:
        errs = check_answer(NEW / args.file)
        for e in errs:
            print('ERROR', e)
        print('%s: %d errors' % (args.file, len(errs)))
        return 1 if errs else 0
    elif args.cmd == 'check':
        return 0 if not check()[0] else 1
    elif args.cmd == 'merge':
        merge(args.apply)
    elif args.cmd == 'export':
        export(args.apply)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
