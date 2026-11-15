"""Synthetic hostile-container checks plus sealed Tengoku carry-forward proof."""
import hashlib
import struct
import unittest
from tools import cfw_self as C


def fixture():
    elf = bytearray(144)
    elf[:6] = b'\x7fELF\x02\x02'
    struct.pack_into('>HHIQQQIHHHHHH', elf, 16,
                     2, 21, 1, 0x10000, 64, 0, 0, 64, 56, 1, 64, 0, 0)
    C.PH.pack_into(elf, 64, 1, 5, 128, 0x10000, 0x10000, 16, 32, 16)
    elf[128:] = b'ppu-test-payload'
    out = bytearray(512+len(elf))
    out[:4] = b'SCE\0'
    struct.pack_into('>IHH', out, 4, 2, 0x8000, 1)
    struct.pack_into('>QQ', out, 16, 512, len(elf))
    struct.pack_into('>QQQQQQQQ', out, 0x28, 0x80, 0xa0, 0xe0, 512,
                     0x120, 0x140, 0x160, 112)
    struct.pack_into('>QIIQQ', out, 0x80, 123, 0x1000002, 4, 1, 0)
    out[0xa0:0xe0] = elf[:64]
    out[0xe0:0x118] = elf[64:120]
    struct.pack_into('>QQIIII', out, 0x120, 640, 16, 1, 0, 0, 2)
    struct.pack_into('>4I', out, 0x140, 1, 0, 16, 0)
    struct.pack_into('>IIQ', out, 0x160, 1, 48, 1)
    out[0x170:0x190] = bytes(range(32))
    struct.pack_into('>IIQ', out, 0x190, 2, 64, 0)
    out[0x190+36:0x190+56] = hashlib.sha1(elf).digest()
    out[512:] = elf
    return bytes(out), bytes(elf)


class ContainerTests(unittest.TestCase):
    def test_full_payload_and_bss_are_preserved(self):
        data, elf = fixture()
        proof = C.verify(data, elf, data)
        self.assertTrue(proof['payload_byte_identical'])
        self.assertEqual(proof['active_loads'], 1)
        self.assertEqual(C.extract_debug(data), elf)
        self.assertFalse(proof['hardware_verified'])

    def test_original_application_identity_and_capabilities_retained(self):
        data, elf = fixture()
        tool = bytearray(data)
        tool[0x80:0xa0] = bytes(32)
        tool[0x170:0x190] = bytes(32)
        final = C.retain_identity(tool, data)
        self.assertEqual(final, data)
        C.verify(final, elf, data)

    def test_corrupted_payload_headers_mappings_or_identity_rejected(self):
        data, elf = fixture()
        for offset in (4, 6, 16, 24, 0x80, 0xa0, 0xe0, 0x120, 0x130,
                       0x140, 0x170, 0x190+36, 512+128):
            with self.subTest(offset=offset):
                damaged = bytearray(data)
                damaged[offset] ^= 1
                with self.assertRaises(ValueError):
                    C.verify(damaged, elf, data)

    def test_truncated_or_trailing_containers_rejected(self):
        data, elf = fixture()
        for damaged in (data[:3], data[:70], data[:-1], data+b'junk'):
            with self.assertRaises(ValueError):
                C.verify(damaged, elf, data)

    def test_malformed_control_chains_rejected(self):
        data, _ = fixture()
        for offset, value in ((0x164, 8), (0x16c, 0), (0x190, 1), (0x19c, 1)):
            damaged = bytearray(data)
            struct.pack_into('>I', damaged, offset, value)
            with self.assertRaises(ValueError):
                C.controls(damaged)

    def test_invalid_loader_layout_rejected(self):
        _, elf = fixture()
        for field, value in ((1, 7), (2, 129), (5, 256), (6, 8), (7, 3)):
            damaged = bytearray(elf)
            row = list(C.PH.unpack_from(elf, 64))
            row[field] = value
            C.PH.pack_into(damaged, 64, *row)
            with self.assertRaises(ValueError):
                C.program_headers(damaged)


class TengokuCarryForwardTests(unittest.TestCase):
    def test_built_wrapper_carries_entire_certified_translation(self):
        from tools import cfw_package as P
        proof = P.components()
        self.assertEqual(proof['changed_outputs'], ['EBOOT.BIN', 'EFFPS3.CPK'])
        self.assertTrue(proof['self_checks']['payload_byte_identical'])
        self.assertTrue(proof['other_game_files_and_fonts_unchanged'])
        self.assertEqual(proof['self_checks']['active_loads'], 3)


if __name__ == '__main__':
    unittest.main()
