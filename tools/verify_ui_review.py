"""Execute the final native fallback and read back the five reviewed screens."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import ui_hook as H,ppc_exec as P,eboot_text as E,library_build as L
from tools import ui_catalog as U,settings_layout as S,endless_narration as N,ui_review_fixes as R
from tools.ui_description_layout import advance

SHOTS=(('level-up','7a05cbc9-2cf4-4fd0-bd83-c8fc4b1e2af9'),
       ('concluding-narration','c24de3eb-2f6a-40f5-91bf-af7bb9f27a1f'),
       ('intermission-footer','15b5f467-1052-4e1e-9beb-8002d66b1761'),
       ('rengoku-link','5bb9fa24-e554-41fa-a5c3-e6cab433dc24'),
       ('settings','f973c433-1cf3-4616-8afa-a2947fe71c8c'))


def native_cases(elf):
    """Execute the shipped helper and original CP932 draw tail, including misses."""
    mem=P.Memory();phs=H._headers(elf)[2]
    for seg in phs[:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=seg==phs[1])
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000))
    mem.map(0x42000000,bytes(0x100))
    mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000))
    out=[]
    for text in ('ＯＮ','ＯＦＦ','　','未知'):
        for mode in (0,1):
            raw=text.encode('cp932');mem.write(0x42000000,raw+b'\0')
            mem.write(0x41000000,bytes(0x2000))
            for offset in (0x54,0x5c):mem.write(0x41000000+offset,struct.pack('>f',28))
            mem.write(0x410000ac,struct.pack('>H',mode))
            m=P.Machine(mem);m.r=[0x770000+i for i in range(32)]
            m.r[1]=0x40003f00;m.r[2]=H.TOC;m.r[3]=0x42000000;m.r[7]=1;m.r[8]=0
            m.f[1]=639.5;m.f[2]=361.;m.f[3]=1.;m.lr=0x152000
            before=(m.r[1],m.r[2],m.r[27:32],m.lr)
            def strlen(vm):
                n=0
                while mem.read(vm.r[3]+n,1)!=b'\0':
                    n+=1
                    if n>4096:raise ValueError('Native count walked outside the source caption')
                vm.r[3]=n;vm.pc=vm.lr
            def alternate(vm):
                # This formatter's encoding/source arguments are the contract;
                # replay its known half-cell geometry after checking them.
                if vm.r[3:6]!=[0x42000000,0,1]:raise ValueError('Alternate native caption arguments changed')
                vm.r[3]=-len(text)*14 & P.M64;vm.pc=vm.lr
            m.hooks[H.STRLEN]=strlen;m.hooks[0x13d5c]=alternate
            m.pc=0x149bc;m.run({0x14158},limit=50000)
            if m.r[3]!=0x42000000 or m.r[7]!=1 or mem.read(m.r[3],len(raw)+1)!=raw+b'\0':
                raise ValueError('Native fallback draws code bytes instead of the source caption')
            if m.f[1]!=639.5-len(text)*14 or (m.f[2],m.f[3])!=(361.,1.):
                raise ValueError('Native fallback geometry differs')
            if (m.r[1],m.r[2],m.r[27:32],m.lr)!=before:raise ValueError('Native fallback lost caller state')
            out.append(dict(text=text,mode=mode,drawer_pointer=m.r[3],left=m.f[1],steps=m.steps))
    return out


def verify(version):
    from tools.verify_focus_style import verify as previous
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    from tools.cpk import CPK
    from tools import battle_layout,ui_layout_text,rpw_text
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2])
    h=build['executable']['ui_hook'];runner=H._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    if R.plan():raise ValueError('Review wording remains stale')
    if json.loads(S.DEST.read_text(encoding='utf8'))!=S.plan():raise ValueError('Settings layout remains stale')
    if json.loads(N.DEST.read_text(encoding='utf8'))!=N.plan():raise ValueError('Concluding narration remains stale')
    source=battle_layout.source()
    settings=config(ROOT/'config/tengoku.json');original=member(verified_source(settings,ARCHIVE),27)
    with CPK(folder/'AIDDATAPACK.CPK')as arc:
        by_id={e['id']:e for e in arc.files};fssa=arc.read(by_id[0]);narration=arc.read(by_id[27])
    if narration!=original:raise ValueError('Concluding narration rows or timing changed')
    grow=len(fssa)-len(source)
    widgets={at-grow:r for r in U.fssa_strings(fssa,decode=lambda raw:L.decode(raw,mapping))for at in r['widget_offsets']}
    for edit in S.plan()['edits']:
        if widgets[edit['widget_offset']]['text']!=edit['en']:raise ValueError('ON/OFF final widget differs')
    captions=[];settings_captions=[]
    translated=U.translations()
    original_widgets={at:r for r in U.fssa_strings(source)for at in r['widget_offsets']}
    for at in (0x94504,0x945a4,0x94604,0x946a4):
        row=original_widgets[at];en=translated[sha256(row['text'].encode('utf8'))[:20]]['en']
        expected=E.encode(en,mapping);pointer,_=runner.run(row['raw']+b'\0')
        if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final volume caption differs')
        first=en.split('\n')[0];edge=191.5+sum(map(advance,first))*28/32
        if first!='・Voice Vol.' or edge>413.5-28-8:raise ValueError('Voice caption reaches controller icon')
        settings_captions.append(dict(widget=at,en=en,voice_right_edge=edge,icon_reserved_from=385.5))
    for row,en in zip(N.sources(original),N.ENGLISH):
        expected=E.encode(en,mapping);pointer,_=runner.run(row['raw']+b'\0')
        if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final concluding narration draw differs')
        units=sum(map(advance,en))
        if units>900:raise ValueError('Concluding narration exceeds panel')
        captions.append(dict(id=row['id'],en=en,units=units,limit=900))
    for at,en in ((0x99f04,'DEF\nSKL'),(0x99f24,'EVD\nHIT')):
        if widgets[at]['text']!=en or fssa[at+grow+19]!=28:raise ValueError('Level-up labels are still undersized')
        if fssa[at+grow+21:at+grow+32]!=source[at+21:at+32]:raise ValueError('Level-up line pitch or state changed')
    cqbk=H.utf8_key('格闘'.encode('utf8'),H.PREPARED.read_bytes());expected=E.encode('CQB',mapping)
    pointer,_=runner.run(cqbk+b'\0')
    if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Dynamic CQB label differs')
    levels=[]
    with CPK(folder/'RPW_DATA.CPK')as arc:built_rpw=arc.read(arc.files[0])
    _,built_pool=rpw_text.pool_of(built_rpw)
    built_chunks={c['name']:c for c in rpw_text.rpw_chunks(built_rpw)}
    starts={0}|{i+1 for i,b in enumerate(built_pool)if b==0 and i+1<len(built_pool)}
    for row in rpw_text.slots(rpw_text.load_rpw()):
        if row['chunk']=='sk-pri' and '気力' in row['jp']:
            # Final allocated font cells are not all standard CP932 codes.
            # Follow the verified name-column pointer and use the build decoder.
            stride=rpw_text.SCHEMA[row['chunk']][0]
            at=built_chunks[row['chunk']]['body_offset']+(row['record']*stride+row['col'])*4
            pointer=struct.unpack_from('<I',built_rpw,at)[0]
            if pointer not in starts:raise ValueError('Final Focus skill pointer is not a string start')
            label=L.decode(built_pool[pointer:built_pool.index(0,pointer)],mapping)
            if 'Morale' in label or ('気力＋（回避）'==row['jp'] and label!='Foc+ Evade'):
                raise ValueError('Final Focus skill label is stale')
            levels.append(dict(id=row['id'],en=label))
    shots=[]
    from PIL import Image
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src=dest
        with Image.open(src)as im:size=list(im.size)
        shots.append(dict(issue=label,source=str(src),saved_path=str(dest),sha256=sha256_file(src),pixel_size=size))
    return dict(schema=1,version=version,native_fallback=native_cases(elf),
        concluding_narration=captions,narration_member_unchanged=True,levelup_focus_skills=levels,
        readable_stat_labels=['CQB','RNG','DEF','SKL','EVD','HIT'],settings_widgets=S.plan()['edits'],
        settings_captions=settings_captions,
        screenshots=shots,prior_verification=prior,iso_verification=prior['iso_verification'],runtime_verified=False,
        source_sha256={p:sha256_file(ROOT/p)for p in ('tools/link_layout.py','tools/ppc_exec.py',
            'tools/endless_narration.py','tools/intermission_layout.py','tools/status_layout.py',
            'tools/settings_layout.py','tools/ui_review_fixes.py','tools/verify_ui_review.py',
            'tests/test_link_layout.py','tests/test_ui_review.py')})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.15')
    ap.add_argument('--apply',action='store_true');args=ap.parse_args();data=verify(args.version)
    print('Native fallback cases:',len(data['native_fallback']))
    print('Narration:',data['concluding_narration']);print('Final Focus skills:',len(data['levelup_focus_skills']))
    print('ISO:',data['iso_verification'])
    if args.apply:
        for s in data['screenshots']:
            dest=Path(s['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists()and sha256_file(dest)!=s['sha256']:raise ValueError('Screenshot collision')
            if Path(s['source'])!=dest:shutil.copyfile(s['source'],dest)
        write_json(ROOT/'work/ui'/('ui_review_'+args.version+'.json'),data)
    else:print('DRY RUN: no screenshots or evidence written.')


if __name__=='__main__':main()
