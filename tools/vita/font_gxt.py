"""Verified linear P4/P8 GXT font pages; preserve native palettes and metadata."""
import struct
from PIL import Image


def require(condition, message):
    if not condition:
        raise ValueError(message)


class FontPage:
    def __init__(self, data):
        self.data = bytes(data)
        require(data[:8] == b'GXT\0\x03\0\0\x10', 'Unsupported GXT version')
        count, offset, size, p4, p8 = struct.unpack_from('<5I', data, 8)
        require(count == 1 and offset == 64 and (p4,p8) in ((2,0),(0,2)), 'Unexpected font palettes/layout')
        self.colors = 16 if p4 else 256
        self.bits = 4 if p4 else 8
        texture, pixels, palette, flags, kind, fmt = struct.unpack_from('<6I', data, 32)
        self.width, self.height, mipmaps = struct.unpack_from('<HHI', data, 56)
        require((texture, palette, flags, kind, fmt, mipmaps) ==
                (64, 0, 0, 0x60000000, 0x94000000 if p4 else 0x95000000, 1), 'Not a linear paletted font texture')
        require((self.width, self.height) == (4096, 1120), 'Unexpected font dimensions')
        require(pixels == self.width * self.height * self.bits // 8 and size == pixels + self.colors*8
                and len(data) == offset + size, 'Font size mismatch')
        self.pixels = pixels
        self.palettes = [data[64 + pixels + i*self.colors*4:64 + pixels + (i+1)*self.colors*4] for i in range(2)]

    def indices(self):
        if self.bits == 8:
            return self.data[64:64+self.pixels]
        out = bytearray(self.pixels * 2)
        out[0::2] = bytes(v & 15 for v in self.data[64:64 + self.pixels])
        out[1::2] = bytes(v >> 4 for v in self.data[64:64 + self.pixels])
        return out

    def image(self, palette=1):
        rgba = self.palettes[palette]
        indices = Image.frombytes('P', (self.width, self.height), bytes(self.indices()))
        indices.putpalette(bytes(rgba[i + c] for i in range(0, len(rgba), 4) for c in range(3)))
        indices.info['transparency'] = bytes(rgba[3::4])
        return indices.convert('RGBA')

    def cell(self, index, palette=1):
        x, y = index % 128 * 32, index // 128 * 32
        return self.image(palette).crop((x, y, x + 32, y + 32))

    def blank_cells(self):
        from PIL import ImageChops
        image = ImageChops.lighter(self.image(0).getchannel('A'),self.image(1).getchannel('A'))
        return {i for i in range(4480) if image.crop(
            (i % 128 * 32, i // 128 * 32, i % 128 * 32 + 32, i // 128 * 32 + 32)).getbbox() is None}

    def replace(self, coverage_by_index):
        return self.replace_planes({i:(raw,raw) for i,raw in coverage_by_index.items()})

    def replace_planes(self, planes_by_index):
        out = bytearray(self.data)
        alphas = [p[3::4] for p in self.palettes]
        cache = {}
        def quantize(a,b):
            if (a,b) not in cache:
                cache[a,b] = min(range(self.colors),key=lambda i:(alphas[0][i]-a)**2+(alphas[1][i]-b)**2)
            return cache[a,b]
        for index, (first,second) in planes_by_index.items():
            require(0 <= index < 4480 and len(first) == len(second) == 1024, 'Invalid font cell')
            x0, y0 = index % 128 * 32, index // 128 * 32
            for y in range(32):
                start = 64 + ((y0+y)*self.width+x0)*self.bits//8
                for x in range(0, 32, 2):
                    a=quantize(first[y*32+x],second[y*32+x]);b=quantize(first[y*32+x+1],second[y*32+x+1])
                    if self.bits == 4:out[start+x//2] = a | b<<4
                    else:out[start+x:start+x+2] = bytes((a,b))
        palette_bytes = self.colors*8
        require(out[:64] == self.data[:64] and out[-palette_bytes:] == self.data[-palette_bytes:], 'Font metadata changed')
        return bytes(out)


def index_for_code(code):
    # Flat SJIS grid: checked against the Vita atlas's punctuation/Latin anchors.
    return ((code >> 8) - 0x81) * 192 + ((code & 255) - 0x40)


def unused_codes(pages):
    blanks = set.intersection(*(p.blank_cells() for p in pages))
    result = []
    for hi in range(0x81, 0x89):
        for lo in range(0x40, 0xFD):
            if lo == 0x7F:
                continue
            code = hi * 256 + lo
            try:
                bytes([hi, lo]).decode('cp932')
            except UnicodeDecodeError:
                if index_for_code(code) in blanks:
                    result.append(code)
    return result
