import unittest
from tools import verify_review51 as V,review51_text as T

class DLCMenuTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.proof=V.components()

 def test_complete_category_and_split_runtime_rows(self):
  r=self.proof
  self.assertEqual((r['category_entries'],r['synopses'],r['prompts'],r['menu_states'],r['rules_notices']),(74,35,29,9,1))
  self.assertEqual(r['draw_keys'],63)
  self.assertEqual((len(r['menu_state_lookups']),r['native_utf8_prompts_verified']),(9,29))
  self.assertEqual((r['native_rules_rows'],len(r['centered_rules_origins'])),(4,4))
  for row in r['draw_bounds']:
   if row['va']!=hex(T.RULES):self.assertLessEqual(row['left']+row['width'],1204)
  self.assertTrue(r['fonts_and_narration_unchanged'])

 def test_every_launch_and_claim_constructor_keeps_names_and_rewards(self):
  r=self.proof
  self.assertEqual((r['native_titles'],r['native_reward_names'],len(r['native_confirmation_cases'])),(40,60,70))
  self.assertEqual(len(r['native_pack_title_and_description_cases']),5)
  row=next(x for x in r['native_confirmation_cases']if x['index']==3 and not x['claim'])
  for expected in ('Fumoffu Awakens','Funds: 50000','Z-Chips: 100','Propellant Tank','Auxiliary ISC','Start this scenario?'):
   self.assertIn(expected,row['en'])
  self.assertTrue(all(x['bytes']<512 for x in r['native_confirmation_cases']))
  self.assertTrue(r['no_writable_executable_load'])
  self.assertTrue(r['unknown_title_and_reward_fallbacks_preserved'])

 def test_all_three_labels_keep_clear_of_content(self):
  for row in T.layout()['bounds']:self.assertLessEqual(row['right']+8,row['neighbor_left'])

if __name__=='__main__':unittest.main()
