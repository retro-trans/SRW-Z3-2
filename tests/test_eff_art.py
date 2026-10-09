"""EFFPS3 text art: record editing, caption splicing, renderers, verification
and (when the pristine archive is present) the real replacement set."""
import copy
import struct
import unittest

import numpy as np

from tools import eff_art as ea, gtf
from tools.common import ROOT, sha256

SOURCE = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/ANIME/EFFPS3.CPK'
try:
    FONTS = (ea.font_dir() / ea.CAPTION_STYLE['face']).exists() and \
        (ea.font_dir() / ea.HEADING_STYLE['face']).exists() and ea.WINDOWS_FONTS.joinpath('timesbd.ttf').exists()
except Exception:
    FONTS = False


def gtf_blob(textures):
    """A GTF with linear ARGB textures [(w, h)], zero pixels."""
    count = len(textures)
    head = b'\x02\x02\x00\x00' + struct.pack('>II', sum(w * h * 4 for w, h in textures), count)
    offset = 0x80 * ((12 + 36 * count + 0x7f) // 0x80)
    descs, data_off = b'', offset
    for i, (w, h) in enumerate(textures):
        descs += struct.pack('>III4BIHHHBxII', i, data_off, w * h * 4, 0xa5, 1, 2, 0, 0xaae4, w, h, 1, 1, w * 4, 0)
        data_off += w * h * 4
    blob = head + descs
    return blob + bytes(offset - len(blob)) + bytes(data_off - offset)


def record(texture, rect, xy, colour=b'\xff\xff\xff\x40' * 4, flags=0x5000, mode=0x301):
    return colour + bytes(8) + struct.pack('>8h', *xy) + struct.pack('>8H', 0, *rect, flags, mode, texture)


def member(records, textures=((64, 32), (32, 32))):
    script = struct.pack('<4I', 2, 16, 32, 0) + b''.join(records)
    script += bytes(-len(script) % 0x80)
    return script + gtf_blob(textures)


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.recs = [record(0, (0, 0, 16, 8), (-100, -10, -60, -10, -100, 10, -60, 10)),
                     record(0, (0, 0, 16, 8), (-110, -12, -50, -12, -110, 12, -50, 12)),     # zoomed keyframe
                     record(1, (0, 0, 8, 8), (-62, -10, -40, -10, -62, 10, -40, 10)),
                     record(0, (16, 0, 16, 8), (-40, -10, 0, -10, -40, 10, 0, 10))]
        self.blob = member(self.recs)

    def test_find_quads_only_in_script(self):
        key = ea.quad_key(0, (0, 0, 16, 8))
        found = ea.find_quads(self.blob, key)
        self.assertEqual(len(found), 2)
        self.assertTrue(all(p < ea.gtf_base(self.blob) for p in found))
        self.assertEqual(ea.quad_xy(self.blob, found[0])[:2], [-100, -10])
        self.assertEqual(len(ea.rect_records(self.blob, 1, (0, 0, 8, 8))), 1)

    def test_widen_keeps_left_edge_and_zoom(self):
        found = ea.find_quads(self.blob, ea.quad_key(0, (0, 0, 16, 8)))
        edits = {}
        ea._widen(edits, self.blob, found, 2.0, w=32)
        rest = struct.unpack('>8h', edits[found[0] - 16])
        zoom = struct.unpack('>8h', edits[found[1] - 16])
        self.assertEqual(rest, (-100, -10, -20, -10, -100, 10, -20, 10))
        self.assertEqual(zoom[0], -110)
        self.assertEqual(zoom[2] - zoom[0], 2 * 60)          # each keyframe keeps its own zoom
        self.assertEqual(struct.unpack('>8H', edits[found[0]])[3], 32)

    def test_shift_scales_with_keyframe_zoom(self):
        found = ea.find_quads(self.blob, ea.quad_key(1, (0, 0, 8, 8)))
        edits = {}
        ea._shift(edits, self.blob, found, 40, 11)          # this keyframe is 22 wide = 2x zoom
        self.assertEqual(struct.unpack('>8h', edits[found[0] - 16])[0], -62 + 80)

    def test_hide_zeroes_vertex_colours_only(self):
        found = ea.find_quads(self.blob, ea.quad_key(0, (16, 0, 16, 8)))
        edits = {}
        ea._hide(edits, found)
        self.assertEqual(edits, {found[0] - 40: bytes(16)})

    def test_verify_member_accepts_only_declared_edits(self):
        found = ea.find_quads(self.blob, ea.quad_key(0, (16, 0, 16, 8)))
        edits = {}
        ea._hide(edits, found)
        tex = gtf.textures(self.blob)[0]
        rgba = np.zeros((32, 64, 4), np.uint8)
        rgba[4:8, 4:8] = 255
        built = bytearray(gtf.replace(self.blob, tex, rgba))
        for p, data in edits.items():
            built[p:p + len(data)] = data
        self.assertTrue(ea.verify_member(self.blob, bytes(built), {tex.key: rgba}, edits))
        undeclared = bytearray(built)
        undeclared[20] ^= 1
        with self.assertRaises(ValueError):
            ea.verify_member(self.blob, bytes(undeclared), {tex.key: rgba}, edits)
        with self.assertRaises(ValueError):                  # edit present but not declared
            ea.verify_member(self.blob, bytes(built), {tex.key: rgba}, {})
        wrong = rgba.copy()
        wrong[0, 0] = 1
        with self.assertRaises(ValueError):
            ea.verify_member(self.blob, bytes(built), {tex.key: wrong}, edits)
        other = gtf.textures(self.blob)[1]
        touched = bytearray(built)
        touched[other['offset']] ^= 1
        with self.assertRaises(ValueError):
            ea.verify_member(self.blob, bytes(touched), {tex.key: rgba}, edits)


def checker_strip(width, end):
    """Checker like the captions: 3x3 cells, flat plateau, fades at both ends."""
    out = np.zeros((32, width, 4), np.uint8)
    out[..., :3] = (218, 232, 253)
    for x in range(1, end):
        fade = min(1.0, x / 6.0, (end - x) / 18.0)
        for y in range(3, 31):
            if ((x // 3) + (y // 3)) % 2:
                out[y, x, 3] = int(127 * fade)
    return out


def bar_strip(width, end):
    out = np.zeros((32, width, 4), np.uint8)
    for i in range(25):
        out[1 + i, i, 3] = 255                         # slanted start
    out[28, 25:end - 21, :] = (110, 140, 220, 255)     # the plain line
    for x in range(end - 21, end):                     # gradient + chevrons
        out[26:30, x] = (150 + 4 * (x - end + 21), 180, 240, 255)
    return out


class SpliceTests(unittest.TestCase):
    def test_checker_grows_and_shrinks_in_whole_periods(self):
        strip = checker_strip(392, 140)
        for delta in (60, -6, -54):
            out = ea.splice_checker(strip, delta)
            self.assertEqual(out.shape, strip.shape)
            new_end = ea._extent(out[..., 3])[1]
            self.assertEqual(new_end, ea._extent(strip[..., 3])[1] + delta)
            # the tail fade is carried over unchanged
            old_end = ea._extent(strip[..., 3])[1]
            self.assertTrue(np.array_equal(out[:, new_end - 19:new_end + 1],
                                           strip[:, old_end - 19:old_end + 1]))
            # 3x3 cells stay continuous across the splice
            on = out[..., 3] > 0
            for x in range(8, new_end - 24):
                self.assertTrue(np.array_equal(on[:, x], on[:, x + 6]))
        with self.assertRaises(ValueError):
            ea.splice_checker(strip, 5)

    def test_bar_keeps_start_and_end_cap(self):
        bar = bar_strip(448, 188)
        for delta in (100, -60):
            out = ea.splice_bar(bar, delta)
            end = ea._extent(out[..., 3])[1]
            self.assertEqual(end, 187 + delta)
            self.assertTrue(np.array_equal(out[:, :25], bar[:, :25]))
            self.assertTrue(np.array_equal(out[:, end - 20:end + 1], bar[:, 167:188]))
        with self.assertRaises(ValueError):
            ea.splice_bar(bar, -200)
        with self.assertRaises(ValueError):
            ea.splice_bar(bar, 300)                    # would run past 448


@unittest.skipUnless(FONTS, 'PS3 system fonts / Times Bold not available')
class RendererTests(unittest.TestCase):
    def test_caption_encoding(self):
        for align in ('left', 'right'):
            rgba, info = ea.caption_text('Japan, Tokyo', align)
            self.assertEqual(rgba.shape, (24, 392, 4))
            self.assertTrue((rgba[..., :3] == ea.CAPTION_STYLE['fill']).all())
            self.assertTrue(set(np.unique(rgba[..., 3])) <= set(range(0, 256, 17)))
            x0, x1 = info['ink']
            if align == 'left':
                self.assertLessEqual(abs(x0 - ea.CAPTION_STYLE['left']), 1)
            else:
                self.assertLessEqual(abs(x1 - ea.CAPTION_STYLE['right']), 1)
            rows = np.nonzero(rgba[..., 3].max(axis=1))[0]
            self.assertGreaterEqual(rows[0], 2)
            self.assertLessEqual(rows[-1], 23)

    def test_caption_condenses_then_refuses(self):
        _rgba, info = ea.caption_text('Outer-Space Mothership Celestial Being', 'left')
        self.assertLess(info['squeeze'], 1.0)
        self.assertLessEqual(info['ink'][1] - info['ink'][0] + 1, ea.CAPTION_STYLE['max_width'])
        with self.assertRaises(ValueError):
            ea.caption_text('Merida Island, Mithril Western Pacific Fleet Headquarters Base', 'left')

    def test_heading_cell_encoding(self):
        crisp, glow, info = ea.heading_cell('Episode', ea.EPISODE_CELL[2])
        from tools.texture_art import CRISP_LEVELS, GLOW_LEVELS
        self.assertTrue(set(np.unique(crisp)) <= set(CRISP_LEVELS))
        self.assertTrue(set(np.unique(glow)) <= set(GLOW_LEVELS))
        self.assertTrue((glow >= crisp).all())               # glow = screen(crisp, halo)
        cols = np.nonzero(crisp.max(axis=0))[0]
        self.assertEqual(cols[0], ea.HEADING_STYLE['left'])
        self.assertFalse(crisp[105:].any())

    def test_library_states_share_one_core(self):
        core, infos = ea.library_core(['Robot Library', 'Character Library', 'Glossary', 'Sound Select',
                                       'Scenario Chart'])
        self.assertEqual(len({i['track'] for i in infos}), 1)   # one letter spacing for all five
        for info, (y0, y1, x1) in zip(infos, ea._library_boxes()):
            self.assertGreaterEqual(info['ink_rows'][0], y0)
            self.assertLessEqual(info['ink_rows'][1], y1)
        states = {s: ea.library_state(core, s).astype(float) for s in ea.LIBRARY_TEXTURES}
        self.assertTrue(np.array_equal(states[11][..., 3], states[13][..., 3]))
        # dark state decomposes back into the core (core black over white glow)
        a, r = states[13][..., 3] / 255, states[13][..., 0] / 255
        self.assertLess(np.abs(a * (1 - r) - core).max(), 0.02)


class CatalogTests(unittest.TestCase):
    def test_catalog_rules(self):
        catalog = ea.load_catalog()
        ids = [e['id'] for e in catalog['entries']]
        self.assertEqual(len(ids), len(set(ids)))
        captions = [m for e in catalog['entries'] if e['family'] == 'location_captions' for m in e['members']]
        self.assertEqual(len(captions), 92)
        self.assertEqual(len(set(captions)), 92)
        self.assertEqual({e['id'] for e in catalog['entries'] if e['status'] == 'pending'},
                         {'title:229', 'menu:233', 'menu:234', 'hud:239'})
        lib = next(e for e in catalog['entries'] if e['id'] == 'library:232')
        self.assertEqual(lib['en'][:3], ['Robot Library', 'Character Library', 'Glossary'])

    def test_catalog_rejects_bad_rows(self):
        catalog = ea.load_catalog()
        path = ROOT / 'work/tengoku/cache/effps3_catalog_test.json'
        bad = copy.deepcopy(catalog)
        row = next(e for e in bad['entries'] if e['status'] == 'translate')
        row['en'] = 'Tōkyō'
        dup = copy.deepcopy(catalog)
        dup['entries'].append(copy.deepcopy(next(e for e in dup['entries'] if e['id'] == 'caption:109')))
        dup['entries'][-1]['id'] = 'caption:dup'
        unguarded = copy.deepcopy(catalog)
        next(e for e in unguarded['entries'] if e['id'] == 'caption:122')['member_sha256'].pop('123')
        import json
        try:
            for broken in (bad, dup, unguarded):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(broken, ensure_ascii=False), encoding='utf-8')
                with self.assertRaises(ValueError):
                    ea.load_catalog(path)
        finally:
            if path.exists():
                path.unlink()


@unittest.skipUnless(SOURCE.exists() and FONTS and ea.BERSERK_ASSET.exists(),
                     'pristine EFFPS3, fonts or Berserk asset missing')
class RealArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = ea._settings()
        cls.art = ea.plan(cls.settings)

    def test_replacement_set(self):
        rep = self.art['report']
        self.assertEqual(rep['counts'], {'location_captions': 79, 'episode_headings': 3, 'berserk': 1,
                                         'library_labels': 1})
        self.assertEqual(len(self.art['members']), 95)
        self.assertNotIn(232, self.art['compress'])          # stored raw in the original
        self.assertIn(109, self.art['compress'])
        self.assertEqual(ea.sha256(self.art['members'][276]), ea.BERSERK_SHIPPED)

    def test_every_member_reverifies_and_rejects_tampering(self):
        for mid, data in self.art['members'].items():
            ea.verify_member(self.art['sources'][mid], data, self.art['intended'][mid], self.art['edits'][mid])
        data = bytearray(self.art['members'][105])
        p = min(self.art['edits'][105])
        data[p - 8] ^= 1                                     # a script byte nobody declared
        with self.assertRaises(ValueError):
            ea.verify_member(self.art['sources'][105], bytes(data), self.art['intended'][105],
                             self.art['edits'][105])

    def test_heading_edits_hide_wa_and_move_digit(self):
        src, out = self.art['sources'][105], self.art['members'][105]
        wa = ea.find_quads(src, ea.quad_key(2, ea.WA))
        self.assertTrue(all(out[p - 40:p - 24] == bytes(16) for p in wa))
        digit = ea.find_quads(src, ea.quad_key(4, ea.DIGIT))
        self.assertEqual(ea.quad_xy(out, digit[0])[0] - ea.quad_xy(src, digit[0])[0], 94)
        dai = ea.find_quads(out, ea.quad_key(2, ea.EPISODE_CELL))
        self.assertEqual(len(dai), 775)

    def test_captions_keep_header_and_quads(self):
        for mid in (109, 121, 141):
            src, out = self.art['sources'][mid], self.art['members'][mid]
            tex = gtf.textures(src)[0]
            a, b = gtf.decode(src, tex), gtf.decode(out, tex)
            self.assertTrue(np.array_equal(a[:72], b[:72]))          # JAPAN/WORLD MAP header untouched
            self.assertTrue(np.array_equal(a[:, 448:], b[:, 448:]))
            self.assertEqual(out[:tex['gtf']], src[:tex['gtf']])     # no script change for captions


if __name__ == '__main__':
    unittest.main()
