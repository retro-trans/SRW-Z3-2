"""Bind and validate Spirit UI translations against original Tengoku records.

python -m tools.ui_spirits inspect
python -m tools.ui_spirits check
python -m tools.ui_spirits export [--apply]

Export produces reviewed text and a source audit, not a game patch. Runtime
consumers, font encoding and screen fit have not been established.
"""
import argparse
import json
import re
import struct
import unicodedata
from collections import Counter

from tools.common import ROOT, sha256, sha256_file, write_json
from tools.cpk import CPK
from tools.inventory import RPW, STAGE
from tools.pipeline import config, verified_source
from tools.source_text import rpw_chunks, rpw_strings

FIELDS = {'name': 1, 'abbreviation': 2, 'description': 3}
TOKEN = re.compile(r'\$\$([^$\n]+)\$\$')
SCHEMA_PATH = ROOT / 'work/ui/schemas/rpw_spirit.json'
TRANSLATION_PATH = ROOT / 'work/translation/en/ui/spirit_commands.json'
GLOSSARY_PATH = ROOT / 'work/glossary/glossary.json'


def read_source(settings):
    path = verified_source(settings, RPW)
    archive = CPK(path)
    if len(archive.files) != 1:
        raise ValueError('RPW no longer has exactly one member')
    member = archive.files[0]
    data = archive.read(member)
    chunks = [c for c in rpw_chunks(data) if c['name'] == 'spirit']
    if len(chunks) != 1:
        raise ValueError('expected exactly one spirit chunk')
    chunk = chunks[0]
    body = data[chunk['body_offset']:chunk['body_end']]
    strings = {s['body_offset']: s for s in rpw_strings(data) if not s['terminal_empty']}
    # Re-derive the smallest candidate record stride from this target table.
    # Full semantic review pins this hypothesis in the separately saved schema.
    candidates = []
    for stride in range(16, 129, 4):
        if len(body) % stride:
            continue
        if all(struct.unpack_from('<I', body, start + column * 4)[0] in strings
               for start in range(0, len(body), stride) for column in FIELDS.values()):
            candidates.append(stride)
    if not candidates or min(candidates) != 20:
        raise ValueError('target Spirit record structure changed: %s' % candidates)
    records = []
    for index in range(len(body) // 20):
        record_offset = chunk['body_offset'] + index * 20
        record_data = data[record_offset:record_offset + 20]
        words = struct.unpack('<5I', record_data)
        fields = {}
        for role, column in FIELDS.items():
            string = strings[words[column]]
            raw = data[string['offset']:string['offset'] + string['bytes']]
            fields[role] = {'occurrence_id': 'rpw:%d:spirit:%d:%s' % (member['id'], index, role),
                'pointer_offset': record_offset + 4 * column, 'column': column,
                'string_body_offset': words[column], 'string_offset': string['offset'],
                'string_ordinal': string['ordinal'], 'source_bytes': string['bytes'],
                'source_sha256': sha256(raw), 'jp': string['jp']}
        records.append({'record_index': index, 'record_offset': record_offset,
                        'record_sha256': sha256(record_data), 'metadata_words': [words[0], words[4]],
                        'fields': fields})
    return {'schema': 1, 'title_id': settings['title_id'], 'archive': RPW,
            'archive_sha256': sha256_file(path), 'member_id': member['id'],
            'member_sha256': sha256(data), 'chunk': 'spirit', 'chunk_offset': chunk['body_offset'],
            'chunk_bytes': len(body), 'chunk_sha256': sha256(body),
            'candidate_strides': candidates, 'record_stride': 20,
            'string_columns': FIELDS, 'runtime_consumer_verified': False, 'records': records}


def resolve(text, glossary):
    terms = glossary['terms']
    keys = [t['token'] for t in terms]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate glossary token')
    by_token = {t['token']: t for t in terms}
    def replace(match):
        key = match.group(1)
        if key not in by_token:
            raise ValueError('unknown target glossary token: ' + key)
        value = by_token[key]['en']
        if not value or '$$' in value:
            raise ValueError('invalid glossary expansion')
        return value
    rendered = TOKEN.sub(replace, text)
    if '$$' in rendered:
        raise ValueError('malformed glossary token')
    return rendered


def numbers(text):
    normalized = unicodedata.normalize('NFKC', text)
    # Compare numeric meaning across ordinary translation forms, not just
    # digit spelling. This is a narrow check, not a substitute for review.
    normalized = re.sub(r'一(?=度|戦闘|回)', '1', normalized)
    normalized = normalized.replace('半分', '0.5')
    normalized = re.sub(r'\bat once\b', 'simultaneously', normalized, flags=re.I)
    for pattern, value in ((r'\b(?:one|once)\b', '1'), (r'\bdoubles?\b', '2'),
                           (r'\b(?:half|halves)\b', '0.5')):
        normalized = re.sub(pattern, value, normalized, flags=re.I)
    return Counter(re.findall(r'\d+(?:\.\d+)?(?:/\d+)?', normalized))


def controls(text):
    return Counter(re.findall(r'\$[A-Za-z]|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdifuxX](?![A-Za-z])|[《》]', text))


def validate(source, schema, translation, glossary):
    for key in ('title_id', 'archive', 'archive_sha256', 'member_id', 'member_sha256',
                'chunk', 'chunk_offset', 'chunk_bytes', 'chunk_sha256', 'record_stride', 'string_columns'):
        if schema.get(key) != source[key]:
            raise ValueError('source/schema drift: ' + key)
    if translation['title_id'] != source['title_id'] or glossary['meta']['title_id'] != source['title_id']:
        raise ValueError('translation/glossary target title mismatch')
    if translation['source_member_sha256'] != source['member_sha256']:
        raise ValueError('translation member fingerprint mismatch')
    expected = {field['occurrence_id']: (record, role, field)
                for record in source['records'] for role, field in record['fields'].items()}
    supplied = [r['occurrence_id'] for r in translation['entries']]
    if len(supplied) != len(set(supplied)):
        raise ValueError('duplicate translation assignment')
    if set(supplied) != set(expected):
        raise ValueError('source coverage mismatch: missing=%s extra=%s' %
                         (sorted(set(expected) - set(supplied)), sorted(set(supplied) - set(expected))))
    name_bindings = {}
    for term in glossary['terms']:
        if term.get('status') not in ('official', 'proposed') or term.get('meaning_reviewed') is not True:
            raise ValueError('unreviewed or ambiguous target glossary identity')
        if term['kind'] != 'spirit' or term['token'] != term['jp'] + '#spirit':
            raise ValueError('unexpected token kind or identity in Spirit glossary')
        target = term['target']
        if target.get('archive') != source['archive'] or target.get('member_id') != source['member_id']:
            raise ValueError('glossary target archive/member mismatch')
        identity = target['occurrence_id']
        if identity not in expected or identity in name_bindings:
            raise ValueError('invalid or duplicate glossary target binding')
        record, role, field = expected[identity]
        if role != 'name' or field['jp'] != term['jp'] or target['source_sha256'] != field['source_sha256']:
            raise ValueError('glossary identity disagrees with target name field')
        if target['member_sha256'] != source['member_sha256']:
            raise ValueError('glossary source member drift')
        name_bindings[identity] = term['token']
    by_jp = {t['jp']: t['token'] for t in glossary['terms']}
    output, excluded = [], []
    for entry in translation['entries']:
        record, role, field = expected[entry['occurrence_id']]
        for key in ('jp', 'source_sha256', 'pointer_offset', 'string_body_offset'):
            if entry[key] != field[key]:
                raise ValueError('translation binding drift: %s %s' % (entry['occurrence_id'], key))
        if entry['record_sha256'] != record['record_sha256']:
            raise ValueError('source record drift')
        if entry['status'] == 'excluded':
            if record['record_index'] != 0 or not entry.get('reason') or entry.get('en') is not None:
                raise ValueError('only the documented empty Spirit sentinel may be excluded')
            excluded.append(entry['occurrence_id'])
            continue
        if record['record_index'] == 0 or entry['status'] != 'reviewed':
            raise ValueError('sentinel or unreviewed record supplied as translation')
        authored = entry['en']
        if not isinstance(authored, str) or not authored:
            raise ValueError('empty translation')
        if role == 'name' and field['jp'] != '？？？？':
            if authored != '$$%s$$' % name_bindings.get(field['occurrence_id']):
                raise ValueError('command name must use its bound target glossary token')
        if role == 'description':
            quoted = re.findall('「([^」]+)」', field['jp'])
            required = [by_jp[name] for name in quoted]
            actual = TOKEN.findall(authored)
            if required != actual:
                raise ValueError('referenced Spirit identities/order changed: ' + entry['occurrence_id'])
        rendered = resolve(authored, glossary)
        if field['jp'] and set(field['jp']) == {'？'} and rendered != '?' * len(field['jp']):
            raise ValueError('unknown-state placeholder changed')
        if not rendered.isascii():
            raise ValueError('this authoring batch requires plain ASCII English plus line feeds')
        if any(ord(c) < 32 and c != '\n' for c in rendered):
            raise ValueError('unexpected control character in English')
        if role == 'description' and numbers(field['jp']) != numbers(rendered):
            raise ValueError('effect numbers changed: ' + entry['occurrence_id'])
        if controls(field['jp']) != controls(rendered) or field['jp'].count('\n') != rendered.count('\n'):
            raise ValueError('controls or authored line count changed: ' + entry['occurrence_id'])
        output.append(dict(entry, role=role, rendered_en=rendered,
                           max_line_characters=max(map(len, rendered.split('\n'))),
                           glyphs_verified=False, layout_verified=False, binary_ready=False))
    command_records = sum(r['fields']['name']['jp'] not in ('－－', '？？？？') for r in source['records'])
    if len(name_bindings) != command_records:
        raise ValueError('glossary command coverage mismatch')
    return {'schema': 1, 'title_id': source['title_id'], 'family': 'spirit_commands',
            'scope': 'RPW spirit table only, all name/abbreviation/description occurrences',
            'source_records': len(source['records']), 'source_occurrences': len(expected),
            'reviewed_occurrences': len(supplied), 'translated_occurrences': len(output),
            'excluded_occurrences': excluded, 'command_terms': len(name_bindings),
            'source_member_sha256': source['member_sha256'], 'source_chunk_sha256': source['chunk_sha256'],
            'layout_verified': False, 'runtime_verified': False, 'binary_ready': False,
            'remaining': ['Font mapping and encoding', 'Actual draw consumers and shared-string handling',
                          'Widget fit and compact effect badges', 'Tutorial/other UI occurrences', 'Runtime checks'],
            'entries': output}


def load_and_validate(settings):
    source = read_source(settings)
    def load(path):
        return json.loads(path.read_text(encoding='utf-8'))
    return validate(source, load(SCHEMA_PATH), load(TRANSLATION_PATH), load(GLOSSARY_PATH))


def related(settings, apply=False):
    """Search the existing source inventory, then verify every matching span.

    This is a bounded follow-up search, not a complete UI-family inventory.
    Stage hits may be dialogue; none is assigned or translated automatically.
    """
    index_path = settings['work'] / 'prepared/ui_candidates.json'
    candidates = json.loads(index_path.read_text(encoding='utf-8'))['occurrences']
    glossary = json.loads(GLOSSARY_PATH.read_text(encoding='utf-8'))
    names = {t['jp'] for t in glossary['terms']}
    source = read_source(settings)
    bound_offsets = {f['string_offset'] for r in source['records'] for f in r['fields'].values()}
    archives, members, hits = {}, {}, []
    for row in candidates:
        quoted = re.findall('[「『]([^」』]+)[」』]', row['jp'])
        matched_terms = sorted(names.intersection(quoted))
        if '精神' not in row['jp'] and not matched_terms:
            continue
        key = (row['archive'], row['member_id'])
        if key not in members:
            if key[0] not in archives:
                if key[0] == STAGE:
                    path = settings['work'] / 'prepared/STGZ3OF2.dec.cpk'
                    prepared = json.loads((settings['work'] / 'prepared/inventory_summary.json').read_text(encoding='utf-8'))
                    if sha256_file(path) != prepared['sdat']['decoded_sha256']:
                        raise ValueError('prepared stage archive drift')
                else:
                    path = verified_source(settings, key[0])
                archives[key[0]] = CPK(path)
            archive = archives[key[0]]
            entry = next(e for e in archive.files if e['id'] == key[1])
            data = archive.read(entry)
            members[key] = (data, sha256(data))
        data, fingerprint = members[key]
        span = data[row['offset']:row['offset'] + row['bytes']]
        if fingerprint != row['member_sha256'] or sha256(span) != row['source_sha256'] or span.decode('cp932') != row['jp']:
            raise ValueError('discovery source span drift: ' + row['occurrence_id'])
        hits.append(dict(row, source_span_reverified=True, quoted_spirit_candidates=matched_terms,
                         already_bound_in_spirit_table=key[0] == RPW and row['offset'] in bound_offsets,
                         followup_state='classify_context_before_translation'))
    by_archive = Counter(r['archive'] for r in hits)
    report = {'schema': 1, 'title_id': settings['title_id'], 'source_index_sha256': sha256_file(index_path),
              'scope': 'Existing stage-literal/RPW/NUL-run discovery index; no executable, library-description or artwork sweep',
              'filter': 'Contains 精神 or a quoted Japanese name from the target Spirit glossary',
              'candidates_searched': len(candidates), 'source_spans_reverified': len(hits),
              'by_archive': dict(by_archive), 'already_bound_source_strings': sum(r['already_bound_in_spirit_table'] for r in hits),
              'remaining_classification_candidates': sum(not r['already_bound_in_spirit_table'] for r in hits),
              'runtime_verified': False, 'occurrences': hits}
    print(json.dumps({k: v for k, v in report.items() if k != 'occurrences'}, ensure_ascii=True, indent=2))
    path = settings['work'] / 'ui/spirit_related_candidates.json'
    print('%s: related candidates -> %s' % ('APPLY' if apply else 'DRY RUN', path))
    for row in hits[:8]:
        print('  %s: %s' % (row['occurrence_id'], row['jp'][:70].encode('unicode_escape').decode('ascii')))
    if apply:
        if path.exists():
            raise ValueError('related-candidate output exists; preserve it before regenerating')
        write_json(path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'check', 'export', 'related'))
    parser.add_argument('--config', default=str(ROOT / 'config/tengoku.json'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    settings = config(args.config)
    if args.command == 'related':
        related(settings, args.apply)
        return
    if args.command == 'inspect':
        report = read_source(settings)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return
    report = load_and_validate(settings)
    summary = {k: v for k, v in report.items() if k != 'entries'}
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    if args.command == 'export':
        directory = settings['work'] / 'ui/spirit_commands'
        print('%s: reviewed text and audit -> %s' % ('APPLY' if args.apply else 'DRY RUN', directory))
        for entry in report['entries'][:6]:
            print('  %s: %s' % (entry['occurrence_id'], entry['rendered_en'].replace('\n', ' / ')))
        if args.apply:
            if directory.exists():
                raise ValueError('export destination exists; preserve it before regenerating')
            directory.mkdir(parents=True)
            write_json(directory / 'validated_text.json', report)
            rows = ['# Spirit command text review', '', 'Source translations only; font, fit and runtime unverified.', '',
                    '| Record | Name | Status abbreviation | Effect |', '| --- | --- | --- | --- |']
            grouped = {}
            for entry in report['entries']:
                index = entry['occurrence_id'].split(':')[3]
                grouped.setdefault(index, {})[entry['role']] = entry['rendered_en']
            for index, fields in grouped.items():
                rows.append('| %s | %s | %s | %s |' % (index, fields['name'], fields['abbreviation'],
                            fields['description'].replace('\n', '<br>').replace('|', '\\|')))
            (directory / 'review.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
            print('Exported source text only; no game files written.')


if __name__ == '__main__':
    main()
