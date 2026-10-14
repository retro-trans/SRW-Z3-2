"""Exercise complete scene/news centering and native save paragraph copying."""
import json, unittest
from tools.common import ROOT
from tools import ui_hook as H, ui_build as U, ui_vwf_build as F, vwf, link_layout as K
from tools import review32_content as C, review32_save as S, review32_layout as A
from tools import library_runtime as R, eboot_text as E
from tools.cpk import CPK
from tools.inventory import FONT
from tools.pipeline import config,verified_source


class Review32(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=H.PREPARED.read_bytes();cls.original=original
        prior=json.loads((ROOT/'work/output/builds/0.5.31/build.json').read_text('utf8'))['mapping']
        tokens=set(prior)|C.characters()
        with CPK(verified_source(config(ROOT/'config/tengoku.json'),FONT))as arc:
            pages=[arc.read(r)for r in arc.files if r['id']in(1,3)]
        cls.mapping,_=U.allocate(pages,tokens,lambda t:[t]);widths={}
        for token,code in cls.mapping.items():
            x,y=U.cell_xy(code);width=F.raster(token)[1]
            if width!=32:widths[y//32*128+x//32]=width
        elf,info=vwf.patch(original,widths)
        entries=C.hook_entries(original,cls.mapping);plan=S.plan(original,cls.mapping);plan['mapping']=cls.mapping
        elf,hook=H.apply(elf,entries,plan['payloads']+[(K.STATE,K.PAYLOAD)])
        elf,_=R.native_patch(elf,original,cls.mapping)
        cls.final,cls.save_report=S.apply(elf,original,plan,hook['table']['payload_vas'])
        cls.final,cls.layout=K.apply(cls.final,original,hook['table']['payload_vas'][K.STATE],info['table_va'],cls.mapping,[])
        cls.save_plan=plan

    def test_all_scene_and_news_origins_preserve_caller_state(self):
        cases=C.origin_cases(self.final,self.mapping,self.layout)
        self.assertEqual(len(cases),539)
        self.assertEqual(len([r for r in cases if r['two_lines']]),22)
        self.assertTrue(any(r['id']=='206:t_3:3'for r in cases))

    def test_real_save_constructor_keeps_both_english_paragraphs(self):
        table=H.unicode_table(self.final)
        for key,carrier in self.save_plan['payloads']:
            lines,steps=S.native_lines(self.final,carrier[:-1]);self.assertGreater(steps,100)
            row=next(r for r in self.save_plan['rows']if r['key']==key)
            self.assertEqual([H.convert(line,table)for line in lines],
                             [E.encode(line,self.mapping)for line in row['english'].split('\n')])

    def test_layout_is_bound_to_fixed_numeric_and_icon_slots(self):
        data=A.plan();self.assertEqual(len(data['edits']),11)
        self.assertTrue(all(r['pixels']<=r['available']for r in data['bounds']))
        for row in data['edits']:
            if 'icon_column'in row:
                encoded=A.guide_encoded(row,self.mapping);self.assertEqual(encoded.count(b'\n'),1)
                self.assertIn(E.encode(': Fast)',self.mapping),encoded)

    def test_complete_headline_words_and_source_structure_survive(self):
        rows=C.headlines();self.assertEqual(len(rows),11)
        for row in rows:
            self.assertEqual(len(row['lines']),2)
            original=E.unshow(C.L.expand(E.load()['strings'][row['jp']]['en'],E.resolver()))
            self.assertEqual(' '.join(row['lines']).split(),original.split())
            self.assertLessEqual(max(row['spans']),C.HEADLINE_UNITS)


if __name__=='__main__':unittest.main()
