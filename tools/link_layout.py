"""Tengoku VWF link rectangles and segment positions; identities stay native.

Reference: SRW Z3's link_background_layout/main_link_background_layout.
All sites and dataflow below were independently located in BLJS10299.
The drawer's final pen minus its initial pen is the width oracle, including
runtime names and native glyphs. Geometry never changes link record metadata.
"""
import struct
from tools import ui_hook, vwf
from tools.common import sha256

STATE = 'layout:link-state'
PAYLOAD = bytes(1040)                 # 256 floats, origin, advance, spare
BLR = 0x4e800020
NOP = 0x60000000


class Asm:
    def __init__(self, va):
        self.va, self.w, self.labels, self.fix = va, [], {}, []
    def e(self, w): self.w.append(w)
    def d(self, op, rt, ra, off): self.e(op | rt<<21 | ra<<16 | (off&65535))
    def x(self, op, rt, ra, rb): self.e(op | rt<<21 | ra<<16 | rb<<11)
    def ptr(self, reg, va):
        self.d(0x3c000000,reg,0,va>>16); self.d(0x60000000,reg,reg,va&65535)
    def mr(self, dst, src): self.x(0x7c000378,src,dst,src)
    def label(self, name): self.labels[name] = len(self.w)
    def br(self, op, label): self.fix.append((len(self.w),op,label)); self.e(0)
    def call(self, target): self.e(ui_hook.branch(self.va+len(self.w)*4,target)|1)
    def jump(self, target): self.e(ui_hook.branch(self.va+len(self.w)*4,target))
    def code(self):
        for i,op,label in self.fix:
            self.w[i] = op | ((self.labels[label]-i)*4 & (0x3fffffc if op==0x48000000 else 0xfffc))
        return b''.join(struct.pack('>I',w)for w in self.w)


def save(a):
    a.d(0xf8000001,1,1,-0x80); a.e(0x7c0802a6); a.d(0xf8000000,0,1,0x90)
def restore(a):
    a.d(0xe8000000,0,1,0x90); a.e(0x7c0803a6); a.d(0x38000000,1,1,0x80)
def integer_float(a, integer, fpr, slot=0x70):
    a.d(0xf8000000,integer,1,slot); a.d(0xc8000000,fpr,1,slot)
    a.e(0xfc00069c | fpr<<21 | fpr<<11); a.e(0xfc000018 | fpr<<21 | fpr<<11)


def units(va, table):
    """Pure leaf: r3=encoded single-line text -> summed units, -1 for native.
    Bounded to the same 8192-byte cap as the draw dictionary; only volatile
    GPRs and cr0 are used. A native/unknown cell keeps native measurement.
    """
    a=Asm(va); a.mr(4,3); a.ptr(5,table); a.d(0x38000000,8,0,0)
    a.d(0x38000000,11,0,4096)
    a.label('loop'); a.d(0x88000000,6,4,0); a.d(0x2c000000,0,6,0); a.br(0x41820000,'done')
    a.d(0x38000000,6,6,-0x81); a.d(0x28000000,0,6,7); a.br(0x41810000,'native')
    a.d(0x88000000,7,4,1); a.d(0x38000000,7,7,-0x40)
    a.d(0x28000000,0,7,191); a.br(0x41810000,'native')
    a.d(0x1c000000,6,6,192); a.x(0x7c000214,6,6,7); a.x(0x7c0000ae,6,5,6)
    a.d(0x28000000,0,6,31); a.br(0x41810000,'native')
    a.x(0x7c000214,8,8,6); a.d(0x38000000,4,4,2); a.d(0x38000000,11,11,-1)
    a.d(0x2c000000,0,11,0); a.br(0x40820000,'loop')
    a.label('native'); a.d(0x38000000,8,0,-1)
    a.label('done'); a.mr(3,8); a.e(BLR); return a.code()


def lookup_wrapper(va, lookup):
    a=Asm(va); save(a); a.d(0xf8000000,31,1,0x70); a.mr(31,3)
    a.call(lookup); a.mr(3,31); a.d(0xe8000000,31,1,0x70); restore(a); a.e(BLR)
    return a.code()


def compare(va,lookup):
    a=Asm(va); save(a); a.d(0xf8000000,3,1,0x70); a.mr(3,4)
    a.call(lookup); a.mr(4,3); a.d(0xe8000000,3,1,0x70)
    restore(a); a.jump(0x68f738); return a.code()


def drawer_pen(va,state,end=False):
    a=Asm(va); a.d(0xf8000001,1,1,-0x40)
    a.d(0xf8000000,9,1,0x10); a.ptr(9,state)
    if end:
        a.d(0xd8000000,10,1,0x18); a.d(0xc0000000,10,9,1024)
        a.x(0xec000028,10,0,10); a.d(0xd0000000,10,9,1028)
        a.d(0xc8000000,10,1,0x18)
    else: a.d(0xd0000000,31,9,1024)
    a.d(0xe8000000,9,1,0x10); a.d(0x38000000,1,1,0x40)
    a.e(0xd01e004c if end else 0xd3fe004c); a.jump(0x14890 if end else 0x141ac)
    return a.code()


def column(va,state):
    a=Asm(va); a.ptr(10,state); a.d(0xc0000000,13,10,1028)
    a.d(0x3c000000,0,0,0x4300); a.d(0x90000000,0,1,0x70); a.d(0xc0000000,12,1,0x70)
    a.e(0xec000032 | 13<<21 | 13<<16 | 12<<6)
    a.e(0xfc00001e | 13<<21 | 13<<11); a.d(0x38000000,10,1,0x70)
    a.x(0x7c0007ae,13,0,10); a.d(0x80000000,9,1,0x70); a.jump(0x2209ec)
    return a.code()


def position(va):
    a=Asm(va)
    a.d(0xa0000000,11,4,0x22); a.e(0x7d6b0734)
    a.d(0x88000000,0,4,0x2f); a.e(0x7c000774); a.x(0x7c0001d6,0,0,6)
    a.x(0x7c000214,11,11,0); a.d(0x90000000,11,8,0)
    a.e(0x7c000670 | 5<<21 | 7<<11) # srawi r0,r5,7
    a.d(0xa0000000,9,4,0x20); a.e(0x7d290734); a.x(0x7c000214,9,9,0)
    a.d(0x90000000,9,7,0); a.e(BLR); return a.code()


def capture(va,state):
    a=Asm(va); a.e(0x987c0004)
    a.d(0x80000000,9,1,0x70); a.d(0x1c000000,9,9,64)
    a.d(0x80000000,0,1,0x74); a.d(0x1c000000,0,0,4)
    a.x(0x7c000214,9,9,0); a.ptr(10,state); a.x(0x7c000214,9,9,10)
    a.d(0xc0000000,13,10,1028); a.d(0xd0000000,13,9,0); a.jump(0x21cde0)
    return a.code()


def secondary(va,state,draw=False):
    a=Asm(va)
    if draw: a.d(0xc0000000,0,1,0x78); a.e(0xd01f0008); a.jump(0x216ad4)
    else:
        a.e(0x7c7d1b78); a.e(0x5489063e) # clrlwi r9,r4,24
        a.d(0x1c000000,9,9,4); a.ptr(10,state); a.x(0x7c000214,9,9,10)
        a.d(0xc0000000,0,9,0); a.d(0xd0000000,0,1,0x78); a.jump(0x216a40)
    return a.code()


def primary(va,state):
    a=Asm(va); a.call(0x2177bc); a.d(0x80000000,9,3,12); a.d(0x90000000,9,1,0x70)
    a.mr(3,31); a.call(0x2a9114); a.d(0x90000000,3,1,0x74)
    # Tengoku keeps the draw context in r28 (Jigoku uses r27). The
    # unchanged draw tail dereferences r28, so use the dead r27 as index.
    a.call(0x21c9b0); a.mr(29,3); a.d(0x38000000,27,0,0)
    a.label('loop'); a.mr(3,29); a.mr(4,27); a.call(0x21c730)
    a.d(0x2c000000,0,3,0); a.br(0x41820000,'next')
    for offset,local in ((12,0x70),(16,0x74)):
        a.d(0x80000000,9,3,offset); a.d(0x80000000,10,1,local)
        a.x(0x7c000040,0,9,10); a.br(0x40820000,'next')
    a.br(0x48000000,'found')
    a.label('next'); a.d(0x38000000,27,27,1); a.d(0x2c000000,0,27,256)
    a.br(0x41800000,'loop'); a.br(0x48000000,'done')
    a.label('found'); a.d(0x90000000,3,1,0x78); a.ptr(9,state)
    a.d(0x1c000000,10,27,4); a.x(0x7c000214,9,9,10)
    a.d(0xc0000000,0,9,0); a.d(0xd0000000,0,1,0x7c)
    a.mr(3,31); a.mr(4,28); a.call(0x2148d0)
    a.d(0x88000000,9,3,0x2d); a.e(0x7d290774); a.d(0x38000000,9,9,1)
    a.d(0x80000000,11,1,0x78); a.d(0xa0000000,10,11,2); a.e(0x7d4a0734)
    a.d(0x38000000,10,10,1); a.d(0xa0000000,11,11,0); a.e(0x7d6b0734)
    for reg,off in ((11,0),(10,4),(9,12)):
        integer_float(a,reg,0,0xa0); a.d(0xd0000000,0,30,off)
    a.d(0xc0000000,0,1,0x7c); a.d(0xd0000000,0,30,8)
    a.label('done'); a.jump(0x214ab4); return a.code()


def scene(va):
    a=Asm(va); a.call(0x212488); a.d(0x2c000000,0,3,0); a.br(0x40820000,'done')
    a.call(0x2177bc); a.d(0x80000000,3,3,12)
    a.label('done'); a.jump(0x21ce0c); return a.code()


def name_width(va,lookup,measure):
    a=Asm(va); a.call(lookup); a.d(0x90000000,3,1,0x78); a.call(measure)
    a.d(0x2c000000,0,3,-1); a.br(0x41820000,'native')
    a.d(0x80000000,9,31,0xc); a.x(0x7c0001d6,3,3,9); a.ptr(9,0x3d000000)
    a.br(0x48000000,'float')
    a.label('native'); a.d(0x80000000,3,1,0x78); a.call(0x68a2ac)
    a.e(0x5463f87e); a.d(0x80000000,9,31,0x14); a.x(0x7c0001d6,3,3,9); a.ptr(9,0x3f800000)
    a.label('float'); integer_float(a,3,0); a.d(0x90000000,9,1,0x70)
    a.d(0xc0000000,10,1,0x70); a.e(0xec000032 | 0<<21 | 0<<16 | 10<<6)
    a.d(0xd0000000,0,1,0x70); a.d(0x80000000,3,1,0x70); a.jump(0x2aae08)
    return a.code()


def center(va,lookup,measure,selection_codes=None):
    """Measure both caption encodings; retain legacy Yes/No selector anchors."""
    a=Asm(va); save(a); a.e(0x7c000026); a.d(0x90000000,0,1,0x78)
    a.d(0x2c000000,0,30,0); a.br(0x40820000,'cp')
    a.mr(3,31); a.call(ui_hook.CONVERTER[0]); a.d(0x80000000,3,2,-0x7f3c)
    a.d(0x38000000,3,3,0xb8); a.call(lookup); a.br(0x48000000,'measure')
    a.label('cp')
    if selection_codes is None: a.br(0x48000000,'native')
    else:
        a.mr(3,31); a.call(lookup)
        for n,codes in enumerate(selection_codes):
            # Read each code only after checking that its lead byte exists.
            for j,code in enumerate(codes):
                a.d(0x88000000,10,3,j*2); a.d(0x2c000000,0,10,0); a.br(0x41820000,'measure')
                a.d(0xa0000000,10,3,j*2); a.d(0x28000000,0,10,code); a.br(0x40820000,'selector%d'%n)
            a.d(0x88000000,10,3,len(codes)*2); a.d(0x2c000000,0,10,0); a.br(0x41820000,'native')
            a.label('selector%d'%n)
    a.label('measure'); a.call(measure)
    a.d(0x2c000000,0,3,-1); a.br(0x41820000,'native')
    integer_float(a,3,0); a.d(0x80000000,9,2,-0x7f3c); a.d(0xc0000000,13,9,0x54)
    a.e(0xec000032 | 13<<6); a.ptr(9,0x3c800000) # 1/64: half VWF width
    a.d(0x90000000,9,1,0x70); a.d(0xc0000000,13,1,0x70); a.e(0xec000032 | 13<<6)
    a.x(0xec000028,1,29,0); restore(a); a.jump(0x14a68)
    a.label('native'); a.d(0x80000000,0,1,0x78); a.e(0x7c0ff120)
    restore(a); a.br(0x409e0000,'alternate'); a.d(0x38000000,3,0,0)
    # 0x14aac recovers the CP932 source from r0. restore() uses r0 to
    # recover LR, so restore that source too before the native count path.
    # Otherwise native/blank captions are drawn from the caller's code.
    a.mr(0,31); a.jump(0x14a2c)
    a.label('alternate'); a.mr(3,31); a.d(0x38000000,4,0,0); a.mr(5,30)
    a.jump(0x14ac4); return a.code()


def heading(va,lookup):
    a=Asm(va); a.mr(3,31); a.call(lookup); a.mr(31,3)
    a.d(0xe8000000,0,1,0xc0); a.jump(0x1dd17c); return a.code()


GUARDS = {0x141a8:0xd3fe004c,0x1488c:0xd01e004c,0x2209e4:0x7c690e70,0x2209e8:0x7d290194,
    0x21f700:0x8804002e,0x21cddc:0x987c0004,0x216a3c:0x7c7d1b78,0x216ad0:0xd01f0008,
    0x214b54:ui_hook.branch(0x214b54,0x2177bc)|1,0x21ce04:ui_hook.branch(0x21ce04,0x212488)|1,
    0x21ce74:ui_hook.branch(0x21ce74,0x68f738)|1,
    0x2aae04:ui_hook.branch(0x2aae04,0x68a2ac)|1,0x14a24:0x409e00a0,
    0x1dd178:0xe80100c0}
SPANS = ((0x214b54,0x214c50),(0x216a14,0x216ad8),(0x21cce8,0x21cf20),
         (0x21f700,0x21f73c),(0x22079c,0x220a70),(0x2aad38,0x2aae68),(0x149bc,0x14ae4),
         (0x1dd120,0x1dd23c))


def apply(elf,original,state,table,mapping=None,save_center=None):
    if sha256(original)!=vwf.ELF_SHA256: raise ValueError('Layout baseline changed')
    phoff,_,phs,_=ui_hook._headers(elf); first,second=phs[:2]
    read=ui_hook._reader(elf,phs); native=ui_hook._reader(original,ui_hook._headers(original)[2])
    for lo,hi in SPANS:
        if read(lo,hi-lo)!=native(lo,hi-lo): raise ValueError('Layout consumer changed: %#x'%lo)
    for site,word in GUARDS.items():
        if read(site,4)!=struct.pack('>I',word): raise ValueError('Layout site drift: %#x'%site)
    if state%16 or read(state,len(PAYLOAD))!=PAYLOAD: raise ValueError('Link scratch is unaligned/occupied')
    out=bytearray(elf); cursor=(first[5]+15)&~15; spans=[]; code_rows=[]
    def add(label, builder, site=None):
        nonlocal cursor
        va=cursor+first[3]; raw=builder(va); end=cursor+len(raw)
        if end>second[2] or any(elf[cursor:end]): raise ValueError('Layout RX gap exhausted')
        out[cursor:end]=raw; spans.append((cursor,end)); cursor=(end+15)&~15
        code_rows.append(dict(id=label,va=va,bytes=len(raw)))
        if site is not None:
            at=site-first[3]; struct.pack_into('>I',out,at,ui_hook.branch(site,va)); spans.append((at,at+4))
        return va
    def lookup_code(va):
        raw=ui_hook.stub(va,back=va,replay=NOP)
        return raw[:-4]+struct.pack('>I',BLR)
    look=add('exact lookup',lookup_code)
    wrapper=add('display lookup',lambda va:lookup_wrapper(va,look))
    measure=add('VWF units',lambda va:units(va,table))
    if save_center:
        from tools.status_layout import save_origin
        add('drawer origin',lambda va:save_origin(va,state,save_center),0x141a8)
    else:add('drawer origin',lambda va:drawer_pen(va,state),0x141a8)
    add('drawer advance',lambda va:drawer_pen(va,state,True),0x1488c)
    add('segment column',lambda va:column(va,state),0x2209e4)
    # Column is now fixed-point; the former carry add must not run.
    struct.pack_into('>I',out,0x2209e8-first[3],NOP); spans.append((0x2209e8-first[3],0x2209ec-first[3]))
    add('segment x/y',position,0x21f700)
    add('registered width',lambda va:capture(va,state),0x21cddc)
    add('selected width',lambda va:secondary(va,state),0x216a3c)
    add('secondary rectangle',lambda va:secondary(va,state,True),0x216ad0)
    add('primary rectangle',lambda va:primary(va,state),0x214b54)
    add('dialogue scene',scene,0x21ce04)
    # This call needs BL so the tail-called native strcmp returns to the
    # unchanged registration loop. All other intercepts resume by B.
    cmp_va=add('translated registration',lambda va:compare(va,wrapper))
    at=0x21ce74-first[3]; struct.pack_into('>I',out,at,ui_hook.branch(0x21ce74,cmp_va)|1)
    spans.append((at,at+4))
    add('name width',lambda va:name_width(va,wrapper,measure),0x2aae04)
    from tools.eboot_text import encode
    selection_codes = [list(struct.unpack('>'+('H'*len(word)),encode(word,mapping)))
                       for word in ('No','Yes')] if mapping else None
    add('caption centering',lambda va:center(va,wrapper,measure,selection_codes),0x14a24)
    add('formatted heading',lambda va:heading(va,wrapper),0x1dd178)
    for va,word in {0x2aae14:NOP,0x2aae30:NOP,0x2aae3c:0x90610070,
                    0x2aae40:0xc0010070,0x2aae44:NOP,0x2aae48:NOP}.items():
        at=va-first[3]; struct.pack_into('>I',out,at,word); spans.append((at,at+4))
    end=max(b for a,b in spans if a>=first[5])
    struct.pack_into('>QQ',out,phoff+32,end,end); spans.append((phoff+32,phoff+48))
    restored=bytearray(out)
    for lo,hi in spans: restored[lo:hi]=elf[lo:hi]
    if restored!=elf: raise ValueError('Layout isolation failure')
    return bytes(out),dict(code=code_rows,state_va=state,width_table_va=table,
        centering_selection_codes=selection_codes,
        save_center=save_center,
        source_spans=[dict(start=lo,end=hi,sha256=sha256(native(lo,hi-lo))) for lo,hi in SPANS],
        modified_file_ranges=spans,identity_and_navigation_preserved=True,
        font_measurement='actual drawer advance',runtime_verified=False)
