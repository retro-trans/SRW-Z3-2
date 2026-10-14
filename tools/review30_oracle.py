"""Execute the native skill question composer with bounded getter/libc models."""
import struct
from tools import ui_hook as H,ppc_exec as P,review30_messages as Q

def skill(elf,name,old_name,kind,leveled=False,multiple=False,current=0,innate=1):
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,bytes(0x10000))
    m=P.Machine(mem);m.r[1]=0x40008000;m.r[2]=H.TOC;m.r[3]=0x41003000;m.r[4]=0x41003400;m.lr=0xdead0000;m.pc=Q.START
    def word(at):return int.from_bytes(mem.read(at,4),'big')
    def put(at,n):mem.write(at,struct.pack('>I',n))
    def cstring(at):
        for n in range(1024):
            if mem.read(at+n,1)==b'\0':return mem.read(at,n)
        raise ValueError('Skill composer failed to terminate')
    # Copy only the four native TOC state pointers into writable model state.
    bindings={-0x151c:0x41001000,-0x1510:0x41000000,-0x1514:0x41000004}
    for off,va in bindings.items():
        for region in mem.regions:
            if region[0]<=H.TOC+off<region[0]+len(region[1]):
                at=H.TOC+off-region[0];region[1][at:at+4]=struct.pack('>I',va)
    put(0x41000000,0);put(0x41000004,0x41000008);put(0x41000008,0x41001800)
    state=0x41001000;put(state+0x1fc,0);put(state+0x200,0);put(state+0x204,1)
    put(state+0x30,0);put(state+0x3c,kind);put(state+0x614,2);put(state+0x34,int(multiple))
    put(0x41002008,0x41002100);put(0x41002408,0x41002500)
    mem.write(0x41002100,name+b'\0');mem.write(0x41002500,old_name+b'\0')
    for va in (0x41003000,0x41003400):mem.write(va+512,b'CANARY')
    while m.pc!=0xdead0000:
        if m.steps>10000:raise ValueError('Skill composer exceeded instruction bound')
        if m.pc==0x38a20c:m.r[3]=0x41002000 if m.r[3]==1 else 0x41002400;m.pc=m.lr
        elif m.pc==0x38d478:m.r[3]=int(leveled);m.pc=m.lr
        elif m.pc==0x389874:m.r[3]=current;m.pc=m.lr
        elif m.pc==0x3898c0:m.r[3]=innate;m.pc=m.lr
        elif m.pc in (0x68f88c,0x68f400):
            text=cstring(m.r[4]);prefix=cstring(m.r[3])if m.pc==0x68f400 else b''
            if len(prefix+text)>=512:raise ValueError('Skill output buffer exceeded')
            mem.write(m.r[3],prefix+text+b'\0');m.pc=m.lr
        else:m.step()
    if any(mem.read(va+512,6)!=b'CANARY'for va in (0x41003000,0x41003400)):raise ValueError('Skill output canary changed')
    return [cstring(va)for va in (0x41003000,0x41003400)],m.steps
