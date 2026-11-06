"""Context-scoped DLC mission, squad and title authoring; no machine identifiers."""
import argparse,json,re,unicodedata
from tools.common import ROOT,write_json
from tools import dlc_text as T,squad_text as S,mission_text as M,eboot_text as E,rpw_text as R,library_build as L
from tools.library_text import GLOSSARY,Resolver
DEST=ROOT/'work/translation/en/dlc_ui.json'
NEW_MISSIONS={
 'ダウンロードコンテンツには\nＳＲポイントはありません。':'DLC scenarios have no SR Point.',
 'ドラゴンズハイヴの撃墜。':"Dragon\'s Hive is shot down.",
 '３時の方向のマーカーに到着する。':"Reach the marker at 3 o'clock.",
 '９時の方向のマーカーに到着する。':"Reach the marker at 9 o'clock.",
 'なし':'None',
 'ボン太くんの撃墜。':'Bonta-kun is shot down.',
 '五飛の撃墜。':'Wufei is shot down.',
 'いずれかのＦＢ隊員の撃墜。':'Any Firebug member is shot down.',
 'デルタプラスの撃墜。':'Shoot down Delta Plus.',
 '４ターン味方フェイズを迎える。':'Reach the allied phase of turn 4.'}
NEW_NAMES={'光球':'Orb of Light','通常':'Normal','母艦':'Mothership','ロボットマフィア':'Robot Mafia','タロス像':'Talos Statue','ピクシー１':'Pixie 1','テロリスト':'Terrorists','アヤナミ':'Ayanami'}

def plan():
 terms=json.loads(GLOSSARY.read_text('utf8'))['terms'];res=Resolver(terms);source_names=S.load()['strings'];source_missions=M.load()['strings'];rpw=R.load_names()['strings'];eboot=E.load()['strings']
 def canonical(jp):
  if jp in NEW_NAMES:return NEW_NAMES[jp]
  if re.fullmatch('ＥＶＡ[０-９]+',jp):return 'EVA-'+unicodedata.normalize('NFKC',jp[3:])
  if jp in source_names:return L.expand(source_names[jp]['en'],res)
  if '＆'in jp:return ' & '.join(canonical(s)for s in jp.split('＆'))
  en={t['en']for t in terms if t['jp']==jp and t.get('en')}
  if len(en)==1:return en.pop()
  if jp in eboot and eboot[jp].get('en'):return L.expand(eboot[jp]['en'],res)
  en={d[jp]['en']for fam,d in rpw.items()if jp in d and fam in ('pilot','robot','series')}
  if len(en)==1:return en.pop()
  raise ValueError('Unresolved DLC UI name '+repr(jp)+' '+repr(en))
 names={};missions={};titles={};assets={};unclassified=[]
 for p in T.inventory()['packages']:
  for m in p['members']:
   raw=(ROOT/m['path']).read_bytes()
   if m['id']==0:
    jp=raw[40:168].split(b'\0')[0].decode('cp932');utf8=raw[168:296].split(b'\0')[0].decode('utf8')
    if jp!=utf8:raise ValueError('DLC title encoding variants disagree')
    en=eboot[jp]['en']if jp in eboot else 'Premium Present'if p['code']=='DLC2334'and jp=='予備'else None
    if not en:raise ValueError('Untranslated DLC title')
    titles[p['code']]=dict(jp=jp,en=L.expand(en,res),utf8_source='プレミアム・プレゼント'if p['code']=='DLC2334'else jp,
     reason='Replace reserved placeholder with supplied Premium Present package title.'if p['code']=='DLC2334'else'Existing canonical stage title.')
   if b'\0'in raw:continue
   for lit,jp in S.literals(raw):names[jp]=dict(en=canonical(jp),kind='squad_name')
   for table,lits,roles in M.tables(raw):
    for (lit,jp),rs in zip(lits,roles):
     en=NEW_MISSIONS.get(jp)or(source_missions.get(jp)or{}).get('en')
     if not en:raise ValueError('Untranslated DLC condition '+repr(jp))
     errors=[];M.validate(p['code'],jp,en,res,errors)
     if errors:raise ValueError(errors)
     missions[jp]=dict(en=en,roles=sorted(rs))
   # Every other quoted source string is either numeric, program/debug data or an internal asset label.
   for lit in S.scan(raw):
    jp=M.unescape(lit['raw'])
    if not M.needs_text(jp):continue
    if S.in_scope(lit['ctx']):continue
    if any((nm or b'').startswith(b'OPERATE_TBL')for _,nm,_ in lit['ctx']):continue
    unclassified.append((p['code'],m['id'],jp,[str(nm)for _,nm,_ in lit['ctx']]))
  for name in ('ICON0.PNG','PIC1.PNG'):
   path=ROOT/'work/tengoku_dlc'/p['code']/'package'/name
   from tools.common import sha256_file
   assets.setdefault(name,set()).add(sha256_file(path))
 if unclassified:raise ValueError('Unclassified Japanese quoted literals: '+repr(unclassified[:5]))
 return dict(schema=1,version='0.5.49',titles=titles,missions=missions,names=names,
  shared_images={k:sorted(v)for k,v in assets.items()},shared_image_review='PIC1 has no Japanese prose; ICON0 is shared game branding, preserved.',
  runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
 print('Titles',len(data['titles']),'Conditions',len(data['missions']),'Names',len(data['names']))
 for jp,row in data['names'].items():print(jp,'=>',row['en'])
 if a.apply:write_json(DEST,data)
 else:print('DRY RUN: authored UI catalog only.')
if __name__=='__main__':main()
