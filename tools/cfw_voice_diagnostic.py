"""0.5.54: observe voice bank loads and replace only fallback quote text.

No file I/O, allocations, audio calls or selection changes in the injected code.
Reuse the existing Library private alphabet and reserved RW lookup headroom.
"""
import struct
from tools import ui_hook as H, srvc as S, library_runtime as L, cfw_self as C
from tools.link_layout import Asm
from tools.common import sha256

VERSION='0.5.54'
POLL=0x139084
FALLBACK=0x12e700
GUARDS={POLL:0x901f0020,FALLBACK:0x8362a014}
RESERVED=0x300
TEXT=0x100
DIGITS=0x200
VALUES=0xc0
FIELDS=(('B',3),('H',2),('N',4),('O',6),('S',5),('F',1),('C',4))
FRAME=0xd0
REGS=(0,3,4,5,6,7,8,9,10,11,12)


def text_layout():
    pieces=('0.5.54 B',' H',' N','\\nO',' S',' F','C')
    out=bytearray()
    positions={}
    for literal,(name,digits) in zip(pieces,FIELDS):
        for character in literal:
            out+=character.encode() if character in '\\n' and literal=='\\nO' and character!='O' else L.LETTERS[character].encode('utf8')
        positions[name]=(len(out),digits)
        out+=L.LETTERS['0'].encode('utf8')*digits
    if len(out)+1>134:
        raise ValueError('Diagnostic exceeds native caption buffer')
    return bytes(out)+b'\0',positions


def save(a):
    a.d(0xf8000001,1,1,-FRAME)
    for index,register in enumerate(REGS):
        a.d(0xf8000000,register,1,0x20+index*8)
    a.e(0x7c000026)
    a.d(0xf8000000,0,1,0x80)


def restore(a):
    a.d(0xe8000000,0,1,0x80)
    a.e(0x7c0ff120)
    for index,register in reversed(list(enumerate(REGS))):
        a.d(0xe8000000,register,1,0x20+index*8)
    a.d(0x38000000,1,1,FRAME)


def clear32(a,target,source):
    a.e(0x78000020|source<<21|target<<16)


def poll_stub(va,state):
    a=Asm(va)
    save(a)
    a.ptr(3,state)
    a.d(0xe8000000,8,1,0x20) # original r0 = completed read buffer
    a.d(0x38000000,4,3,16)
    a.d(0x38000000,5,0,8)
    a.label('find')
    a.d(0x80000000,6,4,0)
    a.e(H._cmpx(0,0,0,6,8))
    a.br(0x41820000,'found')
    a.d(0x38000000,4,4,16)
    a.d(0x38000000,5,5,-1)
    a.d(0x2c000000,0,5,0)
    a.br(0x40820000,'find')
    a.d(0x80000000,6,3,0)
    a.e(21<<26|6<<21|6<<16|29<<6|31<<1) # cursor & 7
    a.d(0x1c000000,4,6,16)
    a.x(0x7c000214,4,4,3)
    a.d(0x38000000,4,4,16)
    a.d(0x38000000,6,6,1)
    a.d(0x90000000,6,3,0)
    a.label('found')
    a.d(0x90000000,8,4,0)
    a.d(0xa0000000,7,31,0x2c)
    a.d(0x28000000,0,7,S.NBLOCKS-1)
    a.br(0x41810000,'bad')
    a.d(0x80000000,9,31,0x28)
    a.d(0x1c000000,6,7,4)
    a.x(0x7c000214,9,9,6)
    clear32(a,9,9)
    a.d(0x80000000,10,9,0)
    a.d(0x80000000,11,9,4)
    a.x(0x7c000050,11,10,11)
    a.br(0x48000000,'store')
    a.label('bad')
    for register in (7,10,11):
        a.d(0x38000000,register,0,-1)
    a.label('store')
    for register,offset in ((7,4),(10,8),(11,12)):
        a.d(0x90000000,register,4,offset)
    restore(a)
    a.e(GUARDS[POLL])
    a.jump(POLL+4)
    return a.code()


def fallback_stub(va,state,positions):
    a=Asm(va)
    save(a)
    a.ptr(3,state)
    a.d(0x38000000,6,0,-1)
    for index in range(len(FIELDS)):
        a.d(0x90000000,6,3,VALUES+index*4)
    # Same bank-slot calculation as the native entry builder at 0x12eb80.
    a.d(0x28000000,0,24,3)
    a.br(0x41810000,'entry')
    a.d(0x28000000,0,22,1)
    a.br(0x41810000,'entry')
    a.d(0x38000000,4,0,0)
    a.d(0x28000000,0,24,1)
    a.br(0x40810000,'side')
    a.d(0x38000000,4,0,64)
    a.label('side')
    a.d(0x1c000000,5,22,32)
    a.x(0x7c000214,4,4,5)
    a.x(0x7c000214,4,4,25)
    clear32(a,4,4)
    a.d(0x80000000,8,4,0)
    a.d(0x2c000000,0,8,0)
    a.br(0x41820000,'entry')
    a.d(0x88000000,6,8,0)
    a.d(0x90000000,6,3,VALUES+4)
    a.d(0x88000000,7,8,6)
    a.d(0x88000000,10,8,7)
    a.d(0x1c000000,10,10,256)
    a.x(0x7c000378,10,7,7)
    a.d(0x90000000,7,3,VALUES+8)
    a.d(0x38000000,4,3,16)
    a.d(0x38000000,5,0,8)
    a.label('find')
    a.d(0x80000000,9,4,0)
    a.e(H._cmpx(0,0,0,9,8))
    a.br(0x41820000,'found')
    a.d(0x38000000,4,4,16)
    a.d(0x38000000,5,5,-1)
    a.d(0x2c000000,0,5,0)
    a.br(0x40820000,'find')
    a.br(0x48000000,'entry')
    a.label('found')
    for source,target in ((4,VALUES),(8,VALUES+12),(12,VALUES+16)):
        a.d(0x80000000,6,4,source)
        a.d(0x90000000,6,3,target)
    a.label('entry')
    a.d(0x80000000,6,29,0xc4)
    a.d(0x28000000,0,6,15)
    a.br(0x41810000,'format')
    a.d(0x1c000000,6,6,12)
    a.x(0x7c000214,4,29,6)
    clear32(a,4,4)
    a.d(0x88000000,6,4,5)
    a.d(0x90000000,6,3,VALUES+20)
    a.d(0xa0000000,6,4,0)
    a.d(0x90000000,6,3,VALUES+24)
    a.label('format')
    a.ptr(8,state+DIGITS)
    for index,(name,digits) in enumerate(FIELDS):
        position,_=positions[name]
        a.d(0x80000000,6,3,VALUES+index*4)
        for digit in range(digits):
            shift=4*(digits-digit-1)
            a.e(21<<26|6<<21|7<<16|((32-shift)&31)<<11|28<<6|31<<1)
            a.d(0x1c000000,7,7,4)
            a.x(0x7c000214,10,8,7)
            for byte in range(3):
                a.d(0x88000000,9,10,byte)
                a.d(0x98000000,9,3,TEXT+position+digit*3+byte)
    restore(a)
    a.ptr(27,state+TEXT)
    a.jump(FALLBACK+4)
    return a.code()


def patch(elf,build):
    for va,expected in GUARDS.items():
        if S.word(elf,va)!=expected:
            raise ValueError('Voice hook source changed: '+hex(va))
    phoff,headers=C.program_headers(elf)
    rx=headers[2]
    if rx[3]!=0x1800000 or rx[2]+rx[5]!=len(elf):
        raise ValueError('Expected sealed DLC RX extension at end of ELF')
    table=build['executable']['ui_hook']['table']
    used=(table['used_bytes']+15)&~15
    state=H.EXT_VA+used
    at=S.va_to_offset(elf,state,RESERVED)
    if used+RESERVED>table['ext_size'] or any(elf[at:at+RESERVED]):
        raise ValueError('Diagnostic headroom is occupied')
    template,positions=text_layout()
    raw=bytearray(RESERVED)
    raw[TEXT:TEXT+len(template)]=template
    for index,digit in enumerate('0123456789ABCDEF'):
        raw[DIGITS+index*4:DIGITS+index*4+3]=L.LETTERS[digit].encode('utf8')
    for character in set('0.5.54 BHNOSFC0123456789ABCDEF'):
        if H.utf8_key(L.LETTERS[character].encode('utf8'),elf)!=bytes.fromhex(build['mapping'][character]):
            raise ValueError('Existing private alphabet differs: '+character)
    cursor=(rx[3]+rx[5]+15)&~15
    poll=poll_stub(cursor,state)
    fallback_va=(cursor+len(poll)+15)&~15
    fallback=fallback_stub(fallback_va,state,positions)
    code=bytes(cursor-rx[3]-rx[5])+poll+bytes(fallback_va-cursor-len(poll))+fallback
    out=bytearray(elf)+code
    out[at:at+RESERVED]=raw
    for site,target in ((POLL,cursor),(FALLBACK,fallback_va)):
        struct.pack_into('>I',out,S.va_to_offset(elf,site),H.branch(site,target))
    new_rx=list(rx)
    new_rx[5]+=len(code)
    new_rx[6]+=len(code)
    C.PH.pack_into(out,phoff+2*C.PH.size,*new_rx)
    allowed=[(at,at+RESERVED),(phoff+2*C.PH.size,phoff+3*C.PH.size)]
    allowed += [(S.va_to_offset(elf,site),S.va_to_offset(elf,site)+4) for site in GUARDS]
    restored=bytearray(out[:len(elf)])
    for first,last in allowed:
        restored[first:last]=elf[first:last]
    if restored!=elf:
        raise ValueError('Diagnostic changes escape approved spans')
    C.program_headers(bytes(out))
    return bytes(out),dict(version=VERSION,parent_elf_sha256=sha256(elf),
        output_elf_sha256=sha256(out),state_va=state,state_bytes=RESERVED,
        text_va=state+TEXT,text_utf8_bytes=len(template)-1,caption_capacity=134,
        poll_stub_va=cursor,poll_stub_bytes=len(poll),fallback_stub_va=fallback_va,
        fallback_stub_bytes=len(fallback),hook_sites={hex(k):hex(v) for k,v in
            ((POLL,cursor),(FALLBACK,fallback_va))},modified_ranges=allowed,
        appended_code_bytes=len(code),private_alphabet_reused=True,
        data_load_layout_and_font_unchanged=True,selection_and_audio_calls_unchanged=True,
        hardware_verified=False)
