"""Source-driven inventories; reviewed translation and runtime coverage are separate."""
import json
import re
from collections import Counter, defaultdict

from tools.common import ROOT, sha256, sha256_file, write_json
from tools.cpk import CPK
from tools.source_text import byte_offsets, library_fields, lua_strings, nul_text_candidates, rpw_chunks, rpw_strings

BASE = '/PS3_GAME/USRDIR/'
STAGE = BASE + 'DATA/STAGE/STGZ3OF2.SDAT'
RPW = BASE + 'COMMONDATA/MTDATA/RPW_DATA.CPK'
LIBRARIES = {kind: BASE + 'COMMONDATA/MTDATA/MTZKN_%s.CPK' % code
             for kind, code in (('keyword', 'KW'), ('pilot', 'PT'), ('robot', 'RT'))}
UI_ARCHIVES = [BASE + 'COMMONDATA/KURODATA/LUACPK.CPK', BASE + 'DATA/AIDDATA/AIDDATAPACK.CPK']
FONT = BASE + 'DATA/TABATA/TPACKPS3.CPK'


def prepare_inventory(settings, stage, output):
    from tools.pipeline import verified_source
    ui_rows, stage_members, long_literals, library_records = [], [], [], []
    failures, archives = [], []
    member_dir = output / 'stage_members'
    member_dir.mkdir()
    archive = CPK(stage)
    archive_hash = sha256_file(stage)
    for entry in archive.files:
        data = archive.read(entry)
        member_hash = sha256(data)
        summary = {'member_id': entry['id'], 'stored_bytes': entry['size'], 'decoded_bytes': len(data),
                   'sha256': member_hash, 'classification': 'binary_or_non_cp932', 'scene_hints': [],
                   'stage_binding_verified': False, 'long_literals': 0}
        (member_dir / ('%05d.bin' % entry['id'])).write_bytes(data)
        try:
            text = data.decode('cp932') if b'\0' not in data else None
        except UnicodeDecodeError:
            text = None
        if text is not None:
            summary['classification'] = 'nul_free_cp932'
            # Source file comments are mapping clues, not confirmed gameplay stage IDs.
            summary['scene_hints'] = sorted(set(re.findall(r'Csz3_([A-Za-z0-9_]+)\.Cpp', text, re.I)))
            try:
                literals = list(lua_strings(text))
                offsets = byte_offsets(text)
                if offsets[-1] != len(data):
                    raise ValueError('cp932 byte-offset mapping mismatch')
                summary['literal_count'] = len(literals)
                for ordinal, literal in enumerate(literals):
                    start, end = offsets[literal['content_start']], offsets[literal['content_end']]
                    row = {'occurrence_id': 'stage:%05d:%d' % (entry['id'], start),
                           'archive': STAGE, 'decoded_archive_sha256': archive_hash,
                           'member_id': entry['id'], 'member_sha256': member_hash,
                           'offset': start, 'bytes': end - start, 'ordinal': ordinal,
                           'encoding': 'cp932', 'source_sha256': sha256(data[start:end]),
                           'literal_kind': literal['kind'], 'jp': literal['text'],
                           'context_before': text[max(0, literal['start'] - 180):literal['start']],
                           'role': 'unresolved', 'binding_reviewed': False}
                    if literal['kind'] == 'long':
                        long_literals.append(row)
                        summary['long_literals'] += 1
                    # All literals retained; no old dictionary filters the target denominator.
                    ui_rows.append(dict(row, inventory_method='lua_literal', consumer_verified=False))
            except ValueError as error:
                failures.append({'archive': STAGE, 'member_id': entry['id'], 'error': str(error)})
        stage_members.append(summary)
    write_json(output / 'stage_index.json', {'archive': STAGE, 'sha256': archive_hash,
               'mapping_note': 'Scene hints are source-comment identifiers; gameplay stage map is unverified.',
               'members': stage_members, 'parse_failures': failures})
    write_json(output / 'stage_long_literals.json', {'status': 'source_candidates_not_translation_assignments',
               'note': 'Includes non-dialogue literals. Event/speaker identities require further binding review.',
               'records': long_literals})
    archives.append({'path': STAGE, 'decoded_sha256': archive_hash, 'members': len(archive.files)})
    print('indexed %d stage members and %d long literals (%d parse failures)' %
          (len(stage_members), len(long_literals), len(failures)), flush=True)

    path = verified_source(settings, RPW)
    archive = CPK(path)
    if len(archive.files) != 1:
        raise ValueError('RPW archive member count changed')
    entry = archive.files[0]
    data = archive.read(entry)
    rpw_hash = sha256(data)
    rpw_rows = list(rpw_strings(data))
    write_json(output / 'rpw_inventory.json', {'archive': RPW, 'archive_sha256': sha256_file(path),
               'member_id': entry['id'], 'member_sha256': sha256(data), 'chunks': rpw_chunks(data),
               'pointer_schemas_verified': False, 'strings': rpw_rows})
    for row in rpw_rows:
        ui_rows.append(dict(row, occurrence_id='rpw:%d:%d' % (entry['id'], row['offset']),
                            archive=RPW, member_id=entry['id'], member_sha256=rpw_hash,
                            source_sha256=sha256(data[row['offset']:row['offset'] + row['bytes']]),
                            encoding='cp932', inventory_method='rpw_jstring', role='unresolved', consumer_verified=False))
    archives.append({'path': RPW, 'members': 1, 'sha256': sha256_file(path)})
    for kind, source in LIBRARIES.items():
        path = verified_source(settings, source)
        archive = CPK(path)
        for entry in archive.files:
            data = archive.read(entry)
            magic, fields = library_fields(data)
            library_records.append({'archive': source, 'member_id': entry['id'], 'sha256': sha256(data),
                                    'kind': kind, 'magic': magic, 'fields': fields})
        archives.append({'path': source, 'members': len(archive.files), 'sha256': sha256_file(path)})
    write_json(output / 'library_inventory.json', {'records': library_records, 'identities_reviewed': False})

    reference = json.loads((ROOT / 'work/glossary/reference/jigoku_glossary.json').read_text(encoding='utf-8'))
    by_name = defaultdict(list)
    for index, term in enumerate(reference['terms']):
        by_name[(term['jp'], term['kind'])].append({'reference_index': index, 'en': term['en'],
                  'source': term.get('source'), 'status': term.get('status'), 'legacy_zukan_id': term.get('zukan_id')})
    candidates = []
    name_tags = {'keyword': {'WORD'}, 'pilot': {'CHFN', 'CHNN'}, 'robot': {'RBTN', 'RBN2'}}
    for record in library_records:
        for field in record['fields']:
            if field['tag'] in name_tags[record['kind']] and field['text']:
                candidates.append({'target_archive': record['archive'], 'target_member_id': record['member_id'],
                    'target_member_sha256': record['sha256'], 'field': field['tag'], 'jp': field['text'],
                    'kind': record['kind'], 'target_context': record['fields'],
                    'reference_candidates': by_name.get((field['text'], record['kind']), []),
                    'identity_reviewed': False, 'approved_english': None, 'target_token': None})
    write_json(output / 'glossary_candidates.json', {'active_glossary': False, 'candidates': candidates})
    print('indexed RPW, library records and %d unreviewed glossary candidates' % len(candidates), flush=True)

    scanned_members = []
    for source in UI_ARCHIVES:
        path = verified_source(settings, source)
        archive = CPK(path)
        for entry in archive.files:
            data = archive.read(entry)
            rows = list(nul_text_candidates(data))
            member_hash = sha256(data)
            scanned_members.append({'archive': source, 'member_id': entry['id'], 'sha256': sha256(data),
                                    'bytes_scanned': len(data), 'candidate_runs': len(rows)})
            for row in rows:
                ui_rows.append(dict(row, occurrence_id='%s:%d:%d' % (source, entry['id'], row['offset']),
                    archive=source, member_id=entry['id'], member_sha256=member_hash, encoding='cp932',
                    source_sha256=sha256(data[row['offset']:row['offset'] + row['bytes']]),
                    inventory_method='heuristic_nul_run', role='unresolved', consumer_verified=False))
        archives.append({'path': source, 'members': len(archive.files), 'sha256': sha256_file(path)})
    catalogue = json.loads((ROOT / 'work/ui/reference/jigoku_ui/catalogue.json').read_text(encoding='utf-8'))
    by_jp = defaultdict(list)
    for row in catalogue['entries']:
        by_jp[row['row']['jp']].append(row['reference_id'])
    for row in ui_rows:
        row['reference_candidates'] = by_jp.get(row['jp'], [])
        row['disposition'] = 'unresolved'
        row['proposed_english'] = None
    write_json(output / 'ui_candidates.json', {'state': 'initial_source_discovery',
        'scope': ['All lexed stage literals', 'All RPW j-string slots', 'Heuristic NUL-delimited cp932 runs in LUACPK and AIDDATAPACK'],
        'limitations': ['No executable discovery', 'No artwork transcription', 'No verified consumers or widget bounds',
                       'Generated/split/escaped variants need structural discovery', 'No absence or completeness claims'],
        'scanned_members': scanned_members, 'parse_failures': failures, 'occurrences': ui_rows})
    path = verified_source(settings, FONT)
    print('UI source candidates written; inventorying artwork archive', flush=True)
    archive = CPK(path)
    font_members = []
    for entry in archive.files:
        data = archive.read(entry)
        font_members.append({'member_id': entry['id'], 'bytes': len(data), 'sha256': sha256(data),
                             'first_32_bytes_hex': data[:32].hex(), 'role_verified': False})
    write_json(output / 'artwork_inventory.json', {'archive': FONT, 'archive_sha256': sha256_file(path),
               'glyph_allocation_verified': False, 'members': font_members})
    archives.append({'path': FONT, 'members': len(archive.files), 'sha256': sha256_file(path)})
    return {'schema': 1, 'title_id': settings['title_id'], 'archives': archives,
        'stage_members': len(stage_members), 'stage_text_members': sum(m['classification'] == 'nul_free_cp932' for m in stage_members),
        'stage_long_literals': len(long_literals), 'stage_members_with_scene_hints': sum(bool(m['scene_hints']) for m in stage_members),
        'source_parse_failures': failures, 'rpw_chunks': len(rpw_chunks(verified_rpw(settings))),
        'rpw_string_slots': len(rpw_rows), 'library_records_by_kind': dict(Counter(r['kind'] for r in library_records)),
        'glossary_candidates': len(candidates), 'ui_source_candidates': len(ui_rows),
        'ui_candidates_with_reference_matches': sum(bool(r['reference_candidates']) for r in ui_rows),
        'artwork_members': len(font_members), 'runtime_verified': False, 'translation_records_written': 0}


def verified_rpw(settings):
    from tools.pipeline import verified_source
    archive = CPK(verified_source(settings, RPW))
    return archive.read(archive.files[0])
