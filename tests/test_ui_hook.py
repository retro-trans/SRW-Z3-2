import struct
import unittest

from tools import ui_hook as uh
from tools import ppc_exec
from tools.common import ROOT

PREPARED = ROOT / 'work/tengoku/prepared/EBOOT.elf'
VWF_END = 0x92eb94           # PH0 size after tools/vwf.py (stub ends at VA 0x93eb94)

# A real FNV-1a 32-bit collision between two drawer-valid cp932 strings.
COLLIDE = (bytes.fromhex('89c195668bc8'), bytes.fromhex('97ba92cd8e58'))


def synthetic_elf():
    """The measured Tengoku layout with the guarded words, nothing else.

    Same file size, program headers, section table geometry and non-loaded
    tail as the real program ELF; VWF already applied (PH0 grown, branch at
    0x147dc into the gap). No SRVC consumer, so the SRVC gate is skipped.
    """
    elf = bytearray(uh.FILE_SIZE)
    elf[:16] = b'\x7fELF\x02\x02\x01\x66' + bytes(8)
    struct.pack_into('>HHIQQQIHHHHHH', elf, 16, 2, 0x15, 1, 0x957608, 64, uh.E_SHOFF, 0,
                     64, 56, 8, 64, uh.SHNUM, 31)
    rows = [uh.PH0_BASE + (VWF_END, VWF_END, 0x10000), uh.PH1] + uh.PH_REST
    for i, r in enumerate(rows):
        uh.PH.pack_into(elf, 64 + i * 56, *r)
    sections = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                (1, 1, 6, 0x10200, 0x200, 0x2c, 0, 0, 4, 0),
                (1, 1, 6, 0x10230, 0x230, 0x769cac, 0, 0, 0x10, 0)]
    sections += [(1, 1, 2, 0x82db00 + 0x100 * i, 0x81db00 + 0x100 * i, 0x40, 0, 0, 4, 0) for i in range(13)]
    sections += [(1, 1, 3, 0x940000 + 0x100 * i, 0x930000 + 0x100 * i, 0x40, 0, 0, 8, 0) for i in range(12)]
    sections += [(1, 8, 3, 0xa31300, 0xa212f4, 0x4c8818, 0, 0, 0x80, 0)]
    sections += [(1, 1, 0, 0, 0xa212f4, 0xc58, 0, 0, 4, 0), (1, 1, 0, 0, 0xa21f4c, 0x268c, 0, 0, 1, 0),
                 (1, 3, 0, 0, 0xa245d8, 0x148, 0, 0, 1, 0)]
    assert len(sections) == uh.SHNUM
    for i, s in enumerate(sections):
        uh.SH.pack_into(elf, uh.E_SHOFF + i * 64, *s)
    elf[0xa212f4:0xa245d8] = bytes((i * 7 + 3) & 0xff for i in range(0xa245d8 - 0xa212f4))
    for va, word in list(uh.GUARDS.items()) + [(uh.SITE, uh.ORIGINAL)]:
        struct.pack_into('>I', elf, va - 0x10000, word)
    struct.pack_into('>I', elf, uh.VWF_SITE - 0x10000, uh.branch(uh.VWF_SITE, 0x93eb10))
    struct.pack_into('>f', elf, uh.TOC - 0x7f1c - 0x10000, -1.0)     # the constant the lfs loads
    elf[0x92eb10 - 0x100:VWF_END] = b'\x60\x00\x00\x00' * ((VWF_END - 0x92eb10 + 0x100) // 4)
    return bytes(elf)


def entry(key, english, eid):
    return {'key': key, 'english': english, 'id': eid}


def fw(text):
    """Fullwidth cp932 test English (always drawable)."""
    return text.translate({i: i + 0xfee0 for i in range(0x21, 0x7f)}).replace(' ', '　').encode('cp932')


class GrammarTests(unittest.TestCase):
    def test_extent_follows_the_drawer(self):
        self.assertEqual(uh.extent(b'\x82\xa0\x00'), 2)
        self.assertEqual(uh.extent(b'1\x00\x82\xa0\x00'), 4)        # escape operand may be NUL
        self.assertEqual(uh.extent(b'\x82\xa0/\x82\xa0\x00'), 3)   # '/' stops drawing
        self.assertEqual(uh.extent(b'\n.\x82\xa0\x00'), 4)
        self.assertIsNone(uh.extent(b'\x81\x40' * 2049 + b'\0'))
        with self.assertRaises(ValueError):
            uh.extent(b'\x82')

    def test_fnv1a_vectors(self):
        self.assertEqual(uh.fnv1a(b''), 0x811c9dc5)
        self.assertEqual(uh.fnv1a(b'a'), 0xe40c292c)
        self.assertEqual(uh.fnv1a(COLLIDE[0]), uh.fnv1a(COLLIDE[1]))

    def test_english_lint(self):
        key = b'\x8c\x88\x92\xe8'
        self.assertEqual(uh.check_english(key, fw('OK')), [])
        self.assertTrue(uh.check_english(key, b'OK'))               # single-byte ASCII
        self.assertTrue(uh.check_english(key, fw('OK') + b'\x82'))  # odd trailing byte
        self.assertTrue(uh.check_english(key, b'1\x0b' + fw('A')))  # escape not in key
        self.assertEqual(uh.check_english(key, b'1\x0b' + fw('A'), allow_escapes=True), [])
        self.assertEqual(uh.check_english(b'1\x0b' + key, b'1\x0b' + fw('A')), [])


class TableTests(unittest.TestCase):
    def test_power_of_two_and_load_factor(self):
        for n in (0, 1, 7, 8, 9, 100, 1000):
            rows = [entry(bytes((0x88 + i // 180, 0x40 + i % 180)), fw('X'), 'e%d' % i) for i in range(n)]
            ext, info = uh.build_table(rows)
            self.assertEqual(info['slots'] & (info['slots'] - 1), 0)
            self.assertLessEqual(info['load_factor'], 0.5)
            self.assertEqual(ext[:4], b'UIH1')
            self.assertEqual(len(ext) % uh.EXT_STEP, 0)

    def test_conflicts_and_duplicates(self):
        k = b'\x8c\x88\x92\xe8'
        with self.assertRaises(ValueError):
            uh.build_table([entry(k, fw('A'), 'a'), entry(k, fw('B'), 'b')])
        _, info = uh.build_table([entry(k, fw('A'), 'a'), entry(k, fw('A'), 'b')])
        self.assertEqual((info['entries'], info['duplicates_merged']), (1, 1))
        with self.assertRaises(ValueError):
            uh.build_table([entry(b'\x82', fw('A'), 'odd')])        # not one drawer string
        with self.assertRaises(ValueError):
            uh.build_table([entry(k, fw('A'), 'x'), entry(b'\x82\xa0', fw('B'), 'x')])


class HookSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.elf = synthetic_elf()
        base = b'\x83\x65\x83\x58\x83\x67'
        cls.entries = [
            entry(COLLIDE[0], fw('Collide A'), 'collide-a'),
            entry(COLLIDE[1], fw('Collide B'), 'collide-b'),
            entry(base, fw('Test'), 'prefix-short'),
            entry(base + b'\x82\xa0', fw('Test A'), 'prefix-long'),
            entry(b'\x8c\x88\x92\xe8\n\x96\xdf\x82\xe9', fw('Confirm') + b'\n' + fw('Back'), 'newline'),
            entry(b'1\x0b\x89\xcc1\x00\x82\xcc', b'1\x0b' + fw('Song') + b'1\x00' + fw('!'), 'escape-nul'),
            entry(b'\x82\xa0/', fw('Slash'), 'slash-end'),
            entry(b'\x81\x40' * 2047, fw('Long'), 'near-cap'),
        ]
        # many keys sharing home slots
        cls.entries += [entry(bytes((0x88, 0x40 + i, 0x89, 0x40 + i)), fw('N%d' % i), 'n%d' % i) for i in range(60)]
        cls.out, cls.report = uh.hook(cls.elf, cls.entries, require_srvc=False, execute=None)

    def test_layout_numbers(self):
        r = self.report
        self.assertEqual(r['stub_va'], '0x93eba0')
        self.assertEqual(r['ext_va'], '0xf00000')
        self.assertEqual(r['ext_file_offset'], '0xef0000')
        self.assertEqual(r['ph1_filesz_memsz'][1], ['%#x' % (0x5c0000 + r['ext_bytes'])] * 2)
        self.assertEqual(int(r['tail_offset'][1], 16) % 16, uh.TAIL % 16)
        self.assertEqual(r['moved_sections'], [29, 30, 31])
        self.assertLessEqual(r['table']['load_factor'], 0.5)
        self.assertEqual(r['table']['hash32_collisions'], 1)
        self.assertGreater(r['table']['displaced_entries'], 0)
        _, _, phs, _ = uh._headers(self.out)
        self.assertEqual(phs[2:], uh.PH_REST)

    def test_every_entry_resolves_by_machine_code_and_mirror(self):
        v = self.report['verification']
        self.assertEqual(v['stub_executed_keys'], len(self.entries))
        _, _, phs, _ = uh._headers(self.out)
        stub_va = int(self.report['stub_va'], 16)
        runner = uh._Runner(self.out, stub_va, self.report['stub_bytes'])
        plain = uh._reader(self.out, phs)
        for e in self.entries:
            r31, _ = runner.run(e['key'] + b'\0')
            en = plain(r31, len(e['english']) + 1)
            self.assertEqual(en, e['english'] + b'\0', e['id'])
            mirror = uh.lookup(uh._reader(self.out, phs, {uh.PROBE_VA: e['key'] + b'\0'}), uh.PROBE_VA)
            self.assertEqual(mirror, r31 & 0xffffffff)

    def test_misses_leave_r31(self):
        _, _, phs, _ = uh._headers(self.out)
        runner = uh._Runner(self.out, int(self.report['stub_va'], 16), self.report['stub_bytes'])
        untouched = (0xa5a5a5a5 << 32) | 0x50000000
        base = b'\x83\x65\x83\x58\x83\x67'
        for data in (b'', base[:4], base + b'\x82\xa2', COLLIDE[0][:4], b'\x81\x40' * 2049,
                     b'\x82\xa0/\x82\xa0'[:2], b'1\x0b\x89\xcc1\x01\x82\xcc'):
            r31, _ = runner.run(data + b'\0')
            self.assertEqual(r31, untouched, data[:12])
        # '/' ends the drawn string: bytes after it do not matter
        r31, _ = runner.run(b'\x82\xa0/\x99\x99\0')
        self.assertNotEqual(r31, untouched)

    def test_isolation_detects_tampering(self):
        geo = {'stub_off': int(self.report['stub_va'], 16) - 0x10000,
               'stub_end': int(self.report['stub_end_va'], 16) - 0x10000,
               'stub_va': int(self.report['stub_va'], 16),
               'ext_end': 0xef0000 + self.report['ext_bytes'],
               'new_tail': int(self.report['tail_offset'][1], 16),
               'delta': int(self.report['tail_delta'], 16)}
        uh.verify(self.elf, self.out, self.entries, geo, require_srvc=False, execute=4)
        for at in (0x200, 0x9db0a0, 0xa00000, len(self.out) - 3000):
            bad = bytearray(self.out)
            bad[at] ^= 1
            with self.assertRaises(ValueError):
                uh.verify(self.elf, bytes(bad), self.entries, geo, require_srvc=False, execute=4)

    def test_refuses_unexpected_layouts(self):
        def change(fn):
            b = bytearray(self.elf)
            fn(b)
            with self.assertRaises(ValueError):
                uh.hook(bytes(b), self.entries[:2], require_srvc=False)
        change(lambda b: struct.pack_into('>Q', b, 64 + 56 + 32, uh.PH1[5] + 16))     # PH1 filesz
        change(lambda b: struct.pack_into('>Q', b, 64 + 2 * 56 + 8, 0xa30000))        # PH2 offset
        change(lambda b: b.extend(b'\0' * 16))                                        # file size
        change(lambda b: struct.pack_into('>I', b, uh.SITE - 0x10000, 0x60000000))    # site patched
        change(lambda b: struct.pack_into('>I', b, uh.VWF_SITE - 0x10000, 0xc1a10094))  # no VWF
        change(lambda b: b.__setitem__(0x92ff00, 1))                                  # gap in use
        change(lambda b: struct.pack_into('>I', b, 0x149a4 - 0x10000, 0x4bfff7f8))    # join changed
        with self.assertRaises(ValueError):                                           # already hooked
            uh.hook(self.out, self.entries[:2], require_srvc=False)
        with self.assertRaises(ValueError):                                           # SRVC gate required
            uh.apply(self.elf, self.entries[:2])

    def test_stub_shape(self):
        code = self.out[int(self.report['stub_va'], 16) - 0x10000:int(self.report['stub_end_va'], 16) - 0x10000]
        listing, _ = uh.check_stub_words(code, int(self.report['stub_va'], 16))
        names = [n for _, _, n in listing]
        self.assertEqual(names[0], 'stdu')
        self.assertEqual(listing[-1][2], 'b')
        self.assertEqual(struct.unpack('>I', code[-8:-4])[0], uh.ORIGINAL)
        self.assertNotIn('bl', names)
        self.assertNotIn('mtspr', names)


@unittest.skipUnless(PREPARED.exists(), 'prepared Tengoku ELF not present')
class RealElfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import vwf
        cls.elf = PREPARED.read_bytes()
        cls.base, _ = vwf.patch(cls.elf, {})

    def test_utf8_key_samples(self):
        self.assertEqual(uh.utf8_key('決定'.encode()), '決定'.encode('cp932'))
        self.assertEqual(uh.utf8_key('Ａ'.encode()), 'Ａ'.encode('cp932'))
        self.assertEqual(uh.utf8_key(b'A'), 'Ａ'.encode('cp932'))          # ASCII -> fullwidth
        self.assertEqual(uh.utf8_key('あ\nい'.encode()), 'あ\nい'.encode('cp932'))
        self.assertEqual(uh.utf8_key('1\x0bあ1\x01'.encode()), b'1\x0a' + 'あ'.encode('cp932') + b'1\x00')
        self.assertEqual(uh.utf8_key('©'.encode()), '■'.encode('cp932'))   # unmapped
        self.assertEqual(uh.utf8_key('あഅx'.encode()), 'あ'.encode('cp932'))  # skips 2 units
        for bad in ('x1'.encode(), '\U0001f600'.encode(), b'\xff'):
            with self.assertRaises(ValueError):
                uh.utf8_key(bad)

    def test_converter_oracle_sample(self):
        import json
        inv = json.loads(uh.INVENTORY.read_text(encoding='utf-8'))['strings']
        utf8 = [(int(s['va'], 16), s['jp']) for s in inv if s['encoding'] == 'utf-8']
        pick = [x for x in utf8 if '1' in x[1] and not x[1].endswith('1')][:20]
        pick += [x for x in utf8 if '\n' in x[1]][:20] + [x for x in utf8 if any(c < '\x80' for c in x[1])][:20]
        pick += utf8[::60]
        r = uh.validate_converter(strings=pick, elf=self.elf)
        self.assertEqual(r['mismatched'], [])
        self.assertEqual(r['identical_both_models'] + len(r['skipped']), len(pick))
        oracle = uh.ConverterOracle(self.elf)
        table = uh.unicode_table(self.elf)
        for text in ('あഅആい', 'Aéÿ', '1\x01x1\x0b', 'ａ\nｂ'):
            want = uh.convert(text.encode(), table) + b'\0\0'
            for model in 'AB':
                got, fill, _ = oracle.run(text.encode(), model)
                self.assertEqual(got[:len(want)], want)
                self.assertFalse(any(b != fill for b in got[len(want):]))

    def test_canaries_build_and_all_gates_pass(self):
        entries = uh.canary_entries(self.elf)
        self.assertEqual([e['source']['encoding'] for e in entries], ['cp932', 'utf-8'])
        out, rep = uh.apply(self.base, entries)
        self.assertTrue(rep['verification']['srvc_table']['checked'])
        self.assertTrue(rep['verification']['srvc_table']['pristine_size'])
        self.assertEqual(rep['stub_va'], '0x93eba0')

    def test_order_with_srvc_table_rewrite_does_not_matter(self):
        from tools import srvc
        entries = uh.canary_entries(self.elf)
        old = srvc.read_table(self.base, srvc.SRVC_SIZE)
        new = [x + (16 if i >= 5 else 0) for i, x in enumerate(old)]
        a, _ = uh.hook(srvc.patch_table(self.base, old, new), entries, execute=2)
        hooked, _ = uh.hook(self.base, entries, execute=2)
        b = srvc.patch_table(hooked, old, new)
        self.assertEqual(a, b)
        self.assertEqual(srvc.read_table(b, new[-1]), new)

    def test_inventory_keys_hook(self):
        import json
        inv = json.loads(uh.INVENTORY.read_text(encoding='utf-8'))['strings']
        rows, seen = [], set()
        for s in inv:
            if not s['display'] or len(rows) >= 400:
                continue
            raw = s['jp'].encode('cp932' if s['encoding'] == 'cp932' else 'utf-8')
            try:
                key = raw if s['encoding'] == 'cp932' else uh.utf8_key(raw, self.elf)
                if uh.extent(key + b'\0') != len(key):
                    continue
            except (ValueError, UnicodeEncodeError):
                continue
            if key in seen:
                continue
            seen.add(key)
            rows.append(entry(key, fw('E%d' % len(rows)), s['va']))
        out, rep = uh.hook(self.base, rows, execute=64)
        self.assertEqual(rep['verification']['readback_keys'], len(rows))


class DecoderTests(unittest.TestCase):
    def test_forms_used_by_the_stub(self):
        code = uh.stub(0x93eba0)
        names = [ppc_exec.decode(struct.unpack_from('>I', code, i)[0], 0x93eba0 + i)[0]
                 for i in range(0, len(code), 4)]
        for n in ('stdu', 'mfcr', 'rldicl', 'addis', 'cmpl', 'mullw', 'lbzx', 'rlwinm', 'mtcrf', 'lfs'):
            self.assertIn(n, names)

    def test_unknown_word_is_refused(self):
        with self.assertRaises(ppc_exec.Unsupported):
            ppc_exec.decode(0x7c0004ac)        # sync: not implemented, must not be skipped


if __name__ == '__main__':
    unittest.main()
