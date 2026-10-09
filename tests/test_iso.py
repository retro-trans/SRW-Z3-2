"""Synthetic ISO fixtures; no original game data is checked in."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools.common import destination
from tools.isoread import ISO9660, SECTOR


def record(name, lba, size, flags=0):
    length = 33 + len(name) + (len(name) % 2 == 0)
    data = bytearray(length)
    data[0] = length
    struct.pack_into('<I', data, 2, lba)
    struct.pack_into('>I', data, 6, lba)
    struct.pack_into('<I', data, 10, size)
    struct.pack_into('>I', data, 14, size)
    data[25] = flags
    data[28:32] = b'\x01\0\0\x01'
    data[32] = len(name)
    data[33:33 + len(name)] = name
    return data


def fixture(entries, joliet=False):
    data = bytearray(30 * SECTOR)
    primary = bytearray(SECTOR)
    primary[:7] = b'\x01CD001\x01'
    struct.pack_into('<I', primary, 80, 30)
    struct.pack_into('>I', primary, 84, 30)
    struct.pack_into('<H', primary, 128, SECTOR)
    struct.pack_into('>H', primary, 130, SECTOR)
    root = record(b'\0', 20, SECTOR, 2)
    primary[156:156 + len(root)] = root
    data[16 * SECTOR:17 * SECTOR] = primary
    terminator = 17
    if joliet:
        secondary = bytearray(primary)
        secondary[0] = 2
        secondary[88:91] = b'%/E'
        data[17 * SECTOR:18 * SECTOR] = secondary
        terminator = 18
    data[terminator * SECTOR:terminator * SECTOR + 7] = b'\xffCD001\x01'
    directory = b''.join(entries)
    data[20 * SECTOR:20 * SECTOR + len(directory)] = directory
    data[22 * SECTOR:22 * SECTOR + 5] = b'FIRST'
    data[25 * SECTOR:25 * SECTOR + 4] = b'LAST'
    return data


class ISOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def image(self, entries, joliet=False):
        path = self.root / 'test.iso'
        path.write_bytes(fixture(entries, joliet))
        return path

    def test_multi_extent_read_and_stream_exclude_sector_padding(self):
        path = self.image([record(b'WP.CPK;1', 22, 5, 128), record(b'WP.CPK;1', 25, 4)])
        with ISO9660(path) as iso:
            files = list(iso.walk())
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0][1]['size'], 9)
            self.assertEqual(iso.read(files[0][1]), b'FIRSTLAST')
            self.assertEqual(b''.join(iso.blocks(files[0][1], 2)), b'FIRSTLAST')
            output = self.root / 'joined'
            iso.copy(files[0][1], output)
            self.assertEqual(output.read_bytes(), b'FIRSTLAST')
            with self.assertRaises(FileExistsError):
                iso.copy(files[0][1], output)

    def test_joliet_keeps_long_unicode_names(self):
        name = 'LONG_SHADER_NAME_01234567890123456789_日本.CGELF'
        path = self.image([record((name + ';1').encode('utf-16-be'), 22, 5)], True)
        with ISO9660(path) as iso:
            self.assertEqual(list(iso.walk())[0][0], '/' + name)

    def test_unfinished_and_wrong_name_chains_fail(self):
        for entries in ([record(b'A;1', 22, 5, 128)],
                        [record(b'A;1', 22, 5, 128), record(b'B;1', 25, 4)],
                        [record(b'A;1', 22, 5), record(b'A;1', 25, 4)]):
            with ISO9660(self.image(entries)) as iso:
                with self.assertRaises(ValueError):
                    list(iso.walk())

    def test_endian_mismatch_and_outside_extent_fail(self):
        damaged = record(b'A;1', 22, 5)
        damaged[6] = 1
        for item in (damaged, record(b'A;1', 29, SECTOR + 1)):
            with ISO9660(self.image([item])) as iso:
                with self.assertRaises(ValueError):
                    list(iso.walk())

    def test_paths_cannot_escape_output(self):
        for name in ('../oops', '/absolute', 'C:/outside', 'ok/../../oops', 'data:stream', 'a\\..\\oops'):
            with self.assertRaises(ValueError):
                destination(self.root, name)


if __name__ == '__main__':
    unittest.main()
