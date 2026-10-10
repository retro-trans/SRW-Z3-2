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


class CondensedLayout(unittest.TestCase):
    def test_duplicate_active_records_are_rejected(self):
        import json
        import tempfile
        from pathlib import Path
        original = db.dlg.TRANSLATIONS
        with tempfile.TemporaryDirectory() as folder:
            try:
                db.dlg.TRANSLATIONS = Path(folder)
                for name in ('first', 'second'):
                    (Path(folder) / (name + '.json')).write_text(json.dumps({'rows': {'same-id': {'en': 'A'}}}), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Duplicate active dialogue record'):
                    db.translations()
            finally:
                db.dlg.TRANSLATIONS = original

    def test_source_bound_profile_rejects_changed_record(self):
        from tools import dialogue_layout as layout
        self.assertTrue(layout.condensed('604:t_6:4', {'sha': '3a93a41e5e'}))
        self.assertFalse(layout.condensed('other', {'sha': '3a93a41e5e'}))
        with self.assertRaises(ValueError):
            layout.condensed('604:t_6:4', {'sha': 'changed'})

    def test_condensed_encoding_uses_matching_glyph_cells(self):
        from tools import dialogue_layout as layout
        mapping = {'A': '81ae', '@condensed:A': '81af'}
        self.assertEqual(db.encode('A$n', layout.mapping_for('604:t_6:4', mapping)), b'\x81\xaf$n')
        self.assertEqual(db.encode('A$n', layout.mapping_for('other', mapping)), b'\x81\xae$n')

    def test_full_sphere_list_fits_without_losing_names(self):
        import json
        from tools.common import ROOT
        from tools.dialogue import Width
        from tools.library_text import GLOSSARY, Resolver
        entry = json.loads((ROOT / 'work/translation/en/retranslation_2026-10-09_batch5/drafts/dlg_2086_02.json').read_text(encoding='utf-8'))['rows']['604:t_6:4']
        resolver = Resolver(json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms'])
        width = Width(resolver)
        rendered = db.render(entry, {'id': '604:t_6:4'}, resolver,
                             lambda c: width.adv.get(c, 32))
        self.assertEqual(len(rendered.split('\n')) - 1, 3)
        flattened = ' '.join(x.strip('　') for x in rendered.partition('\n')[2].split('\n'))
        self.assertEqual(flattened, width.expand(entry['en'].partition('\n')[2]))


if __name__ == '__main__':
    unittest.main()
