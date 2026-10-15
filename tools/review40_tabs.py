"""Preload English for both Search tab states before native measurement."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/review40_tabs.json'
PAIRS={'Spirit':(0x96f24,0x97104),'Skills':(0x96f44,0x97124)}
ABILITIES=(0x96f64,0x97144)


def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']}
    edits=[];bounds=[]
    for en,pair in PAIRS.items():
        expected='精神コマンド' if en=='Spirit' else '特殊スキル'
        for at in pair:
            row=widgets[at]
            if row['text']!=expected or not source[at+23]&0x40:raise ValueError('Search tab source changed')
            x,y=struct.unpack_from('>ff',source,at+4);quad=source[at+19]
            width=sum(map(advance,en))*quad/32
            if width>200:raise ValueError('Search label exceeds its tab')
            edits.append(dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
                source_widget_sha256=sha256(source[at:at+32]),
                notes='English is present before native centering, like Abilities. Preserve all geometry, colors and selection fields.'))
            bounds.append(dict(widget_offset=at,en=en,center=640+x*640,y=360+y*360,
                               quad=quad,width=width,left=640+x*640-width/2,right=640+x*640+width/2))
    for at in ABILITIES:
        if widgets[at]['text']!='特殊能力':raise ValueError('Abilities reference changed')
    return dict(schema=1,version='0.5.40',edits=sorted(edits,key=lambda e:e['widget_offset']),
                bounds=bounds,abilities_unchanged=list(ABILITIES),runtime_verified=False)


def native_cases(elf,mapping,table_va,texts=None):
    """Run the installed caption renderer to its real glyph-drawer entry."""
    from tools import ppc_exec as P,ui_hook as H,eboot_text as E
    mem=P.Memory();phs=H._headers(elf)[2]
    for n,seg in enumerate(phs[:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=n==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000));mem.map(0x42000000,bytes(0x100))
    mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000));widths=mem.read(table_va,4480)
    source=B.source();specs=list(plan()['bounds'])
    for at in ABILITIES:
        x,y=struct.unpack_from('>ff',source,at+4)
        specs.append(dict(widget_offset=at,en='Abilities',center=640+x*640,y=360+y*360,quad=source[at+19]))
    cases=[]
    for row in specs:
        raw=texts[row['widget_offset']] if texts is not None else E.encode(row['en'],mapping)
        if raw!=E.encode(row['en'],mapping):raise ValueError('Native caption input is not compiled English')
        units=sum(widths[(a-0x81)*192+b-0x40]for a,b in zip(raw[::2],raw[1::2]))
        for mode in (0,1):
            mem.write(0x42000000,raw+b'\0');mem.write(0x41000000,bytes(0x2000))
            for at in (0x54,0x5c):mem.write(0x41000000+at,struct.pack('>f',row['quad']))
            mem.write(0x410000ac,struct.pack('>H',mode));m=P.Machine(mem)
            m.r=[0x770000+i for i in range(32)]
            m.r[1]=0x40003f00;m.r[2]=H.TOC;m.r[3]=0x42000000;m.r[7]=1;m.r[8]=0
            m.f[1]=row['center'];m.f[2]=row['y'];m.f[3]=1.;m.lr=0x152000
            before=(m.r[1],m.r[2],m.r[27:32],m.lr);m.pc=0x149bc;m.run({0x14158},limit=50000)
            width=units*row['quad']/32
            if abs(m.f[1]+width/2-row['center'])>.0001:raise ValueError('Native tab center differs')
            if mem.read(m.r[3],len(raw)+1)!=raw+b'\0' or m.r[7]!=1:raise ValueError('Native tab drawer receives different text')
            if (m.f[2],m.f[3])!=(row['y'],1.):raise ValueError('Native tab drawing state differs')
            if (m.r[1],m.r[2],m.r[27:32],m.lr)!=before:raise ValueError('Native tab renderer loses caller state')
            cases.append(dict(widget_offset=row['widget_offset'],en=row['en'],quad=row['quad'],mode=mode,
                              left=m.f[1],width=width,center=row['center'],native_steps=m.steps))
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();data=plan()
    for r in data['bounds']:print(hex(r['widget_offset']),r['en'],'center',r['center'],'quad',r['quad'],'width',r['width'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')


if __name__=='__main__':main()
