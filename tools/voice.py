"""Battle voice translations: reuse Jigoku English and check answer files.

    python -m tools.voice reuse [--apply]    # Jigoku TM -> work/translation/en/voice/<group>.json
    python -m tools.voice check              # validate every answer file against the pristine SRVC

Answer file (docs/BATTLE_VOICE.md, "Proposed translation workflow"):
    {"schema": 1, "group": "g002", "blocks": [2, 3], "speaker": {...},
     "lines": {"<block>:<pool offset>": {"jp": "...", "en": "...", "source": "jigoku|new", ...}}}
`en` is the text as it will appear in game, with the Japanese bracket form
mirrored (「...」 kept, （...） -> (...)). Names are glossary `$$tokens$$`.
Inputs come from `python -m tools.voice_bind` / `tools.voice_tm` (work/tengoku/voice/).
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict

from tools.common import ROOT, write_json
from tools.library_text import GLOSSARY, TOKEN, Resolver

VOICE = ROOT / 'work/tengoku/voice'
ANSWERS = ROOT / 'work/translation/en/voice'
NEW = ROOT / 'work/translation/en/voice_new'        # agents' slice answers
BRIEFS = ROOT / 'work/tengoku/voice_briefs'
SLICE = 80

OPEN = {'「': '「', '（': '('}
CLOSE = {'」': '」', '）': ')'}


def load():
    lines = json.loads((VOICE / 'lines.json').read_text(encoding='utf-8'))['lines']
    blocks = json.loads((VOICE / 'blocks.json').read_text(encoding='utf-8'))['blocks']
    tm = json.loads((VOICE / 'tm.json').read_text(encoding='utf-8'))['matches']
    return lines, blocks, tm


def is_placeholder(jp):
    from tools.voice_bind import is_sentinel
    return is_sentinel(jp)


def strings_by_block(lines):
    """{block: {string id: {'jp', 'slots': set}}} for every referenced string."""
    out = defaultdict(dict)
    for l in lines:
        b = int(l['string'].split(':')[0])
        s = out[b].setdefault(l['string'], {'jp': l['jp'], 'slots': set()})
        for slot in l.get('slots') or []:
            s['slots'].add(slot[1])
    return out


def group_key(block):
    return 'g%03d' % block['group'][0]


def bracket(jp, en):
    """Mirror the Japanese bracket form onto bare English."""
    en = en.strip()
    for o in ('「', '(', '（'):
        if en.startswith(o):
            return en                       # already bracketed
    head = OPEN.get(jp[:1], '')
    tail = CLOSE.get(jp[-1:], '')
    return head + en + tail


class Namer:
    """Literal English names -> glossary tokens, where the line's Japanese has the term."""

    def __init__(self, terms):
        self.variants = defaultdict(set)
        self.jp = {}
        for t in terms:
            if t.get('en') and t.get('status') != 'pending' and len(t['en']) >= 3 and t.get('kind') != 'pilot_generic':
                self.variants[t['en']].add(t['token'])
                self.jp[t['token']] = t['jp']
        forms = sorted(self.variants, key=len, reverse=True)
        self.pattern = re.compile(r"(?<![A-Za-z0-9$'-])(%s)(?![A-Za-z0-9-])" % '|'.join(re.escape(f) for f in forms))
        self.skip = {'Gundam', 'Boss', 'Princess', 'Pirate', 'Queen', 'Someone'}

    def apply(self, en, jp):
        def swap(m):
            form = m.group(1)
            if form in self.skip:
                return m.group(0)
            options = [tk for tk in self.variants[form] if self.jp[tk] in jp]
            return '$$%s$$' % options[0] if len(options) == 1 else m.group(0)
        pieces = re.split(r'(\$\$[^$]+\$\$)', en)
        for i in range(0, len(pieces), 2):
            pieces[i] = self.pattern.sub(swap, pieces[i])
        return ''.join(pieces)


def reuse(apply):
    lines, blocks, tm = load()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    namer = Namer(terms)
    by_block = strings_by_block(lines)
    groups = defaultdict(list)
    for b in blocks:
        if b['lines']:
            groups[group_key(b)].append(b)
    stats = Counter()
    written = 0
    for key, members in sorted(groups.items()):
        path = ANSWERS / (key + '.json')
        existing = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        old = existing['lines'] if existing else {}
        lead = members[0].get('jigoku') or {}
        section = lead.get('section') if (lead.get('fraction') or 0) >= 0.5 else None
        out = dict(old)
        for b in members:
            for sid, s in sorted(by_block[b['block']].items()):
                jp = s['jp']
                if sid in old and old[sid].get('source') != 'jigoku':
                    stats['kept human answer'] += 1
                    continue
                if is_placeholder(jp):
                    stats['placeholder'] += 1
                    continue
                cands = tm.get(jp)
                if not cands:
                    stats['fresh'] += 1
                    continue
                pick = [c for c in cands if section is not None and section in c['jigoku_sections']]
                conflict = len(cands) > 1
                chosen = (pick or cands)[0]
                entry = {'jp': jp, 'en': namer.apply(bracket(jp, chosen['en']), jp), 'source': 'jigoku',
                         'slots': sorted(s['slots'])}
                if conflict:
                    entry['alternatives'] = [c['en'] for c in cands if c is not chosen]
                    entry['review'] = 'same-speaker' if pick else 'conflict'
                    stats['conflict' if not pick else 'multi, same speaker chosen'] += 1
                stats['reused'] += 1
                out[sid] = entry
        speaker = (existing or {}).get('speaker') or {
            'token': (lead.get('tokens') or [None])[0], 'jigoku_pilot': lead.get('pilot'),
            'jigoku_unit': lead.get('unit'), 'fraction': lead.get('fraction'), 'basis': 'jigoku section match (unreviewed)'}
        doc = {'schema': 1, 'group': key, 'blocks': [b['block'] for b in members], 'speaker': speaker,
               'lines': dict(sorted(out.items(), key=lambda kv: tuple(map(int, kv[0].split(':')))))}
        if out and apply:
            write_json(path, doc)
            written += 1
    print(', '.join('%s %d' % kv for kv in sorted(stats.items())))
    print('groups with reuse: %d%s' % (written, '' if apply else ' (DRY RUN, pass --apply)'))


BREAK = '\\n'          # the game's literal two-character line break
SEGMENT = 36           # characters per segment, Jigoku's measured practice (runtime unverified)


def expand_len(text, resolver):
    """Display length with tokens replaced by their English."""
    def sub(m):
        t, _problem = resolver.resolve(m.group(1))
        return (t or {}).get('en') or m.group(1)
    return TOKEN.sub(sub, text)


def validate(where, jp, en, resolver, errors, missing, review):
    if jp[:1] in OPEN and not en.startswith(OPEN[jp[:1]]):
        errors.append(where + ': must open with %s like the Japanese' % OPEN[jp[:1]])
    if jp[-1:] in CLOSE and not en.endswith(CLOSE[jp[-1:]]):
        errors.append(where + ': must close with %s like the Japanese' % CLOSE[jp[-1:]])
    bare = TOKEN.sub('', en)
    if '$$' in bare:
        errors.append(where + ': malformed $$ token')
    odd = sorted({c for c in bare if (ord(c) > 126 and c not in '「」') or ord(c) < 32})
    if odd:
        errors.append('%s: non-ASCII %r (use \\n, two characters, for a break)' % (where, ''.join(odd)))
    if en.count(BREAK) != jp.count(BREAK):
        errors.append('%s: %d line breaks, the Japanese has %d' % (where, en.count(BREAK), jp.count(BREAK)))
    for m in TOKEN.finditer(en):
        _t, problem = resolver.resolve(m.group(1))
        if problem and 'not in the library glossary' in problem:
            missing.add(m.group(1))
        elif problem:
            errors.append('%s: %s' % (where, problem))
    shown = expand_len(en, resolver).strip('「」()')
    for seg in shown.split(BREAK):
        if len(seg.strip()) > SEGMENT:
            review['LONG %s: %d chars' % (where, len(seg.strip()))] += 1


def check(only=None):
    lines, blocks, _tm = load()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    by_block = strings_by_block(lines)
    known = {sid: s['jp'] for b in by_block.values() for sid, s in b.items()}
    errors, missing, done, review = [], set(), set(), Counter()
    if only:
        path = NEW / only
        data = json.loads(path.read_text(encoding='utf-8'))
        for sid, e in data.get('rows', {}).items():
            where = '%s %s' % (path.name, sid)
            if sid not in known:
                errors.append(where + ': unknown string id')
                continue
            if e.get('jp') != known[sid]:
                errors.append(where + ': Japanese differs from the game file')
            validate(where, known[sid], e.get('en') or '', resolver, errors, missing, review)
        brief = BRIEFS / (path.stem + '.md')
        if brief.exists():
            wanted = set(re.findall(r'^## (\d+:\d+)$', brief.read_text(encoding='utf-8'), re.M))
            gone = wanted - set(data.get('rows', {}))
            if gone:
                errors.append('%d rows of the brief are not translated, e.g. %s' % (len(gone), sorted(gone)[0]))
        print('%s: %d rows' % (path.name, len(data.get('rows', {}))))
    for path in ([] if only else sorted(ANSWERS.glob('*.json'))):
        data = json.loads(path.read_text(encoding='utf-8'))
        for sid, e in data.get('lines', {}).items():
            where = '%s %s' % (path.name, sid)
            if sid in done:
                errors.append(where + ': defined twice')
            done.add(sid)
            if sid not in known:
                errors.append(where + ': unknown string id')
                continue
            if e.get('jp') != known[sid]:
                errors.append(where + ': Japanese differs from the game file')
            validate(where, known[sid], e.get('en') or '', resolver, errors, missing, review)
            if e.get('review'):
                review['review: ' + e['review']] += 1
    total = sum(1 for sid, jp in known.items() if not is_placeholder(jp))
    if not only:
        print('translated %d / %d block strings (placeholder excluded)' % (len(done & set(known)), total))
    longs = [k for k in review if k.startswith('LONG')]
    for k in longs[:40]:
        print(k)
    if longs:
        print('LONG segments (> %d chars, runtime limit unverified): %d' % (SEGMENT, len(longs)))
    review = Counter({k: v for k, v in review.items() if not k.startswith('LONG')})
    for k, v in sorted(review.items()):
        print('note %s: %d' % (k, v))
    if missing:
        print('names not in the glossary (%d): %s' % (len(missing), ', '.join(sorted(missing))))
    for e in errors[:80]:
        print('ERROR ' + e)
    print('OK' if not errors else '%d errors' % len(errors))
    return not errors


def group_jobs():
    """{group key: (members, [(rep sid, jp, slots, sids)] still untranslated)} in slot order."""
    lines, blocks, _tm = load()
    by_block = strings_by_block(lines)
    groups = defaultdict(list)
    for b in blocks:
        if b['lines']:
            groups[group_key(b)].append(b)
    jobs = {}
    for key, members in sorted(groups.items()):
        path = ANSWERS / (key + '.json')
        done = json.loads(path.read_text(encoding='utf-8'))['lines'] if path.exists() else {}
        rows = {}
        for b in members:
            for sid, s in sorted(by_block[b['block']].items(), key=lambda kv: int(kv[0].split(':')[1])):
                if sid in done or is_placeholder(s['jp']):
                    continue
                r = rows.setdefault(s['jp'], {'sid': sid, 'slots': set(), 'sids': []})
                r['slots'] |= s['slots']
                r['sids'].append(sid)
        jobs[key] = (members, rows, done)
    return jobs


SLOT_ORDER = None


def slot_rank(labels, blocks_doc):
    order = {v['label']: int(k) for b in blocks_doc for k, v in b['slots'].items()}
    return min((order.get(l, 99) for l in labels), default=99)


def _set_header(key, members, done):
    lead = members[0]
    jig = lead.get('jigoku') or {}
    out = ['## Voice set %s' % key, '',
           '- Blocks: %s' % ', '.join(str(b['block']) for b in members),
           '- Jigoku identification: pilot %s, unit %s, %s of lines shared%s' % (
               jig.get('pilot') or '-', jig.get('unit') or '-',
               ('%d/%d' % (jig['shared'], jig['of'])) if jig.get('of') else 'none',
               ('; tokens %s' % ', '.join('`$$%s$$`' % t for t in jig['tokens'])) if jig.get('tokens') else ''),
           '- Jigoku note: %s' % (jig.get('why') or '-'),
           '- Names spoken in the lines: %s' % (', '.join('%s x%d' % (x['jp'], x['count']) for x in lead.get('spoken', [])[:15]) or '-'),
           '- Weapon-name leads: %s' % (', '.join(str(w.get('jp', w)) if isinstance(w, dict) else str(w) for w in lead.get('weapons', [])[:12]) or '-'),
           '']
    ref = [(e['jp'], e['en']) for e in done.values()][:40]
    if ref:
        out += ['### Already translated lines of %s (match their voice and names)' % key, '']
        out += ['- %s -> %s' % (j, e) for j, e in ref]
        out.append('')
    return out


def _rows(part):
    out = []
    for jp, r in part:
        out += ['## %s' % r['sid'], '',
                '- situation: %s; same line also used in %d other block string(s)' % (', '.join(sorted(r['slots'])) or '?', len(r['sids']) - 1),
                '', '```', jp, '```', '']
    return out


def export(apply):
    jobs = group_jobs()
    units = []                                   # (name, [(key, part)])
    small, mix = [], 0
    for key, (members, rows, done) in jobs.items():
        if not rows:
            continue
        items = sorted(rows.items(), key=lambda kv: (slot_rank(kv[1]['slots'], members), int(kv[1]['sid'].split(':')[0]), int(kv[1]['sid'].split(':')[1])))
        if len(items) < 20:
            small.append((key, items))
            continue
        for n in range(0, len(items), SLICE):
            units.append(('v_%s_%02d' % (key, n // SLICE), [(key, items[n:n + SLICE])]))
    batch = []
    for key, items in small:
        if batch and sum(len(i) for _, i in batch) + len(items) > SLICE:
            units.append(('v_mix_%02d' % mix, batch)); mix += 1; batch = []
        batch.append((key, items))
    if batch:
        units.append(('v_mix_%02d' % mix, batch))
    total, briefs = 0, []
    for name, sets in units:
        rows = sum(len(p) for _, p in sets)
        total += rows
        out = ['# Battle voice brief %s (%d rows, voice set%s %s)' % (name, rows, '' if len(sets) == 1 else 's', ', '.join(k for k, _ in sets)), '',
               'Write `work/translation/en/voice_new/%s.json`. Read `docs/BATTLE_VOICE_STYLE.md` first.' % name, '']
        for key, part in sets:
            members, _r, done = jobs[key]
            out += _set_header(key, members, done)
            out += ['### Rows of %s' % key, ''] + _rows(part)
        briefs.append((name, '\n'.join(out)))
    if apply:
        BRIEFS.mkdir(parents=True, exist_ok=True)
        for old in BRIEFS.glob('v_*.md'):
            old.unlink()
        for name, text in briefs:
            (BRIEFS / (name + '.md')).write_bytes(text.encode('utf-8'))
    print('%d rows in %d briefs%s' % (total, len(briefs), '' if apply else ' (DRY RUN)'))
    print(' '.join(n for n, _ in briefs))


def merge(apply):
    jobs = group_jobs()
    lines, _b, _tm = load()
    jp_of = {l['string']: l['jp'] for l in lines}
    n = Counter()
    group_of = {b['block']: k for k, (members, _r, _d) in jobs.items() for b in members}
    per_group = defaultdict(dict)
    speakers = defaultdict(dict)
    for path in sorted(NEW.glob('v_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        for sid, e in data.get('rows', {}).items():
            per_group[group_of.get(int(sid.split(':')[0]))][sid] = (e, path.stem)
        for k, sp in (data.get('speakers') or {}).items():
            speakers[k][path.stem] = sp
    for key, rows in sorted(per_group.items()):
        if key is None:
            n['skipped (unknown block)'] += len(rows)
            continue
        members, _rows, _done = jobs[key]
        data = {'rows': {sid: e for sid, (e, _src) in rows.items()}}
        src_of = {sid: src for sid, (_e, src) in rows.items()}
        target = ANSWERS / (key + '.json')
        doc = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {
            'schema': 1, 'group': key, 'blocks': [b['block'] for b in members], 'speaker': {}, 'lines': {}}
        sids_by_jp = defaultdict(list)
        for b in members:
            for sid, jp in jp_of.items():
                if int(sid.split(':')[0]) == b['block']:
                    sids_by_jp[jp].append(sid)
        for sid, e in data.get('rows', {}).items():
            jp = jp_of.get(sid)
            if jp is None or e.get('jp') != jp:
                n['skipped (id/jp mismatch)'] += 1
                continue
            for s in sids_by_jp[jp]:
                cur = doc['lines'].get(s)
                if cur and cur.get('source') not in (None, 'new'):
                    continue
                doc['lines'][s] = {'jp': jp, 'en': e['en'], 'source': 'new', 'slice': src_of[sid]}
                n['merged'] += 1
        for src, sp in speakers.get(key, {}).items():
            doc.setdefault('speaker', {})['proposed_by_' + src] = sp
        doc['lines'] = dict(sorted(doc['lines'].items(), key=lambda kv: tuple(map(int, kv[0].split(':')))))
        if apply:
            write_json(target, doc)
    print(', '.join('%s %d' % kv for kv in sorted(n.items())) or 'nothing to merge', '' if apply else '(DRY RUN)')


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('reuse')
    r.add_argument('--apply', action='store_true')
    c = sub.add_parser('check')
    c.add_argument('--file', help='check one slice in work/translation/en/voice_new/')
    for name in ('export', 'merge'):
        x = sub.add_parser(name)
        x.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd in ('reuse', 'export', 'merge'):
        {'reuse': reuse, 'export': export, 'merge': merge}[a.cmd](a.apply)
        return 0
    return 0 if check(a.file) else 1


if __name__ == '__main__':
    sys.exit(main())
