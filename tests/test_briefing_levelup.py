import json
import struct
import unittest
from tools.common import ROOT
from tools import briefing_narration as B,status_layout as S


class BriefingLevelUp(unittest.TestCase):
    def test_fleet_source_guard_and_original_sentence_break(self):
        from tools import fleet_narration as F
        from tools.pipeline import config,verified_source
        from tools.ui_coverage import member
        from tools.aid_art import ARCHIVE
        raw=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),F.MEMBER)
        rows=F.sources(raw)
        self.assertEqual([r['offset']for r in rows],list(F.OFFSETS))
        broken=bytearray(raw);broken[F.OFFSETS[0]]^=1
        with self.assertRaises(ValueError):F.sources(broken)
        self.assertEqual(json.loads(F.DEST.read_text(encoding='utf8')),F.plan())
        self.assertFalse(F.ENGLISH[0].endswith('.'))
        self.assertTrue(F.ENGLISH[1].endswith('.'))

    def test_native_date_float_move_preserves_other_state(self):
        from tools import ppc_exec as P
        mem=P.Memory();mem.map(0x300000,struct.pack('>I',0xffa00890),writable=False)
        m=P.Machine(mem);m.pc=0x300000;m.f=[i+.125 for i in range(32)]
        m.cr=0xb3c7a965;m.lr=0xdead00;before=(m.r[:],m.f[:],m.cr,m.lr)
        m.step()
        self.assertEqual(m.f[29],before[1][1])
        self.assertEqual((m.r,m.cr,m.lr),(before[0],before[2],before[3]))
        self.assertEqual([f for n,f in enumerate(m.f)if n!=29],
                         [f for n,f in enumerate(before[1])if n!=29])

    def test_briefing_source_guard_and_complete_three_rows(self):
        from tools.pipeline import config,verified_source
        from tools.ui_coverage import member
        from tools.aid_art import ARCHIVE
        raw=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),B.MEMBER)
        rows=B.sources(raw)
        self.assertEqual([r['offset']for r in rows],list(B.OFFSETS))
        broken=bytearray(raw);broken[0]^=1
        with self.assertRaises(ValueError):B.sources(broken)
        self.assertEqual(json.loads(B.DEST.read_text(encoding='utf8')),B.plan())
        for line in B.ENGLISH:self.assertNotIn('\n',B.opening_narration.validate(line))

    def test_levelup_pair_order_and_shared_score_cleanup(self):
        edits={e['widget_offset']:e for e in S.plan()['edits']}
        self.assertEqual(edits[0x99f04]['en'],'DEF\nSKL')
        self.assertEqual(edits[0x99f24]['en'],'EVD\nHIT')
        self.assertEqual(edits[0x8f044]['en'],'')
        for at in (0x99f04,0x99f24):
            self.assertNotIn('x',edits[at]);self.assertEqual(edits[at]['font_metrics'][3],28)
        self.assertNotIn('x',edits[0x8f044]);self.assertNotIn('font_metrics',edits[0x8f044])


if __name__=='__main__':unittest.main()
