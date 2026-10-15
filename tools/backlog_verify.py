"""Execute native backlog allocation, writes, ring shifts and reset paths."""
import json
import struct
from tools import ui_hook as H, ppc_exec as P, backlog_storage as B


def exercise(elf, texts, *, constructor=0x23cd34, expanded=True):
    read = H._reader(elf, H._headers(elf)[2])
    mem = P.Memory()
    for seg in H._headers(elf)[2][:2]:
        mem.map(seg[3], elf[seg[2]:seg[2] + seg[5]], writable=False)
    stack, heap, source, event, obj = 0x40000000, 0x41000000, 0x42000000, 0x43000000, 0x44000000
    for at, size in ((stack, 0x20000), (heap, 0x10000), (source, 0x4000), (event, 0x400), (obj, 0x100)):
        mem.map(at, bytes(size))
    size = B.SIZE if expanded else 0x1d64
    stride = B.STRIDE if expanded else 0x158
    text_bytes = B.TEXT if expanded else B.OLD_TEXT
    mem.write(heap, b'\xa5' * size + b'CANARY')
    results = []

    def string(at):
        out = bytearray()
        while mem.read(at + len(out), 1) != b'\0':
            out += mem.read(at + len(out), 1)
            if len(out) > 8192:
                raise ValueError('Backlog text has no terminator')
        return bytes(out)

    def allocate(vm):
        if vm.r[3] != size:
            raise ValueError('Native backlog allocation differs')
        vm.r[3] = heap
        vm.pc = vm.lr

    def memset(vm):
        mem.write(vm.r[3], bytes([vm.r[4] & 255]) * vm.r[5]); vm.pc = vm.lr

    def strncpy(vm):
        data = string(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3], data.ljust(vm.r[5], b'\0')); vm.pc = vm.lr

    def move(vm):
        mem.write(vm.r[3], mem.read(vm.r[4], vm.r[5])); vm.pc = vm.lr

    def strcmp(vm):
        a, b = string(vm.r[3]), string(vm.r[4])
        vm.r[3] = (0 if a == b else -1 if a < b else 1) & P.M64
        vm.pc = vm.lr

    def getter(vm):
        vm.r[3] = heap; vm.pc = vm.lr

    hooks = {0x245c8: allocate, 0x69327c: memset, 0x68fca0: strncpy,
             0x687890: move, 0x68f738: strcmp, 0x1f5220: getter}

    def run(pc, *args):
        vm = P.Machine(mem)
        vm.r[1], vm.r[2] = stack + 0x1f000, H.TOC
        vm.r[3:3 + len(args)] = args
        vm.pc, vm.lr, vm.hooks = pc, 0x45000000, hooks
        vm.run({0x45000000}, limit=150000)
        if mem.read(heap + size, 6) != b'CANARY':
            raise ValueError('Native backlog write escaped its allocation')
        return vm

    run(constructor, obj)
    if struct.unpack('>I', mem.read(obj + 4, 4))[0] != heap:
        raise ValueError('Native backlog allocation is not attached')
    entry_type = struct.unpack('>I', read(H.TOC - 0x3dd0, 4))[0]
    entry_type = struct.unpack('>I', read(entry_type, 4))[0]
    for ordinal, text in enumerate(texts):
        if len(text) >= 0x3000:
            raise ValueError('Backlog fixture too large')
        mem.write(source, text + b'\0')
        links = [0x10000 + ordinal * 16 + n for n in range(6)]
        mem.write(event + 0x200, struct.pack('>6I', *links))
        mem.write(event + 0x100, struct.pack('>2I', event + 0x200, 6))
        mem.write(event, struct.pack('>8I', entry_type, 10, 20, ordinal + 1,
                                    source, 1, event + 0x100, ordinal + 100))
        vm = run(0x1f56e4, obj, event)
        if vm.r[3] != 1:
            raise ValueError('Native backlog rejected a new entry')
        live = min(ordinal + 1, B.COUNT)
        if struct.unpack('>i', mem.read(heap, 4))[0] != live - 1:
            raise ValueError('Native backlog count differs')
        for index in range(live):
            expected_index = ordinal - live + index + 1
            header = heap + 4 + index * 32
            base = heap + 0x284 + index * stride
            pointer = struct.unpack('>I', mem.read(header + 0x10, 4))[0]
            if pointer != base:
                raise ValueError('Ring shift did not rebind the inline text pointer')
            if struct.unpack('>I', mem.read(header + 0xc, 4))[0] != expected_index + 1:
                raise ValueError('Ring shift changed the event identity')
            expected = texts[expected_index][:text_bytes - 1]
            if string(pointer) != expected:
                raise ValueError('Native backlog truncates or changes the stored entry')
            descriptor = struct.unpack('>I', mem.read(header + 0x18, 4))[0]
            metadata = base + text_bytes + 3
            if descriptor != metadata + 24:
                raise ValueError('Ring shift did not rebind link metadata')
            if struct.unpack('>2I', mem.read(descriptor, 8)) != (metadata, 6):
                raise ValueError('Backlog link descriptor changed')
            if list(struct.unpack('>6I', mem.read(metadata, 24))) != [0x10000 + expected_index * 16 + n for n in range(6)]:
                raise ValueError('Native backlog changed the six link identities')
        results.append(dict(insert=ordinal + 1, retained=live, text_bytes=len(text), native_steps=vm.steps))
    final = string(heap + 0x284 + (min(len(texts), B.COUNT) - 1) * stride)
    duplicate = run(0x1f56e4, obj, event)
    suppressed = duplicate.r[3] == 0
    if expanded and not suppressed:
        raise ValueError('Native duplicate-entry suppression changed')
    run(0x23cae4, obj)
    for i in range(B.COUNT):
        base = heap + 0x284 + i * stride
        if mem.read(base, text_bytes) != bytes(text_bytes):
            raise ValueError('Native backlog reset leaves stale text')
        if mem.read(base + text_bytes + 3, 24) != b'\xff' * 24:
            raise ValueError('Native backlog reset changed empty link identities')
    return dict(constructor=hex(constructor), insertions=results, full_text_retained=expanded,
                ring_shifts=max(0, len(texts) - B.COUNT), reset_entries=B.COUNT,
                final_text=final.hex(), duplicate_suppressed=suppressed, allocation_canary_intact=True)


def row_copies(elf, lines, *, expanded=True):
    """Native row-copy branches and early-return frame restore, with canaries."""
    mem = P.Memory()
    for seg in H._headers(elf)[2][:2]:
        mem.map(seg[3], elf[seg[2]:seg[2] + seg[5]], writable=False)
    stack, source, descriptor = 0x40000000, 0x41000000, 0x42000000
    mem.map(stack, bytes(0x4000)); mem.map(source, bytes(0x4000)); mem.map(descriptor, bytes(0x100))
    top = stack + 0x3000
    original_regs = [0x12340000 + n for n in range(32)]
    vm = P.Machine(mem); vm.r = list(original_regs)
    vm.r[1], vm.r[2], vm.r[3] = top, H.TOC, descriptor
    vm.pc, vm.lr = B.WINDOW[0], 0x43000000
    vm.run({0x43000000}, limit=1000)
    if vm.r[1] != top or vm.r[14:32] != original_regs[14:32] or vm.r[2] != H.TOC:
        raise ValueError('Expanded backlog frame does not restore its caller')
    frame = 0x1f0 + (B.STACK_GROW if expanded else 0)
    sp = top - frame
    capacity = B.LINE_BYTES if expanded else 128
    cases = []

    def copy(vm):
        mem.write(vm.r[3], mem.read(vm.r[4], vm.r[5])); vm.pc = vm.lr

    for raw in lines:
        if not 1 <= len(raw) <= 255 or b'\0' in raw:
            raise ValueError('Backlog row fixture exceeds its native byte descriptor')
        mem.write(source, raw + b'\0')
        mem.write(descriptor, struct.pack('>2I', source, 0) + bytes([len(raw), 0, 0, 0]))
        buffer = sp + 0xb0
        mem.write(buffer - 6, b'BEFORE')
        mem.write(buffer, b'\xa5' * (capacity + 1))
        mem.write(buffer + capacity + 1, b'AFTER')
        vm = P.Machine(mem)
        vm.r[1], vm.r[2] = sp, H.TOC
        vm.r[27], vm.r[28], vm.r[14] = descriptor, descriptor, 0
        vm.pc, vm.lr = 0x1e7efc, 0x43000000
        vm.hooks = {0x6872cc: copy}
        vm.run({0x1e7f50, 0x1e8128}, limit=1000)
        expected = raw[:capacity]
        if mem.read(buffer, len(expected) + 1) != expected + b'\0':
            raise ValueError('Backlog drawing truncates or changes a line')
        if mem.read(buffer - 6, 6) != b'BEFORE' or mem.read(buffer + capacity + 1, 5) != b'AFTER':
            raise ValueError('Backlog row copy overwrites adjacent stack data')
        cases.append(dict(input_bytes=len(raw), output_bytes=len(expected), native_steps=vm.steps))
    return dict(frame_restored=True, row_copies=cases, canaries_intact=True)
