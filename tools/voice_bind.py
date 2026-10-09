"""What each battle voice line is bound to: block, situation slot, rule, speaker leads.

    python -m tools.voice_bind            dry run: counts and a sample
    python -m tools.voice_bind --apply    write work/tengoku/voice/{blocks,lines}.json

Structural bindings (from SRVC itself, exact):
- block = the voice bank the game loads by id (one block per bank);
- slot  = one of the 74 situation slots in the block header (A array). Every
  line is reached through exactly one slot's rules;
- rule  = (condition, weight, first line, line count). Condition 0 is the
  generic pool; nonzero conditions select lines against particular
  opponents/traits (class byte << 8 | value). Their meanings are game data
  this tool does not decode.
- cue   = the sound-cue id and flag stored per line.

Speaker leads (evidence, never a verdict -- see docs/Z3_LESSONS.md section 1):
- jigoku: the Jigoku-hen section sharing the most lines, with the identity
  that project recorded for it (its analysis/voice_identity.json first);
- weapons: weapon names spoken in the block -> RPW weapon -> wpn-1r owner ->
  robot name -> the robot encyclopedia's PLTN pilot field;
- spoken: glossary pilot names that occur in the block's lines (often the
  people the speaker addresses, not the speaker).
Each lead is mapped to this project's glossary tokens where a name matches.
"""
import argparse
import collections
import glob
import json
import re
import struct
from pathlib import Path

from tools import srvc

JIGOKU = Path('E:/Projects/SRW Z3')
GLOSSARY = Path(__file__).resolve().parents[1] / 'work/glossary/library_terms.json'
SENTINEL = ('－－－', '無音', '表示しません')
MIN_SHARED = 8                 # characters; shorter barks are shared by everyone
KATA = re.compile(r'[\u30a1-\u30fa\u30fc\u30fb]{4,}')
MAXOWNERS = 4

# Proposed from reading the lines each slot selects across all 283 text
# blocks. '?' marks a reading with real doubt. Weapon slots: see SLOT_WEAPON.
SLOT_LABELS = {
    0: 'attack', 1: 'counterattack', 2: 'support attack', 3: 'follow-up attack',
    4: 'team attack: focus/hold (?)', 5: 'team attack: split targets (?)',
    7: 'special opponent: attacking (?)', 8: 'special opponent: defending (?)',
    9: 'special opponent: other (?)', 10: 'shot down', 11: 'hit: heavy damage',
    12: 'hit: moderate damage', 13: 'hit: light damage', 14: 'shield guard',
    15: 'evade', 16: 'special evade', 17: 'no damage', 18: 'barrier/field block',
    19: 'phase shift armor', 20: 'parry/intercept', 21: 'special cut-in (?)',
    22: 'system/suspend message (?)', 23: 'cannot attack (?)', 24: 'out of range (?)',
    25: 'out of EN/ammo', 26: 'support defense (cover)', 27: 'could not retaliate (?)',
    28: 'attack variant (?)', 29: 'special (?)', 30: 'special (?)',
}
SLOT_WEAPON = range(35, 53)    # attack call-outs, one slot per weapon/attack number


def slot_label(s):
    if s in SLOT_WEAPON:
        return 'weapon slot %d' % (s - SLOT_WEAPON.start)
    return SLOT_LABELS.get(s, 'unlabelled slot %d' % s)


def is_sentinel(jp):
    return any(m in jp for m in SENTINEL)


# --------------------------------------------------------------------------
# Glossary


class Names:
    def __init__(self, path=GLOSSARY):
        terms = json.loads(Path(path).read_text(encoding='utf-8'))['terms']
        self.pilots = [t for t in terms if t['kind'] == 'pilot']
        self.by_jp = collections.defaultdict(list)
        self.by_en = collections.defaultdict(list)
        for t in self.pilots:
            self.by_jp[t['jp']].append(t)
            if t.get('en'):
                self.by_en[t['en'].lower()].append(t)

    @staticmethod
    def _row(t):
        return {'token': t['token'], 'jp': t['jp'], 'en': t.get('en'), 'status': t.get('status')}

    def resolve(self, name):
        """Glossary pilot rows for a free-form name (Japanese or English)."""
        if not name:
            return []
        name = name.strip()
        hit = self.by_jp.get(name) or self.by_en.get(name.lower())
        if hit:
            return [self._row(t) for t in hit]
        # A Jigoku identity is often 'English (Japanese)' or a description.
        found = {}
        for jp, ts in self.by_jp.items():
            if len(jp) >= 3 and jp in name:
                for t in ts:
                    found[t['token']] = t
        low = name.lower()
        for en, ts in self.by_en.items():
            if len(en) >= 4 and re.search(r'(?<![a-z])%s(?![a-z])' % re.escape(en), low):
                for t in ts:
                    found[t['token']] = t
        # keep only the most specific matches (drop names inside longer ones)
        keys = sorted(found, key=lambda k: -len(found[k]['jp']))
        keep = [k for k in keys if not any(k != o and found[k]['jp'] in found[o]['jp'] for o in keys)]
        return [self._row(found[k]) for k in keep[:4]]

    def spoken(self, texts, top=5):
        blob = '\n'.join(texts)
        c = collections.Counter()
        for jp in self.by_jp:
            if len(jp) >= 3:
                n = blob.count(jp)
                if n:
                    c[jp] = n
        # a name inside a longer counted name is the same mention
        for jp in list(c):
            if any(jp != o and jp in o for o in c):
                c[jp] -= sum(c[o] for o in c if jp != o and jp in o)
        return [{'jp': jp, 'count': n, 'tokens': [t['token'] for t in self.by_jp[jp]]}
                for jp, n in c.most_common() if n > 0][:top]


# --------------------------------------------------------------------------
# Jigoku identity transfer


def jigoku_sections(root=JIGOKU):
    docs = {}
    for p in glob.glob(str(root / 'translation' / 'voice_*.json')):
        d = json.loads(Path(p).read_text(encoding='utf-8'))
        docs[d['section']] = d
    ident_path = root / 'analysis' / 'voice_identity.json'
    ident = json.loads(ident_path.read_text(encoding='utf-8')) if ident_path.exists() else {}
    return docs, ident


def jigoku_match(texts, docs, ident, index):
    mine = {t for t in texts if len(t) >= MIN_SHARED and not is_sentinel(t)}
    c = collections.Counter()
    for t in mine:
        for s in index.get(t, ()):
            c[s] += 1
    if not mine or not c:
        return None
    s, n = max(c.items(), key=lambda kv: (kv[1], -kv[0]))     # ties -> lowest section
    doc = docs[s]
    fixed = ident.get(str(s)) or {}
    pilot = fixed.get('pilot') or (doc.get('pilots') or [None])[0]
    unit = fixed.get('unit') or doc.get('unit')
    return {'section': s, 'shared': n, 'of': len(mine), 'fraction': round(n / len(mine), 3),
            'pilot': pilot, 'unit': unit, 'why': (fixed.get('why') or '')[:200]}


# --------------------------------------------------------------------------
# RPW weapon -> unit -> pilot


def rpw_tables(raw, inventory):
    strings = {s['body_offset']: s['jp'] for s in inventory['strings']}
    chunks = {c['name']: c for c in inventory['chunks']}

    def words(name):
        c = chunks[name]
        n = (c['body_end'] - c['body_offset']) // 4
        return struct.unpack_from('<%dI' % n, raw, c['body_offset'])

    w = words('weapon')
    wnames = {}
    for r in range(len(w) // 13):
        for col in (3, 4):
            jp = strings.get(w[13 * r + col], '').strip()
            if jp and jp not in ('-', 'ダミー'):
                wnames.setdefault(r, set()).add(jp)
    t = words('wpn-1r')
    owner = {}
    for k in range(0, len(t) - 2, 3):
        uid, count, first = t[k:k + 3]
        for r in range(first, first + count):
            owner[r] = uid
    rb = words('robot')
    uname = {}
    for r in range(len(rb) // 24):
        for col in (2, 3):
            jp = strings.get(rb[24 * r + col], '').strip()
            if jp and jp not in ('-', 'ダミー', '？？？'):
                uname.setdefault(rb[24 * r + 4], jp)
                break
    return wnames, owner, uname


def robot_pilots(library_records):
    out = collections.defaultdict(set)
    for r in library_records:
        if r['kind'] != 'robot':
            continue
        f = {x['tag']: x['text'] for x in r['fields']}
        # Tengoku's PLTN is mostly a dash and carries developer placeholders
        # (text between reference marks); only real names are leads.
        pilots = [p for p in re.split(r'[／/、\n]', f.get('PLTN', ''))
                  if p.strip('－-― 　') and '※' not in p and p.strip() != '誰か']
        for key in ('RBTN', 'RBN2'):
            if f.get(key):
                out[f[key].replace('　', '').strip()].update(p.strip() for p in pilots)
    return out


def weapon_index(wnames, owner, uname):
    """fragment -> unit names, minus fragments of robot names (Jigoku lesson:
    pilots shout their machine's name, which is not weapon evidence)."""
    frag = collections.defaultdict(set)
    full = collections.defaultdict(set)
    for rec, names in wnames.items():
        who = uname.get(owner.get(rec))
        if not who:
            continue
        for nm in names:
            if len(nm) >= 3:
                full[nm].add(who)
            for m in KATA.finditer(nm):
                s = m.group(0)
                for a in range(len(s) - 3):
                    for z in range(a + 4, len(s) + 1):
                        frag[s[a:z]].add(who)
    for nm in set(uname.values()):
        for m in KATA.finditer(nm):
            g = m.group(0)
            for a in range(len(g) - 3):
                for z in range(a + 4, len(g) + 1):
                    frag.pop(g[a:z], None)
    return full, frag


def weapon_leads(texts, full, frag):
    score = collections.Counter()
    for t in texts:
        hit = [nm for nm in full if nm in t and len(full[nm]) <= MAXOWNERS]
        if hit:
            nm = max(hit, key=len)
            for who in full[nm]:
                score[who] += 1.0 / len(full[nm])
            continue
        for m in KATA.finditer(t):
            s, best = m.group(0), None
            for a in range(len(s) - 3):
                for z in range(len(s), a + 3, -1):
                    if s[a:z] in frag:
                        best = s[a:z]
                        break
                if best:
                    break
            if best and len(frag[best]) <= MAXOWNERS:
                for who in frag[best]:
                    score[who] += 0.5 / len(frag[best])
    return [{'unit': u, 'points': round(p, 2)} for u, p in score.most_common(4) if p >= 1.0]


# --------------------------------------------------------------------------


def groups(block_sets):
    """Blocks sharing >= 90% of the larger line set hold the same voice set
    (max, not min: tiny one-line blocks would otherwise chain unrelated sets)."""
    parent = {b: b for b in block_sets}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    keys = [b for b in block_sets if block_sets[b]]
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            sa, sb = block_sets[a], block_sets[b]
            if len(sa & sb) >= 0.9 * max(len(sa), len(sb)):
                parent[find(b)] = find(a)
    out = collections.defaultdict(list)
    for b in keys:
        out[find(b)].append(b)
    return {b: sorted(v) for v in out.values() for b in v}


def bind(data, tab, names=None, jigoku=None, rpw=None, library=None):
    blocks = srvc.parse(data, tab)
    refs = srvc.lines(data, blocks)
    names = names or Names()
    by_block = collections.defaultdict(list)
    for r in refs:
        by_block[r['block']].append(r)
    docs, ident = jigoku if jigoku is not None else ({}, {})
    index = collections.defaultdict(set)
    for s, d in docs.items():
        for v in d['lines'].values():
            index[v['jp']].add(s)
    full = frag = None
    pil = {}
    if rpw is not None:
        full, frag = weapon_index(*rpw_tables(*rpw))
    if library is not None:
        pil = robot_pilots(library)
    sets = {b.i: {r['jp'] for r in by_block[b.i] if not is_sentinel(r['jp'])} for b in blocks}
    grp = groups(sets)
    out_blocks, out_lines = [], []
    for b in blocks:
        rs = by_block[b.i]
        texts = sorted({r['jp'] for r in rs})
        row = {'block': b.i, 'base': b.base, 'size': b.end - b.base, 'lines': b.n6,
               'distinct': len(texts),
               'translatable': sum(1 for t in texts if not is_sentinel(t)),
               'group': grp.get(b.i, [b.i]),
               'slots': {str(s): {'label': slot_label(s), 'rules': c, 'flags': f}
                         for s, (_first, c, f) in enumerate(b.slots) if c}}
        if texts:
            jm = jigoku_match(texts, docs, ident, index) if docs else None
            if jm:
                jm['tokens'] = [x['token'] for x in names.resolve(jm['pilot'])]
            row['jigoku'] = jm
            if full is not None:
                weapon_texts = [r['jp'] for r in rs if any(u[0] in SLOT_WEAPON for u in r['uses'])]
                wl = weapon_leads(weapon_texts or texts, full, frag)
                for w in wl:
                    w['pilots'] = sorted(pil.get(w['unit'].replace('　', ''), ()))
                    w['tokens'] = sorted({x['token'] for p in w['pilots'] for x in names.resolve(p)})
                row['weapons'] = wl
            row['spoken'] = names.spoken(texts)
        out_blocks.append(row)
        for r in rs:
            out_lines.append({'id': '%d:%d' % (b.i, r['k']), 'string': '%d:%d' % (b.i, r['offset'] - b.pool),
                              'cue': r['cue'], 'flag': r['flag'],
                              'slots': [[s, slot_label(s), '%#x' % c, w] for s, _r, c, w in r['uses']],
                              'jp': r['jp']})
    return out_blocks, out_lines


def summary(blocks):
    text = [b for b in blocks if b['lines']]
    jig = [b for b in text if b.get('jigoku')]
    strong = [b for b in jig if b['jigoku']['fraction'] >= 0.5]
    tok = [b for b in text if (b.get('jigoku') or {}).get('tokens') and b['jigoku']['fraction'] >= 0.5]
    wpn = [b for b in text if b.get('weapons')]
    wtok = [b for b in wpn if any(w['tokens'] for w in b['weapons'])]
    anyt = [b for b in text if b in tok or b in wtok]
    return {'blocks': len(blocks), 'text_blocks': len(text),
            'groups': len({tuple(b['group']) for b in text}),
            'jigoku_any': len(jig), 'jigoku_strong_ge_0_5': len(strong),
            'jigoku_strong_with_token': len(tok), 'weapon_lead': len(wpn),
            'weapon_lead_with_token': len(wtok), 'any_token_lead': len(anyt),
            'no_lead': len([b for b in text if not (b.get('jigoku') or b.get('weapons'))])}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Bind battle voice lines to slots and speakers')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    from tools.common import ROOT, write_json
    from tools.inventory import verified_rpw
    data, elf = srvc.load_prepared()
    tab = srvc.read_table(elf, len(data))
    settings = srvc._settings()
    prepared = settings['work'] / 'prepared'
    inventory = json.loads((prepared / 'rpw_inventory.json').read_text(encoding='utf-8'))
    library = json.loads((prepared / 'library_inventory.json').read_text(encoding='utf-8'))['records']
    blocks, lines = bind(data, tab, Names(), jigoku_sections(), (verified_rpw(settings), inventory), library)
    s = summary(blocks)
    for k, v in s.items():
        print('%-28s %d' % (k, v))
    out = settings['work'] / 'voice'
    print('%s: %s/blocks.json, %s/lines.json' % ('APPLY' if args.apply else 'DRY RUN', out, out))
    if args.apply:
        write_json(out / 'blocks.json', {'schema': 1, 'summary': s, 'slot_labels': {
            str(k): slot_label(k) for k in list(SLOT_LABELS) + list(SLOT_WEAPON)}, 'blocks': blocks})
        write_json(out / 'lines.json', {'schema': 1, 'lines': lines})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
