"""Audit the released UI against current Jigoku references; preview by default.

Only --apply writes a source-free evidence report. No translation, game input,
build or reference-project file is changed. Exact matches are reuse candidates,
not reviewed Tengoku translations or proof of a live screen's rendering path.
"""
import argparse
import json
import struct
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import eboot_text, rpw_text, ui_hook
from tools.cpk import CPK
from tools.pipeline import config, verified_source
from tools.self_elf import decrypt, EBOOT
from tools.source_text import rpw_chunks, lua_strings, JAPANESE
from tools.aid_art import ARCHIVE as AID
from tools.inventory import UI_ARCHIVES


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def member(path, mid=0):
    with CPK(path) as archive:
        entry, = [e for e in archive.files if e['id'] == mid]
        return archive.read(entry)


def reference(reference_root):
    old = read(ROOT / 'work/ui/reference/jigoku_ui/catalogue.json')
    groups = {Path(r['source_file']).stem for r in old['entries']}
    # Current canonical wording includes later fixes absent from the old pack.
    groups.update(p.stem for p in (reference_root / 'localization/messages').glob('ui.*.json')
                  if not p.stem.startswith('ui.vita'))
    groups.update(('gift_report_hook', 'deployment_hook', 'squad_names_hook',
                   'trader_spirit_prompts', 'trader_upgrade_text', 'weapon_requirement_runtime'))
    refs, inputs = [], {}
    for group in sorted(groups):
        src = reference_root / 'localization/messages' / (group + '.json')
        en = reference_root / 'localization/locales/en' / (group + '.json')
        if not src.exists() or not en.exists():
            raise ValueError('Missing current canonical reference: ' + group)
        sources, english = read(src)['messages'], read(en)['messages']
        inputs[group] = {'source_file_sha256': sha256_file(src), 'locale_file_sha256': sha256_file(en)}
        for rid, row in sources.items():
            refs.append(dict(id=rid, group=group, source=row.get('source'),
                             kind=row.get('kind'), context=row.get('context', {}),
                             en=english.get(rid, {}).get('text'),
                             locale_status=english.get(rid, {}).get('status')))
    return refs, inputs


def description_cells(data):
    chunks = {c['name']: c for c in rpw_chunks(data)}
    _, pool = rpw_text.pool_of(data)
    out = {}
    starts = {0} | {i + 1 for i, b in enumerate(pool) if b == 0}
    for name, stride, cols in [('sk-pri', 13, (4, 5)), ('boost-p', 21, range(3, 9))]:
        chunk = chunks[name]
        size = chunk['body_end'] - chunk['body_offset']
        if size % (stride * 4):
            raise ValueError('Description record stride changed: ' + name)
        for record in range(size // (stride * 4)):
            for col in cols:
                at = chunk['body_offset'] + (record * stride + col) * 4
                pointer = struct.unpack_from('<I', data, at)[0]
                if pointer not in starts:
                    raise ValueError('Description pointer is not a string start')
                raw = pool[pointer:pool.index(b'\0', pointer)]
                out['%s:%d:%d' % (name, record, col)] = dict(
                    family=name, pointer_offset=at, pool_offset=pointer,
                    string_offset=chunks['j-string']['body_offset'] + pointer,
                    raw=raw, text=raw.decode('cp932'))
    return out


def exact_offsets(blob, raw):
    """Whole NUL-delimited source strings only; reject suffix-only matches."""
    offsets, pos = [], 0
    needle = raw + b'\0'
    while True:
        pos = blob.find(needle, pos)
        if pos < 0:
            return offsets
        if pos == 0 or blob[pos - 1] == 0:
            offsets.append(pos)
        pos += 1


def ui_string_table(blob):
    """Read Tengoku's actual DIXT offsets into its TDXT NUL string pool."""
    if blob[:4] not in (b'SB2T', b'UB2T') or blob[16:20] != b'DIXT':
        raise ValueError('Unknown UI string-table wrapper')
    size = struct.unpack_from('>I', blob, 24)[0]
    text_at = 32 + size
    if size % 4 or blob[text_at:text_at + 4] != b'TDXT':
        raise ValueError('UI offset table geometry changed')
    text_size = struct.unpack_from('>I', blob, text_at + 8)[0]
    pool_at = text_at + 16
    if pool_at + text_size != len(blob):
        raise ValueError('UI string pool size mismatch')
    pool = blob[pool_at:]
    starts = {0} | {i + 1 for i, value in enumerate(pool) if value == 0}
    encoding = 'cp932' if blob[:4] == b'SB2T' else 'utf-8'
    rows = []
    for rid in range(size // 4):
        pointer_at = 32 + 4 * rid
        pos = struct.unpack_from('>I', blob, pointer_at)[0]
        if pos not in starts or pos >= len(pool):
            raise ValueError('UI table pointer is not a string start')
        raw = pool[pos:pool.index(b'\0', pos)]
        rows.append(dict(id=rid, pointer_offset=pointer_at, string_offset=pool_at + pos,
                         raw=raw, text=raw.decode(encoding), encoding=encoding))
    return rows


def audit(reference_root, version):
    settings = config(ROOT / 'config/tengoku.json')
    build_dir = ROOT / 'work/output/builds' / version
    build = read(build_dir / 'build.json')
    for name in ('EBOOT.BIN', 'RPW_DATA.CPK', 'AIDDATAPACK.CPK'):
        if sha256_file(build_dir / name) != build['outputs'][name]:
            raise ValueError('Selected build output hash mismatch: ' + name)
    mapping = build['mapping']
    elf, _ = decrypt(verified_source(settings, EBOOT).read_bytes())
    entries, skipped = eboot_text.hook_entries(elf, mapping, lambda raw: ui_hook.utf8_key(raw, elf))
    # Reproduce the historical 0.5.2 cap even after later hook improvements.
    # The old artifact is immutable evidence, not a build from current inputs.
    if version == '0.5.2':
        oversized = [e for e in entries if len(e['english']) >= 4096]
        entries = [e for e in entries if len(e['english']) < 4096]
        if oversized:
            reason = 'English is not one drawer string (odd trailing byte, 0x2f or > 4096 bytes)'
            skipped['refused by hook: '+reason[:60]] += len(oversized)
    if len(entries) != build['executable']['ui_hook']['entries'] or dict(skipped) != build['executable']['ui_hook']['skipped']:
        raise ValueError('Current UI hook inputs differ from the selected build')
    hooked = {e['key'] for e in entries}
    executable = (build_dir / 'EBOOT.BIN').read_bytes()
    _, _, phs, _ = ui_hook._headers(executable)
    def read_va(va, size):
        segment, = [p for p in phs if p[0] == 1 and p[3] <= va and va + size <= p[3] + p[5]]
        off = segment[2] + va - segment[3]
        return executable[off:off + size]
    if hooked != set(ui_hook.slot_map(read_va)):
        raise ValueError('Current dictionary differs from actual built UI table')
    refs, reference_inputs = reference(reference_root)
    by_source = defaultdict(list)
    for ref in refs:
        if ref['source']:
            by_source[ref['source']].append(ref)

    rpw = rpw_text.load_rpw(settings)
    rpw_built = member(build_dir / 'RPW_DATA.CPK')
    desc, built_desc = description_cells(rpw), description_cells(rpw_built)
    if set(desc) != set(built_desc):
        raise ValueError('Built description columns differ from the source')
    desc_groups = defaultdict(list)
    desc_stats = {}
    for rid, row in desc.items():
        if row['raw'] != built_desc[rid]['raw']:
            raise ValueError('Description changed in build: ' + rid)
        if row['raw']:
            desc_groups[(row['family'], row['text'])].append((rid, row))
    descriptions = []
    for (family, jp), cells in sorted(desc_groups.items(), key=lambda item: item[1][0][0]):
        raw = cells[0][1]['raw']
        candidates = [r for r in by_source[jp] if r['en'] is not None and r['kind'] == 'ui']
        descriptions.append(dict(source_sha256=sha256(raw), source_bytes=len(raw),
            family=cells[0][1]['family'], exact_hook_key=raw in hooked,
            source_and_built_descriptions_identical=True,
            cells=[dict(id=rid, pointer_offset=row['pointer_offset'], string_offset=row['string_offset']) for rid, row in cells],
            reference_candidates=[dict(id=r['id'], group=r['group'], en=r['en'], status=r['locale_status']) for r in candidates]))
    for family in ('sk-pri', 'boost-p'):
        rows = [r for r in descriptions if r['family'] == family]
        desc_stats[family] = dict(nonempty_cells=sum(len(r['cells']) for r in rows),
            distinct_strings=len(rows), exact_hook_keys=sum(r['exact_hook_key'] for r in rows),
            missing_hook_strings=sum(not r['exact_hook_key'] for r in rows),
            strings_with_current_jigoku_candidates=sum(bool(r['reference_candidates']) for r in rows))

    aid = member(verified_source(settings, AID))
    aid_built = member(build_dir / 'AIDDATAPACK.CPK')
    if aid != aid_built:
        raise ValueError('This audit expects the released UI layout member to be untouched')
    aid_rows, group_stats = [], defaultdict(Counter)
    for jp, same in by_source.items():
        try:
            raw = jp.encode('cp932')
        except UnicodeError:
            continue
        offsets = exact_offsets(aid, raw)
        if not offsets:
            continue
        ui_refs = [r for r in same if r['kind'] == 'ui']
        if not ui_refs:
            continue
        covered = raw in hooked
        for group in {r['group'] for r in ui_refs}:
            group_stats[group]['distinct_target_strings'] += 1
            group_stats[group]['exact_hook_keys' if covered else 'missing_hook_keys'] += 1
        aid_rows.append(dict(source_sha256=sha256(raw), source_bytes=len(raw),
            target_offsets=offsets, exact_hook_key=covered, built_member_unchanged=True,
            reference_candidates=[dict(id=r['id'], group=r['group'], en=r['en'], status=r['locale_status']) for r in ui_refs]))

    inventory = eboot_text.inventory()
    source_records = eboot_text.records()
    records_by_jp = defaultdict(list)
    for record in source_records:
        if record.get('display') and record['usage'] in eboot_text.IN_SCOPE:
            records_by_jp[record['jp']].append(record)
    eboot_gaps = []
    for jp, row in inventory.items():
        reason = 'format/fragment' if row['format'] or row['fragment'] else None
        records = records_by_jp[jp]
        if reason is None:
            keys = []
            for record in records:
                off = int(record['offset'], 16)
                raw = elf[off:off + record['bytes']]
                keys.append(raw if record['encoding'] == 'cp932' else ui_hook.utf8_key(raw, elf))
            if any(key in hooked for key in keys):
                continue
            reason = 'refused by exact hook'
        eboot_gaps.append(dict(source_sha256=sha256(jp.encode('utf-8')), families=row['families'],
            vas=row['vas'], reason=reason, en=eboot_text.load()['strings'][jp].get('en')))
    os_rows = [r for r in source_records if r['usage'].startswith('display(os-dialog')]
    art = read(ROOT / 'work/translation/en/ui/aiddata_art.json')['cells']
    member4 = member(verified_source(settings, AID), 4)
    if member4 != member(build_dir / 'AIDDATAPACK.CPK', 4):
        raise ValueError('Unresolved UI layout/text member changed in selected build')
    aid_tables = {}
    converter_table = ui_hook.unicode_table(elf)
    for mid in (5, 6):
        original = member(verified_source(settings, AID), mid)
        if original != member(build_dir / 'AIDDATAPACK.CPK', mid):
            raise ValueError('Additional UI table changed in selected build')
        cells = ui_string_table(original)
        strings = defaultdict(list)
        for cell in cells:
            if JAPANESE.search(cell['text']):
                strings[cell['text']].append(cell)
        rows = []
        for jp, occurrences in strings.items():
            raw = occurrences[0]['raw']
            key = raw if mid == 5 else ui_hook.convert(raw, converter_table)
            candidates = [r for r in by_source[jp] if r['kind'] == 'ui']
            rows.append(dict(source_sha256=sha256(raw), exact_hook_key=key in hooked,
                source_bytes=len(raw), existing_executable_english=eboot_text.load()['strings'].get(jp, {}).get('en'),
                cells=[{k: c[k] for k in ('id', 'pointer_offset', 'string_offset', 'encoding')} for c in occurrences],
                reference_candidates=[dict(id=r['id'], group=r['group'], en=r['en'], status=r['locale_status']) for r in candidates]))
        aid_tables[str(mid)] = dict(source_and_built_sha256=sha256(original), built_member_unchanged=True,
            wrapper=original[:4].decode('ascii'), records=len(cells),
            japanese_occurrences=sum(len(r['cells']) for r in rows), japanese_distinct_strings=len(rows),
            missing_exact_hook_strings=sum(not r['exact_hook_key'] for r in rows),
            strings_with_current_jigoku_candidates=sum(bool(r['reference_candidates']) for r in rows),
            rows=rows)
    lua_scope = []
    with CPK(verified_source(settings, UI_ARCHIVES[0])) as archive:
        for entry in archive.files:
            raw = archive.read(entry)
            rows = [r for r in lua_strings(raw.decode('cp932')) if JAPANESE.search(r['text'])]
            lua_scope.append(dict(member=entry['id'], source_sha256=sha256(raw),
                japanese_literals=len(rows), reference_matched_literals=sum(r['text'] in by_source for r in rows),
                roles_verified=False))
    report = dict(schema=1, date='2026-10-10', title_id='BLJS10299', build_version=version,
        purpose='Source and built-artifact coverage comparison; runtime remains unverified',
        remaining_total=None,
        limitations=['Reference matches are candidates, not context-reviewed target translations.',
            'Source byte matches do not establish widget consumers or runtime visibility.',
            'Unmatched Jigoku strings are unresolved, not proven absent in Tengoku.',
            'Dynamic joins, numeric variants, all UI states and untranscribed artwork are not a complete inventory.',
            'Current Jigoku canonical files include unbuilt local fixes; fingerprints pin the consulted state.'],
        reference=dict(commit=subprocess.check_output(['git', '-C', str(reference_root), 'rev-parse', 'HEAD'], text=True).strip(),
            groups=len(reference_inputs), records=len(refs), unavailable_sources=sum(not r['source'] for r in refs),
            inputs=reference_inputs),
        build=dict(source_report_sha256=sha256_file(build_dir / 'build.json'),
            executable_ui_entries=len(entries), spirit_occurrences=build['spirit_occurrences'],
            rpw_name_cells=build['rpw_names']['cells'], mission_strings=build['mission_strings'],
            squad_names=build['squad_names'], episode_title_cards=len(build['title_cards_rendered']),
            aid_art_cells=len(art), runtime_verified=build['runtime_verified']),
        eboot=dict(translated_distinct_strings=len(eboot_text.load()['strings']), skipped=dict(skipped),
            gaps=eboot_gaps, os_dialog_occurrences=len(os_rows), os_dialog_distinct_strings=len({r['jp'] for r in os_rows})),
        rpw=dict(source_member_sha256=sha256(rpw), built_member_sha256=sha256(rpw_built),
            descriptions=descriptions, summary=desc_stats),
        aiddata=dict(archive=AID, member=0, source_and_built_sha256=sha256(aid), bytes=len(aid),
            reference_matched_distinct_strings=len(aid_rows),
            missing_exact_hook_distinct_strings=sum(not r['exact_hook_key'] for r in aid_rows),
            group_counts={k: dict(v) for k, v in sorted(group_stats.items())}, rows=aid_rows,
            additional_tables=aid_tables,
            unresolved_member4={'source_and_built_sha256': sha256(member4), 'built_member_unchanged': True,
                'state': 'Binary layout/text records; structural and consumer discovery still required'}),
        luacpk=dict(archive=UI_ARCHIVES[0], members=lua_scope,
            note='All nine members lexed; source roles and dynamically assembled values remain unresolved.'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=ROOT.parent / 'SRW Z3')
    parser.add_argument('--version', default='0.5.2')
    parser.add_argument('--output', type=Path, default=ROOT / 'work/ui/coverage_2026-10-10.json')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report = audit(args.reference.resolve(), args.version)
    print(json.dumps(dict(build=report['build'], reference_groups=report['reference']['groups'],
        eboot_skipped=report['eboot']['skipped'], os_dialogs=report['eboot']['os_dialog_distinct_strings'],
        rpw_descriptions=report['rpw']['summary'],
        aiddata_matched_strings=report['aiddata']['reference_matched_distinct_strings'],
        aiddata_missing_hook_strings=report['aiddata']['missing_exact_hook_distinct_strings'],
        aiddata_additional_tables={k: {key: value for key, value in v.items() if key != 'rows'}
            for k, v in report['aiddata']['additional_tables'].items()},
        aiddata_groups=report['aiddata']['group_counts']), indent=2))
    print('Missing label samples (Jigoku candidates; target meaning/layout review pending):')
    for row in [r for r in report['aiddata']['rows'] if not r['exact_hook_key']][:10]:
        print(row['target_offsets'][:3], [r['en'] for r in row['reference_candidates']][:3])
    if args.apply:
        if args.output.exists():
            raise ValueError('Refuse to overwrite existing audit evidence')
        write_json(args.output, report)
        print('Saved:', args.output)
    else:
        print('DRY RUN: no files written; use --apply to save the evidence report.')


if __name__ == '__main__':
    main()
