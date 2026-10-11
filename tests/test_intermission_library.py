import json
import struct
import unittest
from tools.common import ROOT
from tools import intermission_layout as I, library_runtime as L, ui_hook as H
from tools import ui_catalog, ui_layout_text, eff_art, chart_art, gtf
from tools.ui_description_layout import advance


class IntermissionTests(unittest.TestCase):
    def test_split_labels_are_single_captions_and_library_keeps_special_mode(self):
        source=I.battle_layout.source();plan=I.plan()
        rows={e['widget_offset']:e for e in plan['edits']}
        self.assertEqual(rows[0x9b544]['en'],'Upgrades')
        for at in (0x97c84,0x97ca4,0x97cc4,0x97ce4,0x9b864,0x9b884):
            self.assertEqual(rows[at]['en'],'')
        self.assertEqual(rows[0x97c64]['en'],'Rengoku Link')
        for at in range(0x94b04,0x94bc4,32):
            row=rows[at]
            self.assertNotIn('"',row['en'])
            self.assertNotIn('mode',row)
            self.assertEqual(source[at+23],1)
            self.assertLess(sum(map(advance,row['en']))*37/32,455)

    def test_final_widget_isolation_rejects_noncaption_changes(self):
        source=I.battle_layout.source();plan=I.plan()
        mapping=json.loads((ROOT/'work/output/builds/0.5.10/build.json').read_text(encoding='utf8'))['mapping']
        built,_=ui_layout_text.fssa_patch(source,plan['edits'],mapping)
        bad=bytearray(built);bad[0x97c64+24]^=1
        with self.assertRaises(ValueError):
            ui_layout_text.verify_fssa(source,bytes(bad),plan['edits'],mapping)


class LibraryRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=H.PREPARED.read_bytes()
        build=json.loads((ROOT/'work/output/builds/0.5.10/build.json').read_text(encoding='utf8'))
        cls.mapping=build['mapping']
        cls.plan=L.plan(cls.source,cls.mapping,advance)
        cls.elf,cls.report=L.native_patch(cls.source,cls.source,cls.mapping)

    def test_all_keyword_ids_have_both_variants_and_original_record_guard(self):
        self.assertEqual({e['id'] for e in self.plan['report']['entries']},set(range(143)))
        self.assertEqual(len(self.plan['pointers']),286)
        self.assertEqual(len(self.plan['payloads']),574)
        for row in self.plan['report']['entries']:
            values=struct.unpack_from('>6I',self.source,row['record_offset'])
            self.assertEqual(values[4:],(0xffffffff,row['id']))
        bad=bytearray(self.source);bad[0x8acf78]^=1
        with self.assertRaisesRegex(ValueError,'baseline changed'):
            L.plan(bytes(bad),self.mapping,advance)

    def test_native_converter_executes_wrapped_lines_and_rejects_occupied_cell(self):
        oracle=H.ConverterOracle(self.elf);table=H.unicode_table(self.elf)
        payloads=dict(self.plan['payloads'])
        owned=[raw for key,raw in payloads.items() if key.startswith('library:keyword:') and not key.endswith(':encoded')]
        cases=[payloads['library:keyword:0:DSCR'],max(max(owned,key=len)[:-1].split(b'\n'),key=len)+b'\0']
        for raw in cases:
            expected=H.convert(raw[:-1],table)
            self.assertLess(len(expected)+1,8192)
            for model in ('A','B'):
                out,_,_=oracle.run(raw,model)
                self.assertEqual(out[:len(expected)],expected)
                self.assertEqual(out[len(expected)],0)
        ch='A';cell=H.UTAB_VA-0x10000+0x100+ord(L.LETTERS[ch])*2
        bad=bytearray(self.source);bad[cell]^=1
        with self.assertRaisesRegex(ValueError,'cell is occupied'):
            L.native_patch(bytes(bad),self.source,self.mapping)

    def test_shipped_conversion_consumers_preserve_native_fallback_and_long_prose(self):
        from tools import vwf,ui_runtime
        executable,_=vwf.patch(self.source,{})
        hooked,report=H.hook(executable,[],require_srvc=False,payloads=self.plan['payloads'])
        addresses=report['table']['payload_vas']
        out,_=ui_runtime.apply(hooked,self.plan,addresses)
        out,_=L.native_patch(out,self.source,self.mapping)
        out,conversion=L.apply_fastpath(out,self.source,self.plan,addresses)
        result=L.verify_fastpath(out,self.plan,addresses,conversion)
        self.assertEqual(result['owned_consumer_cases'],572)
        self.assertEqual(result['fallback_cases'],3)
        bad=bytearray(hooked);bad[0x13f4c-0x10000]^=1
        with self.assertRaisesRegex(ValueError,'consumer changed'):
            L.apply_fastpath(bytes(bad),self.source,self.plan,addresses)


class ChartTests(unittest.TestCase):
    def test_native_animation_and_all_unpainted_atlas_pixels_are_preserved(self):
        import numpy as np
        sources=eff_art.source_members(eff_art._settings(),list(chart_art.SOURCES),chart_art.SOURCES)
        for mid,source in sources.items():
            built,pixels,edits,info=chart_art.render(source,mid)
            self.assertTrue(eff_art.verify_member(source,built,pixels,edits))
            self.assertEqual(info['header'],'Scenario Chart')
            for t in gtf.textures(source):
                old=gtf.decode(source,t);new=gtf.decode(built,t)
                if str(t.key) in info['rectangles']:
                    x,y,w,h=info['rectangles'][str(t.key)];new[y:y+h,x:x+w]=old[y:y+h,x:x+w]
                self.assertTrue(np.array_equal(old,new))


if __name__=='__main__':unittest.main()
