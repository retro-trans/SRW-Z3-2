"""Execute the original report composer with bounded string-library adapters."""
import struct
from tools import ui_hook as H,ppc_exec as P


def report(elf,condition_id,part_name):
    return _execute(elf,0x31c798,condition_id,part_name)


def bonus(elf,index):
    return _execute(elf,0x2f4570,index,b'')


def _execute(elf,start,value,part_name):
    """Run original PPC composition; adapters only implement std::string/libc."""
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,bytes(0x10000))
    m=P.Machine(mem);m.r=[0]*32;m.r[1]=0x40008000;m.r[2]=H.TOC;m.r[3]=value;m.lr=0xdead0000;m.pc=start
    heap=0x41002000;captured=[]
    mem.write(0x41000000,part_name+b'\0')
    def word(at):return int.from_bytes(mem.read(at,4),'big')
    def write_word(at,value):mem.write(at,struct.pack('>I',value))
    if start==0x2f4570:
        select=0x41001200;options=word(H.TOC-0x1810)
        # Only the current menu selection/state is supplied; the native
        # pointer getter and UTF-8 quotation/append code execute unchanged.
        write_word(select,0);write_word(select+4,0)
        # Preserve source program memory; provide the selected native record
        # through a private copy of the menu records and its TOC binding.
        original=mem.read(options,64)
        record=bytearray(original);struct.pack_into('>I',record,4,value)
        tocseg=next(s for s in H._headers(elf)[2]if s[3]<=H.TOC-0x1810<s[3]+s[5])
        for region in mem.regions:
            if region[0]==tocseg[3]:
                region[1][H.TOC-0x1810-region[0]:H.TOC-0x180c-region[0]]=struct.pack('>I',0x41001100)
                region[1][H.TOC-0x1828-region[0]:H.TOC-0x1824-region[0]]=struct.pack('>I',select)
        mem.write(0x41001100,record)
    def cstring(at):
        out=bytearray()
        for n in range(4096):
            b=mem.read(at+n,1)
            if b==b'\0':return bytes(out)
            out.extend(b)
        raise ValueError('Native composed string did not terminate')
    while m.pc!=0xdead0000:
        if m.steps>50000:raise ValueError('Native report exceeded execution bound')
        if m.pc==0x68a2ac:m.r[3]=len(cstring(m.r[3]));m.pc=m.lr
        elif m.pc==0x6872cc:
            mem.write(m.r[3],mem.read(m.r[4],m.r[5]));m.pc=m.lr
        elif m.pc==0x6b8644:
            obj,size=m.r[3],m.r[4];cap=word(obj+24);length=word(obj+20)
            if size>cap:
                old=word(obj+4)if cap>15 else obj+4
                mem.write(heap,mem.read(old,length+1));write_word(obj+4,heap)
                write_word(obj+24,max(size,31));heap+=max(size,31)+32
            m.r[3]=int(size!=0);m.pc=m.lr
        elif m.pc==0x3a65c:
            # Actual item getter returns a record whose name pointer is +4.
            write_word(0x41001004,0x41000000);m.r[3]=0x41001000;m.pc=m.lr
        elif m.pc==0x2d8aec:
            captured=[cstring(word(m.r[3]+4*n))for n in range(m.r[4])];m.r[3]=0;m.pc=m.lr
        elif m.pc==0x24140:m.pc=m.lr
        else:m.step()
    if len(captured)!=(3 if start==0x31c798 else 2):raise ValueError('Native message line count changed')
    return captured,m.steps
