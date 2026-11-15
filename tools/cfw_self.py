"""Validate a PSL1GHT disc fake-SELF while preserving every ELF byte.

Container layout: ps3dev/PSL1GHT f649a08f, tools/fself. Application identity
and capabilities come from the user's pinned Tengoku original SELF. This
does not create a retail signature or establish physical-console compatibility.
"""
import hashlib
import struct

PH = struct.Struct('>IIQQQQQQ')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def span(data, offset, count):
    need(0 <= offset <= len(data) and 0 <= count <= len(data)-offset,
         'Container range outside file')
    return data[offset:offset+count]


def u64(data, offset):
    return struct.unpack('>Q', span(data, offset, 8))[0]


def program_headers(elf):
    need(span(elf, 0, 6) == b'\x7fELF\x02\x02', 'Expected big-endian ELF64')
    need(struct.unpack('>HH', span(elf, 16, 4)) == (2, 21), 'Expected PPU executable')
    ehsize, size, count = struct.unpack('>HHH', span(elf, 52, 6))
    offset = u64(elf, 32)
    need(ehsize == 64 and size == PH.size and 0 < count < 64, 'Invalid ELF headers')
    raw = span(elf, offset, size*count)
    rows = [PH.unpack_from(raw, i*size) for i in range(count)]
    loads = []
    for kind, flags, off, va, pa, filesz, memsz, align in rows:
        span(elf, off, filesz)
        if kind != 1 or not memsz:
            continue
        need(memsz >= filesz and align > 0 and align & (align-1) == 0,
             'Invalid LOAD size/alignment')
        need(off % align == va % align, 'Misaligned LOAD')
        need(flags & 3 != 3, 'Writable/executable LOAD')
        need(all(va+memsz <= a or va >= z for a, z in loads), 'Overlapping LOADs')
        loads.append((va, va+memsz))
    return offset, rows


def controls(data):
    need(span(data, 0, 4) == b'SCE\0', 'Expected SELF')
    pos, length = u64(data, 0x58), u64(data, 0x60)
    span(data, pos, length)
    end, result = pos+length, {}
    while pos < end:
        kind, size, more = struct.unpack('>IIQ', span(data, pos, 16))
        need(size >= 16 and pos+size <= end and kind not in result,
             'Invalid SELF control chain')
        need(more in (0, 1) and bool(more) == (pos+size < end), 'Invalid control continuation')
        result[kind] = (pos, size)
        pos += size
    need(pos == end and 1 in result and result[1][1] == 48, 'Missing capabilities')
    return result


def application(data):
    return span(data, u64(data, 0x28), 32)


def retain_identity(generated, original):
    controls(original)
    oldapp = application(original)
    need(struct.unpack_from('>I', oldapp, 12)[0] == 4, 'Original is not disc SELF')
    out = bytearray(generated)
    app = u64(out, 0x28)
    span(out, app, 32)
    out[app:app+32] = oldapp
    old, new = controls(original)[1][0]+16, controls(out)[1][0]+16
    out[new:new+32] = span(original, old, 32)
    return bytes(out)


def extract_debug(data):
    """Read the complete uncompressed PSL1GHT payload by its declared extent."""
    need(span(data, 0, 4) == b'SCE\0', 'Expected SELF')
    need(struct.unpack('>IHH', span(data, 4, 8)) == (2, 0x8000, 1),
         'Expected version-2 fake SELF')
    offset, size = u64(data, 16), u64(data, 24)
    need(offset >= 0x70 and offset % 0x80 == 0 and offset+size == len(data),
         'Invalid debug payload extent')
    return span(data, offset, size)


def verify(data, elf, original):
    phoff, headers = program_headers(elf)
    need(extract_debug(data) == elf, 'SELF changed ELF payload')
    payload = u64(data, 16)
    eoff, poff, shoff, soff = [u64(data, i) for i in (0x30, 0x38, 0x40, 0x48)]
    need(span(data, eoff, 64) == elf[:64], 'Embedded ELF header differs')
    need(span(data, poff, len(headers)*PH.size) == span(elf, phoff, len(headers)*PH.size),
         'Embedded program headers differ')
    need(soff+len(headers)*32 <= payload, 'Segment map overlaps payload')
    for i, row in enumerate(headers):
        mapping = struct.unpack('>QQIIII', span(data, soff+i*32, 32))
        need(mapping == (payload+row[2], row[5], 1, 0, 0, 2 if row[0] == 1 else 0),
             'SELF segment mapping differs')
    section_offset = u64(elf, 40)
    section_size, section_count = struct.unpack('>HH', span(elf, 58, 4))
    need(shoff == payload+section_offset, 'SELF section-table offset differs')
    need(span(data, shoff, section_size*section_count) ==
         span(elf, section_offset, section_size*section_count), 'Section headers differ')
    need(application(data) == application(original), 'Application identity differs')
    need(struct.unpack_from('>I', application(data), 12)[0] == 4, 'Not disc application')
    c, old = controls(data), controls(original)
    need(span(data, c[1][0]+16, 32) == span(original, old[1][0]+16, 32), 'Capabilities differ')
    need(2 in c and c[2][1] == 64, 'Missing executable digest')
    need(span(data, c[2][0]+36, 20) == hashlib.sha1(elf).digest(), 'Executable digest differs')
    version = u64(data, 0x50)
    need(struct.unpack('>III', span(data, version, 12)) == (1, 0, 16),
         'Unexpected SCE version record')
    return dict(format='CFW fake SELF; not retail-signed', payload_byte_identical=True,
                payload_sha256=hashlib.sha256(elf).hexdigest(), program_segments=len(headers),
                active_loads=sum(r[0] == 1 and r[6] > 0 for r in headers),
                original_application_and_capabilities=True, all_segment_mappings_verified=True,
                no_writable_executable_load=True, hardware_verified=False)
