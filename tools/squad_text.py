"""Team / squad / faction names in the stage scripts, and the combined stage-literal rebuild.

    python -m tools.squad_text inventory          # names, contexts, members
    python -m tools.squad_text seed [--apply]     # research suggestions -> squad_names.json (new names only)
    python -m tools.squad_text check              # coverage, characters, byte limit

The names are display text only (work/tengoku/research/squad_names.md): no
script compares them, teams are identified by number, and the engine copies
a name by value into a 96-byte team field (a save snapshot keeps 64 bytes).
So the literals are rewritten in place, the same English in every member.
In scope: ENEMY_TBL team-name fields, TOUROKU team-build / no-sortie names and
the name argument of SC_UNIT_JOIN_TO_TAG / SC_TAGCTRL_SET_TAGNAME, found by
syntactic context with a byte-level Lua 5.1 scan (ported from the research
scanner). Mission strings (OPERATE_TBL) are tools/mission_text.py; one
rebuild here applies both, because 110 members hold both.
"""
import argparse
import json
import re
from collections import Counter, defaultdict

from tools.common import ROOT, write_json
from tools import dialogue as dlg
from tools import mission_text as mt

TRANSLATION = ROOT / 'work/translation/en/ui/squad_names.json'
RESEARCH = ROOT / 'work/tengoku/research/squad_names.json'
MAX_BYTES = 62                 # encoded, without NUL: fits the 64-byte save copy and the 96-byte team field
IDENT = re.compile(rb'[A-Za-z_][A-Za-z0-9_]*')
KEYWORDS = {b'then', b'do', b'end', b'else', b'elseif', b'return', b'local', b'if', b'and', b'or', b'not',
            b'while', b'for', b'in', b'function', b'repeat', b'until'}
SCOPE_TABLES = ('ENEMY_TBL', 'TOUROKU')
SCOPE_CALLS = ('SC_UNIT_JOIN_TO_TAG', 'SC_TAGCTRL_SET_TAGNAME')


def scan(raw):
    """Every "..." / '...' literal outside comments and [[...]], with its enclosing table/call names.

    Returns [{'start', 'end', 'raw', 'ctx': [(kind, name, index), ...]}] (body span, outermost first)."""
    i, n = 0, len(raw)
    stack, lits = [], []
    last_ident = pending = prev = None
    while i < n:
        c = raw[i]
        if c == 0x2D and raw[i:i + 2] == b'--':
            if raw[i + 2:i + 4] == b'[[':
                i = raw.find(b']]', i + 4) + 2
            else:
                j = raw.find(b'\n', i)
                i = n if j < 0 else j + 1
            continue
        if c == 0x5B and raw[i:i + 2] == b'[[':
            i = raw.find(b']]', i + 2) + 2
            prev = 'long'
            continue
        if c in (0x22, 0x27):
            j = i + 1
            while raw[j] != c:
                j += 2 if raw[j] == 0x5C else 1
            lits.append({'start': i + 1, 'end': j, 'raw': raw[i + 1:j], 'ctx': [tuple(s) for s in stack]})
            prev = 'str'
            i = j + 1
            continue
        if c == 0x7B:
            name = pending if prev == '=' else None
            stack.append(['{', name, 0])
            prev = '{'
        elif c == 0x28:
            stack.append(['(', last_ident if prev == 'ident' else None, 0])
            prev = '('
        elif c in (0x7D, 0x29):
            if stack:
                stack.pop()
            prev = ')'
        elif c in (0x2C, 0x3B):
            if stack:
                stack[-1][2] += 1
            prev = ','
        elif c == 0x3D:
            if raw[i + 1:i + 2] == b'=':
                prev = '=='
                i += 2
                continue
            if raw[i - 1:i] not in (b'~', b'<', b'>'):
                pending = last_ident
            prev = '='
        else:
            m = IDENT.match(raw, i)
            if m:
                w = m.group(0)
                if w in KEYWORDS:
                    prev = 'kw'
                else:
                    last_ident, prev = w, 'ident'
                i = m.end()
                continue
            if 0x20 < c < 0x80 and c != 0x2E:
                prev = 'op'
        i += 1
    return lits


def in_scope(ctx):
    names = [(k, (nm or b'').decode('latin1')) for k, nm, _ix in ctx]
    if any(k == '{' and nm.startswith(('OPERATE_TBL', 'GIFT')) for k, nm in names):
        return False
    if any(k == '(' and nm == 'print' for k, nm in names):
        return False
    return any((k == '{' and nm.startswith(SCOPE_TABLES)) or (k == '(' and nm in SCOPE_CALLS) for k, nm in names)


def literals(raw):
    """[(literal, text)] for the in-scope Japanese name literals of one member."""
    out = []
    for lit in scan(raw):
        if not in_scope(lit['ctx']):
            continue
        text = mt.unescape(lit['raw'])
        if mt.needs_text(text):
            out.append((lit, text))
    return out


def members():
    for path in sorted(dlg.MEMBERS.glob('*.bin')):
        raw = path.read_bytes()
        if b'\0' in raw:
            continue
        yield int(path.stem), raw


def inventory():
    items = {}
    for mid, raw in members():
        for lit, text in literals(raw):
            it = items.setdefault(text, {'count': 0, 'members': [], 'contexts': Counter()})
            it['count'] += 1
            if mid not in it['members']:
                it['members'].append(mid)
            outer = next(((k, (nm or b'').decode('latin1')) for k, nm, _ in lit['ctx']
                          if (nm or b'').decode('latin1').startswith(SCOPE_TABLES + SCOPE_CALLS)), ('?', '?'))
            it['contexts'][re.sub(r'_\d+$', '', outer[1])] += 1
    return items


def load():
    if TRANSLATION.exists():
        return json.loads(TRANSLATION.read_text(encoding='utf-8'))
    return {'schema': 1, 'strings': {}}


def seed(apply):
    data = load()
    research = {n['jp']: n for n in json.loads(RESEARCH.read_text(encoding='utf-8'))['names']}
    fixes = {'マクロス・クォーター（要塞艦型）': 'Macross Quarter (Fortress)', '紅蓮聖天八極式': 'Guren SEITEN'}
    added = 0
    for jp in inventory():
        if jp in data['strings'] or jp not in research:
            continue
        r = research[jp]
        en = fixes.get(jp, r['suggested_en'])
        if en:
            data['strings'][jp] = {'en': en, 'source': 'research:' + (r.get('suggested_source') or r['coverage'])}
            added += 1
    print('seeded %d names' % added)
    if apply:
        write_json(TRANSLATION, data)
    else:
        print('DRY RUN (pass --apply)')


def check(verbose=True):
    items = inventory()
    data = load()
    errors, missing = [], []
    for jp in items:
        e = data['strings'].get(jp)
        if not e or not e.get('en'):
            missing.append(jp)
            continue
        en = e['en']
        odd = sorted({c for c in en if not 32 <= ord(c) < 127})
        if odd:
            errors.append('%s: non-ASCII %r' % (jp, ''.join(odd)))
        if 2 * len(en) > MAX_BYTES:
            errors.append('%s: "%s" is %d bytes, limit %d' % (jp, en, 2 * len(en), MAX_BYTES))
    if verbose:
        for e in errors:
            print('ERROR', e)
        print('%d names (%d literals), %d without English, %d errors' %
              (len(items), sum(i['count'] for i in items.values()), len(missing), len(errors)))
    return errors, missing


def plan():
    return {jp: e['en'] for jp, e in load()['strings'].items() if e.get('en')}


def characters(texts):
    return {c for t in texts for c in t if 32 <= ord(c) < 127}


# --------------------------------------------------------------------------
# Combined rebuild of the stage literals (mission strings + squad names)

def rebuild_member(mid, mission, squad, mapping):
    """Member bytes with mission str_tbl strings and squad names replaced, or None.

    Readback: rescan the new bytes; every literal outside the edits is byte-identical, every edited
    one unescapes to its encoded English, OPERATE_TBL id_tbl is unchanged, and the bytes between
    literals are identical."""
    from tools import library_build as lb
    raw = (dlg.MEMBERS / ('%05d.bin' % mid)).read_bytes()
    edits = {}
    for m, lits, _roles in mt.tables(raw):
        for lit, text in lits:
            if text in mission:
                edits[m.start(1) + lit.start(1)] = (m.start(1) + lit.end(1), lb.encode(mission[text], mapping))
    if b'\0' not in raw:
        for lit, text in literals(raw):
            if text in squad:
                encoded = lb.encode(squad[text], mapping)
                if len(encoded) > MAX_BYTES:
                    raise ValueError('member %d: squad name %r encodes to %d bytes' % (mid, text, len(encoded)))
                if lit['start'] in edits:
                    raise ValueError('member %d: literal at %d edited twice' % (mid, lit['start']))
                edits[lit['start']] = (lit['end'], encoded)
    if not edits:
        return None
    out, pos = bytearray(), 0
    for start in sorted(edits):
        end, encoded = edits[start]
        if start < pos:
            raise ValueError('member %d: overlapping literal edits' % mid)
        out += raw[pos:start] + mt.lua_literal(encoded)
        pos = end
    out += raw[pos:]
    new = bytes(out)
    old_lits, new_lits = scan(raw), scan(new)
    if len(old_lits) != len(new_lits):
        raise ValueError('member %d: literal count changed' % mid)
    gaps_old = [raw[a['end']:b['start']] for a, b in zip(old_lits, old_lits[1:])]
    gaps_new = [new[a['end']:b['start']] for a, b in zip(new_lits, new_lits[1:])]
    if gaps_old != gaps_new or raw[:old_lits[0]['start']] != new[:new_lits[0]['start']] \
            or raw[old_lits[-1]['end']:] != new[new_lits[-1]['end']:]:
        raise ValueError('member %d: bytes outside the literals changed' % mid)
    for o, nw in zip(old_lits, new_lits):
        want = edits[o['start']][1] if o['start'] in edits else mt.unescape_bytes(o['raw'])
        if mt.unescape_bytes(nw['raw']) != want:
            raise ValueError('member %d: literal readback mismatch at %d' % (mid, o['start']))
    if [m.group(2) for m in mt.OP.finditer(raw)] != [m.group(2) for m in mt.OP.finditer(new)]:
        raise ValueError('member %d: id_tbl changed' % mid)
    return new


def stage_members():
    """Every member that may need a literal rebuild."""
    ids = set(mt.members())
    for mid, raw in members():
        if literals(raw):
            ids.add(mid)
    return sorted(ids)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['inventory', 'seed', 'check'])
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    if args.cmd == 'inventory':
        items = inventory()
        ctx = Counter()
        for it in items.values():
            ctx.update(it['contexts'])
        print('%d names, %d literals, %d members; contexts %s' % (
            len(items), sum(i['count'] for i in items.values()),
            len({m for i in items.values() for m in i['members']}), dict(ctx)))
    elif args.cmd == 'seed':
        seed(args.apply)
    elif args.cmd == 'check':
        return 1 if check()[0] else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
