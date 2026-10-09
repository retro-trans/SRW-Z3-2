"""CRI CPK archive reader.

SRW Z3 wraps its data in CRI Middleware CPK archives. This parses the @UTF
tables that describe them and extracts member files, transparently
decompressing CRILAYLA where present.

Pure stdlib on purpose: no dependency should stand between a fork and a build.

    python -m tools.cpk list   <file.cpk>
    python -m tools.cpk info   <file.cpk>
    python -m tools.cpk unpack <file.cpk> <outdir> [--apply]

Archives up to MMAP_THRESHOLD (64 MiB) are read into memory. Larger ones
(EFFPS3, an uncompressed TPACK build) are memory-mapped read-only instead,
so only the members actually read are copied. Call close() (or use the
reader as a context manager) before deleting or replacing a mapped file.
"""
import mmap
import os
import struct
import sys
from pathlib import Path

# @UTF column storage classes (flags & 0xf0)
STORAGE_ZERO = 0x10
STORAGE_CONSTANT = 0x30
STORAGE_PERROW = 0x50

# @UTF value types (flags & 0x0f) -> (struct code, byte width)
TYPES = {
    0x00: ("B", 1), 0x01: ("b", 1),
    0x02: (">H", 2), 0x03: (">h", 2),
    0x04: (">I", 4), 0x05: (">i", 4),
    0x06: (">Q", 8), 0x07: (">q", 8),
    0x08: (">f", 4), 0x09: (">d", 8),
    0x0A: ("string", 4),
    0x0B: ("bytes", 8),
}


class UTFTable:
    """One @UTF table: a schema plus rows, addressed by column name."""

    def __init__(self, buf, base=0):
        if base < 0 or base + 32 > len(buf):
            raise ValueError('truncated @UTF header')
        if buf[base:base + 4] != b"@UTF":
            raise ValueError("not an @UTF table at 0x%x" % base)
        self.size = struct.unpack_from(">I", buf, base + 4)[0]
        d = base + 8  # every offset below is relative to here
        if self.size < 24 or d + self.size > len(buf):
            raise ValueError('@UTF table exceeds buffer')

        (rows_off, str_off, data_off, name_off,
         n_cols, row_len, n_rows) = struct.unpack_from(">IIIIHHI", buf, d)
        if not (24 <= rows_off <= str_off <= data_off <= self.size):
            raise ValueError('invalid @UTF region order')
        if rows_off + row_len * n_rows > str_off:
            raise ValueError('@UTF rows overlap strings')

        self.buf = buf
        self.field_offset = {}   # (row, column) -> absolute offset of the value
        self.blob_offset = {}    # (row, column) -> absolute offset of blob data
        self.strings = buf[d + str_off: d + data_off]
        self.name = self._str(name_off)
        self.n_rows = n_rows

        # --- schema ---
        self.columns = []   # (name, flags, constant_or_None)
        p = d + 0x18
        for _ in range(n_cols):
            flags = buf[p]
            if flags & 0xF0 not in (STORAGE_ZERO, STORAGE_CONSTANT, STORAGE_PERROW):
                raise ValueError('unsupported @UTF storage class')
            p += 1
            cname = self._str(struct.unpack_from(">I", buf, p)[0])
            p += 4
            const = None
            if flags & 0xF0 == STORAGE_CONSTANT:
                const, p = self._read(buf, p, flags & 0x0F, d + data_off)
            self.columns.append((cname, flags, const))
        if p > d + rows_off:
            raise ValueError('@UTF schema overlaps rows')

        # --- rows ---
        self.rows = []
        for r in range(n_rows):
            p = d + rows_off + r * row_len
            row = {}
            for cname, flags, const in self.columns:
                store = flags & 0xF0
                if store == STORAGE_ZERO:
                    row[cname] = 0
                elif store == STORAGE_CONSTANT:
                    row[cname] = const
                else:
                    self.field_offset[(r, cname)] = p
                    typ = flags & 0x0F
                    if typ == 0x0B:
                        off, _ln = struct.unpack_from(">II", buf, p)
                        self.blob_offset[(r, cname)] = d + data_off + off
                    row[cname], p = self._read(buf, p, typ, d + data_off)
                if p > d + rows_off + (r + 1) * row_len:
                    raise ValueError('@UTF value exceeds row')
            self.rows.append(row)

    def _str(self, off):
        if not 0 <= off < len(self.strings):
            raise ValueError('@UTF string offset out of bounds')
        end = self.strings.find(b"\0", off)
        if end < 0:
            raise ValueError('unterminated @UTF string')
        return self.strings[off:end].decode("utf-8")

    def _read(self, buf, p, typ, data_base):
        if typ not in TYPES:
            raise ValueError("unknown @UTF type 0x%x" % typ)
        code, width = TYPES[typ]
        if code == "string":
            return self._str(struct.unpack_from(">I", buf, p)[0]), p + 4
        if code == "bytes":
            off, ln = struct.unpack_from(">II", buf, p)
            if data_base + off + ln > len(buf):
                raise ValueError('@UTF blob out of bounds')
            return buf[data_base + off: data_base + off + ln], p + 8
        if width == 1:
            return struct.unpack_from(">" + code, buf, p)[0], p + 1
        return struct.unpack_from(code, buf, p)[0], p + width

    def get(self, row, key, default=None):
        return self.rows[row].get(key, default)

    def column_type(self, key):
        for cname, flags, _const in self.columns:
            if cname == key:
                return flags & 0x0F
        raise KeyError(key)

    def patch(self, buf, row, key, value):
        """Overwrite one per-row integer in `buf` (a bytearray) in place.
        Only valid for per-row columns; constants are shared by every row."""
        off = self.field_offset.get((row, key))
        if off is None:
            raise KeyError("%r is not a per-row field" % key)
        code, width = TYPES[self.column_type(key)]
        if width == 1:
            struct.pack_into(">" + code, buf, off, value)
        else:
            struct.pack_into(code, buf, off, value)


def decompress_crilayla(src):
    """CRILAYLA: LZ variant that emits its output back-to-front."""
    if src[:8] != b"CRILAYLA":
        return src
    if len(src) < 16:
        raise ValueError('truncated CRILAYLA header')
    usize, dsize = struct.unpack_from("<II", src, 8)
    if usize > 256 << 20 or 0x10 + dsize + 0x100 > len(src):
        raise ValueError('invalid/unsupported CRILAYLA size')
    header = src[0x10 + dsize: 0x10 + dsize + 0x100]  # raw 0x100 prefix
    out = bytearray(usize)

    pos = 0x10 + dsize - 1   # bits are consumed backwards
    pool = bits = 0

    def take(n):
        nonlocal pos, pool, bits
        v = 0
        while n:
            if not bits:
                if pos < 0x10:
                    raise ValueError('CRILAYLA bitstream exhausted')
                pool = src[pos]
                pos -= 1
                bits = 8
            k = min(n, bits)
            v = (v << k) | ((pool >> (bits - k)) & ((1 << k) - 1))
            bits -= k
            n -= k
        return v

    VLE = (2, 3, 5, 8)
    o = usize - 1
    while o >= 0:
        if take(1):
            ref = o + take(13) + 3
            ln = 3
            for width in VLE:
                d = take(width)
                ln += d
                if d != (1 << width) - 1:
                    break
            else:
                while True:
                    d = take(8)
                    ln += d
                    if d != 255:
                        break
            for _ in range(ln):
                if not o < ref < usize:
                    raise ValueError('invalid CRILAYLA back reference')
                out[o] = out[ref]
                o -= 1
                ref -= 1
                if o < 0:
                    break
        else:
            out[o] = take(8)
            o -= 1
    return header + bytes(out)


MMAP_THRESHOLD = 64 << 20


class CPK:
    def __init__(self, path):
        self.path = path
        self._file = None
        size = Path(path).stat().st_size
        if size > MMAP_THRESHOLD and size:
            self._file = open(path, 'rb')
            self.buf = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            with open(path, "rb") as fh:
                self.buf = fh.read()
        try:
            self._load()
        except Exception:
            self.close()
            raise

    def close(self):
        """Release a memory-mapped archive (a no-op for in-memory ones)."""
        if self._file is not None:
            self.buf.close()
            self._file.close()
            self._file = None
            self.buf = b''

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    @property
    def mapped(self):
        return self._file is not None

    def _load(self):
        path = self.path
        if self.buf[:4] != b"CPK ":
            raise ValueError("%s: not a CPK" % path)
        self.header = UTFTable(self.buf, 0x10)
        self.files = self._toc() or self._itoc()
        if len(self.files) != self._h('Files'):
            raise ValueError('CPK member count disagrees with header')
        ids = [e['id'] for e in self.files]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate CPK member ID')
        previous_end = self._h('ContentOffset') or 0
        for entry in sorted(self.files, key=lambda e: e['offset']):
            if entry['offset'] < previous_end or entry['size'] < 0 or entry['offset'] + entry['size'] > len(self.buf):
                raise ValueError('overlapping/out-of-bounds CPK member')
            previous_end = entry['offset'] + entry['size']

    def _h(self, key):
        return self.header.get(0, key)

    def _toc(self):
        toc_off = self._h("TocOffset") or 0
        if not toc_off:
            return []
        content = self._h("ContentOffset") or 0
        # file offsets are relative to whichever of the two comes first
        base = min(toc_off, content) if content else toc_off
        toc = UTFTable(self.buf, toc_off + 0x10)
        out = []
        for r in range(toc.n_rows):
            out.append({
                "dir": toc.get(r, "DirName", "") or "",
                "name": toc.get(r, "FileName", ""),
                "size": toc.get(r, "FileSize", 0),
                "extract": toc.get(r, "ExtractSize", 0),
                "offset": base + (toc.get(r, "FileOffset", 0) or 0),
                "id": toc.get(r, "ID", r),
            })
        return out

    def _itoc(self):
        """ITOC layout: no filenames. Files are identified by ID and laid out
        back to back from ContentOffset, each padded up to Align."""
        itoc_off = self._h("ItocOffset") or 0
        if not itoc_off:
            return []
        itoc = UTFTable(self.buf, itoc_off + 0x10)
        sizes = {}
        for key in ("DataL", "DataH"):   # 16-bit and 32-bit size tables
            blob = itoc.get(0, key)
            if not blob:
                continue
            sub = UTFTable(blob, 0)
            for r in range(sub.n_rows):
                if sub.get(r, 'ID') in sizes:
                    raise ValueError('duplicate member ID across ITOC rows')
                sizes[sub.get(r, "ID")] = (sub.get(r, "FileSize", 0),
                                           sub.get(r, "ExtractSize", 0))
        align = self._h("Align") or 1
        off = self._h("ContentOffset") or 0
        out = []
        for i in sorted(sizes):
            size, extract = sizes[i]
            out.append({"dir": "", "name": "%05d.bin" % i, "size": size,
                        "extract": extract, "offset": off, "id": i})
            off += size
            if align and off % align:
                off += align - (off % align)
        return out

    def read(self, entry):
        raw = self.buf[entry["offset"]: entry["offset"] + entry["size"]]
        expected = entry['extract'] or entry['size']
        result = decompress_crilayla(raw) if raw.startswith(b'CRILAYLA') else raw
        if len(raw) != entry['size'] or len(result) != expected:
            raise ValueError('CPK member %s declared-size mismatch' % entry['id'])
        return result

    def unpack(self, outdir):
        from tools.common import destination
        planned = []
        for e in self.files:
            rel = os.path.join(e["dir"].replace("/", os.sep), e["name"])
            dest = destination(outdir, rel)
            if dest.exists():
                raise ValueError('output already exists: %s' % dest)
            planned.append((e, dest))
        if len({str(p).casefold() for _, p in planned}) != len(planned):
            raise ValueError('duplicate CPK output paths')
        n = 0
        for e, dest in planned:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "xb") as fh:
                fh.write(self.read(e))
            n += 1
        return n


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 2
    cmd, path = argv[1], argv[2]
    cpk = CPK(path)
    if cmd == "info":
        print("%s\n  files=%d" % (path, len(cpk.files)))
        for k, _f, _c in cpk.header.columns:
            print("  %-20s %s" % (k, cpk.header.get(0, k)))
    elif cmd == "list":
        for e in cpk.files:
            flag = "CRILAYLA" if e["extract"] != e["size"] else ""
            print("%10d %10d  %-8s %s/%s"
                  % (e["size"], e["extract"], flag, e["dir"], e["name"]))
        print("-- %d files" % len(cpk.files))
    elif cmd == "unpack":
        if len(argv) < 4:
            print("unpack needs an output directory")
            return 2
        if '--apply' not in argv[4:]:
            print('DRY RUN: %d members -> %s; pass --apply to write' % (len(cpk.files), argv[3]))
            for entry in cpk.files[:5]:
                print('  %s/%s (%d decoded bytes)' % (entry['dir'], entry['name'], entry['extract']))
        else:
            print("%d files -> %s" % (cpk.unpack(argv[3]), argv[3]))
    else:
        print("unknown command %r" % cmd)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
