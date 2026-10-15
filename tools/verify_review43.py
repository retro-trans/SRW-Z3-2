"""Verify the delivered phase/map-panel fixes and their unchanged dependencies."""
import argparse,itertools,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review43_build as B,review43_text as R,ui_layout_text as U,eboot_text as E
from tools import ui_hook as H,review42_news as NEWS
from tools.cpk import CPK
from tools.ui_coverage import ui_string_table

SHOTS=(('phase','0ddcb291-e308-42f1-8feb-be2e5201cf01'),('aboard','2317b5d7-8c70-49f0-a4bc-ff3a3ff3055a'),
       ('Tenshi','a650aa31-7dc3-4c01-a58b-40bcf84e2343'),('Trans-Am','04e225e3-1b4c-418c-a543-911e1c180b40'))


def verify():
    folder=ROOT/'work/output/builds'/B.VERSION;b=json.loads((folder/'build.json').read_text('utf8'))
    parent=json.loads((B.BASE/'build.json').read_text('utf8'))
    parent_proof=ROOT/'work/ui/review42_verified_0.5.42.json'
    if sha256_file(parent_proof)!=b['incremental_build']['parent_proof_sha256']:raise ValueError('Parent proof changed')
    for name,digest in b['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Compiled asset differs: '+name)
        if name not in B.CHANGED and digest!=parent['outputs'][name]:raise ValueError('Unrelated asset changed')
    if b['mapping']!=parent['mapping']or b['widths']!=parent['widths']:raise ValueError('Font shapes/spacing changed')
    elf=(folder/'EBOOT.BIN').read_bytes();wanted,redirect=B.command_patch((B.BASE/'EBOOT.BIN').read_bytes(),b['mapping'])
    if elf!=wanted:raise ValueError('Executable changes beyond the command slot')
    news=NEWS.verify(elf,b['mapping'],b['executable']['ui_hook'],b['executable']['link_layout'])
    from tools.pipeline import config
    ui=U.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
    U.verify_archive(folder/'AIDDATAPACK.CPK',ui)
    with CPK(folder/'AIDDATAPACK.CPK')as arc:
        members={i:arc.read(next(r for r in arc.files if r['id']==i))for i in (0,5)}
    with CPK(B.BASE/'AIDDATAPACK.CPK')as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    geometry=B.ui_check(old,members[0],b['mapping']);native=B.native_cases(elf,b,members[5])
    rows=ui_string_table(members[5],decode=lambda r:r.hex());terrain=[]
    for edit in R.plan()['table_fragments']:
        if rows[edit['table_row_id']]['raw']!=U.table_encode(edit,b['mapping']):raise ValueError('SB2T compiled row differs')
        if edit['table_row_id']!=3:terrain.append(edit['table_row_id'])
    masks=[]
    for flags in itertools.product((False,True),repeat=4):
        raw=b''.join(rows[91+i]['raw']if present else 'ー'.encode('cp932')for i,present in enumerate(flags))
        if len(raw)!=8:raise ValueError('Terrain mask changes native four-cell layout')
        masks.append(raw.hex())
    with CPK(B.BASE/'STGZ3OF2.cpk')as arc:old=arc.read(next(r for r in arc.files if r['id']==598))
    with CPK(folder/'STGZ3OF2.cpk')as arc:new=arc.read(next(r for r in arc.files if r['id']==598))
    a=E.encode('...An Tenshi.',b['mapping']);z=E.encode('...A Tenshi.',b['mapping'])
    if old.count(a)!=1 or old.replace(a,z)!=new:raise ValueError('Dialogue changed beyond the article')
    if sha256_file(folder/'STGZ3OF2.cpk')!=b['stage_archive']['cpk_sha256']or not b['stage_archive']['roundtrip_verified']:
        raise ValueError('Stage encryption evidence differs')
    from tools.verify_review34 import members_equal
    isolation={}
    for name,changed in (('AIDDATAPACK.CPK',{0,5}),('EFFPS3.CPK',{229}),('STGZ3OF2.cpk',{598})):
        unchanged=members_equal(B.BASE/name,folder/name,changed);isolation[name]=dict(unchanged_members=len(unchanged))
    image_path=ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.iso')
    image=json.loads(image_path.with_suffix('.json').read_text('utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82 or sha256_file(image_path)!=image['sha256']:
        raise ValueError('Final ISO readback differs')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-review43-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.40',phase=native,aboard=R.plan()['aboard_bounds'],
        terrain_component_rows=terrain,terrain_masks=masks,tenshi=dict(record='598:t_5:36',english='...A Tenshi.',other_stage_bytes_unchanged=True),
        command=redirect,widget_geometry=geometry,archive_isolation=isolation,carried_news=news,
        parent_proof_sha256=sha256_file(parent_proof),font_codes_advances_and_archive_unchanged=True,
        keyword_popup_unchanged=True,iso_verification=image,screenshots=shots,runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.preview:print('DRY RUN: native phase origins/command lookup, all widget states, terrain component rows, one stage article, parent news, archives and final ISO.');return
    data=verify();print('Final ISO:',data['iso_verification']['sha256']);print('Phase origins:',len(data['phase']['phase_origins']))
    print('Unchanged geometry:',data['widget_geometry']);print('Terrain components/masks:',len(data['terrain_component_rows']),len(data['terrain_masks']))
    if a.apply:
        for row in data['screenshots']:
            src,dst=Path(row['source']),Path(row['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists()and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review43_verified_'+B.VERSION+'.json'),data)
    else:print('DRY RUN: no evidence written.')

if __name__=='__main__':main()
