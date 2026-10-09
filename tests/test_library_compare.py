import unittest
from tools.library_compare import compare


def record(i, name, text, **extra):
    fields = {'WORD': name, 'DSCR': text, 'DSC2': text}
    fields.update(extra)
    return {'id': i, 'text': dict(fields), 'fields': {k: v.encode('utf-8') for k, v in fields.items()}}


class LibraryCompareTests(unittest.TestCase):
    def test_statuses_ignore_entry_ids(self):
        jigoku = [record(0, 'Alpha', 'same text'), record(1, 'Beta', 'old biography ' * 10)]
        tengoku = [record(5, 'Beta', 'old biography ' * 10 + 'more.'),
                   record(6, 'Alpha', 'same text'), record(7, 'Gamma', 'unrelated')]
        rows, jigoku_only, shared = compare(tengoku, jigoku, 'WORD')
        status = {r['tengoku_id']: (r['status'], r.get('jigoku_id')) for r in rows}
        self.assertEqual(status, {5: ('minor_edit', 1), 6: ('identical', 0), 7: ('new', None)})
        self.assertEqual((jigoku_only, shared), ([], []))

    def test_same_name_variants_pair_one_to_one(self):
        jigoku = [record(0, 'ELS', 'first form text', PLTN='a'), record(1, 'ELS', 'second form text', PLTN='b')]
        tengoku = [record(0, 'ELS', 'second form text', PLTN='b'), record(1, 'ELS', 'first form text', PLTN='a'),
                   record(2, 'ELS', 'third form text', PLTN='c')]
        rows, jigoku_only, shared = compare(tengoku, jigoku, 'WORD')
        pairs = {r['tengoku_id']: (r['jigoku_id'], r['matched_by']) for r in rows}
        self.assertEqual(pairs[0], (1, 'name'))
        self.assertEqual(pairs[1], (0, 'name'))
        self.assertEqual(pairs[2][1], 'name_shared')
        self.assertEqual(len(shared), 1)

    def test_renamed_entry_pairs_by_description(self):
        text = 'A long biography that stayed exactly the same between both games.'
        rows, jigoku_only, _ = compare([record(3, 'New Name', text)], [record(9, 'Old Name', text)], 'WORD')
        self.assertEqual((rows[0]['jigoku_id'], rows[0]['matched_by'], rows[0]['name_changed']),
                         (9, 'description', True))
        self.assertEqual(jigoku_only, [])

    def test_partial_names_are_hints_not_pairs(self):
        rows, jigoku_only, _ = compare([record(0, 'Implant', 'medical term')],
                                       [record(4, 'plant', 'space colony')], 'WORD')
        self.assertEqual(rows[0]['status'], 'new')
        self.assertEqual(rows[0]['review_partial_name_jigoku_ids'], [4])
        self.assertEqual(jigoku_only, [4])


if __name__ == '__main__':
    unittest.main()
