import json,struct,unittest
from tools import ppc_exec as P,ui_hook as H,runtime_names as N,review26_messages as G,review26_weapons as W,rpw_text as R
from tools.common import ROOT

class Review26Tests(unittest.TestCase):
    def test_separator_defaults_custom_null_and_registers(self):
        for given,family in [('ヒビキ','カミシロ'),('Custom','カミシロ'),('ヒビキ','Custom'),('ヒビキX','カミシロ'),(None,'カミシロ'),('ヒビキ',None)]:
            mem=P.Memory();code=N.separator_stub({'name:separator':0x320000});mem.map(0x300000,code)
            fields=bytearray(0x40);struct.pack_into('>I',fields,0,0x310000 if given is not None else 0);struct.pack_into('>I',fields,4,0x310100 if family is not None else 0);struct.pack_into('>I',fields,0x2c,0x310200)
            mem.map(H.TOC-0x3c68,fields)
            if given is not None:mem.map(0x310000,given.encode('cp932')+b'\0')
            if family is not None:mem.map(0x310100,family.encode('cp932')+b'\0')
            m=P.Machine(mem);m.r=[0x55000+n for n in range(32)];m.r[2]=H.TOC;m.cr=0xb392cd65;m.lr=0x330000;m.pc=0x300000;before=m.r[:]
            m.run({m.lr},limit=500)
            self.assertEqual(m.r[3],0x320000 if (given,family)==('ヒビキ','カミシロ')else 0x310200)
            self.assertEqual(m.cr,0xb392cd65)
            self.assertEqual(m.lr,0x330000)
            for reg in set(range(32))-{0,3,9,12}:self.assertEqual(m.r[reg],before[reg])

    def test_all_report_literals_and_reviewed_amounts(self):
        data=G.plan();self.assertEqual(sum(len(r['occurrences'])for r in data['strings'].values()),99)
        self.assertEqual(sum(r['developer_only']for r in data['strings'].values()),2)
        for jp,row in data['strings'].items():
            if 'ＡＧから' in jp:
                number=''.join(str(ord(c)-0xff10)for c in __import__('re').search(r'([０-９]+)Ｚ',jp)[1])
                self.assertIn(number+' Z-Chips.',row['en'])
            self.assertFalse(R.unusual(row['en']))
        with self.assertRaises(ValueError):G.english('Unknown report')

    def test_complete_weapon_comparison_and_pixel_bound(self):
        data,names=W.plan();self.assertEqual(data['full_names'],686);self.assertEqual(data['short_names'],606);self.assertEqual(data['shared_full'],440)
        self.assertEqual(len(data['full_name_exceptions']),8)
        self.assertEqual(names['strings']['weapon_short']['輻射波動機構']['en'],'Radiant Wave Surger')
        slots=R.slots(R.load_rpw());caps=R.caps(slots)
        for s in slots:
            if s['family']=='weapon_short' and R.needs_text(s['jp']):self.assertLessEqual(W.width(R.text_for(s,names,caps[('weapon',3)])),440)

    def test_level_family_keys_keep_levels_and_source_guard(self):
        m=json.loads((ROOT/'work/output/builds/0.5.25/build.json').read_text('utf8'))['mapping'];source=H.PREPARED.read_bytes();entries=G.hook_entries(source,m)
        from tools import library_build as L
        for n in range(10):
            key=('ニュータイプＬ'+chr(0xff10+n)).encode('cp932');row=next(r for r in entries if r['key']==key)
            self.assertEqual(L.decode(row['english'],m),'Newtype Lv '+str(n))
        changed=bytearray(source);changed[0x8dc808-0x10000]^=1
        with self.assertRaisesRegex(ValueError,'source changed'):G.hook_entries(bytes(changed),m)

if __name__=='__main__':unittest.main()
