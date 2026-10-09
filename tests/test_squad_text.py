import unittest

from tools import squad_text as sq


SCRIPT = ('-- 「コメント」 "無視"\n'
          'ENEMY_TBL_00={24,0,0,"ラー・カイラム",1,0,true,"ソ\\ーラリアン",}\n'
          'TOUROKU_000={0,65,"マクロス・クォーター",421,}\n'
          'OPERATE_TBL={str_tbl={"敵の全滅。",};\nid_tbl={true,0,-1,-1,-1,-1,-1,-1,};\n}\n'
          't_1={[[会話「ガンダム」]]}\n'
          'function F()\nSC_UNIT_JOIN_TO_TAG(1,2,3,4,"キリコ");\nprint("デバッグ");\nend\n').encode('cp932')


class SquadTextTest(unittest.TestCase):
    def test_scope(self):
        found = [text for _lit, text in sq.literals(SCRIPT)]
        self.assertEqual(found, ['ラー・カイラム', 'ソーラリアン', 'マクロス・クォーター', 'キリコ'])

    def test_scan_skips_comments_and_long_strings(self):
        texts = [sq.mt.unescape(l['raw']) for l in sq.scan(SCRIPT)]
        self.assertNotIn('無視', texts)
        self.assertIn('敵の全滅。', texts)
        self.assertIn('デバッグ', texts)


if __name__ == '__main__':
    unittest.main()
