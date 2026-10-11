import json
import struct
import unittest
import numpy as np
from tools.common import ROOT
from tools import review19_layout as R,mission_names as N,ui_hook as H,vwf,runtime_names,gtf,domination_art as D
from tests.test_ui_hook import fw


class Review19Tests(unittest.TestCase):
    def test_native_mission_substitution_stores_and_custom_names(self):
        source=H.PREPARED.read_bytes()
        mapping={c:fw(c).hex()for c in 'HibikiKamishiroK. '}
        plan=runtime_names.plan(source,mapping)
        executable,_=vwf.patch(source,{})
        hooked,report=H.hook(executable,[dict(id='test',key='隊'.encode('cp932'),english=fw('Team'))],
            require_srvc=False,payloads=plan['payloads']+N.payloads(mapping))
        addresses=report['table']['payload_vas']
        built,info=N.apply(hooked,addresses)
        cases=N.verify(built,mapping,addresses)
        self.assertEqual(len(cases),15)
        self.assertEqual(sum(c['custom_unchanged']for c in cases),8)
        self.assertFalse(info['save_fields_modified'])
        broken=bytearray(hooked);broken[N.CONSUMER[0]-0x10000]^=1
        with self.assertRaisesRegex(ValueError,'consumer changed'):N.apply(bytes(broken),addresses)

    def test_layered_rewards_and_link_labels_clear_the_values(self):
        plan=R.plan();rows={r['widget_offset']:r for r in plan['edits']}
        self.assertEqual(rows[0x934c4]['en'],'Clears:\nChart:')
        self.assertLess(R.width('Clears:')+4,240)
        self.assertLess(R.width('Game Clear:')+4,240)
        self.assertLess(R.width(rows[0x93264]['en'])+4,250)
        self.assertLess(R.width(rows[0x9cd64]['en'])+4,92)
        self.assertAlmostEqual(plan['reward_subject_x']+R.width('SR Point'),plan['reward_tail_x'])
        # Native amount starts at 531 on a 31-pixel, five-cell centered number.
        end=(rows[0x99da4]['x']+1)*640+R.width('Bonus funds:',31)
        self.assertLess(end+10,608.5-5*31/2)
        self.assertNotIn(0x99dc4,rows)
        self.assertEqual(len([r for r in rows.values()if r['en']=='Clears:\nChart:']),6)

    def test_hud_digits_percentage_and_all_animation_bytes_unchanged(self):
        from tools import eff_art
        raw=eff_art.source_members(eff_art._settings(),[239],{239:D.SOURCE_SHA})[239]
        built,_,_,report=D.render(raw)
        self.assertEqual(built[:eff_art.gtf_base(raw)],raw[:eff_art.gtf_base(raw)])
        for tex in gtf.textures(raw):
            a=gtf.decode(raw,tex);b=gtf.decode(built,tex)
            if tex['index']==1:
                self.assertTrue(np.array_equal(a[96:128],b[96:128]))
                self.assertTrue(np.array_equal(a[64:96,200:],b[64:96,200:]))
            else:self.assertTrue(np.array_equal(a,b))
        self.assertTrue(report['percentage_digits_unchanged'])


if __name__=='__main__':unittest.main()
