"""Rebuild an ITOC CPK with replacement members.

Why this exists: CriPakTools cannot rebuild ITOC archives. It writes the
content region on 0x800 boundaries while leaving the ITOC implying the packed
layout, so even its own reader then points at padding. ITOC has no FileOffset
column, so the reader recomputes positions and the writer's layout rule has to
match it exactly.

The rule, verified against every member of an untouched STG*.SDAT: members sit
back to back from ContentOffset, each padded up to Align (16).

Replacements are stored UNCOMPRESSED (ExtractSize == FileSize) by default,
which is legal. With compress=True (CLI --compress) each replacement is
CRILAYLA-compressed by compress_crilayla(), decompressed again with the
reader's own tools.cpk.decompress_crilayla and compared byte for byte before
it is accepted; a member that does not shrink stays uncompressed. Untouched
members keep their original bytes verbatim, still compressed.

Only the header region is copied into memory; untouched member payloads are
streamed from the (memory-mapped, when large) source, so archives well past
64 MiB can be rebuilt.

    python -m tools.cpkpatch <in.cpk> <out.cpk> --replace 3=new3.lua [5=new5.lua] [--compress]

The default CLI is a dry run; append --apply after reviewing it. This port
has storage tests only. It does not establish Tengoku runtime compatibility.
"""
import argparse
import os
import struct
import sys

from pathlib import Path
from tools.cpk import CPK, UTFTable, decompress_crilayla

NUL = bytes(1)


CRILAYLA_WINDOW = 8194      # 13-bit distance field + 3
CRILAYLA_PREFIX = 0x100     # stored raw after the bitstream


def compress_crilayla(data):
    """CRILAYLA-compress `data`; None when it cannot be stored that way.

    Layout (what tools.cpk.decompress_crilayla reads): b'CRILAYLA', u32 LE
    size of the body (data minus its first 0x100 bytes), u32 LE size of the
    bitstream, the bitstream, then the first 0x100 bytes raw. The body is
    coded back to front, so in the reversed body this is a plain LZ77:
    flag 1 + 13-bit (distance - 3) + length - 3 in the 2/3/5/8(/8...) bit
    VLE, or flag 0 + an 8-bit literal. Bits are written MSB first and the
    byte stream is stored reversed (the reader starts at the last byte).
    The stream is zero-padded at its end (the low addresses) to a multiple
    of 4 bytes, like every member of the original TPACKPS3.
    Greedy longest match; bytes.find does the window search in C.
    """
    data = bytes(data)
    if len(data) <= CRILAYLA_PREFIX + 3:
        return None
    body = data[CRILAYLA_PREFIX:][::-1]
    n = len(body)
    out = bytearray()
    acc = nacc = 0
    find = body.find
    i = 0
    while i < n:
        limit = n - i
        best = 0
        pos = -1
        if limit >= 3:
            lo = i - CRILAYLA_WINDOW if i > CRILAYLA_WINDOW else 0
            # A match of length L starting at s needs lo <= s <= i - 3, i.e.
            # it lies inside body[lo:i - 3 + L] (overlapping copies allowed).
            s = find(body[i:i + 3], lo, i)
            if s >= 0:
                best, pos, bad = 3, s, limit + 1
                while best < limit:                     # gallop
                    trial = min(best * 2, limit)
                    s = find(body[i:i + trial], lo, i - 3 + trial)
                    if s < 0:
                        bad = trial
                        break
                    best, pos = trial, s
                while bad - best > 1:                   # then bisect
                    mid = (best + bad) // 2
                    s = find(body[i:i + mid], lo, i - 3 + mid)
                    if s >= 0:
                        best, pos = mid, s
                    else:
                        bad = mid
        if best >= 3:
            acc = (acc << 14) | 0x2000 | (i - pos - 3)
            nacc += 14
            extra = best - 3
            for width in (2, 3, 5, 8):
                full = (1 << width) - 1
                if extra < full:
                    acc = (acc << width) | extra
                    nacc += width
                    extra = -1
                    break
                acc = (acc << width) | full
                nacc += width
                extra -= full
            if extra >= 0:
                while extra >= 255:
                    acc = (acc << 8) | 255
                    nacc += 8
                    extra -= 255
                acc = (acc << 8) | extra
                nacc += 8
            i += best
        else:
            acc = (acc << 9) | body[i]
            nacc += 9
            i += 1
        if nacc >= 64:
            k = nacc // 8
            nacc -= 8 * k
            out += (acc >> nacc).to_bytes(k, 'big')
            acc &= (1 << nacc) - 1
    if nacc:
        pad = -nacc % 8
        out += (acc << pad).to_bytes((nacc + pad) // 8, 'big')
    out += bytes(-len(out) % 4)
    stream = bytes(out[::-1])
    return b'CRILAYLA' + struct.pack('<II', n, len(stream)) + stream + data[:CRILAYLA_PREFIX]


def _stored_form(data):
    """(stored bytes, compressed?) for one replacement, proven by a round trip."""
    packed = compress_crilayla(data)
    if packed is None or len(packed) >= len(data):
        return data, False
    if decompress_crilayla(packed) != data:
        raise ValueError('CRILAYLA round trip failed; refusing compressed member')
    return packed, True


def stored_forms(payloads, workers=None):
    """{id: stored bytes} for {id: bytes}; compression runs in parallel."""
    ids = sorted(payloads)
    if not ids:
        return {}
    if workers is None:
        workers = min(len(ids), os.cpu_count() or 1)
    if workers <= 1 or len(ids) <= 1:
        return {i: _stored_form(payloads[i])[0] for i in ids}
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_stored_form, [payloads[i] for i in ids]))
    return {i: r[0] for i, r in zip(ids, results)}


def _payload(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    return Path(value).read_bytes()


def build(src, dst, replacements, compress=False, workers=None):
    """Rebuild `src` into `dst` with {id: path or bytes} replacements.

    compress=True stores each replacement CRILAYLA-compressed (when that is
    smaller) after a decompress round trip; a set of ids compresses only
    those replacements. Returns (members, bytes written).
    """
    if Path(dst).exists() or Path(src).resolve() == Path(dst).resolve():
        raise ValueError('destination exists or aliases source')
    with CPK(src) as cpk:
        return _build(cpk, src, dst, replacements, compress, workers)


def _build(cpk, src, dst, replacements, compress, workers):
    unknown = set(replacements) - {e['id'] for e in cpk.files}
    if unknown:
        raise ValueError('unknown replacement IDs: %s' % sorted(unknown))
    if cpk._h('TocOffset') or cpk._h('EtocOffset') or cpk._h('GtocOffset'):
        raise ValueError('writer currently supports ITOC-only archives without auxiliary TOCs')
    if not cpk.files:
        raise SystemExit("%s: no members (is this an ITOC CPK?)" % src)

    itoc_off = cpk._h("ItocOffset") or 0
    if not itoc_off:
        raise SystemExit("%s: not an ITOC CPK; this tool only handles ITOC" % src)

    content_off = cpk._h("ContentOffset") or 0
    align = cpk._h("Align") or 1

    # Only the header region (CPK header + ITOC + padding) is ever edited, so
    # only that much of the archive is copied into memory.
    buf = bytearray(cpk.buf[:content_off])
    itoc = UTFTable(buf, itoc_off + 0x10)

    # locate every member's size fields inside the DataL/DataH sub-tables
    where = {}   # id -> (blob_abs_offset, sub_table, row)
    for key in ("DataL", "DataH"):
        blob = itoc.get(0, key)
        if not blob:
            continue
        blob_abs = itoc.blob_offset[(0, key)]
        sub = UTFTable(blob, 0)
        for r in range(sub.n_rows):
            where[sub.get(r, "ID")] = (blob_abs, sub, r)

    new_data = {fid: _payload(path) for fid, path in replacements.items()}
    if compress is True:
        packed_ids = set(new_data)
    else:
        packed_ids = set(compress or ())
        if packed_ids - set(new_data):
            raise ValueError('compress names members that are not replaced: %s'
                             % sorted(packed_ids - set(new_data)))
    stored = dict(new_data)
    stored.update(stored_forms({i: new_data[i] for i in packed_ids}, workers))

    # gather payloads in ID order: (id, source, stored size, extract size);
    # an untouched member's source is the (offset, size) of its raw bytes,
    # streamed from the source archive while writing
    payloads = []
    for e in cpk.files:
        fid = e["id"]
        if fid in replacements:
            payloads.append((fid, stored[fid], len(stored[fid]), len(new_data[fid])))
        else:
            payloads.append((fid, (e["offset"], e["size"]), e["size"], e["extract"]))

    # A replacement can outgrow the 16-bit DataL columns (English stage 3
    # member 3 is 68 KB uncompressed against a 52 KB Japanese original). The
    # game's own archives keep such members in DataH (32-bit), and the reader
    # merges both tables sorted by ID, so moving the row is layout-safe.
    to_move = []
    for fid, _data, size, extract in payloads:
        if fid not in where:
            raise SystemExit("id %d has no ITOC entry" % fid)
        _blob_abs, sub, _row = where[fid]
        _code, width = _coltype(sub, "FileSize")
        if width == 2 and max(size, extract) > 0xFFFF:
            to_move.append(fid)

    # Each move grows the ITOC by 4 bytes (u16 -> u32 sizes), more when a
    # CpkItocH has to be built. The padding before ContentOffset is small
    # (40 bytes in STGZ3OF2), so when the moves need more, the content region
    # shifts forward. ITOC has no FileOffset column: readers place members
    # from ContentOffset, so only that header field changes.
    if to_move:
        parent = UTFTable(buf, itoc_off + 0x10)
        free = content_off - (itoc_off + 0x10 + 8 + parent.size)
        need = 4 * len(to_move) + (0 if _datah_is_usable(parent.get(0, 'DataH')) else 128)
        if need > free:
            grow = need - free
            if align and grow % align:
                grow += align - grow % align
            buf[content_off:content_off] = bytes(grow)
            content_off += grow
            cpk.header.patch(buf, 0, 'ContentOffset', content_off)
            print("  ContentOffset moved by %d bytes to %d for the ITOC growth" % (grow, content_off))

    moved = []
    for fid in to_move:
        _move_to_datah(buf, cpk, fid, content_off)
        moved.append(fid)
    if moved:
        itoc = UTFTable(buf, itoc_off + 0x10)
        where = {}
        for key in ("DataL", "DataH"):
            blob = itoc.get(0, key)
            if not blob:
                continue
            blob_abs = itoc.blob_offset[(0, key)]
            sub = UTFTable(blob, 0)
            for r in range(sub.n_rows):
                where[sub.get(r, "ID")] = (blob_abs, sub, r)
        print("  ids %s moved DataL -> DataH (size outgrew 16 bits)"
              % ",".join(map(str, moved)))

    # patch the size tables, refusing anything that would not fit its column
    for fid, _data, size, extract in payloads:
        if fid not in where:
            raise SystemExit("id %d has no ITOC entry" % fid)
        blob_abs, sub, row = where[fid]
        for col, val in (("FileSize", size), ("ExtractSize", extract)):
            code, width = _coltype(sub, col)
            limit = (1 << (width * 8)) - 1
            if val > limit:
                raise SystemExit(
                    "id %d: %s=%d overflows the %d-bit %s column. It would have "
                    "to move to DataH, which this tool does not do."
                    % (fid, col, val, width * 8,
                       "DataL" if width == 2 else "DataH"))
            off = blob_abs + sub.field_offset[(row, col)]
            struct.pack_into(code if width > 1 else ">" + code, buf, off, val)

    # buf already holds only the (possibly grown) header region.
    out = buf

    # Header size fields, decoded from an untouched archive:
    #   ContentSize       aligned total, INCLUDING a final pad the file omits
    #   EnabledDataSize   sum of FileSize    (stored sizes)
    #   EnabledPackedSize sum of ExtractSize (unpacked sizes)
    aligned_total = 0
    for _fid, _data, size, _extract in payloads:
        aligned_total += size
        if align and aligned_total % align:
            aligned_total += align - (aligned_total % align)

    for col, val in (("ContentSize", aligned_total),
                     ("EnabledDataSize", sum(p[2] for p in payloads)),
                     ("EnabledPackedSize", sum(p[3] for p in payloads))):
        try:
            cpk.header.patch(out, 0, col, val)
        except KeyError:
            if cpk._h(col) != val:
                raise ValueError('cannot update required header field: %s' % col)

    with open(dst, "xb") as fh:
        fh.write(out)
        pos = content_off
        for i, (_fid, data, size, _extract) in enumerate(payloads):
            if isinstance(data, tuple):         # untouched: stream raw bytes
                offset, length = data
                for chunk in range(offset, offset + length, 16 << 20):
                    fh.write(cpk.buf[chunk:min(chunk + (16 << 20), offset + length)])
            else:
                fh.write(data)
            pos += size
            # Match the original archive: padding BETWEEN members, not EOF.
            if i != len(payloads)-1 and align and pos % align:
                pad = align - (pos % align)
                fh.write(b'\0' * pad)
                pos += pad
    return len(payloads), pos


def _coltype(table, col):
    from tools.cpk import TYPES
    return TYPES[table.column_type(col)]


def _rows_edit(blob, edit):
    """Return a sub-@UTF blob with its fixed-size integer rows replaced by
    `edit(rows)`. Schema and strings are untouched; the string/data offsets
    and the table size shift by the row-area delta. Only valid for tables
    whose rows carry no string or blob columns (CpkItocL/CpkItocH)."""
    assert blob[:4] == b"@UTF", "not a @UTF sub-table"
    size = struct.unpack_from(">I", blob, 4)[0]
    d = 8
    rows_off, str_off, data_off, name_off, n_cols, row_len, n_rows = \
        struct.unpack_from(">IIIIHHI", blob, d)
    rstart, rend = d + rows_off, d + rows_off + row_len * n_rows
    rows = [bytes(blob[rstart + i * row_len: rstart + (i + 1) * row_len])
            for i in range(n_rows)]
    rows = edit(rows)
    # An archive whose CpkItocH is EMPTY declares row_len 0 (STG0019 ships
    # that way). Adding the first row there has to establish the row length
    # from the row itself, or the table stays 0 x 0 and the reader sees no
    # entry -- which is exactly how "id 3 has no ITOC entry" happened.
    new_row_len = row_len
    if rows:
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            raise SystemExit("sub-@UTF rows differ in length: %s" % sorted(widths))
        w = widths.pop()
        if row_len and w != row_len:
            raise SystemExit("row length %d does not match the table's %d" % (w, row_len))
        new_row_len = w
    delta = new_row_len * len(rows) - (rend - rstart)
    out = bytearray(blob[:rstart]) + b"".join(rows) + blob[rend:]
    struct.pack_into(">I", out, 4, size + delta)
    struct.pack_into(">I", out, d + 4, str_off + delta)
    struct.pack_into(">I", out, d + 8, data_off + delta)
    struct.pack_into(">H", out, d + 18, new_row_len)
    struct.pack_into(">I", out, d + 20, len(rows))
    return bytes(out)


def _build_datah(rows):
    """A correct, freshly built CpkItocH sub-@UTF holding `rows`.

    Some archives (STG0019) ship an EMPTY CpkItocH whose schema is a
    placeholder: row_len 0, the ID column flagged STORAGE_ZERO and the other
    two columns all-zero bytes. No row can be inserted into that, so when a
    member outgrows DataL's 16-bit sizes we replace the whole table with one
    built to the same shape the populated archives use (per-row ID u16,
    FileSize u32, ExtractSize u32; string blob identical to CpkItocL's but
    naming CpkItocH).
    """
    strings = b"".join((b"<NULL>", NUL, b"CpkItocH", NUL, b"ID", NUL,
                        b"FileSize", NUL, b"ExtractSize", NUL))
    name_off, id_off, fs_off, es_off = 7, 16, 19, 28
    schema = (struct.pack(">BI", 0x52, id_off)
              + struct.pack(">BI", 0x54, fs_off)
              + struct.pack(">BI", 0x54, es_off))
    row_len = 10
    rows_off = 24 + len(schema)
    body = b"".join(rows)
    str_off = rows_off + len(body)
    data_off = str_off + len(strings)
    head = struct.pack(">IIIIHHI", rows_off, str_off, data_off, name_off,
                       3, row_len, len(rows))
    blob = head + schema + body + strings
    return b"@UTF" + struct.pack(">I", len(blob)) + blob


def _datah_is_usable(dh):
    """True when an existing CpkItocH can take another row."""
    if not dh:
        return False
    try:
        sub = UTFTable(dh, 0)
        if sub.n_rows == 0:
            return False
        for col, want in (("ID", 0x02), ("FileSize", 0x04), ("ExtractSize", 0x04)):
            if sub.column_type(col) != want:
                return False
        return all((0, c) in sub.field_offset for c in ("ID", "FileSize", "ExtractSize"))
    except Exception:
        return False

def _move_to_datah(buf, cpk, fid, content=None):
    """Move one member's size row from CpkItocL (u16) to CpkItocH (u32),
    rewriting the ITOC in place. The chunk grows by 4 bytes into the padding
    before `content` (the current ContentOffset, which build() may have
    moved forward)."""
    import bisect
    itoc_off = cpk._h("ItocOffset")
    if content is None:
        content = cpk._h("ContentOffset")
    base = itoc_off + 0x10
    parent = UTFTable(buf, base)
    dl, dh = parent.get(0, "DataL"), parent.get(0, "DataH")
    if not dl:
        raise SystemExit("ITOC lacks DataL; cannot move id %d" % fid)
    subL = UTFTable(dl, 0)
    rl = [r for r in range(subL.n_rows) if subL.get(r, "ID") == fid]
    if len(rl) != 1:
        raise SystemExit("id %d not exactly once in DataL" % fid)
    fs, es = subL.get(rl[0], "FileSize"), subL.get(rl[0], "ExtractSize")
    new_row = struct.pack(">HII", fid, fs, es)
    newL = _rows_edit(dl, lambda rows: [r for i, r in enumerate(rows) if i != rl[0]])

    def add(rows):
        ids = [struct.unpack_from(">H", r, 0)[0] for r in rows]
        i = bisect.bisect(ids, fid)
        return rows[:i] + [new_row] + rows[i:]
    if _datah_is_usable(dh):
        subH = UTFTable(dh, 0)
        for col, want in (("ID", 0x02), ("FileSize", 0x04), ("ExtractSize", 0x04)):
            if subH.column_type(col) != want:
                raise SystemExit("unexpected CpkItocH schema (%s)" % col)
        newH = _rows_edit(dh, add)
    else:
        d2 = 8
        n_rows_h = struct.unpack_from(">I", dh, d2 + 20)[0] if dh else 0
        if n_rows_h:
            raise SystemExit("CpkItocH has %d rows but is unreadable" % n_rows_h)
        newH = _build_datah(add([]))

    d = base + 8
    data_off = struct.unpack_from(">I", buf, d + 8)[0]
    data_abs = d + data_off
    old_end = base + 8 + parent.size
    new_data = newL + newH
    delta = len(new_data) - (old_end - data_abs)
    pad = content - (data_abs + len(new_data))
    if pad < 0:
        raise SystemExit("ITOC would overrun ContentOffset moving id %d" % fid)
    if any(buf[old_end:content]):
        raise ValueError('ITOC expansion would overwrite nonzero unknown padding')
    buf[data_abs:content] = new_data + b"\0" * pad
    struct.pack_into(">I", buf, base + 4, parent.size + delta)          # @UTF size
    csz = struct.unpack_from("<I", buf, itoc_off + 8)[0]                # chunk size, LE
    struct.pack_into("<I", buf, itoc_off + 8, csz + delta)
    parent.patch(buf, 0, "FilesL", parent.get(0, "FilesL") - 1)
    parent.patch(buf, 0, "FilesH", parent.get(0, "FilesH") + 1)
    oL = parent.field_offset[(0, "DataL")]
    struct.pack_into(">II", buf, oL, 0, len(newL))
    oH = parent.field_offset[(0, "DataH")]
    struct.pack_into(">II", buf, oH, len(newL), len(newH))
    try:                                    # header ItocSize, where present
        old = UTFTable(buf, 0x10).get(0, 'ItocSize')
        if old:
            cpk.header.patch(buf, 0, "ItocSize", old + delta)
    except KeyError:
        raise ValueError('cannot update ItocSize')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--replace", nargs="+", default=[], metavar="ID=FILE")
    ap.add_argument('--apply', action='store_true', help='write after reviewing the default dry run')
    ap.add_argument('--compress', action='store_true', help='store replacements CRILAYLA-compressed')
    a = ap.parse_args(argv)

    reps = {}
    for item in a.replace:
        if "=" not in item:
            raise SystemExit("--replace wants ID=FILE, got %r" % item)
        k, v = item.split("=", 1)
        if int(k) in reps:
            raise SystemExit('duplicate replacement ID: ' + k)
        reps[int(k)] = v

    with CPK(a.src) as cpk:
        ids = {e['id'] for e in cpk.files}
        members = len(cpk.files)
    unknown = set(reps) - ids
    if unknown:
        raise SystemExit('unknown replacement IDs: %s' % sorted(unknown))
    for fid, path in reps.items():
        print('replace member %d with %s (%d bytes)' % (fid, path, Path(path).stat().st_size))
    if not a.apply:
        print('DRY RUN: %d members, %d replacements -> %s; pass --apply to write' % (members, len(reps), a.dst))
        return 0

    n, size = build(a.src, a.dst, reps, compress=a.compress)
    from tools.verify_archives import compare
    checked = compare(a.src, a.dst, {fid: Path(path).read_bytes() for fid, path in reps.items()})
    if not reps and not checked['byte_identical']:
        raise SystemExit('no-op output differs from source; not accepted')
    print("%d members, %d replaced -> %s (%d bytes)"
          % (n, len(reps), a.dst, size))
    print('Independent readback passed; %d untouched members preserved. Runtime unverified.' %
          checked['untouched_members_verified'])
    return 0


if __name__ == "__main__":
    sys.exit(main())
