"""Tengoku stage dialogue: map stages, export 80-row briefs, check translations.

    python -m tools.dialogue map                     # story order -> script members
    python -m tools.dialogue export [--apply]        # briefs for the planned stages
    python -m tools.dialogue check [--file X.json]   # validate translations

Records are read from the decoded stage members (plain cp932 Lua). A record's
identity is (member, event, ordinal), as in Jigoku's luarec: text is never a
key, because identical lines recur. Translation files hold English and a
fingerprint of the Japanese only; the Japanese stays in the ignored briefs.

English follows Jigoku's shipped format: the speaker line, then 「speech」.
Translators write the speech in full on one line; the builder wraps it to the
dialogue box (30 fullwidth cells, measured: the game's longest Japanese line),
at most 3 speech lines. `check` reports any record that will not fit.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from tools.common import ROOT, write_json
from tools.library_text import GLOSSARY, TOKEN, Resolver, CHARACTERS

MEMBERS = ROOT / 'work/tengoku/prepared/stage_members'
INDEX = ROOT / 'work/tengoku/prepared/stage_index.json'
BRIEFS = ROOT / 'work/tengoku/dialogue_briefs'
TRANSLATIONS = ROOT / 'work/translation/en/dialogue'
ADVANCES = ROOT / 'work/ui/latin_advances.json'
SHIPPED = Path('E:/Projects/SRW Z3/work/tr/shipped.json')   # Jigoku English by source fingerprint

# Story order, route A = the first option at every choice (flowchart:
# docs/STAGE_ORDER.md). Batch 1: prologues 1-2 and stages 1-8 (2001-2010,
# Green Earth after the 2200 choice). Batch 2: Green stages 9-11, the common
# stages 12-16, the 2210 spacequake choice, Macross Quarter route 17-18.
# Batch 3: MQ 19-20, MQ+Hive 21-22, common 23-25, the 2220 choice, Central
# Continent route 26-28.
# Batch 4: continent 29, common 30-35, the 2230 choice (Japan / Neo Zeon /
# Amalgam), Japan Defense route 36-38.
PLAN = ['2001', '2002', '2003a', '2003b', '2004', '2005', '2200', '2201',
        '2006', '2007', '2008a', '2008b', '2009', '2010a', '2010b',
        '2011', '2012', '2013', '2026a', '2026b', '2027', '2028', '2029', '2030',
        '2210', '2211', '2031a', '2031b', '2032',
        '2033', '2034a', '2034b', '2039', '2040a', '2040b', '2047', '2048', '2049',
        '2220', '2221', '2050', '2051', '2052',
        '2053', '2058', '2059', '2060', '2061', '2062', '2063',
        '2230', '2231', '2064', '2065', '2066',
        '2067', '2068a', '2068b', '2079', '2080', '2240', '2241', '2081',
        '2084', '2085', '2086', '2087', '2088a', '2088b',
        '2089', '2090', '2091', '2250', '2251', '2092', '2093', '2094',
        '2098', '2099', '2100a', '2100b', '2102',
        '2103', '2104', '2105', '2106a', '2106b', '2106c', '2106d',
        # branches (after route A): batch 8 = Blue Earth 4-11, Dragon's Hive 17-20
        '2202', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021',
        '2022', '2023a', '2023b', '2024', '2025',
        '2212', '2213', '2035a', '2035b', '2036', '2037', '2038a', '2038b',
        # batch 9 = Sousuke rescue 17-22, Left-Behind Sea 26-29, remaining choice D-Traders
        '2041a', '2041b', '2041c', '2042a', '2042b', '2043', '2044', '2045', '2046',
        '2222', '2054a', '2054b', '2055', '2056', '2057',
        '2232', '2233', '2242', '2243', '2252',
        # batch 10 = Neo Zeon route 36-40, Amalgam route 36-40
        '2069', '2070', '2071', '2072', '2073', '2074', '2075', '2076', '2077', '2078',
        # batch 11 = Crowe 43, Char 43, Macross Quarter 52-54, despair 57
        '2082a', '2082b', '2083', '2095', '2096', '2097', '2101a', '2101b',
        # batch 12 = outside the story: ace pilot talks, guidance scenario, next-episode previews
        '2500', '2600', '2700']
SLICE = 80
BOX_UNITS = 30 * 32
MAX_SPEECH_LINES = 3
PROTAGONIST_UNITS = 8 * 18        # $n budgeted as 8 average letters, as in Jigoku
FULLWIDTH = 32

# Record grammar ported from Jigoku tools/luarec.py (same Lua layout in Tengoku).
BLOCK = re.compile(r'(?<!--)\[\[(.*?)\]\]', re.S)
EVENT = re.compile(r'^(t_\d+)\s*=\s*\{(.*?)^\};', re.M | re.S)
HEAD = re.compile(r'\{\s*(\w+)\s*,\s*(\d+)\s*,\s*(\w+)\s*,\s*(pid_\w+)\s*,\s*$', re.M)
CODES = re.compile(r'(?<!\$)\$[nlFcf](?!\$)')
LINK = re.compile(r'《(.*?)》')


def digest(jp):
    """Jigoku-compatible fingerprint (sha1 of the LF text, 10 hex)."""
    return hashlib.sha1(jp.replace('\r\n', '\n').encode('utf-8')).hexdigest()[:10]


def member_text(mid):
    return (MEMBERS / ('%05d.bin' % mid)).read_bytes().decode('cp932')


def records(mid):
    text = member_text(mid)
    ident = {}
    for ev in EVENT.finditer(text):
        for n, m in enumerate(BLOCK.finditer(ev.group(2))):
            ident[ev.start(2) + m.start()] = (ev.group(1), n)
    out = []
    for m in BLOCK.finditer(text):
        event, n = ident.get(m.start(), (None, None))
        head = HEAD.search(text, max(0, m.start() - 160), m.start())
        if event is None or head is None:
            continue          # not a dialogue record (e.g. a background-name literal)
        jp = m.group(1).replace('\r\n', '\n')
        out.append({'id': '%d:%s:%d' % (mid, event, n), 'member': mid, 'event': event, 'n': n,
                    'wpos': head.group(1), 'face': int(head.group(2)), 'pid': head.group(4),
                    'jp': jp, 'sha': digest(jp)})
    return out


def stage_members():
    index = json.loads(INDEX.read_text(encoding='utf-8'))
    hint = {h: m['member_id'] for m in index['members'] for h in (m.get('scene_hints') or [])}
    return {s: [hint[s + k] for k in ('_SDemo', '_DlgEv') if s + k in hint] for s in PLAN}


def plan_rows():
    rows = []
    for stage, mids in stage_members().items():
        for mid in mids:
            for r in records(mid):
                r['stage'] = stage
                rows.append(r)
    return rows


def chapter(stage):
    """Map halves (2003a/b) and a route-choice scene with its D-Trader (2200/2201) to one chapter."""
    return stage[:3] + '0' if stage.startswith('22') else stage.rstrip('abcd')


def slices(rows):
    """80-row slices that never cross a chapter boundary."""
    out, current, key = [], [], None
    for r in rows:
        if current and (chapter(r['stage']) != key or len(current) == SLICE):
            out.append(current)
            current = []
        key = chapter(r['stage'])
        current.append(r)
    if current:
        out.append(current)
    named = []
    for i, s in enumerate(out):
        c = chapter(s[0]['stage'])
        named.append(('dlg_%s_%02d' % (c, sum(1 for x in out[:i] if chapter(x[0]['stage']) == c)), s))
    return named


# ------------------------------------------------------------------ width

class Width:
    def __init__(self, resolver):
        self.adv = json.loads(ADVANCES.read_text(encoding='utf-8'))['advances']
        self.resolver = resolver

    def text(self, s):
        return sum(self.adv.get(c, FULLWIDTH) for c in s)

    def expand(self, s):
        def sub(m):
            t, _ = self.resolver.resolve(m.group(1))
            en = (t['en'] if t and t['en'] else m.group(1))
            return en[0].lower() + en[1:] if m.group(2) else en
        return TOKEN.sub(sub, s)

    def wrap(self, speech):
        """Lines of the speech after wrapping; $n counts as PROTAGONIST_UNITS."""
        words = self.expand(speech).split(' ')
        lines, line, used = [], '', 0
        for word in words:
            w = self.text(word.replace('$n', '')) + word.count('$n') * PROTAGONIST_UNITS
            gap = self.adv[' '] if line else 0
            lead = FULLWIDTH if lines else 0          # continuation lines start with
            if line and used + gap + w > BOX_UNITS - lead:
                lines.append(line)
                line, used = word, w
            else:
                line, used = (line + ' ' + word) if line else word, used + gap + w
        lines.append(line)
        return lines


# ------------------------------------------------------------------ names

def speaker_options(jp, resolver):
    """Accepted English speaker lines for a record's first line, and their status.

    Several options when one Japanese name is several glossary terms (レイ):
    the translator picks by pid and scene; `check` accepts any of them.
    """
    first = jp.split('\n', 1)[0]
    if '$' in first or not first.strip('　 '):
        return [first], 'code'
    if set(first) <= set('？?'):
        return ['?' * len(first)], 'literal'
    t, problem = resolver.resolve(first)
    if t and t['en']:
        return ['$$%s$$' % t['token']], 'glossary'
    options = ['$$%s$$' % c['token'] for c in resolver.bare.get(first, []) if c['en']]
    if options:
        return options, 'choose'
    return ['$$%s$$' % first], 'missing'


def genders():
    chars = json.loads(CHARACTERS.read_text(encoding='utf-8'))['characters']
    out = {}
    for c in chars.values():
        for token in c.get('tokens', {}).values():
            out[token] = c.get('gender')
    return out


# ------------------------------------------------------------------ export

def export(apply):
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    gender = genders()
    shipped = json.loads(SHIPPED.read_text(encoding='utf-8')) if SHIPPED.exists() else {}
    rows = plan_rows()
    groups = slices(rows)
    done = {}
    for path in sorted(TRANSLATIONS.glob('*.json')):
        for rid, entry in json.loads(path.read_text(encoding='utf-8')).get('rows', {}).items():
            done.setdefault(entry['sha'], (rid, entry['en']))
    print('%d records in %d stages -> %d slices' % (len(rows), len(PLAN), len(groups)))
    reuse = sum(1 for r in rows if r['sha'] in shipped)
    missing = Counter()
    for name, group in groups:
        stage_rows = [r for r in rows if r['stage'] == group[0]['stage']]
        out = ['# Dialogue brief %s (stage %s, %d rows)' % (name, group[0]['stage'], len(group)), '',
               'Write `work/translation/en/dialogue/%s.json`. Read `docs/DIALOGUE_STYLE.md` first.' % name,
               'Neighbouring slices: other `dlg_%s_*.md` briefs in this folder.' % group[0]['stage'], '']
        for r in group:
            options, status = speaker_options(r['jp'], resolver)
            if status == 'missing':
                missing[r['jp'].split('\n', 1)[0]] += 1
            shown = []
            for option in options:
                t, _ = resolver.resolve(option.strip('$')) if option.startswith('$$') else (None, None)
                shown.append('`%s`%s' % (option, ' = %s%s' % (t['en'], ' [%s]' % gender[t['token']]
                                                                 if t['token'] in gender else '') if t else ''))
            out += ['## %s' % r['id'], '',
                    '- speaker line: %s (%s); pid %s, %s, face %d' % (' OR '.join(shown), status, r['pid'], r['wpos'], r['face']),
                    '- sha: `%s`; links 《》: %d; codes: %s' % (r['sha'], len(LINK.findall(r['jp'])),
                                                           ' '.join(CODES.findall(r['jp'])) or '-'),
                    '', '```', r['jp'], '```']
            if r['sha'] in done and done[r['sha']][0] != r['id']:
                out += ['', 'Tengoku English already written for identical Japanese (%s; reuse it if it fits):' % done[r['sha']][0],
                        '', '```', done[r['sha']][1], '```']
            if r['sha'] in shipped:
                out += ['', 'Jigoku English (identical Japanese; verify it fits this scene):', '',
                        '```', shipped[r['sha']]['en'], '```']
            out.append('')
        if apply:
            BRIEFS.mkdir(parents=True, exist_ok=True)
            with (BRIEFS / (name + '.md')).open('w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(out) + '\n')
    print('rows with identical Jigoku English: %d' % reuse)
    print('speakers not in the glossary: %d distinct, e.g. %s' % (len(missing), ', '.join(k for k, _ in missing.most_common(20))))
    print('slices: ' + ' '.join(n for n, _ in groups))
    print('Wrote briefs to %s' % BRIEFS if apply else 'DRY RUN: no briefs written')


# ------------------------------------------------------------------ check

def speech_blocks(jp):
    """Number of separate 「...」 blocks in a record (e.g. one line per route branch)."""
    return sum(1 for line in jp.split('\n')[1:] if line.startswith('「'))


def check(only=None):
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    width = Width(resolver)
    rows = {r['id']: r for r in plan_rows()}
    errors, long_rows, missing, done = [], [], set(), set()
    for path in sorted(TRANSLATIONS.glob('*.json')):
        if only and path.name != only:
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        for rid, entry in data.get('rows', {}).items():
            where = '%s %s' % (path.name, rid)
            if rid in done:
                errors.append(where + ': defined twice')
            done.add(rid)
            r = rows.get(rid)
            if r is None:
                errors.append(where + ': unknown record id')
                continue
            if entry.get('sha') != r['sha']:
                errors.append(where + ': Japanese changed (sha mismatch)')
            en = entry.get('en') or ''
            head, _, body = en.partition('\n')
            options, status = speaker_options(r['jp'], resolver)
            if head not in options:
                errors.append('%s: speaker line %r, expected %s' % (where, head, ' or '.join(options)))
            # A caption (no speaker, centred with fullwidth spaces) keeps its line layout.
            caption = status == 'code' and not head.strip('　 ')
            speech = body.replace('\n', ' ').strip()
            blocks = speech_blocks(r['jp'])
            if not caption:
                parts = body.split('\n')
                if blocks > 1 and len(parts) != blocks:
                    errors.append(where + ': the Japanese has %d 「...」 blocks; write each on its own line' % blocks)
                elif blocks <= 1 and '\n' in body:
                    errors.append(where + ': write the speech on one line; the builder wraps it')
                elif r['jp'].split('\n', 1)[-1].startswith('「') and not all(
                        x.strip().startswith('「') and x.strip().endswith('」') for x in parts):
                    errors.append(where + ': speech must be one 「...」 block per Japanese block')
            elif en.count('\n') != r['jp'].count('\n'):
                errors.append(where + ': a caption keeps the Japanese line count')
            bare = TOKEN.sub('', en)
            if '$$' in bare:
                errors.append(where + ': malformed $$ token')
            allowed = '「」《》　' + ('～' if caption else '')
            # This CP932 glyph is used as a decoration in five source rows.
            # Preserve its original code point; its visual meaning is unverified.
            source_glyphs = '\u0431'
            allowed += ''.join(c for c in source_glyphs if c in r['jp'])
            for glyph in source_glyphs:
                if bare.count(glyph) != r['jp'].count(glyph):
                    errors.append(where + ': source glyph U+%04X count differs' % ord(glyph))
            odd = sorted({c for c in bare if ord(c) > 126 and c not in allowed or (ord(c) < 32 and c != '\n')})
            if odd:
                errors.append('%s: non-ASCII %s' % (where, ''.join(odd)))
            if Counter(CODES.findall(bare)) != Counter(CODES.findall(r['jp'])):
                errors.append('%s: control codes %s, Japanese has %s' % (where, CODES.findall(bare), CODES.findall(r['jp'])))
            if len(LINK.findall(en)) != len(LINK.findall(r['jp'])):
                errors.append('%s: %d 《》 links, Japanese has %d' % (where, len(LINK.findall(en)), len(LINK.findall(r['jp']))))
            if ']]' in en:
                errors.append(where + ': ]] would end the Lua string')
            for m in TOKEN.finditer(en):
                t, problem = resolver.resolve(m.group(1))
                if problem and 'not in the library glossary' in problem:
                    missing.add(m.group(1))
                elif problem:
                    errors.append('%s: %s' % (where, problem))
            lines = [l for part in body.split('\n') for l in width.wrap(part.strip().strip('「」'))] \
                if speech and not caption else []
            if len(lines) > MAX_SPEECH_LINES:
                long_rows.append('%s: %d lines (max %d)' % (where, len(lines), MAX_SPEECH_LINES))
    total = len(rows)
    print('translated %d / %d records' % (len(done & set(rows)), total))
    if missing:
        print('names not in the glossary (%d): %s' % (len(missing), ', '.join(sorted(missing))))
    for line in long_rows[:60]:
        print('TOO LONG ' + line)
    for e in errors[:80]:
        print('ERROR ' + e)
    print('OK' if not errors else '%d errors' % len(errors))
    return not errors


# Literal forms the name pass must not tokenize, with the reason.
NAME_SKIP = {
    'Lion': {'480:t_000:2', '480:t_000:4', '480:t_000:34', '480:t_000:35'},  # ordinary lion/machine shape, not the Macross song
    'Fire': {'64:t_104:4', '70:t_004:3', '224:t_10:52'},  # Breast Fire / Basara's shout, not Noin's codename
    'Gundam': None,   # generic "that Gundam", not one machine
    'Boss': {'4:t_111:2', '39:t_2:10', '46:t_102:5', '201:t_033:0',  # Bobby's ボス = Jeffrey, not Boss
             '330:t_017:3', '330:t_017:7', '330:t_103:1',   # Dove's ボス = Beck
             '677:t_026:1'},
    'Princess': None,   # 姫 is an "ambiguous" glossary entry; keep the plain word
    'Pirate': None,   # generic speaker token; Lukkage's "Great Pirate" title stays plain
    'Queen': None,   # Ziene's code name; Guin's "Queen Relena" is a title
    'Someone': None,   # generic speaker token
    'Mars': {'853:t_97:7'},   # Aquarion's Vector halves, not Takeru / Luna Maria
    'Luna': {'853:t_97:7'},
}


def names(apply, sample=15):
    """Turn literal English names in speech into glossary tokens.

    As the library name script: a literal becomes a token only where the
    record's own Japanese contains the term's Japanese and exactly one token
    fits; lower-case forms only when they equal the current English. Speaker
    lines are left alone (the checker pins them). Also drops a duplicated
    article before a token whose English starts with 'the'.
    """
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    by_token = {t['token']: t for t in terms}
    variants = {}
    for t in terms:
        if t['en'] and t['status'] != 'pending' and len(t['en']) >= 3:
            variants.setdefault(t['en'], set()).add(t['token'])
    forms = sorted(variants, key=len, reverse=True)
    pattern = re.compile(r"(?<![A-Za-z0-9$'-])(%s)(?![A-Za-z0-9-])" % '|'.join(re.escape(f) for f in forms))
    the_tokens = {t['token'] for t in terms if (t['en'] or '').lower().startswith('the ')}
    rows = {r['id']: r for r in plan_rows()}
    per_form, examples, files = Counter(), [], {}
    for path in sorted(TRANSLATIONS.glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        dirty = False
        for rid, entry in data.get('rows', {}).items():
            japanese = rows[rid]['jp'].split('\n', 1)[-1]
            head, sep, body = entry['en'].partition('\n')
            pieces = re.split(r'(\$\$[^$]+\$\$|\$[nlFcf])', body)
            for i in range(0, len(pieces), 2):
                def swap(m):
                    form = m.group(1)
                    if form in NAME_SKIP and (NAME_SKIP[form] is None or rid in NAME_SKIP[form]):
                        return m.group(0)
                    options = [tk for tk in variants[form] if by_token[tk]['jp'] in japanese
                               and (form[0].isupper() or by_token[tk]['en'] == form)]
                    if len(options) != 1:
                        return m.group(0)
                    per_form[form] += 1
                    return '$$%s$$' % options[0]
                pieces[i] = pattern.sub(swap, pieces[i])
            new = ''.join(pieces)
            for token in the_tokens:
                new = re.sub(r'\b[Tt]he \$\$%s(\|lc)?\$\$' % re.escape(token), '$$%s\\1$$' % token, new)
            if new != body:
                if len(examples) < sample:
                    examples.append((path.name, rid, body, new))
                entry['en'], dirty = head + sep + new, True
        if dirty:
            files[path] = data
    print('records changed in %d files; literal names tokenized: %d' % (len(files), sum(per_form.values())))
    print('most frequent: ' + ', '.join('%s x%d' % kv for kv in per_form.most_common(30)))
    for name, rid, before, after in examples:
        print('%s %s: %s\n    -> %s' % (name, rid, before, after))
    if apply:
        for path, data in files.items():
            write_json(path, data)
        print('Wrote %d files' % len(files))
    else:
        print('DRY RUN: no files written')

    return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('map', 'export', 'check', 'names'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--file')
    args = parser.parse_args()
    if args.command == 'map':
        for stage, mids in stage_members().items():
            n = sum(len(records(m)) for m in mids)
            print('%-6s members %-10s records %d' % (stage, mids, n))
    elif args.command == 'export':
        export(args.apply)
    elif args.command == 'names':
        names(args.apply)
    else:
        raise SystemExit(0 if check(args.file) else 1)


if __name__ == '__main__':
    main()
