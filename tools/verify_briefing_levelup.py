"""Verify the final date drawer, three briefing captions and level-up labels."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT,sha256_file,sha256,write_json
from tools import briefing_narration as B,fleet_narration as F,status_layout as S,ui_hook as H
from tools import ui_catalog,eboot_text,ppc_exec as P
from tools.ui_description_layout import advance,condensed_advance

DATE_CALL=0x1541c8
SHOTS=(('date','2d2e0376-cebe-4101-8943-6448ecec96d6'),
       ('briefing','9f73a3bf-2a69-47ec-84cf-a4d4a6bc8711'),
       ('level-up','0c2d32a5-13f8-4593-9fd3-345d98f47484'),
       ('fleet-narration','55dc9cd3-2cdc-4f23-977a-90d48486f29a'))


def date_cases(elf,build):
    """Enter the real native centered drawer, then its installed VWF helper."""
    source=H.PREPARED.read_bytes();phs=H._headers(elf)[2];read=H._reader(elf,phs)
    if read(DATE_CALL,4)!=struct.pack('>I',H.branch(DATE_CALL,0x149bc)|1):
        raise ValueError('Native date caller changed')
    # Target caller, independently located: size 40, CP932, x=640, y=360.
    lo,hi=0x15418c,0x1541f4
    if read(lo,hi-lo)!=source[lo-0x10000:hi-0x10000]:raise ValueError('Date geometry or caller changed')
    for offset,value in ((-0x56d4,640.),(-0x56d0,360.),(-0x56cc,1.)):
        if read(H.TOC+offset,4)!=struct.pack('>f',value):raise ValueError('Date origin changed')
    key=H.utf8_key(S.DATE[0].encode('utf8'),source)
    mapping=build['mapping'];expected=eboot_text.encode(S.DATE[1],mapping)
    h=build['executable']['ui_hook'];runner=H._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    pointer,_=runner.run(key+b'\0')
    if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final date translation differs')
    units=sum(map(advance,S.DATE[1]));out=[]
    for quad in (30,40):
        for mode in (0,1):
            mem=P.Memory()
            for seg in phs[:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=seg==phs[1])
            mem.map(0x40000000,bytes(0x3000));mem.map(0x41000000,bytes(0x1000))
            mem.map(0x42000000,key+b'\0',writable=False)
            mem.write(H.TOC-0x7f3c,struct.pack('>I',0x41000000))
            mem.write(0x41000054,struct.pack('>f',quad));mem.write(0x410000ac,struct.pack('>H',mode))
            m=P.Machine(mem);m.r[1]=0x40001800;m.r[2]=H.TOC;m.r[3]=0x42000000
            m.r[7]=1;m.r[8]=0;m.f[1]=640.;m.f[2]=360.;m.f[3]=1.;m.lr=DATE_CALL+4
            m.pc=0x149bc;m.run({0x14a68,0x14a2c,0x14ac4},limit=30000)
            width=units*quad/32
            if m.pc!=0x14a68 or abs(m.f[1]+width/2-640.)>.0001:
                raise ValueError('Final English date does not center')
            if m.f[30]!=360. or m.f[31]!=1. or m.r[31]!=0x42000000:
                raise ValueError('Date vertical position, style or source pointer changed')
            if m.f[1]<0 or m.f[1]+width>1280:raise ValueError('Date exceeds the viewport')
            out.append(dict(quad=quad,mode=mode,left=m.f[1],width=width,center=640.,y=360.,steps=m.steps))
    return out


def verify(version):
    from tools.verify_intermission_library import verify as previous_verify
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    from tools.cpk import CPK
    prior=previous_verify(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    elf=(folder/'EBOOT.BIN').read_bytes();source=H.PREPARED.read_bytes()
    read=H._reader(elf,H._headers(elf)[2]);mapping=build['mapping']
    h=build['executable']['ui_hook'];runner=H._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    original=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),B.MEMBER)
    with CPK(folder/'AIDDATAPACK.CPK')as archive:
        built=archive.read(next(e for e in archive.files if e['id']==B.MEMBER))
    if built!=original:raise ValueError('Briefing rows or timing changed')
    if json.loads(B.DEST.read_text(encoding='utf8'))!=B.plan():raise ValueError('Briefing translation plan is stale')
    fleet_source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),F.MEMBER)
    with CPK(folder/'AIDDATAPACK.CPK')as archive:
        fleet_built=archive.read(next(e for e in archive.files if e['id']==F.MEMBER))
    if fleet_built!=fleet_source:raise ValueError('Fleet narration rows or timing changed')
    if json.loads(F.DEST.read_text(encoding='utf8'))!=F.plan():raise ValueError('Fleet translation plan is stale')
    grouped,translated=ui_catalog.checked();entries,_=ui_catalog.hook_entries(source,mapping,[])
    by_key={e['key']:e for e in entries};rows=[]
    for row in B.sources(original)+F.sources(fleet_source):
        rid=sha256(row['text'].encode('utf8'))[:20];en=translated[rid]['en']
        text,condensed=B.opening_narration.profile(en);active=dict(mapping)
        if condensed:
            from tools.dialogue_layout import PREFIX
            active.update({t[len(PREFIX):]:code for t,code in mapping.items()if t.startswith(PREFIX)})
        expected=eboot_text.encode(text,active)
        if by_key[row['raw']]['english']!=expected:raise ValueError('Briefing dictionary encoding differs')
        pointer,_=runner.run(row['raw']+b'\0')
        if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final briefing execution differs')
        units=sum(map(condensed_advance if condensed else advance,en))
        rows.append(dict(id=row['id'],text=en,condensed=condensed,advance_units=units,limit=900))
    edits={e['widget_offset']:e for e in S.plan()['edits']}
    if edits[0x8f044]['en']!='':raise ValueError('Shared score suffix remains')
    if edits[0x99f04]['en']!='DEF\nSKL':
        raise ValueError('Level-up reversed stat pair differs')
    if edits[0x99f24]['en']!='EVD\nHIT':
        raise ValueError('Level-up evasion and accuracy differ')
    # Earlier verification reads back the merged FSSA, both font pages and
    # every compact glyph; numeric/rating records retain their original bytes.
    shots=[]
    from PIL import Image
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src=dest
        with Image.open(src)as im:size=list(im.size)
        shots.append(dict(issue=label,source=str(src),saved_path=str(dest),sha256=sha256_file(src),pixel_size=size,runtime_confirmation=False))
    return dict(schema=1,version=version,date_drawer=dict(caller=DATE_CALL,cases=date_cases(elf,build)),
        briefing=rows[:3],fleet_narration=rows[3:],fleet_source_unchanged=True,
        briefing_source_unchanged=True,level_up_labels=['CQB','RNG','DEF','SKL','EVD','HIT'],
        score_suffix='',screenshots=shots,prior_verification=prior,iso_verification=prior['iso_verification'],
        source_sha256={f:sha256_file(ROOT/f)for f in ('tools/briefing_narration.py','tools/fleet_narration.py','tools/status_layout.py',
            'tools/ui_catalog.py','tools/verify_briefing_levelup.py','tests/test_briefing_levelup.py',
            'work/translation/en/ui/expanded/briefing.json','work/translation/en/ui/expanded/fleet.json',
            'work/translation/en/ui/status_layout.json')},
        runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.13')
    ap.add_argument('--apply',action='store_true');args=ap.parse_args();data=verify(args.version)
    print('Date drawer:',data['date_drawer']);print('Briefing:',data['briefing'])
    print('Fleet narration:',data['fleet_narration'])
    print('Level-up labels:',data['level_up_labels'],'Score suffix:',repr(data['score_suffix']))
    if args.apply:
        for shot in data['screenshots']:
            dest=Path(shot['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists()and sha256_file(dest)!=shot['sha256']:raise ValueError('Screenshot collision')
            if Path(shot['source'])!=dest:shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('briefing_levelup_'+args.version+'.json'),data)
    else:print('DRY RUN: no screenshots or evidence written.')


if __name__=='__main__':main()
