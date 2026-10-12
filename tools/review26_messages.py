"""Translate the complete source-bound stage-report and leveled-skill families."""
import argparse,json,re,struct
from tools.common import ROOT,sha256,write_json
from tools import squad_text as S,mission_text as M,eboot_text as E,ui_hook as H,rpw_text as R
DEST=ROOT/'work/translation/en/ui/review26_messages.json'

def gifts():
    found={}
    for mid,raw in S.members():
        for lit in S.scan(raw):
            if not any(k=='{' and (nm or b'').startswith(b'GIFT') for k,nm,i in lit['ctx']):continue
            jp=M.unescape(lit['raw'])
            if not M.needs_text(jp):continue
            row=found.setdefault(jp,dict(source_sha256=sha256(jp.encode('cp932')),occurrences=[]))
            row['occurrences'].append(dict(member=mid,offset=lit['start'],literal_sha256=sha256(lit['raw'])))
    return found

def english(jp):
    if 'ＡＧからのボーナス' in jp:
        number=re.search(r'([０-９]+)Ｚ',jp)[1];number=''.join(str(ord(c)-0xff10)for c in number)
        return 'Received a bonus from AG:\n'+number+' Z-Chips.'
    if jp.startswith('強化パーツ'):
        parts=R.load_names()['strings']['part'];names=[]
        for name in re.findall('「([^」]+)」',jp):
            if name not in parts:raise ValueError('Unknown reported Power Part')
            names.append(parts[name]['en'])
        return 'Obtained Power Part'+('s'if len(names)>1 else '')+': '+' and '.join(names)+'.'
    fixed={
      'インターミッションで「Ｄトレーダー」が使用可能になりました。':'D-Trader is now available during intermission.',
      'インターミッションのコマンド「サブオーダー」が\n使用可能になりました':'Sub Order is now available\nduring intermission.',
      '機体『サーペント』を入手した':'Obtained the Serpent unit.',
      'ＤＥＭ輸送艦に使用した改造費用は\n払い戻されました':'The funds spent upgrading the DEM Transport Ship\nhave been refunded.',
      'ブレイヴの改造に使われた資金が払い戻されました。':'The funds spent upgrading the Brave have been refunded.',
      'レクチャープレート『Ｄコマンド』が解放されました':'The D-Command Lecture Plate is now unlocked.',
      'レクチャープレート『真化融合』が解放されました':'The Shinka Fusion Lecture Plate is now unlocked.',
      '３０１のメッセージ':'Message 301','出てはいけない':'This must not appear.'}
    if jp not in fixed:raise ValueError('Unreviewed stage report')
    return fixed[jp]

def plan():
    found=gifts()
    if len(found)!=24 or sum(len(r['occurrences'])for r in found.values())!=99:raise ValueError('Report family changed')
    return dict(schema=1,version='0.5.26',player_notices=22,player_occurrences=97,developer_notices=2,
        strings={jp:dict(row,en=english(jp),developer_only=all(x['member']==863 for x in row['occurrences'])and jp in ('３０１のメッセージ','出てはいけない'))for jp,row in found.items()})

def characters():
    return set(''.join(english(jp)for jp in gifts()).replace('\n','')+'Newtype Lv 0123456789')

def hook_entries(elf,mapping):
    data=plan()
    if json.loads(DEST.read_text('utf8'))!=data:raise ValueError('Report bindings stale')
    from tools.library_build import wrap
    from tools.ui_vwf_build import raster
    width=lambda c:raster(c)[1]if c in mapping else 32
    out=[]
    def add(key,en,ident):
        if H.extent(key+b'\0')!=len(key):raise ValueError('Invalid composed report/skill key')
        out.append(dict(id='review26:'+ident,key=key,english=E.encode(en,mapping)))
    for jp,row in data['strings'].items():
        en='\n'.join(wrap(line,width,1070) for line in row['en'].split('\n'))
        if len(en.splitlines())>3:raise ValueError('Stage report exceeds panel rows')
        add(jp.encode('cp932'),en,'gift:'+row['source_sha256'][:16])
    # The native constructor copies the Newtype prefix and appends its level.
    read=H._reader(elf,H._headers(elf)[2])
    prefix=struct.unpack('>I',read(H.TOC-0xa54,4))[0]
    if prefix!=0x8dc808 or read(prefix,22)!='ニュータイプＬ'.encode('utf8')+b'\0':raise ValueError('Newtype requirement source changed')
    table=struct.unpack('>I',read(H.TOC-0xa5c,4))[0]
    if table!=0xa2f5a0:raise ValueError('Requirement digit source changed')
    bases={s['jp']:R.text_for(s,R.load_names())for s in R.slots(R.load_rpw())if s['family']=='skill' and R.needs_text(s['jp'])}
    for n,va in enumerate(struct.unpack('>10I',read(table,40))):
        digit=chr(0xff10+n)
        if read(va,3)!=digit.encode('cp932')+b'\0':raise ValueError('Requirement level changed')
        for jp,en in bases.items():
            if not en:raise ValueError('Untranslated skill base')
            for suffix in ('Ｌ'+digit,'Ｌ　'+digit):
                add((jp+suffix).encode('cp932'),en+' Lv '+str(n),'skill:'+sha256((jp+suffix).encode('cp932'))[:16])
                add(E.encode(en,mapping)+suffix.encode('cp932'),en+' Lv '+str(n),'skill-encoded:'+sha256((jp+suffix).encode('cp932'))[:16])
        add(H.utf8_key(('ニュータイプＬ'+digit).encode('utf8'),elf),'Newtype Lv '+str(n),'newtype:'+str(n))
    return list({r['key']:r for r in out}.values())

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['strings'].values():print(len(row['occurrences']),repr(row['en']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no data written.')
if __name__=='__main__':main()
