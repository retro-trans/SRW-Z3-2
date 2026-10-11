import json,struct,unittest
from tools.common import ROOT
from tools import review24_layout as L,review24_report as R,ui_hook as H,ui_runtime as U
from tools import eboot_text as E,vwf,ppc_exec as P

class Review24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=H.PREPARED.read_bytes()
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.23/build.json').read_text(encoding='utf8'))['mapping']
        cls.planned=R.plan(cls.original,cls.mapping)
        elf,_=vwf.patch(cls.original,{})
        elf,hook=H.hook(elf,[],require_srvc=False,execute=0,payloads=cls.planned['payloads'])
        cls.elf,_=R.apply(elf,cls.original,cls.planned,hook['table']['payload_vas'])

    def test_resource_rows_keep_zero_and_large_values_and_canaries(self):
        for kind,prefix in [('chips','Z Chips: '),('funds','Funds: ')]:
            for value in (0,5,220,999999,2147483647):
                row,_=R.resource(self.elf,kind,value)
                number=str(value).translate(str.maketrans('0123456789','０１２３４５６７８９')).encode('cp932')
                self.assertEqual(row,E.encode(prefix,self.mapping)+number)

    def test_source_changes_are_rejected(self):
        for va in (0x185ba8,0x1858f0,0x15d108,0x9f1360):
            bad=bytearray(self.original);bad[va-0x10000]^=1
            with self.assertRaises(ValueError):R.plan(bytes(bad),self.mapping)

    def test_caption_bounds_pitch_and_live_fields(self):
        from tools import battle_layout as B,ui_layout_text as F,native_labels as N
        source=B.source();plan=L.plan();mapping=dict(self.mapping)
        for e in plan['edits']:
            if e.get('font_style')=='native-label':
                for c in e['en'].replace('\n',''):mapping.setdefault(N.PREFIX+c,mapping[c])
        out,_=F.fssa_patch(source,plan['edits'],mapping);grow=len(out)-len(source)
        for b in plan['bounds']:self.assertGreaterEqual(b['gap'],6)
        for at in (0xa3ee4,0xa3f04,0xa3f44,0xa27a4,0x9a644):
            self.assertEqual(source[at:at+32],out[at+grow:at+grow+32])
        for e in plan['edits']:
            at=e['widget_offset'];self.assertEqual(source[at+8:at+32],out[at+grow+8:at+grow+32])

    def test_signed_high_word_multiply(self):
        instruction=31<<26|3<<21|4<<16|5<<11|75<<1
        for a,b,expected in ((5,0x66666667,2),(0x7fffffff,0x66666667,858993459),
                             (0xffffffff,2,0xffffffffffffffff),(0x80000000,0x80000000,0x40000000)):
            mem=P.Memory();mem.map(0x10000,struct.pack('>I',instruction),writable=False)
            m=P.Machine(mem);m.pc=0x10000;m.r[4]=a;m.r[5]=b;m.step();self.assertEqual(m.r[3],expected)

if __name__=='__main__':unittest.main()
