"""Synthetic translation fixtures; no game image or generated dump required."""
import copy
import unittest

from tools.common import sha256
from tools.ui_spirits import controls, numbers, resolve, validate


def fixture():
    source = {'title_id': 'BLJS10299', 'archive': '/synthetic', 'archive_sha256': 'a',
              'member_id': 0, 'member_sha256': 'm', 'chunk': 'spirit', 'chunk_offset': 100,
              'chunk_bytes': 80, 'chunk_sha256': 'c', 'record_stride': 20,
              'string_columns': {'name': 1, 'abbreviation': 2, 'description': 3}, 'records': []}
    translation = {'title_id': 'BLJS10299', 'source_member_sha256': 'm', 'entries': []}
    glossary = {'meta': {'title_id': 'BLJS10299'}, 'terms': []}
    rows = [('－－', '－', '－'), ('試験甲', '甲', '気力を１０上げます。'),
            ('試験乙', '乙', '「試験甲」「試験乙」が同時にかかります。'), ('？？？？', '？', '？')]
    english = [(None, None, None), ('$$試験甲#spirit$$', 'Ta', 'Raises Morale by 10.'),
               ('$$試験乙#spirit$$', 'Tb', 'Applies $$試験甲#spirit$$ and $$試験乙#spirit$$ all at once.'), ('????', '?', '?')]
    for index, row in enumerate(rows):
        record = {'record_index': index, 'record_sha256': 'record%d' % index, 'fields': {}}
        for column, role in enumerate(('name', 'abbreviation', 'description'), 1):
            jp = row[column - 1]
            field = {'occurrence_id': 'rpw:0:spirit:%d:%s' % (index, role), 'jp': jp,
                     'source_sha256': sha256(jp.encode('cp932')), 'pointer_offset': 100 + index * 20 + column * 4,
                     'string_body_offset': index * 100 + column * 10}
            record['fields'][role] = field
            translation['entries'].append(dict(field, record_sha256=record['record_sha256'],
                status='excluded' if index == 0 else 'reviewed', reason='Empty sentinel' if index == 0 else None,
                en=english[index][column - 1]))
        source['records'].append(record)
        if index in (1, 2):
            name = record['fields']['name']
            glossary['terms'].append({'kind': 'spirit', 'jp': name['jp'], 'token': name['jp'] + '#spirit',
                'en': 'Test',  # Intentional identical English for distinct identities.
                'status': 'proposed', 'meaning_reviewed': True,
                'target': {'archive': '/synthetic', 'member_id': 0, 'occurrence_id': name['occurrence_id'], 'source_sha256': name['source_sha256'], 'member_sha256': 'm'}})
    return source, {k: v for k, v in source.items() if k != 'records'}, translation, glossary


class SpiritValidationTests(unittest.TestCase):
    def test_complete_batch_and_explicit_sentinel(self):
        report = validate(*fixture())
        self.assertEqual((report['source_occurrences'], report['translated_occurrences']), (12, 9))
        self.assertFalse(report['binary_ready'])

    def test_missing_and_duplicate_assignments_fail(self):
        for mutation in ('missing', 'duplicate'):
            source, schema, translation, glossary = fixture()
            if mutation == 'missing':
                translation['entries'].pop()
            else:
                translation['entries'].append(copy.deepcopy(translation['entries'][-1]))
            with self.assertRaisesRegex(ValueError, 'coverage|duplicate'):
                validate(source, schema, translation, glossary)

    def test_pointer_and_source_fingerprint_drift_fail(self):
        for key in ('pointer_offset', 'source_sha256', 'record_sha256'):
            source, schema, translation, glossary = fixture()
            translation['entries'][3][key] = 'changed'
            with self.assertRaises(ValueError):
                validate(source, schema, translation, glossary)

    def test_same_english_wrong_identity_still_fails(self):
        source, schema, translation, glossary = fixture()
        translation['entries'][8]['en'] = 'Applies $$試験乙#spirit$$ and $$試験甲#spirit$$ all at once.'
        with self.assertRaisesRegex(ValueError, 'identities/order'):
            validate(source, schema, translation, glossary)

    def test_glossary_cannot_bind_to_another_record(self):
        source, schema, translation, glossary = fixture()
        glossary['terms'][0]['target']['occurrence_id'] = 'rpw:0:spirit:2:name'
        with self.assertRaisesRegex(ValueError, 'identity'):
            validate(source, schema, translation, glossary)

    def test_effect_number_change_fails(self):
        source, schema, translation, glossary = fixture()
        translation['entries'][5]['en'] = 'Raises Morale by 30.'
        with self.assertRaisesRegex(ValueError, 'numbers'):
            validate(source, schema, translation, glossary)

    def test_ambiguous_term_is_not_accepted(self):
        source, schema, translation, glossary = fixture()
        glossary['terms'][0]['status'] = 'ambiguous'
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            validate(source, schema, translation, glossary)

    def test_foreign_archive_binding_fails(self):
        source, schema, translation, glossary = fixture()
        glossary['terms'][0]['target']['archive'] = '/another-game'
        with self.assertRaisesRegex(ValueError, 'archive/member'):
            validate(source, schema, translation, glossary)

    def test_unknown_state_marker_count_is_preserved(self):
        source, schema, translation, glossary = fixture()
        translation['entries'][9]['en'] = '?'
        with self.assertRaisesRegex(ValueError, 'unknown-state'):
            validate(source, schema, translation, glossary)

    def test_unreviewed_and_extra_excluded_entries_fail(self):
        for status in ('draft', 'excluded'):
            source, schema, translation, glossary = fixture()
            translation['entries'][5]['status'] = status
            with self.assertRaises(ValueError):
                validate(source, schema, translation, glossary)

    def test_unknown_or_malformed_token_fails(self):
        glossary = fixture()[3]
        for text in ('$$missing#spirit$$', '$$broken', '$$$$'):
            with self.assertRaises(ValueError):
                resolve(text, glossary)

    def test_numeric_paraphrases_do_not_hide_changes(self):
        self.assertEqual(numbers('一度だけ２倍になります。'), numbers('Doubles damage for one attack.'))
        self.assertEqual(numbers('１ターンの間、半分にします。'), numbers('Halves damage for 1 turn.'))
        self.assertEqual(numbers('同時にかかります。'), numbers('Applies all at once.'))
        self.assertNotEqual(numbers('１／８'), numbers('1/4'))

    def test_percent_prose_and_real_placeholders_are_distinct(self):
        self.assertFalse(controls('Hit rate +30% for 1 turn.'))
        self.assertEqual(controls('$n has %d HP.'), {'$n': 1, '%d': 1})


if __name__ == '__main__':
    unittest.main()
