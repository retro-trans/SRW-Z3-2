"""Read back both English Search tab states and preserved parent assets."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review40_build as B
from tools.verify_review34 import members_equal
from tools.cpk import CPK


def verify():
    p=B.plan();folder=ROOT/'work/output/builds'/B.VERSION
    build=json.loads((folder/'build.json').read_text('utf8'));unchanged=[]
    for key in ('mapping','widths','latin_font'):
        if build[key]!=p['prior'][key]:raise ValueError('Font data differs from 0.5.39')
    for name,digest in build['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Final asset changed: '+name)
        if name not in B.CHANGED:
            if digest!=p['prior']['outputs'][name]:raise ValueError('Unrelated file differs: '+name)
            unchanged.append(dict(name=name,sha256=digest))
    with CPK(folder/'AIDDATAPACK.CPK') as arc:new=arc.read(next(r for r in arc.files if r['id']==0))
    with CPK(B.BASE/'AIDDATAPACK.CPK') as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    if new!=p['ui']['members'][0]:raise ValueError('Search tabs differ from canonical UI plan')
    checked=B.ui_check(old,new,build['mapping']);B.U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui'])
    grow=len(new)-len(B.S.B.source())
    compiled={at-grow:r['raw']for r in B.S.U.fssa_strings(new,decode=lambda r:r.hex())for at in r['widget_offsets']}
    native=B.S.native_cases((folder/'EBOOT.BIN').read_bytes(),build['mapping'],build['executable']['table_va'],compiled)
    archives={name:members_equal(B.BASE/name,folder/name,members)
              for name,members in {'AIDDATAPACK.CPK':{0},'EFFPS3.CPK':{229}}.items()}
    with CPK(folder/'EFFPS3.CPK') as arc:
        if arc.read(next(r for r in arc.files if r['id']==229))!=p['title']:raise ValueError('Version stamp differs')
    for name in ('font_1.bin','font_3.bin','STGZ3OF2.cpk','rpw.bin'):
        if sha256_file(folder/name)!=sha256_file(B.BASE/name):raise ValueError('Sidecar changed: '+name)
    image=json.loads((ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.json')).read_text('utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82 or sha256_file(Path(image['image']))!=image['sha256']:
        raise ValueError('Final ISO validation differs')
    dst=ROOT/'work/ui/screenshots/reported-review40-search-tabs.png'
    src=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-d5f31897-a73a-40f9-be18-6cff701682ae.png')
    if not src.exists():src=dst
    ready=json.loads((ROOT/'work/ui/local_release_0.5.39.json').read_text('utf8'))
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.28',search_tabs=checked,
        source_bound_widgets=B.S.plan(),native_caption_cases=native,runtime_verified=False,iso_verification=image,
        screenshots=[dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src))],
        carried_verification=dict(version='0.5.39',proof_sha256=p['parent_proof_sha256'],
            regression_tests=ready['regression_tests'],full_regression_tests=ready['carried_regression_tests'],
            unchanged_files=unchanged,unchanged_archive_members=archives))


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.preview:print('DRY RUN: four English tab states, unchanged Abilities, 4,803 widgets, carried assets and 82-file ISO.');return
    d=verify();print('Search tabs:',d['search_tabs']);print('ISO:',d['iso_verification']['sha256'])
    if a.apply:
        for r in d['screenshots']:
            src,dst=Path(r['source']),Path(r['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists() and sha256_file(dst)!=r['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review40_verified_'+B.VERSION+'.json'),d)
    else:print('DRY RUN: no evidence written.')


if __name__=='__main__':main()
