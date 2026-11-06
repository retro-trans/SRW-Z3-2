"""Complete DLC menu text, including split-row and native system consumers."""
import argparse,json,struct
from functools import lru_cache
from tools.common import ROOT,sha256,write_json
from tools import eboot_text as E,ui_hook as H,library_build as L,battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance,condensed_advance
VERSION='0.5.51'
DEST=ROOT/'work/translation/en/ui/review51_dlc_menu.json'
TABLE=0xa1b508
RULES=0x896040

@lru_cache(None)
def catalog():
 original=H.PREPARED.read_bytes();rd=H._reader(original,H._headers(original)[2]);res=E.resolver();old=E.load()['strings']
 expanded={}
 for path in sorted(U.DEST.glob('*.json')):expanded.update(json.loads(path.read_text('utf8'))['strings'])
 result={}
 for row in E.records():
  va=int(row['va'],16)
  menu=0x893bd8<=va<0x894578 and row['family']!='debug'and va!=0x893df8
  if row['family']!='dlc_synopsis'and not menu and va!=RULES:continue
  jp=row['jp'];en=(old.get(jp)or expanded.get(sha256(jp.encode('utf8'))[:20])or{}).get('en')
  if va==0x893eb8:en='Funds: '
  if va==0x893ed0:en='Z-Chips: '
  if va==0x893ee8:en='Power Parts: '
  if va==0x893f00:en='             '
  if va==0x893f18:en='-----\n'
  if va==0x9efc38:en='The protagonist and Suzune infiltrate a New Earth Empire-held town to liberate it.\nBut mid-mission, under intense stress, Suzune...'
  if not en:raise ValueError('Untranslated DLC menu entry: '+row['va'])
  en=E.unshow(L.expand(en,res))
  if E.FORMAT.findall(en)!=E.FORMAT.findall(jp):raise ValueError('DLC menu placeholder changed')
  if en.count('\n')!=jp.count('\n'):raise ValueError('DLC menu row boundaries changed')
  result[row['va']]=dict(en=en,source_sha256=sha256(jp.encode(row['encoding'])),kind='synopsis'if row['family']=='dlc_synopsis'else'rules'if va==RULES else'state'if va<0x893cb0 else'prompt')
 if len(result)!=74:raise ValueError('DLC menu inventory changed')
 return dict(schema=1,version=VERSION,rows=result,meaning_review=dict(examined=74,in_scope=74,linguistic_entries=72,synopses=35,prompts=29,menu_states=9,rules=1,
  corrections=['Restore the first synopsis purpose clause to its original first row.'],new_terms=0,uncertainties=[]))

def checked():
 data=catalog()
 if json.loads(DEST.read_text('utf8'))!=data:raise ValueError('DLC menu authoring is stale')
 return data

def entries(mapping):
 data=checked();records={r['va']:r for r in E.records()};out={};bounds=[]
 from tools.dialogue_layout import PREFIX
 from tools.review32_content import CAPTION_MARK
 for va,row in data['rows'].items():
  if row['kind']in('prompt','state'):continue
  source=records[va];jp=source['jp'];en=row['en']
  for n,(key,text)in enumerate(zip(jp.split('\n'),en.split('\n'))):
   condensed=row['kind']=='synopsis'and sum(map(advance,text))*27/32>960
   selected=dict(mapping)
   if condensed:selected.update({k[len(PREFIX):]:v for k,v in mapping.items()if k.startswith(PREFIX)})
   span=sum(map(condensed_advance if condensed else advance,text));quad=27 if row['kind']=='synopsis'else 28
   width=span*quad/32
   if width>(960 if row['kind']=='synopsis'else 1070):raise ValueError('Complete DLC row exceeds panel: '+va)
   raw=key.encode(source['encoding']);raw=H.utf8_key(raw)if source['encoding']=='utf-8'else raw
   encoded=E.encode(text,selected)
   if row['kind']=='rules':encoded=bytes.fromhex(mapping[CAPTION_MARK])+encoded
   if raw in out and out[raw]['english']!=encoded:raise ValueError('Conflicting DLC menu row')
   out[raw]=dict(id='review51:'+va+':'+str(n),key=raw,english=encoded)
   bounds.append(dict(va=va,row=n,en=text,condensed=condensed,width=width,quad=quad,left=244 if row['kind']=='synopsis'else 640-width/2))
 return list(out.values()),bounds

def layout():
 s=B.source();widgets={a:r for r in U.fssa_strings(s)for a in r['widget_offsets']};edits=[]
 def bind(at,**kw):
  r=widgets[at];edits.append(dict(widget_offset=at,source_sha256=sha256(r['raw']),source_widget_sha256=sha256(s[at:at+32]),**kw))
 bind(0x92584,en='Episode',notes='Keep the episode label clear of the separately drawn availability status.')
 bind(0x928e4,en='Synopsis\n\nRewards',notes='Retain the native three-row label grid and separate it from the content column.')
 bind(0x8f844,font_quad=27,notes='Fit all complete synopsis rows with the existing ordinary/condensed alphabets; preserve the automatic width sentinels and row pitch.')
 bounds=[]
 for at,text in ((0x92584,'Episode'),(0x928e4,'Synopsis'),(0x928e4,'Rewards')):
  left=640+struct.unpack_from('>f',s,at+4)[0]*640;right=left+sum(map(advance,text))*s[at+19]/32
  limit=990 if at==0x92584 else 244
  if right+8>limit:raise ValueError('DLC menu label overlaps content')
  bounds.append(dict(widget_offset=at,en=text,left=left,right=right,neighbor_left=limit))
 return dict(schema=1,version=VERSION,edits=edits,bounds=bounds,runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=catalog()
 print('Complete DLC category:',len(data['rows']),'entries; 35 synopses, 29 prompts, 9 menu states, 1 rules notice.')
 for va in ('0x9efc38','0x894120','0x896040'):print(va,repr(data['rows'][va]['en']))
 print('Layout:',layout()['bounds'])
 if a.apply:write_json(DEST,data)
 else:print('DRY RUN: no translations or game files written.')
if __name__=='__main__':main()
