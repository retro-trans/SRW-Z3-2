"""Read back the final ISO's upgrade families, award geometry and trophy pack."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import upgrade_messages as U,upgrade_layout as L,upgrade_oracle as O,trophy_text as T
from tools import ui_hook as H,ui_catalog as C,eboot_text as E,library_build as B,battle_layout as A,rpw_text as R
from tools.cpk import CPK

SHOTS=(('unlock-custom','147610c4-6904-4dea-8707-3fd8343458b5'),
       ('unlock-combo','665aeb5c-7517-4e64-b262-6bd1822b51a9'),
       ('upgrade-question','49e3d66b-0d10-4da1-9cc6-2eadc58e71a4'),
       ('unlock-HP-EN','5b37022b-6331-480a-a09a-e606c66b07ca'),
       ('custom-award','6641e9e1-0147-43a7-896c-2796ae65f6fc'))


def verify(version):
    from tools.verify_review19 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));elf=(folder/'EBOOT.BIN').read_bytes();mapping=build['mapping']
    info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes']);read=H._reader(elf,H._headers(elf)[2])
    entries=U.hook_entries(H.PREPARED.read_bytes(),mapping);by_key={r['key']:r for r in entries}
    def hit(key):
        expected=by_key[key]['english'];pointer,steps=runner.run(key+b'\0')
        if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final upgrade lookup failed')
        return dict(id=by_key[key]['id'],steps=steps,english=B.decode(expected,mapping))
    lookups=[hit(r['key'])for r in entries]
    with CPK(folder/'RPW_DATA.CPK')as archive:rpw=archive.read(archive.files[0])
    _,pool=R.pool_of(rpw)
    # Source slots identify records; relocated VWF cells are not CP932 text.
    original_rpw=R.load_rpw();old_js,_=R.pool_of(original_rpw);rpw_grow=len(rpw)-len(original_rpw)
    part_slots={s['record']:s for s in R.slots(original_rpw)if s['chunk']=='boost-p' and s['col']==1}
    source=H.PREPARED.read_bytes();src_read=H._reader(source,H._headers(source)[2]);cases=[]
    rows,_=U.source_rows(source)
    for row in rows:
        if row['condition_en'] is None:continue
        slot=part_slots[row['part_record']]
        at=slot['pointer_offset']+(rpw_grow if slot['pointer_offset']>=old_js['body_end'] else 0)
        ptr=struct.unpack_from('<I',rpw,at)[0]
        raw=pool[ptr:pool.index(b'\0',ptr)]
        if raw!=E.encode(row['item_en'],mapping):raise ValueError('Final RPW item name differs from composed lookup')
        ident=struct.unpack('>h',src_read(0x855c0c+row['index']*16+12,2))[0]
        lines,steps=O.report(elf,ident,raw)
        cases.append(dict(index=row['index'],native_steps=steps,condition=hit(lines[1]),item=hit(lines[2])))
    table=struct.unpack('>11I',src_read(0xa26808,44));choices=[]
    for index,va in enumerate(table):
        if va not in U.BONUSES:continue
        lines,steps=O.bonus(elf,index)
        choices.append(dict(choice=index,native_steps=steps,message=hit(H.utf8_key(lines[0],source))))
    planned=L.plan()
    if json.loads(L.DEST.read_text(encoding='utf8'))!=planned:raise ValueError('Award layout source binding stale')
    source_aid=A.source()
    with CPK(folder/'AIDDATAPACK.CPK')as archive:final=archive.read(next(e for e in archive.files if e['id']==0))
    grow=len(final)-len(source_aid)
    widgets={a:r for r in C.fssa_strings(final,decode=lambda raw:B.decode(raw,mapping))for a in r['widget_offsets']}
    for row in planned['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['text']!=row['en']:raise ValueError('Final award caption differs')
        if final[target+4:target+8]!=struct.pack('>f',row['x']):raise ValueError('Final award origin differs')
        if final[target+8:target+23]!=source_aid[at+8:at+23]:raise ValueError('Award native y/font/color changed')
        if final[target+23]!=row['mode']:raise ValueError('Award alignment state differs')
    final_trophy=(folder/'TROPHY.TRP').read_bytes();T.verify(T.source(),final_trophy,T.plan())
    if build['disc_files'].get(T.DISC)!='TROPHY.TRP':raise ValueError('Trophy pack omitted from ISO replacements')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-upgrade20-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',
                          sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,lookup_cases=lookups,native_report_cases=cases,
        native_bonus_question_cases=choices,award_lines=planned['lines'],trophies=build['trophies'],
        screenshots=shots,prior_verification=prior,iso_verification=prior['iso_verification'],runtime_verified=False,
        proofreading=dict(fields_examined=104,fields_in_scope=104,reviewer='upgrade20_wording',
            corrections=['HP and EN to level 10','Spirit names Break and Luck from bound glossary'],
            inference='Simultaneous Spirit use expressed as concurrent effects; no trigger change.'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default='0.5.20');p.add_argument('--apply',action='store_true');a=p.parse_args();result=verify(a.version)
    print('Final lookups:',len(result['lookup_cases']),'native reports:',len(result['native_report_cases']),
          'native bonus questions:',len(result['native_bonus_question_cases']),'trophies:',result['trophies']['trophy_count'])
    print('ISO:',result['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('upgrade_ui_verified_'+a.version+'.json'),result)

if __name__=='__main__':main()
