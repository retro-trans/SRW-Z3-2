"""Translate composed movement masks, retaining four terrain flag cells."""
import itertools,struct
from tools import battle_layout as B,ui_catalog as U,status_layout as S,eboot_text as E,ui_hook as H,ppc_exec as P
from tools.common import sha256

def source_rows():
    source=B.source();rows=[r for r in U.fssa_strings(source)if r['text']=='空陸水地']
    if not rows:raise ValueError('Native movement mask source missing')
    return rows

def hook_entries(elf,mapping):
    source_rows();out=[]
    for flags,dash in itertools.product(itertools.product((False,True),repeat=4),('－','ー')):
        jp=''.join(c if present else dash for c,present in zip('空陸水地',flags))
        en=''.join(S.TERRAIN[c]if present else dash for c,present in zip('空陸水地',flags))
        # Standalone masks and number/slash/mask are distinct native draws.
        variants=[(jp,en)]
        for n in range(100):
            number=''.join(chr(0xff10+int(c))for c in str(n))
            variants.append((number+'／'+jp,str(n)+'/'+en))
        for key,text in variants:
            out.append(dict(id='review30:movement:'+sha256(key.encode('cp932'))[:16],
                key=key.encode('cp932'),english=E.encode(text,mapping)))
    return list({r['key']:r for r in out}.values())

def report():
    return dict(mask_combinations=16,disabled_glyphs=['－','ー'],draw_keys=3131,native_cells=4,
        source_widgets=[a for r in source_rows()for a in r['widget_offsets']],runtime_verified=False)

def native_mask(elf,flags):
    """Run 0x329948's real flag branches, including its U+30FC dash stores."""
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,bytes(0x1000))
    native_state=int.from_bytes(mem.read(H.TOC-0x131c,4),'big');mem.map(native_state,bytes(8))
    m=P.Machine(mem);m.r[1]=0x40008000;m.r[2]=H.TOC;m.r[3]=0x41000000;m.r[4]=0x41000200;m.lr=0xdead0000;m.pc=0x329948
    mem.write(0x41000040,b'CANARY')
    getters=dict(zip((0x382134,0x381acc,0x381aec,0x3820c0),flags))
    def cstring(at):
        for n in range(64):
            if mem.read(at+n,1)==b'\0':return mem.read(at,n)
        raise ValueError('Movement mask did not terminate')
    while m.pc!=0xdead0000:
        if m.steps>3000:raise ValueError('Movement formatter execution bound')
        if m.pc==0x39a244:m.r[3]=0;m.pc=m.lr
        elif m.pc in getters:m.r[3]=int(getters[m.pc]);m.pc=m.lr
        elif m.pc==0x68a2ac:m.r[3]=len(cstring(m.r[3]));m.pc=m.lr
        elif m.pc==0x68f400:
            text=cstring(m.r[3])+cstring(m.r[4])
            if len(text)>63:raise ValueError('Movement mask overflow')
            mem.write(m.r[3],text+b'\0');m.pc=m.lr
        else:m.step()
    if mem.read(0x41000040,6)!=b'CANARY':raise ValueError('Movement mask canary changed')
    return cstring(0x41000000),m.steps
