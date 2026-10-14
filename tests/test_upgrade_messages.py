import json,struct,unittest
from tools import upgrade_messages as U,upgrade_oracle as O,upgrade_layout as L
from tools import ui_hook as H,eboot_text as E,trophy_text as T,vwf
from tests.test_ui_hook import fw
from tools.common import ROOT


class UpgradeMessageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=H.PREPARED.read_bytes()
        chars=U.characters()|set(''.join(r['item_en']for r in U.plan()['conditions']))
        cls.mapping={c:fw(c).hex()for c in chars}
        cls.entries=U.hook_entries(cls.source,cls.mapping)
        base,_=vwf.patch(cls.source,{})
        cls.elf,cls.info=H.hook(base,cls.entries,require_srvc=False)
        cls.runner=H._Runner(cls.elf,int(cls.info['stub_va'],16),cls.info['stub_bytes'])
        cls.read=staticmethod(H._reader(cls.elf,H._headers(cls.elf)[2]))

    def hit(self,key,text):
        pointer,_=self.runner.run(key+b'\0');want=E.encode(text,self.mapping)+b'\0'
        self.assertEqual(self.read(pointer,len(want)),want)

    def test_every_native_report_with_source_and_relocated_part_names(self):
        read=H._reader(self.source,H._headers(self.source)[2]);rows,_=U.source_rows(self.source)
        count=0
        for row in rows:
            if row['condition_en'] is None:continue
            ident=struct.unpack('>h',read(0x855c0c+row['index']*16+12,2))[0]
            for name in (row['part_jp'].encode('cp932'),E.encode(row['item_en'],self.mapping)):
                lines,_=O.report(self.source,ident,name)
                self.hit(lines[1],'Condition met: '+row['condition_en']+'.')
                self.hit(lines[2],'Now at D-Trader: '+row['item_en']+'.')
                count+=1
        self.assertEqual(count,46)
        self.assertEqual(len(self.entries),80)
        self.assertEqual(U.plan()['item_count'],24)

    def test_all_native_bonus_questions_after_real_utf8_conversion(self):
        read=H._reader(self.source,H._headers(self.source)[2]);table=struct.unpack('>11I',read(0xa26808,44));count=0
        for index,va in enumerate(table):
            if va not in U.BONUSES:continue
            lines,_=O.bonus(self.source,index)
            self.hit(H.utf8_key(lines[0],self.source),'Gain "'+U.BONUSES[va]+'".')
            self.assertEqual(lines[1],'よろしいですか？'.encode('utf8'));count+=1
        self.assertEqual(count,9)

    def test_exact_lookup_does_not_replace_unrelated_messages(self):
        raw='無関係な確認'.encode('cp932');pointer,_=self.runner.run(raw+b'\0')
        self.assertEqual(pointer&0xffffffff,0x50000000)

    def test_colored_awards_join_once_with_native_fonts(self):
        plan=L.plan();source=__import__('tools.battle_layout',fromlist=['source']).source()
        for line in plan['lines']:
            self.assertAlmostEqual(line['join'],line['left']+L.width(line['subject']))
            self.assertAlmostEqual((line['left']+line['right'])/2,line['center'])
        for row in plan['edits']:
            self.assertFalse(row['mode']&64)
            self.assertEqual(row['mode'],source[row['widget_offset']+23]&~64)
            self.assertNotIn('font_metrics',row)

    def test_complete_trophy_pack_and_corruption_rejection(self):
        final,report=T.build();original=T.source();data=T.plan()
        self.assertTrue(T.verify(original,final,data));self.assertEqual(report['translated_fields'],144)
        self.assertEqual(len(data['trophies']),35)
        self.assertIn('Break, Gain and Luck',data['trophies'][28]['detail'])
        self.assertNotIn('Fortune',json.dumps(data))
        bad=bytearray(final);bad[-1]^=1
        with self.assertRaisesRegex(ValueError,'checksum'):T.unpack(bytes(bad))

    def test_source_guard_rejects_changed_runtime_table(self):
        changed=bytearray(self.source);changed[0x310328-0x10000]^=1
        with self.assertRaisesRegex(ValueError,'getter changed'):U.source_rows(bytes(changed))

if __name__=='__main__':unittest.main()
