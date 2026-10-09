"""OP.CPK series captions: renderer, encoding fidelity, catalog, plan() and archive round trip."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools import gtf, op_art as op
from tools.common import ROOT

SOURCE = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/BTLC/OP.CPK'
try:
    FONTS = (op.font_dir() / op.STYLE['face']).exists()
except Exception:
    FONTS = False


def strip_member(count=10, seed=0):
    """A synthetic OP member: 0x60-byte container prefix, one GTF with
    `count` 1280x64 linear strips, then trailing script bytes."""
    rng = np.random.default_rng(seed)
    size = op.STRIP_W * op.STRIP_H * 4
    head_len = 12 + 36 * count
    first = (head_len + 0x7f) // 0x80 * 0x80
    head = b'\x02\x02\x00\x00' + struct.pack('>II', size * count, count)
    for i in range(count):
        head += struct.pack('>III4BIHHHBxII', i, first + i * size, size, 0xa5, 1, 2, 0, 0xaae4,
                            op.STRIP_W, op.STRIP_H, 1, 1, op.STRIP_W * 4, 0)
    gtf_blob = head + bytes(first - len(head)) + bytes(size * count)
    prefix = struct.pack('<III', 12, 0x10, 0x50) + bytes(0x60 - 12)
    blob = prefix + gtf_blob + b'SCRIPT' * 50
    tex = gtf.textures(blob)
    for t in tex:
        grey = np.zeros((64, 1280), np.uint8)
        grey[15:50, 500:700] = rng.choice(np.arange(0, 256, 17), (35, 200))
        rgba = np.dstack([grey, grey, grey, np.where(grey > 0, 255, 0).astype(np.uint8)])
        blob = gtf.replace(blob, t, rgba)
    return blob


class LayoutTests(unittest.TestCase):
    def test_strips_accepts_layout_and_rejects_wrong_count(self):
        blob = strip_member(10)
        self.assertEqual(len(op.strips(blob, 0)), 10)
        with self.assertRaises(ValueError):
            op.strips(blob, 2)                      # member 2 has 11 strips

    def test_identified_names_are_table_series(self):
        names = op.series_names()
        self.assertEqual(len(op.IDENTIFIED), sum(op.LAYOUT.values()))
        self.assertEqual(len(set(op.IDENTIFIED.values())), 31)
        for jp in op.IDENTIFIED.values():
            self.assertIn(jp, names)


@unittest.skipUnless(FONTS, 'PS3 system fonts not available')
class RendererTests(unittest.TestCase):
    def test_encoding_matches_original_strips(self):
        rgba, info = op.caption_pixels('Mobile Suit Gundam Wing: Endless Waltz')
        grey, alpha = rgba[..., 0], rgba[..., 3]
        self.assertTrue(np.array_equal(grey, rgba[..., 1]) and np.array_equal(grey, rgba[..., 2]))
        self.assertTrue(set(np.unique(grey)) <= set(range(0, 256, 17)))
        self.assertFalse(grey[alpha == 0].any())
        # the halo surrounds the fill by about 5 px on each side, like the originals
        fx, fy, fw, fh = info['fill_box']
        ax, ay, aw, ah = info['alpha_box']
        self.assertTrue(4 <= fx - ax <= 6 and 4 <= (ax + aw) - (fx + fw) <= 6)
        self.assertTrue(4 <= fy - ay <= 6)
        self.assertLess(abs(fx + (fw - 1) / 2.0 - op.STYLE['center_x']), 1.0)

    def test_cap_height_and_baseline_match_the_games_latin(self):
        rgba, _ = op.caption_pixels('EEEE')
        rows = np.nonzero((rgba[..., 0] > 128).any(1))[0]
        self.assertEqual(rows.max(), op.STYLE['baseline'] - 1)       # bottom row 47
        self.assertAlmostEqual(rows.max() - rows.min() + 1, op.STYLE['cap_height'], delta=1)

    def test_long_names_condense_then_shrink(self):
        _, info = op.caption_pixels('Mobile Suit Gundam 00 The Movie: A Wakening of The Trailblazer')
        self.assertLess(info['squeeze'], 1.0)
        self.assertLessEqual(info['fill_box'][2], op.STYLE['max_width'])
        _, huge = op.caption_pixels('A Very Long Series Name ' * 4)
        self.assertAlmostEqual(huge['squeeze'], op.STYLE['min_squeeze'], delta=0.02)
        self.assertLess(huge['shrink'], 1.0)
        self.assertTrue(huge['needs_review'])

    def test_caption_member_only_changes_pixels(self):
        blob = strip_member(10)
        built, intended, infos = op.caption_member(blob, 0, {0: 'Macross 7', 9: 'The Big O'})
        self.assertEqual(sorted(infos), [0, 9])
        self.assertEqual(len(built), len(blob))
        self.assertEqual(built[:0x60], blob[:0x60])
        self.assertEqual(built[-300:], blob[-300:])
        self.assertTrue(op.verify_member(blob, built, intended))
        tex = gtf.textures(blob)
        bad = bytearray(built)
        bad[tex[3]['offset'] + 9] ^= 1                      # an untouched strip
        with self.assertRaises(ValueError):
            op.verify_member(blob, bytes(bad), intended)
        bad = bytearray(built)
        bad[-1] ^= 1                                        # script bytes
        with self.assertRaises(ValueError):
            op.verify_member(blob, bytes(bad), intended)


class CatalogTests(unittest.TestCase):
    def test_catalog_english_is_the_glossary_series_name(self):
        catalog = op.load_catalog()
        names = op.series_names()
        self.assertEqual(len(catalog['captions']), 31)
        for k, row in catalog['captions'].items():
            self.assertEqual(op.IDENTIFIED[(row['member'], row['texture'])], row['jp'], k)
            self.assertEqual(row['en'], names[row['jp']], k)
            self.assertGreater(row['match_score'], row['runner_up_score'], k)

    def test_catalog_validation(self):
        good = op.load_catalog()
        path = ROOT / 'work/tengoku/cache/test_op_catalog.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            for mutate in (lambda d: d['captions'].pop('m0_t0'),
                           lambda d: d['captions']['m0_t0'].update(en='Two\nlines'),
                           lambda d: d['captions']['m0_t0'].update(en='Café'),
                           lambda d: d.update(schema=2)):
                bad = json.loads(json.dumps(good))
                mutate(bad)
                path.write_text(json.dumps(bad), encoding='utf-8')
                with self.assertRaises(ValueError):
                    op.load_catalog(path)
        finally:
            if path.exists():
                path.unlink()


@unittest.skipUnless(SOURCE.exists(), 'pristine OP.CPK missing')
class RealSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.path = op.source_members(op._settings())

    def test_halo_model_reproduces_original_alpha(self):
        errors = []
        for mid, blob in self.sources.items():
            for t in op.strips(blob, mid):
                orig = gtf.decode(blob, t)
                model = op.encode(orig[..., 0] / 255.0)
                region = (orig[..., 3] > 0) | (model[..., 3] > 0)
                errors.append(np.abs(model[..., 3].astype(int) - orig[..., 3].astype(int))[region].mean())
                self.assertTrue(np.array_equal(model[..., 0][orig[..., 3] == 255], orig[..., 0][orig[..., 3] == 255]))
        self.assertLess(np.mean(errors), 8.0)          # about 6/255 mean on the halo region

    @unittest.skipUnless(FONTS, 'PS3 system fonts not available')
    def test_plan_and_archive_round_trip(self):
        from tools.cpkpatch import build
        from tools.verify_archives import compare
        art = op.plan()
        self.assertEqual(sorted(art['members']), [0, 1, 2])
        self.assertEqual(len(art['report']['captions']), 31)
        self.assertEqual(art['report']['pending'], [])
        with tempfile.TemporaryDirectory() as tmp:
            for compress in (False, True):
                out = Path(tmp) / ('OP_%s.CPK' % compress)
                build(art['source_path'], out, art['members'], compress=compress, workers=1)
                result = compare(art['source_path'], out, art['members'])
                self.assertEqual(op.verify_archive(out, art), 3)
                self.assertEqual(result['replaced_compressed'] > 0, compress)

    @unittest.skipUnless(FONTS, 'PS3 system fonts not available')
    def test_pending_strips_stay_untouched(self):
        catalog = op.load_catalog()
        for k, row in catalog['captions'].items():
            if row['member'] != 1 or k != 'm1_t6':
                row['en'] = None
        art = op.plan(catalog=catalog)
        self.assertEqual(sorted(art['members']), [1])
        self.assertEqual(len(art['report']['pending']), 30)
        tex = op.strips(art['members'][1], 1)
        for t in tex:
            same = art['members'][1][t['offset']:t['offset'] + t['size']] == \
                self.sources[1][t['offset']:t['offset'] + t['size']]
            self.assertEqual(same, t['index'] != 6)


if __name__ == '__main__':
    unittest.main()
