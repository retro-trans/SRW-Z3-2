"""Regression for text that displays correctly in dialogue but breaks in Back Log."""
import unittest
from tools import backlog_storage as B, backlog_verify as V, review37_backlog as A, ui_hook as H
from tools import library_build as L


class BacklogStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = H.PREPARED.read_bytes()
        cls.final, cls.plan = B.apply(cls.original)
        cls.data = A.corpus()

    def test_reported_entry_reproduces_a_split_font_cell_in_old_storage(self):
        raw = self.data['reported']['raw']
        self.assertEqual(len(raw), 323)
        old = V.exercise(self.original, [raw], expanded=False)
        actual = bytes.fromhex(old['final_text'])
        self.assertEqual(len(actual), 308)
        self.assertNotEqual(actual, raw)
        with self.assertRaises(UnicodeDecodeError):
            L.decode(actual, self.data['mapping'])

    def test_both_constructors_ring_shifts_links_and_resets_preserve_every_long_entry(self):
        proof = A.verify(self.final)
        self.assertEqual(proof['corpus']['dialogue_entries'], 63553)
        self.assertEqual(proof['corpus']['entries_over_old_limit'], 204)
        self.assertEqual(proof['corpus']['rows_over_old_limit'], 125)
        for ring in proof['native_ring_cases']:
            self.assertEqual(ring['ring_shifts'], 185)
            self.assertEqual(ring['reset_entries'], 20)
            self.assertTrue(ring['duplicate_suppressed'])

    def test_old_row_copy_clips_a_long_line_and_new_copy_preserves_it(self):
        raw = max((raw for _, _, raw in self.data['rows']), key=len)
        self.assertEqual(len(raw), 156)
        old = V.row_copies(self.original, [raw], expanded=False)
        new = V.row_copies(self.final, [raw])
        self.assertEqual(old['row_copies'][0]['output_bytes'], 128)
        self.assertEqual(new['row_copies'][0]['output_bytes'], 156)
        self.assertTrue(new['frame_restored'])


if __name__ == '__main__':
    unittest.main()
