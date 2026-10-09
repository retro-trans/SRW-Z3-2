"""SRVC block format, executable table, growable rebuild and independent readback."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools import srvc, srvc_check, voice_bind, voice_write

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / 'work/tengoku/prepared'


def make_block(lines, unref=(), tail=0, cue_flag=0):
    """A block in the game's layout: one rule in slot 0 covering every line.
    `lines` may repeat a string; repeats share one pool entry."""
    pool, at = bytearray(), {}
    for s in list(dict.fromkeys(list(lines) + list(unref))):
        at[s] = len(pool)
        pool += s + b'\0'
    n6 = len(lines)
    slots = [0] * srvc.SLOTS
    rules = b''
    if n6:
        slots[0] = 0 | 1 << 16 | 0xff << 24
        rules = struct.pack('<4H', 0, 5, 0, n6)
    out = bytearray(struct.pack('<BBBBHH', 3, srvc.SLOTS, 0, 0, 1 if n6 else 0, n6))
    out += struct.pack('<%dI' % srvc.SLOTS, *slots) + rules
    out += b''.join(struct.pack('<II', 1000 + k, cue_flag) for k in range(n6))
    out += b''.join(struct.pack('<I', at[s]) for s in lines)
    out += pool + bytes(tail)
    out += bytes(-len(out) % 16)
    return bytes(out)


def make_srvc(specs):
    data, tab = bytearray(), []
    for spec in specs:
        tab.append(len(data))
        data += make_block(**spec)
    tab.append(len(data))
    return bytes(data), tab


def make_elf(tab):
    """Sparse program ELF holding exactly the consumer code, TOC slots, the
    start-read descriptor, the path string and the table."""
    code_va, code_off, code_len = 0x139000, 0x1000, 0xb000
    toc_va, toc_off, toc_len = 0x99a000, 0xc000, 0x6000
    data_va, data_off, data_len = 0x9eb000, 0x12000, 0x2000
    elf = bytearray(data_off + data_len)
    elf[:4] = b'\x7fELF'
    elf[4], elf[5] = 2, 2
    struct.pack_into('>Q', elf, 32, 64)
    struct.pack_into('>HH', elf, 54, 56, 3)
    for i, (off, va, n) in enumerate(((code_off, code_va, code_len), (toc_off, toc_va, toc_len),
                                      (data_off, data_va, data_len))):
        struct.pack_into('>IIQQQQQQ', elf, 64 + 56 * i, 1, 5, off, va, va, n, n, 0x10000)
    seg = lambda va: (code_off + va - code_va) if va < toc_va else (
        (toc_off + va - toc_va) if va < data_va else data_off + va - data_va)
    for va, w in srvc.CODE.items():
        struct.pack_into('>I', elf, seg(va), w)
    opd = 0x99b000
    struct.pack_into('>II', elf, seg(opd), srvc.START_READ_VA, srvc.TOC_BASE)
    struct.pack_into('>I', elf, seg(srvc.TOC_BASE - 0x5b5c), opd)
    struct.pack_into('>I', elf, seg(srvc.TOC_BASE - 0x5b54), data_va + 0xa0)
    struct.pack_into('>I', elf, seg(srvc.TOC_BASE - 0x5d74), data_va + 0x80)
    elf[seg(data_va + 0x80):seg(data_va + 0x80) + len(srvc.PATH_STRING)] = srvc.PATH_STRING
    elf[seg(data_va + 0xa0):seg(data_va + 0xa0) + 4 * len(tab)] = srvc.pack_table(tab)
    # the next table in the image restarts at 0, ending the run
    return bytes(elf)


SPECS = [
    {'lines': []},
    {'lines': [b'\x81\x75A\x81\x76', b'\x81\x75B\x81\x76', b'\x81\x75A\x81\x76'], 'unref': [b'old']},
    {'lines': [b'one', b'two'], 'tail': 16},
    {'lines': []},
    {'lines': [b'x', b'', b'yy']},
]


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.data, self.tab = make_srvc(SPECS)
        self.elf = make_elf(self.tab)

    def test_locates_table_from_code(self):
        loc = srvc.locate_table(self.elf, len(self.data))
        self.assertEqual(loc['table'], self.tab)
        self.assertEqual(loc['count'], len(SPECS))

    def test_changed_consumer_code_is_refused(self):
        elf = bytearray(self.elf)
        at = srvc.va_to_offset(self.elf, 0x1390c4)
        elf[at + 3] ^= 1
        with self.assertRaises(ValueError):
            srvc.locate_table(bytes(elf))

    def test_table_must_end_at_file_size(self):
        with self.assertRaises(ValueError):
            srvc.locate_table(self.elf, len(self.data) + 16)

    def test_noop_rebuild_is_identical(self):
        new, tab, _ = srvc.rebuild(self.data, self.tab)
        self.assertEqual((new, tab), (self.data, self.tab))

    def test_shared_string_is_replaced_once_and_unreferenced_kept(self):
        blocks = srvc.parse(self.data, self.tab)
        b = blocks[1]
        a = b.pool + b.offs[0]
        new, tab, rows = srvc.rebuild(self.data, self.tab, {a: b'LONG REPLACEMENT ' * 20})
        nb = srvc.parse(new, tab)[1]
        got = [srvc.string_at(new, nb.pool + o) for o in nb.offs]
        self.assertEqual(got, [b'LONG REPLACEMENT ' * 20, b'\x81\x75B\x81\x76', b'LONG REPLACEMENT ' * 20])
        self.assertIn(b'old\0', new[nb.pool:tab[2]])
        self.assertGreater(tab[2] - tab[1], self.tab[2] - self.tab[1])
        self.assertTrue(all(x % 16 == 0 for x in tab))
        self.assertEqual(new[tab[2]:], self.data[self.tab[2]:])
        elf2 = srvc.patch_table(self.elf, self.tab, tab, expect=None)
        self.assertEqual(srvc_check.verify(self.elf, elf2, self.data, new, {a: b'LONG REPLACEMENT ' * 20}), [])

    def test_per_line_split(self):
        refs = {(1, 2): b'only the third line'}
        new, tab, _ = srvc.rebuild(self.data, self.tab, refs=refs)
        nb = srvc.parse(new, tab)[1]
        got = [srvc.string_at(new, nb.pool + o) for o in nb.offs]
        self.assertEqual(got[0], b'\x81\x75A\x81\x76')
        self.assertEqual(got[2], b'only the third line')
        elf2 = srvc.patch_table(self.elf, self.tab, tab, expect=None)
        self.assertEqual(srvc_check.verify(self.elf, elf2, self.data, new, refs=refs), [])

    def test_empty_string_and_tail_preserved(self):
        blocks = srvc.parse(self.data, self.tab)
        self.assertGreaterEqual(blocks[2].tail, 16)
        new, tab, _ = srvc.rebuild(self.data, self.tab, {blocks[4].pool + blocks[4].offs[0]: b'xyz',
                                                         blocks[2].pool + blocks[2].offs[0]: b'ONE'})
        nb = srvc.parse(new, tab)
        self.assertEqual([srvc.string_at(new, nb[4].pool + o) for o in nb[4].offs], [b'xyz', b'', b'yy'])
        self.assertEqual(nb[2].tail, blocks[2].tail)

    def test_readback_catches_corruption(self):
        blocks = srvc.parse(self.data, self.tab)
        a = blocks[2].pool + blocks[2].offs[1]
        repl = {a: b'replacement'}
        new, tab, _ = srvc.rebuild(self.data, self.tab, repl)
        elf2 = srvc.patch_table(self.elf, self.tab, tab, expect=None)
        self.assertEqual(srvc_check.verify(self.elf, elf2, self.data, new, repl), [])
        # wrong text
        self.assertTrue(srvc_check.verify(self.elf, elf2, self.data, new, {a: b'other'}))
        # stale executable table (grown file with the original table)
        self.assertTrue(srvc_check.verify(self.elf, self.elf, self.data, new, repl))
        # a byte flipped in an untouched block
        bad = bytearray(new)
        bad[tab[1] + 9] ^= 0x40
        self.assertTrue(srvc_check.verify(self.elf, elf2, self.data, bytes(bad), repl))
        # a string reaching past its block window
        bad = bytearray(new)
        nb = srvc.parse(new, tab)[2]
        bad[nb.pool:tab[3]] = b'z' * (tab[3] - nb.pool)
        self.assertTrue(srvc_check.verify(self.elf, elf2, self.data, bytes(bad), repl))
        # executable changed outside the table
        bad_elf = bytearray(elf2)
        bad_elf[-1] ^= 1
        self.assertTrue(srvc_check.verify(self.elf, bytes(bad_elf), self.data, new, repl))

    def test_refuses_non_string_start_and_nul(self):
        blocks = srvc.parse(self.data, self.tab)
        with self.assertRaises(ValueError):
            srvc.rebuild(self.data, self.tab, {blocks[1].pool + 1: b'x'})
        with self.assertRaises(ValueError):
            srvc.rebuild(self.data, self.tab, {blocks[1].pool: b'a\0b'})

    def test_patch_table_refuses_wrong_original(self):
        with self.assertRaises(ValueError):
            srvc.patch_table(self.elf, [0] * len(self.tab), self.tab, expect=None)

    def test_writer_edits_guard_stale_and_conflicts(self):
        enc = lambda t: t.encode('ascii')
        ok = [{'block': 1, 'k': 0, 'jp': srvc.text(b'\x81\x75A\x81\x76'), 'text': 'Hello'}]
        new, elf2, rep = voice_write.build(self.data, self.elf, ok, enc, expect=None)
        self.assertEqual(rep['strings_replaced'], 1)
        self.assertEqual(srvc.read_table(elf2, len(new), None)[-1], len(new))
        with self.assertRaises(ValueError):
            voice_write.build(self.data, self.elf, [dict(ok[0], jp='stale')], enc, expect=None)
        clash = ok + [{'block': 1, 'k': 2, 'text': 'Different'}]
        with self.assertRaises(ValueError):
            voice_write.build(self.data, self.elf, clash, enc, expect=None)

    def test_output_guard(self):
        with self.assertRaises(ValueError):
            voice_write._guard('E:/RPCS3/dev_hdd0')
        with self.assertRaises(ValueError):
            voice_write._guard(ROOT / 'work/output/iso/test')
        with tempfile.TemporaryDirectory() as tmp:
            voice_write._guard(tmp)

    def test_every_line_bound_to_one_slot(self):
        blocks = srvc.parse(self.data, self.tab)
        for r in srvc.lines(self.data, blocks):
            self.assertEqual(len(r['uses']), 1)
            self.assertEqual(voice_bind.slot_label(r['uses'][0][0]), 'attack')


@unittest.skipUnless((PREPARED / 'SRVC.BIN').exists() and (PREPARED / 'EBOOT.elf').exists(),
                     'run `python -m tools.srvc prepare --apply` first')
class TengokuFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.elf = srvc.load_prepared()
        cls.tab = srvc.read_table(cls.elf, len(cls.data))

    def test_table_and_counts(self):
        self.assertEqual(len(self.data), srvc.SRVC_SIZE)
        self.assertEqual(len(self.tab), srvc.NBLOCKS + 1)
        blocks = srvc.parse(self.data, self.tab)
        refs = srvc.lines(self.data, blocks)
        self.assertEqual(len(refs), 78302)
        self.assertEqual(len({r['jp'] for r in refs}), 37187)
        self.assertEqual(sum(1 for b in blocks if b.n6), 283)
        self.assertTrue(all(len(r['uses']) >= 1 for r in refs))
        # the 03 4a scan and the executable table agree block for block
        scan = [i for i in range(0, len(self.data), 16) if self.data[i:i + 2] == b'\x03\x4a']
        self.assertEqual(scan, self.tab[:-1])

    def test_noop_rebuild_is_byte_identical(self):
        new, tab, _ = srvc.rebuild(self.data, self.tab)
        self.assertEqual(new, self.data)
        self.assertEqual(tab, self.tab)
        self.assertEqual(srvc.patch_table(self.elf, self.tab, tab), self.elf)

    def test_synthetic_replacement_reads_back(self):
        edits = voice_write.synthetic_edits(self.data, self.tab)
        new, elf2, rep = voice_write.build(self.data, self.elf, edits, lambda t: t.encode('ascii'))
        self.assertEqual(rep['blocks'], 368)
        self.assertGreater(len(new), len(self.data))
        self.assertEqual(srvc.read_table(elf2, len(new))[-1], len(new))
        # an untouched (textless) block keeps its bytes at its new position
        new_tab = srvc.read_table(elf2, len(new))
        self.assertEqual(new[new_tab[0]:new_tab[1]], self.data[self.tab[0]:self.tab[1]])


if __name__ == '__main__':
    unittest.main()
