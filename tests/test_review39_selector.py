import json,struct,unittest
from tools.common import ROOT
from tools import review39_selector as S,review39_build as B,ui_layout_text as U


class MapSelectorTests(unittest.TestCase):
    def test_two_states_have_identical_plural_words_and_one_separator(self):
        p=S.plan();self.assertEqual(p,json.loads(S.DEST.read_text('utf8')))
        rows={r['widget_offset']:r for r in p['edits']}
        for pair in S.PAIRS:
            words=''.join(rows[a]['en']for a in pair)
            self.assertEqual(words,'Allies / Enemies');self.assertEqual(words.count('/'),1)
        for a,b in zip(S.PAIRS[0],S.PAIRS[1]):
            for field in ('en','x','y','font_metrics'):self.assertEqual(rows[a][field],rows[b][field])
        self.assertGreaterEqual(p['bounds']['minimum_side_margin'],7)

    def test_compiled_widgets_preserve_colors_and_selection_flags(self):
        mapping=json.loads((B.BASE/'build.json').read_text('utf8'))['mapping']
        source=S.B.source();p=S.plan();new,_=U.fssa_patch(source,p['edits'],mapping)
        grow=len(new)-len(source)
        for e in p['edits']:
            at=e['widget_offset'];final=new[at+grow:at+grow+32];old=source[at:at+32]
            self.assertEqual(final[12:16],old[12:16]);self.assertEqual(final[21:23],old[21:23])
            self.assertEqual(final[24:],old[24:]);self.assertEqual(final[23],old[23]&~0x40)
            self.assertEqual(list(final[16:21]),[26,26,24,26,26])
        broken=bytearray(new);broken[p['edits'][0]['widget_offset']+grow+12]^=1
        with self.assertRaises(ValueError):U.verify_fssa(source,bytes(broken),p['edits'],mapping)


if __name__=='__main__':unittest.main()
