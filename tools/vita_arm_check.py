"""Execute the actual Tengoku Thumb trampolines and appended relocations."""
import argparse
import json
import struct
from tools import vita_arm as A, vita_source as V
from tools.common import write_json
from tools.vita import self_decrypt as S
from tools.vita.font_gxt import index_for_code
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import *

REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,
      UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
      UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_LR,UC_ARM_REG_SP]


def bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def number(value):return struct.unpack('<f',struct.pack('<I',value))[0]


class Machine:
    def __init__(self,data,report,text_shift=0,data_shift=0):
        self.report=report;self.text_shift=text_shift;self.data_shift=data_shift
        info=S.parse(data);self.u=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        for i,shift in ((0,text_shift),(1,data_shift)):
            p=info['phdrs'][i];off,size,_,_=info['infos'][i]
            address=p[2]+shift;start=address&~4095;end=(address+size+4095)&~4095
            u.mem_map(start,end-start);u.mem_write(address,data[off:off+size])
        for at in range(0,len(bytes.fromhex(report['added_relocations_hex'])),12):
            code,addend,offset=struct.unpack_from('<III',bytes.fromhex(report['added_relocations_hex']),at)
            V.need(code==0x310,'Unexpected new relocation kind')
            patch=A.TEXT_BASE+text_shift+offset;symbol=info['phdrs'][1][2]+data_shift+addend
            u.mem_write(patch,struct.pack('<I',(symbol-patch)&0xffffffff))
        u.mem_map(0x90000000,0x20000)
        self.scratch=report['scratch_va']+data_shift
        u.reg_write(UC_ARM_REG_CPSR,0xA8000030)
        u.reg_write(UC_ARM_REG_SP,0x90010000)
        u.reg_write(UC_ARM_REG_C1_C0_2,0xF<<20);u.reg_write(UC_ARM_REG_FPEXC,1<<30)

    def hook(self,name):
        site=A.SITES[name][0]+self.text_shift
        self.u.emu_start(site|1,site+4,count=20000)
        V.need(self.u.reg_read(UC_ARM_REG_PC)==site+4,'Hook did not reach original continuation: '+name)

    def lookup(self,key,utf8=False):
        u=self.u;source=0x90001000;u.mem_write(source,key+b'\0\0')
        u.reg_write(UC_ARM_REG_R0,source);u.reg_write(UC_ARM_REG_R1,int(utf8))
        u.reg_write(UC_ARM_REG_LR,0x90000001)
        u.emu_start((self.report['entries']['lookup']+self.text_shift)|1,0x90000000,count=200000)
        V.need(u.reg_read(UC_ARM_REG_PC)==0x90000000,'Lookup did not return')
        return u.reg_read(UC_ARM_REG_R0)


def verify():
    data,report=A.plan();rows,widths,mapping=A.parent_rows();cases=0
    for text_shift,data_shift in ((0,0),(0x10000,0x50000)):
        m=Machine(data,report,text_shift,data_shift);u=m.u
        # Full vocabulary once; all relocated samples plus binary color operands.
        selected=rows.items() if not text_shift else list(rows.items())[::127]
        for key,value in selected:
            for utf8 in (b'\0' not in key,):
                pointer=m.lookup(key,utf8=utf8)
                V.need(bytes(u.mem_read(pointer,len(value)+1))==value+b'\0','Native lookup differs from certified English')
                cases+=1
        for key in (b'not present',b'',b'\x81\x40\x81\x40'):
            V.need(m.lookup(key,utf8=True)==0x90001000,'Unmatched source was altered')
        # Main SJIS/control-key entry must retain embedded NUL operands.
        cp_keys=[(k,v) for k,v in rows.items() if b'\0' in k]
        for key,value in cp_keys:
            pointer=m.lookup(key)
            V.need(bytes(u.mem_read(pointer,len(value)+1))==value+b'\0','Native control operand lookup differs')
            cases+=1
        for cell,width in enumerate(widths):
            u.reg_write(UC_ARM_REG_R9,cell);u.reg_write(UC_ARM_REG_S18,bits(21.25))
            u.reg_write(UC_ARM_REG_S19,bits(24));u.reg_write(UC_ARM_REG_S21,bits(31))
            u.mem_write(m.scratch,struct.pack('<f',7.5));u.reg_write(UC_ARM_REG_LR,0x12345679)
            u.reg_write(UC_ARM_REG_S0,0x12345678);u.reg_write(UC_ARM_REG_S1,0x34567890)
            before=[u.reg_read(r) for r in REGS];flags=u.reg_read(UC_ARM_REG_CPSR)&0xF8000000
            m.hook('advance');advance=31 if width==32 else width*24/32
            V.need(number(u.reg_read(UC_ARM_REG_S18))==21.25+advance,'Wrong proportional advance')
            V.need(struct.unpack('<f',u.mem_read(m.scratch,4))[0]==7.5+advance,'Wrong piece advance')
            V.need(before==[u.reg_read(r) for r in REGS] and flags==u.reg_read(UC_ARM_REG_CPSR)&0xF8000000,'Advance changed live state')
            V.need(u.reg_read(UC_ARM_REG_S0)==0x12345678 and u.reg_read(UC_ARM_REG_S1)==0x34567890,'Advance changed temporary FP state')
            cases+=1
        for name,target,base,col in (('normal',1,1,3),('mode1',1,1,3),('keyword',2,2,3),('substitution',1,8,10)):
            for value in (-128,0,42*128+64):
                for i,r in enumerate(REGS[:-1]):u.reg_write(r,100+i)
                u.reg_write(REGS[base],100);u.reg_write(REGS[col],value&0xffffffff)
                u.reg_write(UC_ARM_REG_LR,7);u.mem_write(m.scratch,struct.pack('<f',999))
                before=[u.reg_read(r) for r in REGS];m.hook(name)
                expected=list(before);expected[target]=(100+(value>>7))&0xffffffff
                V.need(expected==[u.reg_read(r) for r in REGS],'Piece origin changed live registers or row LR: '+name)
                V.need(bytes(u.mem_read(m.scratch,4))==bytes(4),'Piece origin did not reset width')
                cases+=1
        for amount in (0,0.25,12.5,323.75):
            u.mem_write(m.scratch,struct.pack('<f',amount));u.reg_write(UC_ARM_REG_R0,300)
            u.reg_write(UC_ARM_REG_R9,900);u.reg_write(UC_ARM_REG_LR,0x12345679)
            m.hook('piece_end')
            V.need(u.reg_read(UC_ARM_REG_R9)==900+int(amount*128) and u.reg_read(UC_ARM_REG_R0)==300,'Piece cursor uses byte count')
            V.need(u.reg_read(UC_ARM_REG_LR)==0x12345679,'Piece cursor changed LR')
            cases+=1
        raw_key=next(k for k,v in rows.items() if b'\0' not in k and len(k)>12 and len(v)>12)
        for key in (raw_key,b'\x81\x40',b''):
            for i,r in enumerate(REGS[:-1]):u.reg_write(r,0x600+i)
            source=0x90001000;u.mem_write(source,key+b'\0\0');u.reg_write(UC_ARM_REG_R7,source)
            before=[u.reg_read(r) for r in REGS];flags=u.reg_read(UC_ARM_REG_CPSR)&0xF8000000
            m.hook('draw');after=[u.reg_read(r) for r in REGS]
            # A key selected from the full alias dictionary can be UTF-8;
            # use a native wide miss here, and test hits below with real glyphs.
            V.need(all(before[i]==after[i] for i in range(len(REGS)) if i!=7),'Drawer changed unrelated GPR state')
            V.need(flags==u.reg_read(UC_ARM_REG_CPSR)&0xF8000000 and number(u.reg_read(UC_ARM_REG_S0))==-1,'Drawer replay or flags differ')
            cases+=1
        text='Center test'
        encoded=b''.join(bytes.fromhex(mapping[c]) for c in text)
        expected=sum(widths[index_for_code(int(mapping[c],16))] for c in text)
        state=0x90006000
        u.mem_write(state+0x14,struct.pack('<f',24));u.mem_write(state+0x18,struct.pack('<f',28))
        for marker,two in (('@scene-center',False),('@headline-center',True)):
            raw=bytes.fromhex(mapping[marker])+encoded
            u.mem_write(0x90001000,raw+b'\0\0');u.reg_write(UC_ARM_REG_R7,0x90001000)
            u.reg_write(UC_ARM_REG_R5,state);u.reg_write(UC_ARM_REG_S18,bits(99));u.reg_write(UC_ARM_REG_S17,bits(200))
            u.reg_write(UC_ARM_REG_LR,0x12345679);m.hook('draw')
            V.need(u.reg_read(UC_ARM_REG_R7)==0x90001002,'Marker was not consumed')
            V.need(number(u.reg_read(UC_ARM_REG_S18))==A.CANVAS_CENTER-expected*24/64,'Wrong Vita scene center')
            V.need(number(u.reg_read(UC_ARM_REG_S17))==200-(14 if two else 0),'Wrong headline row origin')
            V.need(u.reg_read(UC_ARM_REG_LR)==0x12345679,'Scene origin changed LR')
            cases+=1
        for raw,encoding,narrow in ((encoded,1,True),('Unmatched source'.encode(),0,False)):
            u.mem_write(0x90001000,raw+b'\0\0');u.reg_write(UC_ARM_REG_R0,state)
            u.reg_write(UC_ARM_REG_R6,0x90001000);u.reg_write(UC_ARM_REG_R5,encoding)
            u.reg_write(UC_ARM_REG_S0,bits(9));u.reg_write(UC_ARM_REG_S1,bits(31));u.reg_write(UC_ARM_REG_S2,bits(.5))
            u.reg_write(UC_ARM_REG_LR,0x12345679);before=[u.reg_read(r) for r in REGS]
            m.hook('center')
            V.need(number(u.reg_read(UC_ARM_REG_S0))==(expected*24/32 if narrow else 9*31),'Wrong proportional or fallback center width')
            V.need(before==[u.reg_read(r) for r in REGS] and number(u.reg_read(UC_ARM_REG_S1))==31,'Center changed native caller state')
            cases+=1
    return dict(schema=1,title_id=V.TITLE, candidate_sha256=report['output_sha256'],
        native_cases=cases,full_table_entries=len(rows),independent_text_data_relocations=True,
        all_4480_widths_executed=True,live_keyword_row_lr_preserved=True,
        embedded_nul_operands_executed=True,scene_and_caption_centers_executed=True,
        runtime_verified=False,centering_pending=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result=verify();print(json.dumps(result,indent=2))
    if a.apply:write_json(V.WORK/'arm_execution_v2.json',result)
    else:print('DRY RUN: no execution report written.')


if __name__=='__main__':main()
