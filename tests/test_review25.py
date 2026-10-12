import json,unittest
from functools import lru_cache
from tools.common import ROOT
from tools import review25_dialogue as R,review25_layout as A,dialogue_build as D,dialogue as Q,eboot_text as E,dialogue_layout as C,review25_names as N
from tools.ui_vwf_build import raster
from tools.ui_build import FACE
@lru_cache(None)
def width(c):return raster(c,FACE)[1]if ord(c)<128 else 32

class Review25Tests(unittest.TestCase):
    def test_caption_source_guard_and_measured_center(self):
        text="　\n　　\n　　　～ Gargantia Fleet / Fleet Commander's Room ～"
        record=dict(id='51:t_1:57',sha=R.CAPTION_SHA)
        out=R.centered(text,record,width);lines=out.split('\n');self.assertEqual(lines[:2],text.split('\n')[:2])
        body=lines[2].lstrip(' ');pad=len(lines[2])-len(body)
        self.assertLessEqual(abs(pad*width(' ')+sum(map(width,body))/2-Q.BOX_UNITS/2),width(' ')/2)
        with self.assertRaises(ValueError):R.centered(text,dict(record,sha='changed'),width)
        self.assertEqual(R.centered(text,dict(record,id='unrelated'),width),text)

    def test_normal_font_three_rows_keep_keyword_link(self):
        record=dict(id=R.MAO_ID,sha=R.MAO_SHA);self.assertFalse(C.condensed(R.MAO_ID))
        out=D.render(dict(en=R.MAO,sha=R.MAO_SHA),record,E.resolver(),width)
        lines=out.split('\n')[1:];self.assertEqual(len(lines),3)
        for line in lines:self.assertLessEqual(sum(width(c)for c in line if c not in D.LINK_MARKS),Q.BOX_UNITS)
        self.assertIn('probably a type of 《Baal》',out)

    def test_title_spacing_preserves_counter_contents_and_terrain(self):
        from tools import battle_layout as B,ui_layout_text as F
        source=B.source();plan=A.plan();mapping=json.loads((ROOT/'work/output/builds/0.5.24/build.json').read_text(encoding='utf8'))['mapping']
        out,_=F.fssa_patch(source,plan['edits'],mapping);grow=len(out)-len(source)
        for row in plan['bounds']:self.assertGreaterEqual(row['title_gap'],12)
        for e in plan['edits']:
            at=e['widget_offset'];self.assertEqual(source[at+8:at+32],out[at+grow+8:at+grow+32])
            if 'en'not in e:self.assertEqual(source[at:at+4],out[at+grow:at+grow+4])
        for at in (0xa4be4,0xa4c04,0xa4c24,0xa4c84):self.assertEqual(source[at:at+32],out[at+grow:at+grow+32])

    def test_name_correction_preserves_word_boundaries(self):
        self.assertEqual(N.corrected('Amerria / South Amerria Continent'),'Ameria / South Ameria Continent')
        self.assertEqual(N.corrected('Amerrian Ameria Yui Ikari'),'Amerrian Ameria Yui Ikari')

if __name__=='__main__':unittest.main()
