import json
import unittest
from tools.common import ROOT
from tools import endless_narration as N,ui_review_fixes as R


class ReviewTests(unittest.TestCase):
    def test_concluding_rows_are_guarded_and_keep_the_timed_continuation(self):
        from tools.pipeline import config,verified_source
        from tools.ui_coverage import member
        from tools.aid_art import ARCHIVE
        blob=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),27)
        rows=N.sources(blob)
        self.assertEqual([r['offset']for r in rows],[0x654,0x6a4])
        self.assertEqual([len(r['raw'])for r in rows],[22,32])
        self.assertTrue(N.ENGLISH[0].endswith('...'))
        self.assertTrue(N.ENGLISH[1].startswith('the beginning'))
        self.assertEqual(json.loads(N.DEST.read_text(encoding='utf8')),N.plan())
        bad=bytearray(blob);bad[0x654]^=1
        with self.assertRaises(ValueError):N.sources(bytes(bad))

    def test_caption_repair_keeps_rows_and_unrelated_words(self):
        voice='・音声設定\n・ＳＥ設定\n・ＢＧＭ設定\n\n・ソート・サブ情報の記憶'
        before='・Voice Settings ( :    )\n・SE Settings\n・BGM Settings\n\n・Remember Sort / Secondary Info'
        after=R.wording(voice,before)
        self.assertEqual(before.count('\n'),after.count('\n'))
        self.assertNotIn('Settings (',after)
        self.assertEqual(after.split('\n')[0],'・Voice Vol.')
        # Source Play anchor minus one icon cell and an eight-pixel gap.
        # Labels start at 191.5; the fixed Play text starts at 413.5.
        from tools.ui_description_layout import advance
        self.assertLessEqual(191.5+sum(map(advance,after.split('\n')[0]))*28/32,413.5-28-8)
        self.assertEqual(R.wording('声','Melee Settings'), 'Melee Settings')
        self.assertFalse(R.plan(),'Reviewed UI fixes remain unapplied')


if __name__=='__main__':unittest.main()
