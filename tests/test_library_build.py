import struct
import unittest

from tools import library_build as lb
from tools.library_text import Resolver
from tools.source_text import library_fields


def obfuscate(data):
    return bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in data)


def record(fields):
    body = b''.join(t.encode() + struct.pack('<I', len(p)) + p for t, p in fields)
    block = b'DATA' + struct.pack('<I', len(body)) + body
    return obfuscate(b'ZKANKYWD' + struct.pack('<II', 0x100, 0xc) + b'DSIZ' + struct.pack('<I', len(block)) + block)


TERMS = [
    {'jp': 'スフィア', 'kind': 'keyword', 'en': 'Sphere', 'status': 'official', 'targets': [], 'token': 'スフィア'},
    {'jp': '脳量子波', 'kind': 'keyword', 'en': 'quantum brainwaves', 'status': 'official', 'targets': [], 'token': '脳量子波'},
    {'jp': '第９の使徒', 'kind': 'robot', 'en': 'the Ninth Angel', 'status': 'official', 'targets': [], 'token': '第９の使徒'},
]


class LibraryBuildTests(unittest.TestCase):
    def test_expand_capitalizes_only_at_sentence_starts(self):
        r = Resolver(TERMS)
        self.assertEqual(lb.expand('$$脳量子波$$ matter. Uses $$脳量子波$$.', r),
                         'Quantum brainwaves matter. Uses quantum brainwaves.')
        self.assertEqual(lb.expand('A $$スフィア|lc$$ bearer and two $$スフィア$$s', r),
                         'A sphere bearer and two Spheres')
        self.assertEqual(lb.expand('It fought $$第９の使徒$$.\n$$第９の使徒$$ fell.', r),
                         'It fought the Ninth Angel.\nThe Ninth Angel fell.')
        with self.assertRaises(ValueError):
            lb.expand('$$missing$$', r)

    def test_wrap_respects_units_and_indents_paragraphs(self):
        width = lambda c: 32 if ord(c) > 0x7f else 10
        # indent 32 + 'aaaa bbbb' 90 = 122: one unit too wide for 121
        text = lb.wrap('aaaa bbbb cccc\ndd', width, units=121)
        lines = text.split('\n')
        self.assertEqual(lines, ['　aaaa', 'bbbb cccc', '　dd'])
        self.assertTrue(all(sum(width(c) for c in line) <= 121 for line in lines))
        self.assertEqual(lb.wrap('aaaa bbbb', width, units=122), '　aaaa bbbb')

    def test_encode_decode_mixed_text(self):
        mapping = {'A': '8190', 'b': '81a0', ' ': '81b0'}
        data = lb.encode('　A b\n「A」', mapping)
        self.assertEqual(lb.decode(data, mapping), '　A b\n「A」')
        with self.assertRaises(UnicodeEncodeError):
            lb.encode('\U0001f600', mapping)

    def test_rebuild_keeps_order_header_and_untouched_fields(self):
        raw = record([('WORD', 'スフィア'.encode('cp932')), ('SRCE', b'\x81\x75X\x81\x76'), ('DSCR', b'old')])
        rebuilt = lb.rebuild(raw, {'DSCR': b'new text', 'WORD': b'W'})
        magic, fields = library_fields(rebuilt)
        plain = obfuscate(rebuilt)
        self.assertEqual(magic, 'ZKANKYWD')
        self.assertEqual([f['tag'] for f in fields], ['WORD', 'SRCE', 'DSCR'])
        payload = {f['tag']: plain[f['offset']:f['offset'] + f['bytes']] for f in fields}
        self.assertEqual(payload, {'WORD': b'W', 'SRCE': b'\x81\x75X\x81\x76', 'DSCR': b'new text'})
        self.assertEqual(lb.rebuild(raw, {}), raw)

    def test_voice_actor_fails_closed_and_keeps_placeholders(self):
        catalog = {'石田彰': 'Akira Ishida'}
        self.assertEqual(lb.voice_actor('石田彰', catalog), 'Akira Ishida')
        self.assertIsNone(lb.voice_actor('－－－', catalog))
        with self.assertRaises(ValueError):
            lb.voice_actor('未知', catalog)

    def test_pilot_names_join_and_placeholders(self):
        r = Resolver(TERMS + [
            {'jp': '甲', 'kind': 'pilot', 'en': 'Ko', 'status': 'official', 'targets': [], 'token': '甲'},
            {'jp': '乙', 'kind': 'pilot', 'en': 'Otsu', 'status': 'official', 'targets': [], 'token': '乙'}])
        self.assertEqual(lb.pilot_names('甲、乙', r), 'Ko, Otsu')
        with self.assertRaises(ValueError):      # ・ is inside one name, never a separator
            lb.pilot_names('甲・乙', r)
        self.assertIsNone(lb.pilot_names('※ここに、搭乗者名称を書く※', r))
        self.assertIsNone(lb.pilot_names('－', r))

    def test_stat_fields_become_ascii(self):
        self.assertEqual(lb.stat('５７．０ｍ'), '57.0m')


if __name__ == '__main__':
    unittest.main()
