"""Translate whole D-Trader purchase questions after native name assembly."""
import struct
from tools import ui_hook as H,eboot_text as E,rpw_text as R
from tools.common import sha256
from tools.ui_description_layout import advance
PREFIX=0x855dba
SUFFIX=0x855dea
START,END=0x31720c,0x3177b8

def source_rows(elf):
 rd=H._reader(elf,H._headers(elf)[2])
 if rd(H.TOC-0x15a8,4)!=struct.pack('>I',0x855c0c):raise ValueError('Trader pool binding changed')
 for va,jp in ((PREFIX,'「'),(SUFFIX,'」を購入します。')):
  raw=jp.encode('cp932')+b'\0'
  if rd(va,len(raw))!=raw:raise ValueError('Purchase fragment changed')
 if rd(0x317330,8)!=bytes.fromhex('387c01de48372f79'):raise ValueError('Purchase suffix composer changed')
 names=R.load_names();rows=[]
 for s in R.slots(R.load_rpw()):
  if s['chunk']!='boost-p'or s['col']!=1 or not R.needs_text(s['jp']):continue
  en=R.text_for(s,names)
  if not en:raise ValueError('Power Part lacks a translation')
  text='Buy "'+en+'".'
  if sum(map(advance,text))*31/32>1040:raise ValueError('Purchase question exceeds panel')
  rows.append(dict(record=s['record'],jp=s['jp'],en=en,question=text))
 return rows

def hook_entries(elf,mapping):
 out={}
 for row in source_rows(elf):
  for kind,name in (('source',row['jp'].encode('cp932')),('translated',E.encode(row['en'],mapping))):
   key='「'.encode('cp932')+name+'」を購入します。'.encode('cp932')
   if H.extent(key+b'\0')!=len(key):raise ValueError('Invalid purchase key')
   out[key]=dict(id='review47:buy:'+str(row['record'])+':'+kind,key=key,english=E.encode(row['question'],mapping))
 return list(out.values())

def report(elf):
 rd=H._reader(elf,H._headers(elf)[2]);rows=source_rows(elf)
 return dict(parts=len(rows),composer_va=START,composer_sha256=sha256(rd(START,END-START)),
  source_and_translated_names=True,longest_pixels=max(sum(map(advance,r['question']))*31/32 for r in rows))

def native_compose(elf,name):
 """Run the actual purchase constructor; only allocation/copy libc calls are modeled."""
 from tools import ppc_exec as P
 mem=P.Memory()
 for i,s in enumerate(H._headers(elf)[2][:2]):mem.map(s[3],elf[s[2]:s[2]+s[5]],writable=i==1)
 mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,name+bytes(0x1000-len(name)));mem.map(0x42000000,bytes(0x1000))
 global_state=int.from_bytes(mem.read(H.TOC-0x15b0,4),'big');mem.map(global_state,bytes(0x1000))
 def string(at):
  for n in range(1024):
   if mem.read(at+n,1)==b'\0':return mem.read(at,n)
  raise ValueError('Unterminated constructor string')
 def reserve(v):
  base=v.r[3];cap=int.from_bytes(mem.read(base+24,4),'big')
  if cap<=15:
   n=int.from_bytes(mem.read(base+20,4),'big');old=mem.read(base+4,n)
   mem.write(0x42000000,old+b'\0');mem.write(base+4,struct.pack('>I',0x42000000));mem.write(base+24,struct.pack('>I',1023))
  if v.r[4]>=1023:raise ValueError('Constructor exceeds test allocation')
  v.r[3]=1;v.pc=v.lr
 def memcpy(v):mem.write(v.r[3],mem.read(v.r[4],v.r[5]));v.pc=v.lr
 v=P.Machine(mem);v.r=[0x770000+i for i in range(32)];v.r[1]=0x40008000;v.r[2]=H.TOC;v.r[3]=0x41000000
 v.pc=START;v.lr=0xdead0000;v.hooks={0x6b8644:reserve,0x6872cc:memcpy}
 v.run({0x2d8aec},limit=10000)
 if v.r[4:7]!=[2,1,1]:raise ValueError('Purchase choice behavior changed')
 pointers=struct.unpack('>II',mem.read(v.r[3],8));lines=[string(p)for p in pointers]
 if lines!=['「'.encode('cp932')+name+'」を購入します。'.encode('cp932'),'よろしいですか？'.encode('cp932')]:
  raise ValueError('Native constructor differs from translated key')
 return lines,v.steps
