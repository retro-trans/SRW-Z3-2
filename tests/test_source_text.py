import unittest
from tools.source_text import byte_offsets, lua_strings


class LuaTests(unittest.TestCase):
    def test_comments_and_delimiters_inside_quoted_strings(self):
        text = '--[[ comment [[nested-looking ]]\nx="[[quoted]]"\ny=[=[a ]] b]=]\n-- line [[ignored]]\nz=[[日本語]]'
        found = list(lua_strings(text))
        self.assertEqual([r['text'] for r in found], ['[[quoted]]', 'a ]] b', '日本語'])
        self.assertEqual([r['kind'] for r in found], ['quoted', 'long', 'long'])

    def test_escaped_quotes_and_cp932_trail_backslash(self):
        text = 'x="ソ\\\"end"; y=[[次]]'
        rows = list(lua_strings(text))
        offsets = byte_offsets(text)
        encoded = text.encode('cp932')
        for row in rows:
            self.assertEqual(encoded[offsets[row['content_start']]:offsets[row['content_end']]].decode('cp932'), row['text'])

    def test_malformed_source_is_not_silently_skipped(self):
        for text in ('x=[[missing', 'x="unfinished', '--[=[unfinished', 'x="literal\nnewline"'):
            with self.assertRaises(ValueError):
                list(lua_strings(text))


if __name__ == '__main__':
    unittest.main()
