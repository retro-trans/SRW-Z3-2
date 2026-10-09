"""Generated CPK fixtures cover metadata growth and refusal cases."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools.cpk import CPK, decompress_crilayla
from tools.cpkpatch import build
from tools.verify_archives import compare, itoc_members


def table(name, columns, rows):
    strings = bytearray()
    def label(value):
        offset = len(strings)
        strings.extend(value.encode('ascii') + b'\0')
        return offset
    name_offset = label(name)
    schema = b''.join(struct.pack('>BI', 0x50 | kind, label(key)) for key, kind in columns)
    payload, body = bytearray(), bytearray()
    for row in rows:
        for key, kind in columns:
            value = row[key]
            if kind == 11:
                body.extend(struct.pack('>II', len(payload), len(value)))
                payload.extend(value)
            else:
                body.extend(struct.pack('>' + {2: 'H', 4: 'I', 6: 'Q'}[kind], value))
    stride = sum({2: 2, 4: 4, 6: 8, 11: 8}[kind] for _, kind in columns)
    row_offset = 24 + len(schema)
    string_offset = row_offset + len(body)
    data_offset = string_offset + len(strings)
    result = struct.pack('>IIIIHHI', row_offset, string_offset, data_offset, name_offset, len(columns), stride, len(rows))
    result += schema + body + strings + payload
    return b'@UTF' + struct.pack('>I', len(result)) + result


def fixture(tight=False):
    payloads = [b'one', b'TWO!!']
    low = table('CpkItocL', [('ID', 2), ('FileSize', 2), ('ExtractSize', 2)],
                [{'ID': i + 1, 'FileSize': len(p), 'ExtractSize': len(p)} for i, p in enumerate(payloads)])
    high = table('CpkItocH', [('ID', 2), ('FileSize', 4), ('ExtractSize', 4)], [])
    itoc = table('CpkItocInfo', [('FilesL', 4), ('FilesH', 4), ('DataL', 11), ('DataH', 11)],
                 [{'FilesL': 2, 'FilesH': 0, 'DataL': low, 'DataH': high}])
    content = 4096
    if tight:   # padding after the ITOC too small for any size-row migration
        end = 2064 + len(itoc)
        content = end + (-end % 16)
    fields = {'ContentOffset': content, 'ContentSize': 32, 'EnabledDataSize': 8,
              'EnabledPackedSize': 8, 'ItocOffset': 2048, 'ItocSize': len(itoc) + 16,
              'Files': 2, 'Align': 16}
    header = table('CpkHeader', [(key, 6) for key in fields], [fields])
    result = bytearray(content)
    result[:16] = b'CPK ' + struct.pack('<IQ', 255, len(header))
    result[16:16 + len(header)] = header
    result[2048:2064] = b'ITOC' + struct.pack('<IQ', 255, len(itoc))
    result[2064:2064 + len(itoc)] = itoc
    result += payloads[0] + bytes(13) + payloads[1]
    return result


class CPKTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.cpk'
        self.source.write_bytes(fixture())

    def tearDown(self):
        self.temp.cleanup()

    def test_noop_is_byte_identical(self):
        target = self.root / 'out.cpk'
        build(self.source, target, {})
        self.assertTrue(compare(self.source, target, {})['byte_identical'])

    def test_growth_migrates_low_row_into_empty_high_table(self):
        payload = b'a' * 70000
        replacement = self.root / 'text'
        replacement.write_bytes(payload)
        target = self.root / 'grown.cpk'
        build(self.source, target, {1: replacement})
        result = compare(self.source, target, {1: payload})
        self.assertEqual(result['untouched_members_verified'], 1)
        self.assertEqual(itoc_members(target.read_bytes())[1][1]['size'], 70000)

    def test_multiple_migrations_and_shrinking(self):
        replacements = {}
        for i in (1, 2):
            replacements[i] = self.root / ('large%d' % i)
            replacements[i].write_bytes(bytes([64 + i]) * 70000)
        grown = self.root / 'grown.cpk'
        build(self.source, grown, replacements)
        compare(self.source, grown, {i: p.read_bytes() for i, p in replacements.items()})
        small = self.root / 'small'
        small.write_bytes(b'Z')
        target = self.root / 'shrunk.cpk'
        build(grown, target, {2: small})
        compare(grown, target, {2: b'Z'})

    def test_migration_moves_content_offset_when_padding_is_short(self):
        source = self.root / 'tight.cpk'
        source.write_bytes(fixture(tight=True))
        replacements = {}
        for i in (1, 2):
            replacements[i] = self.root / ('big%d' % i)
            replacements[i].write_bytes(bytes([64 + i]) * 70000)
        target = self.root / 'tight_out.cpk'
        build(source, target, replacements)
        compare(source, target, {i: p.read_bytes() for i, p in replacements.items()})
        self.assertGreater(CPK(target)._h('ContentOffset'), CPK(source)._h('ContentOffset'))
        self.assertEqual(CPK(target)._h('ContentOffset') % 16, 0)

    def test_source_and_existing_destination_are_protected(self):
        original = self.source.read_bytes()
        with self.assertRaises(ValueError):
            build(self.source, self.source, {})
        self.assertEqual(self.source.read_bytes(), original)

    def test_unknown_id_is_rejected_before_output(self):
        target = self.root / 'bad.cpk'
        with self.assertRaises(ValueError):
            build(self.source, target, {999: self.source})
        self.assertFalse(target.exists())

    def test_truncated_or_invalid_compressed_data_rejected(self):
        self.source.write_bytes(fixture()[:-1])
        with self.assertRaises(ValueError):
            CPK(self.source)
        with self.assertRaises(ValueError):
            decompress_crilayla(b'CRILAYLA' + struct.pack('<II', 100, 9999))


if __name__ == '__main__':
    unittest.main()
