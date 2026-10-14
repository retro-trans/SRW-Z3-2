"""Execute the game's complete condition-panel assembler, including its SR slot.

The assembler owns three victory rows, three defeat rows and four SR rows.
Keep the original code and state calculation; model only libc and the optional
SR-status message getter. A canary follows the actual 0x407-byte output.
"""
from functools import lru_cache
from tools import ui_hook as H, ppc_exec as P
from tools.common import sha256

PANEL = (0x1aac08, 0x1aaf10)
SIZE = 0x407
SR_OFFSET = 0x26b
ROW_SIZE = 103
SR_ROWS = 4


def phases(table):
    values = [v.strip() for v in table.group(2).decode('ascii').split(',') if v.strip()]
    ids = [int(v == 'true') if v in ('true', 'false') else int(v) for v in values]
    if len(ids) % 8:
        raise ValueError('Native mission phase table is incomplete')
    return [ids[i:i+8] for i in range(0, len(ids), 8)]


@lru_cache(None)
def source_sha():
    source = H.PREPARED.read_bytes()
    return sha256(H._reader(source, H._headers(source)[2])(PANEL[0], PANEL[1]-PANEL[0]))


def assemble(elf, strings, current, previous=None, status=None):
    """Native strings plus two eight-slot phase rows -> intact output records."""
    read = H._reader(elf, H._headers(elf)[2])
    if sha256(read(PANEL[0], PANEL[1]-PANEL[0])) != source_sha():
        raise ValueError('Native condition-panel assembler changed')
    if len(current) != 8 or (previous is not None and len(previous) != 8):
        raise ValueError('Condition phases have eight slots')
    if len(strings) > 32 or any(len(s) > 302 for s in strings):
        raise ValueError('Condition input exceeds its native string table')
    mem = P.Memory()
    for seg in H._headers(elf)[2][:2]:
        mem.map(seg[3], elf[seg[2]:seg[2]+seg[5]], writable=False)
    mem.map(0x40000000, bytes(0x4000))
    mem.map(0x41000000, bytes(0x20000))
    src, dst = 0x41000000, 0x41010000
    for i, value in enumerate(strings):
        mem.write(src+i*303, value+b'\0')
    mem.write(src+0x25e1, bytes(v & 255 for v in current))
    if previous is not None:
        mem.write(src+0x25e9, bytes(v & 255 for v in previous))
    mem.write(dst, bytes(SIZE)+b'CANARY')

    def string(at):
        out = bytearray()
        while mem.read(at+len(out), 1) != b'\0':
            out += mem.read(at+len(out), 1)
            if len(out) > 4096:
                raise ValueError('Native panel string is unbounded')
        return bytes(out)

    def memset(vm):
        mem.write(vm.r[3], bytes([vm.r[4] & 255])*vm.r[5]); vm.pc = vm.lr

    def strlen(vm):
        vm.r[3] = len(string(vm.r[3])); vm.pc = vm.lr

    def strchr(vm):
        offset = string(vm.r[3]).find(bytes([vm.r[4] & 255]))
        vm.r[3] = vm.r[3]+offset if offset >= 0 else 0; vm.pc = vm.lr

    def strncat(vm):
        value = string(vm.r[3])+string(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3], value+b'\0'); vm.pc = vm.lr

    def sr_status(vm):
        vm.r[3] = 0
        if status is not None:
            mem.write(src+0x3000, status+b'\0'); vm.r[3] = src+0x3000
        vm.pc = vm.lr

    vm = P.Machine(mem)
    vm.r[1], vm.r[2] = 0x40003e00, H.TOC
    vm.r[3:7] = [src, dst, -1 if previous is None else 1, 0]
    vm.pc, vm.lr = PANEL[0], 0x42000000
    vm.hooks = {0x69327c: memset, 0x68a2ac: strlen, 0x68f52c: strchr,
                0x68f978: strncat, 0x1b0918: sr_status}
    vm.run({0x42000000}, limit=20000)
    if mem.read(dst+SIZE, 6) != b'CANARY':
        raise ValueError('Native SR text exceeds the four-row panel')
    records = {}
    for label, offset, count in (('victory', 1, 3), ('defeat', 0x136, 3), ('sr', SR_OFFSET, SR_ROWS)):
        records[label] = [dict(active=mem.read(dst+offset+i*ROW_SIZE, 1)[0],
                               state=mem.read(dst+offset+i*ROW_SIZE+1, 1)[0],
                               text=string(dst+offset+i*ROW_SIZE+2)) for i in range(count)]
    if vm.r[3] != 1:
        raise ValueError('Native condition-panel return changed')
    return records, vm.steps


def sr_cases(elf, rendered, mapping):
    """Every SR text in the real fixed-size panel, in both color states.

    Static keys run through the real drawer after composition. Live strings
    use defaults and maximum native names/counters before panel assembly.
    """
    from tools import mission_text as M, mission_display as D, library_build as L
    inventory = M.inventory()
    static = {r['jp']: r for r in D.rows(rendered)}
    entries = {r['key']: r['english'] for r in D.hook_entries(H.PREPARED.read_bytes(), rendered, mapping)}
    cases = []
    for jp, item in inventory.items():
        if 'sr' not in item['roles'] or not M.needs_text(jp):
            continue
        if jp not in rendered:
            raise ValueError('Untranslated SR condition')
        if jp in static:
            profiles = [('static', D.stage_key(static[jp]).encode('cp932'))]
        else:
            profiles = []
            for profile in ('default', 'maximum-custom'):
                raw = L.encode(rendered[jp], mapping)
                for token in M.PLACEHOLDERS:
                    value = (L.encode('1234567890', mapping) if token.startswith('ローカル') else
                             'Ａ'.encode('cp932')*20 if profile == 'maximum-custom' else
                             L.encode('Hibiki Kamishiro' if token == '主人公フルネーム' else
                                      'Kamishiro' if token == 'カミシロＮ' else 'Hibiki', mapping))
                    raw = raw.replace(token.encode('cp932'), value)
                profiles.append((profile, raw))
        for profile, raw in profiles:
            phase = [0, -1, -1, -1, -1, -1, -1, 0]
            for changed in (False, True):
                records, steps = assemble(elf, [raw], phase, None if changed else phase)
                active = [r for r in records['sr'] if r['active']]
                parts = raw.split(b'\n')
                if len(active) != len(parts) or any(r['text'] != part or r['state'] != int(changed)
                                                  for r, part in zip(active, parts)):
                    raise ValueError('Native SR panel drops words or changes color state')
                if any(r['active'] for category in ('victory', 'defeat') for r in records[category]):
                    raise ValueError('SR condition changed another panel section')
                payloads = [entries[r['text']] if profile == 'static' else r['text'] for r in active]
                cases.append(dict(source_sha256=sha256(jp.encode('cp932')), members=item['members'],
                                  profile=profile, changed=changed, rows=len(active), native_steps=steps,
                                  keys=[r['text'].hex() for r in active] if profile == 'static' else [],
                                  english=[L.decode(p, mapping) for p in payloads]))
    return cases
