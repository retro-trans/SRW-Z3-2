import json,unittest
from tools.common import ROOT
from tools import mission_display as D,mission_text as M,ui_hook as H,review23_layout as R
from tools import ui_layout_text as U,menu_layout as L,status_layout as S,review23_names as N

class Review23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.22/build.json').read_text(encoding='utf8'))['mapping']
        # New native-label letters use the existing ordinary letter slots
        # for this geometry/isolation check; final font readback is separate.
        from tools.native_labels import PREFIX
        for c in 'Sel.MV':cls.mapping.setdefault(PREFIX+c,cls.mapping[c])

    def test_native_copy_preserves_full_static_lookup_keys_and_canary(self):
        rendered=M.plan(lambda c:16)
        cases=D.copy_cases(H.PREPARED.read_bytes(),rendered,self.mapping)
        self.assertEqual(len(cases),262)
        self.assertTrue(any(c['relocated_english_bytes']>128 for c in cases))
        self.assertEqual(max(c['key_bytes']for c in cases),10)
        native=D.stage_text(rendered)
        for jp,en in rendered.items():
            if any(p in jp for p in M.PLACEHOLDERS):self.assertEqual(native[jp],en)
        self.assertEqual(len(D.hook_entries(H.PREPARED.read_bytes(),rendered,self.mapping)),262)
        bad=bytearray(H.PREPARED.read_bytes());bad[0x18c2dc-0x10000]^=1
        with self.assertRaises(ValueError):D.hook_entries(bytes(bad),rendered,self.mapping)

    def test_deployment_labels_leave_numeric_fields_and_flag_pitch_intact(self):
        from tools.battle_layout import source
        from tools.ui_catalog import fssa_strings
        raw=source();edits=R.plan()['edits']
        out,_=U.fssa_patch(raw,edits,self.mapping)
        grow=len(out)-len(raw)
        for at in (0xa2064,0xa37c4,0xa3784,0xa37a4,0xa4c04):
            self.assertEqual(raw[at:at+32],out[at+grow:at+grow+32])
        by={a:r for r in fssa_strings(raw)for a in r['widget_offsets']}
        for e in edits:
            if e['widget_offset']in R.plan()['repeated_movement_widgets']:
                old=by[e['widget_offset']]['text'];self.assertEqual(old.count('\n'),e['en'].count('\n'))
                self.assertEqual(len(old),len(e['en']))
                for mask in range(16):
                    labels=''.join(S.CELL[w]if mask&(1<<n)else '－'for n,w in enumerate(('Air','Grd','Wtr','Und')))
                    self.assertEqual(len(L.encode(dict(en=labels),self.mapping)),8)

    def test_name_corrections_are_word_bound_and_complete(self):
        self.assertEqual(N.corrected('Sachs, Edward Sachs and Girtar Belone.'),'Sacks, Edward Sacks and Giltar Belone.')
        self.assertEqual(N.corrected('Sachsen Heero Yuy Crowe Bluest Yui Ikari'),'Sachsen Heero Yuy Crowe Bluest Yui Ikari')
        report,outputs=N.plan();self.assertEqual(outputs,{})

if __name__=='__main__':unittest.main()
