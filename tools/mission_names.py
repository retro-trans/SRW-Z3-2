"""Translate default protagonist values at the mission substitution boundary."""
import struct
from tools import ui_hook as H,eboot_text as E
from tools.common import sha256
from tools.link_layout import Asm

CONSUMER=(0x15cee8,0x15d108)
CONSUMER_SHA='41e3913c2edf81af7af8af0907c6fb75d88826570c9c567ccea22a2140f4f887'
# These four stores populate key/value pairs passed to the text substitution
# function. The pointers are display values, never writable saved name fields.
SITES=((0x15d068,24,212), (0x15d074,7,228), (0x15d07c,3,236), (0x15d0a0,11,220))
FULL={'ヒビキ・カミシロ':'Hibiki Kamishiro','ヒビキカミシロ':'Hibiki Kamishiro',
      'カミシロ・ヒビキ':'Kamishiro Hibiki','カミシロヒビキ':'Kamishiro Hibiki'}


def payloads(mapping):
    return [('mission-name:'+en,E.encode(en,mapping)+b'\0')for en in sorted(set(FULL.values()))]


def stub(va,site,reg,slot,addresses):
    a=Asm(va)
    a.d(0xf8000001,1,1,-0x60)
    for r,off in ((9,0x10),(12,0x18)):a.d(0xf8000000,r,1,off)
    a.e(0x7d800026);a.d(0x90000000,12,1,0x20) # mfcr r12
    choices=FULL if reg==24 else ({'カミシロ':'Kamishiro'}if reg==3 else {'ヒビキ':'Hibiki'})
    a.d(0x2c000000,0,reg,0);a.br(0x41820000,'done')
    for n,(jp,en)in enumerate(choices.items()):
        for i,b in enumerate(jp.encode('cp932')+b'\0'):
            a.d(0x88000000,9,reg,i);a.d(0x2c000000,0,9,b);a.br(0x40820000,'next%d'%n)
        a.ptr(reg,addresses[('mission-name:'if reg==24 else 'name:')+en])
        a.br(0x48000000,'done');a.label('next%d'%n)
    a.label('done');a.d(0x80000000,12,1,0x20);a.e(0x7d8ff120)
    for r,off in ((9,0x10),(12,0x18)):a.d(0xe8000000,r,1,off)
    a.d(0x38000000,1,1,0x60)
    a.d(0x90000000,reg,1,slot);a.jump(site+4)
    return a.code()


def apply(elf,addresses):
    phoff,_,phs,_=H._headers(elf);first,second=phs[:2];read=H._reader(elf,phs)
    if sha256(read(CONSUMER[0],CONSUMER[1]-CONSUMER[0]))!=CONSUMER_SHA:
        raise ValueError('Mission name substitution consumer changed')
    cursor=(first[5]+15)&~15;out=bytearray(elf);ranges=[];stubs=[]
    for site,reg,slot in SITES:
        original=0x90000000|reg<<21|1<<16|slot
        if read(site,4)!=struct.pack('>I',original):raise ValueError('Mission value store differs')
        va=cursor+first[3];code=stub(va,site,reg,slot,addresses);end=cursor+len(code)
        if end>second[2]or any(elf[cursor:end]):raise ValueError('Mission name RX gap occupied')
        out[cursor:end]=code;at=site-first[3]
        struct.pack_into('>I',out,at,H.branch(site,va))
        ranges.extend(((cursor,end),(at,at+4)))
        stubs.append(dict(site=site,va=va,register=reg,stack_slot=slot,bytes=len(code)))
        cursor=(end+15)&~15
    struct.pack_into('>QQ',out,phoff+32,end,end);ranges.append((phoff+32,phoff+48))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Mission name edit escaped guarded spans')
    return bytes(out),dict(stubs=stubs,consumer_sha256=CONSUMER_SHA,
        save_fields_modified=False,custom_names_preserved=True,runtime_verified=False)


def verify(elf,mapping,addresses):
    """Run each installed substitution store; custom values must pass unchanged."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for i,s in enumerate(H._headers(elf)[2][:2]):mem.map(s[3],elf[s[2]:s[2]+s[5]],writable=i==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x42000000,bytes(128));cases=[]
    for site,reg,slot in SITES:
        choices=FULL if reg==24 else ({'カミシロ':'Kamishiro'}if reg==3 else {'ヒビキ':'Hibiki'})
        for jp,en in list(choices.items())+[('アキラ',None),('',None)]:
            raw=jp.encode('cp932')+b'\0';mem.write(0x42000000,raw)
            m=P.Machine(mem);m.r=[0x770000+i for i in range(32)]
            m.r[1]=0x40003e00;m.r[reg]=0x42000000;m.cr=0x456789ab;m.lr=0x123456
            before=m.r[:];m.pc=site;m.run({site+4},limit=2000)
            pointer=struct.unpack('>I',mem.read(m.r[1]+slot,4))[0]
            expected=addresses[('mission-name:'if reg==24 else 'name:')+en]if en else 0x42000000
            if pointer!=expected or m.r[reg]!=expected:raise ValueError('Mission substitution pointer differs')
            for i in range(32):
                if i!=reg and m.r[i]!=before[i]:raise ValueError('Mission substitution lost a register')
            if m.cr!=0x456789ab or m.lr!=0x123456 or mem.read(0x42000000,len(raw))!=raw:
                raise ValueError('Mission substitution changed caller state or name bytes')
            if en and mem.read(pointer,len(E.encode(en,mapping))+1)!=E.encode(en,mapping)+b'\0':
                raise ValueError('Mission substitution payload differs')
            cases.append(dict(site=site,source=jp,english=en,custom_unchanged=en is None,steps=m.steps))
    return cases
