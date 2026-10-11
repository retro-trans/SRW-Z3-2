"""Draw-time UI text hook for Tengoku (phase 1: exact match). See docs/UI_HOOK.md.

The string drawer at VA 0x14158 reaches its join point 0x141a0 with r31 =
the cp932 string for both callers that pass cp932 (r7 = 1) and callers that
pass UTF-8 (r7 = 0, converted by the game at 0x13b38 into the text state
buffer). `hook()` replaces `lfs f0,-0x7f1c(r2)` at 0x141a0 with a branch to
a stub in the free RX gap after the VWF stub. The stub hashes the string the
way the drawer will read it, looks it up in an open-addressing table at
VA 0xF00000, confirms with a full byte compare and, on a hit, points r31 at
the English. It then replays the displaced `lfs` and returns to 0x141a4.
The game's own strings never change.

The table lives in the read-write data LOAD (PH1), extended past the end of
.bss ("layout B" of work/tengoku/research/eboot_hook.md): file zero-filled
up to VA 0xF00000, table appended, the non-loaded section tail and section
header table moved behind it. PH0 grows by the stub; PH2-4 are untouched.

    python -m tools.ui_hook canary --out work/output/scratch/<dir>
    python -m tools.ui_hook validate-converter [--limit N]
    python -m tools.ui_hook liveness              (needs Capstone, Python 3.8)

`hook(executable, entries)` -> (bytes, report). Entries:
    {'key': bytes, 'english': bytes, 'id': str}
`key` is exactly what r31 points at (cp932; for UTF-8 sources use
`utf8_key`), `english` is already-encoded drawer bytes. Neither may hold a
NUL except as the operand of a 0x30..0x39 escape ('1'+0x00 closes colour);
both must be exactly one drawer string (see `extent`).
"""
import argparse
import functools
import json
import struct
from pathlib import Path

from tools.common import ROOT, sha256
from tools import ppc_exec

# ---------------------------------------------------------------------------
# Pinned Tengoku facts (program ELF from tools/self_elf.py, BLJS10299).

TOC = 0x99fe70
SITE = 0x141a0                 # lfs f0,-0x7f1c(r2): join point, r31 = cp932 string
ORIGINAL = 0xc00280e4
BACK = 0x141a4
VWF_SITE = 0x147dc             # tools/vwf.py branch; must already be installed
GUARDS = {
    0x14158: 0x2f870000,       # cmpwi cr7,r7,0      (drawer entry: r7 = 0 means UTF-8)
    0x14168: 0x7c691b78,       # mr r9,r3
    0x14194: 0x419e0800,       # beq cr7,0x14994     (UTF-8 path)
    0x14198: 0x7d3f4b78,       # mr r31,r9           (cp932 path)
    0x1419c: 0x83c280c4,       # lwz r30,-0x7f3c(r2) (text state)
    0x14248: 0x7be90020,       # clrldi r9,r31,32    (glyph loop reads r31)
    0x1424c: 0x3bff0001,       # addi r31,r31,1
    0x14270: 0x2b80000b,       # cmplwi cr7,r0,0xb   (escape codes 0x2e..0x39)
    0x14994: 0x78630020,       # clrldi r3,r3,32
    0x14998: 0x4bfff1a1,       # bl 0x13b38          (UTF-8 -> cp932)
    0x1499c: 0x83c280c4,       # lwz r30,-0x7f3c(r2)
    0x149a0: 0x3bfe00b8,       # addi r31,r30,0xb8
    0x149a4: 0x4bfff7fc,       # b 0x141a0
}
EXT_VA = 0xF00000
MAGIC = b'UIH1'
TABLE_VERSION = 1
HEADER = 32
SLOT = 16
MIN_SLOTS = 16
MAX_EXTENT = 4096              # strings longer than this (drawer bytes) are a miss
MAX_ENGLISH_EXTENT = 8192      # relocated output may exceed the source-key cap
EXT_STEP = 0x10000             # EXT grows in 64 KiB steps
FRAME = 0x70

# Measured layout of the unfolded program ELF (eboot_hook.md section 3.1).
PH0_BASE = (1, 0x400005, 0, 0x10000, 0x10000)
PH0_ORIGINAL_SIZE = 0x92d988
PH1 = (1, 0x600006, 0x930000, 0x940000, 0x940000, 0xf12f4, 0x5b9b18, 0x10000)
PH_REST = [
    (1, 0x4, 0xa212f4, 0, 0, 0, 0, 0x10000),
    (1, 0x6, 0xa212f4, 0, 0, 0, 0, 0x10000),
    (1, 0x6600006, 0xa212f4, 0, 0, 0, 0, 0x10000),
    (7, 0x4, 0x9937d8, 0x9a37d8, 0x9a37d8, 0x4, 0x1f8, 0x8),
    (0x60000001, 0, 0x92d920, 0x93d920, 0x93d920, 0x28, 0x28, 0x8),
    (0x60000002, 0, 0x92d948, 0x93d948, 0x93d948, 0x40, 0x40, 0x4),
]
E_SHOFF = 0xa24720
SHNUM = 32
FILE_SIZE = 0xa24f20
TAIL = 0xa212f4                # end of PH1 file data = first non-loaded byte
BSS_END = 0xef9b18

# UTF-8 -> cp932 converter (0x13b38) and what it reads.
CONVERTER = (0x13b38, 0x13d5c)
CONVERTER_CODE_SHA256 = '188ed581bd4d82075ea80c21f8005d6f54d30572aa2779f4187b08435fb4a866'
UTAB_DISP, STATE_DISP = -0x7f28, -0x7f3c
UTAB_VA = 0x82db00
UTAB_SIZE = 0x100 + 0x20000
STATE_VA = 0xa31378
MBSTOWCS, UTF8STOUTF16S, STRLEN = 0x687034, 0x77ad40, 0x68a2ac

PH = struct.Struct('>IIQQQQQQ')
SH = struct.Struct('>IIQQQQIIQQ')
PREPARED = ROOT / 'work/tengoku/prepared/EBOOT.elf'
INVENTORY = ROOT / 'work/tengoku/research/eboot_strings.json'
SCRATCH = ROOT / 'work/output/scratch'


# ---------------------------------------------------------------------------
# Drawer string grammar (0x14248..0x14290): what the glyph loop consumes.

def extent(buf, start=0, cap=MAX_EXTENT):
    """Bytes the drawer reads from `start` before it stops, or None if > cap.

    0x00 ends the string; 0x0a and 0x2e are one-byte line breaks; 0x2f ends
    drawing (counted); 0x30..0x39 take one operand byte (any value, NUL
    included); every other byte is the lead of a two-byte character.
    Raises ValueError if the buffer ends mid-string.
    """
    i = start
    try:
        while True:
            if i - start >= cap:
                return None
            c = buf[i]
            if c == 0:
                return i - start
            i += 1
            if c in (0x0a, 0x2e):
                continue
            if c == 0x2f:
                return i - start
            buf[i]                      # operand / trail byte must exist
            i += 1
    except IndexError:
        raise ValueError('string runs past the end of its buffer')


def tokens(data):
    """Drawer tokens of a well-formed string (no terminator)."""
    out, i = [], 0
    while i < len(data):
        c = data[i]
        if c in (0x0a, 0x2e, 0x2f):
            out.append(data[i:i + 1]); i += 1
        else:
            out.append(data[i:i + 2]); i += 2
    return out


def fnv1a(data):
    h = 0x811c9dc5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xffffffff
    return h


def _escapes(data):
    return {t for t in tokens(data) if 0x2e <= t[0] <= 0x39}


def check_english(key, english, allow_escapes=False):
    """Problems with an English replacement, as a list of strings."""
    problems = []
    if not english:
        problems.append('empty English')
        return problems
    # A NUL is allowed only as the operand of a 0x30..0x39 escape (the colour
    # close '1'+0x00 that UTF-8 sources produce); anywhere else it ends the
    # string early and the extent check below refuses it.
    try:
        n = extent(english + b'\0', cap=MAX_ENGLISH_EXTENT)
    except ValueError:
        n = -1
    if n != len(english):
        problems.append('English is not one drawer string (odd trailing byte, 0x2f or > %d bytes)' % MAX_ENGLISH_EXTENT)
        return problems
    # The drawer reads every byte outside 0x0a/0x2e..0x39 as the lead of a
    # two-byte cell, so plain ASCII text would pair up into garbage codes.
    bad = [t for t in tokens(english) if len(t) == 2 and not (0x30 <= t[0] <= 0x39 or t[0] >= 0x81)]
    if bad:
        problems.append('two-byte token with lead %#04x (single-byte ASCII is not drawable)' % bad[0][0])
    extra = _escapes(english) - _escapes(key)
    if extra and not allow_escapes:
        problems.append('English uses drawer escape codes not present in the key: %s'
                        % ', '.join(sorted(t.hex() for t in extra)))
    return problems


# ---------------------------------------------------------------------------
# Table

def build_table(entries, base=EXT_VA, payloads=()):
    """-> (ext bytes, info). Deterministic; refuses bad or conflicting entries."""
    by_key, ids, merged = {}, set(), 0
    for e in entries:
        key, en, eid = bytes(e['key']), bytes(e['english']), str(e['id'])
        if eid in ids:
            raise ValueError('duplicate entry id %r' % eid)
        ids.add(eid)
        if not key:
            raise ValueError('%s: empty key' % eid)
        try:
            n = extent(key + b'\0')
        except ValueError:
            n = None
        if n != len(key):
            raise ValueError('%s: key is not exactly one drawer string (len %d, drawer reads %r)'
                             % (eid, len(key), n))
        problems = check_english(key, en, e.get('allow_escapes', False))
        if problems:
            raise ValueError('%s: %s' % (eid, '; '.join(problems)))
        if key in by_key:
            if by_key[key][1] != en:
                raise ValueError('%s: key also used by %s with different English' % (eid, by_key[key][2]))
            merged += 1
            continue
        by_key[key] = (key, en, eid)
    rows = list(by_key.values())
    slots = MIN_SLOTS
    while slots < 2 * len(rows):
        slots *= 2
    mask = slots - 1
    slots_va = base + HEADER
    strings_at = HEADER + SLOT * slots
    blob = bytearray()
    key_va, en_va = {}, {}
    for key, en, _ in rows:
        key_va[key] = base + strings_at + len(blob)
        blob += key + b'\0'
    for _, en, _ in rows:
        if en not in en_va:
            en_va[en] = base + strings_at + len(blob)
            blob += en + b'\0'
    table = [None] * slots
    probes, hashes = [], {}
    for key, en, eid in rows:
        h = fnv1a(key)
        hashes.setdefault(h, []).append(eid)
        i, k = h & mask, 0
        while table[i] is not None:
            i, k = (i + 1) & mask, k + 1
        table[i] = (h, key_va[key], en_va[en], len(key))
        probes.append(k)
    payload_vas = {}
    for eid, raw in payloads:
        if eid in payload_vas or not raw or raw[-1] != 0:
            raise ValueError('Invalid or duplicate runtime payload: '+eid)
        # Relocated runtime payloads can include float scratch, not just
        # byte strings. Keep each address naturally aligned for PPC loads.
        blob += bytes(-(strings_at+len(blob)) % 16)
        payload_vas[eid] = base + strings_at + len(blob)
        blob += raw
    used = strings_at + len(blob)
    size = max(EXT_STEP, -(-used // EXT_STEP) * EXT_STEP)
    out = bytearray(size)
    struct.pack_into('>4sIIIIIII', out, 0, MAGIC, TABLE_VERSION, mask, slots_va, 0, 0, 0, 0)
    for i, s in enumerate(table):
        if s is not None:
            struct.pack_into('>IIIHH', out, HEADER + SLOT * i, s[0], s[1], s[2], s[3], 0)
    out[strings_at:used] = blob
    info = {'entries': len(rows), 'duplicates_merged': merged, 'slots': slots,
            'load_factor': round(len(rows) / slots, 4), 'max_probe': max(probes or [0]),
            'displaced_entries': sum(1 for p in probes if p),
            'hash32_collisions': sum(len(v) - 1 for v in hashes.values() if len(v) > 1),
            'unique_english': len(en_va), 'used_bytes': used, 'ext_size': size,
            'headroom_bytes': size - used, 'longest_key': max((len(r[0]) for r in rows), default=0),
            'payload_vas': payload_vas}
    return bytes(out), info


def lookup(read, string_va):
    """Independent mirror of the stub's lookup. read(va, n) -> bytes.
    Returns the English VA or None."""
    def u32(va): return struct.unpack('>I', read(va, 4))[0]
    if read(EXT_VA, 4) != MAGIC:
        return None
    # Reconstruct the drawn extent one byte at a time, as the stub does.
    data, p = bytearray(), string_va
    while True:
        if p - string_va >= MAX_EXTENT:
            return None
        c = read(p, 1)[0]
        if c == 0:
            break
        data.append(c); p += 1
        if c in (0x0a, 0x2e):
            continue
        if c == 0x2f:
            break
        data += read(p, 1); p += 1
    if not data:
        return None
    h, mask, slots_va = fnv1a(data), u32(EXT_VA + 8), u32(EXT_VA + 12)
    i = h & mask
    while True:
        sh, kva, eva, klen, _f = struct.unpack('>IIIHH', read(slots_va + SLOT * i, SLOT))
        if kva == 0:
            return None
        if sh == h and klen == len(data) and read(kva, klen) == bytes(data):
            return eva
        i = (i + 1) & mask


# ---------------------------------------------------------------------------
# Stub assembler (only the forms used here)

def _d(op, rt, ra, imm): return op << 26 | rt << 21 | ra << 16 | (imm & 0xffff)
def _ds(op, rs, ra, ds, sub): return op << 26 | rs << 21 | ra << 16 | (ds & 0xfffc) | sub
def _x(rs, ra, rb, xo, rc=0): return 31 << 26 | rs << 21 | ra << 16 | rb << 11 | xo << 1 | rc
def _cmp(op, bf, l, ra, v): return op << 26 | bf << 23 | l << 21 | ra << 16 | (v & 0xffff)
def _cmpx(xo, bf, l, ra, rb): return 31 << 26 | bf << 23 | l << 21 | ra << 16 | rb << 11 | xo << 1


def branch(source, target):
    delta = target - source
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError('branch out of range/alignment')
    return 0x48000000 | (delta & 0x3fffffc)


def stub(stub_va, ext_va=EXT_VA, back=BACK, replay=ORIGINAL):
    """Lookup stub. Clobbers nothing but r31 (on a hit) and its own frame."""
    w, labels, fix = [], {}, []
    def e(x): w.append(x)
    def bc(bo, bi, label): fix.append((len(w), 'bc', bo, bi, label)); e(0)
    def b(label): fix.append((len(w), 'b', 0, 0, label)); e(0)
    def here(name): labels[name] = len(w)
    beq, bne, bge, blt = (12, 2), (4, 2), (4, 0), (12, 0)   # (BO, bit in cr0)
    e(_ds(62, 1, 1, -FRAME, 1))                  # stdu r1,-0x70(r1)
    e(_ds(62, 0, 1, 0x10, 0))                    # std r0,0x10(r1)
    for k, reg in enumerate(range(3, 13)):
        e(_ds(62, reg, 1, 0x18 + 8 * k, 0))      # std r3..r12
    e(0x7c000026)                                # mfcr r0
    e(_d(36, 0, 1, 0x68))                        # stw r0,0x68(r1)
    e(30 << 26 | 31 << 21 | 3 << 16 | (1 << 5))  # clrldi r3,r31,32
    e(_d(15, 12, 0, ext_va >> 16))               # lis r12,EXT@h
    e(_d(24, 12, 12, ext_va & 0xffff))           # ori r12,r12,EXT@l
    e(_d(32, 0, 12, 0))                          # lwz r0,0(r12)
    magic = struct.unpack('>I', MAGIC)[0]
    e(_d(15, 11, 0, magic >> 16))                # lis r11,'UI'
    e(_d(24, 11, 11, magic & 0xffff))            # ori r11,r11,'H1'
    e(_cmpx(32, 0, 0, 0, 11))                    # cmplw r0,r11
    bc(*bne, 'out')
    e(_d(15, 5, 0, 0x811c))                      # lis r5,0x811c
    e(_d(24, 5, 5, 0x9dc5))                      # ori r5,r5,0x9dc5   FNV offset basis
    e(_d(15, 6, 0, 0x0100))                      # lis r6,0x0100
    e(_d(24, 6, 6, 0x0193))                      # ori r6,r6,0x0193   FNV prime
    e(_x(3, 4, 3, 444))                          # mr r4,r3
    e(_d(14, 10, 3, MAX_EXTENT))                 # addi r10,r3,MAX_EXTENT
    here('loop')
    e(_cmpx(32, 0, 1, 4, 10))                    # cmpld r4,r10
    bc(*bge, 'out')                              # too long: miss
    e(_d(34, 7, 4, 0))                           # lbz r7,0(r4)
    e(_cmp(11, 0, 0, 7, 0))                      # cmpwi r7,0
    bc(*beq, 'hashed')
    e(_x(5, 5, 7, 316))                          # xor r5,r5,r7
    e(_x(5, 5, 6, 235))                          # mullw r5,r5,r6
    e(_d(14, 4, 4, 1))                           # addi r4,r4,1
    e(_cmp(11, 0, 0, 7, 0x0a))
    bc(*beq, 'loop')                             # LF: one byte
    e(_cmp(11, 0, 0, 7, 0x2e))
    bc(*beq, 'loop')                             # '.': one-byte break
    e(_cmp(11, 0, 0, 7, 0x2f))
    bc(*beq, 'hashed')                           # '/': drawer stops after it
    e(_d(34, 7, 4, 0))                           # lbz r7,0(r4)  trail / operand
    e(_x(5, 5, 7, 316))
    e(_x(5, 5, 6, 235))
    e(_d(14, 4, 4, 1))
    b('loop')
    here('hashed')
    e(31 << 26 | 8 << 21 | 3 << 16 | 4 << 11 | 40 << 1)   # subf r8,r3,r4  (extent length)
    e(_cmp(11, 0, 0, 8, 0))                      # cmpwi r8,0
    bc(*beq, 'out')                              # empty string
    e(_d(32, 11, 12, 8))                         # lwz r11,8(r12)   slot mask
    e(_d(32, 10, 12, 12))                        # lwz r10,12(r12)  slots VA
    e(_x(5, 9, 11, 28))                          # and r9,r5,r11
    here('probe')
    e(21 << 26 | 9 << 21 | 12 << 16 | 4 << 11 | 0 << 6 | 27 << 1)  # slwi r12,r9,4
    e(31 << 26 | 12 << 21 | 12 << 16 | 10 << 11 | 266 << 1)       # add r12,r12,r10
    e(_d(32, 4, 12, 4))                          # lwz r4,4(r12)    key VA
    e(_cmp(11, 0, 0, 4, 0))
    bc(*beq, 'out')                              # empty slot: miss
    e(_d(32, 7, 12, 0))                          # lwz r7,0(r12)    hash
    e(_cmpx(32, 0, 0, 7, 5))                     # cmplw r7,r5
    bc(*bne, 'next')
    e(_d(40, 7, 12, 12))                         # lhz r7,12(r12)   key length
    e(_cmpx(32, 0, 0, 7, 8))                     # cmplw r7,r8
    bc(*bne, 'next')
    e(_d(14, 6, 0, 0))                           # li r6,0
    here('cmp')
    e(_x(0, 3, 6, 87))                           # lbzx r0,r3,r6
    e(_x(7, 4, 6, 87))                           # lbzx r7,r4,r6
    e(_cmpx(32, 0, 0, 0, 7))                     # cmplw r0,r7
    bc(*bne, 'next')
    e(_d(14, 6, 6, 1))                           # addi r6,r6,1
    e(_cmpx(32, 0, 0, 6, 8))                     # cmplw r6,r8
    bc(*blt, 'cmp')
    e(_d(32, 31, 12, 8))                         # lwz r31,8(r12)   hit: English
    b('out')
    here('next')
    e(_d(14, 9, 9, 1))                           # addi r9,r9,1
    e(_x(9, 9, 11, 28))                          # and r9,r9,r11
    b('probe')
    here('out')
    for k, reg in enumerate(range(3, 13)):
        e(_ds(58, reg, 1, 0x18 + 8 * k, 0))      # ld r3..r12
    e(_d(32, 0, 1, 0x68))                        # lwz r0,0x68(r1)
    e(0x7c0ff120)                                # mtcrf 0xff,r0
    e(_ds(58, 0, 1, 0x10, 0))                    # ld r0,0x10(r1)
    e(_d(14, 1, 1, FRAME))                       # addi r1,r1,0x70
    e(replay)                                    # lfs f0,-0x7f1c(r2)  (displaced)
    e(branch(stub_va + 4 * len(w), back))        # b 0x141a4
    for i, kind, bo, bi, label in fix:
        delta = 4 * (labels[label] - i)
        if kind == 'b':
            w[i] = 0x48000000 | (delta & 0x3fffffc)
        else:
            if not -0x8000 <= delta < 0x8000:
                raise ValueError('conditional branch out of range')
            w[i] = 16 << 26 | bo << 21 | bi << 16 | (delta & 0xfffc)
    return b''.join(struct.pack('>I', x) for x in w)


# ---------------------------------------------------------------------------
# ELF layout

def _headers(elf):
    if elf[:4] != b'\x7fELF' or elf[4] != 2 or elf[5] != 2:
        raise ValueError('not a big-endian ELF64')
    phoff, shoff = struct.unpack_from('>QQ', elf, 32)
    phsz, phn, shsz, shn, shstr = struct.unpack_from('>HHHHH', elf, 54)
    if phoff != 64 or phsz != PH.size or phn != 8 or shsz != SH.size:
        raise ValueError('unexpected ELF header table geometry')
    phs = [PH.unpack_from(elf, phoff + i * PH.size) for i in range(phn)]
    shs = [SH.unpack_from(elf, shoff + i * SH.size) for i in range(shn)]
    return phoff, shoff, phs, shs


def measure(elf):
    """Check the input is the measured unfolded layout; return derived numbers."""
    phoff, shoff, phs, shs = _headers(elf)
    bad = []
    if len(elf) != FILE_SIZE: bad.append('file size %#x != %#x' % (len(elf), FILE_SIZE))
    if shoff != E_SHOFF or len(shs) != SHNUM: bad.append('section table %#x/%d' % (shoff, len(shs)))
    p0 = phs[0]
    if p0[:5] != PH0_BASE or p0[5] != p0[6] or p0[7] != 0x10000 or not PH0_ORIGINAL_SIZE <= p0[5] < PH1[2]:
        bad.append('PH0 %r' % (p0,))
    if phs[1] != PH1: bad.append('PH1 %r' % (phs[1],))
    if phs[2:] != PH_REST: bad.append('PH2-7 differ')
    data_end = PH1[2] + PH1[5]
    if data_end != TAIL or PH1[3] + PH1[6] != BSS_END: bad.append('PH1 extents')
    if EXT_VA < BSS_END or EXT_VA % 0x10000: bad.append('EXT_VA not above .bss on a 64K boundary')
    nonalloc = [s for s in shs[1:] if not s[2] & 2]
    if not nonalloc or min(s[4] for s in nonalloc) != TAIL:
        bad.append('non-loaded tail does not start at the end of PH1 data')
    for i, s in enumerate(shs):
        if s[2] & 2 and s[1] != 8 and s[5] and not any(
                p[0] == 1 and p[2] <= s[4] and s[4] + s[5] <= p[2] + p[5] for p in phs[:2]):
            bad.append('allocated section %d outside PH0/PH1' % i)
        if not s[2] & 2 and s[1] != 8 and s[5] and not (TAIL <= s[4] and s[4] + s[5] <= len(elf)):
            bad.append('non-loaded section %d outside the tail' % i)
    if shoff < TAIL or shoff + SHNUM * SH.size != len(elf):
        bad.append('section header table is not the last thing in the tail')
    if bad:
        raise ValueError('refusing: input layout differs from the measured Tengoku ELF: ' + '; '.join(bad))
    return {'phoff': phoff, 'phs': phs, 'shs': shs, 'shoff': shoff, 'data_end': data_end,
            'ext_off': PH1[2] + (EXT_VA - PH1[3])}


def _word(elf, va):
    return struct.unpack_from('>I', elf, va - 0x10000)[0]


def _guards(elf, ph0_size):
    bad = ['%#x: %08x != %08x' % (va, _word(elf, va), want)
           for va, want in sorted(GUARDS.items()) if _word(elf, va) != want]
    if _word(elf, SITE) != ORIGINAL:
        bad.append('hook site %#x already patched (%08x)' % (SITE, _word(elf, SITE)))
    v = _word(elf, VWF_SITE)
    target = VWF_SITE + ppc_exec.sext(v & 0x3fffffc, 26)
    if v >> 26 != 18 or v & 3 or not 0x10000 + PH0_ORIGINAL_SIZE <= target < 0x10000 + ph0_size:
        bad.append('VWF branch missing at %#x (%08x)' % (VWF_SITE, v))
    if bad:
        raise ValueError('refusing: code guards failed: ' + '; '.join(bad))


# ---------------------------------------------------------------------------
# Stub execution check (ppc_exec, no Capstone)

class _Runner:
    """Executes the produced stub against the produced image."""

    def __init__(self, out, stub_va, stub_size):
        _, _, phs, _ = _headers(out)
        self.mem = ppc_exec.Memory()
        p0, p1 = phs[0], phs[1]
        self.mem.map(p0[3], out[p0[2]:p0[2] + p0[5]], writable=False)
        self.ro = self.mem.map(p1[3], out[p1[2]:p1[2] + p1[5]], writable=True)
        self.stack = self.mem.map(0x40000000, bytes(0x2000))
        self.buf = self.mem.map(0x50000000, bytes(MAX_EXTENT + 0x100))
        self.stub_va, self.stub_size = stub_va, stub_size
        self.cache = {}
        self.ext_snapshot = bytes(self.ro)

    def run(self, data, high=0xa5a5a5a5):
        """Draw `data` (bytes as r31 sees them) -> (r31 out, steps). Asserts preservation."""
        self.buf[:] = bytes(len(self.buf))
        self.buf[:len(data)] = data
        for i in range(len(data), min(len(data) + 16, len(self.buf))):
            if i >= len(data) + 2:
                self.buf[i] = 0x88              # junk after the terminator
        self.stack[:] = b'\x5c' * len(self.stack)
        m = ppc_exec.Machine(self.mem)
        m.cache = self.cache
        for i in range(32):
            m.r[i] = (0x1111111100000000 * (i + 1) + i) & ppc_exec.M64
        m.r[1] = 0x40001800
        m.r[2] = TOC
        m.r[31] = (high << 32) | 0x50000000
        m.cr, m.lr, m.ctr, m.ca = 0x9abcdef1, 0x14dead00, 0x7777, 1
        m.f = [float(i) + 0.5 for i in range(32)]
        before = (list(m.r), m.cr, m.lr, m.ctr, m.ca, list(m.f), bytes(self.stack))
        m.pc = self.stub_va
        m.run({BACK}, limit=200000)
        r, cr, lr, ctr, ca, f, stack = before
        changed = [i for i in range(32) if m.r[i] != r[i] and i != 31]
        if changed or (m.cr, m.lr, m.ctr, m.ca) != (cr, lr, ctr, ca):
            raise ValueError('stub changed registers %r / CR/LR/CTR/XER' % changed)
        f0 = struct.unpack('>f', self.mem.read(TOC - 0x7f1c, 4))[0]   # -1.0f in the real image
        if m.f[0] != f0 or m.f[1:] != f[1:]:
            raise ValueError('stub did not replay lfs f0 or changed other FPRs')
        low = 0x1800 - FRAME
        if bytes(self.stack[:low]) != stack[:low] or bytes(self.stack[0x1800:]) != stack[0x1800:]:
            raise ValueError('stub wrote outside its own frame')
        if bytes(self.ro) != self.ext_snapshot:
            raise ValueError('stub wrote into the data segment')
        return m.r[31], m.steps


def check_stub_words(code, stub_va):
    """Decode every word (ppc_exec), check control flow and stores. -> listing."""
    listing, n = [], len(code) // 4
    for k in range(n):
        va = stub_va + 4 * k
        w = struct.unpack_from('>I', code, 4 * k)[0]
        ins = ppc_exec.decode(w, va)
        listing.append((va, w, ins[0]))
        if ins[0] in ('bl', 'bclr', 'bcctr', 'mtspr'):
            raise ValueError('stub contains %s' % ins[0])
        if ins[0] in ('b', 'bc'):
            t = ins[1] if ins[0] == 'b' else ins[3]
            if not (stub_va <= t < stub_va + len(code) or (t == BACK and k == n - 1)):
                raise ValueError('stub branch at %#x leaves the stub (%#x)' % (va, t))
        if ins[0].startswith('st') and ins[2] != 1:
            raise ValueError('stub stores through r%d' % ins[2])
    if struct.unpack_from('>I', code, len(code) - 8)[0] != ORIGINAL:
        raise ValueError('displaced instruction not replayed last')
    try:
        from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
    except ImportError:
        return listing, None
    md = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
    text = ['%x: %s %s' % (i.address, i.mnemonic, i.op_str) for i in md.disasm(code, stub_va)]
    if len(text) != n:
        raise ValueError('Capstone decodes %d of %d stub words' % (len(text), n))
    if not text[-2].endswith('lfs f0, -0x7f1c(r2)') or not text[-1].endswith('b %#x' % BACK):
        raise ValueError('Capstone: stub does not end with the replayed lfs and the return branch')
    return listing, text


# ---------------------------------------------------------------------------
# The patch

def hook(executable, entries, require_srvc=True, execute=512, payloads=()):
    """Install the hook and the folded table. Returns (bytes, report).

    `execute` = how many distinct keys the real stub is executed for
    (ppc_exec, the longest half plus an even sample of the rest); None
    executes all. Every key is always read back by `lookup`.
    """
    elf = bytes(executable)
    lay = measure(elf)
    phoff, phs, shs = lay['phoff'], lay['phs'], lay['shs']
    p0 = phs[0]
    _guards(elf, p0[5])
    stub_off = (p0[5] + 15) & ~15
    stub_va = 0x10000 + stub_off
    code = stub(stub_va)
    stub_end = stub_off + len(code)
    if any(elf[p0[5]:PH1[2]]):
        raise ValueError('refusing: executable gap %#x..%#x is not all zero' % (p0[5], PH1[2]))
    if stub_end > PH1[2] or 0x10000 + stub_end > PH1[3]:
        raise ValueError('stub does not fit the executable gap')
    ext, info = build_table(entries, payloads=payloads)
    data_end, ext_off = lay['data_end'], lay['ext_off']
    ext_end = ext_off + len(ext)
    new_tail = ext_end + (TAIL - ext_end) % 16          # keep offset % 16 of the tail
    delta = new_tail - TAIL
    new_ph1 = PH1[:5] + (ext_end - PH1[2], ext_end - PH1[2], PH1[7])

    out = bytearray(elf[:data_end])
    struct.pack_into('>I', out, SITE - 0x10000, branch(SITE, stub_va))
    out[stub_off:stub_end] = code
    struct.pack_into('>QQ', out, phoff + 32, stub_end, stub_end)
    PH.pack_into(out, phoff + PH.size, *new_ph1)
    struct.pack_into('>Q', out, 40, lay['shoff'] + delta)
    out += bytes(ext_off - data_end)
    out += ext
    out += bytes(new_tail - ext_end)
    out += elf[TAIL:]
    new_shoff = lay['shoff'] + delta
    moved = []
    for i, s in enumerate(shs):
        row = list(s)
        if s[1] != 8 and s[5] and not s[2] & 2:
            row[4] += delta
            moved.append(i)
        SH.pack_into(out, new_shoff + i * SH.size, *row)
    out = bytes(out)

    geo = {'stub_off': stub_off, 'stub_end': stub_end, 'stub_va': stub_va, 'ext_end': ext_end,
           'new_tail': new_tail, 'delta': delta}
    checks = verify(elf, out, entries, geo, require_srvc, execute, payloads)
    h = lambda v: '%#x' % v
    report = {'schema': 1, 'phase': 1, 'input_sha256': sha256(elf), 'output_sha256': sha256(out),
              'site_va': h(SITE), 'displaced_word': '%08x' % ORIGINAL, 'return_va': h(BACK),
              'stub_va': h(stub_va), 'stub_bytes': len(code), 'stub_end_va': h(0x10000 + stub_end),
              'gap_bytes_left': PH1[2] - stub_end,
              'ph0_filesz_memsz': [h(p0[5]), h(stub_end)],
              'ph1_filesz_memsz': [[h(PH1[5]), h(PH1[6])], [h(new_ph1[5]), h(new_ph1[6])]],
              'bss_end_va': h(BSS_END), 'ext_va': h(EXT_VA), 'ext_file_offset': h(ext_off),
              'ext_bytes': len(ext), 'table': info,
              'tail_offset': [h(TAIL), h(new_tail)], 'tail_delta': h(delta),
              'e_shoff': [h(lay['shoff']), h(new_shoff)], 'moved_sections': moved,
              'file_size': [len(elf), len(out)], 'placeholder_loads': 'PH2-4 untouched',
              'verification': checks, 'runtime_verified': False}
    return out, report


def _reader(out, phs, extra=None):
    """read(va, n) over the file image of PH0/PH1, plus optional {base: bytes}."""
    def read(va, n):
        for base, blob in (extra or {}).items():
            if base <= va and va + n <= base + len(blob):
                return blob[va - base:va - base + n]
        for p in phs[:2]:
            if p[3] <= va and va + n <= p[3] + p[5]:
                return out[p[2] + va - p[3]:p[2] + va - p[3] + n]
        raise ValueError('read outside the file image: %#x' % va)
    return read


PROBE_VA = 0x60000000          # where readback places a drawn string (any non-image address)


def verify(elf, out, entries, geo, require_srvc=True, execute=512, payloads=()):
    """Gates. Raises on any failure; returns a summary dict."""
    lay = measure(elf)
    phoff, phs, shs = lay['phoff'], lay['phs'], lay['shs']
    data_end, ext_off = lay['data_end'], lay['ext_off']
    stub_off, stub_end, ext_end = geo['stub_off'], geo['stub_end'], geo['ext_end']
    new_tail, delta = geo['new_tail'], geo['delta']
    # 1. byte isolation: undo the patch ranges, compare with the input
    restored = bytearray(out[:data_end])
    for a, b in ((SITE - 0x10000, SITE - 0x10000 + 4), (stub_off, stub_end),
                 (phoff + 32, phoff + 48), (phoff + PH.size + 32, phoff + PH.size + 48), (40, 48)):
        restored[a:b] = elf[a:b]
    if restored != elf[:data_end]:
        raise ValueError('isolation: bytes changed outside the branch, stub and header fields')
    if any(out[data_end:ext_off]) or any(out[ext_end:new_tail]):
        raise ValueError('isolation: fill is not zero')
    if len(out) != new_tail + len(elf) - TAIL:
        raise ValueError('isolation: unexpected output length')
    expected_ext, _ = build_table(entries, payloads=payloads)
    if out[ext_off:ext_end] != expected_ext:
        raise ValueError('isolation: dictionary/runtime payload bytes differ')
    tail = bytearray(out[new_tail:])
    sh_at = lay['shoff'] - TAIL
    tail[sh_at:sh_at + SHNUM * SH.size] = elf[lay['shoff']:lay['shoff'] + SHNUM * SH.size]
    if bytes(tail) != elf[TAIL:]:
        raise ValueError('isolation: moved tail differs')
    _, nshoff, nphs, nshs = _headers(out)
    if nshoff != lay['shoff'] + delta or nshoff % 8:
        raise ValueError('isolation: e_shoff')
    unpatched = bytearray(out)
    unpatched[SITE - 0x10000:SITE - 0x10000 + 4] = elf[SITE - 0x10000:SITE - 0x10000 + 4]
    for i, (a, b) in enumerate(zip(shs, nshs)):
        want = list(a)
        if a[1] != 8 and a[5] and not a[2] & 2:
            want[4] += delta
        if tuple(want) != b:
            raise ValueError('isolation: section header %d changed unexpectedly' % i)
        if a[1] != 8 and a[5] and unpatched[b[4]:b[4] + b[5]] != elf[a[4]:a[4] + a[5]]:
            raise ValueError('isolation: section %d payload changed' % i)
        if a[8] and a[1] != 8 and b[4] % a[8] != a[4] % a[8]:
            raise ValueError('isolation: section %d alignment' % i)
    if nphs[0] != phs[0][:5] + (stub_end, stub_end, phs[0][7]) or nphs[2:] != phs[2:]:
        raise ValueError('isolation: program headers')
    if nphs[1] != PH1[:5] + (ext_end - PH1[2], ext_end - PH1[2], PH1[7]):
        raise ValueError('isolation: PH1')
    if any((p[1] & 3) == 3 for p in nphs if p[0] == 1 and p[6]):
        raise ValueError('writable+executable LOAD')
    if nphs[1][2] % nphs[1][7] != nphs[1][3] % nphs[1][7] or nphs[0][3] + nphs[0][6] > nphs[1][3]:
        raise ValueError('LOAD congruence/overlap')
    # 2. table readback: an independent lookup over the produced bytes
    keyed = {}
    for e in entries:
        keyed.setdefault(bytes(e['key']), e)
    plain = _reader(out, nphs)
    slots = slot_map(plain)
    if set(slots) != set(keyed):
        raise ValueError('readback: slot array keys differ from the entries')
    def drawn(va):
        n = extent(plain(va, min(MAX_ENGLISH_EXTENT + 2, nphs[1][3] + nphs[1][5] - va)), cap=MAX_ENGLISH_EXTENT)
        return plain(va, n)
    for key, e in keyed.items():
        found = lookup(_reader(out, nphs, {PROBE_VA: key + b'\0\0'}), PROBE_VA)
        if found is None or drawn(found) != bytes(e['english']) or found != slots[key]:
            raise ValueError('readback: %s does not resolve to its English' % e['id'])
    probes = [b'\x82\xa0', b'\x81\x40' * 3, b'1\x00\x82\xa0']
    probes += [k[:-2] for k in list(keyed)[:64] if len(k) > 2]
    probes += [k + b'\x82\xa0' for k in list(keyed)[:64]]
    probes = [p for p in dict.fromkeys(probes) if p not in keyed and extent(p + b'\0\0') == len(p)]
    for p in probes:
        if lookup(_reader(out, nphs, {PROBE_VA: p + b'\0\0'}), PROBE_VA) is not None:
            raise ValueError('readback: a non-key string resolved')
    # 3. stub: decode every word, then execute the real machine code
    code = out[stub_off:stub_end]
    listing, capstone_text = check_stub_words(code, geo['stub_va'])
    if out[SITE - 0x10000:SITE - 0x10000 + 4] != struct.pack('>I', branch(SITE, geo['stub_va'])):
        raise ValueError('site branch')
    runner = _Runner(out, geo['stub_va'], len(code))
    keys = sorted(keyed, key=lambda k: (-len(k), k))
    if execute is None or len(keys) <= execute:
        chosen = keys
    else:
        half = execute // 2
        rest = keys[half:]
        chosen = keys[:half] + rest[::max(1, len(rest) // max(1, execute - half))]
    worst = 0
    for key in chosen:
        r31, steps = runner.run(key + b'\0')
        worst = max(worst, steps)
        if r31 != slots[key]:
            raise ValueError('stub: %s not resolved by the machine code' % keyed[key]['id'])
    misses = [b'', b'\x81\x40' * (MAX_EXTENT // 2 + 1)] + probes[:32]
    for data in misses:
        r31, steps = runner.run(data + b'\0')
        if r31 != (0xa5a5a5a5 << 32) | 0x50000000:
            raise ValueError('stub: a non-key string %r was replaced' % data[:16])
    # 4. SRVC block table still where tools/srvc.py reads it
    srvc_gate = _srvc_gate(elf, out, require_srvc)
    return {'isolation': True, 'sections_and_headers': True, 'readback_keys': len(keyed),
            'readback_non_keys': len(probes), 'stub_words_decoded': len(listing),
            'capstone_instructions': len(capstone_text) if capstone_text else 'capstone not installed',
            'stub_executed_keys': len(chosen), 'stub_executed_misses': len(misses),
            'stub_max_steps': worst, 'srvc_table': srvc_gate}


def slot_map(read):
    """{key bytes: English VA} by a plain scan of the slot array (no hashing).
    Raises if a key occurs in two slots."""
    mask, slots_va = struct.unpack('>II', read(EXT_VA + 8, 8))
    out = {}
    for i in range(mask + 1):
        h, kva, eva, klen, _ = struct.unpack('>IIIHH', read(slots_va + SLOT * i, SLOT))
        if kva:
            key = read(kva, klen)
            if key in out:
                raise ValueError('key stored in two slots')
            out[key] = eva
    return out


def _srvc_gate(elf, out, required):
    from tools import srvc
    try:
        size = srvc.locate_table(elf)['table'][-1]
    except (ValueError, struct.error) as exc:
        if required:
            raise ValueError('SRVC table not found in the input: %s' % exc)
        return {'checked': False, 'reason': 'input has no SRVC consumer (synthetic executable)'}
    before = srvc.read_table(elf, size)
    after = srvc.read_table(out, size)
    if before != after:
        raise ValueError('SRVC block table no longer reads back after the fold')
    return {'checked': True, 'file_offset': srvc.locate_table(out)['offset'], 'srvc_size': size,
            'pristine_size': size == srvc.SRVC_SIZE, 'blocks': len(after) - 1}


def apply(executable, entries, payloads=()):
    """game_build entry point: after vwf.patch, before or after the SRVC table
    rewrite (the two touch disjoint bytes and commute; tests prove it)."""
    return hook(executable, entries, require_srvc=True, payloads=payloads)


# ---------------------------------------------------------------------------
# UTF-8 -> cp932 keys: emulation of 0x13b38

def _converter_guard(elf):
    code = elf[CONVERTER[0] - 0x10000:CONVERTER[1] - 0x10000]
    if sha256(code) != CONVERTER_CODE_SHA256:
        raise ValueError('converter code at %#x differs from the reviewed one' % CONVERTER[0])
    slot = TOC + UTAB_DISP - PH1[3] + PH1[2]
    if struct.unpack_from('>I', elf, slot)[0] != UTAB_VA:
        raise ValueError('Unicode table TOC slot moved')
    return elf[UTAB_VA - 0x10000:UTAB_VA - 0x10000 + UTAB_SIZE]



@functools.lru_cache(maxsize=4)
def _table_from(path):
    return _converter_guard(Path(path).read_bytes())


def unicode_table(executable=None):
    return _converter_guard(bytes(executable)) if executable is not None else _table_from(str(PREPARED))


def convert(utf8_bytes, table):
    """Bytes the converter writes for a NUL-free UTF-8 string (no terminator)."""
    if b'\0' in utf8_bytes:
        raise ValueError('NUL inside the UTF-8 string')
    text = bytes(utf8_bytes).decode('utf-8')
    if any(ord(c) > 0xffff for c in text):
        raise ValueError('non-BMP character: the game count and UTF-16 length disagree')
    units = [ord(c) for c in text]
    count, out, i = len(units), bytearray(), 0
    while i < count:
        c = units[i]
        if c == 0x000a:
            out.append(0x0a); i += 1
        elif c == 0x0031:                       # '1' + code: colour escape, operand stored +1
            if i + 1 >= count:
                raise ValueError("'1' escape at the end of the string reads past the input")
            out += bytes((0x31, (units[i + 1] - 1) & 0xff)); i += 2
        elif c >> 8 == 0x0d:                    # the game skips this unit and the next
            i += 2
        elif c < 0x80:
            out += table[2 * c:2 * c + 2]; i += 1
        else:
            out += table[0x100 + 2 * c:0x100 + 2 * c + 2]; i += 1
    return bytes(out)


def utf8_key(utf8_bytes, executable=None):
    """cp932 key for a UTF-8 source string, exactly as it reaches 0x141a0."""
    key = convert(utf8_bytes, unicode_table(executable))
    if extent(key + b'\0\0') != len(key):
        raise ValueError('converted string is not one drawer string')
    return key


# ---------------------------------------------------------------------------
# Converter oracle: run the real 0x13b38 machine code

class ConverterOracle:
    """Executes 0x13b38 (and the libc strlen it calls) instruction by instruction.

    Only two calls are modelled in Python: the cellL10n import
    UTF8stoUTF16s (NID 0xf7681b9a, stub 0x77ad40) and mbstowcs(NULL, s, n)
    at 0x687034 (locale-dependent libc code reading TLS). Two models are
    run; the converter output must not depend on which is true:
      'A': mbstowcs counts code points, UTF8stoUTF16s writes no terminator,
           stack and output buffer pre-filled with junk;
      'B': mbstowcs counts bytes, UTF8stoUTF16s writes a 0 terminator,
           stack and output buffer zero.
    """

    def __init__(self, elf=None):
        elf = bytes(elf if elf is not None else PREPARED.read_bytes())
        _converter_guard(elf)
        self.mem = ppc_exec.Memory()
        self.mem.map(0x10000, elf[0:PH0_ORIGINAL_SIZE], writable=False)
        data = bytearray(PH1[6])
        data[:PH1[5]] = elf[PH1[2]:PH1[2] + PH1[5]]
        self.data = self.mem.map(PH1[3], data)
        self.stack = self.mem.map(0x40000000, bytes(0x4000))
        self.src = self.mem.map(0x48000000, bytes(0x4000), writable=False)
        self.cache = {}
        state = struct.unpack_from('>I', elf, PH1[2] + (TOC + STATE_DISP - PH1[3]))[0]
        if state != STATE_VA:
            raise ValueError('text state TOC slot moved')
        self.out_at = STATE_VA + 0xb8 - PH1[3]

    def run(self, source, model):
        """source: a VA in the image, or bytes (placed at 0x48000000, NUL added)."""
        if isinstance(source, (bytes, bytearray)):
            self.src[:] = bytes(len(self.src))
            self.src[:len(source)] = source
            source = 0x48000000
        va = source
        fill = 0x5a if model == 'A' else 0
        self.stack[:] = bytes([fill]) * len(self.stack)
        self.data[self.out_at:self.out_at + 0x2000] = bytes([fill]) * 0x2000
        m = ppc_exec.Machine(self.mem)
        m.cache = self.cache
        m.r[1], m.r[2], m.r[3] = 0x40003f00, TOC, va
        m.lr, m.pc = 0x1000, CONVERTER[0]

        def cstring(addr):
            s = bytearray()
            while True:
                b = self.mem.read(addr + len(s), 1)[0]
                if b == 0:
                    return bytes(s)
                s.append(b)

        def mbstowcs(mm):
            s = cstring(mm.r[4])
            if mm.r[3] != 0:
                raise ppc_exec.Unsupported('mbstowcs with a destination')
            if model == 'A':
                try:
                    n = len(s.decode('utf-8'))
                except UnicodeDecodeError:
                    n = -1
            else:
                n = len(s)
            mm.r[3] = n & ppc_exec.M64
            mm.pc = mm.lr

        def utf8stoutf16s(mm):
            mm.mem.write((mm.r[1] + 0x28) & ppc_exec.M64, mm.r[2].to_bytes(8, 'big'))  # stub saves r2
            src, srclen_p, dst, dstlen_p = mm.r[3], mm.r[4], mm.r[5], mm.r[6]
            n = struct.unpack('>i', mm.mem.read(srclen_p, 4))[0]
            units = mm.mem.read(src, n).decode('utf-8').encode('utf-16-be')
            cap = struct.unpack('>i', mm.mem.read(dstlen_p, 4))[0]
            if len(units) // 2 + 1 > cap:
                raise ppc_exec.Unsupported('string longer than the conversion buffer')
            mm.mem.write(dst, units + (b'\0\0' if model == 'B' else b''))
            mm.mem.write(dstlen_p, struct.pack('>i', len(units) // 2))
            mm.r[3] = 0
            mm.pc = mm.lr

        m.hooks = {MBSTOWCS: mbstowcs, UTF8STOUTF16S: utf8stoutf16s}
        m.run({0x1000}, limit=2000000)
        return bytes(self.data[self.out_at:self.out_at + 0x2000]), fill, m.steps


def validate_converter(limit=None, strings=None, elf=None):
    """Run the oracle over the inventory's UTF-8 strings; returns a report."""
    elf = bytes(elf if elf is not None else PREPARED.read_bytes())
    table = unicode_table(elf)
    oracle = ConverterOracle(elf)
    if strings is None:
        inv = json.loads(INVENTORY.read_text(encoding='utf-8'))['strings']
        strings = [(int(s['va'], 16), s['jp']) for s in inv if s['encoding'] == 'utf-8']
    if limit:
        strings = strings[:limit]
    ok, skipped, mismatched, steps = 0, [], [], 0
    def f(va): return va - 0x10000 if va < 0x940000 else va - PH1[3] + PH1[2]
    for va, jp in strings:
        raw = elf[f(va):elf.index(b'\0', f(va))]
        if raw != jp.encode('utf-8'):
            raise ValueError('inventory text differs from the ELF at %#x' % va)
        try:
            want = convert(raw, table)
        except ValueError as exc:
            skipped.append({'va': '%#x' % va, 'reason': str(exc)})
            continue
        good = True
        for model in ('A', 'B'):
            got, fill, n = oracle.run(va, model)
            steps += n
            expect = want + b'\0\0'
            if got[:len(expect)] != expect or any(b != fill for b in got[len(expect):]):
                good = False
        if good:
            ok += 1
        else:
            mismatched.append('%#x' % va)
    return {'utf8_records': len(strings), 'identical_both_models': ok, 'mismatched': mismatched,
            'skipped': skipped, 'instructions_executed': steps}


# ---------------------------------------------------------------------------
# Register liveness at the hook site (Capstone; analysis aid, not a build step)

def liveness(elf=None, max_fn=4000):
    """Register liveness at 0x141a0 over the drawer's CFG (both jump tables
    resolved), with every callee summarised by the argument registers it can
    actually read (recursive; unknown, indirect or too-large callees count as
    reading every argument register)."""
    import re
    from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
    elf = bytes(elf if elf is not None else PREPARED.read_bytes())
    md = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
    text_end = 0x10000 + PH0_ORIGINAL_SIZE
    cache = {}

    def dis(va):
        if va not in cache:
            d = list(md.disasm(elf[va - 0x10000:va - 0x10000 + 4], va)) if 0x10000 <= va < text_end else []
            cache[va] = (d[0].mnemonic, d[0].op_str) if d else None
        return cache[va]
    jt = {}
    for site, disp, count in ((0x14290, -0x7f18, 12), (0x14610, -0x7f14, 8)):
        base = _word(elf, TOC + disp)
        jt[site] = [base + ppc_exec.sext(_word(elf, base + 4 * k), 32) for k in range(count)]
    args = {'r%d' % i for i in range(3, 11)} | {'f%d' % i for i in range(1, 14)}
    vol = {'r0', 'ctr', 'xer', 'lr'} | {'r%d' % i for i in range(3, 13)} | \
        {'cr%d' % i for i in (0, 1, 5, 6, 7)} | {'f%d' % i for i in range(14)}
    at_return = {'r1', 'r2', 'r13', 'lr', 'r3', 'f1'} | {'r%d' % i for i in range(14, 32)} | \
        {'f%d' % i for i in range(14, 32)} | {'cr2', 'cr3', 'cr4'}
    mem = re.compile(r'(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)')
    regtok = re.compile(r'^(r\d+|f\d+|cr\d)$')
    update = re.compile(r'^(lbz|lhz|lha|lwz|ld|lfs|lfd|stb|sth|stw|std|stfs|stfd)ux?$')
    summaries, active = {}, set()

    def summary(fn):
        """Argument registers callee `fn` may read before writing."""
        if fn in summaries:
            return summaries[fn]
        if fn in active:
            return args
        active.add(fn)
        try:
            live = solve(fn, None)
            res = (live[fn] & args) if live is not None else args
        finally:
            active.discard(fn)
        summaries[fn] = res
        return res

    def rw(va):
        mn, ops = dis(va)
        mn = mn.rstrip('+-')
        toks = [t for t in ops.split(', ') if t] if ops else []
        reads, writes = set(), set()
        if mn.endswith('.'):
            writes.add('cr0')
            mn = mn[:-1]
        bases = [mem.fullmatch(t).group(2) for t in toks if mem.fullmatch(t)]
        plain = [t for t in toks if regtok.match(t)]
        reads |= set(bases)
        if update.match(mn):
            writes |= set(bases)
        if mn == 'bl':
            return summary(int(ops, 0)) | {'r1', 'r2'}, vol, 'call'
        if mn == 'bctrl':
            return args | {'ctr', 'r1', 'r2'}, vol, 'call'
        if mn == 'blr':
            return set(at_return), set(), 'ret'
        if mn == 'bctr':
            return {'ctr'}, set(), 'jt'
        if mn == 'b':
            return set(), set(), 'b'
        if mn.startswith('b'):
            field = plain[0] if plain and plain[0].startswith('cr') else 'cr0'
            if mn.startswith('bd'):
                return {'ctr'} | ({field} if len(mn) > 4 else set()), {'ctr'}, 'bc'
            if mn.endswith('lr') or mn.endswith('ctr') or mn.endswith('l'):
                return set(), set(), 'unknown'
            return {field}, set(), 'bc'
        if mn.startswith('cmp') or mn.startswith('fcmp'):
            if plain and plain[0].startswith('cr'):
                return reads | set(plain[1:]), writes | {plain[0]}, None
            return reads | set(plain), writes | {'cr0'}, None
        if mn.startswith('st'):
            return reads | set(plain), writes, None
        if mn == 'mtctr':
            return set(plain), {'ctr'}, None
        if mn == 'mtlr':
            return set(plain), {'lr'}, None
        if mn == 'mflr':
            return {'lr'}, set(plain), None
        if mn == 'mfctr':
            return {'ctr'}, set(plain), None
        if mn == 'mfcr':
            return {'cr%d' % i for i in range(8)}, set(plain), None
        if mn in ('mtcrf', 'mtocrf'):
            mask = int(toks[0], 0)
            return set(plain), {'cr%d' % i for i in range(8) if mask & (0x80 >> i)}, None
        if mn in ('nop', 'dcbt', 'dcbtst', 'sync', 'lwsync', 'isync', 'eieio'):
            return reads, writes, None
        if mn in ('addze', 'adde', 'subfe', 'subfze', 'addme', 'subfme'):
            reads.add('xer')
        if mn in ('srawi', 'sraw', 'sradi', 'srad', 'addic', 'addc', 'subfc', 'subfic', 'addze', 'adde',
                  'subfe', 'subfze'):
            writes.add('xer')
        if mn in ('rlwimi', 'rldimi', 'insrwi', 'insrdi') and plain:
            reads.add(plain[0])
        if plain:
            writes.add(plain[0])
            reads |= set(plain[1:])
        return reads, writes, None

    def resolve_jt(va):
        """Compiler switch: lwz rT,d(r2) (table), cmplwi crN,rX,K (bound) shortly before the bctr."""
        base = bound = None
        for k in range(1, 16):
            d = dis(va - 4 * k)
            if d is None:
                break
            m = re.match(r'(r\d+), (-?0x[0-9a-f]+|-?\d+)\(r2\)$', d[1])
            if d[0] == 'lwz' and m and base is None:
                base = _word(elf, TOC + int(m.group(2), 0))
            if d[0] == 'cmplwi' and bound is None:
                bound = int(d[1].split(', ')[-1], 0)
        if base is None or bound is None or bound > 256:
            return None
        return [base + ppc_exec.sext(_word(elf, base + 4 * k), 32) for k in range(bound + 1)]

    def succ(va, tables):
        mn, ops = dis(va)
        kind = rw(va)[2]
        if kind == 'ret':
            return []
        if kind == 'unknown':
            return None
        if kind == 'jt':
            return (tables or {}).get(va) or resolve_jt(va)
        if kind == 'b':
            return [int(ops, 0)]
        if kind == 'bc':
            return [va + 4, int(ops.split(', ')[-1], 0)]
        return [va + 4]

    def solve(entry, tables):
        reach, todo = set(), [entry]
        while todo:
            v = todo.pop()
            if v in reach:
                continue
            if dis(v) is None or len(reach) > max_fn:
                return None
            reach.add(v)
            nxt = succ(v, tables)
            if nxt is None:
                return None          # unresolved indirect branch: caller assumes the worst
            todo += nxt
        live = {v: set() for v in reach}
        changed = True
        while changed:
            changed = False
            for v in sorted(reach, reverse=True):
                r, w, _ = rw(v)
                out = set()
                for s in succ(v, tables):
                    out |= live.get(s, set())
                new = r | (out - w)
                if new != live[v]:
                    live[v] = new
                    changed = True
        live['_reach'] = reach
        return live

    live = solve(SITE, jt)
    if live is None:
        raise ValueError('drawer CFG did not resolve')
    reach = live.pop('_reach')
    gp_vol = {'r0', 'ctr', 'xer', 'lr'} | {'r%d' % i for i in range(3, 13)} | {'cr%d' % i for i in range(8)}
    r31 = ['%#x %s %s' % ((v,) + dis(v)) for v in sorted(reach) if 'r31' in dis(v)[1]]
    calls = sorted({int(dis(v)[1], 0) for v in reach if dis(v)[0] == 'bl'})
    return {'reachable_instructions': len(reach), 'live_in_at_site': sorted(live[SITE]),
            'volatile_live_at_site': sorted(live[SITE] & gp_vol),
            'callee_argument_reads': {('%#x' % c): sorted(summaries.get(c, args)) for c in calls},
            'r31_uses_after_site': r31,
            'jump_tables': {('%#x' % k): ['%#x' % t for t in v] for k, v in jt.items()}}


# ---------------------------------------------------------------------------
# Canary entries for the first runtime test

CANARIES = [
    {'id': 'canary:cp932:pilot-training-melee-help', 'encoding': 'cp932', 'va': 0xa08962,
     'english_text': 'SJIS HOOK OK',
     'evidence': 'cp932 help text of the Pilot Training screen for the first stat row (Melee); '
                 'which row the cursor starts on is not verified. The identical cp932 string is '
                 'a key in Jigoku ui_hook.json, whose hook sat on the cp932 drawer entry (r7 = 1), '
                 'and Jigoku held it as cp932 in its ELF too (0x720990). Tengoku keeps it as cp932 '
                 'in .data at 0xa08962, referenced from a .data table.'},
    {'id': 'canary:utf8:keyhelp-back', 'encoding': 'utf-8', 'va': 0x88b668,
     'english_text': 'UTF8 OK',
     'evidence': "'Back' key-help label of the AID_UIT_KeyHelp family (its class-name string "
                 'is at 0x88b639, directly before the labels), shown on the key-help bar of '
                 'most menus. UTF-8 only, in both Tengoku and Jigoku (no cp932 copy in either '
                 'ELF), so a swap can only come through the converter path (r7 = 0). Jigoku '
                 "translated this family in place and relied on the converter's Unicode table "
                 '(tools/key_help_labels.py, eboot.vwf_face).'},
]


def canary_entries(elf=None):
    elf = bytes(elf if elf is not None else PREPARED.read_bytes())
    out = []
    for c in CANARIES:
        off = c['va'] - 0x10000 if c['va'] < 0x940000 else c['va'] - PH1[3] + PH1[2]
        raw = elf[off:elf.index(b'\0', off)]
        key = raw if c['encoding'] == 'cp932' else utf8_key(raw, elf)
        # Fullwidth cp932 letters are in the game's own font: no VWF mapping needed.
        english = c['english_text'].translate({i: i + 0xfee0 for i in range(0x21, 0x7f)}).replace(' ', '　').encode('cp932')
        out.append({'id': c['id'], 'key': key, 'english': english, 'english_text': c['english_text'],
                    'source': {'encoding': c['encoding'], 'va': '%#x' % c['va'],
                               'jp': raw.decode('cp932' if c['encoding'] == 'cp932' else 'utf-8')},
                    'evidence': c['evidence']})
    return out


def load_entries(path):
    """Entries from a canary/entries JSON (hex bytes) -> hook() input."""
    rows = json.loads(Path(path).read_text(encoding='utf-8'))['entries']
    return [{'id': r['id'], 'key': bytes.fromhex(r['key']), 'english': bytes.fromhex(r['english'])}
            for r in rows]


def _guard_out(path):
    out = Path(path).resolve()
    scratch = SCRATCH.resolve()
    if out != scratch and scratch not in out.parents:
        raise ValueError('canary output must be under %s' % scratch)
    return out


def main(argv=None):
    import sys
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd')
    c = sub.add_parser('canary', help='write a 2-entry canary report (no game files)')
    c.add_argument('--out', required=True)
    v = sub.add_parser('validate-converter', help='run the real converter code on the inventory')
    v.add_argument('--limit', type=int)
    sub.add_parser('liveness', help='register liveness at the hook site (Capstone)')
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if args.cmd == 'canary':
        out = _guard_out(args.out)
        from tools import vwf
        elf = PREPARED.read_bytes()
        entries = canary_entries(elf)
        base, _ = vwf.patch(elf, {})
        _, rep = hook(base, entries)
        doc = {'schema': 1, 'note': 'Canary entries for the first UI-hook runtime test. Not translation data.',
               'entries': [dict(e, key=e['key'].hex(), english=e['english'].hex()) for e in entries],
               'dry_run_on_vwf_baseline': {k: rep[k] for k in ('stub_va', 'stub_bytes', 'table', 'file_size',
                                                               'verification')}}
        out.mkdir(parents=True, exist_ok=True)
        target = out / 'ui_hook_canary.json'
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(json.dumps(doc, ensure_ascii=False, indent=1))
        print('wrote', target)
        return 0
    if args.cmd == 'validate-converter':
        print(json.dumps(validate_converter(args.limit), indent=1))
        return 0
    if args.cmd == 'liveness':
        print(json.dumps(liveness(), indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
