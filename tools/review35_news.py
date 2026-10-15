"""Translate the separate UTF-8 rows copied by the native war-front report."""
import argparse
import json
import struct
from tools.common import ROOT, sha256, write_json
from tools import eboot_text as E, library_build as L, ui_hook as H, review32_content as C

DEST = ROOT / 'work/translation/en/ui/review35_news.json'


def plan():
    original = H.PREPARED.read_bytes()
    read = H._reader(original, H._headers(original)[2])
    base = int.from_bytes(read(H.TOC - 0x41d8, 4), 'big')
    if base != 0xa1f984:
        raise ValueError('Native scenario table changed')
    records = {int(r['va'], 16): r for r in E.records()}
    active = E.load()['strings']; resolver = E.resolver()
    profiles = {r['va']: r for r in C.headlines()}
    rows = {}
    for index in range(376):
        blob = read(base + index * 52, 52)
        if struct.unpack_from('>i', blob, 48)[0] < 0:
            continue
        pointer = int.from_bytes(blob[36:40], 'big')
        if read(pointer, 1) == b'\0':
            continue
        source = records[pointer]
        if source['encoding'] != 'utf-8' or source['family'] != 'date_location':
            raise ValueError('Uncataloged native news text')
        if pointer not in rows:
            text = E.unshow(L.expand(active[source['jp']]['en'], resolver))
            source_lines = source['jp'].split('\n'); lines = text.split('\n')
            if len(source_lines) != len(lines) or len(lines) > 8:
                raise ValueError('News paragraph pairing changed')
            profile = profiles.get(source['va'])
            prefix = profile['prefix'] if profile else ''
            from tools.ui_vwf_build import raster
            from tools.ui_description_layout import advance
            spans = [sum(advance(c) if not prefix else raster(prefix+c)[1] for c in line) for line in lines]
            if len(lines) > 1 and max(spans) > C.HEADLINE_UNITS:
                raise ValueError('Separate news row exceeds its screen width')
            rows[pointer] = dict(va=source['va'], source_sha256=sha256(source['jp'].encode('utf8')),
                                 english=lines, source_lines=source_lines, prefix=prefix,
                                 spans=spans, scenario_indices=[])
        rows[pointer]['scenario_indices'].append(index)
    result = list(rows.values())
    if len(result) != 22 or sum(len(r['english']) > 1 for r in result) != 6:
        raise ValueError('Native news category inventory changed')
    return dict(schema=1, version='0.5.35', rows=result,
                native_copy_sha256=sha256(read(0x184c74, 0x98)),
                native_table_sha256=sha256(read(base, 376 * 52)), runtime_verified=False)


def hook_entries(original, mapping):
    data = plan()
    if json.loads(DEST.read_text('utf8')) != data:
        raise ValueError('Native news translation plan is stale')
    out = []
    for row in data['rows']:
        if len(row['english']) == 1:
            continue
        selected = {c: mapping.get(row['prefix'] + c, code) for c, code in mapping.items()}
        for n, (jp, english) in enumerate(zip(row['source_lines'], row['english'])):
            out.append(dict(id='review35:news:%s:%d' % (row['va'], n),
                            key=H.utf8_key(jp.encode('utf8'), original),
                            english=bytes.fromhex(mapping[C.CAPTION_MARK])+L.encode(english, selected)))
    if len({r['key'] for r in out}) != len(out):
        raise ValueError('Conflicting separate news rows')
    return out


def native_lines(elf, source):
    """Execute 0x184c74..0x184d0c, including the game's 128-byte row copies."""
    from tools import ppc_exec as P
    mem = P.Memory()
    for i, seg in enumerate(H._headers(elf)[2][:2]):
        mem.map(seg[3], elf[seg[2]:seg[2]+seg[5]], writable=i == 1)
    mem.map(0x40000000, bytes(0x4000))
    mem.map(0x41000000, b'\xcc' * 16 + bytes(0x43c) + b'\xcc' * 16)
    mem.map(0x42000000, bytes(36) + struct.pack('>I', 0x43000000) + bytes(12))
    mem.map(0x43000000, source + b'\0', writable=False)
    def string(at):
        for n in range(1024):
            if mem.read(at+n, 1) == b'\0':
                return mem.read(at, n)
        raise ValueError('Unterminated native news string')
    def strchr(vm):
        n = string(vm.r[3]).find(bytes([vm.r[4] & 255]))
        vm.r[3] = vm.r[3]+n if n >= 0 else 0; vm.pc = vm.lr
    def strncpy(vm):
        raw = string(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3], raw+bytes(vm.r[5]-len(raw))); vm.pc = vm.lr
    def strcpy(vm):
        mem.write(vm.r[3], string(vm.r[4])+b'\0'); vm.pc = vm.lr
    vm = P.Machine(mem); vm.r = [0x770000+n for n in range(32)]
    vm.r[1] = 0x40003000; vm.r[2] = H.TOC; vm.r[28] = 0x42000000; vm.r[29] = 0x41000010
    vm.pc = 0x184c74; vm.lr = 0xdead0000
    vm.hooks = {0x68f52c: strchr, 0x68fca0: strncpy, 0x68f88c: strcpy}
    vm.run({0x184d0c}, limit=10000)
    count = mem.read(0x41000448, 1)[0]
    lines = [string(0x41000048+n*128) for n in range(count)]
    if lines != source.split(b'\n'):
        raise ValueError('Native news copy clips or changes a paragraph')
    if mem.read(0x41000000, 16) != b'\xcc'*16 or mem.read(0x4100044c, 16) != b'\xcc'*16:
        raise ValueError('Native news copy crosses its allocation')
    return lines, vm.steps


def verify(elf, mapping, hook, layout):
    original = H.PREPARED.read_bytes(); data = plan()
    entries, _ = E.hook_entries(original, mapping, lambda raw: H.utf8_key(raw, original))
    entries += C.hook_entries(original, mapping) + hook_entries(original, mapping)
    wanted = {r['key']: r for r in entries}
    runner = H._Runner(elf, int(hook['stub_va'], 16), hook['stub_bytes'])
    read = H._reader(elf, H._headers(elf)[2]); copies = []
    if sha256(read(0x184c74, 0x98)) != data['native_copy_sha256']:
        raise ValueError('Native news constructor changed')
    if sha256(read(0xa1f984, 376*52)) != data['native_table_sha256']:
        raise ValueError('Native scenario data changed')
    for row in data['rows']:
        raw = '\n'.join(row['source_lines']).encode('utf8')
        lines, steps = native_lines(elf, raw)
        for line in lines:
            key = H.utf8_key(line, original); expected = wanted[key]['english']
            pointer, _ = runner.run(key+b'\0')
            if read(pointer, len(expected)+1) != expected+b'\0':
                raise ValueError('Native news paragraph remains untranslated: '+row['va'])
        copies.append(dict(va=row['va'], english=row['english'], scenario_indices=row['scenario_indices'],
                           native_steps=steps, paragraphs=len(lines)))
    new = hook_entries(original, mapping)
    spans = [span for row in data['rows'] if len(row['english']) > 1 for span in row['spans']]
    centered = C.origin_cases(elf, mapping, layout,
        only_rows=[(r['id'], r['english'], span, False) for r, span in zip(new, spans)], quads=(28, 40))
    return dict(messages=len(copies), scenario_occurrences=sum(len(r['scenario_indices']) for r in copies),
                separate_draw_keys=len(new), native_copy_cases=copies, origin_cases=centered,
                runtime_verified=False)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true'); args = p.parse_args()
    data = plan()
    for row in data['rows']:
        if len(row['english']) > 1:
            print(row['va'], row['english'], 'widths:', row['spans'])
    print('News messages:', len(data['rows']), 'separate translated rows:',
          sum(len(r['english']) for r in data['rows'] if len(r['english']) > 1))
    if args.apply:
        write_json(DEST, data)
    else:
        print('DRY RUN: no translation data written.')


if __name__ == '__main__':
    main()
