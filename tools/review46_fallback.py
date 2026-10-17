"""Keep the no-pilot name placeholders in the same encoding as RPW names."""
import struct
from tools import ui_hook as H, ppc_exec as P
CASES=((-0xae8,0x8dc7c8,7),( -0xae4,0x8dc7e0,8))

def apply(elf,table):
 original=H.PREPARED.read_bytes();rd=H._reader(elf,H._headers(elf)[2]);src=H._reader(original,H._headers(original)[2])
 out=bytearray(elf);cursor=(table['used_bytes']+15)&~15;spans=[];audit=[]
 def put(va,raw):
  seg=next(p for p in H._headers(elf)[2]if p[3]<=va<p[3]+p[5]);at=seg[2]+va-seg[3]
  out[at:at+len(raw)]=raw;spans.append([at,at+len(raw)])
 for disp,va,count in CASES:
  native=('ー'*count).encode('utf8')+b'\0'
  if src(va,len(native))!=native or rd(H.TOC+disp,4)!=struct.pack('>I',va):raise ValueError('No-pilot fallback binding changed')
  raw=('ー'*count).encode('cp932')+b'\0';target=H.EXT_VA+cursor
  if cursor+len(raw)>table['ext_size']or rd(target,len(raw))!=bytes(len(raw)):raise ValueError('Fallback headroom occupied')
  put(target,raw);put(H.TOC+disp,struct.pack('>I',target));cursor+=len(raw)
  audit.append(dict(toc_disp=disp,original_va=va,patched_va=target,cells=count,before_hex=native.hex(),after_hex=raw.hex()))
 restored=bytearray(out)
 for a,z in spans:restored[a:z]=elf[a:z]
 if restored!=elf:raise ValueError('Unrelated fallback bytes changed')
 return bytes(out),dict(cases=audit,modified_file_ranges=spans,used_bytes=cursor,headroom_bytes=table['ext_size']-cursor)

def native_cases(elf):
 mem=P.Memory()
 for i,s in enumerate(H._headers(elf)[2][:2]):mem.map(s[3],elf[s[2]:s[2]+s[5]],writable=i==1)
 mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x1000));mem.map(0x42000000,bytes(0x100))
 # Helper saves/restores halfword style in the real global scratch structure.
 mem.write(H.TOC-0xb00,struct.pack('>I',0x41000800));audit=[]
 for pc,count in ((0x3a2990,7),(0x3a2a58,8),(0x3a2aa8,8)):
  for state in (0,0x80000000):
   v=P.Machine(mem);v.r[1]=0x40003000;v.r[2]=H.TOC
   v.r[30]=0x41000000;v.r[31]=0x41000000;v.r[29]=0x42000000;v.r[28]=0;v.r[9]=0x41000000

   if pc!=0x3a2990:v.r[30]=0x42000000
   if pc==0x3a2aa8:v.r[29]=0;v.r[28]=0x41000000
   v.r[4]=0;v.r[6]=0;v.cr=0;mem.write(0x41000028,struct.pack('>I',state))
   # The two named fallback branches only prepare arguments; stop at their common text consumer.
   v.pc=pc;v.run({0x5fc64},limit=100)
   ptr=v.r[4];raw=mem.read(ptr,count*2+1)
   if raw!=('ー'*count).encode('cp932')+b'\0':raise ValueError('Native no-pilot name is not CP932')
   if (v.r[3],v.r[5],v.r[6],v.r[8])!=(0x41000000,0x42000000,0,0):raise ValueError('No-pilot caller geometry changed')
   audit.append(dict(pc=pc,state=state,cells=count,raw_hex=raw.hex(),steps=v.steps))
 # The nonempty branches still take the live RPW pointer, including custom names.
 for pc,field in ((0x3a28fc,8),(0x3a2944,12),(0x3a2a20,0)):
  v=P.Machine(mem);v.r[1]=0x40003000;v.r[2]=H.TOC;v.r[3]=0x41000000;v.r[4]=0x41000100
  v.r[30]=0x41000000;v.r[31]=0x41000000;v.r[29]=0x42000000;v.r[28]=0
  mem.write(0x41000100,struct.pack('>II',0x41000200,0x41000300));mem.write(0x41000200+field,struct.pack('>I',0x42000000))
  mem.write(0x41000310,struct.pack('>I',0x41000400));mem.write(0x41000400,struct.pack('>I',0x42000000))
  v.pc=pc;v.run({0x5fc64},limit=100)
  if v.r[4]!=0x42000000:raise ValueError('Live pilot name pointer changed')
  audit.append(dict(pc=pc,live_name_pointer_preserved=True,steps=v.steps))
 # The actual text consumer inherits the same CP932 mode used by live RPW names.
 for flags in (0,0xe0,0x800000e0):
  v=P.Machine(mem);v.r[1]=0x40003000;v.r[2]=H.TOC;v.r[30]=0x41000000
  v.r[27]=struct.unpack('>I',mem.read(H.TOC-0xae4,4))[0];v.r[29]=231;v.r[28]=80
  mem.write(0x41000028,struct.pack('>I',flags));v.pc=0x5e3a0;v.run({0x14ae4},limit=100)
  if v.r[7]!=1 or mem.read(v.r[3],17)!=('ー'*8).encode('cp932')+b'\0':raise ValueError('Placeholder draw encoding differs from pilot names')
  audit.append(dict(pc=0x5e3a0,flags=flags,cp932_draw=True,steps=v.steps))
 return audit
