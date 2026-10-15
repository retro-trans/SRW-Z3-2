"""Reserve the full native Funds range in all three intermission footers."""
import argparse
import json
import struct
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U, ui_hook as H
from tools.ui_description_layout import advance

DEST = ROOT/'work/translation/en/ui/review36_funds.json'
WIDGETS = (0x9af44, 0x9b124, 0x9b304)
LEFT = 346.5
LIMIT = 99_999_999


def plan():
    source = B.source()
    widgets = {at: r for r in U.fssa_strings(source) for at in r['widget_offsets']}
    number = source[0xb9c2c:0xb9c38]
    style = source[0xaf558:0xaf56c]
    if struct.unpack('>ffHBB', number)[2:] != (177, 15, 0) or style[12:18] != bytes.fromhex('111c21600008'):
        raise ValueError('Intermission Funds numeric field changed')
    # Keep the original numeric endpoint, 17-pixel advance and eight digits.
    # Allow a full 32-pixel digit quad plus two pixels of outline at the left.
    # This is deliberately wider than the ordinary visible numeric masks.
    right = 603
    numeric_left = right - 8*17 + 17 - 32 - 2
    width = sum(map(advance, 'Funds.'))*28/32
    if numeric_left - LEFT - width < 8 or LEFT - 334 < 8:
        raise ValueError('Funds label crosses an adjacent native number field')
    edits = []
    for at in WIDGETS:
        row = widgets[at]
        if row['text'] != '資金．' or source[at+19] != 28:
            raise ValueError('Funds caption changed')
        edits.append(dict(widget_offset=at, source_sha256=sha256(row['raw']),
                          source_widget_sha256=sha256(source[at:at+32]), x=(LEFT-640)/640,
                          notes='Coordinate only: retain the shared Funds. translation, font, colors and live amount.'))
    return dict(schema=1, version='0.5.36', edits=edits, numeric_limit=LIMIT,
                numeric_element_offset=0xb9c2c, numeric_element_sha256=sha256(number),
                numeric_style_offset=0xaf558, numeric_style_sha256=sha256(style),
                bounds=dict(label_left=LEFT, label_width=width, label_right=LEFT+width,
                            conservative_number_left=numeric_left, minimum_gap=numeric_left-LEFT-width,
                            sr_number_right=334), runtime_verified=False)


def native_cases(elf):
    """Run the shipped cap getter, digit count and right-alignment arithmetic."""
    from tools import ppc_exec as P
    mem = P.Memory()
    for i, seg in enumerate(H._headers(elf)[2][:2]):
        mem.map(seg[3], elf[seg[2]:seg[2]+seg[5]], writable=i == 1)
    mem.map(0x40000000, bytes(0x4000))
    mem.map(0x41000000, bytes(0x200))
    mem.map(0x42000000, bytes(16))
    mem.write(H.TOC-0x7aa8, struct.pack('>I', 0x42000000))
    mem.write(0x41000068, struct.pack('>f', 32))
    mem.write(0x41000070, struct.pack('>f', 17))
    cases = []
    for value in (0, 9, 99, 999, 9999, 99999, 999999, 9999999, 13028032, LIMIT, LIMIT+1, 2147483647):
        mem.write(0x42000000, struct.pack('>I', value))
        vm = P.Machine(mem); vm.r[1] = 0x40003000; vm.r[2] = H.TOC
        vm.pc = 0x37540; vm.lr = 0xdead0000
        vm.run({vm.lr}, limit=100)
        actual = vm.r[3]
        if actual != min(value, LIMIT):
            raise ValueError('Native Funds cap differs')
        vm.r[28] = actual; vm.pc = 0x14f10
        vm.run({0x14ba0, 0x14ba4}, limit=vm.steps+1000)
        digits = vm.r[24]
        if digits != len(str(actual)):
            raise ValueError('Native numeric digit count differs')
        vm.r[27] = 0x41000000; vm.f[31] = 603; vm.pc = 0x14f5c
        vm.run({0x14bb4}, limit=vm.steps+100)
        left = vm.f[31]-2
        gap = left - LEFT - plan()['bounds']['label_width']
        if gap < 8:
            raise ValueError('Funds overlaps at a native digit boundary')
        cases.append(dict(input=value, displayed=actual, digits=digits, conservative_left=left,
                          gap=gap, native_steps=vm.steps))
    return cases


def main():
    p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true'); args = p.parse_args()
    data = plan()
    print('Three Funds labels:', [hex(r['widget_offset']) for r in data['edits']])
    print('Position:', data['bounds'], 'maximum:', data['numeric_limit'])
    if args.apply:
        write_json(DEST, data)
    else:
        print('DRY RUN: no layout data written.')


if __name__ == '__main__':
    main()
