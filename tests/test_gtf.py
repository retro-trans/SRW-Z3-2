"""GTF decode/encode: synthetic fixtures always, the real TPACK when present.

The real-pack sweep covers members 0, 2, 4, 5, 6 and 88 by default (chained
GTFs, the 9-texture badge atlas, swizzled member 5, cards). Set
TENGOKU_FULL_TEXTURES=1 to round-trip all 135 members.
"""
import os
import struct
import unittest

import numpy as np

from tools import gtf
from tools.common import ROOT

PACK = ROOT / 'work/tengoku/source/PS3_GAME/USRDIR/DATA/TABATA/TPACKPS3.CPK'


def make_gtf(specs, version=b'\x02\x02\x00\x00', seed=0):
    """GTF with textures [(fmt, w, h)], random pixels, 0x80-aligned data."""
    rng = np.random.default_rng(seed)
    head = 12 + 36 * len(specs)
    data_off = head + (-head % 0x80)
    descriptors, payload = b'', b''
    for i, (fmt, w, h) in enumerate(specs):
        size = w * h * gtf.BPP[fmt]
        pitch = 0 if fmt == gtf.SWIZZLED_ARGB else w * gtf.BPP[fmt]
        descriptors += struct.pack('>III4BIHHHBxII', i, data_off + len(payload), size,
                                   fmt, 1, 2, 0, 0xaae4, w, h, 1, 1, pitch, 0)
        payload += rng.integers(0, 256, size, dtype=np.uint8).tobytes()
    header = version + struct.pack('>II', len(payload), len(specs)) + descriptors
    return header + bytes(data_off - len(header)) + payload


class GTFTests(unittest.TestCase):
    def test_round_trip_linear_swizzled_and_multi(self):
        blob = make_gtf([(gtf.LINEAR_ARGB, 12, 5), (gtf.SWIZZLED_ARGB, 16, 8),
                         (gtf.SWIZZLED_ARGB, 4, 32), (gtf.LINEAR_ARGB, 80, 80)])
        tex = gtf.textures(blob)
        self.assertEqual(len(tex), 4)
        for t in tex:
            raw = blob[t['offset']:t['offset'] + t['size']]
            self.assertEqual(gtf.encode(gtf.decode(blob, t), t), raw)
            self.assertEqual(gtf.replace(blob, t, gtf.decode(blob, t)), blob)

    def test_linear_decode_is_argb(self):
        blob = bytearray(make_gtf([(gtf.LINEAR_ARGB, 2, 1)]))
        t = gtf.textures(blob)[0]
        blob[t['offset']:t['offset'] + 8] = bytes([10, 20, 30, 40, 50, 60, 70, 80])
        self.assertEqual(gtf.decode(bytes(blob), t).tolist(), [[[20, 30, 40, 10], [60, 70, 80, 50]]])

    def test_morton_is_a_permutation_with_z_order(self):
        for w, h in ((8, 8), (16, 4), (4, 16), (1024, 512)):
            idx = gtf.morton(w, h).ravel()
            self.assertEqual(sorted(idx.tolist()), list(range(w * h)))
        self.assertEqual(gtf.morton(4, 4)[:2, :2].tolist(), [[0, 1], [2, 3]])
        self.assertEqual(gtf.morton(4, 4)[0, 2], 4)
        with self.assertRaises(ValueError):
            gtf.morton(12, 8)

    def test_paint_changes_only_the_rectangle(self):
        for fmt in (gtf.LINEAR_ARGB, gtf.SWIZZLED_ARGB):
            blob = make_gtf([(gtf.LINEAR_ARGB, 8, 8), (fmt, 16, 16)], seed=3)
            t = gtf.textures(blob)[1]
            patch = np.full((3, 5, 4), 7, np.uint8)
            out = gtf.paint(blob, t, (2, 4, 5, 3), patch)
            self.assertEqual(len(out), len(blob))
            after, before = gtf.decode(out, t), gtf.decode(blob, t)
            self.assertTrue((after[4:7, 2:7] == 7).all())
            after[4:7, 2:7] = before[4:7, 2:7]
            self.assertTrue(np.array_equal(after, before))
            self.assertFalse(gtf.changed_outside(blob, out, t, [(2, 4, 5, 3)]))
            self.assertTrue(gtf.changed_outside(blob, out, t, [(0, 0, 1, 1)]))
            first = gtf.textures(blob)[0]
            self.assertEqual(out[:t['offset']], blob[:t['offset']])
            self.assertEqual(gtf.decode(out, first).tobytes(), gtf.decode(blob, first).tobytes())

    def test_chained_and_embedded_gtfs(self):
        one = make_gtf([(gtf.LINEAR_ARGB, 32, 4)], b'\x01\x05\x00\x00', 1)
        two = make_gtf([(gtf.LINEAR_ARGB, 16, 4)], b'\x02\x02\x00\x00', 2)
        chained = gtf.gtfs(one + two)
        self.assertEqual([base for base, _ in chained], [0, len(one)])
        container = struct.pack('<II', 1, 16) + bytes(0x3f8) + two + b'tail'
        embedded = gtf.gtfs(container)
        self.assertEqual([base for base, _ in embedded], [0x400])
        t = embedded[0][1][0]
        self.assertEqual(gtf.encode(gtf.decode(container, t), t), container[t['offset']:t['offset'] + t['size']])

    def test_font_pages_are_read_only(self):
        blob = make_gtf([(gtf.G8B8, 8, 4)], b'\x02\x02\x00\xff')
        t = gtf.textures(blob)[0]
        self.assertEqual(gtf.decode_g8b8(blob, t).shape, (4, 8))
        with self.assertRaises(ValueError):
            gtf.decode(blob, t)
        with self.assertRaises(ValueError):
            gtf.encode(np.zeros((4, 8, 4), np.uint8), t)

    def test_rejects_out_of_bounds(self):
        blob = make_gtf([(gtf.LINEAR_ARGB, 8, 8)])
        with self.assertRaises(ValueError):
            gtf.parse(blob[:-1])


@unittest.skipUnless(PACK.exists(), 'pristine TPACKPS3.CPK not extracted')
class RealPackTests(unittest.TestCase):
    def test_every_texture_round_trips(self):
        from tools.cpk import CPK
        full = os.environ.get('TENGOKU_FULL_TEXTURES') == '1'
        wanted = None if full else {0, 2, 4, 5, 6, 88}
        counts = {}
        with CPK(PACK) as archive:
            for entry in archive.files:
                if wanted is not None and entry['id'] not in wanted:
                    continue
                blob = archive.read(entry)
                tex = gtf.textures(blob)
                self.assertTrue(tex, 'member %d has no GTF' % entry['id'])
                for t in tex:
                    if t['fmt'] in gtf.WRITABLE:
                        raw = blob[t['offset']:t['offset'] + t['size']]
                        self.assertEqual(gtf.encode(gtf.decode(blob, t), t), raw,
                                         'member %d texture %s' % (entry['id'], t.key))
                    else:
                        self.assertEqual(gtf.decode_g8b8(blob, t).astype('>u2').tobytes(),
                                         blob[t['offset']:t['offset'] + t['size']])
                counts[entry['id']] = len(tex)
        if full:
            self.assertEqual(sum(counts.values()), 165)
        else:
            self.assertEqual(counts, {0: 5, 2: 9, 4: 1, 5: 19, 6: 1, 88: 1})


if __name__ == '__main__':
    unittest.main()
