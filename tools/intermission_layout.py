"""Bound intermission and Library widgets; preserve live counters and IDs."""
import argparse
import struct
from tools.common import ROOT, sha256, write_json
from tools import ui_catalog, battle_layout
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/intermission_layout.json'


def plan():
    s=battle_layout.source()
    widgets={a:r for r in ui_catalog.fssa_strings(s) for a in r['widget_offsets']}
    edits={}
    def bind(at,en,**changes):
        row=widgets[at]
        edits[at]=dict(widget_offset=at,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(s[at:at+32]),source_xy=list(struct.unpack_from('>ff',s,at+4)),
            en=en,notes='Screenshot-bound intermission / Library label; preserve state and live values.',**changes)
    def center(at,en,size=None,correction=0):
        size=size or s[at+19]
        width=sum(map(advance,en))*size/32
        x=struct.unpack_from('>f',s,at+4)[0]-width/1280+correction/640
        changes=dict(x=x,mode=s[at+23]&~0x40)
        if size!=s[at+19]:changes['font_metrics']=[size,size,max(1,size-2),size,size]
        bind(at,en,**changes)
    labels={'パイロット一覧':'Pilot List','パイロット養成':'Training','機体一覧':'Mech List',
        '機体・武器改造':'Upgrades','サブオーダー':'Sub Orders','のせかえ':'Pilot Swap',
        '強化パーツ':'Power Parts','換装パーツ':'Swap Parts','検索':'Search','オプション':'Options',
        'セーブ':'Save','ロード':'Load','次のマップへ':'Next Map','データ引継ぎへ':'Carry Over',
        '分岐シナリオへ':'Route Select','ネットワーク':'Network'}
    for at,r in widgets.items():
        if 0x9b484<=at<=0x9b9e4 and r['text'] in labels:center(at,labels[r['text']])
    for first,tails in ((0x9b844,(0x9b864,0x9b884)),(0x9b8a4,(0x9b8c4,0x9b8e4)),
                        (0x9b904,(0x9b924,0x9b944)),(0x9b964,(0x9b984,0x9b9a4))):
        en='Team Setup' if first<0x9b900 else 'D-Trader'
        center(first,en,28 if first in (0x9b844,0x9b904) else 31)
        # The first piece was left anchored: use the ordinary button center.
        edits[first]['x']=-0.00234375-sum(map(advance,en))*edits[first].get('font_metrics',[0,0,0,s[first+19]])[3]/(32*1280)
        for tail in tails:bind(tail,'')
    for at in (0x97aa4,0x97ac4,0x97b44,0x97bc4,0x97be4):
        center(at,{'システム':'System','ライブラリー':'Library','ボーナスシナリオ':'Bonus Maps',
                   'アップロード':'Upload','ダウンロード':'Download'}[widgets[at]['text']])
    center(0x97c64,'Rengoku Link',25)
    # Mode 3 already calls the centered drawer. Its VWF helper measures this
    # caption, so retain the native center instead of subtracting it twice.
    edits[0x97c64]['x']=struct.unpack_from('>f',s,0x97c68)[0]
    for at in (0x97c84,0x97ca4,0x97cc4,0x97ce4):bind(at,'')
    center(0x97b24,'PS Store',25)
    for at in (0x97b64,0x97b84,0x97ba4):bind(at,'')
    # Library's special renderer adds the original full-width caption's
    # half-width after the stored coordinate. Compensate with measured ink,
    # preserving its special mode 0x01 and native 72px text metrics.
    library=('Robot Library','Robot Library','Character Library','Glossary','Sound Select','Scenario Chart')
    for at,en in zip(range(0x94b04,0x94bc4,32),library):
        original=widgets[at]['text']; old_half=len(original)*37/2
        width=sum(map(advance,en))*37/32
        bind(at,en,x=struct.unpack_from('>f',s,at+4)[0]+(old_half-width/2)/640)
    for at,r in widgets.items():
        if 0x9aec4<=at<=0x9b464:
            if r['text']=='機':bind(at,'')
            elif r['text']=='第話':bind(at,'Ep',x=struct.unpack_from('>f',s,at+4)[0]-10/640)
            elif r['text']=='　クリア':bind(at,'Clear',x=struct.unpack_from('>f',s,at+4)[0]+8/640)
            elif r['text']=='＜　　ターン＞':bind(at,'＜　　 turns＞')
            elif r['text']=='隊\n隻\n':bind(at,'\n\n')
            elif r['text']=='チーム：\n母艦　：':bind(at,'Teams:\nShips:')
            elif r['text']=='出撃\n母艦':bind(at,'Teams\nShips')
    # Top pilot score labels use the same unit suffix outside this footer.
    for at,r in widgets.items():
        if 0x9aec4<=at<=0x9b464 and r['text']=='機':bind(at,'')
    return dict(schema=1,version='0.5.15',source_member_sha256=sha256(s),
                edits=list(edits.values()),runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),repr(e['en']),round(e.get('x',0),5))
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
