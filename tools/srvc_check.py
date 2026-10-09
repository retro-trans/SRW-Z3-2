"""Independent readback of a rebuilt SRVC.BIN + executable pair.

Deliberately shares no code with tools/srvc.py: the table is re-read from the
patched executable through the loader instruction's TOC slot, the blocks are
walked with a separate implementation of the game's parser, and the expected
text of every line is computed from the ORIGINAL file and the edit request.
A checker that reuses the writer's offsets can certify the writer's bug.

What it asserts (returns a list of problems; empty means accepted):
- the executable differs from its original only inside the table bytes;
- the table is 0-based, strictly increasing, 16-aligned, has the original
  number of entries and ends exactly at the new file size;
- every block keeps its header, slot/rule/C/D arrays and cue table byte for
  byte, and every block with no edit is byte-identical to the original;
- every line's string, including its NUL, lies inside its own block window
  [tab[i], tab[i+1]) -- the only bytes the runtime loads -- and reads back as
  the replacement or, when untouched, as the original bytes;
- nothing but zeros follows the last string of a block.
"""
import bisect

LOADER_INSN_VA = 0x143574       # lwz r10, d(r2) -- the table's only reader
TOC = 0x99fe70


def _load_map(elf):
    phoff = int.from_bytes(elf[32:40], 'big')
    size, count = int.from_bytes(elf[54:56], 'big'), int.from_bytes(elf[56:58], 'big')
    out = []
    for i in range(count):
        h = elf[phoff + i * size:phoff + (i + 1) * size]
        if int.from_bytes(h[0:4], 'big') == 1:
            off, va, filesz = (int.from_bytes(h[8:16], 'big'), int.from_bytes(h[16:24], 'big'),
                               int.from_bytes(h[32:40], 'big'))
            out.append((va, va + filesz, off))
    return out


def _at(elf, va):
    for lo, hi, off in _load_map(elf):
        if lo <= va < hi:
            return off + va - lo
    raise ValueError('unmapped VA %#x' % va)


def executable_table(elf, entries):
    insn = int.from_bytes(elf[_at(elf, LOADER_INSN_VA):_at(elf, LOADER_INSN_VA) + 4], 'big')
    if insn >> 26 != 32 or (insn >> 16) & 31 != 2:
        raise ValueError('loader instruction is not lwz rT, d(r2)')
    d = insn & 0xffff
    d = d - 0x10000 if d & 0x8000 else d
    slot = _at(elf, TOC + d)
    table_va = int.from_bytes(elf[slot:slot + 4], 'big')
    start = _at(elf, table_va)
    return start, [int.from_bytes(elf[start + 4 * k:start + 4 * k + 4], 'big') for k in range(entries)]


def _walk(f, base, end):
    """The game's parse at 0x1390fc, written out independently."""
    if f[base] != 3:
        raise ValueError('version byte %d' % f[base])
    c1, c2, c3 = f[base + 1], f[base + 2], f[base + 3]
    c4 = f[base + 4] | f[base + 5] << 8
    c6 = f[base + 6] | f[base + 7] << 8
    cue_end = base + 8 + c1 * 4 + c4 * 8 + c2 * 8 + c3 * 4 + c6 * 8
    pool = cue_end + c6 * 4
    offs = [int.from_bytes(f[cue_end + 4 * k:cue_end + 4 * k + 4], 'little') for k in range(c6)]
    return cue_end, pool, offs


def _string(f, at, end):
    """Bytes up to the NUL, or None if no NUL before `end`."""
    stop = f.find(b'\0', at, end)
    return None if stop < 0 else f[at:stop]


def expected_lines(old, old_tab, strings, refs):
    """{(block, k): bytes} the rebuilt file must hold, from the ORIGINAL file."""
    out = {}
    for i in range(len(old_tab) - 1):
        _cue_end, pool, offs = _walk(old, old_tab[i], old_tab[i + 1])
        for k, o in enumerate(offs):
            at = pool + o
            want = refs.get((i, k), strings.get(at))
            if want is None:
                want = _string(old, at, old_tab[i + 1])
            out[(i, k)] = bytes(want)
    return out


def verify(old_elf, new_elf, old, new, strings=None, refs=None):
    strings, refs = strings or {}, refs or {}
    problems = []
    entries = None
    start, old_tab = executable_table(old_elf, 1)
    # original table length: the strictly increasing run from 0
    k = 1
    while True:
        v = int.from_bytes(old_elf[start + 4 * k:start + 4 * k + 4], 'big')
        if v <= old_tab[-1]:
            break
        old_tab.append(v)
        k += 1
    entries = len(old_tab)
    if old_tab[-1] != len(old):
        return ['original table does not end at the original file size']
    nstart, new_tab = executable_table(new_elf, entries)
    if nstart != start:
        problems.append('table moved in the executable')
    if len(new_elf) != len(old_elf):
        problems.append('executable size changed')
    stop = start + 4 * entries
    if old_elf[:start] != new_elf[:start] or old_elf[stop:] != new_elf[stop:]:
        problems.append('executable changed outside the table')
    if new_tab[0] != 0 or any(b <= a for a, b in zip(new_tab, new_tab[1:])):
        problems.append('new table is not strictly increasing from 0')
    if any(x % 16 for x in new_tab):
        problems.append('new table has unaligned block starts')
    if new_tab[-1] != len(new):
        problems.append('new table ends at %d, file is %d bytes' % (new_tab[-1], len(new)))
    if problems:
        return problems
    want = expected_lines(old, old_tab, strings, refs)
    touched = {i for i, _k in refs}
    touched |= {bisect.bisect_right(old_tab, at) - 1 for at in strings}
    for i in range(entries - 1):
        ob, oe, nb, ne = old_tab[i], old_tab[i + 1], new_tab[i], new_tab[i + 1]
        if i not in touched and old[ob:oe] != new[nb:ne]:
            problems.append('block %d changed but has no edit' % i)
            continue
        o_cue, o_pool, o_offs = _walk(old, ob, oe)
        try:
            n_cue, n_pool, n_offs = _walk(new, nb, ne)
        except ValueError as exc:
            problems.append('block %d: %s' % (i, exc))
            continue
        if new[nb:n_cue] != old[ob:o_cue]:
            problems.append('block %d: header/arrays/cue table changed' % i)
            continue
        if len(n_offs) != len(o_offs):
            problems.append('block %d: line count changed' % i)
            continue
        for k, o in enumerate(n_offs):
            got = _string(new, n_pool + o, ne)
            if got is None:
                problems.append('block %d line %d: string leaves the loaded window' % (i, k))
                break
            if got != want[(i, k)]:
                problems.append('block %d line %d: reads back wrong' % (i, k))
                break
        # Unreferenced pool strings (3,982 in the pristine file) are kept too:
        # the new pool must start with the original pool sequence, replaced
        # where requested, and may only add this block's per-line strings.
        orig, at = [], o_pool
        for raw in old[o_pool:oe].rstrip(b'\0').split(b'\0') if old[o_pool:oe].strip(b'\0') else []:
            orig.append(bytes(strings.get(at, raw)))
            at += len(raw) + 1
        body = new[n_pool:ne].rstrip(b'\0')
        got = body.split(b'\0') if body else []
        extra = {bytes(v) for (b, _k), v in refs.items() if b == i}
        if got[:len(orig)] != orig or not set(got[len(orig):]) <= extra:
            problems.append('block %d: pool sequence differs from the original' % i)
    return problems
