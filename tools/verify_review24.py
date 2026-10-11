"""Read final Clear Reports and label geometry, carrying prior verification."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review24_layout as L,review24_report as R,battle_layout as B,ui_catalog as U
from tools import ui_hook as H,eboot_text as E,menu_layout as F,library_build as Q
from tools.cpk import CPK

SHOTS=(('clear-report','cb29cdd9-e56f-4237-bd74-81752c17f518'),
       ('upgrade-list','4683313d-1a8e-4022-bfb4-fb02691d838b'),
       ('deployment-menu','021623f3-66a9-4328-a126-089c9995a2b3'))

def verify(version):
    from tools.verify_review23 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    elf=(folder/'EBOOT.BIN').read_bytes();original=H.PREPARED.read_bytes();read=H._reader(elf,H._headers(elf)[2])
    planned=R.plan(original,mapping);values=build['executable']['ui_hook']['table']['payload_vas']
    for pointer in planned['pointers']:
        payload=dict(planned['payloads'])[pointer['id']];va=values[pointer['id']]
        if read(pointer['va'],4)!=struct.pack('>I',va)or read(va,len(payload))!=payload:
            raise ValueError('Final Clear Report TOC/payload differs')
    for va in R.PADDING:
        if read(va,4)!=struct.pack('>I',0x38c00000):raise ValueError('Final report amount padding differs')
    cases=[]
    for n in (0,5,220,999999,2147483647):
        number=str(n).translate(str.maketrans('0123456789','０１２３４５６７８９')).encode('cp932')
        for kind,prefix in [('chips','Z Chips: '),('funds','Funds: ')]:
            raw,steps=R.resource(elf,kind,n)
            if raw!=E.encode(prefix,mapping)+number:raise ValueError('Final report changes resource value')
            cases.append(dict(kind=kind,value=n,bytes=len(raw),steps=steps,canary_verified=True))
        for peerless,header in [(False,'President skill bonus:'),(True,'Z-Crystal "Road to Peerlessness":')]:
            rows,steps=R.president(elf,n,peerless)
            wanted=[E.encode(header,mapping),E.encode('Each deployed pilot received',mapping),
                    number+E.encode(' PP.',mapping)]
            if rows!=wanted:raise ValueError('Final PP report wording/value differs')
            cases.append(dict(kind='peerlessness'if peerless else'president',value=n,line_bytes=list(map(len,rows)),steps=steps,canary_verified=True))
    layout=L.plan()
    if json.loads(L.DEST.read_text(encoding='utf8'))!=layout:raise ValueError('Review 24 plan is stale')
    source=B.source()
    with CPK(folder/'AIDDATAPACK.CPK')as c:final=c.read(next(e for e in c.files if e['id']==0))
    grow=len(final)-len(source);widgets={a:r for r in U.fssa_strings(final,decode=lambda raw:Q.decode(raw,mapping))for a in r['widget_offsets']}
    for e in layout['edits']:
        at=e['widget_offset'];target=at+grow
        if widgets[target]['raw']!=F.encode(e,mapping):raise ValueError('Final Review 24 caption differs')
        if final[target+8:target+32]!=source[at+8:at+32]:raise ValueError('Report/menu colors, state, pitch or size changed')
        expected=struct.pack('>f',e['x'])if 'x'in e else source[at+4:at+8]
        if final[target+4:target+8]!=expected:raise ValueError('Final Review 24 caption origin differs')
    info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    grouped,rows=U.checked();commands=[]
    from tools.review24_text import CHANGES
    from tools.review19_layout import width
    for rid,text in CHANGES['help'].items():
        if rows[rid]['en']!=text or 43.5+width(text,31)+6>278:raise ValueError('Deployment command spills beyond button')
        for occurrence in grouped[rid]:
            raw=occurrence['raw'];key=raw if occurrence['encoding']=='cp932'else H.utf8_key(raw,original)
            want=E.encode(text,mapping,utf8_source=occurrence['encoding']=='utf-8')
            pointer,steps=runner.run(key+b'\0')
            if read(pointer,len(want)+1)!=want+b'\0':raise ValueError('Final deployment command lookup differs')
            commands.append(dict(source=occurrence['id'],text=text,width=width(text,31),steps=steps))
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review24-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        layout=layout,native_clear_report_cases=cases,command_lookup_cases=commands,
        screenshots=shots,runtime_verified=False,proofreading=dict(reviewer='review24_wording',meaning_groups=5,meaning_changes=0))

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result=verify(a.version)
    print('Clear Report execution cases:',len(result['native_clear_report_cases']))
    print('Layout widgets:',len(result['layout']['edits']),'Command lookups:',len(result['command_lookup_cases']))
    print('ISO:',result['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no verification evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review24_verified_'+a.version+'.json'),result)

if __name__=='__main__':main()
