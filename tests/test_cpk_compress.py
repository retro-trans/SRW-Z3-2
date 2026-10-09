"""CRILAYLA compression in cpkpatch, and the large-archive (mmap) paths."""
import os
import random
import tempfile
import unittest
from pathlib import Path

from tools import cpk as cpk_module
from tools.cpk import CPK, decompress_crilayla
from tools.cpkpatch import build, compress_crilayla
from tools.verify_archives import compare, itoc_members
try:
    from test_cpk import fixture          # unittest discover -s tests
except ImportError:
    from tests.test_cpk import fixture

PACK = Path(__file__).resolve().parents[1] / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/TABATA/TPACKPS3.CPK'


def samples():
    rng = random.Random(5)
    yield bytes(0x104)                                   # smallest compressible
    yield bytes(range(256)) * 40                         # periodic
    yield bytes(rng.getrandbits(8) for _ in range(5000))  # incompressible
    yield b'\0' * 70000 + b'tail'                       # long runs, 8-bit VLE chains
    text = b'Here Comes the New Problem Boy; A Hope Called Taboo. '
    yield b''.join(text[:rng.randint(3, len(text))] for _ in range(800))
    # matches at the window edge (distance 8194) and just beyond it
    block = bytes(rng.getrandbits(8) for _ in range(8194))
    yield bytes(0x100) + block + block[:300] + bytes(rng.getrandbits(8) for _ in range(1)) + block
    # every VLE boundary: run lengths 3..300
    yield b''.join(bytes([i % 251]) * 3 + b'x' * (i % 300) + b'yz' for i in range(400))


class CompressionTests(unittest.TestCase):
    def test_round_trip_with_reader_decompressor(self):
        for data in samples():
            packed = compress_crilayla(data)
            self.assertIsNotNone(packed)
            self.assertEqual(packed[:8], b'CRILAYLA')
            self.assertEqual(int.from_bytes(packed[12:16], 'little') % 4, 0)
            self.assertEqual(decompress_crilayla(packed), data)

    def test_too_small_is_left_raw(self):
        self.assertIsNone(compress_crilayla(b'x' * 0x100))

    def test_compressed_build_reads_back_and_shrinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.cpk'
            source.write_bytes(fixture())
            big = (b'GTF-ish header' + bytes(500) + b'pixels' * 2000) * 10
            rng = random.Random(1)
            noise = bytes(rng.getrandbits(8) for _ in range(400))
            target = root / 'z.cpk'
            build(source, target, {1: big, 2: noise}, compress=True, workers=1)
            result = compare(source, target, {1: big, 2: noise})
            self.assertEqual(result['replaced_compressed'], 1)    # noise stays raw
            members = itoc_members(target.read_bytes())[1]
            self.assertLess(members[1]['size'], len(big))
            self.assertEqual(members[1]['extract'], len(big))
            self.assertEqual(members[2]['size'], len(noise))
            with CPK(target) as reader:
                self.assertEqual(reader.read(reader.files[0]), big)

    def test_compress_only_selected_members(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.cpk'
            source.write_bytes(fixture())
            data = {1: b'a' * 4000, 2: b'b' * 4000}
            target = root / 'some.cpk'
            build(source, target, data, compress={2}, workers=1)
            self.assertEqual(compare(source, target, data)['replaced_compressed'], 1)
            members = itoc_members(target.read_bytes())[1]
            self.assertEqual(members[1]['size'], 4000)
            self.assertLess(members[2]['size'], 4000)
            with self.assertRaises(ValueError):
                build(source, root / 'bad.cpk', data, compress={3}, workers=1)

    def test_compare_rejects_wrong_compressed_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.cpk'
            source.write_bytes(fixture())
            data = b'abc' * 5000
            target = root / 'z.cpk'
            build(source, target, {1: data}, compress=True, workers=1)
            with self.assertRaises(ValueError):
                compare(source, target, {1: b'abd' * 5000})


class LargeArchiveTests(unittest.TestCase):
    def test_mmap_reader_and_writer(self):
        old = cpk_module.MMAP_THRESHOLD
        cpk_module.MMAP_THRESHOLD = 0
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / 'source.cpk'
                source.write_bytes(fixture())
                with CPK(source) as reader:
                    self.assertTrue(reader.mapped)
                    self.assertEqual(reader.read(reader.files[1]), b'TWO!!')
                target = root / 'out.cpk'
                build(source, target, {})
                self.assertTrue(compare(source, target, {})['byte_identical'])
                target.unlink()          # nothing may still hold the file open
        finally:
            cpk_module.MMAP_THRESHOLD = old

    def test_archive_beyond_64_mib(self):
        payload = bytes(range(256)) * ((65 << 20) // 256 + 1)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.cpk'
            source.write_bytes(fixture())
            target = root / 'large.cpk'
            build(source, target, {2: payload})
            self.assertGreater(target.stat().st_size, 64 << 20)
            result = compare(source, target, {2: payload})
            self.assertEqual(result['untouched_members_verified'], 1)
            with CPK(target) as reader:
                self.assertTrue(reader.mapped)
                rebuilt = root / 'again.cpk'
                small = root / 'small'
                small.write_bytes(b'S')
            build(target, rebuilt, {2: small})       # rebuild FROM a large archive
            compare(target, rebuilt, {2: b'S'})
            self.assertLess(rebuilt.stat().st_size, 1 << 20)


@unittest.skipUnless(PACK.exists() and os.environ.get('TENGOKU_FULL_TEXTURES') == '1',
                     'set TENGOKU_FULL_TEXTURES=1 with the pristine pack for the real-data round trip')
class RealPackCompressionTests(unittest.TestCase):
    def test_every_tpack_member_recompresses(self):
        with CPK(PACK) as archive:
            for entry in archive.files:
                data = archive.read(entry)
                self.assertEqual(decompress_crilayla(compress_crilayla(data)), data, entry['id'])


if __name__ == '__main__':
    unittest.main()
