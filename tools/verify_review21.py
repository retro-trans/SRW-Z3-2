"""Read back final training columns, crystal names and canonical pilot pieces."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review21_layout as L,review21_names as N,battle_layout as B,ui_catalog as U,library_build as R,rpw_text as P
from tools.cpk import CPK

SHOTS=(('Heero','65b9bdbc-445e-4317-a39d-3932f15792ce'),('Crowe','849a23b5-7d5f-4c1f-85eb-8b7edc40e915'),
       ('training','0f9d221f-9760-44de-a171-d829e7653895'),('Z-Crystal','1231c707-0aa6-41e3-b88e-20e424b49649'))

def verify(version):
    from tools.verify_upgrade_ui import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping'];source=B.source();plan=L.plan()
    if json.loads(L.DEST.read_text(encoding='utf8'))!=plan:raise ValueError('Review21 layout data stale')
    with CPK(folder/'AIDDATAPACK.CPK')as archive:final=archive.read(next(e for e in archive.files if e['id']==0))
    grow=len(final)-len(source);widgets={a:r for r in U.fssa_strings(final,decode=lambda raw:R.decode(raw,mapping))for a in r['widget_offsets']}
    for row in plan['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['text']!=row['en']:raise ValueError('Final training/crystal text differs')
        if final[target+8:target+16]!=source[at+8:at+16]or final[target+21:target+32]!=source[at+21:at+32]:
            raise ValueError('Native row geometry or state changed')
        expected=struct.pack('>f',row['x'])if 'x'in row else source[at+4:at+8]
        if final[target+4:target+8]!=expected:raise ValueError('Final label origin differs')
        if final[target+16:target+21]!=bytes(row.get('font_metrics',source[at+16:at+21])):raise ValueError('Final font size differs')
    for at in (0x94fe4,0x95004,0x95024):
        if final[at+grow+4:at+grow+32]!=source[at+4:at+32]:raise ValueError('Crystal numeric cost widget moved')
    with CPK(folder/'RPW_DATA.CPK')as archive:rpw=archive.read(archive.files[0])
    original=P.load_rpw();old_js,_=P.pool_of(original);_,pool=P.pool_of(rpw);growth=len(rpw)-len(original);pieces=[]
    wanted={'pilot-nw:214:1':'Yuy','pilot-nw:215:1':'Yuy','pilot-nw:1022:1':'Bluest'}
    for slot in P.slots(original):
        if slot['id']not in wanted:continue
        at=slot['pointer_offset']+(growth if slot['pointer_offset']>=old_js['body_end']else 0)
        ptr=struct.unpack_from('<I',rpw,at)[0];text=R.decode(pool[ptr:pool.index(b'\0',ptr)],mapping)
        if text!=wanted[slot['id']]:raise ValueError('Final corrected surname differs')
        pieces.append(dict(id=slot['id'],english=text))
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review21-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        name_coverage=N.coverage(),pilot_pieces=pieces,layout=plan,screenshots=shots,runtime_verified=False)

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args();result=verify(a.version)
    print('Final widgets:',len(result['layout']['edits']),'Crystal names:',len(result['layout']['crystal_names']))
    print('Canonical names:',result['name_coverage']);print('ISO:',result['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review21_verified_'+a.version+'.json'),result)

if __name__=='__main__':main()
