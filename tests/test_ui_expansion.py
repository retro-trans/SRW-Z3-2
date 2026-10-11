import struct
import unittest
from unittest.mock import patch

from tools import ui_hook as uh, ui_catalog, ui_layout_text, ui_runtime, eboot_text, ui_description_layout
from tools.common import sha256
from tests.test_ui_hook import synthetic_elf, entry, fw


def fixture_fssa():
    data = bytearray(0x180)
    data[:8] = b'FSSA\x01\x01\0\0'
    struct.pack_into('>II', data, 0x20, 0x80, 0x90)
    struct.pack_into('>II', data, 0x48, 0x100, 0x140)
    data[0x80:0x90] = '隊'.encode('cp932') + b'\0' + bytes(13)
    struct.pack_into('>Iff', data, 0x100, 0, 20.0, 30.0)
    struct.pack_into('>Iff', data, 0x120, 0, 40.0, 50.0)
    data[0x150:0x154] = b'KEEP'
    return bytes(data)


def fixture_table():
    pool = '隊'.encode('cp932') + b'\0' + '行動'.encode('cp932') + b'\0'
    data = bytearray(56)
    data[:4] = b'SB2T'
    data[16:20] = b'DIXT'
    struct.pack_into('>I', data, 24, 8)
    struct.pack_into('>II', data, 32, 0, 3)
    data[40:44] = b'TDXT'
    struct.pack_into('>I', data, 48, len(pool))
    return bytes(data) + pool


class ExpansionHookTests(unittest.TestCase):
    def test_long_english_executes_without_relaxing_source_cap(self):
        english = fw('Sphere ' * 400)
        key = '説明'.encode('cp932')
        entries = [entry(key, english, 'long')]
        out, report = uh.hook(synthetic_elf(), entries, require_srvc=False)
        self.assertGreater(len(english), uh.MAX_EXTENT)
        runner = uh._Runner(out, int(report['stub_va'], 16), report['stub_bytes'])
        pointer, _ = runner.run(key + b'\0')
        _, _, phs, _ = uh._headers(out)
        self.assertEqual(uh._reader(out, phs)(pointer, len(english)+1), english+b'\0')
        self.assertIsNone(uh.extent(fw('A')*2049+b'\0'))
        self.assertTrue(uh.check_english(key, fw('A')*4097))

    def test_auxiliary_payload_readback_and_tamper_rejection(self):
        source = synthetic_elf()
        rows = [entry('隊'.encode('cp932'), fw('Team'), 'team')]
        payloads = [('native', b'Wait %d seconds.\0')]
        out, report = uh.hook(source, rows, require_srvc=False, payloads=payloads)
        va = report['table']['payload_vas']['native']
        _, _, phs, _ = uh._headers(out)
        self.assertEqual(uh._reader(out, phs)(va, 17), payloads[0][1])
        bad = bytearray(out)
        bad[va-0x10000] ^= 1
        stub_off = int(report['stub_va'], 16)-0x10000
        ext_off = int(report['ext_file_offset'], 16)
        geo = dict(stub_off=stub_off, stub_end=stub_off+report['stub_bytes'],
                   ext_end=ext_off+report['ext_bytes'], new_tail=int(report['tail_offset'][1],16),
                   delta=int(report['tail_delta'],16))
        with self.assertRaisesRegex(ValueError, 'payload bytes differ'):
            uh.verify(source, bytes(bad), rows, geo, False, 0, payloads)

    def test_formatter_keeps_specifiers_and_reward_buffer_fits(self):
        mapping = {chr(c): fw(chr(c)).hex() for c in range(32, 127)}
        raw = ui_runtime.encode_format('Part: %s / +%d PP', mapping)
        self.assertEqual(raw, fw('Part: ')+b'%s'+fw(' / +')+b'%d'+fw(' PP'))
        self.assertLessEqual(len(ui_runtime.encode_format('Part: ', mapping))+28*2+1, 81)
        self.assertLessEqual(len(ui_runtime.encode_format('Ace Bonus: ', mapping))+24*2+1, 81)

    def test_tutorial_color_operand_preserved(self):
        mapping = {'A': fw('A').hex()}
        self.assertEqual(eboot_text.encode('1\x02A', mapping), b'1\x02'+fw('A'))
        self.assertEqual(eboot_text.encode('1\x02A', mapping, utf8_source=True), b'1\x01'+fw('A'))
        self.assertEqual(eboot_text.encode('1\nA', dict(mapping, **{'1':fw('1').hex()})), fw('1')+b'\n'+fw('A'))

    def test_native_template_remains_real_utf8_and_does_not_edit_unicode_table(self):
        original = '待機中 %d 秒'.encode('utf-8')
        elf = bytearray(synthetic_elf())
        at = 0x894090-0x10000
        elf[at:at+len(original)+1] = original+b'\0'
        source = dict(id='eboot:0x894090',family='generated',offset=at,
                      raw=original,text=original.decode(),encoding='utf-8')
        with patch.object(ui_catalog,'checked',return_value=({'test':[source]}, {'test':dict(en='Wait %d sec.')})), \
             patch.object(eboot_text,'records',return_value=[]), patch.object(ui_catalog,'sources',return_value=[]):
            planned = ui_runtime.plan(bytes(elf),{})
        out, report = ui_runtime.apply(bytes(elf),planned,{})
        self.assertEqual(out[at:at+12], b'Wait %d sec.')
        self.assertEqual(report['carrier_cells'],0)
        table_at = uh.UTAB_VA-0x10000
        self.assertEqual(out[table_at:table_at+0x20000],elf[table_at:table_at+0x20000])
        elf[at] ^= 1
        with self.assertRaisesRegex(ValueError,'source drift'):
            ui_runtime.apply(bytes(elf),planned,{})


class LayoutRelocationTests(unittest.TestCase):
    def test_description_wrapper_keeps_every_word_and_rejects_overflow(self):
        text = 'Movement +2;\\nMAP attacks are excluded. DLC only.'
        result = ui_description_layout.wrap(text, 20, lambda c:1)
        self.assertEqual(result.split(), text.replace('\\n',' ').split())
        self.assertLessEqual(len(result.splitlines()), 3)
        with self.assertRaisesRegex(ValueError, 'three lines'):
            ui_description_layout.wrap('a b c d', 1, lambda c:1)

    def test_widget_binding_keeps_shared_character_and_other_sections(self):
        source = fixture_fssa()
        edit = dict(widget_offset=0x100, source_sha256=sha256('隊'.encode('cp932')),
                    source_widget_sha256=sha256(source[0x100:0x120]), en='Team')
        mapping = {c:fw(c).hex() for c in 'Team'}
        out, report = ui_layout_text.fssa_patch(source, [edit], mapping)
        grow = report['appended_pool_bytes']
        self.assertEqual(out[0x80:0x90], source[0x80:0x90])
        self.assertEqual(struct.unpack_from('>I', out, 0x120+grow)[0], 0)
        self.assertEqual(out[0x150+grow:0x154+grow], b'KEEP')
        changed = bytearray(out)
        changed[0x150+grow] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside appended text'):
            ui_layout_text.verify_fssa(source, bytes(changed), [edit], mapping)
        edit['source_widget_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
            ui_layout_text.fssa_patch(source, [edit], mapping)

    def test_table_fragment_keeps_unedited_pointer_and_original_pool(self):
        source = fixture_table()
        edit = dict(table_row_id=1, source_sha256=sha256('行動'.encode('cp932')), en=' actions')
        mapping = {c:fw(c).hex() for c in ' actions'}
        out = ui_layout_text.table_patch(source, [edit], mapping)
        self.assertEqual(out[56:len(source)], source[56:])
        self.assertEqual(out[32:36], source[32:36])
        rows = ui_catalog.ui_string_table(out)
        self.assertEqual(rows[1]['raw'], fw(' actions'))
        edit['source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
            ui_layout_text.table_patch(source, [edit], mapping)


if __name__ == '__main__':
    unittest.main()
