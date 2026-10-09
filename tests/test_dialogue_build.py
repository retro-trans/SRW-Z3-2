import unittest

from tools import dialogue_build as db


class _Resolver:
    def resolve(self, token):
        return {'en': token}, None


class WrapSpeech(unittest.TestCase):
    def test_wraps_within_box(self):
        lines = db.wrap_speech('「' + ' '.join(['word'] * 40) + '」', lambda c: 16 if ord(c) < 128 else 32)
        self.assertGreater(len(lines), 1)
        for i, line in enumerate(lines):
            lead = 32 if i else 0
            width = sum(16 if ord(c) < 128 else 32 for c in line)
            self.assertLessEqual(width, db.dlg.BOX_UNITS - lead)

    def test_protagonist_code_is_budgeted(self):
        # $n is budgeted at 144 units: six fit in the 960-unit box, seven do not.
        self.assertEqual(len(db.wrap_speech(' '.join(['$n'] * 6), lambda c: 16)), 1)
        self.assertEqual(len(db.wrap_speech(' '.join(['$n'] * 7), lambda c: 16)), 2)


class Render(unittest.TestCase):
    def test_two_blocks_stay_separate(self):
        entry = {'en': 'Jeffrey\n「A goes left.」\n「B goes right.」'}
        out = db.render(entry, {}, _Resolver(), lambda c: 16)
        self.assertEqual(out.split('\n'), ['Jeffrey', '「A goes left.」', '「B goes right.」'])

    def test_continuation_indent(self):
        entry = {'en': 'X\n「' + ' '.join(['word'] * 40) + '」'}
        lines = db.render(entry, {}, _Resolver(), lambda c: 16).split('\n')
        self.assertTrue(all(l.startswith('　') for l in lines[2:]))


class LuaSafety(unittest.TestCase):
    def test_block_ending_in_bracket_byte_is_refused(self):
        # A letter allocated 0x825D would end the block with ']' and close [[...]] early.
        self.assertFalse(db.lua_safe(db.encode('OK', {'O': '81ae', 'K': '825d'})))
        self.assertTrue(db.lua_safe(db.encode('OK', {'O': '81ae', 'K': '81af'})))
        self.assertFalse(db.lua_safe(b'a]]b'))
        self.assertFalse(db.lua_safe(b'a[[b'))


if __name__ == '__main__':
    unittest.main()
