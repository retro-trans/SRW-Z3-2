"""Rebuild SRVC.BIN with replacement lines and rewrite the executable block table.

    python -m tools.voice_write synthetic --out <scratch dir>           dry run
    python -m tools.voice_write synthetic --out <scratch dir> --apply   write test pair

The pair is one change: a rebuilt SRVC.BIN is only valid with the table the
same run wrote into the executable, and the original executable is only valid
with the original SRVC.BIN (Jigoku's installed-cache incident). The output is
checked by tools/srvc_check.py, which shares no code with the writer, and
nothing is written unless that check is clean.

Edits (`build`):
    {'block': i, 'k': line, 'jp': original Japanese, 'text': new text,
     'scope': 'string' | 'line'}
'string' (default) replaces the pool string line k points at, so every line
of that block that shares the string changes with it -- the normal case,
one translation per stored string. 'line' gives that one line its own new
string. `jp` must equal the file's text (stale-source guard). Encoding of
`text` is the caller's `encode` (the game build supplies its font mapping;
the synthetic test uses plain ASCII and must never be deployed).

Limits enforced here: block count/order, headers, rule/slot/C/D/cue arrays
and line counts never change; every string stays inside its block window;
blocks stay 16-aligned. NOT enforced, because unverified: any runtime cap on
a block's size (largest original 54,016 B), screen width, glyph coverage.
"""
import argparse
import json
from pathlib import Path

from tools import srvc, srvc_check

FORBIDDEN = [Path('E:/RPCS3')]


def _guard(out_dir):
    from tools.common import ROOT
    out = Path(out_dir).resolve()
    for bad in FORBIDDEN + [(ROOT / 'work/output/iso').resolve()]:
        bad = bad.resolve()
        if out == bad or bad in out.parents:
            raise ValueError('refusing to write into %s' % bad)
    return out


def plan_edits(data, tab, edits, encode):
    """Edits -> (strings, refs) for srvc.rebuild, with stale/conflict checks."""
    blocks = srvc.parse(data, tab)
    strings, refs, owner = {}, {}, {}
    for e in edits:
        i, k = e['block'], e['k']
        if not 0 <= i < len(blocks) or not 0 <= k < blocks[i].n6:
            raise ValueError('no line %d:%d' % (i, k))
        b = blocks[i]
        at = b.pool + b.offs[k]
        have = srvc.text(srvc.string_at(data, at))
        if e.get('jp') is not None and have != e['jp']:
            raise ValueError('line %d:%d holds %r, edit expects %r' % (i, k, have, e['jp']))
        raw = encode(e['text'])
        if not raw or b'\0' in raw:
            raise ValueError('line %d:%d encodes to an empty or NUL-bearing string' % (i, k))
        if e.get('scope', 'string') == 'line':
            refs[(i, k)] = raw
            continue
        if at in strings and strings[at] != raw:
            raise ValueError('line %d:%d shares its string with %s but the text differs'
                             % (i, k, owner[at]))
        strings[at] = raw
        owner[at] = '%d:%d' % (i, k)
    return strings, refs


def build(data, elf, edits, encode, expect=(srvc.TABLE_OFF, srvc.NBLOCKS)):
    """Returns (new SRVC, new executable, report). Raises on any problem."""
    tab = srvc.read_table(elf, len(data), expect)
    strings, refs = plan_edits(data, tab, edits, encode)
    new, newtab, rows = srvc.rebuild(data, tab, strings, refs)
    new_elf = srvc.patch_table(elf, tab, newtab, expect)
    problems = srvc_check.verify(elf, new_elf, data, new, strings, refs)
    if problems:
        raise ValueError('readback failed: ' + '; '.join(problems[:5]))
    if srvc.read_table(new_elf, len(new), expect) != newtab:
        raise ValueError('rewritten table does not read back')
    grown = [r for r in rows if r[2] > r[1]]
    report = {'blocks': len(rows), 'blocks_edited': sum(1 for r in rows if r[3]),
              'blocks_grown': len(grown), 'strings_replaced': len(strings),
              'lines_split': len(refs), 'old_size': len(data), 'new_size': len(new),
              'largest_block_old': max(r[1] for r in rows),
              'largest_block_new': max(r[2] for r in rows),
              'blocks_over_original_max': [r[0] for r in rows if r[2] > max(x[1] for x in rows)],
              'table_offset': srvc.locate_table(new_elf)['offset'], 'readback_problems': 0, 'runtime_verified': False}
    return new, new_elf, report


def synthetic_edits(data, tab):
    """One replaced string per text block, one per-line split, one big growth."""
    edits = []
    blocks = srvc.parse(data, tab)
    for b in blocks:
        if not b.n6:
            continue
        edits.append({'block': b.i, 'k': 0, 'jp': srvc.text(srvc.string_at(data, b.pool + b.offs[0])),
                      'text': 'VOICE TEST %d:0 - synthetic, never deploy' % b.i})
    big = max((b for b in blocks if b.n6 > 2), key=lambda b: b.end - b.base)
    edits.append({'block': big.i, 'k': 1, 'text': 'GROWTH ' * 400, 'scope': 'string'})
    edits.append({'block': big.i, 'k': 2, 'text': 'SPLIT LINE %d:2' % big.i, 'scope': 'line'})
    # drop edits that collide on a shared string (k=1/2 may share with k=0)
    seen, out = {}, []
    for e in edits:
        b = blocks[e['block']]
        key = (b.i, b.offs[e['k']], e.get('scope', 'string'))
        if key in seen:
            continue
        seen[key] = 1
        out.append(e)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd')
    s = sub.add_parser('synthetic')
    s.add_argument('--out', required=True)
    s.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)
    if args.cmd != 'synthetic':
        ap.print_help()
        return 2
    out = _guard(args.out)
    data, elf = srvc.load_prepared()
    tab = srvc.read_table(elf, len(data))
    edits = synthetic_edits(data, tab)
    new, new_elf, report = build(data, elf, edits, lambda t: t.encode('ascii'))
    report['edits'] = len(edits)
    report['note'] = 'SYNTHETIC TEST DATA - plain ASCII, not the project font encoding; never deploy'
    print(json.dumps(report, indent=1))
    print('%s: %s' % ('APPLY' if args.apply else 'DRY RUN', out))
    if args.apply:
        out.mkdir(parents=True, exist_ok=True)
        for name, blob in (('SRVC.BIN', new), ('EBOOT.elf', new_elf)):
            with open(str(out / name), 'xb') as stream:
                stream.write(blob)
        (out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
