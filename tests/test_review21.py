import json,unittest
from tools import review21_layout as L,review21_names as N,ui_layout_text as T,battle_layout as B,eboot_text as E,ui_vwf_build as V

class Review21Tests(unittest.TestCase):
    def test_complete_name_corpus_and_unrelated_yui(self):
        report=N.coverage()
        self.assertEqual(report['fields_examined']['dialogue'],63553)
        self.assertGreater(report['corrected_full_name_occurrences']['Heero Yuy'],0)
        self.assertGreater(report['corrected_full_name_occurrences']['Crowe Bluest'],0)
        term,_=E.resolver().resolve('ユイ')
        self.assertEqual(term['en'],'Yui')
        _,pending=N.plan();self.assertFalse(pending)

    def test_source_bound_widgets_and_four_digit_cost_clearance(self):
        plan=L.plan();self.assertEqual(plan,json.loads(L.DEST.read_text(encoding='utf8')))
        source=B.source();tokens={c for row in plan['edits']for c in row['en']if c!='\n'}
        # Real build mapping already validates fonts; this independent map
        # deliberately includes unassigned CP932 cells in its round trip.
        mapping={c:bytes((0x81+(i//192),0x40+(i%192))).hex()for i,c in enumerate(sorted(tokens))}
        final,_=T.fssa_patch(source,plan['edits'],mapping)
        self.assertGreater(len(final),len(source))
        for row in plan['crystal_rows']:
            ink=sum(V.raster(c)[1]for c in row['text'])*24/32
            self.assertGreaterEqual(row['cost_left']-row['left']-ink,12)
        self.assertEqual(len(set(r['text']for r in plan['crystal_rows'])),9)
        for row in plan['tabs']:
            self.assertAlmostEqual(row['left']+row['width']/2,row['center'])
        broken=plan['edits'][0].copy();broken['source_widget_sha256']='0'*64
        with self.assertRaises(ValueError):T.fssa_patch(source,[broken],mapping)

if __name__=='__main__':unittest.main()
