import json,unittest
from tools.common import ROOT
from tools import review33_reports as G, review33_names as N, review32_content as C
from tools import ui_hook as H,vwf,link_layout as K,ui_build as U,ui_vwf_build as F

class Review33(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.32/build.json').read_text('utf8'))['mapping']
        original=H.PREPARED.read_bytes();widths={}
        for token,code in cls.mapping.items():
            x,y=U.cell_xy(code);width=F.raster(token)[1]
            if width!=32:widths[y//32*128+x//32]=width
        elf,info=vwf.patch(original,widths)
        elf,cls.hook=H.apply(elf,G.hook_entries(original,cls.mapping),[(K.STATE,K.PAYLOAD)])
        cls.elf,cls.layout=K.apply(elf,original,cls.hook['table']['payload_vas'][K.STATE],info['table_va'],cls.mapping,[])

    def test_every_native_report_paragraph_translates_and_centers(self):
        result=G.verify(self.elf,self.mapping,self.hook,self.layout)
        self.assertEqual(result['player_occurrences'],97)
        self.assertEqual(len(result['native_report_cases']),22)
        self.assertEqual(len(result['origin_cases']),36)
        bonuses=[r for r in result['native_report_cases']if 'bonus from AG' in r['english']]
        self.assertEqual(sum(r['occurrences']for r in bonuses),82)
        self.assertTrue(any(r['english'].endswith('50 Z-Chips.')for r in bonuses))

    def test_active_arm_raker_has_no_lowercase_override(self):
        data=N.plan();self.assertEqual(data['active_references'],1);self.assertEqual(data['edits'],[])

if __name__=='__main__':unittest.main()
