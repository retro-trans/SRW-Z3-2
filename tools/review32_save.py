"""Relocate all three save questions before native paragraph copying/conversion."""
import struct
from tools import ui_hook as H, eboot_text as E, library_runtime as R, library_build as L
from tools.common import sha256
VAS = (0x892668, 0x8926d8, 0x892748)


def plan(original, mapping):
    read = H._reader(original, H._headers(original)[2]); active = E.load()['strings']
    records = {int(r['va'],16):r for r in E.records()}; payloads = []; pointers = []; rows = []
    for va in VAS:
        row = records[va]; raw = row['jp'].encode('utf8')+b'\0'
        if row['family'] != 'system_message' or row['encoding'] != 'utf-8' or read(va,len(raw)) != raw:
            raise ValueError('Save-question source changed')
        english = E.unshow(L.expand(active[row['jp']]['en'], E.resolver()))
        if len(english.split('\n')) != 2:
            raise ValueError('Save-question paragraph count changed')
        carrier = ''.join(R.LETTERS.get(c,c) for c in english).encode('utf8')+b'\0'
        name = 'review32:save:'+hex(va)
        matches = []
        for seg in H._headers(original)[2][:2]:
            for offset in range(seg[2],seg[2]+seg[5]-3,4):
                if original[offset:offset+4] == struct.pack('>I',va):
                    matches.append(seg[3]+offset-seg[2])
        if len(matches) != 1:
            raise ValueError('Save-question pointer binding changed')
        payloads.append((name,carrier)); pointers.append(dict(va=matches[0],key=name,expected=struct.pack('>I',va)))
        rows.append(dict(source_va=va,pointer_va=matches[0],key=name,english=english,
                         carrier_bytes=len(carrier),source_sha256=sha256(raw)))
    return dict(payloads=payloads,pointers=pointers,rows=rows)


def apply(elf, original, planned, addresses):
    read = H._reader(elf,H._headers(elf)[2]); out = bytearray(elf); ranges = []
    for pointer in planned['pointers']:
        va = pointer['va']
        if read(va,4) != pointer['expected']:
            raise ValueError('Save-question pointer was modified')
        at = va-0x10000; out[at:at+4] = struct.pack('>I',addresses[pointer['key']]); ranges.append((at,at+4))
    restored = bytearray(out)
    for a,b in ranges: restored[a:b] = elf[a:b]
    if restored != elf: raise ValueError('Save relocation escaped its three pointers')
    table = H.unicode_table(bytes(out))
    for key,carrier in planned['payloads']:
        row = next(r for r in planned['rows'] if r['key']==key)
        if H.convert(carrier[:-1],table) != E.encode(row['english'], planned['mapping']):
            raise ValueError('Save carrier does not convert to the complete English')
    return bytes(out), dict(rows=planned['rows'],modified_file_ranges=ranges,runtime_verified=False)


def native_lines(elf, source):
    """Run the real question constructor through its paragraph copies."""
    from tools import ppc_exec as P
    mem = P.Memory()
    for i,seg in enumerate(H._headers(elf)[2][:2]):
        mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=i==1)
    mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,source+b'\0')
    state = int.from_bytes(mem.read(H.TOC-0x54b0,4),'big');mem.map(state,bytes(0x100))
    def string(at):
        for length in range(512):
            if mem.read(at+length,1)==b'\0':return mem.read(at,length)
        raise ValueError('Question string does not terminate')
    def memset(vm):mem.write(vm.r[3],bytes([vm.r[4]&255])*vm.r[5]);vm.pc=vm.lr
    def strchr(vm):
        offset=string(vm.r[3]).find(bytes([vm.r[4]&255]));vm.r[3]=vm.r[3]+offset if offset>=0 else 0;vm.pc=vm.lr
    def memcpy(vm):mem.write(vm.r[3],mem.read(vm.r[4],vm.r[5]));vm.pc=vm.lr
    def strncpy(vm):
        raw=string(vm.r[4])[:vm.r[5]];mem.write(vm.r[3],raw+bytes(vm.r[5]-len(raw)));vm.pc=vm.lr
    def snprintf(vm):
        raw=string(vm.r[5])
        if b'%'in raw:raise ValueError('Unexpected format variable in save question')
        mem.write(vm.r[3],raw[:vm.r[4]-1]+b'\0');vm.r[3]=len(raw);vm.pc=vm.lr
    vm=P.Machine(mem);vm.r=[0x770000+r for r in range(32)]
    vm.r[1]=0x40008000;vm.r[2]=H.TOC;vm.r[3:8]=[0x41000000,2,0,0,0]
    vm.pc=0x168a1c;vm.lr=0xdead0000
    vm.hooks={0x69327c:memset,0x68f52c:strchr,0x6872cc:memcpy,0x68fca0:strncpy,0x69020c:snprintf}
    vm.run({0x9af68},limit=10000)
    lines=[string(p)for p in vm.r[4:8]if p]
    if lines!=source.split(b'\n'):
        raise ValueError('Native save question loses a paragraph or clips a carrier')
    frame=0x40008000-0x4a0
    if mem.read(frame+0x430,8)!=int(0x770000+18).to_bytes(8,'big'):
        raise ValueError('Save-question rows overwrite the native frame')
    return lines,vm.steps
