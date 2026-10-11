import unittest
import numpy as np
from tools import title_screen as T, eff_art as E, gtf


class TitleScreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
        cls.built,cls.intended,_,cls.info=T.render(cls.source,'0.5.10')
        cls.tex=T.audit(cls.source)

    def test_native_animation_and_z_preserved(self):
        self.assertEqual(self.source[:E.gtf_base(self.source)],self.built[:E.gtf_base(self.source)])
        for tid in (4,5,14,15,16,17,18,19,20):
            t=self.tex[tid]
            a,b=t['offset'],t['offset']+t['size']
            self.assertEqual(self.source[a:b],self.built[a:b])
        T.verify(self.source,self.built,self.intended)

    def test_reject_unrelated_texture_changes(self):
        data=bytearray(self.built);data[self.tex[4]['offset']+20]^=1
        with self.assertRaises(ValueError):T.verify(self.source,bytes(data),self.intended)
        data=bytearray(self.built);data[8]^=1
        with self.assertRaises(ValueError):T.verify(self.source,bytes(data),self.intended)

    def test_subtitle_overlap_windows_and_unused_gaps(self):
        a=gtf.decode(self.built,self.tex[12]);old=gtf.decode(self.source,self.tex[12])
        # Repeated source windows agree where settled native character quads overlap.
        self.assertTrue(np.array_equal(a[:,166:208],a[:,216:258]))
        self.assertTrue(np.array_equal(a[:,382:432],a[:,440:490]))
        self.assertTrue(np.array_equal(a[:,208:216],old[:,208:216]))
        self.assertTrue(np.array_equal(a[:,432:440],old[:,432:440]))
        for name in T.ASSET_SHA:
            image=T.asset(name);self.assertEqual(image.getextrema()[3],(0,255))

    def test_footer_version_and_three_backgrounds(self):
        first=np.asarray(T.footer('0.5.10'));second=np.asarray(T.footer('0.5.11'))
        self.assertFalse(np.array_equal(first[:26],second[:26]))
        # Leave the downsampling filter's few halo rows around the first line.
        self.assertTrue(np.array_equal(first[32:],second[32:]))
        with self.assertRaises(ValueError):T.footer('0.5.10-beta')
        for tid in (0,6,10):
            a,b=gtf.decode(self.source,self.tex[tid]),gtf.decode(self.built,self.tex[tid])
            keep=np.ones(a.shape[:2],bool);x,y,x1,y1=T.FOOTERS[tid];keep[y:y1,x:x1]=False
            self.assertTrue(np.array_equal(a[keep],b[keep]))
            self.assertFalse(np.array_equal(a[y:y1,x:x1],b[y:y1,x:x1]))

    def test_footer_stays_visible_in_native_background_zoom(self):
        for tid,box in T.FOOTERS.items():
            rows=E.rect_records(self.source,tid,(0,0,1280,720))
            self.assertTrue(rows)
            for row in rows:
                xy=E.quad_xy(self.source,row)
                right=(xy[0]+(xy[2]-xy[0])*box[2]/1280+480)*4/3
                bottom=(xy[1]+(xy[5]-xy[1])*box[3]/720+270)*4/3
                self.assertLessEqual(right,1254)
                self.assertLessEqual(bottom,698)


if __name__=='__main__':unittest.main()
