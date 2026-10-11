"""Complete assembled target/movement families and readable status columns."""
import argparse
import itertools
import json
import struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,ui_hook as H,eboot_text as E,status_layout as S

DEST=ROOT/'work/translation/en/ui/category_layout.json'
TERRAIN=ROOT/'work/translation/en/ui/terrain_names.json'
TARGET_PREFIX={'自分':'Self','味方':'Ally','敵':'Enemy','自チーム':'Own Team'}
TARGET_SUFFIX={'単体':'Single','周囲':'Area','全体':'All','チーム':'Team'}
TARGET_COMPACT={'敵単体':'One Foe','敵周囲':'Foe Area','敵全体':'All Foes','敵チーム':'Foe Team',
                '自チーム単体':'Team Unit','自チーム周囲':'Team Area',
                '自チーム全体':'Own Team','自チームチーム':'Own Team'}


def assembled_targets(elf):
    read=H._reader(elf,H._headers(elf)[2])
    for va,jp in ((0xa0de3e,'自分'),(0xa0de44,'味方'),(0xa0de4a,'敵'),(0xa0de4e,'自チーム'),
                  (0xa0de58,'単体'),(0xa0de5e,'周囲'),(0xa0de64,'全体'),(0xa0de6a,'チーム')):
        if read(va,len(jp.encode('cp932'))+1)!=jp.encode('cp932')+b'\0':
            raise ValueError('Spirit target fragment changed')
    return {p+s:TARGET_COMPACT.get(p+s,('One Ally' if p+s=='味方単体'
        else 'All Allies' if p+s=='味方全体'
        else 'Self' if p+s=='自分単体' else a+' '+b))
        for p,a in TARGET_PREFIX.items()for s,b in TARGET_SUFFIX.items()}


def terrain_rows():
    from tools.cpk import CPK
    from tools.pipeline import config,verified_source
    from tools.common import sha256_file
    data=json.loads(TERRAIN.read_text(encoding='utf8'))
    path=verified_source(config(ROOT/'config/tengoku.json'),B.MAP_ARCHIVE)
    if sha256_file(path)!=data['archive_sha256']:raise ValueError('Terrain archive changed')
    with CPK(path)as archive:
        members={e['id']:archive.read(e)for e in archive.files if e['id']%4==0}
    found={}
    for mid,blob in members.items():
        w,h,count,flags,unit,base,size,grid=struct.unpack_from('<8I',blob)
        if base!=32 or size!=count*32 or grid!=w*h or len(blob)!=base+size+grid:
            raise ValueError('Terrain member geometry changed')
        for n in range(count):
            at=36+n*32;field=blob[at:at+28];raw=field.split(b'\0')[0]
            if not raw:continue
            jp=raw.decode('cp932');row=data['strings'][jp]
            bound=next((r for r in row['bindings']if r['member']==mid and r['record']==n),None)
            if not bound or bound['source_field_sha256']!=sha256(field) or row['source_sha256']!=sha256(raw):
                raise ValueError('Terrain field fingerprint changed')
            if row.get('reviewed')is not True:raise ValueError('Unreviewed terrain')
            from tools.ui_description_layout import advance
            if row['width_at_28']!=sum(map(advance,row['en']))*28/32:
                raise ValueError('Terrain label measurement changed')
            found[jp]=row['en']
    if set(found)!=set(data['strings'])or len(members)!=128:raise ValueError('Terrain coverage differs')
    return found


def hook_entries(elf,mapping):
    out=[]
    texts=dict(assembled_targets(elf),**terrain_rows())
    # The movement composer has four independent flags. Cover all 16 states,
    # including callers that still assemble the native table characters.
    for flags in itertools.product((False,True),repeat=4):
        jp=''.join(c if present else '－' for c,present in zip('空陸水地',flags))
        texts[jp]=''.join(S.TERRAIN[c]if present else '－'for c,present in zip('空陸水地',flags))
    for jp,en in texts.items():
        keys={H.utf8_key(jp.encode('utf8'),elf)}
        raw=jp.encode('cp932')
        try:
            if H.extent(raw+b'\0')==len(raw):keys.add(raw)
        except ValueError:pass
        for key in sorted(keys):
            out.append(dict(id='category:'+str(len(out)),key=key,english=E.encode(en,mapping)))
    # The first training column replaces a blank placeholder at runtime.
    for jp,en in (('格：\n射：',S.CELL['CQB']+'\n'+S.CELL['RNG']),
                  ('格：',S.CELL['CQB']),('射：',S.CELL['RNG'])):
        out.append(dict(id='category:training:'+str(len(out)),key=jp.encode('cp932'),english=E.encode(en,mapping)))
    # Default names substituted into compiled mission conditions bypass the
    # dialogue-only getters. Match complete display strings; custom names and
    # all save/name buffers remain untouched.
    from tools import mission_text as M,library_build as L
    from tools.ui_vwf_build import raster
    rendered=M.plan(lambda c:raster(c)[1]if c in mapping else 32)
    for text in rendered.values():
        if 'ヒビキＡ' not in text and 'ヒビキＮ' not in text:continue
        compiled=L.encode(text,mapping)
        for placeholder in ('ヒビキＡ','ヒビキＮ'):
            raw=placeholder.encode('cp932')
            if raw not in compiled:continue
            out.append(dict(id='category:mission-name:'+str(len(out)),
                key=compiled.replace(raw,'ヒビキ'.encode('cp932')),
                english=compiled.replace(raw,E.encode('Hibiki',mapping))))
    return list({r['key']:r for r in out}.values())


def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits={}
    def bind(at,en,**changes):
        row=widgets[at];edits[at]=dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),source_xy=list(struct.unpack_from('>ff',source,at+4)),
            notes=changes.pop('notes','Readable labels in the native stat columns; keep live values and row pitch.'),**changes)
    for at,row in widgets.items():
        if row['text']=='気力':bind(at,'Foc')
    for at,en in ((0x9d644,'SKL\nDEF'),(0x9d664,'EVD\nHIT'),(0x9ddc4,'CQB\nRNG'),
                  (0x9dde4,'SKL\nDEF'),(0x9de04,'EVD\nHIT'),(0x9d7c4,'SKL\nDEF'),(0x9d7e4,'EVD\nHIT')):
        metrics=list(source[at+16:at+21]);metrics[3]=26
        bind(at,en,font_metrics=metrics)
    bind(0x9d804,'Train')
    for at,en in ((0x9d824,'CQB\nRNG'),(0x9d844,'SKL\nDEF'),(0x9d864,'EVD\nHIT')):
        metrics=list(source[at+16:at+21]);metrics[3]=28
        bind(at,'\n'.join(S.CELL[word]for word in en.split('\n')),font_metrics=metrics,
             display_labels=en,notes='Enlarged one-cell labels fit before the native training parentheses; preserve live value positions and row pitch.')
    bind(0x8f864,'Eff.')
    return dict(schema=1,version='0.5.17',source_member_sha256=sha256(source),edits=list(edits.values()),
        terrain_names=len(terrain_rows()),target_combinations=len(assembled_targets(H.PREPARED.read_bytes())),
        runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=plan()
    for r in data['edits']:print(hex(r['widget_offset']),repr(r['en']),r.get('font_metrics'))
    print('Terrain names:',data['terrain_names'],'Spirit target combinations:',data['target_combinations'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
