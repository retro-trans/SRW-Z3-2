"""Translate native Clear Report resource rows without changing award values."""
import struct
from tools.common import sha256
from tools import ui_hook as H,ui_runtime as R,eboot_text as E

TEXT={0x9f1340:('以下のボーナスを得ました。','Bonus received:'),
      0x9f13a8:('以下のボーナスを得ました。','Bonus received:'),
      0x9f1360:('＜Ｚチップ　：','Z Chips: '),0x9f1370:('＞',''),
      0x9f13c8:('＜資金　：','Funds: '),0x9f13d8:('＞','')}
CODE={(0x1858a8,0x185990):'67bf980aca53927920d89c2ac779785a3cd8d16f43380e6195ec110f2322536a',
      (0x15d108,0x15d328):'67c6a7c3d1fa7305ba58ddf0eb75d868cf15e4bd426e05066535f434be026eb6'}
PADDING={0x185ba8:0x38c00006,0x185fbc:0x38c00006}

def guard(elf):
    read=H._reader(elf,H._headers(elf)[2])
    for (lo,hi),digest in CODE.items():
        if sha256(read(lo,hi-lo))!=digest:raise ValueError('Clear Report composer changed')
    for va,(jp,en)in TEXT.items():
        raw=jp.encode('cp932')+b'\0'
        if read(va,len(raw))!=raw:raise ValueError('Clear Report fragment changed')
    for va,word in PADDING.items():
        if read(va,4)!=struct.pack('>I',word):raise ValueError('Resource amount padding consumer changed')

def plan(original,mapping):
    guard(original);payloads=[];pointers=[]
    for va,(jp,en)in TEXT.items():
        refs=R.toc_references(original,va)
        if len(refs)!=1 or len(refs[0]['consumer_loads'])!=1:raise ValueError('Ambiguous Clear Report fragment consumer')
        identity='review24:report:%x'%va
        encoded=E.encode(en,mapping)+b'\0'
        if len(encoded)>81:raise ValueError('Report exceeds native line buffer')
        payloads.append((identity,encoded))
        pointers.extend(dict(ref,id=identity,old=va)for ref in refs)
    return dict(payloads=payloads,pointers=pointers,inline=[],unresolved=[],
        report=dict(clear_report_fragments=len(payloads),runtime_verified=False))

def apply(elf,original,planned,payload_vas):
    guard(original)
    output,report=R.apply(elf,planned,payload_vas);out=bytearray(output)
    for va,word in PADDING.items():
        at=va-0x10000
        if output[at:at+4]!=struct.pack('>I',word):raise ValueError('Padding instruction already changed')
        struct.pack_into('>I',out,at,0x38c00000) # li r6,0: no six-cell numeric padding
    restored=bytearray(out)
    for va in PADDING:restored[va-0x10000:va-0x10000+4]=output[va-0x10000:va-0x10000+4]
    if restored!=output:raise ValueError('Clear Report instruction isolation failed')
    return bytes(out),dict(report,padding_sites=[hex(a)for a in PADDING],numeric_conversion_unchanged=True,
        isolation=True,output_sha256=sha256(out))

def resource(elf,kind,value):
    """Run the native composer and fullwidth number routine; adapt libc only."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]]+bytes(seg[6]-seg[5]))
    stack=mem.map(0x40000000,b'\x5c'*0x4000);buffer=mem.map(0x41000000,b'\x88'*0x200)
    m=P.Machine(mem);m.r=[0x9000+n for n in range(32)];m.r[1]=0x40002000;m.r[2]=H.TOC
    read=H._reader(elf,H._headers(elf)[2]);prefix,suffix,site=(0x4f38,0x4f34,0x185ba8)if kind=='chips'else(0x4f48,0x4f44,0x185fbc)
    m.r[3]=0x41000010;m.r[4]=int.from_bytes(read(H.TOC-prefix,4),'big');m.r[5]=value
    m.r[6]=int.from_bytes(read(site,4),'big')&0xffff;m.r[7]=int.from_bytes(read(H.TOC-suffix,4),'big')
    m.pc=0x1858a8;m.lr=0xdead0000;before=m.r[:]
    def string(at):
        out=bytearray()
        for n in range(128):
            b=mem.read(at+n,1)
            if b==b'\0':return bytes(out)
            out.extend(b)
        raise ValueError('Native report string exceeds line buffer')
    while m.pc!=0xdead0000:
        if m.steps>50000:raise ValueError('Report execution exceeded bound')
        if m.pc==0x68a2ac:m.r[3]=len(string(m.r[3]));m.pc=m.lr
        elif m.pc==0x68f400:
            dest=m.r[3];raw=string(dest)+string(m.r[4]);mem.write(dest,raw+b'\0');m.pc=m.lr
        else:m.step()
    result=string(0x41000010)
    if len(result)>81 or buffer[:16]!=b'\x88'*16 or buffer[16+len(result)+1:]!=b'\x88'*(len(buffer)-17-len(result)):
        raise ValueError('Report buffer canary changed')
    if any(m.r[r]!=before[r]for r in [1,2,*range(26,32)]):raise ValueError('Report callee-saved register changed')
    return result,m.steps

def president(elf,value,peerless=False):
    """Execute either actual three-row PP branch and its numeric converter."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]]+bytes(seg[6]-seg[5]))
    mem.map(0x40000000,b'\x5c'*0x4000);mem.map(0x41000000,bytes(0x200))
    m=P.Machine(mem);m.r=[0x9000+n for n in range(32)];m.r[1]=0x40002000;m.r[2]=H.TOC
    m.r[29]=m.r[1]+0xd0;m.r[31]=0x41000000
    mem.write(0x4100008c,struct.pack('>I',0x41000100))
    value_at,flag_at=(0x41000120,0x41000129)if peerless else(0x41000104,0x41000124)
    mem.write(value_at,struct.pack('>I',value));mem.write(flag_at,b'\x01')
    m.r[24]=m.r[1]+0xd0;m.r[25]=0;m.r[30]=0
    m.pc=0x185fec if peerless else 0x185e08;stop=0x185bec if peerless else 0x185afc
    def string(at):
        out=bytearray()
        for n in range(128):
            b=mem.read(at+n,1)
            if b==b'\0':return bytes(out)
            out.extend(b)
        raise ValueError('PP report string exceeds line buffer')
    while m.pc!=stop:
        if m.steps>50000:raise ValueError('PP report execution exceeded bound')
        if m.pc==0x68a2ac:m.r[3]=len(string(m.r[3]));m.pc=m.lr
        elif m.pc==0x68f400:
            dest=m.r[3];raw=string(dest)+string(m.r[4]);mem.write(dest,raw+b'\0');m.pc=m.lr
        elif m.pc==0x69020c:
            raw=string(m.r[5]);raw=raw.replace(b'%s',string(m.r[6]))if b'%s'in raw else raw
            if len(raw)>=m.r[4]:raise ValueError('Native snprintf would truncate the PP report')
            mem.write(m.r[3],raw+b'\0');m.r[3]=len(raw);m.pc=m.lr
        else:m.step()
    rows=[string(m.r[1]+0xd0+82*n)for n in range(3)]
    for n,row in enumerate(rows):
        if mem.read(m.r[1]+0xd0+82*n+len(row)+1,81-len(row))!=b'\x5c'*(81-len(row)):
            raise ValueError('PP report row canary changed')
    if mem.read(value_at,4)!=struct.pack('>I',value)or mem.read(flag_at,1)!=b'\0':
        raise ValueError('PP amount or completion state differs')
    return rows,m.steps
