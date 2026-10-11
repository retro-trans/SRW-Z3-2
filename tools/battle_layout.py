"""Source-bound Z3-style battle-preview, hover and transformation labels."""
import argparse
import struct
from tools.common import ROOT,sha256,write_json
from tools import ui_catalog,ui_hook,eboot_text,vwf,status_layout

DEST=ROOT/'work/translation/en/ui/battle_layout.json'
# Z3's one-cell flag geometry, with this game's settled Spirit abbreviations.
TINY={chr(0xe005+i):word for i,word in enumerate(
    ('Va','So','Ft','Al','Pe','Wa','Fo','St','Ac','Ze','Me','Sn','As','Fy','Lu','Ga','Di','An'))}
SEPARATOR = chr(0xe01e)
TINY[SEPARATOR] = '/'
FLAGS=dict(zip('熱魂闘閃不鉄集必加覚手狙突直幸努乱分',TINY))
FLAGS['／'] = SEPARATOR
HOOKS={'消費ＥＮ':'EN','宇宙':'Space'}
MAP_ARCHIVE='/PS3_GAME/USRDIR/DATA/MAPETC/MAPZ3TENPS3.CPK'
MAP_MEMBER=168
MAP_SHA='c1768a55e97773d5f0464bc8d4db524f8811af57fb5a17079915ad5f10a4d138'


def terrain_entry(mapping):
    # Attributes are 32-byte records followed by a tile grid, like Z3's ZLD.
    # Bind the actual target member, without rewriting its terrain parameters.
    from tools.ui_coverage import member
    from tools.pipeline import config,verified_source
    blob=member(verified_source(config(ROOT/'config/tengoku.json'),MAP_ARCHIVE),MAP_MEMBER)
    if sha256(blob)!=MAP_SHA:raise ValueError('Map terrain source changed')
    width,height,count,flags,unit,base,size,grid=struct.unpack_from('<8I',blob)
    if base!=32 or size!=count*32 or grid!=width*height or len(blob)!=base+size+grid:
        raise ValueError('Target terrain record geometry changed')
    jp='暗礁宙域';raw=jp.encode('cp932')
    if blob[0x84:0xa0]!=raw+bytes(28-len(raw)):raise ValueError('Debris Field attribute changed')
    return dict(id='battle:terrain:168:3',key=raw,english=eboot_text.encode('Debris Field',mapping))


def raster_tiny(text,face):
    """Z3 flag profile: cap 16, baseline 23, 2px ink gap, 28px ink budget."""
    from PIL import Image,ImageDraw,ImageFont,ImageChops
    probe=ImageFont.truetype(str(face),100)
    _,top,_,bottom=probe.getbbox('H',anchor='ls')
    font=ImageFont.truetype(str(face),round(100*16/(bottom-top)*4))
    parts=[]
    for ch in text:
        l,t,r,b=font.getbbox(ch,anchor='ls')
        ink=Image.new('L',(r-l+9,b-t+8))
        ImageDraw.Draw(ink).text((4-l,4-t),ch,font=font,anchor='ls',fill=255)
        ink=ImageChops.lighter(ink,ImageChops.offset(ink,1,0))
        small=ink.resize((round(ink.width/4),round(ink.height/4)),Image.Resampling.BOX)
        box=small.getbbox()
        if box:parts.append((small.crop(box),round(23+t/4-1)+box[1]))
    natural=sum(p.width for p,y in parts);gaps=2*(len(parts)-1)
    budget=min(natural,28-gaps);out=Image.new('L',(32,32));total=last=0;x=(32-budget-gaps)//2
    for ink,y in parts:
        total+=ink.width;edge=round(total*budget/natural);width=edge-last;last=edge
        out.paste(ink.resize((width,ink.height),Image.Resampling.BOX),(x,y));x+=width+2
    return out,32


def source():
    from tools.ui_coverage import member
    from tools.pipeline import config,verified_source
    from tools.aid_art import ARCHIVE
    return member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))


def plan():
    s=source();widgets={a:r for r in ui_catalog.fssa_strings(s)for a in r['widget_offsets']};edits={}
    def bind(at,en,**changes):
        row=widgets[at]
        edits[at]=dict(widget_offset=at,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(s[at:at+32]),source_xy=list(struct.unpack_from('>ff',s,at+4)),
            en=en,notes='Fit the native battle/map label slot; retain values, line pitch and state flags.',**changes)
    for at,row in widgets.items():
        jp=row['text']
        if jp.startswith('熱魂闘閃'):
            bind(at,''.join(FLAGS.get(c,c)for c in jp))
        if jp=='気力' and (0x9a784<=at<=0x9ada4 or at in (0xa03e4,0xa0424,0x9ed84,0xa2684)):
            bind(at,'Foc')
    labels={0xa01a4:'Start Battle',0xa01c4:'Start Battle',0xa01e4:'Action',0xa0204:'Action',
        0xa0224:'Anim: OFF',0xa0244:'Anim: OFF',0xa0264:'Anim: ON',0xa0284:'Anim: ON',
        0xa0324:'Support',0xa0344:'Support',0xa0364:'S. Atk',0xa0384:'Re-Atk',0xa03a4:'S. Def',
        0x8ae64:'Atk.',0xa0444:'Atk.',0xa0584:'Ctr.',0xa05a4:'Evd.',0xa05c4:'Def.',0xa05e4:'S.D.',0xa0644:'Wait',
        0xa70e4:'Rnd.',0x8ece4:'EN',0x8ed04:'EN',0x9a4a4:'DEF:\nEVD:',
        0x9a4e4:'Rec:\nRec:',0xa6fe4:'',0x8c2e4:': Fast',0x8c944:': Fast'}
    for at,en in labels.items():bind(at,en)
    # Narrow popup labels: copy Z3's metric changes, preserving row spacing.
    for at in (0x9ac64,0x9ace4,0x9ad64):bind(at,'MV',font_metrics=[22,22,20,22,22])
    for at,en in ((0xa4dc4,'AT\nDF'),(0xa6464,'AT'),(0xa6484,'AT'),(0xa64c4,'DF'),(0xa64e4,'DF')):
        bind(at,en,font_metrics=[18,18,16,18,18])
    # The change-form pane draws its pilot summary independently of the list.
    bind(0x9ed84,'Foc');bind(0xa2684,'Foc')
    return dict(schema=1,version='0.5.18',source_member_sha256=sha256(s),edits=list(edits.values()),
        tiny_cells=TINY,reference=['SRW Z3/tools/digraph.py','SRW Z3/tools/battle_preview_layout.py',
        'SRW Z3/tools/map_popup_layout.py','SRW Z3/translation/ui_hook.json','SRW Z3/translation/terrain_all_hook.json'],
        terrain=dict(archive=MAP_ARCHIVE,member=MAP_MEMBER,member_sha256=MAP_SHA,offset=0x84,en='Debris Field'),
        viewport=dict(width=1280,height=720),runtime_verified=False)


def hook_entries(elf,mapping):
    if sha256(elf)!=vwf.ELF_SHA256:raise ValueError('Battle hook baseline changed')
    out=[]
    for jp,en in HOOKS.items():
        if jp.encode('utf8')+b'\0' not in elf:raise ValueError('Battle executable label source missing')
        out.append(dict(id='battle:'+jp,key=ui_hook.utf8_key(jp.encode('utf8'),elf),english=eboot_text.encode(en,mapping)))
    out.append(terrain_entry(mapping))
    return out


def native_patch(elf,original,mapping):
    if sha256(original)!=vwf.ELF_SHA256:raise ValueError('Flag converter baseline changed')
    out=bytearray(elf);ranges=[]
    for token in TINY:
        at=ui_hook.UTAB_VA-0x10000+0x100+ord(token)*2
        if original[at:at+2]!=bytes.fromhex('81a1') or elf[at:at+2]!=bytes.fromhex('81a1'):
            raise ValueError('Flag converter fallback changed')
        out[at:at+2]=bytes.fromhex(mapping[token]);ranges.append((at,at+2))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Flag converter isolation failure')
    return bytes(out),dict(converter_private_cells=len(TINY),modified_file_ranges=ranges,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),repr(e['en']),e.get('font_metrics'))
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
