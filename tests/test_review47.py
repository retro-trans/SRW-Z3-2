"""Exercise real purchase assembly and both generic choice states."""
import copy,json,struct,unittest
from tools import review47_messages as M,review47_text as T,ui_hook as H,eboot_text as E
from tools.common import ROOT

class Review47(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=H.PREPARED.read_bytes()
  cls.mapping=json.loads((ROOT/'work/output/builds/0.5.46/build.json').read_text('utf8'))['mapping']

 def test_all_native_purchase_names_and_relocated_english(self):
  rows=M.source_rows(self.original);self.assertEqual(len(rows),78)
  expected={r['key']:r['english']for r in M.hook_entries(self.original,self.mapping)}
  for row in rows:
   for name in (row['jp'].encode('cp932'),E.encode(row['en'],self.mapping)):
    lines,steps=M.native_compose(self.original,name)
    self.assertEqual(expected[lines[0]],E.encode(row['question'],self.mapping))
    self.assertEqual(lines[1],'よろしいですか？'.encode('cp932'))
    self.assertGreater(steps,100)

 def test_purchase_source_drift_is_rejected(self):
  bad=bytearray(self.original);bad[M.SUFFIX-0x10000]^=1
  with self.assertRaisesRegex(ValueError,'fragment'):M.source_rows(bytes(bad))

 def test_selected_words_share_grey_prefix_origins(self):
  p=T.plan();rows={r['widget_offset']:r for r in p['bounds']}
  self.assertEqual(len(rows),12)
  for grey,selected in ((0x8bd24,0x8bd44),(0x98f84,0x98fa4),(0x99364,0x99384),
                        (0x993a4,0x993c4),(0x993e4,0x99404),(0x99424,0x99444)):
   a,b=rows[grey],rows[selected]
   if b['en']=='Yes':self.assertEqual(a['left'],b['left'])
   else:self.assertEqual(a['right'],b['right'])
  self.assertTrue(all(e['mode']==0 for e in p['edits']))

 def test_active_names_are_canonical_including_typo_alias(self):
  terms=json.loads((ROOT/'work/glossary/library_terms.json').read_text('utf8'))['terms']
  want={'レーベン':'Lowen','レーベン・ゲネラール':'Lowen General','レーベル・ゲネラール':'Lowen General',
        'シュラン':'Schlan','シュラン・オペル':'Schlan Opel'}
  actual={t['token']:t['en']for t in terms if t.get('token')in want}
  self.assertEqual(actual,want)
if __name__=='__main__':unittest.main()
