import itertools
import struct
import unittest
from tools import status_layout as sl,ui_hook,link_layout as ll,ppc_exec as p,vwf,eboot_text,ui_layout_text
from tools.ui_vwf_build import raster
from tools.ui_description_layout import advance
from tools.common import ROOT


class StatusLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.cpk import CPK
        from tools.ui_build import allocate
        from tools.inventory import FONT
        from tools.pipeline import config,verified_source
        from tools.ui_coverage import member
        from tools.aid_art import ARCHIVE
        settings=config(ROOT/'config/tengoku.json')
        font=CPK(verified_source(settings,FONT))
        pages=[font.read(e)for e in font.files if e['id']in(1,3)]
        cls.mapping,_=allocate(pages,set(map(chr,range(32,127)))|set(sl.TINY)|set(sl.MARKERS.values()),lambda t:[t])
        cls.elf=ui_hook.PREPARED.read_bytes()
        cls.source=member(verified_source(settings,ARCHIVE));cls.plan=sl.plan()

    def test_cell_ink_and_native_pitch(self):
        for token,word in sl.TINY.items():
            ink,width=raster(token);box=ink.getbbox()
            self.assertEqual(width,32);self.assertIsNotNone(box)
            self.assertGreaterEqual(box[0],1);self.assertLessEqual(box[2],31)
            self.assertGreater(box[1],0);self.assertLess(box[3],32)
        for marker in sl.MARKERS.values():
            ink,width=raster(marker);self.assertIsNone(ink.getbbox());self.assertEqual(width,32)

    def test_terrain_converter_and_all_movement_combinations(self):
        out,report=sl.native_patch(self.elf,self.elf,self.mapping)
        restored=bytearray(out)
        for a,b in report['modified_file_ranges']:restored[a:b]=self.elf[a:b]
        self.assertEqual(restored,self.elf)
        table=ui_hook.unicode_table(out)
        oracle=ui_hook.ConverterOracle(out)
        for va in sl.MOVEMENT:
            cells=[out[va-0x10000+i*8:va-0x10000+i*8+3].decode('utf8') for i in range(4)]
            for flags in itertools.product((False,True),repeat=4):
                text=''.join(c if present else '－' for c,present in zip(cells,flags))
                expected=b''.join(bytes.fromhex(self.mapping[c])if c in sl.TINY else c.encode('cp932')for c in text)
                self.assertEqual(ui_hook.convert(text.encode('utf8'),table),expected)
                for model in ('A','B'):
                    self.assertEqual(oracle.run(text.encode('utf8'),model)[0][:len(expected)+2],expected+b'\0\0')
        for va,jp,en in sl.SPECIAL:
            raw=out[va-0x10000:out.index(0,va-0x10000)]
            self.assertEqual(ui_hook.convert(raw,table),eboot_text.encode(en,self.mapping))
        broken=bytearray(self.elf);broken[sl.MOVEMENT[0]-0x10000]^=1
        with self.assertRaises(ValueError):sl.native_patch(broken,self.elf,self.mapping)

    def test_widget_isolation_and_column_budgets(self):
        out,_=ui_layout_text.fssa_patch(self.source,self.plan['edits'],self.mapping)
        ui_layout_text.verify_fssa(self.source,out,self.plan['edits'],self.mapping)
        grow=len(out)-len(self.source)
        for edit in self.plan['edits']:
            at=edit['widget_offset']
            expected=bytearray(self.source[at+8:at+32])
            if 'font_metrics' in edit:
                self.assertIn(at,(0x99f04,0x99f24))
                self.assertEqual(edit['font_metrics'],[27,28,26,28,28])
                expected[8:13]=bytes(edit['font_metrics'])
            self.assertEqual(out[at+grow+8:at+grow+32],expected)
        # Measured native label slots, independent from the changed text.
        budgets={0x9d5c4:60,0x9d704:72,0x9d624:100,0x9de24:100,
            0x9d884:108,0x9d8a4:107,0x9db64:105,0x9d9a4:80,0x9d9c4:86,
            0x9d9e4:107,0x9da04:90,0x9da24:68,0x9da84:198,0x9daa4:155,
            0x9dac4:78,0x9dae4:79,0x9db04:114,0x9db24:89,0x9db44:103}
        for edit in self.plan['edits']:
            at=edit['widget_offset']
            if at in budgets:
                quad=self.source[at+19]
                for line in edit['en'].split('\n'):
                    self.assertLess(sum(map(advance,line))*quad/32,budgets[at],(hex(at),line))

    def test_save_origin_execution_and_native_fallback(self):
        specs=sl.save_specs(self.mapping)
        for n,text in enumerate([en for jp,en in sl.CAPTIONS]+['native','']):
            for quad in (25,28,31,36):
                mem=p.Memory();mem.map(0x400000,bytes(0x3000));mem.map(0x310000,bytes(0x2000))
                if n<len(sl.CAPTIONS):
                    raw=bytes.fromhex(self.mapping[sl.MARKERS[sl.CAPTIONS[n][0]]])+eboot_text.encode(text,self.mapping)
                    left=639.5-len(sl.CAPTIONS[n][0])*quad/2
                else:raw='未知'.encode('cp932')if text else b'';left=215.25
                mem.map(0x340000,raw+b'\0\0',writable=False)
                mem.map(0x330000,sl.save_origin(0x330000,0x310000,specs),writable=False)
                m=p.Machine(mem);m.r=[0x990000+i for i in range(32)];m.r[1]=0x401800
                m.r[30]=0x311000;m.r[31]=0x340000;m.f=[i+.25 for i in range(32)]
                m.f[31]=left;m.cr=0xb3c7a965;m.lr=0xdead00
                mem.write(0x311054,struct.pack('>f',quad));before=(m.r[:],m.f[:],m.cr,m.lr)
                m.pc=0x330000;m.run({0x141ac},limit=10000)
                for r in set(range(32))-{31}:self.assertEqual(m.r[r],before[0][r])
                for f in set(range(32))-{31}:self.assertEqual(m.f[f],before[1][f])
                self.assertEqual((m.cr,m.lr),before[2:])
                if n<len(sl.CAPTIONS):
                    self.assertEqual(m.r[31],0x340002)
                    self.assertAlmostEqual(m.f[31]+sum(map(advance,text))*quad/64,639.5,places=4)
                else:self.assertEqual(m.r[31],0x340000);self.assertEqual(m.f[31],left)
                self.assertEqual(mem.read(0x310400,4),struct.pack('>f',m.f[31]))
                self.assertEqual(mem.read(0x31104c,4),struct.pack('>f',m.f[31]))

    def test_yes_no_selection_anchors_share_center(self):
        edits={e['widget_offset']:e for e in self.plan['edits']}
        pos=lambda at:edits[at]['x']*640+640
        width=lambda s:sum(map(advance,s))*25/32
        left=pos(0x993a4)
        self.assertAlmostEqual(left+width('Yes / No')/2,639.5)
        self.assertAlmostEqual(pos(0x99384)-25,left)
        self.assertAlmostEqual(pos(0x993c4)-37.5,left+width('Yes / '))
        self.assertAlmostEqual(pos(0x99404),left)
        self.assertAlmostEqual(pos(0x99444),left+width('Yes / '))

    def test_constructed_names_and_split_questions(self):
        entries=sl.hook_entries(self.elf,self.mapping)
        self.assertEqual(len({e['id']for e in entries}),len(entries))
        blob,report=ui_hook.build_table(entries)
        by_key={e['key']:e['english']for e in entries}
        for before,after in (('SaotomeAlto','Saotome Alto'),('Alto・Saotome','Alto Saotome')):
            self.assertEqual(by_key[eboot_text.encode(before,self.mapping)],eboot_text.encode(after,self.mapping))
        for jp,en in sl.SAVE:
            key=ui_hook.utf8_key(jp.encode('utf8'),self.elf)
            self.assertEqual(by_key[key][2:],eboot_text.encode(en,self.mapping))


if __name__=='__main__':unittest.main()
