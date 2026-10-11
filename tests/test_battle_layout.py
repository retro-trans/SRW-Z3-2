import struct
import unittest
from tools import battle_layout as bl,status_layout as sl,ui_layout_text,ui_hook,eboot_text
from tools.ui_vwf_build import raster
from tools.ui_description_layout import advance
from tools.common import ROOT


class BattleLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.cpk import CPK
        from tools.ui_build import allocate
        from tools.inventory import FONT
        from tools.pipeline import config,verified_source
        with CPK(verified_source(config(ROOT/'config/tengoku.json'),FONT))as font:
            pages=[font.read(e)for e in font.files if e['id']in(1,3)]
        cls.mapping,_=allocate(pages,set(map(chr,range(32,127)))|set(bl.TINY),lambda t:[t])
        cls.source=bl.source();cls.plan=bl.plan();cls.elf=ui_hook.PREPARED.read_bytes()

    def test_flag_cells_preserve_index_and_pitch(self):
        original={a:r for r in bl.ui_catalog.fssa_strings(self.source)for a in r['widget_offsets']}
        rows=[e for e in self.plan['edits']if original[e['widget_offset']]['text'].startswith('熱魂闘閃')]
        self.assertEqual(len(rows),5)
        for row in rows:
            raw=original[row['widget_offset']]['raw']
            english=eboot_text.encode(row['en'],self.mapping)
            self.assertEqual(len(raw),len(english))
            for jp,en in zip(raw.decode('cp932'),row['en']):
                if jp=='／':self.assertEqual(en,bl.SEPARATOR)
                else:self.assertEqual(bl.TINY[en],bl.TINY[bl.FLAGS[jp]])
            self.assertTrue(all(c in bl.TINY for c in row['en']))
            labels=[bl.TINY[c] for c in row['en']]
            if '／' in raw.decode('cp932'):
                self.assertEqual(labels[13:17],['Fy','/','Di','An'])
            else:self.assertEqual(labels[13:17],['Fy','Lu','Ga','Di'])
        for token in bl.TINY:
            ink,width=raster(token);box=ink.getbbox()
            self.assertEqual(width,32)
            self.assertGreaterEqual(box[0],2);self.assertLessEqual(box[2],30)
            self.assertLessEqual(box[3],31);self.assertGreater(box[1],0)

    def test_converter_instructions_and_isolation(self):
        out,report=bl.native_patch(self.elf,self.elf,self.mapping)
        restored=bytearray(out)
        for a,b in report['modified_file_ranges']:restored[a:b]=self.elf[a:b]
        self.assertEqual(restored,self.elf)
        oracle=ui_hook.ConverterOracle(out)
        for token in bl.TINY:
            for model in ('A','B'):
                expected=bytes.fromhex(self.mapping[token])+b'\0\0'
                self.assertEqual(oracle.run(token.encode('utf8'),model)[0][:4],expected)
        self.assertEqual(len(bl.hook_entries(self.elf,self.mapping)),3)

    def test_bound_widget_isolation_and_metrics_guard(self):
        out,_=ui_layout_text.fssa_patch(self.source,self.plan['edits'],self.mapping)
        ui_layout_text.verify_fssa(self.source,out,self.plan['edits'],self.mapping)
        grow=len(out)-len(self.source)
        original={a:r for r in bl.ui_catalog.fssa_strings(self.source)for a in r['widget_offsets']}
        for e in self.plan['edits']:
            at=e['widget_offset']
            self.assertEqual(out[at+grow+4:at+grow+16],self.source[at+4:at+16])
            self.assertEqual(out[at+grow+21:at+grow+32],self.source[at+21:at+32])
            self.assertEqual(e['en'].count('\n'),original[at]['text'].count('\n'))
        at=0x9ac64+grow+21
        broken=bytearray(out);broken[at]^=1
        with self.assertRaises(ValueError):ui_layout_text.verify_fssa(self.source,bytes(broken),self.plan['edits'],self.mapping)
        edit=dict(self.plan['edits'][-1],font_metrics=[18,18,16,0,18])
        with self.assertRaises(ValueError):ui_layout_text.fssa_patch(self.source,[edit],self.mapping)

    def test_native_label_budgets_and_result_suffix(self):
        # Native slots from the action buttons, separate colon/value widgets,
        # and the user screenshots. Values and icon coordinates stay fixed.
        budgets={0xa0444:(37,94),0xa0584:(37,94),0xa05a4:(37,94),0xa05c4:(37,94),0xa05e4:(37,94),
            0xa0644:(37,94),0xa01c4:(31,220),0xa0244:(31,220),0xa0284:(31,220),
            0xa0344:(31,220),0xa0204:(31,220),0xa70e4:(23,57),0x8c2e4:(23,96),0x8c944:(21,96),
            0x9a4a4:(23,88),0x9a4e4:(23,74),0x9ac64:(22,36),0xa6464:(18,50),0xa6484:(18,50),
            0xa64c4:(18,50),0xa64e4:(18,50)}
        for e in self.plan['edits']:
            at=e['widget_offset']
            if at in budgets:
                quad,budget=budgets[at]
                for line in e['en'].split('\n'):self.assertLess(sum(map(advance,line))*quad/32,budget,(hex(at),line))
        row=next(e for e in self.plan['edits']if e['widget_offset']==0xa6fe4)
        self.assertEqual(row['en'],'')
        out,_=ui_layout_text.fssa_patch(self.source,self.plan['edits'],self.mapping)
        # Numeric styles/elements and the full original text pool survive.
        a,b=struct.unpack_from('>II',self.source,0x4c);grow=len(out)-len(self.source)
        self.assertEqual(out[a+grow:b+grow],self.source[a:b])

if __name__=='__main__':unittest.main()
