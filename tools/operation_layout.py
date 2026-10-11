"""Assembled headings bound to the executable's actual stage records."""
import struct
from tools import eboot_text, ui_hook, library_build


def episodes(elf):
    """Read the 52-byte stage records used by 0x1dcb4c/0x1dd010.

    Tengoku's stage IDs start at 2001. The title index at +24 selects the
    Tengoku table; +14 is the episode number, including branching routes.
    Do not infer episode numbers from the order of title-card textures.
    """
    read=ui_hook._reader(elf,ui_hook._headers(elf)[2])
    base=struct.unpack('>I',read(ui_hook.TOC-0x41d8,4))[0]
    if base!=0xa1f984:raise ValueError('Stage record table moved')
    result={}
    for n in range(375):
        record=read(base+n*52,52)
        name=read(struct.unpack_from('>I',record,4)[0],24).split(b'\0')[0].decode('ascii')
        if not name.startswith('2'):continue
        number=struct.unpack_from('>h',record,14)[0]
        index=struct.unpack_from('>H',record,24)[0]
        if not 1<=number<=99 or index==65535:continue
        pointer=struct.unpack('>I',read(0xa1f6ec+index*4,4))[0]
        title=read(pointer,256).split(b'\0')[0].decode('utf8')
        result.setdefault((number,title),[]).append(n)
    if (1,'新地球皇国') not in result:raise ValueError('Episode-one stage binding changed')
    return result


def hook_entries(elf,mapping):
    read=ui_hook._reader(elf,ui_hook._headers(elf)[2])
    for va,jp in ((0x9f14f8,'プロローグ'),(0x9f14e0,'第'),(0x9f14e8,'話'),
                  (0x9f1548,'『'),(0x9f1550,'』')):
        if read(va,len(jp.encode('cp932'))+1)!=jp.encode('cp932')+b'\0':
            raise ValueError('Operation heading fragment changed')
    translations=eboot_text.load()['strings']
    titles=[r for r in eboot_text.records() if r['family']=='stage_titles' and
            r['encoding']=='utf-8' and 0x89e828<=int(r['va'],16)<=0x89e850]
    if len(titles)!=2: raise ValueError('Prologue heading source order changed')
    out=[]
    for (n,jp),records in episodes(elf).items():
        en=eboot_text.unshow(library_build.expand(translations[jp]['en'],eboot_text.resolver()))
        wide=str(n).translate(str.maketrans('0123456789','０１２３４５６７８９'))
        for gap in ('',' ','　'):
            for lead in ('','　'):
                text=lead+'第'+wide+'話'+gap+'『'+jp+'』'
                out.append(dict(id='operation:episode:%d:%d'%(records[0],len(out)),
                    key=ui_hook.utf8_key(text.encode('utf8'),elf),
                    english=eboot_text.encode('Episode %d: %s'%(n,en),mapping)))
    for n,row in enumerate(titles,1):
        english='Prologue %d: %s'%(n,translations[row['jp']]['en'])
        # The chart/intermission composers insert a separating space before
        # the quotation; the objectives composer omits it. Match full results.
        for digit in (chr(0xff10+n),):
            for gap in ('',' ','　'):
                for lead in ('','　'):
                    text=lead+'プロローグ第'+digit+'話'+gap+'『'+row['jp']+'』'
                    out.append(dict(id='operation:prologue:%d:%d'%(n,len(out)),key=ui_hook.utf8_key(text.encode('utf8'),elf),
                                    english=eboot_text.encode(english,mapping)))
        # Some chart states draw the quoted title independently.
        out.append(dict(id='operation:quoted-prologue:%d'%n,key=('『'+row['jp']+'』').encode('cp932'),
                        english=eboot_text.encode(translations[row['jp']]['en'],mapping)))
    for row in eboot_text.records():
        if row['family']!='stage_titles' or row['jp'] not in translations:continue
        text=row['jp'];en=translations[text]['en']
        if not en or eboot_text.FORMAT.search(text):continue
        out.append(dict(id='operation:chart-title:'+row['va'],key=('『'+text+'』').encode('cp932'),
                        english=eboot_text.encode(eboot_text.unshow(library_build.expand(en,eboot_text.resolver())),mapping)))
    for n in range(1,100):
        wide=str(n).translate(str.maketrans('0123456789','０１２３４５６７８９'))
        out.append(dict(id='operation:chart-number:%d'%n,key=('第'+wide+'話').encode('cp932'),
                        english=eboot_text.encode('Episode %d'%n,mapping)))
    return list({e['key']:e for e in out}.values())
