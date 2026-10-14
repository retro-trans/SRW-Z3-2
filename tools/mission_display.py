"""Relocate each static mission line after native copying and numbering.

The operation-condition reader uses 302-byte strings (0x1aaa38); the real line
composer uses 103-byte records with 101-byte text fields (0x1aa6e8). Short
source-bound line keys preserve the native line count, numbering and state.
The drawer returns one complete measured English line per native row. Live
names/counters retain native substitution with byte-aware wrapping.
"""
import struct
from functools import lru_cache
from tools.common import sha256
from tools import mission_text as M,library_build as L,ui_hook as H

COMPOSER=(0x1aa6e8,0x1aa91c)
COMPOSER_SHA='af2e291aa8489cb77d122f07dc90f4e25798e816d02cfdfa2c3d9f30873831a1'
PREFIXES=('', '１．', '２．', '３．')

@lru_cache(None)
def advance(c):
    from tools.ui_vwf_build import raster
    return raster(c)[1] if ord(c)<128 else 32

def displayed_english(english,number):
    if not number:return english
    # Two native full-width cells precede numbered lines and continuations.
    wrapped=M.wrap(english,advance,units=M.LINE_UNITS-64)
    return PREFIXES[number]+wrapped.replace('\n','\n　　')

def line_texts(row):
    return M.wrap(row.get('raw_en',row['en']),advance,units=M.LINE_UNITS-64).split('\n')

def line_key(row,index):
    return row['key'] if not index else row['key']+'段'+''.join(chr(0xff10+int(c))for c in str(index))

def stage_key(row):return '\n'.join(line_key(row,i)for i in range(len(line_texts(row))))

def lookup_row(elf,runner,row,mapping):
    read=H._reader(elf,H._headers(elf)[2]);lines=[];steps=0
    for index,text in enumerate(line_texts(row)):
        key=line_key(row,index).encode('cp932');expected=L.encode(text,mapping)
        pointer,n=runner.run(key+b'\0');steps+=n
        if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Mission continuation untranslated')
        lines.append(L.decode(expected,mapping))
    return dict(english='\n'.join(lines),steps=steps,rows=len(lines))

def rows(rendered):
    authored=M.load()['strings'];resolver=M.resolver()
    return [dict(jp=jp,key='条件'+''.join(chr(0xff10+int(c))for c in '%03d'%n),en=en,
                 raw_en=L.expand(authored[jp]['en'],resolver) if jp in authored else en)
            for n,(jp,en)in enumerate(sorted(rendered.items()))
            if not any(p in jp for p in M.PLACEHOLDERS)]

def stage_text(rendered):
    result=dict(rendered)
    for row in rows(rendered):result[row['jp']]=stage_key(row)
    return result

def hook_entries(original,rendered,mapping):
    read=H._reader(original,H._headers(original)[2])
    if read(0x18c2d8,24)!=bytes.fromhex('389e001438a0008078840020786300203bde009c4bfd0bfd'):
        raise ValueError('Mission UI bounded-copy binding changed')
    if read(0x1aaa38,4)!=bytes.fromhex('38a0012e'):
        raise ValueError('Mission script capacity changed')
    if sha256(read(COMPOSER[0],COMPOSER[1]-COMPOSER[0]))!=COMPOSER_SHA:
        raise ValueError('Mission numbered composer changed')
    for number,prefix in enumerate(PREFIXES):
        pointer=struct.unpack('>I',read(H.TOC-0x4b1c+number*4,4))[0]
        encoded=prefix.encode('cp932')+b'\0'
        if read(pointer,len(encoded))!=encoded:raise ValueError('Mission prefix changed')
    out=[]
    for row in rows(rendered):
        key=row['key'].encode('cp932')
        if len(key)!=10 or H.extent(key+b'\0')!=10:raise ValueError('Unsafe mission display key')
        for index,text in enumerate(line_texts(row)):
            for number,prefix in enumerate(PREFIXES):
                lead=prefix if not index else '　　' if number else ''
                out.append(dict(id='mission-display:'+sha256(row['jp'].encode('cp932'))[:16]+':'+str(number)+':'+str(index),
                    key=(lead+line_key(row,index)).encode('cp932'),english=L.encode(lead+text,mapping)))
    return list({r['key']:r for r in out}.values())

def composition_cases(elf,rendered,mapping):
    """Execute the real numbering/line composer before checking drawer keys."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x4000))
    def cstring(at):
        out=bytearray()
        while mem.read(at+len(out),1)!=b'\0':
            out+=mem.read(at+len(out),1)
            if len(out)>4096:raise ValueError('Mission composer string unbounded')
        return bytes(out)
    def memset(vm):mem.write(vm.r[3],bytes([vm.r[4]&255])*vm.r[5]);vm.pc=vm.lr
    def strlen(vm):vm.r[3]=len(cstring(vm.r[3]));vm.pc=vm.lr
    def strchr(vm):
        text=cstring(vm.r[3]);offset=text.find(bytes([vm.r[4]&255]))
        vm.r[3]=vm.r[3]+offset if offset>=0 else 0;vm.pc=vm.lr
    def strncat(vm):
        dst=cstring(vm.r[3]);add=cstring(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3]+len(dst),add+b'\0');vm.pc=vm.lr
    cases=[]
    for row in rows(rendered):
        for number,prefix in enumerate(PREFIXES):
            parts=line_texts(row);capacity=len(parts)*103
            mem.write(0x41000000,stage_key(row).encode('cp932')+b'\0')
            mem.write(0x41001000,bytes(capacity)+b'CANARY')
            m=P.Machine(mem);m.r[1]=0x40003e00;m.r[2]=H.TOC
            m.r[3:7]=[0x41000000,0x41001000,number,number]
            m.lr=0x42000000;m.pc=COMPOSER[0]
            m.hooks.update({0x69327c:memset,0x68a2ac:strlen,0x68f52c:strchr,0x68f978:strncat})
            m.run({0x42000000},limit=2000)
            if m.r[3]!=len(parts):
                raise ValueError('Actual numbered mission key differs')
            if mem.read(0x41001000+capacity,6)!=b'CANARY':
                raise ValueError('Mission composition state or bounds changed')
            keys=[]
            for index in range(len(parts)):
                at=0x41001000+index*103;key=cstring(at+2)
                lead=prefix if not index else '　　' if number else ''
                if key!=(lead+line_key(row,index)).encode('cp932') or mem.read(at,2)!=bytes((1,number)):
                    raise ValueError('Native continuation key or state differs')
                keys.append(key.hex())
            cases.append(dict(keys=keys,number=number,rows=len(parts),steps=m.steps))
    return cases

def live_cases(elf,rendered,mapping):
    """Execute substitution and numbering with defaults and maximum-size names."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x4000))
    def string(at):
        out=bytearray()
        while mem.read(at+len(out),1)!=b'\0':
            out+=mem.read(at+len(out),1)
            if len(out)>4096:raise ValueError('Live mission string unbounded')
        return bytes(out)
    def memset(vm):mem.write(vm.r[3],bytes([vm.r[4]&255])*vm.r[5]);vm.pc=vm.lr
    def strlen(vm):vm.r[3]=len(string(vm.r[3]));vm.pc=vm.lr
    def strncmp(vm):
        a=string(vm.r[3])[:vm.r[5]];b=string(vm.r[4])[:vm.r[5]]
        vm.r[3]=(0 if a==b else -1 if a<b else 1)&P.M64;vm.pc=vm.lr
    def strchr(vm):
        offset=string(vm.r[3]).find(bytes([vm.r[4]&255]))
        vm.r[3]=vm.r[3]+offset if offset>=0 else 0;vm.pc=vm.lr
    def strncat(vm):
        dst=string(vm.r[3]);add=string(vm.r[4])[:vm.r[5]]
        mem.write(vm.r[3]+len(dst),add+b'\0');vm.pc=vm.lr
    hooks={0x69327c:memset,0x68a2ac:strlen,0x693350:strncmp,0x68f52c:strchr,0x68f978:strncat}
    live=[(jp,en)for jp,en in rendered.items()if any(p in jp for p in M.PLACEHOLDERS)]
    cases=[]
    for ordinal,(jp,en)in enumerate(live):
        for profile in ('default','maximum-custom'):
            source=L.encode(en,mapping);expected=source;pairs=[]
            for i,token in enumerate(M.PLACEHOLDERS):
                key=token.encode('cp932')
                value=L.encode('1234567890',mapping) if token.startswith('ローカル') else (
                    'Ａ'.encode('cp932')*20 if profile=='maximum-custom' else
                    L.encode('Hibiki Kamishiro' if token=='主人公フルネーム' else 'Kamishiro' if token=='カミシロＮ' else 'Hibiki',mapping))
                key_va=0x41000400+i*0x100;value_va=key_va+0x60
                mem.write(key_va,key+b'\0');mem.write(value_va,value+b'\0');pairs += [key_va,value_va]
                expected=expected.replace(key,value)
            mem.write(0x41000200,struct.pack('>16I',*(pairs+[0,0])))
            mem.write(0x41000000,source+b'\0');mem.write(0x41001000,bytes(303)+b'CANARY')
            m=P.Machine(mem);m.r[1]=0x40003e00;m.r[2]=H.TOC
            m.r[3:7]=[0x41000000,0x41001000,302,0x41000200]
            m.pc=0x1be808;m.lr=0x42000000;m.hooks=hooks;m.run({m.lr},limit=100000)
            if string(0x41001000)!=expected or mem.read(0x4100112f,6)!=b'CANARY':
                raise ValueError('Live mission substitution clips text or overruns its field')
            parts=expected.split(b'\n');copy_steps=m.steps
            for number,prefix in enumerate(PREFIXES):
                capacity=len(parts)*103;mem.write(0x41002000,bytes(capacity)+b'CANARY')
                m=P.Machine(mem);m.r[1]=0x40003e00;m.r[2]=H.TOC
                m.r[3:7]=[0x41001000,0x41002000,number,number]
                m.pc=COMPOSER[0];m.lr=0x42000000;m.hooks=hooks;m.run({m.lr},limit=10000)
                if m.r[3]!=len(parts) or mem.read(0x41002000+capacity,6)!=b'CANARY':
                    raise ValueError('Live mission composition escaped native rows')
                for i,part in enumerate(parts):
                    at=0x41002000+i*103;lead=(prefix.encode('cp932') if i==0 else '　　'.encode('cp932')) if number else b''
                    if string(at+2)!=lead+part or mem.read(at,2)!=bytes((1,number)):
                        raise ValueError('Live mission composition truncates or alters a row')
                cases.append(dict(ordinal=ordinal,source_sha256=sha256(jp.encode('cp932')),profile=profile,
                    number=number,rows=len(parts),bytes=len(expected),copy_steps=copy_steps,compose_steps=m.steps))
    return cases

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
        raw=stage_key(row).encode('cp932');mem.write(0x41000000,raw+b'\0')
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
