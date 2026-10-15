import json
import unittest
import numpy as np
from tools.common import ROOT
from tools import review38_fonts as S, review38_build as B, ui_build as F, ui_vwf_build as W


class SeparateFontTests(unittest.TestCase):
    def test_all_allocated_fills_and_advances_are_preserved(self):
        prior=json.loads((B.BASE/'build.json').read_text('utf8'))
        for mid in (1,3):
            raw=(B.BASE/('font_%d.bin'%mid)).read_bytes()
            drawn={t:W.raster(t) for t in prior['mapping']}
            self.assertEqual({t:w for t,(_,w) in drawn.items()},prior['widths'])
            final=F.patch_font(raw,prior['mapping'],{t:g for t,(g,_) in drawn.items()})
            report=B.font_check(raw,final,prior['mapping'])
            self.assertEqual(report['native_label_cells'],41)
            self.assertEqual(report['plain_cells'],260)

    def test_only_bound_unit_list_headers_choose_the_native_alphabet(self):
        data=S.plan()
        self.assertEqual(data,json.loads(S.DEST.read_text('utf8')))
        self.assertEqual(len(data['edits']),19)
        at=data['edits'][0]['widget_offset']
        original=[dict(widget_offset=at,en='Team',x=0.25,mode=63),
                  dict(widget_offset=123,en='Team dialogue')]
        merged={e['widget_offset']:e for e in S.merge(original,data['edits'])}
        self.assertEqual(merged[at]['x'],0.25)
        self.assertEqual(merged[at]['mode'],63)
        self.assertNotIn('font_style',merged[123])
        self.assertEqual(merged[at]['font_style'],'native-label')

    def test_original_label_texels_are_copied_without_synthesized_stroke(self):
        from tools import native_labels as N
        page=N.page()
        for char in 'TeamMechKillsPPNextLv':
            image,_=N.raster(char);actual=F.glyph_pixels(image)
            x,y=F.cell_xy(chr(ord(char)+0xfee0).encode('cp932').hex())
            original=page[y:y+32,x:x+32]
            used=np.flatnonzero(original.any(axis=0));copied=np.flatnonzero(actual.any(axis=0))
            self.assertTrue(np.array_equal(original[:,used[0]:used[-1]+1],actual[:,copied[0]:copied[-1]+1]))


if __name__=='__main__':unittest.main()
