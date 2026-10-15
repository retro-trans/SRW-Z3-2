"""Regression: split war-front messages must translate after native copying."""
import json
import unittest
from tools.common import ROOT
from tools import review35_news as N, review32_content as C, ui_hook as H
from tools import eboot_text as E, vwf, link_layout as K


class NewsRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = H.PREPARED.read_bytes()
        folder = ROOT / 'work/output/builds/0.5.34'
        cls.mapping = json.loads((folder/'build.json').read_text('utf8'))['mapping']
        entries, _ = E.hook_entries(cls.original, cls.mapping,
                                   lambda raw: H.utf8_key(raw, cls.original))
        entries += C.hook_entries(cls.original, cls.mapping) + N.hook_entries(cls.original, cls.mapping)
        entries = list({r['key']: r for r in entries}.values())
        from tools.ui_build import cell_xy
        from tools.ui_vwf_build import raster
        widths = {}
        for token, code in cls.mapping.items():
            x, y = cell_xy(code); width = raster(token)[1]
            if width != 32:
                widths[y//32*128+x//32] = width
        elf, info = vwf.patch(cls.original, widths)
        elf, cls.hook = H.hook(elf, entries, require_srvc=False, payloads=[(K.STATE, K.PAYLOAD)])
        cls.final, cls.layout = K.apply(elf, cls.original,
            cls.hook['table']['payload_vas'][K.STATE], info['table_va'], cls.mapping, [])

    def test_old_whole_message_binding_misses_actual_native_rows(self):
        data = N.plan(); missed = 0
        folder = ROOT/'work/output/builds/0.5.34'
        old = (folder/'EBOOT.BIN').read_bytes()
        hook = json.loads((folder/'build.json').read_text('utf8'))['executable']['ui_hook']
        runner = H._Runner(old, int(hook['stub_va'], 16), hook['stub_bytes'])
        for row in data['rows']:
            if len(row['english']) == 1:
                continue
            lines, _ = N.native_lines(old, '\n'.join(row['source_lines']).encode('utf8'))
            for line in lines:
                key = H.utf8_key(line, self.original)
                pointer, _ = runner.run(key+b'\0')
                if pointer & 0xffffffff == 0x50000000:
                    missed += 1
        self.assertEqual(missed, 13)

    def test_complete_native_news_category_draws_translated_paragraphs(self):
        proof = N.verify(self.final, self.mapping, self.hook, self.layout)
        self.assertEqual(proof['messages'], 22)
        self.assertEqual(proof['separate_draw_keys'], 13)
        self.assertEqual(len(proof['origin_cases']), 26)
        world = next(r for r in proof['native_copy_cases'] if r['va'] == '0x8a1280')
        self.assertEqual(world['paragraphs'], 3)
        self.assertIn('18 Terminal Bases Captured', world['english'])
        self.assertIn('3 Central Bases Captured', world['english'])


if __name__ == '__main__':
    unittest.main()
