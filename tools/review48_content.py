"""Source-bound pilot separators and exhaustive native stage-heading coverage."""
import struct,json
from collections import Counter
from functools import lru_cache
from tools import ui_hook as H,eboot_text as E,rpw_text as RP,library_build as L,ppc_exec as P
from tools.common import ROOT,sha256
from tools.ui_description_layout import advance
STAGES=0xa1f984
TITLES=0xa1f6ec
PREFIX_START,PREFIX_END=0x1dd4f0,0x1dd8e8

def native_prefix(elf,index,kind):
 """Execute the native stage-prefix branches; model only lookup and libc."""
 mem=P.Memory()
 for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
 mem.map(0x40000000,bytes(0x10000));mem.map(0x41000000,bytes(0x2000))
 def string(at):
  out=bytearray()
  while mem.read(at+len(out),1)!=b'\0':
   out+=mem.read(at+len(out),1)
   if len(out)>1024:raise ValueError('Unbounded native prefix')
  return bytes(out)
 def memset(v):mem.write(v.r[3],bytes([v.r[4]&255])*v.r[5]);v.pc=v.lr
 def strlen(v):v.r[3]=len(string(v.r[3]));v.pc=v.lr
 def cat(v):
  a=string(v.r[3]);b=string(v.r[4])[:v.r[5]];mem.write(v.r[3]+len(a),b+b'\0');v.pc=v.lr
 def copy(v):
  b=string(v.r[4])[:v.r[5]];mem.write(v.r[3],b+bytes(v.r[5]-len(b)));v.pc=v.lr
 def lookup(v):v.r[3]=STAGES+index*52;v.pc=v.lr
 m=P.Machine(mem);m.r=[0x770000+i for i in range(32)];m.r[1]=0x40008000;m.r[2]=H.TOC;m.r[3:7]=[0,0x41000000,512,kind]
 m.hooks={0x1dcd78:lookup,0x69327c:memset,0x68a2ac:strlen,0x68f978:cat,0x68fca0:copy}
 m.pc=PREFIX_START;m.lr=0xdead0000;m.run({m.lr},limit=5000)
 if m.r[3]!=0x41000000:raise ValueError('Native prefix return pointer differs')
 return string(0x41000000),m.steps

@lru_cache(None)
def stage_rows():
 elf=H.PREPARED.read_bytes();rd=H._reader(elf,H._headers(elf)[2]);translations=E.load()['strings'];resolver=E.resolver();rows=[];cache={}
 if rd(H.TOC-0x41d8,4)!=struct.pack('>I',STAGES):raise ValueError('Native stage table moved')
 for index in range(375):
  raw=rd(STAGES+index*52,52);name=rd(struct.unpack_from('>I',raw,4)[0],24).split(b'\0')[0].decode('ascii')
  if not name.startswith('2'):continue
  number=struct.unpack_from('>h',raw,14)[0];tid=struct.unpack_from('>H',raw,24)[0]
  if tid==65535:
   rows.append(dict(index=index,stage=name,title_id=None,source_sha256=sha256(raw),display=False));continue
  title=rd(struct.unpack('>I',rd(TITLES+tid*4,4))[0],256).split(b'\0')[0].decode('utf8')
  if title not in translations or not translations[title].get('en'):raise ValueError('Untranslated stage title: '+str(tid))
  en=E.unshow(L.expand(translations[title]['en'],resolver))
  if E.unusual(en):raise ValueError('Stage title is not fully translated: '+str(tid))
  prefixes=[];steps=[]
  for kind in (0,1):
   key=(number,raw[30],kind)
   if key not in cache:cache[key]=native_prefix(elf,index,kind)
   prefix,n=cache[key];prefixes.append(prefix);steps.append(n)
  jp=prefixes[0].decode('utf8')
  if prefixes[1]!=jp.encode('cp932'):raise ValueError('Native heading encodings disagree')
  if jp.startswith('第'):english='Episode '+str(number)
  elif jp.startswith('プロローグ第'):english='Prologue '+str(number+2)
  else:english=translations[jp]['en'] if jp else ''
  caption=(english+': 'if english else '')+en
  if sum(map(advance,caption))*28/32>1040:raise ValueError('Complete stage heading exceeds panel: '+caption)
  rows.append(dict(index=index,stage=name,title_id=tid,title=title,english=en,prefix=jp,prefix_en=english,caption=caption,
   source_sha256=sha256(raw),display=True,native_steps=steps))
 if len(rows)!=193 or {r['title_id']for r in rows if r['display']}!=set(range(129)):raise ValueError('Stage/title inventory changed')
 return rows

def name_entries(mapping):
 names=RP.load_names();parts={};out={}
 for row in RP.slots(RP.load_rpw()):
  if row['chunk']=='pilot-nw':parts.setdefault(row['record'],{})[row['col']]=RP.text_for(row,names)
 # Encode the English pieces independently: the native separator is not a
 # translated VWF dot. Never replace the global dot glyph or saved names.
 for rid,columns in parts.items():
  family,given=columns[1],columns[2]
  if not family or not given or family==given or family in ('-','???')or given in ('-','???'):continue
  for kind,(a,z)in enumerate(((given,family),(family,given))):
   key=E.encode(a,mapping)+'・'.encode('cp932')+E.encode(z,mapping)
   row=dict(id=f'review48:name:{rid}:{kind}',key=key,english=E.encode(a+' '+z,mapping))
   if key in out and out[key]['english']!=row['english']:raise ValueError('Ambiguous native pilot name')
   out[key]=row
 return list(out.values())

def title_entries(elf,mapping):
 if sha256(elf)!=sha256(H.PREPARED.read_bytes()):raise ValueError('Stage headings require the original source')
 out={}
 for row in stage_rows():
  if not row['display']:continue
  title=row['title'];prefix=row['prefix']
  for lead in ('','　'):
   for gap in ('',' ','　'):
    text=lead+prefix+gap+'『'+title+'』'
    key=H.utf8_key(text.encode('utf8'),elf)
    out[key]=dict(id=f"review48:stage:{row['index']}:{len(out)}",key=key,english=E.encode(row['caption'],mapping))
  # Plain title and title-only quoted views remain independently translated.
  for text in (title,'『'+title+'』'):
   key=H.utf8_key(text.encode('utf8'),elf)
   out[key]=dict(id=f"review48:title:{row['title_id']}:{len(out)}",key=key,english=E.encode(row['english'],mapping))
 return [dict(row,id='review48:stage-key:'+str(i))for i,row in enumerate(out.values())]

def hook_entries(elf,mapping):return name_entries(mapping)+title_entries(elf,mapping)

def catalog_audit():
 translations=E.load()['strings'];resolver=E.resolver()
 records=[r for r in E.records()if r['family']=='stage_titles']
 for row in records:
  en=translations[row['jp']].get('en')
  if not en or E.unusual(E.unshow(L.expand(en,resolver))):raise ValueError('Untranslated title catalog entry')
 catalog=json.loads((ROOT/'work/translation/en/ui/title_cards.json').read_text('utf8'))
 cards=catalog['cards']
 if len(cards)!=128 or any(not r.get('en')or E.unusual(r['en'])for r in cards.values()):raise ValueError('Incomplete title-card translation')
 art=json.loads((ROOT/'work/translation/en/ui/effps3_art.json').read_text('utf8'))
 # The last episode has its own EFF texture rather than a TPACK title card.
 def walk(value):
  if isinstance(value,dict):
   yield value
   for v in value.values():yield from walk(v)
  elif isinstance(value,list):
   for v in value:yield from walk(v)
 final=next(r for r in walk(art)if r.get('id')=='heading:107')
 if final['en']!=['Final Episode','World Without End']:raise ValueError('Final title artwork differs')
 return dict(catalog_records=len(records),catalog_unique_titles=len({r['jp']for r in records}),untranslated=0,
  translated_texture_cards=len(cards),native_english_texture_member=88,final_texture_member=107,final_texture_english=final['en'])

def report():
 rows=stage_rows();return dict(stage_records=len(rows),display_records=sum(r['display']for r in rows),
  title_count=len({r['title_id']for r in rows if r['display']}),
  prefixes=dict(Counter(r['prefix']for r in rows if r['display'])),catalog=catalog_audit(),runtime_verified=False)
