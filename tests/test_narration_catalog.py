import json
import struct
import unittest
from unittest.mock import patch
from tools import narration_catalog as N
from tools.common import ROOT, sha256


class NarrationCatalogTests(unittest.TestCase):
    def test_records_use_header_capacity_and_keep_blank_timing_rows(self):
        capacity = 12
        stride = capacity + 30
        blob = bytearray(20 + 3 * stride)
        struct.pack_into('>HBB', blob, 0, 3, capacity, 1)
        blob[4:8] = N.SIGNATURE
        for index, text in ((0, '開始'), (2, '終わり')):
            raw = text.encode('cp932')
            at = 20 + index * stride
            blob[at:at+len(raw)] = raw
            blob[at+capacity:at+stride] = b'X' * 30
        before = bytes(blob)
        rows = N.records(blob, 80)
        self.assertEqual([r['offset'] for r in rows], [20, 104])
        self.assertEqual([r['page'] for r in rows], [1, 2])
        self.assertEqual(bytes(blob), before)
        with self.assertRaises(ValueError): N.records(blob[:-1], 80)
        blob[20:32] = b'X' * 12
        with self.assertRaisesRegex(ValueError, 'Unterminated'): N.records(blob, 80)

    def test_source_manifest_and_every_caption_have_reviewed_translation(self):
        from tools.cpk import CPK
        from tools.pipeline import config, verified_source
        from tools.aid_art import ARCHIVE
        from tools.ui_catalog import translations
        from tools.opening_narration import profile
        from tools import opening_narration, briefing_narration, fleet_narration, endless_narration
        with CPK(verified_source(config(ROOT/'config/tengoku.json'), ARCHIVE)) as arc:
            rows = N.sources(arc)
            by_id = {e['id']:e for e in arc.files}
            for old, mid in ((opening_narration,19), (briefing_narration,26),
                             (fleet_narration,27), (endless_narration,27)):
                expected = old.sources(arc.read(by_id[mid]))
                found = {r['id']:r for r in rows}
                for row in expected:
                    self.assertEqual(found[row['id']]['raw'], row['raw'])
        self.assertEqual(len(rows), 197)
        self.assertEqual({r['member'] for r in rows}, set(range(19,54))-{25})
        self.assertEqual(len({r['text'] for r in rows}), 189)
        english = translations()
        for row in rows:
            translated = english[sha256(row['text'].encode('utf-8'))[:20]]
            self.assertTrue(translated['reviewed'])
            self.assertTrue(profile(translated['en'])[0])
        for ident in ('aid:20:19a','aid:20:4f4','aid:21:14','aid:22:14'):
            self.assertIn(ident, {r['id'] for r in rows})
        manifest = json.loads(N.MANIFEST.read_text(encoding='utf-8'))
        manifest['captions'] -= 1
        with patch.object(N, 'MANIFEST') as path:
            path.read_text.return_value = json.dumps(manifest)
            with CPK(verified_source(config(ROOT/'config/tengoku.json'), ARCHIVE)) as arc:
                with self.assertRaisesRegex(ValueError, 'inventory differs'): N.sources(arc)


if __name__ == '__main__': unittest.main()
