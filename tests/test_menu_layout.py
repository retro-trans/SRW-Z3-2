import json
import struct
import unittest
from tools import menu_layout as layout, ui_layout_text, ui_catalog, eboot_text
from tools.common import ROOT
from tools.ui_description_layout import advance
from tools.ui_coverage import member
from tools.pipeline import config, verified_source
from tools.aid_art import ARCHIVE


class MenuLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))
        cls.plan=layout.plan()
        from tests.test_ui_hook import fw
        cls.mapping={chr(c):fw(chr(c)).hex()for c in range(32,127)}
        cls.mapping.update(dict(zip(layout.PADS,('87e0','87e1','87e2'))))

    def test_line_centers_preserve_buttons_and_blank_rows(self):
        inverse={bytes.fromhex(code):token for token,code in self.mapping.items()}
        for edit in self.plan['edits']:
            if 'line_center' not in edit: continue
            raw=layout.encode(edit,self.mapping).split(b'\n')
            self.assertEqual(len(raw),len(edit['en'].split('\n')))
            for word,data in zip(edit['en'].split('\n'),raw):
                if not word: self.assertEqual(data,b''); continue
                text=eboot_text.encode(word,self.mapping)
                self.assertTrue(data.endswith(text))
                pad=data[:-len(text)]
                pad_units=sum(layout.PADS[t] if t in layout.PADS else advance(t)
                    for t in (inverse[pad[i:i+2]]for i in range(0,len(pad),2)))
                left=1030+pad_units*31/32
                width=sum(map(advance,word))*31/32
                self.assertLessEqual(abs(left+width/2-1140),31/64)
                self.assertGreater(left,1030)
                self.assertLess(left+width,1250)

    def test_font_padding_is_invisible_and_precise(self):
        from tools.ui_vwf_build import raster
        for token,width in layout.PADS.items():
            glyph,actual=raster(token)
            self.assertIsNone(glyph.getbbox()); self.assertEqual(actual,width)

    def test_widget_patch_isolated_and_live_counter_fits(self):
        elements=self.plan['element_edits']
        out,_=ui_layout_text.fssa_patch(self.source,self.plan['edits'],self.mapping,elements)
        ui_layout_text.verify_fssa(self.source,out,self.plan['edits'],self.mapping,elements)
        grow=len(out)-len(self.source)
        for edit in self.plan['edits']:
            at=edit['widget_offset']
            self.assertEqual(out[at+grow+8:at+grow+32],self.source[at+8:at+32])
        counter=next(e for e in self.plan['edits'] if e['widget_offset']==0x98544)
        suffix_x=counter['x']*640+640
        numeric=elements[0];at=numeric['element_offset']
        number_right=numeric['x']*640+640-.5
        self.assertEqual(out[at+grow+4:at+grow+12],self.source[at+4:at+12])
        self.assertEqual(struct.unpack_from('>HBB',out,at+grow+8),(45,15,0))
        self.assertAlmostEqual(suffix_x-number_right,1,places=4)
        # Numeric style 45 is right aligned, has a 17-unit digit advance
        # and 28-pixel height. Check the reported zero and three-digit totals.
        style_start=struct.unpack_from('>I',self.source,0x4c)[0]
        style=self.source[style_start+45*20:style_start+46*20]
        self.assertEqual(style[12:16],bytes.fromhex('111c0160'))
        for count in ('0','99','999'):
            self.assertGreater(number_right-len(count)*17,370)
            self.assertLess(suffix_x+sum(map(advance,'Teams'))*28/32,598)
        bad_elements=[dict(numeric,source_element_sha256='0'*64)]
        with self.assertRaises(ValueError):
            ui_layout_text.fssa_patch(self.source,self.plan['edits'],self.mapping,bad_elements)
        broken=[dict(e)for e in self.plan['edits']]; broken[0]['source_widget_sha256']='0'*64
        with self.assertRaises(ValueError): ui_layout_text.fssa_patch(self.source,broken,self.mapping)


if __name__=='__main__': unittest.main()
