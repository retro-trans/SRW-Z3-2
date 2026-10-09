"""Stage mission conditions: the OPERATE_TBL str_tbl strings of the stage scripts.

    python -m tools.mission_text inventory          # strings, roles, members
    python -m tools.mission_text reuse [--apply]    # Jigoku's mission_conditions_hook English
    python -m tools.mission_text export [--apply]   # briefs: work/tengoku/mission_briefs/
    python -m tools.mission_text check [--file X]   # whole file, or one answer slice
    python -m tools.mission_text merge [--apply]    # mission_new/*.json -> mission.json

Each stage member that shows mission conditions has one or more
    OPERATE_TBL={str_tbl={"...", ...}; id_tbl={...};}
id_tbl comes in groups of 8 (one per phase of the map): a final-condition
flag, then three victory slots, three defeat slots and the SR Point slot,
each an index into str_tbl or -1. The strings are display text (the roles
are decided by id_tbl, never by the wording). Team and squad names
(TOUROKU / ENEMY_TBL / SC_ calls) are tools/squad_text.py, whose rebuild applies both.

English is written with glossary $$tokens$$ like the story, one paragraph
per Japanese paragraph (`\\n` in the Japanese = a newline in the English).
The build expands tokens, word-wraps each paragraph to the panel (38
full-width cells, the longest Japanese line is 39), encodes with the font
mapping and writes the Lua literal with `\\n` for breaks and `\\\\` for
any 0x5C byte (the scripts' own convention for ソ, 表...).
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from tools.common import ROOT, write_json
from tools import dialogue as dlg
from tools.library_text import GLOSSARY, TOKEN, Resolver

TRANSLATION = ROOT / 'work/translation/en/ui/mission.json'
NEW = ROOT / 'work/translation/en/ui/mission_new'
BRIEFS = ROOT / 'work/tengoku/mission_briefs'
JIGOKU_HOOK = Path('E:/Projects/SRW Z3/translation/mission_conditions_hook.json')   # read only
OP = re.compile(rb'OPERATE_TBL=\{str_tbl=\{(.*?)\};\s*id_tbl=\{(.*?)\};', re.S)
LIT = re.compile(rb'"((?:[^"\\]|\\.)*)"')
ROLES = {1: 'victory', 2: 'victory', 3: 'victory', 4: 'defeat', 5: 'defeat', 6: 'defeat', 7: 'sr'}
LINE_UNITS = 38 * 32
SLICE = 60


def unescape_bytes(raw):
    """Lua literal body -> the string's bytes, read byte by byte as Lua 5.1 does:
    \\n newline, \\ + any other byte -> that byte (so ソ = 83 5C is stored 83 5C 5C)."""
    out, i = bytearray(), 0
    while i < len(raw):
        b = raw[i]
        if b == 0x5C and i + 1 < len(raw):
            nxt = raw[i + 1]
            if 0x30 <= nxt <= 0x39:
                raise ValueError('decimal escape in a mission literal')
            out += b'\n' if nxt == ord('n') else bytes((nxt,))
            i += 2
            continue
        out.append(b)
        i += 1
    return bytes(out)


def unescape(raw):
    return unescape_bytes(raw).decode('cp932')


def tables(raw):
    """[(table match, [(literal match, text)], [roles per string])] for one member's bytes."""
    result = []
    for m in OP.finditer(raw):
        lits = [(l, unescape(l.group(1))) for l in LIT.finditer(m.group(1))]
        ids = [x.strip() for x in m.group(2).decode('ascii').split(',') if x.strip()]
        if len(ids) % 8:
            raise ValueError('id_tbl length %d is not a multiple of 8' % len(ids))
        roles = [set() for _ in lits]
        for g in range(0, len(ids), 8):
            for slot, role in ROLES.items():
                k = int(ids[g + slot])
                if k >= 0:
                    roles[k].add(role)
        result.append((m, lits, roles))
    return result


def inventory():
    """{text: {'roles', 'members', 'siblings'}} over every stage member."""
    items = {}
    for path in sorted(dlg.MEMBERS.glob('*.bin')):
        raw = path.read_bytes()
        if b'OPERATE_TBL' not in raw:
            continue
        mid = int(path.stem)
        for _m, lits, roles in tables(raw):
            texts = [t for _l, t in lits]
            for (_l, text), rs in zip(lits, roles):
                it = items.setdefault(text, {'roles': set(), 'members': [], 'siblings': []})
                it['roles'] |= rs
                if mid not in it['members']:
                    it['members'].append(mid)
                for s in texts:
                    if s != text and s not in it['siblings'] and len(it['siblings']) < 6:
                        it['siblings'].append(s)
    return items


def needs_text(text):
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff5e]', text))


def load():
    if TRANSLATION.exists():
        return json.loads(TRANSLATION.read_text(encoding='utf-8'))
    return {'schema': 1, 'strings': {}}


def resolver():
    return Resolver(json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms'])


# Runtime substitutions (EBOOT table at 0x9E1198): the protagonist's names, which the
# player can change, and per-map counters that become numbers. They stay byte-exact.
PLACEHOLDERS = ('主人公フルネーム', 'ヒビキＡ', 'ヒビキＮ', 'カミシロＮ', 'ローカルワーク０', 'ローカルワーク１', 'ローカルワーク２')


def validate(where, jp, en, res, errors):
    for p in PLACEHOLDERS:
        if en.count(p) != jp.count(p):
            errors.append('%s: placeholder %s appears %d times, the Japanese has %d (keep it verbatim)'
                          % (where, p, en.count(p), jp.count(p)))
    bare = TOKEN.sub('', en)
    for p in PLACEHOLDERS:
        bare = bare.replace(p, '')
    if '$$' in bare:
        errors.append(where + ': malformed $$ token')
    odd = sorted({c for c in bare if not 32 <= ord(c) < 127 and c != '\n'})
    if odd:
        errors.append('%s: non-ASCII %r' % (where, ''.join(odd)))
    if en.count('\n') > jp.count('\n'):
        errors.append('%s: %d line breaks, the Japanese has %d (breaks are paragraphs; the build wraps)'
                      % (where, en.count('\n'), jp.count('\n')))
    for m in TOKEN.finditer(en):
        _t, problem = res.resolve(m.group(1))
        if problem:
            errors.append('%s: %s' % (where, problem))


def check():
    items = inventory()
    data = load()
    res = resolver()
    errors, missing = [], 0
    for jp, it in items.items():
        if not needs_text(jp):
            continue
        e = data['strings'].get(jp)
        if not e or not e.get('en'):
            missing += 1
            continue
        validate(repr(jp[:30]), jp, e['en'], res, errors)
    for e in errors:
        print('ERROR', e)
    print('%d strings, %d without English, %d errors' % (sum(needs_text(j) for j in items), missing, len(errors)))
    return errors


# --------------------------------------------------------------------------

def reuse(apply):
    items = inventory()
    data = load()
    res = resolver()
    hook = json.loads(JIGOKU_HOOK.read_text(encoding='utf-8'))['lines'] if JIGOKU_HOOK.exists() else []
    found = 0
    for line in hook:
        jp, en = line['jp'], line['en']
        if jp not in items or jp in data['strings']:
            continue
        errs = []
        validate(jp, jp, en, res, errs)
        if errs:
            continue                      # a Jigoku token our glossary does not resolve: leave it to a brief
        data['strings'][jp] = {'en': en, 'source': 'jigoku:mission_conditions_hook.json'}
        found += 1
    print('reused %d of %d Jigoku lines' % (found, len(hook)))
    if apply:
        write_json(TRANSLATION, data)
    else:
        print('DRY RUN (pass --apply)')


def key(jp):
    return jp.replace('\n', '\\n')


def export(apply):
    items = inventory()
    data = load()
    todo = [(jp, it) for jp, it in sorted(items.items(), key=lambda kv: min(kv[1]['members']))
            if needs_text(jp) and not (data['strings'].get(jp) or {}).get('en')]
    briefs = [('m_%02d' % (n // SLICE), todo[n:n + SLICE]) for n in range(0, len(todo), SLICE)]
    print('%d strings -> %d briefs' % (len(todo), len(briefs)))
    if not apply:
        print('DRY RUN (pass --apply)')
        return
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for name, rows in briefs:
        out = ['# %s' % name, '', 'Answer file: work/translation/en/ui/mission_new/%s.json (format: docs/UI_MISSION.md).' % name, '']
        for jp, it in rows:
            out += ['## ' + key(jp), '```json',
                    json.dumps({'jp': jp, 'roles': sorted(it['roles']), 'stage_members': it['members'][:8],
                                'same_screen': it['siblings']}, ensure_ascii=False), '```', '']
        (BRIEFS / (name + '.md')).write_bytes('\n'.join(out).encode('utf-8'))
    print('wrote', BRIEFS)


def check_answer(path, items=None):
    items = items if items is not None else inventory()
    by_key = {key(jp): jp for jp in items}
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    res = resolver()
    errors = []
    for k, row in data.get('rows', {}).items():
        jp = by_key.get(k)
        if jp is None:
            errors.append('%s: unknown key' % k[:40])
            continue
        if not row.get('en'):
            errors.append('%s: no en' % k[:40])
            continue
        validate(k[:40], jp, row['en'], res, errors)
    brief = BRIEFS / (Path(path).stem + '.md')
    if brief.exists():
        wanted = set(re.findall(r'^## (.+)$', brief.read_text(encoding='utf-8'), re.M))
        gone = wanted - set(data.get('rows', {}))
        if gone:
            errors.append('%d items of the brief are not answered, e.g. %s' % (len(gone), sorted(gone)[0][:40]))
    return errors


def merge(apply):
    items = inventory()
    by_key = {key(jp): jp for jp in items}
    data = load()
    merged = 0
    for path in sorted(NEW.glob('*.json')):
        errs = check_answer(path, items)
        if errs:
            print('SKIPPED %s: %s' % (path.name, errs[0]))
            continue
        for k, row in json.loads(path.read_text(encoding='utf-8'))['rows'].items():
            data['strings'][by_key[k]] = {'en': row['en'], 'source': 'fresh:' + path.stem}
            merged += 1
    print('merged %d%s' % (merged, '' if apply else ' (DRY RUN, pass --apply)'))
    if apply:
        write_json(TRANSLATION, data)


# --------------------------------------------------------------------------
# Build

def wrap(text, width_of, units=LINE_UNITS):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            trial = (line + ' ' + word) if line else word
            if line and sum(width_of(c) for c in trial) > units:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return '\n'.join(lines)


def lua_literal(encoded):
    """Encoded bytes -> Lua string body: 0x5C doubled, newline as \\n."""
    if b'"' in encoded or b'\r' in encoded:
        raise ValueError('encoded mission text holds a quote or CR byte')
    return encoded.replace(b'\\', b'\\\\').replace(b'\n', b'\\n')


def plan(width_of):
    """{text: final English} for every translated string (tokens expanded, wrapped)."""
    from tools import library_build as lb
    data = load()
    res = resolver()
    out = {}
    for jp, e in data['strings'].items():
        if e.get('en'):
            out[jp] = wrap(lb.expand(e['en'], res), width_of)
    return out


def characters(texts):
    return {c for t in texts for c in t if 32 <= ord(c) < 127}


def rebuild_member(mid, rendered, mapping):
    """Member bytes with every translated str_tbl literal replaced, or None if nothing changed."""
    from tools import library_build as lb
    raw = (dlg.MEMBERS / ('%05d.bin' % mid)).read_bytes()
    if b'OPERATE_TBL' not in raw:
        return None
    out, pos, expected = bytearray(), 0, []
    for m, lits, _roles in tables(raw):
        base = m.start(1)
        for lit, text in lits:
            if text not in rendered:
                expected.append(unescape_bytes(lit.group(1)))
                continue
            encoded = lb.encode(rendered[text], mapping)
            start, end = base + lit.start(1), base + lit.end(1)
            out += raw[pos:start] + lua_literal(encoded)
            pos = end
            expected.append(encoded)
    out += raw[pos:]
    new = bytes(out)
    if new == raw:
        return None
    # Readback, byte-wise as Lua reads it: same tables, same id_tbl, every literal as intended,
    # and the bytes outside the str_tbl bodies unchanged.
    old_m, new_m = list(OP.finditer(raw)), list(OP.finditer(new))
    if len(old_m) != len(new_m):
        raise ValueError('member %d: table count changed' % mid)
    got, outside_old, outside_new, p_old, p_new = [], b'', b'', 0, 0
    for om, nm in zip(old_m, new_m):
        if om.group(2) != nm.group(2):
            raise ValueError('member %d: id_tbl changed' % mid)
        got += [unescape_bytes(l.group(1)) for l in LIT.finditer(nm.group(1))]
        outside_old += raw[p_old:om.start(1)]
        outside_new += new[p_new:nm.start(1)]
        p_old, p_new = om.end(1), nm.end(1)
    if got != expected or outside_old + raw[p_old:] != outside_new + new[p_new:]:
        raise ValueError('member %d: mission literal readback mismatch' % mid)
    return new


def members():
    return sorted(int(p.stem) for p in dlg.MEMBERS.glob('*.bin') if b'OPERATE_TBL' in p.read_bytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['inventory', 'reuse', 'export', 'check', 'merge'])
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--file')
    args = ap.parse_args(argv)
    if args.cmd == 'inventory':
        items = inventory()
        roles = Counter(','.join(sorted(it['roles'])) or 'unused' for jp, it in items.items() if needs_text(jp))
        print('%d distinct strings needing English in %d members; roles %s' %
              (sum(needs_text(j) for j in items), len(members()), dict(roles)))
    elif args.cmd == 'reuse':
        reuse(args.apply)
    elif args.cmd == 'export':
        export(args.apply)
    elif args.cmd == 'check' and args.file:
        errs = check_answer(NEW / args.file)
        for e in errs:
            print('ERROR', e)
        print('%s: %d errors' % (args.file, len(errs)))
        return 1 if errs else 0
    elif args.cmd == 'check':
        return 1 if check() else 0
    elif args.cmd == 'merge':
        merge(args.apply)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
