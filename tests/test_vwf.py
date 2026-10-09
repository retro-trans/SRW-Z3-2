import copy
import struct
import unittest
from tools.vwf import branch, stub, SITE, CELLS
from tools.ui_build import encode, decode, patch_rpw, verify_rpw
from tests.test_ui_build import fixture

try:
    from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
except ImportError:
    Cs = None


class VWFEncodingTests(unittest.TestCase):
    def test_letters_spaces_newlines_and_badge_are_distinct(self):
        mapping={'A':'8540','b':'8541',' ':'8542','@badge:Ab':'8543'}
        text='Ab  \nb'
        self.assertEqual(decode(encode(text,mapping,'vwf'),mapping,'vwf'),text)
        self.assertEqual(encode('Ab',mapping,'vwf',True),bytes.fromhex('8543'))
        self.assertEqual(decode(bytes.fromhex('8543'),mapping,'vwf'),'Ab')
        self.assertEqual(len(encode('Ab',mapping,'vwf')),4)

    def test_complete_family_preserves_original_data_with_vwf(self):
        raw,rows,_=fixture()
        tokens=set(''.join(r['rendered_en'] for r in rows).replace('\n','')) | {'@badge:Ab'}
        mapping={t:bytes((0x85,0x40+i)).hex() for i,t in enumerate(sorted(tokens))}
        patched,edits,grow=patch_rpw(raw,rows,mapping,'vwf')
        self.assertEqual(edits[1]['bytes'],2)
        self.assertEqual(edits[0]['bytes'],10)
        verify_rpw(raw,patched,edits,mapping)
        self.assertGreater(grow,0)

    def test_branch_rejects_out_of_range_and_misalignment(self):
        for target in (3,1<<25,-(1<<25)-4):
            with self.assertRaises(ValueError):branch(0,target)


@unittest.skipIf(Cs is None,'Capstone required for independent PPC instruction execution')
class VWFInstructionTests(unittest.TestCase):
    def execute(self, cell, width, pitch, quad):
        """Execute decoded instructions, including stores and CR branches.

        This small test interpreter accepts only the instructions disassembled
        by Capstone. Memory outside the stack and width table is inaccessible.
        """
        table,base=0x93d990,0x93eb10
        code=stub(table,base)
        instructions=list(Cs(CS_ARCH_PPC,CS_MODE_64|CS_MODE_BIG_ENDIAN).disasm(code,base))
        self.assertEqual(sum(i.size for i in instructions),len(code))
        ins={i.address:i for i in instructions}
        regs={ 'r%d'%i:0xfedcba9876000000+i for i in range(32)}
        regs['r1']=0x200070
        floats={'f%d'%i:struct.pack('>d',i+0.125) for i in range(32)}
        cr=0xa596c3e1
        mem={i:0xcc for i in range(0x200000,0x200200)}
        mem.update({table+i:32 for i in range(CELLS)})
        if cell<CELLS:mem[table+cell]=width
        def put(addr,data):
            for i,b in enumerate(data):
                self.assertIn(addr+i,mem)
                mem[addr+i]=b
        def get(addr,n):return bytes(mem[addr+i] for i in range(n))
        put(regs['r1']+0xc2,struct.pack('>H',cell))
        put(regs['r1']+0x94,struct.pack('>f',pitch))
        put(regs['r1']+0x9c,struct.pack('>f',quad))
        oldregs,oldfloats,oldmem,oldcr=copy.deepcopy(regs),dict(floats),dict(mem),cr
        def addr(s):
            off,reg=s.rstrip(')').split('(')
            return regs[reg]+int(off,0)
        def rounded(v):return struct.unpack('>f',struct.pack('>f',v))[0]
        def fv(reg):return struct.unpack('>d',floats[reg])[0]
        pc=base
        for _ in range(60):
            if pc==SITE+4:break
            i=ins[pc];op=i.mnemonic;a=i.op_str.split(', ');pc+=4
            if op in ('std','stdu','stw','stfd'):
                dest=addr(a[1]);size=4 if op=='stw' else 8
                raw=floats[a[0]] if op=='stfd' else (regs[a[0]] & ((1<<(8*size))-1)).to_bytes(size,'big')
                put(dest,raw)
                if op=='stdu':regs['r1']=dest
            elif op in ('ld','lwz','lhz','lfd','lfs'):
                size={'ld':8,'lwz':4,'lhz':2,'lfd':8,'lfs':4}[op]
                raw=get(addr(a[1]),size)
                if op=='lfd':floats[a[0]]=raw
                elif op=='lfs':floats[a[0]]=struct.pack('>d',struct.unpack('>f',raw)[0])
                else:regs[a[0]]=int.from_bytes(raw,'big')
            elif op=='mfcr':regs[a[0]]=cr
            elif op=='mtcrf':
                self.assertEqual(a[0],'0xff');cr=regs[a[1]]
            elif op in ('cmpwi','cmplwi'):
                x,y=regs[a[0]],int(a[1],0)
                cr=(cr&0x0fffffff)|((8 if x<y else 4 if x>y else 2)<<28)
            elif op in ('b','bge','beq'):
                if op=='b' or (op=='bge' and not cr&0x80000000) or (op=='beq' and cr&0x20000000):pc=int(a[-1],0)
            elif op=='lis':regs[a[0]]=int(a[1],0)<<16
            elif op=='ori':regs[a[0]]=regs[a[1]]|int(a[2],0)
            elif op=='lbzx':regs[a[0]]=mem[regs[a[1]]+regs[a[2]]]
            elif op=='fcfid':floats[a[0]]=struct.pack('>d',float(int.from_bytes(floats[a[1]],'big',signed=True)))
            elif op=='frsp':floats[a[0]]=struct.pack('>d',rounded(fv(a[1])))
            elif op=='fmuls':floats[a[0]]=struct.pack('>d',rounded(fv(a[1])*fv(a[2])))
            elif op=='addi':regs[a[0]]=regs[a[1]]+int(a[2],0)
            else:self.fail('unexpected instruction '+op)
        self.assertEqual(pc,SITE+4)
        self.assertEqual(regs,oldregs)
        self.assertEqual(cr,oldcr)
        for name,value in oldfloats.items():
            if name!='f13':self.assertEqual(floats[name],value)
        self.assertEqual({a:b for a,b in mem.items() if not 0x200000<=a<0x200070},
                         {a:b for a,b in oldmem.items() if not 0x200000<=a<0x200070})
        return fv('f13')

    def test_proportional_and_original_paths_preserve_live_state(self):
        for cell,width in ((0,9),(200,17),(4479,31),(10,32),(4480,17),(65535,9)):
            with self.subTest(cell=cell,width=width):
                expected=29.5 if cell>=CELLS or width==32 else width*23.5/32
                self.assertEqual(self.execute(cell,width,29.5,23.5),expected)

if __name__=='__main__':unittest.main()
