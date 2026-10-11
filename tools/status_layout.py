"""Source-bound save/status repairs, using Z3's one-cell terrain/stat labels.

Native terrain pitch and rating columns survive. Movement tables contain
UTF-8, unlike Jigoku's CP932 tables; only unused private Unicode mappings
and the independently verified Tengoku movement slots are changed.
"""
import argparse
import json
import struct
from tools.common import ROOT,sha256,write_json
from tools import ui_catalog,ui_hook,eboot_text,vwf
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/status_layout.json'
TINY={chr(0xe000+i):word for i,word in enumerate(('Air','Grd','Wtr','Spc','Und'))}
TINY.update({chr(0xe017+i):word for i,word in enumerate(('Only','CQB','RNG','SKL','DEF','EVD','HIT'))})
CELL={word:token for token,word in TINY.items()}
TERRAIN=dict(zip('空陸海宇水地',(CELL[w] for w in ('Air','Grd','Wtr','Spc','Wtr','Und'))))
STATS=dict(zip(('格闘','射撃','技量','防御','回避','命中'),
               (CELL[w] for w in ('CQB','RNG','SKL','DEF','EVD','HIT'))))
SAVE=(('ここまでのマップ上の進行状況をセーブします。','Save your current map progress.'),
      ('新規作成してよろしいですか？','Create a new save?'))
DATE=('新多元世紀０００１年　１１月１２日','New Multidimensional Century 0001 - November 12')
CAPTIONS=SAVE
MARKERS={jp:'@save-center:%d'%n for n,(jp,en) in enumerate(CAPTIONS)}
MOVEMENT=(0x8da518,0x8da778)
SPECIAL=((0x8da4e8,'空専用',CELL['Air']+CELL['Only']),
         (0x8da4f8,'空水専用',CELL['Air']+CELL['Wtr']+CELL['Only']),
         (0x8da508,'水専用',CELL['Wtr']+CELL['Only']))


def raster_tiny(text,face):
    """Readable compact profile: cap 16, baseline 23, 0.3px dilation.

    Cropped letters get a one-pixel gap and at most 28 pixels of ink. The
    32-unit advance deliberately retains the caller's native cell pitch.
    """
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
    natural=sum(p.width for p,y in parts); gaps=len(parts)-1
    budget=min(natural,28-gaps); out=Image.new('L',(32,32))
    total=last=0;x=(32-budget-gaps)//2
    for ink,y in parts:
        total+=ink.width;edge=round(total*budget/natural);width=edge-last;last=edge
        out.paste(ink.resize((width,ink.height),Image.Resampling.BOX),(x,y));x+=width+1
    return out,32


def plan():
    from tools.ui_coverage import member
    from tools.pipeline import config,verified_source
    from tools.aid_art import ARCHIVE
    source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))
    rows=ui_catalog.fssa_strings(source)
    widgets={at:r for r in rows for at in r['widget_offsets']};edits={}
    def bind(at,en=None,note='Fit the native label slot; retain numeric/rating coordinates.',**changes):
        row=widgets[at]
        edit=dict(widget_offset=at,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            source_xy=list(struct.unpack_from('>ff',source,at+4)),notes=note,**changes)
        if en is not None:edit['en']=en
        edits[at]=edit
    # Four terrain labels must remain four cells, with their original pitch.
    for at,row in widgets.items():
        text=row['text']
        if text.replace('\n','') in ('空陸海宇','空陸水地','空陸－地','空陸―地'):
            bind(at,''.join(TERRAIN.get(c,c) for c in text),note='Z3 compact terrain cells; keep separators, line breaks, pitch and rating slots.')
        if text in STATS:bind(at,STATS[text])
        elif text in ('格闘\n射撃','技量\n防御','防御\n技量','回避\n命中'):
            bind(at,'\n'.join(STATS[c] for c in text.split('\n')))
    # Level-up has room for ordinary three-letter labels. Terrain/training
    # one-cell badges were visibly undersized here; leave those other uses.
    for at,en in ((0x99f04,'DEF\nSKL'),(0x99f24,'EVD\nHIT')):
        bind(at,en,font_metrics=[27,28,26,28,28],
             note='Readable normal Z3 letters in the level-up label column; preserve line pitch and live values.')
    # The level-up panel reverses DEF/SKL and reuses the score suffix.
    if widgets[0x8f044]['text']!='機':raise ValueError('Shared score suffix changed')
    bind(0x8f044,'',note='Remove Units from the shared Score display; preserve the live kill count.')
    for at in (0x9d5c4,0x9d704,0x9dd64):
        if widgets[at]['text']!='気力':raise ValueError('Morale source changed')
        bind(at,'Foc')
    labels={0x9d624:'Move\nArmor\nMob.\nHit',0x9de24:'Move\nArmor\nMob.\nHit',
        0x9d884:'HP\nEN\nArmor\nMob.\nHit',0x9d924:'\n\n\nMove\nType',
        0x9d8a4:'Name',0x9db64:'Name',0x9d9a4:'Type',0x9d9c4:'Attr.',
        0x9d9e4:'Power',0x9da04:'Range',0x9da24:'Hit',0x9da44:'CR',0x9da64:'T',
        0x9da84:'\n\nFoc Req.\nSkill Req.\nTerrain\n',0x9daa4:'Effects',
        0x9dac4:'Cat:',0x9dae4:'Type:',0x9db04:'IFF:',0x9db24:'Form:',0x9db44:'Attr:'}
    for at,en in labels.items():bind(at,en)
    bind(0x8f864,'Eff.',note='Compact Spirit effect caption, clearing the unchanged description start.')
    # The source font draws CR and T separately; retaining both fields avoids
    # duplicate CRT text. Pull Hit away from that split heading.
    bind(0x9da24,'Hit',x=(939.5-640)/640)
    # Grey combined row is left-anchored; colored choices use both centered
    # and left-anchored native states. Preserve their raw Yes/No counts.
    width=lambda s:sum(map(advance,s))*25/32
    left=639.5-width('Yes / No')/2;no_left=left+width('Yes / ')
    for at in (0x993a4,0x993e4,0x99424):bind(at,'Yes / No',x=(left-640)/640)
    for at,x in ((0x99384,left+25),(0x993c4,no_left+37.5),(0x99404,left),(0x99444,no_left)):
        bind(at,x=(x-640)/640,note='Align the selected native Yes/No word with the centered grey row, preserving selection flags.')
    return dict(schema=1,version='0.5.15',source_member_sha256=sha256(source),
        edits=list(edits.values()),tiny_cells=TINY,
        reference='SRW Z3/tools/digraph.py (TINY_CELLS, raster_tiny)',
        save_questions=[dict(jp=jp,en=en,native_cells=len(jp),marker=MARKERS[jp]) for jp,en in SAVE],
        viewport=dict(width=1280,height=720),runtime_verified=False)


def merge(edits,fixes):
    by_widget={e['widget_offset']:e for e in edits}
    for edit in fixes:by_widget[edit['widget_offset']]=edit
    return list(by_widget.values())


def hook_entries(elf,mapping):
    if sha256(elf)!=vwf.ELF_SHA256:raise ValueError('Status hook baseline changed')
    out=[]
    for jp,en in CAPTIONS:
        if jp.encode('utf8') not in elf:raise ValueError('Save line source missing')
        out.append(dict(id='status:save:'+MARKERS[jp],key=ui_hook.utf8_key(jp.encode('utf8'),elf),
            english=bytes.fromhex(mapping[MARKERS[jp]])+eboot_text.encode(en,mapping)))
    # The native full-name join consumes translated RPW pieces. Supply a
    # display-only spaced name; do not alter columns, order flags or saves.
    from tools import rpw_text
    names=rpw_text.load_names();slots=rpw_text.slots(rpw_text.load_rpw());by_record={}
    for slot in slots:
        if slot['chunk']=='pilot-nw':by_record.setdefault(slot['record'],{})[slot['col']]=slot
    joins={}
    for rid,columns in by_record.items():
        family,given=[rpw_text.text_for(columns[c],names) for c in (1,2)]
        if not family or not given or given in ('-','???') or family in ('-','???'):continue
        if family==given:continue
        for variant,(text,en) in enumerate(((family+given,family+' '+given),(given+family,given+' '+family),
                        (given+'・'+family,given+' '+family),(family+'・'+given,family+' '+given))):
            key=eboot_text.encode(text,mapping);value=eboot_text.encode(en,mapping)
            if key in joins and joins[key]['english']!=value:raise ValueError('Ambiguous pilot full-name join')
            joins[key]=dict(id='status:pilot-name:%d:%d'%(rid,variant),key=key,english=value)
    out.extend(joins.values())
    return out


def native_patch(elf,original,mapping):
    if sha256(original)!=vwf.ELF_SHA256:raise ValueError('Movement baseline changed')
    out=bytearray(elf);ranges=[]
    for token in TINY:
        at=ui_hook.UTAB_VA-0x10000+0x100+ord(token)*2
        # Tengoku maps unsupported private Unicode to its replacement square.
        if original[at:at+2]!=bytes.fromhex('81a1') or elf[at:at+2]!=bytes.fromhex('81a1'):
            raise ValueError('Private Unicode converter fallback changed')
        out[at:at+2]=bytes.fromhex(mapping[token]);ranges.append((at,at+2))
    for va in MOVEMENT:
        for n,jp in enumerate('空陸水地'):
            at=va-0x10000+n*8;raw=jp.encode('utf8')+bytes(5)
            if elf[at:at+8]!=raw:raise ValueError('Movement slot source drift')
            out[at:at+8]=TERRAIN[jp].encode('utf8')+bytes(5);ranges.append((at,at+8))
    for va,jp,en in SPECIAL:
        at=va-0x10000;raw=jp.encode('utf8')+b'\0'
        if elf[at:at+len(raw)]!=raw:raise ValueError('Restricted movement source drift')
        new=en.encode('utf8')+b'\0'
        if len(new)>len(raw):raise ValueError('Restricted movement exceeds original slot')
        out[at:at+len(raw)]=new+bytes(len(raw)-len(new));ranges.append((at,at+len(raw)))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Movement patch isolation failure')
    return bytes(out),dict(modified_file_ranges=ranges,movement_tables=list(MOVEMENT),
        converter_private_cells=len(TINY),restricted_movement_strings=len(SPECIAL),runtime_verified=False)


def save_specs(mapping):
    return [dict(code=int(mapping[MARKERS[jp]],16),
        delta_cells=len(jp)/2-sum(map(advance,en))/64) for jp,en in CAPTIONS]


def save_origin(va,state,specs):
    """Adjust only marked split captions before capturing the drawer origin."""
    from tools.link_layout import Asm
    a=Asm(va);a.d(0xf8000001,1,1,-0x60)
    for r,off in ((0,0x10),(9,0x18)):a.d(0xf8000000,r,1,off)
    a.e(0x7c000026);a.d(0x90000000,0,1,0x20)
    for f,off in ((10,0x28),(11,0x30)):a.d(0xd8000000,f,1,off)
    a.d(0x88000000,9,31,0);a.d(0x2c000000,0,9,0);a.br(0x41820000,'done')
    a.d(0xa0000000,9,31,0)
    for n,spec in enumerate(specs):
        a.d(0x28000000,0,9,spec['code']);a.br(0x40820000,'next%d'%n)
        bits=struct.unpack('>I',struct.pack('>f',spec['delta_cells']))[0]
        a.ptr(9,bits);a.d(0x90000000,9,1,0x38);a.d(0xc0000000,10,1,0x38)
        a.d(0xc0000000,11,30,0x54);a.e(0xec000032|10<<21|10<<16|11<<6)
        a.x(0xec00002a,31,31,10);a.d(0x38000000,31,31,2);a.br(0x48000000,'done')
        a.label('next%d'%n)
    a.label('done');a.ptr(9,state);a.d(0xd0000000,31,9,1024)
    for f,off in ((10,0x28),(11,0x30)):a.d(0xc8000000,f,1,off)
    a.d(0x80000000,0,1,0x20);a.e(0x7c0ff120)
    for r,off in ((0,0x10),(9,0x18)):a.d(0xe8000000,r,1,off)
    a.d(0x38000000,1,1,0x60);a.e(0xd3fe004c);a.jump(0x141ac)
    return a.code()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=plan();print('Status widgets:',len(data['edits']),'Compact cells:',data['tiny_cells'])
    print('Save lines:',data['save_questions'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no translation/layout data written.')

if __name__=='__main__':main()
