"""Tengoku-only proportional advance hook. No Jigoku addresses or RAM globals.

The branch owns a temporary stack frame and returns without changing LR.
Width 32 retains the original pitch; other widths scale the live quad width,
as in Z3.1. All touched GPRs, CR and f10 are restored; only f13 is the result.
"""
import struct
from tools.common import sha256

ELF_SHA256 = '2f43cfc45bcc68de6605bd46c1539830370a330cc1fd97db229379ea6524fac6'
SITE = 0x147dc
ORIGINAL = 0xc1a10094
CELLS = 4480


def branch(source, target):
    delta = target-source
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError('branch out of range/alignment')
    return 0x48000000 | (delta & 0x3fffffc)


def stub(table_va, stub_va):
    words, labels, fixups = [], {}, []
    def emit(w): words.append(w)
    def d(op, reg, base, off): emit(op | reg << 21 | base << 16 | (off & 0xffff))
    def cond(op, label): fixups.append((len(words), op, label)); emit(0)
    # 112-byte aligned frame; caller's stack values remain above it.
    d(0xf8000001,1,1,-0x70)  # stdu r1,-0x70(r1)
    d(0xf8000000,0,1,0x10)
    d(0xf8000000,9,1,0x18)
    emit(0x7c000026)  # mfcr r0
    d(0x90000000,0,1,0x20)
    d(0xd8000000,10,1,0x28)  # stfd f10
    d(0xa0000000,0,1,0x132)  # caller cell index
    emit(0x28000000 | CELLS)  # cmplwi r0,4480
    cond(0x40800000,'original')  # bge: never read beyond table
    d(0x3c000000,9,0,table_va >> 16)
    emit(0x60000000 | 9 << 21 | 9 << 16 | (table_va & 0xffff))
    emit(0x7c0000ae | 9 << 16)  # lbzx r0,r9,r0
    emit(0x2c000020)  # cmpwi r0,32
    cond(0x41820000,'original')
    d(0xf8000000,0,1,0x40)
    d(0xc8000000,13,1,0x40)
    emit(0xfc00069c | 13 << 21 | 13 << 11)  # fcfid
    emit(0xfc000018 | 13 << 21 | 13 << 11)  # frsp
    d(0xc0000000,10,1,0x10c)  # caller quad width, not pitch
    emit(0xec000032 | 13 << 21 | 13 << 16 | 10 << 6)
    d(0x3c000000,9,0,0x3d00)  # float 1/32
    d(0x90000000,9,1,0x40)
    d(0xc0000000,10,1,0x40)
    emit(0xec000032 | 13 << 21 | 13 << 16 | 10 << 6)
    cond(0x48000000,'restore')
    labels['original'] = len(words)
    d(0xc0000000,13,1,0x104)  # original lfs f13,0x94(caller r1)
    labels['restore'] = len(words)
    d(0xc8000000,10,1,0x28)
    d(0x80000000,0,1,0x20)
    emit(0x7c0ff120)  # mtcrf 255,r0
    d(0xe8000000,9,1,0x18)
    d(0xe8000000,0,1,0x10)
    d(0x38000000,1,1,0x70)
    emit(branch(stub_va+4*len(words), SITE+4))
    for i, op, label in fixups:
        delta = 4*(labels[label]-i)
        words[i] = op | (delta & (0x3fffffc if op == 0x48000000 else 0xfffc))
    return b''.join(struct.pack('>I', w) for w in words)


def patch(elf, widths):
    if sha256(elf) != ELF_SHA256:
        raise ValueError('unverified Tengoku ELF baseline')
    phoff = struct.unpack_from('>Q',elf,32)[0]
    first = struct.unpack_from('>IIQQQQQQ',elf,phoff)
    second = struct.unpack_from('>IIQQQQQQ',elf,phoff+56)
    if first[:5] != (1,0x400005,0,0x10000,0x10000) or first[5] != first[6]:
        raise ValueError('unexpected executable load segment')
    gap_start, gap_end = first[5], second[2]
    table_off = (gap_start+15) & ~15
    stub_off = (table_off+CELLS+15) & ~15
    table = bytearray([32]*CELLS)
    for cell, width in widths.items():
        if not 0 <= cell < CELLS or not 1 <= width <= 31:
            raise ValueError('invalid narrowed cell width')
        table[cell] = width
    code = stub(table_off+first[3],stub_off+first[3])
    end = stub_off+len(code)
    if end > gap_end or any(elf[gap_start:gap_end]):
        raise ValueError('executable gap is occupied or too small')
    if first[3]+end > second[3]:
        raise ValueError('load segment overlap')
    site_off = SITE-first[3]
    if struct.unpack_from('>I',elf,site_off)[0] != ORIGINAL:
        raise ValueError('unexpected spacing instruction')
    patched = bytearray(elf)
    patched[table_off:table_off+CELLS] = table
    patched[stub_off:end] = code
    struct.pack_into('>I',patched,site_off,branch(SITE,stub_off+first[3]))
    struct.pack_into('>QQ',patched,phoff+32,end,end)
    ranges = [(table_off,table_off+CELLS),(stub_off,end),(site_off,site_off+4),(phoff+32,phoff+48)]
    restored = bytearray(patched)
    for start,stop in ranges: restored[start:stop] = elf[start:stop]
    if restored != elf: raise ValueError('unrelated executable bytes changed')
    return bytes(patched), {'baseline_elf_sha256':sha256(elf), 'output_sha256':sha256(patched),
        'hook_va':SITE,'table_va':table_off+first[3],'stub_va':stub_off+first[3],
        'modified_file_ranges':ranges,'narrowed_cells':len(widths),
        'preserved_cells':CELLS-len(widths),'gap_bytes':gap_end-gap_start,
        'runtime_verified':False}
