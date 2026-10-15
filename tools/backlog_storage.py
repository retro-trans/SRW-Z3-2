"""Expand the dialogue-event backlog's inline text slots, preserving metadata.

The native writer truncates each entry at 308 bytes. After CRLF normalization,
long translated entries can end in the middle of a font cell. All constructors,
reset paths and ring-buffer moves must use the same larger slot layout.
"""
import argparse
import struct
from tools.common import sha256
from tools import ui_hook as H, vwf

GROW = 0x300
OLD_TEXT = 0x135
TEXT = OLD_TEXT + GROW
STRIDE = 0x158 + GROW
COUNT = 20
SIZE = 0x284 + COUNT * STRIDE
WINDOW = (0x1e7c1c, 0x1e83dc)
LINE_BYTES = 255
STACK_GROW = 0x80
SPANS = (
    ('writer and ring compaction', 0x1f56e4, 0x1f5bd0),
    ('reset all entries', 0x23cae4, 0x23cb64),
    ('constructor', 0x23cd34, 0x23ce70),
    ('second constructor', 0x23ce70, 0x23cfac),
    ('reset one entry', 0x6d28cc, 0x6d2940),
)
IMMEDIATES = {0x134: TEXT - 1, 0x135: TEXT, 0x158: STRIDE,
              0x1988: (COUNT - 1) * STRIDE, 0x1d64: SIZE,
              **{n: n + GROW for n in (0x138, 0x139, 0x13c, 0x140, 0x144,
                                        0x148, 0x14c, 0x150, 0x154)}}


def plan():
    original = H.PREPARED.read_bytes()
    if sha256(original) != vwf.ELF_SHA256:
        raise ValueError('Backlog source executable changed')
    read = H._reader(original, H._headers(original)[2])
    rows = []
    sources = []
    for label, start, end in SPANS:
        raw = read(start, end - start)
        sources.append(dict(label=label, start=start, end=end, sha256=sha256(raw)))
        for at in range(start, end, 4):
            word = struct.unpack('>I', read(at, 4))[0]
            # D-form arithmetic and loads/stores carry the layout constants.
            if word >> 26 not in (7, 11, 14, 32, 36, 38) or word & 0xffff not in IMMEDIATES:
                continue
            old = word & 0xffff
            rows.append(dict(va=at, before=word, after=(word & 0xffff0000) | IMMEDIATES[old],
                             old=old, new=IMMEDIATES[old], consumer=label))
    if len(rows) != 64:
        raise ValueError('Backlog patch inventory changed: %d' % len(rows))
    start, end = WINDOW
    sources.append(dict(label='backlog row buffer', start=start, end=end,
                        sha256=sha256(read(start, end - start))))
    for at in range(start, end, 4):
        word = struct.unpack('>I', read(at, 4))[0]
        opcode, base = word >> 26, (word >> 16) & 31
        old = word & (0xfffc if opcode in (58, 62) else 0xffff)
        new = None
        if at == start:
            new = ((-0x1f0 - STACK_GROW) & 0xffff) | (word & 3)
            old = word & 0xffff
        elif base == 1 and opcode in (14, 32, 34, 36, 38, 40, 44, 48, 50, 52, 54, 58, 62) and 0x140 <= old < 0x400:
            new = old + STACK_GROW
            if opcode in (58, 62):
                new |= word & 3
        elif at in (0x1e7f1c, 0x1e8114):
            old, new = word & 0xffff, LINE_BYTES
        elif at == 0x1e8124:
            old, new = word & 0xffff, 0xb0 + LINE_BYTES
        if new is not None:
            rows.append(dict(va=at, before=word, after=(word & 0xffff0000) | new,
                             old=old, new=new, consumer='backlog row buffer'))
    return dict(schema=1, old_text_bytes=OLD_TEXT, text_bytes=TEXT,
                maximum_text_bytes=TEXT - 1, entries=COUNT, stride=STRIDE,
                old_allocation_bytes=0x1d64, allocation_bytes=SIZE,
                old_line_bytes=128, line_bytes=LINE_BYTES, stack_growth=STACK_GROW,
                source_spans=sources, edits=rows, runtime_verified=False)


def apply(elf):
    report = plan()
    headers = H._headers(elf)[2]
    read = H._reader(elf, headers)
    for row in report['source_spans']:
        if sha256(read(row['start'], row['end'] - row['start'])) != row['sha256']:
            raise ValueError('Backlog native consumer changed: ' + row['label'])
    out = bytearray(elf)
    for row in report['edits']:
        segment = next(s for s in headers if s[0] == 1 and s[3] <= row['va'] < s[3] + s[5])
        at = segment[2] + row['va'] - segment[3]
        struct.pack_into('>I', out, at, row['after'])
    return bytes(out), report


def main():
    report = plan()
    print('Backlog text: 308 -> %d bytes; %d entries; allocation %d -> %d bytes.' %
          (TEXT - 1, COUNT, report['old_allocation_bytes'], SIZE))
    print('%d guarded instruction constants; IDs, link slots and flags retain their values.' % len(report['edits']))
    print('DRY RUN: no game assets written.')


if __name__ == '__main__':
    main()
