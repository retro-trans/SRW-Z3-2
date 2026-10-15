import json,struct,unittest
from tools.common import ROOT
from tools import review40_tabs as S,ui_layout_text as U,menu_layout as M
from tools.menu_layout import encode


class SearchTabsTests(unittest.TestCase):
    def test_both_states_are_english_before_native_centering(self):
        mapping=json.loads((ROOT/'work/output/builds/0.5.39/build.json').read_text('utf8'))['mapping']
        source=S.B.source();plan=S.plan()
        self.assertEqual(plan,json.loads(S.DEST.read_text('utf8')))
        reference=[e for e in M.plan()['edits']if e['widget_offset']in S.ABILITIES]
        out,_=U.fssa_patch(source,plan['edits']+reference,mapping);grow=len(out)-len(source)
        rows={a-grow:r for r in S.U.fssa_strings(out,decode=lambda r:r.hex())for a in r['widget_offsets']}
        for word,pair in dict(S.PAIRS,Abilities=S.ABILITIES).items():
            for at in pair:self.assertEqual(rows[at]['raw'],encode(dict(en=word),mapping))
            self.assertEqual(rows[pair[0]]['raw'],rows[pair[1]]['raw'])
        for e in plan['edits']:
            at=e['widget_offset']
            self.assertEqual(out[at+grow+4:at+grow+32],source[at+4:at+32])

    def test_native_centers_and_working_abilities_style_are_preserved(self):
        source=S.B.source();p=S.plan();changed={e['widget_offset']for e in p['edits']}
        self.assertEqual(changed,{0x96f24,0x96f44,0x97104,0x97124})
        self.assertTrue(changed.isdisjoint(S.ABILITIES))
        for word,pair in S.PAIRS.items():
            self.assertEqual(source[pair[0]+4:pair[0]+8],source[pair[1]+4:pair[1]+8])
            for at in pair:self.assertTrue(source[at+23]&0x40)
        for row in p['bounds']:self.assertLess(row['width'],200)
        self.assertTrue(all(set(e)=={'widget_offset','en','source_sha256','source_widget_sha256','notes'}for e in p['edits']))

    def test_real_caption_renderer_keeps_both_state_centers(self):
        base=ROOT/'work/output/builds/0.5.39';b=json.loads((base/'build.json').read_text('utf8'))
        cases=S.native_cases((base/'EBOOT.BIN').read_bytes(),b['mapping'],b['executable']['table_va'])
        self.assertEqual(len(cases),12)
        self.assertEqual({r['en']for r in cases},{'Spirit','Skills','Abilities'})
        for r in cases:self.assertAlmostEqual(r['left']+r['width']/2,r['center'],places=4)


if __name__=='__main__':unittest.main()
