"""Sony GTF textures as found in TPACKPS3.CPK: parse, decode, encode, paint.

Formats (GCM format byte of the texture descriptor):
  0xA5  A8R8G8B8 linear     bytes A,R,G,B per pixel, rows top-down, pitch = 4*w
  0x85  A8R8G8B8 swizzled   same pixels in Morton (Z) order, pitch 0
  0xAB  G8B8 linear         font pages; decoded as big-endian u16, READ ONLY here

GTF layout (big-endian): u32 version, u32 payload size, u32 count, then
count x 36-byte descriptors (+0 id, +4 data offset from the GTF start,
+8 byte size, +12 format, +13 mipmaps, +14 dimension, +15 cubemap,
+16 remap, +20 u16 width, +22 u16 height, +24 u16 depth, +26 location,
+28 pitch, +32 offset). Pixel data starts 0x80-aligned.

A member holds either a chain of GTF files back to back (member 0: five
1280x720 screens) or GTFs embedded in another container (member 5). The
helpers here only ever rewrite the pixel bytes of one texture (or one
rectangle of it); headers and every other byte are copied unchanged.

    python -m tools.gtf list    <member.bin>
    python -m tools.gtf preview <member.bin> <outdir> [--apply]

Requires numpy (bundled Python); Pillow only for PNG helpers.
"""
import struct
import sys
from pathlib import Path

import numpy as np

VERSIONS = (b'\x01\x05\x00\x00', b'\x02\x02\x00\x00', b'\x02\x02\x00\xff')
LINEAR_ARGB, SWIZZLED_ARGB, G8B8 = 0xA5, 0x85, 0xAB
FORMATS = {LINEAR_ARGB: 'A8R8G8B8 linear', SWIZZLED_ARGB: 'A8R8G8B8 swizzled',
           G8B8: 'G8B8 linear (read only)'}
BPP = {LINEAR_ARGB: 4, SWIZZLED_ARGB: 4, G8B8: 2}
WRITABLE = (LINEAR_ARGB, SWIZZLED_ARGB)


class Texture(dict):
    """One descriptor. Keys: gtf (absolute GTF start), index, id, offset
    (absolute pixel offset), size, fmt, mipmap, dimension, cubemap, remap,
    width, height, depth, location, pitch."""
    __getattr__ = dict.__getitem__

    @property
    def key(self):
        return (self['gtf'], self['index'])


def parse(blob, base=0):
    """Descriptors of the GTF starting at `base`, validated against `blob`."""
    if len(blob) < base + 12 or bytes(blob[base:base + 4]) not in VERSIONS:
        raise ValueError('no GTF header at 0x%x' % base)
    _version, payload, count = struct.unpack_from('>III', blob, base)
    if not 0 < count <= 64 or base + 12 + 36 * count > len(blob):
        raise ValueError('implausible GTF texture count %d at 0x%x' % (count, base))
    out = []
    for i in range(count):
        d = base + 12 + 36 * i
        tid, off, size = struct.unpack_from('>III', blob, d)
        fmt, mip, dim, cube = blob[d + 12:d + 16]
        remap = struct.unpack_from('>I', blob, d + 16)[0]
        w, h, depth = struct.unpack_from('>HHH', blob, d + 20)
        location = blob[d + 26]
        pitch = struct.unpack_from('>I', blob, d + 28)[0]
        t = Texture(gtf=base, index=i, id=tid, offset=base + off, size=size, fmt=fmt,
                    mipmap=mip, dimension=dim, cubemap=cube, remap=remap, width=w,
                    height=h, depth=depth, location=location, pitch=pitch)
        if not w or not h or off < 12 + 36 * count or base + off + size > len(blob):
            raise ValueError('GTF texture %d at 0x%x out of bounds' % (i, base))
        if fmt in BPP and size < w * h * BPP[fmt]:
            raise ValueError('GTF texture %d at 0x%x smaller than %dx%d' % (i, base, w, h))
        out.append(t)
    return out


def _end(textures):
    return max(t['offset'] + t['size'] for t in textures)


def gtfs(blob):
    """[(base, [Texture])] for a chained-GTF member or a container with
    embedded GTFs. Chains are followed from offset 0; otherwise the blob is
    scanned for plausible GTF headers whose textures all fit."""
    blob = bytes(blob) if not isinstance(blob, (bytes, bytearray)) else blob
    found = []
    if bytes(blob[:4]) in VERSIONS:
        p = 0
        while p + 12 <= len(blob) and bytes(blob[p:p + 4]) in VERSIONS:
            tex = parse(blob, p)
            found.append((p, tex))
            p = _end(tex)
            if p % 0x80 and bytes(blob[p:p + 4]) not in VERSIONS:
                p += -p % 0x80
        return found
    p = blob.find(b'\x02\x02\x00\x00')
    while p >= 0:
        try:
            tex = parse(blob, p)
        except ValueError:
            tex = None
        if tex and all(t['fmt'] in BPP for t in tex) and \
                struct.unpack_from('>I', blob, p + 4)[0] == sum(t['size'] for t in tex):
            found.append((p, tex))
            p = blob.find(b'\x02\x02\x00\x00', _end(tex))
        else:
            p = blob.find(b'\x02\x02\x00\x00', p + 4)
    return found


def textures(blob):
    return [t for _base, tex in gtfs(blob) for t in tex]


def _spread(v, bits):
    r = np.zeros_like(v)
    for i in range(bits):
        r |= ((v >> i) & 1) << (2 * i)
    return r


def morton(width, height):
    """(h, w) array: swizzled pixel index of every linear (y, x)."""
    lw, lh = width.bit_length() - 1, height.bit_length() - 1
    if 1 << lw != width or 1 << lh != height:
        raise ValueError('swizzled texture must have power-of-two sides')
    m = min(lw, lh)
    xs, ys = np.arange(width, dtype=np.int64), np.arange(height, dtype=np.int64)
    low = (_spread(xs & ((1 << m) - 1), m)[None, :] |
           (_spread(ys & ((1 << m) - 1), m) << 1)[:, None])
    high = ((xs >> m) << (2 * m))[None, :] + ((ys >> m) << (2 * m))[:, None]
    return low + high


def _argb(blob, tex):
    if tex['fmt'] not in WRITABLE:
        raise ValueError('format 0x%02x is not an ARGB32 texture' % tex['fmt'])
    w, h = tex['width'], tex['height']
    if tex['fmt'] == LINEAR_ARGB and tex['pitch'] not in (0, w * 4):
        raise ValueError('padded pitch not supported')
    return np.frombuffer(blob, np.uint8, w * h * 4, tex['offset']).reshape(-1, 4)


def decode(blob, tex):
    """RGBA uint8 array (h, w, 4) for ARGB32 textures."""
    px = _argb(blob, tex)
    w, h = tex['width'], tex['height']
    if tex['fmt'] == SWIZZLED_ARGB:
        px = px[morton(w, h).reshape(-1)]
    return px.reshape(h, w, 4)[..., [1, 2, 3, 0]].copy()


def decode_g8b8(blob, tex):
    """Font page coverage as big-endian u16 (h, w). Read only."""
    if tex['fmt'] != G8B8:
        raise ValueError('not a G8B8 texture')
    w, h = tex['width'], tex['height']
    return np.frombuffer(blob, '>u2', w * h, tex['offset']).reshape(h, w).copy()


def encode(rgba, tex):
    """Pixel bytes for `tex` from an RGBA (h, w, 4) array."""
    if tex['fmt'] not in WRITABLE:
        raise ValueError('format 0x%02x is read only' % tex['fmt'])
    rgba = np.asarray(rgba, dtype=np.uint8)
    w, h = tex['width'], tex['height']
    if rgba.shape != (h, w, 4):
        raise ValueError('pixels %s do not match %dx%d' % (rgba.shape, w, h))
    argb = rgba[..., [3, 0, 1, 2]].reshape(-1, 4)
    if tex['fmt'] == SWIZZLED_ARGB:
        out = np.empty_like(argb)
        out[morton(w, h).reshape(-1)] = argb
        argb = out
    return argb.tobytes()


def replace(blob, tex, rgba):
    """Copy of `blob` with only `tex`'s pixel bytes replaced."""
    data = encode(rgba, tex)
    out = bytearray(blob)
    out[tex['offset']:tex['offset'] + len(data)] = data
    return bytes(out)


def paint(blob, tex, rect, rgba):
    """Copy of `blob` with only the pixels inside rect=(x, y, w, h) replaced."""
    x, y, w, h = rect
    rgba = np.asarray(rgba, dtype=np.uint8)
    if rgba.shape != (h, w, 4):
        raise ValueError('patch %s does not match rect %s' % (rgba.shape, rect))
    if x < 0 or y < 0 or x + w > tex['width'] or y + h > tex['height']:
        raise ValueError('rect %s outside %dx%d' % (rect, tex['width'], tex['height']))
    if tex['fmt'] == LINEAR_ARGB:
        out = bytearray(blob)
        argb = rgba[..., [3, 0, 1, 2]]
        for row in range(h):
            q = tex['offset'] + ((y + row) * tex['width'] + x) * 4
            out[q:q + w * 4] = argb[row].tobytes()
        return bytes(out)
    full = decode(blob, tex)
    full[y:y + h, x:x + w] = rgba
    return replace(blob, tex, full)


def changed_outside(original, built, tex, rects=()):
    """True when bytes outside tex's rectangles (or outside the texture when
    no rects are given) differ between two equal-length blobs."""
    if len(original) != len(built):
        return True
    a, b = tex['offset'], tex['offset'] + tex['width'] * tex['height'] * 4
    if original[:a] != built[:a] or original[b:] != built[b:]:
        return True
    if not rects:
        return False
    keep = np.ones((tex['height'], tex['width']), bool)
    for x, y, w, h in rects:
        keep[y:y + h, x:x + w] = False
    return bool((decode(original, tex)[keep] != decode(built, tex)[keep]).any())


def to_image(rgba):
    from PIL import Image
    return Image.fromarray(np.asarray(rgba, dtype=np.uint8), 'RGBA')


def from_image(image):
    return np.asarray(image.convert('RGBA'), dtype=np.uint8).copy()


def preview(rgba, background=(24, 28, 40)):
    from PIL import Image
    base = Image.new('RGBA', (rgba.shape[1], rgba.shape[0]), background + (255,))
    base.alpha_composite(to_image(rgba))
    return base.convert('RGB')


def main(argv):
    if len(argv) < 3 or argv[1] not in ('list', 'preview'):
        print(__doc__.strip())
        return 2
    blob = Path(argv[2]).read_bytes()
    found = gtfs(blob)
    for base, tex in found:
        for t in tex:
            print('gtf 0x%08x tex %d  %4dx%-4d %-26s %d bytes at 0x%x' % (
                base, t['index'], t['width'], t['height'], FORMATS.get(t['fmt'], hex(t['fmt'])),
                t['size'], t['offset']))
    if argv[1] == 'preview':
        if len(argv) < 4:
            print('preview needs an output directory')
            return 2
        out = Path(argv[3])
        names = ['g%d_t%d_%dx%d.png' % (g, t['index'], t['width'], t['height'])
                 for g, (_b, tex) in enumerate(found) for t in tex]
        if '--apply' not in argv[4:]:
            print('DRY RUN: %d previews -> %s; pass --apply to write' % (len(names), out))
            return 0
        out.mkdir(parents=True, exist_ok=True)
        i = 0
        for _b, tex in found:
            for t in tex:
                if t['fmt'] in WRITABLE:
                    preview(decode(blob, t)).save(out / names[i])
                i += 1
        print('wrote previews to %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
