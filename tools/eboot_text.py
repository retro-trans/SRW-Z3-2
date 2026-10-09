"""Japanese UI text inside the executable: catalog, reuse, briefs and checks.

    python -m tools.eboot_text inventory
    python -m tools.eboot_text reuse [--apply]     # Tengoku English, then exact Jigoku English
    python -m tools.eboot_text export [--apply]    # briefs: work/tengoku/eboot_briefs/
    python -m tools.eboot_text check [--file X]    # whole catalog, or one answer slice
    python -m tools.eboot_text merge [--apply]     # eboot_new/*.json -> eboot.json

Source inventory: work/tengoku/research/eboot_strings.json (research: every
NUL-terminated cp932 / UTF-8 run in the program, classified). In scope: the
records the game draws itself (usage "display" / "display+lookup-risk").
Out of scope here: internal keys, input palettes, debug text, placeholders,
and the ~104 OS-dialog strings (cellMsgDialog / save data), which never reach
the game's text drawer.

English reaches the screen through the draw-time hook (tools/ui_hook.py,
docs/UI_HOOK.md): the executable's strings are never overwritten, so name
strings that double as lookup keys stay intact. One Japanese string = one
English everywhere it is drawn.

Text conventions in eboot.json / briefs: control bytes are written {XX}
(two hex digits, e.g. the colour markup 1{0B} ... 1{01}); a line break is a
real newline; printf specifiers (%s, %d, %2d...) are kept in order. Names may
use glossary $$tokens$$ (expanded at build).
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from tools.common import ROOT, write_json
from tools.library_text import GLOSSARY, TOKEN, Resolver

INVENTORY = ROOT / 'work/tengoku/research/eboot_strings.json'
TRANSLATION = ROOT / 'work/translation/en/ui/eboot.json'
NEW = ROOT / 'work/translation/en/ui/eboot_new'
BRIEFS = ROOT / 'work/tengoku/eboot_briefs'
IN_SCOPE = ('display', 'display+lookup-risk')
FORMAT = re.compile(r'%[-+#0]*\d*(?:\.\d+)?[hlL]*[diouxXeEfgGcsp%]')   # no space flag: '20% or' is prose
CTRL = re.compile(r'\{([0-9A-F]{2})\}')
SLICE = 80
ORDER = ('menu_command', 'system_message', 'help_description', 'reward_bonus', 'shop_trader', 'item_names',
         'ability_names', 'series_names', 'unit_pilot_names', 'team_names', 'library', 'stage_titles',
         'date_location', 'bgm_titles', 'defeat_quotes', 'dlc_synopsis')


def show(text):
    """Text with control characters (other than newline) as {XX}."""
    return ''.join('{%02X}' % ord(c) if ord(c) < 32 and c != '\n' else c for c in text)


def unshow(text):
    return CTRL.sub(lambda m: chr(int(m.group(1), 16)), text)


def key(jp):
    return show(jp).replace('\n', '\\n')


def records():
    return json.loads(INVENTORY.read_text(encoding='utf-8'))['strings']


def inventory():
    """{jp: {'families', 'encodings', 'vas', 'format', 'fragment', 'jigoku_en', 'tengoku_en', 'risk'}}."""
    items = {}
    for r in records():
        if not r.get('display') or r.get('usage') not in IN_SCOPE:
            continue
        it = items.setdefault(r['jp'], {'families': [], 'encodings': [], 'vas': [], 'format': False,
                                        'fragment': False, 'jigoku_en': None, 'tengoku_en': None, 'risk': False})
        for k, v in (('families', r['family']), ('encodings', r['encoding']), ('vas', r['va'])):
            if v not in it[k]:
                it[k].append(v)
        it['format'] |= bool(r.get('format')) or bool(FORMAT.search(r['jp']))
        it['fragment'] |= bool(r.get('fragment'))
        it['risk'] |= 'lookup-risk' in r['usage']
        it['jigoku_en'] = it['jigoku_en'] or (r['jigoku_en'] if r.get('jigoku_match') == 'exact' else None)
        it['jigoku_near'] = it.get('jigoku_near') or (r['jigoku_en'] if r.get('jigoku_match') == 'near' else None)
        it['tengoku_en'] = it['tengoku_en'] or r.get('tengoku_en')
    return items


def load():
    if TRANSLATION.exists():
        return json.loads(TRANSLATION.read_text(encoding='utf-8'))
    return {'schema': 1, 'strings': {}}


def resolver():
    return Resolver(json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms'])


def unusual(text):
    """Characters that cannot be drawn as English: kana/kanji, or anything outside ASCII and cp932.
    cp932 symbols (「」・：※～∀...) stay as the game's own glyphs."""
    bad = set()
    for c in text:
        if 32 <= ord(c) < 127 or c == '\n':
            continue
        if 0xE000 <= ord(c) <= 0xF8FF:            # private-use: another build's font cells, never portable
            bad.add(c)
            continue
        try:
            c.encode('cp932')
        except UnicodeEncodeError:
            bad.add(c)
            continue
        if re.match(r'[぀-ヿ一-鿿０-ｚ]', c):
            bad.add(c)
    return sorted(bad)


def other_sources():
    """{jp: English} from the project's other finished tables (RPW names and quotes, squad names)."""
    out = {}
    rpw = json.loads((ROOT / 'work/translation/en/ui/rpw_names.json').read_text(encoding='utf-8'))['strings']
    for fam in ('series', 'skill', 'part', 'weapon', 'robot', 'pilot', 'quote'):
        for jp, e in rpw.get(fam, {}).items():
            if e.get('en'):
                out.setdefault(jp, e['en'])
    squad = ROOT / 'work/translation/en/ui/squad_names.json'
    if squad.exists():
        for jp, e in json.loads(squad.read_text(encoding='utf-8'))['strings'].items():
            out.setdefault(jp, e['en'])
    return out


def validate(where, jp, en, res, errors):
    """en is stored in {XX} notation."""
    shown_jp = show(jp)
    if FORMAT.findall(shown_jp) != FORMAT.findall(en):
        errors.append('%s: format specifiers %s, the Japanese has %s' % (where, FORMAT.findall(en), FORMAT.findall(shown_jp)))
    if CTRL.findall(en) != CTRL.findall(shown_jp):
        errors.append('%s: control codes %s, the Japanese has %s' % (where, CTRL.findall(en), CTRL.findall(shown_jp)))
    if en.count('\n') > jp.count('\n'):
        errors.append('%s: %d line breaks, the Japanese has %d' % (where, en.count('\n'), jp.count('\n')))
    bare = CTRL.sub('', TOKEN.sub('', en))
    odd = unusual(bare)
    if odd:
        errors.append('%s: non-ASCII %r' % (where, ''.join(odd)))
    if '$$' in TOKEN.sub('', en):
        errors.append(where + ': malformed $$ token')
    for m in TOKEN.finditer(en):
        _t, problem = res.resolve(m.group(1))
        if problem:
            errors.append('%s: %s' % (where, problem))


def check(verbose=True):
    items = inventory()
    data = load()
    res = resolver()
    errors, missing = [], Counter()
    for jp, it in items.items():
        e = data['strings'].get(jp)
        if not e or not e.get('en'):
            missing[it['families'][0]] += 1
            continue
        validate(key(jp)[:40], jp, e['en'], res, errors)
    if verbose:
        for e in errors[:80]:
            print('ERROR', e)
        print('%d strings, %d without English %s, %d errors' % (len(items), sum(missing.values()), dict(missing), len(errors)))
    return errors, missing


def reuse(apply):
    items = inventory()
    data = load()
    res = resolver()
    stats = Counter()
    others = other_sources()
    for jp, it in items.items():
        if jp in data['strings']:
            continue
        for en, source in ((it['tengoku_en'], 'tengoku'), (others.get(jp), 'tengoku-tables'),
                           (it['jigoku_en'], 'jigoku')):
            if not en:
                continue
            en = show(en)
            errs = []
            validate(jp, jp, en, res, errs)
            if errs:
                stats[source + ' rejected'] += 1
                continue
            data['strings'][jp] = {'en': en, 'source': 'reuse:' + source}
            stats[source] += 1
            break
    print(dict(stats))
    if apply:
        write_json(TRANSLATION, data)
    else:
        print('DRY RUN (pass --apply)')


def export(apply):
    items = inventory()
    data = load()
    by_va = sorted((int(r['va'], 16), r['jp']) for r in records() if r.get('display') and r.get('usage') in IN_SCOPE)
    neighbors = {}
    for i, (_va, jp) in enumerate(by_va):
        neighbors.setdefault(jp, [j for _v, j in by_va[max(0, i - 3):i + 4] if j != jp])
    todo = defaultdict(list)
    for jp, it in items.items():
        if (data['strings'].get(jp) or {}).get('en'):
            continue
        fam = it['families'][0]
        todo[fam].append((jp, it))
    briefs = []
    for fam in ORDER:
        rows = sorted(todo.get(fam, []), key=lambda kv: kv[1]['vas'][0])
        for n in range(0, len(rows), SLICE):
            briefs.append(('e_%s_%02d' % (fam, n // SLICE), rows[n:n + SLICE]))
    print('%d strings -> %d briefs: %s' % (sum(len(v) for v in todo.values()), len(briefs),
                                            {k: len(v) for k, v in todo.items()}))
    if not apply:
        print('DRY RUN (pass --apply)')
        return
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for name, rows in briefs:
        out = ['# %s' % name, '', 'Answer file: work/translation/en/ui/eboot_new/%s.json (format: docs/UI_EBOOT.md).' % name, '']
        for jp, it in rows:
            info = {'jp': show(jp), 'family': it['families'], 'format': it['format'], 'fragment': it['fragment'],
                    'nearby': [show(n) for n in neighbors.get(jp, [])][:6]}
            if it.get('jigoku_near'):
                info['jigoku_similar'] = it['jigoku_near']
            out += ['## ' + key(jp), '```json', json.dumps(info, ensure_ascii=False), '```', '']
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
        elif not row.get('en'):
            errors.append('%s: no en' % k[:40])
        else:
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
# Build: hook entries

MARKUP = re.compile(r'1[\x01\x0b]')


def encode(text, mapping, utf8_source=False):
    """English (control codes as characters) -> drawer bytes: Latin as font cells, control and
    colour-markup sequences raw (the '1' of 1{0B} / 1{01} is markup, not a digit).

    A UTF-8 source string reaches the drawer through the game's converter, which stores a
    '1' escape operand minus one (1{0B} -> 31 0A, 1{01} -> 31 00; tools/ui_hook.convert), so
    its English must carry the converted form."""
    from tools import library_build as lb
    out, pos = bytearray(), 0
    for m in MARKUP.finditer(text):
        code = ord(m.group(0)[1]) - (1 if utf8_source else 0)
        out += lb.encode(text[pos:m.start()], mapping) + bytes((0x31, code))
        pos = m.end()
    out += lb.encode(text[pos:], mapping)
    return bytes(out)


def characters():
    from tools import library_build as lb
    res = resolver()
    chars = set()
    for e in load()['strings'].values():
        if e.get('en'):
            text = MARKUP.sub('', unshow(lb.expand(e['en'], res)))
            chars.update(c for c in text if 32 <= ord(c) < 127)
    return chars


def hook_check(key, english):
    from tools import ui_hook
    return ui_hook.check_english(key, english)


def hook_entries(elf, mapping, utf8_key):
    """[{'key', 'english', 'id'}] for tools/ui_hook.

    Keys are the program's own bytes (file offset + length from the inventory, checked against
    the Japanese): cp932 records as stored, UTF-8 records through the game's converter
    (`utf8_key`). Format strings and fragments are skipped: the hook sees them only after
    formatting / joining (a later phase)."""
    from tools import library_build as lb
    items = inventory()
    data = load()
    res = resolver()
    by_jp = defaultdict(list)
    for r in records():
        if r.get('display') and r.get('usage') in IN_SCOPE:
            by_jp[r['jp']].append(r)
    entries, skipped, seen = [], Counter(), set()
    for jp, it in items.items():
        e = data['strings'].get(jp)
        if not e or not e.get('en'):
            skipped['no English'] += 1
            continue
        if it['format'] or it['fragment']:
            skipped['format/fragment'] += 1
            continue
        text = unshow(lb.expand(e['en'], res))
        for r in by_jp[jp]:
            off, n = int(r['offset'], 16), r['bytes']
            raw = bytes(elf[off:off + n])
            enc = r['encoding']
            if raw.decode('cp932' if enc == 'cp932' else 'utf-8') != jp or elf[off + n] != 0:
                raise ValueError('inventory record at %s no longer matches the program' % r['va'])
            key = raw if enc == 'cp932' else utf8_key(raw)
            if key in seen:
                continue
            seen.add(key)
            english = encode(text, mapping, utf8_source=enc != 'cp932')
            problems = hook_check(key, english)
            if problems:
                skipped['refused by hook: ' + problems[0][:60]] += 1
                continue
            entries.append({'key': key, 'english': english, 'id': '%s:%s' % (enc, r['va'])})
    return entries, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['inventory', 'reuse', 'export', 'check', 'merge'])
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--file')
    args = ap.parse_args(argv)
    if args.cmd == 'inventory':
        items = inventory()
        fam = Counter(it['families'][0] for it in items.values())
        print('%d distinct strings; format %d, fragment %d, lookup-risk %d' % (
            len(items), sum(i['format'] for i in items.values()), sum(i['fragment'] for i in items.values()),
            sum(i['risk'] for i in items.values())))
        print(dict(fam))
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
        return 1 if check()[0] else 0
    elif args.cmd == 'merge':
        merge(args.apply)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
