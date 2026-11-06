import unittest
from tools import verify_review50 as V,narration_alignment as N

class TimedNarrationAlignment(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=V.components()

 def test_reported_dlc_page_has_true_measured_centers(self):
  cases=[r for r in self.report['native_caption_origins']if r['id'].startswith('aid:30:')and r['quad']==40]
  self.assertEqual(len(cases),5)
  for row in cases:self.assertEqual(row['center'],640);self.assertGreaterEqual(row['left'],60)
  self.assertAlmostEqual(cases[0]['left'],99.375)
  self.assertGreater(cases[-1]['left'],cases[0]['left'])

 def test_all_narration_and_original_timing_are_covered(self):
  r=self.report;self.assertEqual((r['source_rows'],r['unique_caption_keys'],len(r['native_caption_origins'])),(197,189,394))
  self.assertTrue(r['narration_source_text_and_timing_unchanged']);self.assertTrue(r['font_codes_artwork_and_advances_unchanged'])
  self.assertTrue(any(row['condensed']for row in r['installed_lookups']))
  self.assertTrue(any(not row['condensed']for row in r['installed_lookups']))

 def test_unrelated_drawer_and_dictionary_are_preserved(self):
  self.assertTrue(self.report['renderer_code_unchanged']);self.assertEqual(self.report['unrelated_lookup_payloads_and_pointers_preserved'],20251)
  self.assertTrue(self.report['dialogue_and_dlc_unchanged'])

if __name__=='__main__':unittest.main()
