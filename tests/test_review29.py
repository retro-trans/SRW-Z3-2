"""Exercise actual mission composition before translation lookup."""
import json,unittest
from tools.common import ROOT
from tools import mission_display as D,mission_text as M,ui_hook as H,library_build as L,vwf,ppc_exec as P

class Review29(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=H.PREPARED.read_bytes()
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.28/build.json').read_text('utf8'))['mapping']
        cls.rendered=M.plan(D.advance)
        cls.entries=D.hook_entries(cls.source,cls.rendered,cls.mapping)
        final,_=vwf.patch(cls.source,{})
        cls.final,cls.info=H.apply(final,cls.entries)

    def test_all_native_numbered_rows_reach_complete_english(self):
        cases=D.composition_cases(self.final,self.rendered,self.mapping)
        self.assertEqual(len(cases),1048)
        wanted={r['key']:r['english']for r in self.entries}
        runner=H._Runner(self.final,int(self.info['stub_va'],16),self.info['stub_bytes'])
        read=H._reader(self.final,H._headers(self.final)[2])
        for case in cases:
            self.assertEqual(len(case['keys']),case['rows'])
            for raw in case['keys']:
                key=bytes.fromhex(raw);pointer,_=runner.run(key+b'\0')
                self.assertEqual(read(pointer,len(wanted[key])+1),wanted[key]+b'\0')

    def test_numbered_text_preserves_words_and_panel_width(self):
        for row in D.rows(self.rendered):
            for number in range(1,4):
                text=D.displayed_english(row['en'],number)
                self.assertEqual(text[2:].split(),row['en'].split())
                for line in text.split('\n'):
                    self.assertLessEqual(sum(map(D.advance,line)),M.LINE_UNITS)

    def test_source_guards_include_real_composer_and_number_prefix(self):
        for va in (D.COMPOSER[0],0x99b358):
            bad=bytearray(self.source);bad[va-0x10000]^=1
            with self.assertRaises(ValueError):D.hook_entries(bytes(bad),self.rendered,self.mapping)

    def test_subfic_result_and_carry_boundaries(self):
        for value,immediate in ((0,101),(100,101),(102,101),(P.M64,101),(0,-1)):
            mem=P.Memory();mem.map(0x1000,H._d(8,5,3,immediate).to_bytes(4,'big')+bytes.fromhex('4e800020'))
            m=P.Machine(mem);m.r[3]=value;m.pc=0x1000;m.lr=0x2000;m.run({0x2000})
            self.assertEqual(m.r[5],(immediate-value)&P.M64)
            self.assertEqual(m.ca,int((immediate&P.M64)>=value))

    def test_live_names_counters_and_all_numbered_native_rows(self):
        cases=D.live_cases(self.final,self.rendered,self.mapping)
        self.assertEqual(len(cases),200)
        self.assertTrue(any(r['profile']=='maximum-custom'for r in cases))
        self.assertLessEqual(max(r['bytes']for r in cases),302)

    def test_canonical_term_repair_is_idempotent(self):
        from tools import review29_terms as T
        _,outputs=T.plan();self.assertEqual(outputs,{})

if __name__=='__main__':unittest.main()
