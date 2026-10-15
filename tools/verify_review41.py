"""Verify the real popup archive, all 286 descriptions and the final ISO."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review41_build as B,keyword_popup as K
from tools.verify_review34 import members_equal
from tools.cpk import CPK

SHOTS=(('meganoid','7988f53e-e79c-44da-903e-8600f8a67c08'),
       ('meganoid-earlier','14ebdbb9-2e54-42a1-b566-9a9f93c41579'),
       ('messenger','f631199f-aa48-44ec-a3a2-3604876fd371'))

def verify():
    p=B.plan();folder=ROOT/'work/output/builds'/B.VERSION
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));unchanged=[]
    if build['version']!=B.VERSION or build['disc_files'].get(K.DISC)!=B.ADDED:
        raise ValueError('Actual popup archive not deployed in the build')
    for key in ('mapping','widths','latin_font'):
        if build[key]!=p['prior'][key]:raise ValueError('Font data differs from public 0.5.40')
    for name,digest in build['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Compiled output changed: '+name)
        if name not in B.CHANGED:
            if digest!=p['prior']['outputs'][name]:raise ValueError('Unrelated asset differs: '+name)
            unchanged.append(dict(name=name,sha256=digest))
    keywords=K.verify_archive(folder/B.ADDED,p['keywords'])
    title=members_equal(B.BASE/'EFFPS3.CPK',folder/'EFFPS3.CPK',{229})
    with CPK(folder/'EFFPS3.CPK')as arc:
        if arc.read(next(r for r in arc.files if r['id']==229))!=p['title']:raise ValueError('Version stamp differs')
    image_path=ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.json')
    image=json.loads(image_path.read_text(encoding='utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82 or image['replaced'].get(K.DISC)!=B.ADDED:
        raise ValueError('Corrected popup archive not deployed in final ISO')
    if sha256_file(Path(image['image']))!=image['sha256']:raise ValueError('Final ISO hash differs')
    ready=json.loads((ROOT/'work/ui/local_release_0.5.40.json').read_text(encoding='utf8'))
    live=ROOT/'work/ui/keyword_popup_live_0.5.40.json';audit=json.loads(live.read_text(encoding='utf8'))
    if audit['source_archive_sha256']!=K.SOURCE_SHA or audit['keyword_records_matched']!=143 or audit['loaded_fields_matched']!=572:
        raise ValueError('Live source-binding audit differs')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-review41-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src)))
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.40',keyword_popup=keywords,
        entries=p['keywords']['report']['entries'],source_binding_audit_sha256=sha256_file(live),
        source_binding=audit,iso_verification=image,screenshots=shots,runtime_verified=False,
        carried_verification=dict(version='0.5.40',proof_sha256=p['parent_proof_sha256'],
            regression_tests=dict(ready['regression_tests'],source_version='0.5.40'),
            full_regression_tests=ready['carried_regression_tests'],
            unchanged_files=unchanged,title_unchanged_members=title))

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    data=verify();print('Actual popup archive:',data['keyword_popup']);print('Final ISO:',data['iso_verification']['sha256'])
    if a.apply:
        for row in data['screenshots']:
            src,dst=Path(row['source']),Path(row['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists() and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review41_verified_'+B.VERSION+'.json'),data)
    else:print('DRY RUN: no evidence or screenshots written.')

if __name__=='__main__':main()
