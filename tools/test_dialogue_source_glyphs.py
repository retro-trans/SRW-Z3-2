"""Regression checks for source-only decorative glyph preservation."""
import contextlib,io,json,tempfile,unittest
from pathlib import Path
from tools import dialogue as d,dialogue_build as build

class SourceGlyphTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sources={r['id']:r for r in d.plan_rows() if r['id'] in ('508:t_10:21','508:t_10:22')}
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.original=d.TRANSLATIONS,d.plan_rows
  d.TRANSLATIONS=Path(self.temp.name);d.plan_rows=lambda:list(self.sources.values())
 def tearDown(self):
  d.TRANSLATIONS,d.plan_rows=self.original;self.temp.cleanup()
 def check(self,rid,en):
  (d.TRANSLATIONS/'test.json').write_text(json.dumps({'rows':{rid:{'sha':self.sources[rid]['sha'],'en':en}}}),encoding='utf-8')
  with contextlib.redirect_stdout(io.StringIO()) as out:valid=d.check()
  return valid,out.getvalue()
 def test_preserves_original(self):
  self.assertTrue(self.check('508:t_10:21','$$\uff21\uff27$$\n\u300c$$\u30cf\u30de\u30fc\u30f3$$\u0431\u300d')[0])
 def test_rejects_missing_or_duplicate(self):
  for glyphs in ('','\u0431\u0431'):
   valid,log=self.check('508:t_10:21','$$\uff21\uff27$$\n\u300c$$\u30cf\u30de\u30fc\u30f3$$'+glyphs+'\u300d')
   self.assertFalse(valid);self.assertIn('source glyph U+0431 count differs',log)
 def test_rejects_introduced_glyph(self):
  self.assertFalse(self.check('508:t_10:22','$$\u30cf\u30de\u30fc\u30f3$$\n\u300cYou are too familiar.\u0431\u300d')[0])
 def test_other_unicode_still_rejected(self):
  valid,log=self.check('508:t_10:21','$$\uff21\uff27$$\n\u300c$$\u30cf\u30de\u30fc\u30f3$$\u0431\u2665\u300d')
  self.assertFalse(valid);self.assertIn('non-ASCII',log)
 def test_encoder_preserves_original_cp932(self):
  self.assertEqual(build.encode('\u0431',{}),'\u0431'.encode('cp932'))

if __name__=='__main__':unittest.main()
