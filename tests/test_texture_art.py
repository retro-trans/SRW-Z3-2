"""Title-card renderer, badge renderer, member verification and plan()."""
import struct
import unittest

import numpy as np

from tools import gtf, texture_art as ta
from tools.common import ROOT

PACK = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/TABATA/TPACKPS3.CPK'
try:
    FONTS = (ta.font_dir() / ta.TITLE_STYLE['face']).exists()
except Exception:
    FONTS = False


def card_blob(seed=0):
    """A synthetic 1536x256 linear title card with Japanese-like encoding."""
    rng = np.random.default_rng(seed)
    grey = np.zeros((256, 1536), np.uint8)
    grey[20:100, 400:1100] = rng.choice(ta.CRISP_LEVELS, (80, 700))
    rgba = np.dstack([grey, grey, grey, np.where(grey > 0, 255, 0).astype(np.uint8)])
    head = b'\x02\x02\x00\x00' + struct.pack('>II', 1536 * 256 * 4, 1)
    head += struct.pack('>III4BIHHHBxII', 0, 0x80, 1536 * 256 * 4, 0xa5, 1, 2, 0, 0xaae4,
                        1536, 256, 1, 1, 1536 * 4, 0)
    blob = head + bytes(0x80 - len(head)) + bytes(1536 * 256 * 4)
    return gtf.replace(blob, gtf.textures(blob)[0], rgba)


@unittest.skipUnless(FONTS, 'PS3 system fonts not available')
class TitleRendererTests(unittest.TestCase):
    def test_encoding_matches_original_cards(self):
        rgba, info = ta.title_pixels('A Hope Called Taboo')
        grey = rgba[..., 0]
        self.assertTrue(np.array_equal(rgba[..., 0], rgba[..., 1]))
        self.assertTrue(np.array_equal(rgba[..., 0], rgba[..., 2]))
        self.assertTrue(np.array_equal(rgba[..., 3] == 255, grey > 0))
        self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
        self.assertTrue(set(np.unique(grey[:128])) <= set(ta.CRISP_LEVELS))
        self.assertTrue(set(np.unique(grey[128:])) <= set(ta.GLOW_LEVELS))
        # glow is a halo around the crisp ink: larger, and it covers it
        crisp, glow = grey[:128] > 0, grey[128:] > 0
        self.assertTrue((glow | ~crisp).all())
        self.assertGreater(glow.sum(), 1.5 * crisp.sum())
        x0, y0, w, h = info['ink_box']
        self.assertTrue(7 <= x0 and x0 + w <= 1529 and 4 <= y0 and y0 + h <= 124)
        self.assertLess(abs((x0 + (w - 1) / 2.0) - 767.5), 1.0)

    def test_long_titles_condense_then_shrink(self):
        _, short = ta.title_pixels('Zeal')
        _, long_ = ta.title_pixels('Trespassing with Good Intentions, Again and Again')
        self.assertEqual((short['squeeze'], short['shrink']), (1.0, 1.0))
        self.assertEqual(long_['squeeze'], ta.TITLE_STYLE['min_squeeze'])
        self.assertLess(long_['shrink'], 1.0)
        self.assertLessEqual(long_['ink_box'][2], ta.TITLE_STYLE['max_width'])

    def test_upper_case_calibration_matches_card_88(self):
        # Card 88's own lettering: cap height 91, ink 1521 px wide (x 7..1527).
        _, info = ta.title_pixels('BEYOND THE DIMENSION', {'case': 'upper'})
        self.assertAlmostEqual(info['squeeze'], 0.917, delta=0.01)

    def test_title_member_only_changes_pixels(self):
        blob = card_blob()
        built, intended, _ = ta.title_member(blob, 'Fly into Space')
        self.assertEqual(len(built), len(blob))
        self.assertEqual(built[:0x80], blob[:0x80])
        self.assertTrue(ta.verify_member(blob, built, intended))

    def test_badge_label_keeps_rest_of_texture(self):
        source = np.zeros((80, 80, 4), np.uint8)
        source[70:, :, :] = 9
        out = ta.badge_pixels(5, 'Multi\nAction', source)
        bx, by, bw, bh = ta.BADGE_STYLES[5]['box']
        self.assertTrue((out[by + bh:] == source[by + bh:]).all())
        self.assertGreater(out[by:by + bh, bx:bx + bw, 3].sum(), 0)
        self.assertFalse((out[out[..., 3] == 0][:, :3]).any())


class VerificationTests(unittest.TestCase):
    def test_verify_member_catches_wrong_pixels_and_headers(self):
        blob = card_blob(1)
        tex = gtf.textures(blob)[0]
        target = np.zeros((256, 1536, 4), np.uint8)
        built = gtf.replace(blob, tex, target)
        self.assertTrue(ta.verify_member(blob, built, {tex.key: target}))
        wrong = target.copy()
        wrong[5, 5] = 1
        with self.assertRaises(ValueError):
            ta.verify_member(blob, built, {tex.key: wrong})
        with self.assertRaises(ValueError):
            ta.verify_member(blob, built[:40] + b'\x01' + built[41:], {tex.key: target})
        with self.assertRaises(ValueError):
            ta.verify_member(blob, blob, {})

    def test_catalog_validation(self):
        good = {'schema': 1, 'cards': {'6': {'jp': 'x', 'en': None}}}
        path = ROOT / 'work/tengoku/cache/test_catalog.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        try:
            for bad in ({'schema': 1, 'cards': {'88': {'jp': 'x', 'en': None}}},
                        {'schema': 1, 'cards': {'6': {'jp': 'x', 'en': 'Two\nlines'}}},
                        {'schema': 1, 'cards': {'6': {'jp': 'x', 'en': 'café'}}}):
                path.write_text(json.dumps(bad), encoding='utf-8')
                with self.assertRaises(ValueError):
                    ta.load_catalog(path)
            path.write_text(json.dumps(good), encoding='utf-8')
            self.assertEqual(ta.load_catalog(path)['cards']['6']['en'], None)
        finally:
            path.unlink()

    def test_plan_refuses_unexpected_font_members(self):
        with self.assertRaises(ValueError):
            ta.plan({1: None, 2: None})


@unittest.skipUnless(PACK.exists() and FONTS and ta.AT_ASSET.exists(), 'pristine pack, fonts or AT asset missing')
class RealPlanTests(unittest.TestCase):
    def test_plan_badges_and_one_card(self):
        catalog = ta.load_catalog()
        catalog['cards']['6']['en'] = 'At the End of Time Prison'
        for key, card in catalog['cards'].items():
            if key != '6':
                card['en'] = None
        art = ta.plan({1: None, 3: None}, catalog=catalog, badges={'schema': 1, 'badges': {}})
        self.assertEqual(sorted(art['members']), [0, 2, 6])
        self.assertEqual(art['report']['startup_notices']['translated_screens'], [0, 3, 4])
        self.assertFalse(set(art['members']) & ta.FONT_MEMBERS)
        self.assertEqual([t['texture'] for t in art['report']['badges']['todo']], [4, 5])
        self.assertIn(7, art['report']['title_cards_pending'])
        self.assertEqual(art['report']['title_cards_missing_from_catalog'], [])
        tex = gtf.textures(art['members'][2])[1]
        self.assertEqual(ta.sha256(art['members'][2][tex['offset']:tex['offset'] + tex['size']]),
                         ta.M2_T1_JIGOKU_AT)


if __name__ == '__main__':
    unittest.main()
