import unittest,re
import numpy as np
from tools import review34_startup as S,gtf

class Review34(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=S.source();cls.data=S.checked();cls.built,cls.pixels,cls.report=S.render(cls.source,cls.data)

    def test_complete_startup_family_and_notice_words(self):
        self.assertEqual(len(gtf.textures(self.built)),5)
        self.assertEqual(sum(not r['keep_source_pixels']for rows in self.data['copyright_pages'].values()for r in rows),20)
        self.assertEqual(self.report['translated_screens'],[0,3,4])
        actual=' '.join(self.report['details'][0]['lines']).split()
        self.assertEqual(actual,' '.join(self.data['warning']['paragraphs']).split())
        self.assertIn('knowingly downloading',self.data['warning']['paragraphs'][0])
        self.assertIn("rights holder's permission",self.data['warning']['paragraphs'][0])

    def test_logo_pixels_headers_existing_english_and_alpha_are_unchanged(self):
        old,new=gtf.textures(self.source),gtf.textures(self.built)
        self.assertEqual([dict(t)for t in old],[dict(t)for t in new])
        for n in (1,2):self.assertTrue(np.array_equal(gtf.decode(self.source,old[n]),gtf.decode(self.built,new[n])))
        for n,row in self.data['preserved_english_credit_rows']:
            y=(100 if n==3 else 76)+48*row
            self.assertTrue(np.array_equal(gtf.decode(self.source,old[n])[y:y+40],gtf.decode(self.built,new[n])[y:y+40]))
        for n in (0,3,4):self.assertTrue(np.array_equal(gtf.decode(self.source,old[n])[:,:,3],gtf.decode(self.built,new[n])[:,:,3]))

    def test_copyright_years_and_every_row_fit_the_screen(self):
        years=[re.findall(r'\b(?:19|20)\d{2}\b',r['en'])for r in self.report['details'][1:]]
        self.assertEqual([y for ys in years for y in ys],['1983','1994','1997','2009','2011','1998','1998','2009','2003','2004'])
        for r in self.report['details'][1:]:
            l,t,right,b=r['bounds'];self.assertGreaterEqual(l,105);self.assertLessEqual(right,1176)
            self.assertLessEqual(b-t,32);self.assertGreaterEqual(r['horizontal_scale'],0.78)

    def test_unrecognized_source_is_rejected(self):
        altered=bytearray(self.source);altered[-1]^=1
        with self.assertRaisesRegex(ValueError,'source member changed'):S.render(bytes(altered),self.data)

if __name__=='__main__':unittest.main()
