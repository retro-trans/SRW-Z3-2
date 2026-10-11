import json
import struct
import unittest

from tools.common import ROOT, sha256
from tools import ppc_exec, runtime_names, startup_layout, ui_layout_text, ui_hook, opening_narration
from tests.test_ui_expansion import fixture_fssa
from tests.test_ui_hook import fw


class NameReaderTests(unittest.TestCase):
    addresses = {'name:Hibiki':0x310000,'name:Kamishiro':0x310100,'name:K.':0x310200}

    def execute(self,reader,value,lr=0x400000,nickname=b'Custom'):
        mem = ppc_exec.Memory()
        site,_,toc,jp,en = reader
        va = 0x300000
        mem.map(va,runtime_names.stub(reader,self.addresses),writable=False)
        pointer = 0x320000 if value is not None else 0
        slot = ui_hook.TOC+toc
        # Three adjacent TOC words, with the nickname slot used by the surname.
        slots = bytearray(12)
        struct.pack_into('>I',slots,4,0x320100)
        struct.pack_into('>I',slots,slot-(ui_hook.TOC-0x3c6c),pointer)
        mem.map(ui_hook.TOC-0x3c6c,slots,writable=False)
        if value is not None:
            mem.map(pointer,value+b'\0',writable=False)
        mem.map(0x320100,nickname+b'\0',writable=False)
        for name,address in self.addresses.items():
            mem.map(address,fw(name.split(':')[1])+b'\0',writable=False)
        m = ppc_exec.Machine(mem)
        m.r = [0x123000+i for i in range(32)]
        m.r[2] = ui_hook.TOC
        before = m.r[:]
        m.cr = 0xa5e31c9f
        m.lr = lr
        m.pc = va
        m.run({lr},limit=400)
        self.assertEqual(m.cr,0xa5e31c9f)
        self.assertEqual(m.lr,lr)
        for reg in set(range(32))-{0,3,9,10,11,12}:
            self.assertEqual(m.r[reg],before[reg])
        return m.r[3],pointer

    def test_defaults_custom_prefix_suffix_empty_and_null(self):
        for reader in runtime_names.READERS:
            jp,en = reader[3:]
            default = jp.encode('cp932')
            pointer,_ = self.execute(reader,default)
            self.assertEqual(pointer,self.addresses['name:'+en])
            for custom in (b'',b'A',b'Custom',default[:-2],default+b'X',None):
                pointer,original = self.execute(reader,custom)
                self.assertEqual(pointer,original)

    def test_long_custom_full_name_keeps_bytes_and_fits_value(self):
        reader = runtime_names.READERS[2]
        default = reader[3].encode('cp932')
        for ret in runtime_names.FULL_SURNAME_RETURNS:
            for n in (0,6,20,21,24,27):
                pointer,_ = self.execute(reader,default,ret,nickname=b'A'*n)
                surname = 'Kamishiro' if n<=20 else 'K.'
                self.assertEqual(pointer,self.addresses['name:'+surname])
                self.assertLessEqual(n+2+len(fw(surname))+1,41)
        pointer,_ = self.execute(reader,default,nickname=b'A'*27)
        self.assertEqual(pointer,self.addresses['name:Kamishiro'])

    @unittest.skipUnless((ROOT/'work/tengoku/prepared/EBOOT.elf').exists(),'prepared source unavailable')
    def test_actual_patch_readback_isolation_and_guard_rejection(self):
        from tools import vwf
        source = (ROOT/'work/tengoku/prepared/EBOOT.elf').read_bytes()
        mapping = {c:fw(c).hex() for c in 'HibikiKamishiroK.'}
        plan = runtime_names.plan(source,mapping)
        executable,_ = vwf.patch(source,{})
        hooked,report = ui_hook.hook(executable,[dict(id='test',key='隊'.encode('cp932'),english=fw('Team'))],
                                  require_srvc=False,payloads=plan['payloads'])
        out,fix = runtime_names.apply(hooked,plan,report['table']['payload_vas'])
        self.assertFalse(fix['save_buffers_modified'])
        _,_,phs,_ = ui_hook._headers(out)
        read = ui_hook._reader(out,phs)
        for reader,row in zip(runtime_names.READERS,fix['readers']):
            self.assertEqual(read(row['stub_va'],row['bytes']),runtime_names.stub(reader,report['table']['payload_vas']))
        bad = bytearray(hooked)
        bad[runtime_names.CONSUMER[0]-0x10000] ^= 1
        with self.assertRaisesRegex(ValueError,'consumer changed'):
            runtime_names.apply(bytes(bad),plan,report['table']['payload_vas'])


class StartupLayoutTests(unittest.TestCase):
    def test_wrap_keeps_full_meaning_and_rejects_unbounded_text(self):
        rows = json.loads((ROOT/'work/translation/en/ui/expanded/menus.json').read_text(encoding='utf-8'))['strings']
        from tools.ui_description_layout import advance
        for rid in startup_layout.LINK_IDS:
            text = rows[rid]['en']
            wrapped = startup_layout.wrap_link(text)
            self.assertEqual(wrapped.split(),text.split())
            self.assertLessEqual(len(wrapped.splitlines()),6)
            self.assertTrue(all(sum(map(advance,line))<=1180 for line in wrapped.splitlines()))
        with self.assertRaises(ValueError):
            startup_layout.wrap_link('word '*1000)

    def test_geometry_only_keeps_original_pointer_and_unrelated_widget(self):
        source = fixture_fssa()
        edit = dict(widget_offset=0x100,source_sha256=sha256('隊'.encode('cp932')),
            source_widget_sha256=sha256(source[0x100:0x120]),x=-.25)
        out,report = ui_layout_text.fssa_patch(source,[edit],{})
        self.assertEqual(report['appended_pool_bytes'],0)
        self.assertEqual(out[0x100:0x104],source[0x100:0x104])
        self.assertEqual(out[0x104:0x108],struct.pack('>f',-.25))
        self.assertEqual(out[0x120:],source[0x120:])
        bad = bytearray(out)
        bad[0x108] ^= 1
        with self.assertRaisesRegex(ValueError,'outside appended text'):
            ui_layout_text.verify_fssa(source,bytes(bad),[edit],{})

    def test_opening_rows_fit_original_timing_slots(self):
        rows = json.loads((ROOT/'work/translation/en/ui/expanded/opening.json').read_text(encoding='utf-8'))['strings']
        self.assertEqual(len(rows),sum(map(len,opening_narration.PAGES)))
        for row in rows.values():
            self.assertEqual(opening_narration.validate(row['en']),row['en'])
        with self.assertRaisesRegex(ValueError,'single timed line'):
            opening_narration.validate('A\nB')


if __name__=='__main__':
    unittest.main()
