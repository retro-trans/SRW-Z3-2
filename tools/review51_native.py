"""DLC-only native dialog constructor and report-copy execution checks."""
import struct
from functools import lru_cache
from tools import ui_hook as H,ppc_exec as P,rpw_text as R,eboot_text as E,library_build as L,review51_text as T
from tools.common import sha256
PART_SITES=(0x173920,0x173a48)
TITLE_SITES=(0x173bf4,0x173ce4,0x173d74,0x173dd4)

@lru_cache(None)
def titles():
 rd=H._reader(H.PREPARED.read_bytes(),H._headers(H.PREPARED.read_bytes())[2]);names=E.load()['strings'];res=E.resolver();out=[]
 for n in range(40):
  at=T.TABLE+n*44;raw=rd(at,44);ptr=struct.unpack_from('>I',raw,4)[0];jp=rd(ptr,256).split(b'\0')[0].decode('cp932')
  en=L.expand(names[jp]['en'],res)if jp in names else'---'if n==34 and jp=='ーーー'else None
  if not en or not en.isascii()or len(en)>100:raise ValueError('Native DLC title must be complete ASCII')
  out.append(dict(index=n,field=at+4,jp=jp,en=en,source_pointer=ptr,source_record_sha256=sha256(raw),
   description_pointer=struct.unpack_from('>I',raw,32)[0],
   funds=struct.unpack_from('>I',raw,12)[0],chips=struct.unpack_from('>H',raw,16)[0],parts=list(raw[18:20])))
 return out

@lru_cache(None)
def parts():
 wanted={p for r in titles()for p in r['parts']if p};names=R.load_names();result={}
 for row in R.slots(R.load_rpw()):
  if row['chunk']=='boost-p'and row['col']==1 and row['record']in wanted:
   en=R.text_for(row,names)
   if not en or not en.isascii():raise ValueError('Untranslated native DLC reward')
   result[row['record']]=en
 if set(result)!=wanted:raise ValueError('Incomplete DLC part inventory')
 return result

def part_stub(start,pointers):
 words=[]
 for ident,ptr in sorted(pointers.items()):
  words.extend([H._cmp(11,7,0,3,ident),0x409e0010,H._d(15,3,0,ptr>>16),H._d(24,3,3,ptr&0xffff),0x4e800020])
 words.append(H.branch(start+len(words)*4,0x15d6a4))
 return b''.join(struct.pack('>I',w)for w in words)

def title_stub(start,pointers):
 words=[]
 for source,ptr in sorted(pointers.items()):
  words.extend([H._d(15,9,0,source>>16),H._d(24,9,9,source&0xffff),H._cmpx(0,7,0,3,9),0x409e0010,
   H._d(15,3,0,ptr>>16),H._d(24,3,3,ptr&0xffff),H.branch(start+(len(words)+6)*4,0x15161c)])
 words.append(H.branch(start+len(words)*4,0x15161c))
 return b''.join(struct.pack('>I',w)for w in words)

def machine(elf):
 mem=P.Memory()
 for s in H._headers(elf)[2]:
  if s[0]==1 and s[5]:mem.map(s[3],elf[s[2]:s[2]+s[5]])
 mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,bytes(0x8000))
 def string(at):
  for n in range(4096):
   if mem.read(at+n,1)==b'\0':return mem.read(at,n)
  raise ValueError('Unterminated native DLC text')
 def strlen(v):v.r[3]=len(string(v.r[3]));v.pc=v.lr
 def strcat(v):mem.write(v.r[3]+len(string(v.r[3])),string(v.r[4])+b'\0');v.pc=v.lr
 def number(v):mem.write(v.r[4],str(v.r[3]).encode('ascii')+b'\0');v.r[3]=v.r[4];v.pc=v.lr
 def convert(v):
  raw=string(v.r[3]);raw.decode('ascii')
  if len(raw)>=v.r[5]:raise ValueError('Native DLC conversion would clip a name')
  mem.write(v.r[4],raw+b'\0');v.r[3]=len(raw);v.pc=v.lr
 def memset(v):mem.write(v.r[3],bytes([v.r[4]&255])*v.r[5]);v.pc=v.lr
 def memcpy(v):mem.write(v.r[3],mem.read(v.r[4],v.r[5]));v.pc=v.lr
 def copy(v):
  raw=string(v.r[4])[:v.r[5]];mem.write(v.r[3],raw+bytes(v.r[5]-len(raw)));v.pc=v.lr
 def strchr(v):
  pos=string(v.r[3]).find(bytes([v.r[4]&255]));v.r[3]=v.r[3]+pos if pos>=0 else 0;v.pc=v.lr
 def sprintf(v):
  raw=string(v.r[5])
  if b'%'in raw:raise ValueError('Unexpected printf operand in fixed DLC notice')
  if len(raw)>=v.r[4]:raise ValueError('Native DLC report buffer overflow')
  mem.write(v.r[3],raw+b'\0');v.r[3]=len(raw);v.pc=v.lr
 vm=P.Machine(mem);vm.r=[0x770000+i for i in range(32)];vm.r[1]=0x40008000;vm.r[2]=H.TOC
 vm.lr=0xdead0000;vm.hooks={0x68a2ac:strlen,0x68f400:strcat,0x1bd70c:number,0x15161c:convert,
  0x69327c:memset,0x6872cc:memcpy,0x68fca0:copy,0x68f52c:strchr,0x69020c:sprintf}
 return vm,string

def compose(elf,row,adapter,claim=False):
 vm,string=machine(elf);vm.r[3:6]=[row['source_pointer'],0x41001000,128];vm.pc=adapter
 vm.run({vm.lr},limit=1000)
 if string(0x41001000)!=row['en'].encode('ascii'):raise ValueError('Native DLC title adapter differs')
 # Both prompts are read through their patched, original TOC consumers.
 disp=-21036 if claim else-21040
 pointer=int.from_bytes(vm.mem.read(H.TOC+disp,4),'big')
 question=string(pointer)
 expected='Claim this bonus?'if claim else'Start this scenario?'
 if question.decode('utf8')!=expected:raise ValueError('Untranslated DLC launch/claim question')
 vm.r[3:10]=[0x41000000,0x41001000,row['funds'],row['chips'],*row['parts'],pointer]
 vm.pc=0x1733ec;vm.run({vm.lr},limit=12000);raw=string(0x41000000);text=raw.decode('utf8')
 wanted=['『'+row['en']+'』','Scenario Clear Bonus','Funds: '+str(row['funds']),'Z-Chips: '+str(row['chips']),expected]
 for fragment in wanted:
  if fragment not in text:raise ValueError('Native DLC confirmation lost text: '+fragment+' in '+repr(text))
 for ident in row['parts']:
  if ident and parts()[ident]not in text:raise ValueError('Native DLC reward name missing')
 if any('\u3040'<=c<='\u9fff'for c in text if c not in '『』'):raise ValueError('Japanese remains in native DLC dialog')
 if len(raw)>=512:raise ValueError('Native confirmation exceeds original buffer')
 return dict(index=row['index'],claim=claim,en=text,bytes=len(raw),steps=vm.steps)

def report_lines(elf,source):
 vm,string=machine(elf);vm.mem.write(0x41000000,source+b'\0');vm.r[3:8]=[0x41000000,1,0,0,0];vm.pc=0x168a1c
 vm.run({0x9af68},limit=12000)
 lines=[string(p)for p in vm.r[4:8]if p]
 if lines!=source.split(b'\n'):raise ValueError('Native DLC report clips or reorders a row')
 return lines,vm.steps
