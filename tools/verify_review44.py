"""Read back shipped Colony Laser references, reward fields and command captions."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review44_build as B,review44_text as R,ui_layout_text as U,ui_hook as H,eboot_text as E
from tools.cpk import CPK

SHOTS=(('Colony-Laser','784926d9-115a-405b-88ce-9f27d32c23b1'),
       ('EXP','5e83addb-1cc6-44d6-a580-49bcd9570d3d'),('deployment','809c5d4b-17fc-4832-808c-1e65fb031f29'))


def verify():
    folder=ROOT/'work/output/builds'/B.VERSION;b=json.loads((folder/'build.json').read_text('utf8'))
    prior=json.loads((B.BASE/'build.json').read_text('utf8'));proof=ROOT/'work/ui/review43_verified_0.5.43.json'
    if sha256_file(proof)!=b['incremental_build']['parent_proof_sha256']:raise ValueError('Parent evidence changed')
    for name,digest in b['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Compiled asset changed: '+name)
        if name not in B.CHANGED and digest!=prior['outputs'][name]:raise ValueError('Unrelated output changed')
    if b['mapping']!=prior['mapping']or b['widths']!=prior['widths']:raise ValueError('Font allocation or spacing changed')
    elf=(folder/'EBOOT.BIN').read_bytes();expected,hook=B.dictionary_patch((B.BASE/'EBOOT.BIN').read_bytes(),b['mapping'])
    if elf!=expected:raise ValueError('Executable changes beyond the checked English values')
    stub=b['executable']['ui_hook'];vm=H._Runner(elf,int(stub['stub_va'],16),stub['stub_bytes']);read=H._reader(elf,H._headers(elf)[2])
    lookups=[]
    for case in hook['cases']:
        ptr,steps=vm.run(bytes.fromhex(case['key_hex'])+b'\0')
        wanted=(R.caption_encoded(case['english'],b['mapping'])if case['english'].startswith('　')else E.encode(case['english'],b['mapping']))+b'\0'
        if ptr is None or read(ptr,len(wanted))!=wanted:raise ValueError('Installed UI output differs')
        lookups.append(dict(id=case['id'],english=case['english'],steps=steps))
    from tools.pipeline import config
    ui=U.plan(config(ROOT/'config/tengoku.json'),b['mapping']);U.verify_archive(folder/'AIDDATAPACK.CPK',ui)
    with CPK(folder/'AIDDATAPACK.CPK')as arc:new_ui=arc.read(next(r for r in arc.files if r['id']==0));sb=arc.read(next(r for r in arc.files if r['id']==5))
    with CPK(B.BASE/'AIDDATAPACK.CPK')as arc:old_ui=arc.read(next(r for r in arc.files if r['id']==0))
    geometry=B.ui_check(old_ui,new_ui,b['mapping']);numbers=B.numeric_cases(elf);captions=B.caption_cases(elf,b,hook)
    stages,dialogues=B.stages(b);libraries,library_rows=B.libraries(b)
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        for mid,raw in stages.items():
            if arc.read(next(r for r in arc.files if r['id']==mid))!=raw:raise ValueError('Compiled dialogue differs')
    with CPK(folder/'MTZKN_PT.CPK')as arc:
        for mid,raw in libraries['MTZKN_PT.CPK'].items():
            if arc.read(next(r for r in arc.files if r['id']==mid))!=raw:raise ValueError('Compiled Library correction differs')
    if sha256_file(folder/'STGZ3OF2.cpk')!=b['stage_archive']['cpk_sha256']or not b['stage_archive']['roundtrip_verified']:
        raise ValueError('Stage encryption lacks matched evidence')
    from tools import review43_build as PREVIOUS
    carried=PREVIOUS.native_cases(elf,b,sb)
    from tools.verify_review34 import members_equal
    isolation={}
    for name,changed in (('AIDDATAPACK.CPK',{0}),('EFFPS3.CPK',{229}),('STGZ3OF2.cpk',set(stages)),('MTZKN_PT.CPK',set(libraries['MTZKN_PT.CPK']))):
        unchanged=members_equal(B.BASE/name,folder/name,changed);isolation[name]=dict(unchanged_members=len(unchanged))
    image_path=ROOT/'work/output/iso'/B.VERSION/('Tengoku-hen-English-'+B.VERSION+'.iso')
    image=json.loads(image_path.with_suffix('.json').read_text('utf8'))
    if image['version']!=B.VERSION or image['files_verified_each_tree']!=82 or sha256_file(image_path)!=image['sha256']:
        raise ValueError('Final ISO differs')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-review44-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.40',dialogue=dialogues,library=library_rows,
        reward_cases=numbers,command_lookups=lookups,caption_cases=captions,layout=R.plan(),widget_checks=geometry,archive_isolation=isolation,
        parent_proof_sha256=sha256_file(proof),carried_phase_and_trans_am=carried,
        font_codes_advances_and_archive_unchanged=True,keyword_popup_archive_unchanged=True,
        iso_verification=image,screenshots=shots,runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.preview:print('DRY RUN: compiled references and labels, native reward digit boundaries/lookup states, blank font cells, archive isolation and final ISO.');return
    data=verify();print('Colony Laser dialogue/Library:',len(data['dialogue']),len(data['library']));print('Reward/lookup cases:',len(data['reward_cases']),len(data['command_lookups']))
    print('Final ISO:',data['iso_verification']['sha256'])
    if a.apply:
        for row in data['screenshots']:
            src,dst=Path(row['source']),Path(row['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists()and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review44_verified_'+B.VERSION+'.json'),data)
    else:print('DRY RUN: no evidence written.')

if __name__=='__main__':main()
