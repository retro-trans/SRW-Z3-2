"""Relocate static mission text after the game's bounded native copy.

The UI refresh calls the mission substitution helper with a 128-byte inline
destination (0x18c2dc). Store a short, source-bound display key there, then let
the existing exact-match drawer hook return the complete measured English.
Conditions with live names/counters retain the existing substitution route.
"""
import struct
from tools.common import sha256
from tools import mission_text as M,library_build as L,ui_hook as H

def rows(rendered):
    return [dict(jp=jp,key='条件'+''.join(chr(0xff10+int(c))for c in '%03d'%n),en=en)
            for n,(jp,en)in enumerate(sorted(rendered.items()))
            if not any(p in jp for p in M.PLACEHOLDERS)]

def stage_text(rendered):
    result=dict(rendered)
    for row in rows(rendered):result[row['jp']]=row['key']
    return result

def hook_entries(original,rendered,mapping):
    read=H._reader(original,H._headers(original)[2])
    if read(0x18c2d8,24)!=bytes.fromhex('389e001438a0008078840020786300203bde009c4bfd0bfd'):
        raise ValueError('Mission UI bounded-copy binding changed')
    if read(0x1aaa38,4)!=bytes.fromhex('38a0012e'):
        raise ValueError('Mission script capacity changed')
    out=[]
    for row in rows(rendered):
        key=row['key'].encode('cp932');en=L.encode(row['en'],mapping)
        if len(key)!=10 or H.extent(key+b'\0')!=10:raise ValueError('Unsafe mission display key')
        out.append(dict(id='mission-display:'+sha256(row['jp'].encode('cp932'))[:16],key=key,english=en))
    return out

def copy_cases(elf,rendered,mapping):
    """Execute the original bounded substitution copier with no live tokens.

    Libc calls are bounded models of memset/strlen/strncmp/strncat. All
    mission substitution instructions themselves execute without shortcuts.
    A canary immediately after the 128-byte destination detects overflow.
    """
    from tools import ppc_exec as P
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x10000))
    def cstring(at):
        out=bytearray()
        while mem.read(at+len(out),1)!=b'\0':
            out+=mem.read(at+len(out),1)
            if len(out)>8192:raise ValueError('Native copier scanned beyond its string')
        return bytes(out)
    def memset(vm):mem.write(vm.r[3],bytes([vm.r[4]&255])*vm.r[5]);vm.pc=vm.lr
    def strlen(vm):vm.r[3]=len(cstring(vm.r[3]));vm.pc=vm.lr
    def strncmp(vm):
        a=cstring(vm.r[3])[:vm.r[5]];b=cstring(vm.r[4])[:vm.r[5]]
        vm.r[3]=(0 if a==b else -1 if a<b else 1)&P.M64;vm.pc=vm.lr
    def strncat(vm):
        dst=cstring(vm.r[3]);add=cstring(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3]+len(dst),add+b'\0');vm.pc=vm.lr
    cases=[]
    for row in rows(rendered):
        raw=row['key'].encode('cp932');mem.write(0x41000000,raw+b'\0')
        mem.write(0x41003000,bytes(128)+b'CANARY');mem.write(0x41005000,bytes(8))
        m=P.Machine(mem);m.r=[0x770000+i for i in range(32)]
        m.r[1]=0x40003e00;m.r[3:7]=[0x41000000,0x41003000,128,0x41005000]
        m.lr=0x42000000;m.pc=0x1be808
        m.hooks.update({0x69327c:memset,0x68a2ac:strlen,0x693350:strncmp,0x68f978:strncat})
        m.run({0x42000000},limit=20000)
        if cstring(0x41003000)!=raw or mem.read(0x41003080,6)!=b'CANARY':
            raise ValueError('Mission key corrupted by native bounded copy')
        cases.append(dict(key=row['key'],source_sha256=sha256(row['jp'].encode('cp932')),
                          key_bytes=len(raw),relocated_english_bytes=len(L.encode(row['en'],mapping)),steps=m.steps))
    return cases
