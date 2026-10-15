"""Final readback of both map-selector states and preserved 0.5.38 assets."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review39_build as B
from tools.verify_review34 import members_equal
from tools.cpk import CPK


def verify():
    p=B.plan();folder=ROOT/'work/output/builds'/B.VERSION
    build=json.loads((folder/'build.json').read_text('utf8'));unchanged=[]
    for key in ('mapping','widths','latin_font'):
        if build[key]!=p['prior'][key]:raise ValueError('Font data differs from 0.5.38')
    for name,digest in build['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Final asset changed: '+name)
        if name not in B.CHANGED:
            if digest!=p['prior']['outputs'][name]:raise ValueError('Unrelated file differs: '+name)
            unchanged.append(dict(name=name,sha256=digest))
    with CPK(folder/'AIDDATAPACK.CPK') as arc:new=arc.read(next(r for r in arc.files if r['id']==0))
    with CPK(B.BASE/'AIDDATAPACK.CPK') as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    if new!=p['ui']['members'][0]:raise ValueError('Selector differs from canonical UI plan')
    checked=B.ui_check(old,new,build['mapping']);B.U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui'])
    archives={name:members_equal(B.BASE/name,folder/name,members)
              for name,members in {'AIDDATAPACK.CPK':{0},'EFFPS3.CPK':{229}}.items()}
    with CPK(folder/'EFFPS3.CPK') as arc:
        if arc.read(next(r for r in arc.files if r['id']==229))!=p['title']:raise ValueError('Version stamp differs')
    for name in ('font_1.bin','font_3.bin','STGZ3OF2.cpk','rpw.bin'):
        if sha256_file(folder/name)!=sha256_file(B.BASE/name):raise ValueError('Sidecar changed: '+name)
    image=json.loads((ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.json')).read_text('utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82 or sha256_file(Path(image['image']))!=image['sha256']:
        raise ValueError('Final ISO validation differs')
    screenshots=[]
    for n,identity in enumerate(('8154ad31-cb14-4c2c-878e-70e395cb075d','1e77449f-d855-4be4-8996-a0c3903ca4c6')):
        dst=ROOT/'work/ui/screenshots'/('reported-review39-selector-%d.png'%(n+1))
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+identity+'.png')
        if not src.exists():src=dst
        screenshots.append(dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src)))
    ready=json.loads((ROOT/'work/ui/local_release_0.5.38.json').read_text('utf8'))
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.28',selector=checked,
        source_bound_widgets=B.S.plan(),runtime_verified=False,iso_verification=image,screenshots=screenshots,
        carried_verification=dict(version='0.5.38',proof_sha256=p['parent_proof_sha256'],
            regression_tests=ready['regression_tests'],unchanged_files=unchanged,unchanged_archive_members=archives))


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.preview:print('DRY RUN: both compiled selector states, 4,803 widgets, unchanged fonts/code/dialogue and 82-file ISO.');return
    d=verify();print('Selector:',d['selector']);print('ISO:',d['iso_verification']['sha256'])
    if a.apply:
        for r in d['screenshots']:
            src,dst=Path(r['source']),Path(r['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists() and sha256_file(dst)!=r['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review39_verified_'+B.VERSION+'.json'),d)
    else:print('DRY RUN: no evidence written.')


if __name__=='__main__':main()
