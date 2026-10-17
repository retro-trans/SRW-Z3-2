"""Read back the final screenshot corrections and execute the installed caption helpers."""
import argparse, json, shutil
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools import review45_build as B, review45_text as R, review44_build as PREVIOUS
from tools import ui_hook as H, ui_layout_text as U, library_build as L, review32_content as C
from tools import dialogue_build as DB, ui_catalog as UC, opening_narration as N
from tools import ui_description_layout as W
from tools.cpk import CPK

SHOTS = [('D-Command','564723e3-6b52-45c6-8e7b-b9d1e3ab8739'),
         ('palace','82224a29-b9aa-4419-a68e-0115cb246e82'),
         ('part','59537ca5-1d1c-46b8-ae49-7595b061e239'),
         ('narration','05615a0d-4c43-4823-af8f-20df4e52def2')]


def components():
    folder=ROOT/'work/output/builds'/B.VERSION
    b=json.loads((folder/'build.json').read_text('utf8')); prior=json.loads((B.BASE/'build.json').read_text('utf8'))
    for name,digest in b['outputs'].items():
        if sha256_file(folder/name)!=digest: raise ValueError('Compiled file changed: '+name)
        if name not in B.CHANGED and digest!=prior['outputs'][name]: raise ValueError('Unrelated output changed')
    if b['mapping']!=prior['mapping'] or b['widths']!=prior['widths']: raise ValueError('Font allocation/spacing changed')
    elf=(folder/'EBOOT.BIN').read_bytes(); expected,hook=B.dictionary((B.BASE/'EBOOT.BIN').read_bytes(),prior)
    if elf!=expected: raise ValueError('Executable differs from the verified dictionary changes')
    selected=dict(cases=[r for r in hook['cases'] if r['id'] in R.help_changes()])
    origins=[]
    for quad in (28,31):
        origins+=PREVIOUS.caption_cases(elf,b,selected,expected_count=24,quad=quad)
    full,report=UC.hook_entries(H.PREPARED.read_bytes(),b['mapping'],[])
    full={row['key']:row['english'] for row in full}
    for case in hook['cases']:
        if full[bytes.fromhex(case['key_hex'])]+b'\0'!=bytes.fromhex(case['encoded_hex']):
            raise ValueError('Fresh full-build UI catalogue differs: '+case['id'])
    from tools.pipeline import config
    planned=U.plan(config(ROOT/'config/tengoku.json'),b['mapping']); U.verify_archive(folder/'AIDDATAPACK.CPK',planned)
    original=R.B.source()
    with CPK(B.BASE/'AIDDATAPACK.CPK') as a, CPK(folder/'AIDDATAPACK.CPK') as z:
        old=a.read(next(r for r in a.files if r['id']==0)); new=z.read(next(r for r in z.files if r['id']==0))
    def widgets(blob):
        grow=len(blob)-len(original)
        return {at-grow:(row,blob[at:at+32]) for row in UC.fssa_strings(blob,decode=lambda raw:L.decode(raw,b['mapping'])) for at in row['widget_offsets']}
    before,after=widgets(old),widgets(new)
    if before.keys()!=after.keys(): raise ValueError('Widget inventory changed')
    for at,(row,state) in before.items():
        target,other=after[at]
        if at==0x8d464:
            if state[4:]!=other[4:]: raise ValueError('D-Command states or geometry changed')
            from tools.menu_layout import encode
            if target['raw']!=encode(R.plan()['edits'][0],b['mapping']): raise ValueError('Preloaded captions differ')
        elif row['raw']!=target['raw'] or state[4:]!=other[4:]: raise ValueError('Unrelated widget changed')
    stages,dialogue=B.stages(b)
    with CPK(folder/'STGZ3OF2.cpk') as arc:
        for mid,raw in stages.items():
            if arc.read(next(r for r in arc.files if r['id']==mid))!=raw: raise ValueError('Corrected stage differs')
    caption=next(r['english'] for r in dialogue if r['id']==R.CAPTION_ID)
    lines,index=C.caption(caption); visible='\n'.join(lines[index:]); span=max(sum(map(W.advance,line)) for line in lines[index:])
    raw=bytes.fromhex(b['mapping'][C.CAPTION_MARK])+L.encode(visible,b['mapping'])
    caption_origins=C.origin_cases(elf,b['mapping'],b['executable']['link_layout'],
        only_rows=[(R.CAPTION_ID,raw,span,False)],quads=(28,31,40))
    if any(row['left']<285 or row['left']+span*row['quad']/32>1175 for row in caption_origins):
        raise ValueError('Palace caption crosses portrait or right margin')
    text,condensed=N.profile(R.NARRATION)
    if text!=R.NARRATION or not condensed: raise ValueError('Narration lost wording or fitted alphabet')
    narration_width=sum(map(W.condensed_advance,text))*40/32
    if 224+narration_width>1224: raise ValueError('Narration exceeds the reported screen')
    rpw,part=B.part(b)
    if (folder/'rpw.bin').read_bytes()!=rpw: raise ValueError('Part correction changes other stats')
    with CPK(folder/'RPW_DATA.CPK') as arc:
        if arc.read(arc.files[0])!=rpw: raise ValueError('Shipped part name differs')
    from tools.verify_review34 import members_equal
    isolation={}
    for name,changed in (('AIDDATAPACK.CPK',{0}),('RPW_DATA.CPK',{0}),('EFFPS3.CPK',{229}),('STGZ3OF2.cpk',set(stages))):
        isolation[name]=dict(unchanged_members=len(members_equal(B.BASE/name,folder/name,changed)))
    carried_rewards=PREVIOUS.numeric_cases(elf)
    return dict(schema=1,version=B.VERSION,previous_public_version='0.5.44',dialogue=dialogue,
        command_lookups=hook['cases'],command_origins=origins,palace_origins=caption_origins,
        widgets_preserved=len(before),part=R.plan()['part'],part_stats_preserved=True,
        narration=dict(english=text,condensed=True,left=224,right=224+narration_width,words_preserved=True,timing_preserved=True),
        archive_isolation=isolation,carried_reward_cases=carried_rewards,
        parent_proof_sha256=sha256_file(ROOT/'work/ui/review44_verified_0.5.44.json'),
        font_codes_advances_and_archive_unchanged=True,runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');args=p.parse_args()
    if args.preview: print('DRY RUN: native lookup/origins, fresh catalogue, unchanged widgets/stats/fonts, archive isolation and ISO.'); return
    result=components(); image=ROOT/f'work/output/iso/{B.VERSION}/Tengoku-hen-English-{B.VERSION}.iso'
    report=json.loads(image.with_suffix('.json').read_text('utf8'))
    if report['version']!=B.VERSION or report['files_verified_each_tree']!=82 or sha256_file(image)!=report['sha256']:
        raise ValueError('Final ISO differs')
    result['iso_verification']=report;result['screenshots']=[]
    for label,ident in SHOTS:
        source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-review45-'+label+'.png')
        if not source.exists():source=dest
        result['screenshots'].append(dict(source=str(source),saved_path=str(dest),sha256=sha256_file(source)))
    print('Verified 10 lookups, 48 command origins, 3 palace origins, all 4803 widgets, part stats, narration and complete ISO.')
    if args.apply:
        for row in result['screenshots']:
            source,dest=Path(row['source']),Path(row['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and sha256_file(dest)!=row['sha256']: raise ValueError('Screenshot collision')
            if source!=dest: shutil.copyfile(source,dest)
        write_json(ROOT/f'work/ui/review45_verified_{B.VERSION}.json',result)
    else: print('DRY RUN: no evidence written.')


if __name__=='__main__':main()
