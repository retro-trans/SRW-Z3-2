import unittest
import numpy as np
from PIL import Image
from tools.ui_build import glyph_pixels
from tools.ui_vwf_build import raster
from tools.focus_terminology import wording


class FocusStyleTests(unittest.TestCase):
    def test_native_two_channel_masks_keep_fill_and_outline_distinct(self):
        for c in 'FocLvSP':
            fill,advance=raster(c);pixels=glyph_pixels(fill)
            self.assertTrue(np.array_equal(pixels&255,np.asarray(fill)))
            self.assertTrue(np.all((pixels>>8)>=(pixels&255)))
            self.assertTrue(np.any(((pixels>>8)>0)&((pixels&255)==0)))
            self.assertEqual(raster(c)[1],advance)
        self.assertFalse(glyph_pixels(Image.new('L',(32,32))).any())

    def test_stat_replacement_preserves_non_stat_will_and_spirit_focus(self):
        self.assertEqual(wording('気力','Morale'),'Foc')
        self.assertEqual(wording('気力を１０上げます。','Raises Morale by 10.'),'Raises Focus by 10.')
        self.assertEqual(wording('気力１３０で集中','At Morale 130, casts Focus.'),'At Focus 130, casts Focus.')
        self.assertEqual(wording('意志','The Great Will'),'The Great Will')
        self.assertEqual(wording('気力低下','Focus will not decrease.'),'Focus will not decrease.')
        self.assertEqual(wording('気力低下','loses 10 Morale1{01}.'),'loses 10 Focus1{01}.')

    def test_compact_label_leaves_gap_before_native_value(self):
        from tools.ui_description_layout import advance
        # Original two-cell 気力 label reserves 56px at a 28px quad.
        self.assertLess(sum(map(advance,'Foc'))*28/32+4,56)
        from tools.focus_terminology import plan
        self.assertFalse(plan(),'Active UI terminology changes remain unapplied')


if __name__=='__main__':unittest.main()
