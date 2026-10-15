"""Read back independent font styles, selected headers and final ISO."""
import argparse
import json
import shutil
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools import review38_build as B, review38_fonts as S, ui_build as F
from tools.verify_review34 import members_equal
from tools.cpk import CPK

SHOTS={
 'yellow-labels':'4ff3b9f4-8890-4c1f-bff8-f92cad065fb1',
 'dialogue':'93fd73cc-c25b-47a3-bafe-b5a61d7f982b',
 'narration':'b09f437e-de60-406d-8c86-4a1cb4272dc7'}


def verify():
    folder=ROOT/'work/output/builds'/B.VERSION
    build=json.loads((folder/'build.json').read_text('utf8'));p=B.plan()
    if build['mapping']!=p['prior']['mapping'] or build['widths']!=p['prior']['widths']:
        raise ValueError('Font codepoints or advances changed')
    unchanged=[]
    for name,digest in build['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Final output changed: '+name)
        if name not in B.CHANGED:
            if digest!=p['prior']['outputs'][name]:raise ValueError('Unrelated game output changed: '+name)
            unchanged.append(dict(name=name,sha256=digest))
    archives={};font_reports={}
    for name,members in {'TPACKPS3.CPK':{1,3},'AIDDATAPACK.CPK':{0},'EFFPS3.CPK':{229}}.items():
        archives[name]=members_equal(B.BASE/name,folder/name,members)
    with CPK(folder/'TPACKPS3.CPK') as final,CPK(B.BASE/'TPACKPS3.CPK') as old:
        for mid in (1,3):
            before=old.read(next(r for r in old.files if r['id']==mid))
            after=final.read(next(r for r in final.files if r['id']==mid))
            if after!=p['fonts'][mid] or after!=(folder/('font_%d.bin'%mid)).read_bytes():
                raise ValueError('Packaged font differs from generated masks')
            font_reports[mid]=B.font_check(before,after,build['mapping'])
    with CPK(folder/'AIDDATAPACK.CPK') as arc:
        final=arc.read(next(r for r in arc.files if r['id']==0))
    with CPK(B.BASE/'AIDDATAPACK.CPK') as arc:
        old=arc.read(next(r for r in arc.files if r['id']==0))
    if final!=p['ui']['members'][0]:raise ValueError('UI differs from canonical font selection')
    B.U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui'])
    ui=B.ui_check(old,final,build['mapping'])
    with CPK(folder/'EFFPS3.CPK') as arc:
        if arc.read(next(r for r in arc.files if r['id']==229))!=p['title_bytes']:
            raise ValueError('Title stamp differs')
    if sha256_file(folder/'STGZ3OF2.cpk')!=build['stage_archive']['cpk_sha256']:
        raise ValueError('Decoded stage sidecar changed')
    image_path=ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.json')
    image=json.loads(image_path.read_text('utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82:
        raise ValueError('Incomplete final ISO evidence')
    if sha256_file(Path(image['image']))!=image['sha256']:raise ValueError('Final ISO changed')
    screenshots=[]
    for label,identity in SHOTS.items():
        dest=ROOT/'work/ui/screenshots'/('reported-review38-'+label+'.png')
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+identity+'.png')
        if not src.exists():src=dest
        screenshots.append(dict(source=str(src),saved_path=str(dest),sha256=sha256_file(src)))
    preview=ROOT/'work/ui/fonts/0.5.38-font-comparison.png'
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.28',
        font_styles=font_reports,selected_headers=S.plan(),unit_list_isolation=ui,
        current_letter_shapes_and_advances_preserved=True,
        original_pp_next_lv_masks_preserved=True,
        comparison=dict(path=str(preview),sha256=sha256_file(preview),kind='atlas-mask comparison; not an in-game screenshot'),
        carried_verification=dict(version='0.5.37',proof_sha256=p['parent_proof_sha256'],
            unchanged_files=unchanged,unchanged_archive_members=archives,
            backlog_executable_and_all_dialogue_bytes_unchanged=True),
        iso_verification=image,runtime_verified=False,screenshots=screenshots)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');args=p.parse_args()
    if args.preview:
        print('DRY RUN: font fill/advance equality, copied native borders, 19 context-bound headers, parent isolation and ISO.')
        return
    data=verify();print('Both font pages:',data['font_styles']);print('UI:',data['unit_list_isolation'])
    print('ISO:',data['iso_verification']['sha256'])
    if args.apply:
        for row in data['screenshots']:
            src,dst=Path(row['source']),Path(row['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists() and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review38_verified_'+B.VERSION+'.json'),data)
    else:print('DRY RUN: no evidence written.')


if __name__=='__main__':main()
