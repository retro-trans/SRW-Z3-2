"""Translation memory: Tengoku battle voice lines vs Jigoku's shipped English.

    python -m tools.voice_tm            counts only
    python -m tools.voice_tm --apply    also write work/tengoku/voice/tm.json

Source of the English: Jigoku-hen `translation/voice_*.json` (211 published
section documents, {entry: {jp, en, budget}}; the Japanese keeps its corner
brackets, the English does not -- its writer added them). Matching is exact
on the full Japanese string, brackets and literal backslash-n included.

A match is a candidate to READ, not an answer to paste (BASE_RULES): the
same Japanese can need different English for a different speaker, Jigoku's
English uses Jigoku spellings and a Jigoku-only character set, and one
Japanese line can carry several Jigoku renderings (reported as conflicts).
"same_speaker" marks matches that come from the Jigoku section identified
as the same voice set (>= 50% shared lines; tools/voice_bind.py).
"""
import argparse
import collections
import json

from tools import srvc
from tools.voice_bind import JIGOKU, MIN_SHARED, is_sentinel, jigoku_match, jigoku_sections


def memory(docs):
    """{jp: {en: [sections]}}"""
    tm = collections.defaultdict(lambda: collections.defaultdict(list))
    for s, d in sorted(docs.items()):
        for v in d['lines'].values():
            if isinstance(v, dict) and v.get('en'):
                tm[v['jp']][v['en']].append(s)
    return tm


def match(data, tab, docs, ident):
    blocks = srvc.parse(data, tab)
    refs = srvc.lines(data, blocks)
    tm = memory(docs)
    index = collections.defaultdict(set)
    for s, d in docs.items():
        for v in d['lines'].values():
            index[v['jp']].add(s)
    by_block = collections.defaultdict(list)
    for r in refs:
        by_block[r['block']].append(r)
    same = {}
    for b, rs in by_block.items():
        jm = jigoku_match(sorted({r['jp'] for r in rs}), docs, ident, index)
        if jm and jm['fraction'] >= 0.5:
            same[b] = jm['section']
    c = collections.Counter()
    distinct_all, distinct_hit = set(), set()
    units = {}
    for r in refs:
        jp = r['jp']
        key = (r['block'], r['offset'])
        if is_sentinel(jp):
            c['refs_sentinel'] += 1
            continue
        distinct_all.add(jp)
        c['refs'] += 1
        hit = tm.get(jp)
        sec = same.get(r['block'])
        own = bool(hit) and sec is not None and any(sec in v for v in hit.values())
        if hit:
            distinct_hit.add(jp)
            c['refs_matched'] += 1
            if own:
                c['refs_same_speaker'] += 1
        if key not in units:
            units[key] = (jp, bool(hit), own)
    c['distinct'] = len(distinct_all)
    c['distinct_matched'] = len(distinct_hit)
    c['distinct_fresh'] = len(distinct_all - distinct_hit)
    c['refs_fresh'] = c['refs'] - c['refs_matched']
    c['block_strings'] = len(units)
    c['block_strings_matched'] = sum(1 for v in units.values() if v[1])
    c['block_strings_same_speaker'] = sum(1 for v in units.values() if v[2])
    c['distinct_conflicting'] = sum(1 for jp in distinct_hit if len(tm[jp]) > 1)
    c['distinct_short_matched'] = sum(1 for jp in distinct_hit if len(jp) < MIN_SHARED)
    out = {jp: [{'en': en, 'jigoku_sections': secs} for en, secs in
                sorted(tm[jp].items(), key=lambda kv: -len(kv[1]))] for jp in sorted(distinct_hit)}
    return dict(c), out


def main(argv=None):
    ap = argparse.ArgumentParser(description='Jigoku translation-memory match for battle voice')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    from tools.common import write_json
    data, elf = srvc.load_prepared()
    tab = srvc.read_table(elf, len(data))
    docs, ident = jigoku_sections()
    counts, out = match(data, tab, docs, ident)
    print('Jigoku memory: %d section documents, %d distinct Japanese lines with English'
          % (len(docs), len(memory(docs))))
    for k in sorted(counts):
        print('%-28s %d' % (k, counts[k]))
    path = srvc._settings()['work'] / 'voice' / 'tm.json'
    print('%s: %s' % ('APPLY' if args.apply else 'DRY RUN', path))
    if args.apply:
        write_json(path, {'schema': 1, 'source': str(JIGOKU / 'translation'), 'counts': counts,
                          'matches': out})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
