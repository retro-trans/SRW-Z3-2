import unittest
from tools import review48_content as C,review48_text as R,eboot_text as E,ui_hook as H
from tools.common import ROOT
import json

class Review48(unittest.TestCase):
 def test_native_name_separator(self):
  mapping=json.loads((ROOT/'work/output/builds/0.5.47/build.json').read_text('utf8'))['mapping']
  entries={r['key']:r['english']for r in C.name_entries(mapping)}
  key=E.encode('Asakim',mapping)+bytes.fromhex('8145')+E.encode('Dowin',mapping)
  self.assertEqual(entries[key],E.encode('Asakim Dowin',mapping))
  self.assertNotEqual(key,E.encode('Asakim・Dowin',mapping))
  self.assertNotIn(bytes.fromhex('8145'),entries)
  self.assertEqual(len(entries),810)

 def test_all_native_final_variants(self):
  elf=H.PREPARED.read_bytes()
  for index in range(306,310):
   for kind,codec in ((0,'utf8'),(1,'cp932')):
    prefix,steps=C.native_prefix(elf,index,kind)
    self.assertEqual(prefix.decode(codec),'最終話')
    self.assertGreater(steps,20)
  rows=[r for r in C.stage_rows()if r.get('prefix')=='最終話']
  self.assertEqual(len(rows),4)
  self.assertTrue(all(r['caption']=='Final Episode: World Without End'for r in rows))

 def test_complete_catalog(self):
  report=C.report()
  self.assertEqual((report['stage_records'],report['display_records'],report['title_count']),(193,163,129))
  self.assertEqual(report['catalog']['catalog_unique_titles'],342)
  self.assertEqual(report['catalog']['untranslated'],0)
  self.assertEqual(report['catalog']['translated_texture_cards'],128)

 def test_warning_highlight_is_same_word(self):
  from tools.ui_description_layout import advance
  data=R.plan();bounds=data['bounds'];edits=data['edits']
  self.assertEqual(R.SENTENCE[len(R.PREFIX):len(R.PREFIX)+len(R.WORD)],R.WORD)
  self.assertAlmostEqual(bounds['word_left'],bounds['left']+sum(map(advance,R.PREFIX))*28/32)
  self.assertTrue(all(not r['mode']&0x40 for r in edits))
  self.assertLess(bounds['right']-bounds['left'],bounds['available'])

if __name__=='__main__':unittest.main()
