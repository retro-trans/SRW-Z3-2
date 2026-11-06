"""Apply reviewed DLC terminology after agent edits; no base-game prose rewrite."""
import argparse,copy,json,re
from tools.common import ROOT,write_json
from tools import dlc_text as T
from tools.library_text import GLOSSARY,term
RESEARCH=ROOT/'work/glossary/research/dlc_terms.json'
TERMS=[
 ('オハイオ屋','Ohio-ya','location','proposed transliteration; no established English spelling found',[]),
 ('コッヘル','Kocher','keyword','camping cookware; a deliberately wrong mascot guess, not a character',['https://kotobank.jp/word/こつへる-3151749']),
 ('暁の疾風旅団','Dawn Gale Brigade','keyword','proposed faction name; Firebug remnants reduced to banditry',[]),
 ('根源的災厄','Primordial Calamity','keyword','proposed name; distinct from Origin Law',['https://srw.wiki.cre.jp/wiki/ネタバレ/第3次Z天獄篇']),
 ('根源的な災厄','Primordial Calamity','keyword','alias of 根源的災厄',[]),
 ('根源の災厄','Primordial Calamity','keyword','alias of 根源的災厄',[]),
 ('ＡＣＰファイズ','ACP Faiz','keyword','ACP (Assault Combat Pattern) Faiz; attack/tactic',['https://www.akurasu.net/wiki/Units_List/Banpresto_Originals/Unit_Descriptions']),
 ('クリスタル超獣','Crystal Superbeast','keyword','proposed literal; plural Crystal Superbeasts',[]),
 ('Ｇビット','G-Bit','keyword','plural G-Bits; Bandai uses G-BIT/G-BITs',['https://www.bandai.co.jp/candy/gundam/un2/pb02/']),
 ('ノックス','Nocis','location','Turn A city; English episode title uses Nocis',['https://gundam.fandom.com/wiki/The_Fall_of_Nocis']),
 ('貧乏くじ同盟','Hard Luck Alliance','keyword','proposed informal group nickname',['https://srw.wiki.cre.jp/wiki/貧乏クジ同盟']),
 ('貧乏クジ同盟','Hard Luck Alliance','keyword','alias of 貧乏くじ同盟',[])]

def plan():
 glossary=json.loads(GLOSSARY.read_text('utf8'));before=copy.deepcopy(glossary);known={t['token']:t for t in glossary['terms']};source={r['id']:r for r in T.all_rows()};edits={};counts={};research=[]
 for jp,en,kind,note,urls in TERMS:
  related=[r for r in source.values()if jp in r['jp']]
  status='proposed'if 'proposed'in note or not urls else'sourced';origin='DLC context review 2026-11-06'
  if jp in known:
   if known[jp]['en']!=en:raise ValueError('Conflicting DLC term '+jp)
  else:
   glossary['terms'].append(dict(term(jp,kind,en,status,origin,[]),token=jp,researched_token=True,note=note))
  entry=next(t for t in glossary['terms']if t.get('token')==jp)
  entry.setdefault('targets',[]);entry['researched_token']=True
  research.append(dict(jp=jp,token=jp,en=en,kind=kind,status=status,source=origin,note=note,sources=urls,source_records=[r['id']for r in related],official=False))
 for path in sorted(T.ANSWERS.glob('*.json')):
  data=json.loads(path.read_text('utf8'));new=copy.deepcopy(data)
  for rid,row in new['rows'].items():
   src=source[rid]['jp'];text=row['en']
   for jp,en,_,_,_ in TERMS:
    if jp not in src:continue
    pattern=re.compile(r'(?<![\w$])'+re.escape(en)+r'(s)?(?![\w$])')
    text,n=pattern.subn(lambda m:'$$'+jp+'$$'+(m[1]or''),text)
    if n:counts[jp]=counts.get(jp,0)+n
   if '天翅'in src:
    text=text.replace('Shadow $$エンジェル$$','$$堕天翅$$')
    text=text.replace('$$天翅$$','$$堕天翅$$')
    text=re.sub(r'(?<![\w$])Shadow Angel(s)?(?![\w$])',lambda m:'$$堕天翅$$'+(m[1]or''),text)
   row['en']=text
  if new!=data:edits[path]=new
 prior=json.loads(RESEARCH.read_text('utf8')).get('tokenized',{})if RESEARCH.exists()else{}
 return glossary,before,dict(schema=1,date='2026-11-06',terms=research,tokenized={k:prior.get(k,0)+counts.get(k,0)for k in prior.keys()|counts.keys()},
  note='Source-based terminology; proposed items are not claimed official. Existing base-game prose and the ambiguous global 天翅 token remain unchanged.'),edits

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();g,b,r,edits=plan()
 print('New glossary entries',len(g['terms'])-len(b['terms']),'DLC files',len(edits),'Occurrences',r['tokenized'])
 if a.apply:
  write_json(GLOSSARY,g);write_json(RESEARCH,r)
  for path,data in edits.items():write_json(path,data)
 else:print('DRY RUN: add reviewed glossary aliases and replace matching literal DLC names with tokens.')
if __name__=='__main__':main()
