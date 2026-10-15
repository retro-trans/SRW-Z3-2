"""Read startup art from the final archive and bind unchanged code to 0.5.33 proof."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256,sha256_file,write_json
from tools.cpk import CPK
from tools import review34_startup as S,gtf,texture_art as A,title_screen as T,eff_art as E
SHOTS=(('copyright-1','6e55b9da-35eb-4867-9cb5-e0a10a6c3279'),('copyright-2','4c225cce-1409-4f9b-90bf-459c09371696'),('warning','ff01182b-3e87-41de-9dc8-b5ebf0d775a9'))

def members_equal(old,new,changed):
    cases=[]
    with CPK(old)as a,CPK(new)as b:
        left={r['id']:r for r in a.files};right={r['id']:r for r in b.files}
        if set(left)!=set(right):raise ValueError('Archive member inventory changed')
        for mid,row in left.items():
            if mid in changed:continue
            x,y=a.read(row),b.read(right[mid])
            if x!=y:raise ValueError('Carried archive member changed: '+str(mid))
            cases.append(dict(member=mid,sha256=sha256(y)))
    return cases

def verify(version):
    folder=ROOT/'work/output/builds'/version;base=ROOT/'work/output/builds/0.5.33'
    build=json.loads((folder/'build.json').read_text('utf8'));prior=json.loads((base/'build.json').read_text('utf8'))
    proof=ROOT/'work/ui/review33_verified_0.5.33.json';ready=json.loads((ROOT/'work/ui/local_release_0.5.33.json').read_text('utf8'))
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Carried native verification changed')
    unchanged=[]
    if set(build['outputs'])!=set(prior['outputs']):raise ValueError('Build output inventory changed')
    for name,digest in build['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Final build file changed: '+name)
        if name not in ('TPACKPS3.CPK','EFFPS3.CPK'):
            if digest!=prior['outputs'][name] or sha256_file(base/name)!=digest:raise ValueError('Carried game file changed: '+name)
            unchanged.append(dict(name=name,sha256=digest))
    kept_tpack=members_equal(base/'TPACKPS3.CPK',folder/'TPACKPS3.CPK',{0})
    kept_eff=members_equal(base/'EFFPS3.CPK',folder/'EFFPS3.CPK',{T.MEMBER})
    expected,pixels,report=S.render(S.source(),S.checked())
    with CPK(folder/'TPACKPS3.CPK')as arc:actual=arc.read(next(r for r in arc.files if r['id']==0))
    if actual!=expected:raise ValueError('Final startup screens differ from the reviewed English')
    A.verify_member(S.source(),actual,pixels)
    title_source=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,wanted,_,title_info=T.render(title_source,version)
    with CPK(folder/'EFFPS3.CPK')as arc:actual_title=arc.read(next(r for r in arc.files if r['id']==T.MEMBER))
    if actual_title!=title:raise ValueError('Final title does not match the build version')
    T.verify(title_source,actual_title,wanted)
    image=json.loads((ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.json')).read_text('utf8'))
    if image['version']!=version or image['files_verified_each_tree']!=82:raise ValueError('ISO evidence incomplete')
    if set(image['replaced'].values())!=set(build['outputs']):raise ValueError('ISO replacement inventory differs')
    if sha256_file(Path(image['image']))!=image['sha256']:raise ValueError('Verified ISO changed')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-review34-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,iso_verification=image,startup=report,title=title_info,
        carried_verification=dict(version='0.5.33',path=str(proof),sha256=sha256_file(proof),unchanged_files=unchanged,
                                  tpack_members=kept_tpack,eff_members=kept_eff),screenshots=shots,runtime_verified=False)

def main():
    from tools.game_build import VERSION
    ap=argparse.ArgumentParser();ap.add_argument('--version',default=VERSION);ap.add_argument('--apply',action='store_true');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
    if a.preview:print('DRY RUN: startup bitmap readback, all unchanged game-file/member hashes, matched native proof and title/ISO checks; no evidence written.');return
    data=verify(a.version)
    print('Three English startup screens, 20 translated credits, preserved logos/English rows, all carried file/member hashes and ISO passed.')
    if not a.apply:print('DRY RUN: no evidence written.');return
    for row in data['screenshots']:
        src=Path(row['source']);dst=Path(row['saved_path'])
        if dst.exists()and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
        if src!=dst:shutil.copyfile(src,dst)
    write_json(ROOT/'work/ui'/('review34_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
