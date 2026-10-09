import unittest

from tools import mission_text as mt


class MissionTextTest(unittest.TestCase):
    def test_unescape_is_bytewise_like_lua(self):
        # ソ is 83 5C: the scripts store it as 83 5C 5C; "ポ\イ" is a harmless escape of 0x83.
        self.assertEqual(mt.unescape('ソ'.encode('cp932') + b'\\'), 'ソ')
        self.assertEqual(mt.unescape('ポ'.encode('cp932') + b'\\' + 'イント'.encode('cp932')), 'ポイント')
        self.assertEqual(mt.unescape(b'A\\nB'), 'A\nB')

    def test_lua_literal_round_trip(self):
        encoded = bytes((0x83, 0x5C, 0x81, 0xAE)) + b'\n' + bytes((0x87, 0x5C))
        self.assertEqual(mt.unescape_bytes(mt.lua_literal(encoded)), encoded)
        with self.assertRaises(ValueError):
            mt.lua_literal(b'say "hi"')

    def test_id_table_roles(self):
        raw = ('OPERATE_TBL={str_tbl={"敵の全滅。","味方戦艦の撃墜。","なし",};\n'
               'id_tbl={true,0,-1,-1,1,-1,-1,2,};\n}').encode('cp932')
        (_m, lits, roles), = mt.tables(raw)
        self.assertEqual([t for _l, t in lits], ['敵の全滅。', '味方戦艦の撃墜。', 'なし'])
        self.assertEqual(roles, [{'victory'}, {'defeat'}, {'sr'}])

    def test_wrap_keeps_paragraphs(self):
        text = mt.wrap('aaaa bbbb cccc\nd', lambda c: 1, units=9)
        self.assertEqual(text, 'aaaa bbbb\ncccc\nd')


if __name__ == '__main__':
    unittest.main()
