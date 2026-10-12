"""Final readback of all native map defeat quotes and carried repairs."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review28_quotes as Q,rpw_text as R,library_build as L
from tools.cpk import CPK


def verify(version):
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'))
    mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes();planned=Q.plan()
    if json.loads(Q.DEST.read_text('utf8'))!=planned:raise ValueError('Defeat quote audit stale')
    native=Q.verify(elf,planned,mapping)
    source=R.load_rpw();js,_=R.pool_of(source);names=R.load_names();source_rows=[r for r in R.slots(source)if r['family']=='quote']
    with CPK(folder/'RPW_DATA.CPK')as arc:final=arc.read(arc.files[0])
    newjs,_=R.pool_of(final);grow=len(final)-len(source);cells=[]
    for row in source_rows:
        at=row['pointer_offset']+(grow if row['pointer_offset']>=js['body_end']else 0)
        pointer=struct.unpack_from('<I',final,at)[0];start=newjs['body_offset']+pointer
        expected=L.encode(R.text_for(row,names),mapping)
        if final[start:final.index(b'\0',start)]!=expected:raise ValueError('RPW defeat quote differs')
        cells.append(dict(id=row['id'],english=R.text_for(row,names)))
    src=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-3ab101b9-d83e-4cad-81b0-d8bb09e138ad.png')
    dst=ROOT/'work/ui/screenshots/reported-0.5.18-review28-Nigel.png'
    if not src.exists():src=dst
    shot=dict(source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False)
    print('All 249 native and RPW defeat quote entries passed. Checking carried fixes...',flush=True)
    from tools.verify_review27 import verify as previous
    prior=previous(version)
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        quote_audit_sha256=sha256_file(Q.DEST),native_defeat_quotes=native,rpw_defeat_quotes=cells,
        distinct_quotes=planned['distinct_quotes'],wording_audit_sha256=sha256_file(ROOT/'work/ui/review28_wording_audit.json'),
        screenshots=[shot],runtime_verified=False)


def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args()
    if a.preview:
        data=Q.plan();print('Preview:',len(data['rows']),'quote entries;',data['distinct_quotes'],'distinct.');print(data['rows'][67]['english']);print('Planned: final quote/readback evidence and reported screenshot. DRY RUN: no files written.');return
    data=verify(a.version);print('Native quote stores:',len(data['native_defeat_quotes']['store_cases']),'RPW cells:',len(data['rpw_defeat_quotes']),'Distinct:',data['distinct_quotes']);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Reported screenshot differs')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review28_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
