"""CMN.CPK battle art: catalog, record relocation, renderers, verification, archive round trip."""
import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools import cmn_art as ca, gtf
from tools.common import ROOT, sha256

SOURCE = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/BTLC/CMN.CPK'
try:
    FONTS = ca.font_path().exists()
except Exception:
    FONTS = False

# Jigoku 0.6.24's nine shipped records, re-located to Tengoku offsets (BE).
SHIPPED_RECORDS = {
    0x3b14: (-104, -88, 149, 88, 1, 0, 252, 176), 0x39f8: (21, -88, 191, 88, 254, 0, 422, 176),
    0x38e8: (31, -92, 184, 84, 424, 0, 575, 176), 0x37d8: (0, -88, 132, 88, 577, 0, 707, 176),
    0x36d0: (28, -88, 205, 88, 709, 0, 884, 176), 0x35c0: (-27, -88, 92, 88, 886, 0, 1003, 176),
    0x34b0: (-64, -88, 56, 88, 1005, 0, 1123, 176), 0x339c: (-108, -88, 109, 88, 1125, 0, 1340, 176),
    0x3288: (-19, -88, 112, 88, 1342, 0, 1471, 176),
}


def catalog(**en):
    data = json.loads(ca.CATALOG.read_text(encoding='utf-8'))
    for key, value in en.items():
        data['labels'][key]['en'] = value
    return data


def synthetic_member():
    """Effect block with the nine original records + a one-texture GTF at GTF_BASE."""
    head = bytearray(ca.GTF_BASE)
    for offset, anchor_offset, anchor, record in ca.PIECES:
        struct.pack_into('>2h', head, anchor_offset, *anchor)
        struct.pack_into(ca.RECORD, head, offset, *record)
    w, h = 64, 16
    g = b'\x02\x02\x00\x00' + struct.pack('>II', w * h * 4, 1)
    g += struct.pack('>III4BIHHHBxII', 0, 0x80, w * h * 4, 0xa5, 1, 2, 0, 0xaae4, w, h, 1, 1, w * 4, 0)
    g += bytes(0x80 - len(g)) + bytes(w * h * 4)
    return bytes(head) + g


class CatalogTests(unittest.TestCase):
    def test_shipped_catalog_is_valid_and_complete(self):
        data = ca.load_catalog()
        self.assertEqual(set(data['labels']), set(ca.LABELS))
        self.assertTrue(all(row['en'] for row in data['labels'].values()))

    def test_catalog_rejections(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'c.json'
            for mutate in (lambda c: c['labels']['counter'].update(jp='反撃'),
                           lambda c: c['labels']['counter'].update(rect=[0, 0, 272, 60]),
                           lambda c: c['labels']['counter'].update(en='Contre‑attaque'),
                           lambda c: c['labels']['counter'].update(en='Two\nlines'),
                           lambda c: c['labels']['maximum_break'].update(en='MAX BREAK'),
                           lambda c: c['labels'].pop('counter')):
                data = catalog()
                mutate(data)
                path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                with self.assertRaises(ValueError):
                    ca.load_catalog(path)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.original = synthetic_member()
        tex = gtf.textures(self.original)[0]
        self.key = tex.key
        self.rgba = np.full((16, 64, 4), 200, np.uint8)
        built = bytearray(gtf.replace(self.original, tex, self.rgba))
        self.records = {o: (0, -88, 10, 88, 1, 0, 9, 176) for o, *_ in ca.PIECES}
        for o, r in self.records.items():
            struct.pack_into(ca.RECORD, built, o, *r)
        self.built = bytes(built)

    def verify(self, built, records=None):
        return ca.verify_member(self.original, built, {self.key: self.rgba}, records or self.records)

    def test_accepts_intended_member(self):
        self.assertTrue(self.verify(self.built))

    def test_rejects_wrong_record_anchor_script_and_pixels(self):
        bad = bytearray(self.built)
        struct.pack_into(ca.RECORD, bad, ca.PIECES[0][0], 1, 2, 3, 4, 5, 6, 7, 8)
        with self.assertRaises(ValueError):
            self.verify(bytes(bad))
        bad = bytearray(self.built)
        bad[ca.PIECES[2][1]] ^= 1                       # anchor
        with self.assertRaises(ValueError):
            self.verify(bytes(bad))
        bad = bytearray(self.built)
        bad[0x100] ^= 1                                 # unrelated script byte
        with self.assertRaises(ValueError):
            self.verify(bytes(bad))
        bad = bytearray(self.built)
        bad[-1] ^= 1                                    # pixel
        with self.assertRaises(ValueError):
            self.verify(bytes(bad))
        with self.assertRaises(ValueError):             # record outside the allow-list
            self.verify(self.built, {**self.records, 0x100: (0,) * 8})
        with self.assertRaises(ValueError):
            ca.verify_member(self.original, self.original, {}, {})

    def test_strip_quads_finds_exactly_the_pieces(self):
        self.assertEqual([p for p, _ in ca.strip_quads(self.original)], sorted(o for o, *_ in ca.PIECES))


@unittest.skipUnless(SOURCE.exists() and FONTS, 'pristine CMN.CPK or PS3 fonts missing')
class RealPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ca.source_member()
        cls.art = ca.plan(source=cls.source)
        cls.built = cls.art['members'][ca.MEMBER]

    def test_source_has_native_duplicate_glyph(self):
        uvs = [ca.read_record(self.source, o)[4:] for o, *_ in ca.PIECES]
        self.assertEqual(uvs[0], uvs[3])
        self.assertEqual(len(set(uvs)), 8)

    def test_records_are_jigoku_shipped_values_relocated(self):
        self.assertEqual({o: ca.read_record(self.built, o) for o, *_ in ca.PIECES}, SHIPPED_RECORDS)
        self.assertEqual(self.art['records'][ca.MEMBER], SHIPPED_RECORDS)

    def test_whole_cells_contiguous_and_unclipped(self):
        atlas = gtf.decode(self.built, ca.textures(self.built)[16])
        expected_x = ca.SCREEN_X0
        uvs = set()
        for offset, anchor_offset, _a, _r in ca.PIECES:
            ax, ay = struct.unpack_from('>2h', self.built, anchor_offset)
            x0, y0, x1, y1, u0, v0, u1, v1 = ca.read_record(self.built, offset)
            self.assertEqual(ax + x0, expected_x)
            self.assertEqual((ay + y0, ay + y1), (-88, 88))
            self.assertEqual((u0, u1), (ax + x0 - ca.SCREEN_X0 + 1, ax + x1 - ca.SCREEN_X0 - 1))
            alpha = atlas[v0:v1, u0:u1, 3]
            cols, rows = np.nonzero(alpha.any(0))[0], np.nonzero(alpha.any(1))[0]
            self.assertGreater(cols[0], 0)
            self.assertLess(cols[-1], u1 - u0 - 1)
            self.assertGreater(rows[0], 0)
            self.assertLess(rows[-1], v1 - v0 - 1)
            uvs.add((u0, u1))
            expected_x = ax + x1
        self.assertEqual(expected_x, -ca.SCREEN_X0)
        self.assertEqual(len(uvs), 9)
        self.assertEqual([p for p, _ in ca.strip_quads(self.built)], sorted(SHIPPED_RECORDS))

    def test_only_records_and_three_textures_change(self):
        ca.verify_member(self.source, self.built, self.art['intended'][ca.MEMBER], self.art['records'][ca.MEMBER])
        diff = np.nonzero(np.frombuffer(self.source, np.uint8) != np.frombuffer(self.built, np.uint8))[0]
        tex = ca.textures(self.source)
        allowed = [(o, o + 16) for o in SHIPPED_RECORDS] + \
                  [(tex[i]['offset'], tex[i]['offset'] + tex[i]['size']) for i in (10, 11, 16)]
        self.assertTrue(all(any(a <= d < b for a, b in allowed) for d in diff))
        for i in (10, 11, 16):
            t = tex[i]
            self.assertNotEqual(self.source[t['offset']:t['offset'] + t['size']],
                                self.built[t['offset']:t['offset'] + t['size']])

    def test_renderers_reproduce_jigoku_shipped_pixels(self):
        data, _i, records, _r = ca.build_member(self.source, catalog(support_defense='Support Defend', attack_again='Attack Again'))
        tex = ca.textures(data)
        for index, want in ca.JIGOKU_SHIPPED_PIXELS.items():
            t = tex[index]
            self.assertEqual(sha256(data[t['offset']:t['offset'] + t['size']]), want, index)
        self.assertEqual(records, SHIPPED_RECORDS)

    def test_support_defense_differs_from_jigoku_only_in_its_row(self):
        jigoku, *_ = ca.build_member(self.source, catalog(support_defense='Support Defend'))
        t = ca.textures(self.built)[11]
        a, b = gtf.decode(jigoku, t), gtf.decode(self.built, t)
        self.assertTrue(np.array_equal(a[:192], b[:192]))
        self.assertFalse(np.array_equal(a[192:], b[192:]))
        self.assertFalse(self.art['report']['review'])

    def test_pending_labels_leave_art_untouched(self):
        art = ca.plan(catalog=catalog(counter=None, support_defense=None), source=self.source)
        t = ca.textures(self.source)[11]
        built = gtf.decode(art['members'][ca.MEMBER], t)
        self.assertTrue(np.array_equal(built[:64], gtf.decode(self.source, t)[:64]))
        self.assertEqual(sorted(art['report']['pending']), ['counter', 'support_defense'])
        none = ca.plan(catalog=catalog(**{k: None for k in ca.LABELS}), source=self.source)
        self.assertEqual(none['members'], {})
        only_combo = ca.plan(catalog=catalog(**{k: None for k in ca.LABELS if k != 'combo_attack'}),
                             source=self.source)
        self.assertEqual(only_combo['records'][ca.MEMBER], {})
        self.assertEqual(only_combo['members'][ca.MEMBER][:ca.GTF_BASE], self.source[:ca.GTF_BASE])

    def test_source_drift_fails_closed(self):
        bad = bytearray(self.source)
        bad[ca.PIECES[0][0]] ^= 1
        with self.assertRaises(ValueError):
            ca.check_source(bytes(bad))
        with self.assertRaises(ValueError):
            ca.build_member(bytes(bad), catalog())

    def test_archive_round_trip(self):
        from tools.cpkpatch import build
        from tools.pipeline import config, verified_source
        from tools.verify_archives import compare
        src = verified_source(config(ROOT / 'config/tengoku.json'), ca.CMN)
        for compress in (False, True):
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / 'CMN.CPK'
                build(src, out, self.art['members'], compress=compress, workers=1)
                self.assertEqual(ca.verify_archive(out, self.art), 1)
                report = compare(src, out, self.art['members'])
                self.assertEqual(report['replaced'], 1)
                self.assertEqual(report['replaced_compressed'], int(compress))
                self.assertLess(out.stat().st_size, 4_200_000 if not compress else 1_000_000)


@unittest.skipUnless(SOURCE.exists() and FONTS and ca.JIGOKU_ORIGINAL.exists() and ca.JIGOKU_SHIPPED.exists(),
                     'Jigoku CMN archives missing')
class JigokuEvidenceTests(unittest.TestCase):
    def test_relocation_evidence(self):
        r = ca.compare_jigoku(ca.source_member())
        self.assertTrue(r['records_equal'])
        self.assertEqual(r['block_words_not_byte_order_equivalent'], [])
        self.assertTrue(r['jigoku_shipped_script_changes_only_in_records'])
        self.assertEqual(len(r['tengoku_strip_quads']), 9)
        self.assertEqual(len(r['jigoku_strip_quads']), 9)
        self.assertTrue(all(r['renderer_reproduces_jigoku_0.6.24'].values()))
        for index in (10, 11, 16):
            self.assertEqual(r['pixel_identical_to_jigoku_original'][index], index)


if __name__ == '__main__':
    unittest.main()
