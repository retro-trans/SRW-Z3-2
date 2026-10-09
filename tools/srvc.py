"""Tengoku battle voice file DATA/BTLC/SRVC.BIN and its executable block table.

Format (validated over all 368 blocks of the pristine Tengoku file and against
the executable's own parser at VA 0x1390fc; see docs/BATTLE_VOICE.md):

    file  = block[0] .. block[367], back to back, each starting 16-aligned
    block = [tab[i], tab[i+1]) where tab is 369 big-endian u32 file offsets
            held in the EBOOT data segment (VA 0x9eb0a0, file 0x9db0a0)

    +0  u8  version   always 3; the game's parser zeroes the counts otherwise
    +1  u8  n1        situation slots, always 74            -> A[n1]  u32
    +2  u8  n2        8-byte records, text independent      -> C[n2]
    +3  u8  n3        4-byte records, text independent      -> D[n3]
    +4  u16le n4      selection rules                       -> B[n4]  8 bytes
    +6  u16le n6      voice lines                           -> cue[n6] 8 bytes
    +8  A, B, C, D, cue[n6] (u32 cue id, u32 flag), offs[n6] (u32le,
        relative to pool), pool (cp932, NUL terminated), zero tail to the
        next block start

A slot = (u16 first rule, u8 rule count, u8 flags); a rule (B) = (u16
condition, u16 weight, u16 first line, u16 line count). Every line is reached
through exactly one slot's rules in the pristine file.

The game never walks the file: it reads exactly [tab[id], tab[id+1]) for a
bank id and parses that window. So a block may grow only if the table in the
executable is rewritten in the same build, and a string must never be placed
outside its own block window.

    python -m tools.srvc prepare [--apply]   extract pristine SRVC + program ELF
    python -m tools.srvc info                table evidence and counts
    python -m tools.srvc roundtrip           byte-identical no-op rebuild
"""
import argparse
import re
import struct
import sys
from collections import namedtuple
from pathlib import Path

SRVC = '/PS3_GAME/USRDIR/DATA/BTLC/SRVC.BIN'
SRVC_SIZE = 3499808
PATH_STRING = b'/app_home/DATA/BTLC/SRVC.BIN'
VERSION = 3
SLOTS = 74
NUL = b'\0'
BREAK = '\\n'                 # SRVC writes a line break as literal backslash-n

# Executable facts, all re-derived and checked by locate_table(); none is
# trusted on its own. Addresses are VAs in the reconstructed program ELF
# (tools/self_elf.py), whose first two LOAD segments map VA = offset + 0x10000.
TOC_BASE = 0x99fe70           # r2 of every OPD entry (33,039 of them)
LOADER_VA = 0x143574          # lwz r10, -0x5b54(r2): table base -> ctx+0x28
START_READ_VA = 0x1390a0      # lwz r4, -0x5d74(r2) (path); &tab[id] -> 0x13c164
PARTIAL_READ_VA = 0x13c164    # off = tab[id], len = tab[id+1] - tab[id]
PARSER_VA = 0x1390fc          # block parser; checks version byte == 3
TABLE_VA = 0x9eb0a0
TABLE_OFF = 0x9db0a0
NBLOCKS = 368

# Instruction words that define the consumer. A different executable revision
# must fail here instead of being patched at a guessed offset.
CODE = {
    0x143548: 0xa01b165c,     # lhz  r0, 0x165c(r27)   resident bank id
    0x14354c: 0xa13a0024,     # lhz  r9, 0x24(r26)     wanted bank id
    0x143574: 0x8142a4ac,     # lwz  r10, -0x5b54(r2)  table base (TOC slot)
    0x143598: 0x915f0028,     # stw  r10, 0x28(r31)    ctx+0x28 = table
    0x1390b0: 0x8082a28c,     # lwz  r4, -0x5d74(r2)   path string
    0x1390b8: 0xa0bd002c,     # lhz  r5, 0x2c(r29)     bank id
    0x1390bc: 0x801d0028,     # lwz  r0, 0x28(r29)     table base
    0x1390c4: 0x54a5103a,     # slwi r5, r5, 2         id * 4
    0x1390d0: 0x48003095,     # bl   0x13c164          partial read
    0x13c174: 0x80050000,     # lwz  r0, 0(r5)         tab[id]
    0x13c184: 0x80a50004,     # lwz  r5, 4(r5)         tab[id+1]
    0x13c190: 0x7ca02850,     # subf r5, r0, r5        length
    0x139118: 0x88040000,     # lbz  r0, 0(r4)         version byte
    0x139120: 0x2f800003,     # cmpwi cr7, r0, 3
}

Block = namedtuple('Block', 'i base end n1 n2 n3 n4 n6 rules_at c_at d_at cue_at offs_at pool '
                            'slots rules cues offs starts tail')


def segments(elf):
    """[(file offset, va, filesz)] for every LOAD program header."""
    if elf[:4] != b'\x7fELF' or elf[4] != 2 or elf[5] != 2:
        raise ValueError('not a big-endian ELF64')
    phoff = struct.unpack_from('>Q', elf, 32)[0]
    phsz, phn = struct.unpack_from('>HH', elf, 54)
    out = []
    for i in range(phn):
        kind, _flags, off, va, _pa, filesz = struct.unpack_from('>IIQQQQ', elf, phoff + i * phsz)
        if kind == 1 and filesz:
            out.append((off, va, filesz))
    return out


def va_to_offset(elf, va, size=4):
    for off, base, filesz in segments(elf):
        if base <= va and va + size <= base + filesz:
            return off + va - base
    raise ValueError('VA %#x is not file-backed' % va)


def word(elf, va):
    return struct.unpack_from('>I', elf, va_to_offset(elf, va))[0]


def lwz_toc_disp(insn):
    """Displacement of `lwz rT, d(r2)`, or None."""
    if insn >> 26 != 32 or (insn >> 16) & 31 != 2:
        return None
    return ((insn & 0xffff) ^ 0x8000) - 0x8000


def locate_table(elf, srvc_size=None):
    """Re-derive the block table from the executable's own code.

    Returns {'offset', 'va', 'count', 'table', 'toc_slot', 'evidence'}.
    `count` blocks; `table` has count+1 entries ending at the file size.
    """
    bad = ['%#x: %#010x, expected %#010x' % (va, word(elf, va), want)
           for va, want in sorted(CODE.items()) if word(elf, va) != want]
    if bad:
        raise ValueError('SRVC consumer code differs: ' + '; '.join(bad))
    # The TOC base is the r2 recorded in the state-function descriptors the
    # loader installs (TOC slot -0x5b5c -> OPD of 0x1390a0).
    disp = lwz_toc_disp(word(elf, LOADER_VA))
    slot_va = TOC_BASE + disp
    table_va = word(elf, slot_va)
    opd_va = word(elf, TOC_BASE - 0x5b5c)
    if (word(elf, opd_va), word(elf, opd_va + 4)) != (START_READ_VA, TOC_BASE):
        raise ValueError('state descriptor does not name the start-read function with this TOC')
    path_va = word(elf, TOC_BASE + lwz_toc_disp(word(elf, 0x1390b0)))
    p = va_to_offset(elf, path_va, len(PATH_STRING) + 1)
    if elf[p:p + len(PATH_STRING) + 1] != PATH_STRING + NUL:
        raise ValueError('start-read path is not SRVC.BIN')
    off = va_to_offset(elf, table_va)
    tab = [struct.unpack_from('>I', elf, off)[0]]
    if tab[0] != 0:
        raise ValueError('block table does not start at file offset 0')
    # The run of strictly increasing, 16-aligned offsets is the table; the
    # next table in the image starts again at 0.
    while True:
        v = struct.unpack_from('>I', elf, off + 4 * len(tab))[0]
        if v <= tab[-1]:
            break
        tab.append(v)
    if any(x % 16 for x in tab):
        raise ValueError('block offsets are not 16-aligned')
    if srvc_size is not None and tab[-1] != srvc_size:
        raise ValueError('table ends at %d, SRVC.BIN is %d bytes' % (tab[-1], srvc_size))
    return {'offset': off, 'va': table_va, 'count': len(tab) - 1, 'table': tab,
            'toc_slot_va': slot_va, 'path_va': path_va,
            'evidence': {'code_words_checked': len(CODE), 'toc_displacement': disp}}


def read_table(elf, srvc_size=None, expect=(TABLE_OFF, NBLOCKS)):
    """The validated table; `expect` pins its file offset and block count
    (None only for synthetic test executables)."""
    loc = locate_table(elf, srvc_size)
    if expect is not None and (loc['offset'], loc['count']) != tuple(expect):
        raise ValueError('block table moved or changed length: %#x, %d' % (loc['offset'], loc['count']))
    return loc['table']


def pack_table(tab):
    return struct.pack('>%dI' % len(tab), *tab)


def patch_table(elf, old_tab, new_tab, expect=(TABLE_OFF, NBLOCKS)):
    """Write a rebuilt table over the validated original. Nothing else moves."""
    if len(old_tab) != len(new_tab):
        raise ValueError('block count must not change')
    if read_table(elf, None, expect) != list(old_tab):
        raise ValueError('executable table is not the expected original')
    at = locate_table(elf)['offset']
    out = bytearray(elf)
    out[at:at + 4 * len(new_tab)] = pack_table(new_tab)
    # The next word must still end the run, or a re-read would over-count.
    nxt = struct.unpack_from('>I', out, at + 4 * len(new_tab))[0]
    if nxt > new_tab[-1]:
        raise ValueError('rebuilt table would merge with the following table')
    return bytes(out)


def parse_block(data, i, base, end):
    if data[base] != VERSION:
        raise ValueError('block %d: version %d' % (i, data[base]))
    n1, n2, n3 = data[base + 1], data[base + 2], data[base + 3]
    n4, n6 = struct.unpack_from('<HH', data, base + 4)
    slots_at = base + 8
    rules_at = slots_at + 4 * n1
    c_at = rules_at + 8 * n4
    d_at = c_at + 8 * n2
    cue_at = d_at + 4 * n3
    offs_at = cue_at + 8 * n6
    pool = offs_at + 4 * n6
    if pool > end:
        raise ValueError('block %d: arrays overrun the block' % i)
    slots = [(v & 0xffff, (v >> 16) & 0xff, v >> 24)
             for v in struct.unpack_from('<%dI' % n1, data, slots_at)]
    rules = [struct.unpack_from('<4H', data, rules_at + 8 * k) for k in range(n4)]
    cues = [struct.unpack_from('<II', data, cue_at + 8 * k) for k in range(n6)]
    offs = list(struct.unpack_from('<%dI' % n6, data, offs_at)) if n6 else []
    raw = data[pool:end]
    body = raw.rstrip(NUL)
    if body:
        body += NUL
    if any(raw[len(body):]):
        raise ValueError('block %d: nonzero bytes after the pool' % i)
    starts = [0] + [m.end() for m in re.finditer(NUL, body)][:-1] if body else []
    sset = set(starts)
    for k, o in enumerate(offs):
        if o not in sset:
            raise ValueError('block %d line %d: offset %d is not a string start' % (i, k, o))
    for s, (first, count, _flags) in enumerate(slots):
        if first + count > n4:
            raise ValueError('block %d slot %d: rules out of range' % (i, s))
    for k, (_c, _w, first, count) in enumerate(rules):
        if first + count > n6:
            raise ValueError('block %d rule %d: lines out of range' % (i, k))
    return Block(i, base, end, n1, n2, n3, n4, n6, rules_at, c_at, d_at, cue_at, offs_at, pool,
                 slots, rules, cues, offs, starts, len(raw) - len(body))


def parse(data, tab):
    if tab[0] != 0 or tab[-1] != len(data):
        raise ValueError('table covers [%d, %d), file is %d bytes' % (tab[0], tab[-1], len(data)))
    return [parse_block(data, i, tab[i], tab[i + 1]) for i in range(len(tab) - 1)]


def string_at(data, off):
    return data[off:data.index(NUL, off)]


def text(raw):
    return raw.decode('cp932')


def lines(data, blocks):
    """Every line reference: dict(block, k, offset, cue, flag, jp, slots, rules)."""
    out = []
    for b in blocks:
        where = [[] for _ in range(b.n6)]
        for s, (first, count, _f) in enumerate(b.slots):
            for r in range(first, first + count):
                cond, weight, l0, ln = b.rules[r]
                for k in range(l0, l0 + ln):
                    where[k].append((s, r, cond, weight))
        for k, o in enumerate(b.offs):
            off = b.pool + o
            out.append({'block': b.i, 'k': k, 'offset': off, 'cue': b.cues[k][0],
                        'flag': b.cues[k][1], 'jp': text(string_at(data, off)), 'uses': where[k]})
    return out


def rebuild(data, tab, strings=None, refs=None):
    """Rebuild every block with growable pools.

    strings = {absolute offset of an ORIGINAL pool string: new bytes} -- one
              replacement serves every line that points at that string.
    refs    = {(block, line k): new bytes} -- gives one line its own string
              (appended at the end of its block's pool), overriding `strings`.
    Header .. cue table are copied verbatim, the original pool order is kept,
    the original zero tail is kept, blocks stay 16-aligned and in order.
    Returns (new bytes, new table, report rows (i, old size, new size, edits)).
    """
    strings, refs = dict(strings or {}), dict(refs or {})
    for v in list(strings.values()) + list(refs.values()):
        if not isinstance(v, (bytes, bytearray)) or NUL in v:
            raise ValueError('replacement must be bytes without NUL')
    blocks = parse(data, tab)
    known = {b.pool + s for b in blocks for s in b.starts}
    stray = sorted(set(strings) - known)
    if stray:
        raise ValueError('not an original string start: %s' % ', '.join('%#x' % x for x in stray[:5]))
    stray = sorted(k for k in refs if not (0 <= k[0] < len(blocks) and 0 <= k[1] < blocks[k[0]].n6))
    if stray:
        raise ValueError('no such line: %r' % stray[:5])
    out, newtab, report = bytearray(), [], []
    for b in blocks:
        newtab.append(len(out))
        out += data[b.base:b.offs_at]
        pos, pool, edits = {}, bytearray(), 0
        for s in b.starts:
            pos[s] = len(pool)
            new = strings.get(b.pool + s)
            if new is None:
                new = string_at(data, b.pool + s)
            else:
                edits += 1
            pool += new + NUL
        extra = {}
        offs = []
        for k, o in enumerate(b.offs):
            new = refs.get((b.i, k))
            if new is None:
                offs.append(pos[o])
                continue
            if new not in extra:
                extra[new] = len(pool)
                pool += new + NUL
                edits += 1
            offs.append(extra[new])
        out += struct.pack('<%dI' % b.n6, *offs) if b.n6 else b''
        out += pool + bytes(b.tail)
        out += bytes(-len(out) % 16)
        report.append((b.i, b.end - b.base, len(out) - newtab[-1], edits))
    newtab.append(len(out))
    return bytes(out), newtab, report


# --------------------------------------------------------------------------
# Workspace preparation and CLI


def _settings():
    from tools.common import ROOT
    from tools.pipeline import config
    return config(ROOT / 'config/tengoku.json')


def prepared_paths(settings=None):
    settings = settings or _settings()
    base = settings['work'] / 'prepared'
    return base / 'SRVC.BIN', base / 'EBOOT.elf'


def prepare(apply=False):
    """Copy the pristine SRVC and reconstruct the program ELF into prepared/."""
    from tools.common import sha256, sha256_file
    from tools.pipeline import verified_source
    from tools.self_elf import decrypt, EBOOT
    settings = _settings()
    src = verified_source(settings, SRVC)
    srvc_out, elf_out = prepared_paths(settings)
    print('%s: %s -> %s, program ELF -> %s' % ('APPLY' if apply else 'DRY RUN', src, srvc_out, elf_out))
    data = src.read_bytes()
    elf, _report = decrypt(verified_source(settings, EBOOT).read_bytes())
    tab = read_table(elf, len(data))
    parse(data, tab)
    if not apply:
        return
    for path, blob in ((srvc_out, data), (elf_out, elf)):
        if path.exists():
            if sha256_file(path) != sha256(blob):
                raise ValueError('%s exists with different content' % path)
            continue
        with open(str(path), 'xb') as stream:
            stream.write(blob)
    print('wrote %s (%d B) and %s (%d B)' % (srvc_out, len(data), elf_out, len(elf)))


def load_prepared():
    srvc_path, elf_path = prepared_paths()
    if not srvc_path.exists() or not elf_path.exists():
        raise ValueError('run `python -m tools.srvc prepare --apply` first')
    data, elf = srvc_path.read_bytes(), elf_path.read_bytes()
    return data, elf


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd')
    p = sub.add_parser('prepare')
    p.add_argument('--apply', action='store_true')
    sub.add_parser('info')
    sub.add_parser('roundtrip')
    args = ap.parse_args(argv)
    if args.cmd == 'prepare':
        prepare(args.apply)
        return 0
    if args.cmd in ('info', 'roundtrip'):
        data, elf = load_prepared()
        loc = locate_table(elf, len(data))
        tab = loc['table']
        blocks = parse(data, tab)
        if args.cmd == 'info':
            refs = lines(data, blocks)
            print('table: file %#x / VA %#x, %d blocks + sentinel, TOC slot VA %#x'
                  % (loc['offset'], loc['va'], loc['count'], loc['toc_slot_va']))
            print('blocks with lines: %d; line references: %d; distinct strings: %d'
                  % (sum(1 for b in blocks if b.n6), len(refs), len({r['jp'] for r in refs})))
            print('largest block: %d B' % max(b.end - b.base for b in blocks))
            return 0
        new, newtab, _ = rebuild(data, tab)
        ok = new == data and newtab == tab
        print('no-op rebuild byte-identical: %s' % ok)
        return 0 if ok else 1
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
