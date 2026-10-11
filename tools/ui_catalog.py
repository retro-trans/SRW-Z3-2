"""Source-bound UI expansion. Preview/export briefs without changing game data."""
import argparse
import json
import struct
from collections import defaultdict, Counter

from tools.common import ROOT, sha256, write_json
from tools.pipeline import config, verified_source
from tools import eboot_text, rpw_text
from tools.ui_coverage import member, reference, description_cells, ui_string_table
from tools.aid_art import ARCHIVE
from tools.source_text import JAPANESE
from tools.source_text import lua_strings
from tools.inventory import UI_ARCHIVES
from tools.cpk import CPK
from tools import library_build as lb, ui_hook

DEST = ROOT / 'work/translation/en/ui/expanded'
BRIEFS = ROOT / 'work/tengoku/ui_expansion_briefs'


def fssa_strings(blob, decode=None):
    """Tengoku's header-bound string pool and 32-byte text-widget records.

    These sections come from the target header, not Jigoku offsets. Return
    pointer-backed strings only, excluding Japanese embedded in binary words.
    """
    if blob[:8] != b'FSSA\x01\x01\0\0':
        raise ValueError('Unexpected FSSA header')
    base, end = struct.unpack_from('>II', blob, 0x20)
    records, record_end = struct.unpack_from('>II', blob, 0x48)
    if not (0x7c < base < end <= records < record_end <= len(blob)) or (record_end-records) % 32:
        raise ValueError('FSSA section geometry changed')
    pool = blob[base:end]
    starts = {0} | {i + 1 for i, b in enumerate(pool) if b == 0}
    grouped = defaultdict(list)
    for at in range(records, record_end, 32):
        pointer = struct.unpack_from('>I', blob, at)[0]
        if pointer not in starts or pointer >= len(pool):
            raise ValueError('FSSA text widget points outside a string start: %#x' % at)
        grouped[pointer].append(at)
    rows = []
    for pos, refs in sorted(grouped.items()):
        raw = pool[pos:pool.index(b'\0', pos)]
        rows.append(dict(id='aid:0:%x' % (base+pos), text=decode(raw) if decode else raw.decode('cp932'),
            raw=raw, encoding='cp932', offset=base+pos, widget_offsets=refs))
    return rows


def sources():
    settings = config(ROOT / 'config/tengoku.json')
    aid_path = verified_source(settings, ARCHIVE)
    out = []
    for row in fssa_strings(member(aid_path)):
        out.append(dict(row, family='menus', archive=ARCHIVE, member=0))
    from tools import narration_catalog
    with CPK(aid_path) as archive:
        out.extend(dict(row,archive=ARCHIVE) for row in narration_catalog.sources(archive))
    for mid in (5, 6):
        for row in ui_string_table(member(aid_path, mid)):
            out.append(dict(row, id='aid:%d:%d' % (mid, row['id']), family='menus' if mid == 5 else 'help',
                archive=ARCHIVE, member=mid, offset=row['string_offset']))
    for rid, row in description_cells(rpw_text.load_rpw(settings)).items():
        out.append(dict(row, id='rpw:'+rid, family='skills' if row['family']=='sk-pri' else 'parts',
            encoding='cp932', offset=row['string_offset']))
    for row in eboot_text.records():
        if row['usage'].startswith('display(os-dialog') or (row.get('display') and row['usage'] in eboot_text.IN_SCOPE and (row.get('format') or row.get('fragment'))):
            raw = row['jp'].encode('cp932' if row['encoding']=='cp932' else 'utf-8')
            out.append(dict(id='eboot:'+row['va'], family='system' if row['usage'].startswith('display(os-dialog') else 'generated',
                text=row['jp'], raw=raw, encoding=row['encoding'], offset=int(row['offset'],16),
                format=bool(row.get('format')), fragment=bool(row.get('fragment'))))
    # Member 0's Gurren Lagann combination table names the spawned player
    # team. The remaining Japanese Lua literals are test strings or map keys.
    with CPK(verified_source(settings,UI_ARCHIVES[0])) as archive:
        entry, = [e for e in archive.files if e['id']==0]
        text = archive.read(entry).decode('cp932')
        candidates = [r for r in lua_strings(text) if JAPANESE.search(r['text'])]
        if len(candidates)!=1 or 'GRNRGN_TBL' not in text[:candidates[0]['start']]:
            raise ValueError('Lua team-name consumer changed')
        row = candidates[0]
        raw = row['text'].encode('cp932')
        at = len(text[:row['content_start']].encode('cp932'))
        out.append(dict(id='lua:0:%x'%at,family='menus',text=row['text'],raw=raw,
            encoding='cp932',offset=at,archive=UI_ARCHIVES[0],member=0))
    return [r for r in out if r['raw'] and JAPANESE.search(r['text'])]


def inventory():
    refs, _ = reference(ROOT.parent / 'SRW Z3')
    by_source = defaultdict(list)
    for row in refs:
        if row['source'] and row['en'] and row['kind']=='ui':
            by_source[row['source']].append(dict(group=row['group'], id=row['id'], text=row['en']))
    old = eboot_text.load()['strings']
    groups = {}
    for row in sources():
        jp = row['text']
        rid = sha256(jp.encode('utf-8'))[:20]
        entry = groups.setdefault(rid, dict(id=rid, jp=eboot_text.show(jp), existing_en=old.get(jp,{}).get('en'),
            reference_candidates=by_source[jp], occurrences=[], families=[]))
        if row['family'] not in entry['families']:
            entry['families'].append(row['family'])
        entry['occurrences'].append(dict(id=row['id'], encoding=row['encoding'], offset=row['offset'],
            source_sha256=sha256(row['raw']), **({'widget_offsets':row['widget_offsets']} if 'widget_offsets' in row else {})))
    return groups


def translations():
    rows = {}
    for path in sorted(DEST.glob('*.json')):
        for rid, row in json.loads(path.read_text(encoding='utf-8'))['strings'].items():
            if rid in rows:
                raise ValueError('Duplicate UI translation ID: '+rid)
            rows[rid] = row
    return rows


def checked(require_complete=True):
    rows = translations()
    grouped = defaultdict(list)
    for source in sources():
        grouped[sha256(source['text'].encode('utf-8'))[:20]].append(source)
    if set(rows)-set(grouped) or (require_complete and set(grouped)-set(rows)):
        raise ValueError('UI IDs differ: missing=%d foreign=%d' % (len(set(grouped)-set(rows)),len(set(rows)-set(grouped))))
    for rid, row in rows.items():
        jp = grouped[rid][0]['text']
        en = row.get('en')
        if not isinstance(en,str) or not en or row.get('reviewed') is not True:
            raise ValueError('UI translation is empty/unreviewed: '+rid)
        if eboot_text.FORMAT.findall(jp) != eboot_text.FORMAT.findall(en):
            raise ValueError('Printf argument sequence changed: '+rid)
        # Named OS substitutions are keys, so their identity and counts survive.
        import re
        pattern = r'【[^】]+】'
        is_os = any(s['family']=='system' and s['id'].startswith('eboot:') for s in grouped[rid])
        if is_os and Counter(re.findall(pattern,jp)) != Counter(re.findall(pattern,en)):
            raise ValueError('Runtime named tokens changed: '+rid)
        control = lambda text: Counter(re.findall(r'1\{[0-9A-F]{2}\}',text))
        if control(eboot_text.show(jp)) != control(en):
            raise ValueError('UI color controls changed: '+rid)
    return grouped, rows


def characters():
    grouped, rows = checked()
    res = eboot_text.resolver()
    chars = set()
    for rid,row in rows.items():
        if row.get('action') in ('keep-input','review-only','fragment'):
            continue
        text = eboot_text.unshow(lb.expand(row['en'],res))
        from tools import ui_description_layout,opening_narration
        text,condensed = ui_description_layout.profile(text,grouped[rid])
        from tools import tutorial_layout
        text,tutorial_condensed=tutorial_layout.profile(text,grouped[rid])
        condensed=condensed or tutorial_condensed
        if any(s['family']=='opening' for s in grouped[rid]):
            text,condensed = opening_narration.profile(text)
        for c in eboot_text.MARKUP.sub('',text):
            try:
                raw = c.encode('cp932')
            except UnicodeError:
                raw = b''
            if 32 <= ord(c) < 127 or (ord(c) >= 32 and not raw):
                chars.add(c)
                if condensed and ord(c)<128:
                    from tools.dialogue_layout import PREFIX
                    chars.add(PREFIX+c)
    return chars


def hook_entries(elf, mapping, base_entries):
    """Add UI keys from actual target sources; reviewed wording wins globally.

    Source game data stays pristine. Input grids and single glyph fragments
    have separate roles and must never become global dictionary replacements.
    """
    grouped, rows = checked()
    res = eboot_text.resolver()
    by_key = {e['key']:e for e in base_entries}
    skipped = []
    added = set()
    for rid, row in rows.items():
        action = row.get('action')
        if action in ('keep-input','review-only','fragment'):
            skipped.append(dict(id=rid,reason=action))
            continue
        en = eboot_text.unshow(lb.expand(row['en'],res))
        from tools import ui_description_layout
        en,condensed = ui_description_layout.profile(en,grouped[rid])
        from tools import tutorial_layout
        en,tutorial_condensed=tutorial_layout.profile(en,grouped[rid])
        condensed=condensed or tutorial_condensed
        if any(s['family']=='opening' for s in grouped[rid]):
            from tools.opening_narration import profile
            en,condensed = profile(en)
        active_mapping = mapping
        # The emblem footer draws a neutral text prefix beneath its colored
        # FSSA caption. Both paths must use the same native Latin masks.
        if rid in ('0ba4c2f203085202ecb4','443fd8711641b2ab41e5'):
            from tools.native_labels import PREFIX as LABEL_PREFIX
            active_mapping=dict(mapping)
            for c in set(en):active_mapping[c]=mapping[LABEL_PREFIX+c]
        if condensed:
            from tools.dialogue_layout import PREFIX
            active_mapping = dict(mapping)
            for token,code in mapping.items():
                if token.startswith(PREFIX):
                    active_mapping[token[len(PREFIX):]] = code
        for source in grouped[rid]:
            # OS and printf templates are implemented by ui_runtime, not an
            # exact match to their final generated display string.
            if source['family']=='system' and source['id'].startswith('eboot:'):
                continue
            if eboot_text.FORMAT.search(source['text']):
                continue
            try:
                key = source['raw'] if source['encoding']=='cp932' else ui_hook.utf8_key(source['raw'],elf)
                if ui_hook.extent(key+b'\0') != len(key):
                    raise ValueError('source is not one drawer string')
                english = eboot_text.encode(en,active_mapping,utf8_source=source['encoding']=='utf-8')
                problems = ui_hook.check_english(key,english,allow_escapes=True)
                if problems:
                    raise ValueError('; '.join(problems))
            except (ValueError,UnicodeError) as exc:
                skipped.append(dict(id=rid,source=source['id'],reason=str(exc)))
                continue
            entry = dict(key=key,english=english,id='expanded:'+rid+':'+source['encoding'],allow_escapes=True)
            if key in added and by_key[key]['english'] != english:
                raise ValueError('Conflicting reviewed UI meanings: '+rid)
            by_key[key] = entry
            added.add(key)
    return list(by_key.values()),dict(reviewed_strings=len(rows),source_occurrences=sum(map(len,grouped.values())),
        dictionary_keys=len(added),omitted=skipped,runtime_verified=False,layout_verified=False)


def draft_generated(apply=False):
    """Retain reviewed active wording; repair the five lossy purchase fragments."""
    items = json.loads((BRIEFS/'generated.json').read_text(encoding='utf-8'))['strings']
    corrections = {
        'd42bd513cf778a97225b': '」 is granted.',
        '7cfbf2047236e0355bb7': '」 unit(s) will be sold.',
        '78a767096b2fae05b84c': '」 will be purchased.',
        'c26131936557f8a29952': '+%s PP each.',
        'a97d7282f806c33f0aef': 'After clearing Episode %d',
    }
    rows = {}
    for rid, row in items.items():
        if not row['existing_en']:
            raise ValueError('Generated UI has no active draft: '+rid)
        rows[rid] = dict(en=corrections.get(rid,row['existing_en']), reviewed=True,
            notes='Source fragment/format; integration must preserve argument order and joined values.')
    print('Generated UI rows reviewed:',len(rows))
    for rid, text in corrections.items():
        print(rid,repr(items[rid]['existing_en']),'->',repr(text))
    if apply:
        write_json(DEST/'generated.json',dict(schema=1,strings=rows))
    else:
        print('DRY RUN: no files written.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--draft-generated', action='store_true')
    args = parser.parse_args()
    if args.draft_generated:
        draft_generated(args.apply)
        return
    items = inventory()
    groups = defaultdict(dict)
    for rid, row in items.items():
        family = next((f for f in ('system','generated','skills','parts','help','menus','opening') if f in row['families']))
        groups[family][rid] = row
    print(json.dumps({f:len(rows) for f, rows in groups.items()}, indent=2))
    for family, rows in groups.items():
        print(family, [(r['id'], r['jp'][:70], r['existing_en']) for r in list(rows.values())[:3]])
    if args.apply:
        for family, rows in groups.items():
            write_json(BRIEFS / (family+'.json'), dict(schema=1, strings=rows))
        print('Exported source-bound briefs:', BRIEFS)
    else:
        print('DRY RUN: no files written.')


if __name__ == '__main__':
    main()
