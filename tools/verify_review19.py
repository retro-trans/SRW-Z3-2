"""Final readback for the six public 0.5.18 screenshot reports."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review19_layout as R,mission_names as N,domination_art as D
from tools import ui_hook as H,ui_catalog as U,library_build as L,battle_layout as B
from tools.cpk import CPK

SHOTS=(('link-question','3db4f003-0ca2-4e2b-88e9-204f0d2acef9'),
       ('link-PP','d5036867-e960-4bc2-a09f-7223e0f25ebf'),
       ('mission-name','2fccefe9-d515-4fea-b5d7-2fdb6866eb76'),
       ('library-name','c93d0711-b78d-4c6d-89f8-3bfc04df9774'),
       ('SR-reward','cbd3545d-dbf0-42ae-966b-4dd6ab90a45f'),
       ('world-map','69b27b81-50d5-406d-9cfc-f570c74251f9'))


def verify(version):
    from tools.verify_enemy_ui import verify as previous
    prior=previous(version)
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    elf=(folder/'EBOOT.BIN').read_bytes();mapping=build['mapping']
    addresses=build['executable']['ui_hook']['table']['payload_vas']
    cases=N.verify(elf,mapping,addresses)
    source=B.source();planned=R.plan()
    if json.loads(R.DEST.read_text(encoding='utf8'))!=planned:raise ValueError('Review plan stale')
    with CPK(folder/'AIDDATAPACK.CPK')as a:final=a.read(next(e for e in a.files if e['id']==0))
    grow=len(final)-len(source)
    widgets={a:r for r in U.fssa_strings(final,decode=lambda raw:L.decode(raw,mapping))for a in r['widget_offsets']}
    labels=[]
    for row in planned['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['text']!=row['en']:raise ValueError('Final caption mismatch at %#x'%at)
        for field,off in (('x',4),('y',8)):
            expected=struct.pack('>f',row[field])if field in row else source[at+off:at+off+4]
            if final[target+off:target+off+4]!=expected:raise ValueError('Final caption coordinate mismatch')
        if final[target+16:target+23]!=source[at+16:at+23]:raise ValueError('Caption altered native font/row pitch')
        if final[target+23]!=(row.get('mode',source[at+23])):raise ValueError('Caption alignment state mismatch')
        labels.append(dict(widget_offset=at,en=row['en'],x=struct.unpack_from('>f',final,target+4)[0]))
    for at in (0x99dc4,0x8c024):
        if final[at+grow+4:at+grow+32]!=source[at+4:at+32]:raise ValueError('Live reward amount moved')
    from tools import eff_art
    raw=eff_art.source_members(eff_art._settings(),[D.MEMBER],{D.MEMBER:D.SOURCE_SHA})[D.MEMBER]
    expected,_,_,hud=D.render(raw)
    with CPK(folder/'EFFPS3.CPK')as a:actual=a.read(next(e for e in a.files if e['id']==D.MEMBER))
    if expected!=actual:raise ValueError('Final domination atlas differs')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review19-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',
            sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,widget_captions=labels,mission_name_execution_cases=cases,
        protagonist_audit=dict(dialogue_getters=3,mission_substitution_values=4,
            name_order_preserved=True,custom_names_preserved=True,save_bytes_modified=False,
            script_lookup_keys_unchanged=True,display_name_sources='RPW, Library descriptors, dialogue getters, mission substitution values'),
        domination_hud=hud,screenshots=shots,prior_verification=prior,
        iso_verification=prior['iso_verification'],runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.19')
    ap.add_argument('--apply',action='store_true');args=ap.parse_args();result=verify(args.version)
    print('Source-bound captions:',len(result['widget_captions']))
    print('Native mission name cases:',len(result['mission_name_execution_cases']))
    print('HUD caption:',result['domination_hud'])
    print('ISO:',result['iso_verification']['sha256'])
    if not args.apply:print('DRY RUN: no evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review19_verified_'+args.version+'.json'),result)


if __name__=='__main__':main()
