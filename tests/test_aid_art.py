"""AIDDATAPACK member 1 art: renderer, catalog, member verification, plan()."""
import json
import struct
import unittest

import numpy as np

from tools import aid_art as aa, gtf
from tools.common import ROOT

PACK = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/AIDDATA/AIDDATAPACK.CPK'
try:
    FONTS = (aa.font_dir() / aa.FACE).exists()
except Exception:
    FONTS = False


def atlas_blob(seed=0):
    """A synthetic member 1: one GTF, four swizzled 512x512 textures."""
    rng = np.random.default_rng(seed)
    head = b'\x02\x02\x00\x00' + struct.pack('>II', 4 * 0x100000, 4)
    for i in range(4):
        head += struct.pack('>III4BIHHHBxII', i, 0x100 + i * 0x100000, 0x100000, 0x85, 1, 2, 0,
                            0xaae4, 512, 512, 1, 1, 0, 0)
    blob = head + bytes(0x100 - len(head)) + bytes(4 * 0x100000)
    for t in gtf.textures(blob):
        rgba = np.zeros((512, 512, 4), np.uint8)
        rgba[100:140, 50:300] = rng.integers(0, 255, (40, 250, 4), dtype=np.uint8)
        blob = gtf.replace(blob, t, rgba)
    return blob


def paint(blob, ti, rect, value):
    t = gtf.textures(blob)[ti]
    rgba = gtf.decode(blob, t)
    x0, y0, x1, y1 = rect
    rgba[y0:y1, x0:x1] = value
    return gtf.replace(blob, t, rgba), rgba


class VerifyMemberTests(unittest.TestCase):
    def setUp(self):
        self.blob = atlas_blob()
        self.tex = gtf.textures(self.blob)

    def test_accepts_change_inside_rect(self):
        built, rgba = paint(self.blob, 2, (10, 10, 60, 40), 200)
        key = self.tex[2].key
        self.assertTrue(aa.verify_member(self.blob, built, {key: rgba}, {key: [(10, 10, 60, 40)]}))

    def test_rejects_change_outside_rect(self):
        built, rgba = paint(self.blob, 2, (10, 10, 60, 40), 200)
        key = self.tex[2].key
        with self.assertRaises(ValueError):
            aa.verify_member(self.blob, built, {key: rgba}, {key: [(10, 10, 60, 39)]})

    def test_rejects_untouched_texture_and_header_changes(self):
        built, rgba = paint(self.blob, 2, (10, 10, 60, 40), 200)
        key = self.tex[2].key
        other, _ = paint(built, 0, (0, 0, 1, 1), 7)
        with self.assertRaises(ValueError):
            aa.verify_member(self.blob, other, {key: rgba}, {key: [(10, 10, 60, 40)]})
        broken = bytearray(built)
        broken[0x20] ^= 1
        with self.assertRaises(ValueError):
            aa.verify_member(self.blob, bytes(broken), {key: rgba}, {key: [(10, 10, 60, 40)]})
        with self.assertRaises(ValueError):
            aa.verify_member(self.blob, self.blob, {}, {})

    def test_rejects_wrong_intended_pixels(self):
        built, rgba = paint(self.blob, 2, (10, 10, 60, 40), 200)
        key = self.tex[2].key
        wrong = rgba.copy()
        wrong[15, 15] = 1
        with self.assertRaises(ValueError):
            aa.verify_member(self.blob, built, {key: wrong}, {key: [(10, 10, 60, 40)]})


class CatalogTests(unittest.TestCase):
    def catalog(self):
        return json.loads(aa.CATALOG.read_text(encoding='utf-8'))

    def test_catalog_file_is_valid_and_complete(self):
        data = aa.load_catalog()
        cells = data['cells']
        self.assertEqual({c['source'] for c in cells.values()}, set(aa.SOURCES))
        self.assertEqual(sum(1 for c in cells.values() if c['source'] == 'jigoku-0.6.24'), 26)
        self.assertEqual(sum(1 for c in cells.values() if c['source'] == 'new'), 35)
        for cid, cell in cells.items():
            if cell['source'] == 'new':
                self.assertTrue(cell['en'].isascii(), cid)
                self.assertIn(cell['style'], aa.STYLES)
            self.assertEqual(len(cell['source_sha256']), 64)
        # the project's Spirit abbreviations, not Jigoku's
        self.assertEqual(cells['t0.spirit_wall']['en'], 'Wa')
        self.assertEqual(cells['t2.accuracy']['en'], 'Acc.')
        self.assertEqual(cells['t2.map']['en'], 'MAP')
        # nothing in the catalog paints texture 1 (frames only)
        self.assertFalse([c for c in cells.values() if c['texture'] == 1])

    def test_rejects_overlap_bad_source_and_non_ascii(self):
        import tempfile
        from pathlib import Path
        base = self.catalog()
        cases = []
        bad = json.loads(json.dumps(base))
        bad['cells']['t2.morale']['rect'] = bad['cells']['t2.stats']['rect']
        cases.append(bad)
        bad = json.loads(json.dumps(base))
        bad['cells']['t2.morale']['source'] = 'maybe'
        cases.append(bad)
        bad = json.loads(json.dumps(base))
        bad['cells']['t2.morale']['en'] = '気力'
        cases.append(bad)
        bad = json.loads(json.dumps(base))
        bad['cells']['t0.parry']['rect'] = [0, 48, 90, 72]     # not Jigoku's rectangle
        cases.append(bad)
        with tempfile.TemporaryDirectory() as tmp:
            for i, data in enumerate(cases):
                path = Path(tmp) / ('c%d.json' % i)
                path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                with self.assertRaises(ValueError):
                    aa.load_catalog(path)

    def test_jigoku_asset_hashes(self):
        cells, meta = aa.jigoku_cells()
        self.assertEqual(len(cells), len(aa.JIGOKU_CELLS))
        self.assertEqual(meta['tengoku_member_sha256'], aa.M1_SHA256)


@unittest.skipUnless(FONTS, 'PS3 system fonts not available')
class RendererTests(unittest.TestCase):
    def test_word_fits_cell_and_is_centred(self):
        rgba, info = aa.word_pixels('Morale', (56, 32), (2, 3, 52, 29), 'white')
        self.assertEqual(rgba.shape, (32, 56, 4))
        self.assertFalse(rgba[rgba[..., 3] == 0].any())
        ys, xs = np.nonzero(rgba[..., 3])
        self.assertLessEqual(abs((xs.min() + xs.max() + 1) / 2.0 - 27), 1.5)
        self.assertGreaterEqual(info['squeeze'], aa.MIN_SQUEEZE)
        # white fill and black outline both present
        opaque = rgba[rgba[..., 3] == 255][:, 0]
        self.assertTrue((opaque > 240).any() and (opaque < 16).any())

    def test_long_text_condenses_then_shrinks(self):
        _, short = aa.word_pixels('Up', (56, 32), (2, 3, 52, 29), 'white')
        _, long_ = aa.word_pixels('Disabled Forever', (56, 32), (2, 3, 52, 29), 'white')
        self.assertEqual(short['squeeze'], 1.0)
        self.assertLess(long_['font_px'], short['font_px'])

    def test_inverse_style_has_black_fill(self):
        rgba, _ = aa.word_pixels('Sub Order', (208, 41), (2, 2, 206, 40), 'inverse')
        centre = rgba[rgba[..., 3] == 255][:, 0]
        self.assertTrue((centre < 16).sum() > (centre > 240).sum() * 0.3)

    def test_icon_keeps_plate_outside_letters(self):
        plate = np.zeros((46, 48, 4), np.uint8)
        plate[15:41, 3:35] = (88, 88, 88, 255)
        rgba, _ = aa.icon_pixels('Wa', plate, (48, 46), (23.0, 22.0))
        self.assertEqual(rgba.shape, (46, 48, 4))
        self.assertTrue((rgba[40, 4] == plate[40, 4]).all())
        self.assertTrue((rgba[..., 0] > 240).any())


@unittest.skipUnless(PACK.exists() and FONTS, 'pristine Tengoku source not extracted')
class RealArchiveTests(unittest.TestCase):
    def test_plan_changes_only_cell_rectangles(self):
        art = aa.plan()
        src, built = art['sources'][1], art['members'][1]
        self.assertEqual(len(src), len(built))
        self.assertTrue(aa.verify_member(src, built, art['intended'][1], art['rects'][1]))
        self.assertEqual(art['report']['textures_changed'], [0, 2, 3])
        tex = gtf.textures(src)
        t1 = tex[1]
        self.assertEqual(src[t1['offset']:t1['offset'] + t1['size']], built[t1['offset']:t1['offset'] + t1['size']])
        # Jigoku cells carry exactly the shipped pixels
        cells, _ = aa.jigoku_cells()
        catalog = aa.load_catalog()
        for cid, (pix, row) in cells.items():
            if catalog['cells'][cid]['source'] != 'jigoku-0.6.24':
                continue
            after = gtf.decode(built, tex[row['texture']])
            self.assertTrue(np.array_equal(aa.rect_pixels(after, tuple(row['rect'])), pix), cid)

    def test_plan_is_deterministic(self):
        self.assertEqual(aa.plan()['members'][1], aa.plan()['members'][1])


if __name__ == '__main__':
    unittest.main()
