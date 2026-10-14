"""Read back skill questions, D-Trader/ship spacing and Earth Sphere fixes."""
import argparse,json,shutil,struct
from pathlib import Path
from functools import lru_cache
from tools.common import ROOT,sha256_file,write_json
from tools import review30_messages as Q,review30_oracle as O,review30_layout as A,review30_movement as M
from tools import ui_hook as H,library_build as L,eboot_text as E,ui_catalog as U,battle_layout as B
from tools.cpk import CPK
SHOTS=(('skill-question','36ad813a-3c01-4231-9a8d-af813e51e028'),('D-Trader-movement','2ead6410-3a6f-4d3f-9a43-7efa887dda84'),
       ('Earth-Sphere','01411132-18b5-4e2a-88a6-65a0965c549d'),('D-Trader-labels','75369e97-38a8-45fb-b75b-fda5a5caf68d'),
       ('battleship-deployment','19b2c8f2-bb3a-4789-80a7-5962681fcd9e'))

def verify(version):
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'))
    mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2])
    info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    entries=Q.hook_entries(H.PREPARED.read_bytes(),mapping)+M.hook_entries(elf,mapping);wanted={r['key']:r['english']for r in entries}
    for row in entries:
        pointer,_=runner.run(row['key']+b'\0')
        if read(pointer,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Skill/movement drawer lookup differs')
    native=[]
    for row in Q.source_rows(H.PREPARED.read_bytes()):
        for route in ('source','translated'):
            name=row['jp'].encode('cp932')if route=='source'else E.encode(row['en'],mapping)
            old='カウンター'.encode('cp932')if route=='source'else E.encode('Counter',mapping)
            forms=[(3,False,False,0,0),(2,False,False,0,0)]
            if row['flags']&2:forms += [(3,True,False,0,0),(1,True,False,8,0),(1,True,True,1,3)]
            for kind,leveled,multiple,current,innate in forms:
                lines,steps=O.skill(elf,name,old,kind,leveled,multiple,current,innate);english=[]
                for key in filter(None,lines):
                    expected=wanted[key];pointer,_=runner.run(key+b'\0')
                    if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Native learning composition untranslated')
                    english.append(L.decode(expected,mapping))
                native.append(dict(skill_record=row['record'],route=route,kind=kind,leveled=leveled,multiple=multiple,english=english,native_steps=steps))
    import itertools
    from tools import status_layout as S
    movement_native=[];table=H.unicode_table(elf)
    for flags in itertools.product((False,True),repeat=4):
        raw,steps=M.native_mask(elf,flags)
        expected=''.join(S.TERRAIN[c]if present else 'ー'for c,present in zip('空陸水地',flags))
        if raw!=expected.encode('utf8')or H.convert(raw,table)!=E.encode(expected,mapping):raise ValueError('Final native movement formatter differs')
        movement_native.append(dict(flags=list(flags),steps=steps,translated=True))
    source=B.source()
    with CPK(folder/'AIDDATAPACK.CPK')as arc:final=arc.read(next(r for r in arc.files if r['id']==0))
    grow=len(final)-len(source);widgets={at:r for r in U.fssa_strings(final,decode=lambda raw:L.decode(raw,mapping))for at in r['widget_offsets']}
    from tools.menu_layout import encode
    for row in A.plan()['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['raw']!=encode(row,mapping):raise ValueError('Final caption differs')
        expected=bytearray(source[at+4:at+32])
        if 'x'in row:struct.pack_into('>f',expected,0,row['x'])
        if final[target+4:target+32]!=expected:raise ValueError('Final caption changed unrelated fields')
    from tools import dialogue_build as D,dialogue as G,library_text as T
    from tools.ui_vwf_build import raster
    @lru_cache(None)
    def width(c):return raster(c)[1]if c in mapping else 32
    audit=json.loads((ROOT/'work/ui/review30_term_audit.json').read_text('utf8'));changed=[]
    rendered=D.plan(width);members={int(e['field'].split('/')[2].split(':')[0])for r in audit['changes']if '/dialogue/'in r['file']for e in r['edits']}
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        index={r['id']:r for r in arc.files}
        for mid in sorted(members):
            if arc.read(index[mid])!=D.rebuild_member(mid,rendered,mapping):raise ValueError('Earth Sphere dialogue member differs')
            changed.append(dict(archive='dialogue',member=mid))
    library=T.load_library();entries_lib,errors=T.load_translations()
    if errors:raise ValueError(errors)
    fields=L.plan(library,entries_lib,json.loads(T.GLOSSARY.read_text('utf8'))['terms'])
    from tools.source_text import library_fields
    selected={int(e['field'].split('/')[2])for r in audit['changes']if '/library/'in r['file']for e in r['edits']}
    with CPK(folder/'MTZKN_RT.CPK')as arc:
        index={r['id']:r for r in arc.files}
        for tid in sorted(selected):
            raw=arc.read(index[tid]);decoded=bytes(x if x in (0,0x5e)else x^0x5e for x in raw)
            for slot in library_fields(raw)[1]:
                tag=slot['tag']
                if tag not in fields['robot'][tid]:continue
                expected=fields['robot'][tid][tag]
                if tag in ('DSCR','DSC2'):expected=L.wrap(expected,width)
                if decoded[slot['offset']:slot['offset']+slot['bytes']]!=L.encode(expected,mapping):raise ValueError('Earth Sphere library field differs')
            changed.append(dict(archive='robot-library',member=tid))
    print('All skill/movement keys, native skill questions, nine captions and Earth Sphere archive fields passed.',flush=True)
    from tools.verify_review29 import verify as previous
    prior=previous(version);shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-0.5.28-review30-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,previous_public_version='0.5.28',prior_verification=prior,
        iso_verification=prior['iso_verification'],skill_draw_keys=len(wanted)-M.report()['draw_keys'],native_skill_cases=native,
        movement=M.report(),native_movement_cases=movement_native,layout=A.plan(),earth_sphere_archive_members=changed,screenshots=shots,runtime_verified=False)

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser();p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args()
    if a.preview:print('Preview: complete skill/movement family, native skill composition, nine caption fields, Earth Sphere archives and all carried repairs. DRY RUN: no evidence written.');return
    data=verify(a.version);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot differs')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review30_verified_'+a.version+'.json'),data)
if __name__=='__main__':main()
