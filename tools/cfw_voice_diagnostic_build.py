"""Build and verify the local 0.5.54 PS3 voice/quote diagnostic; never publish."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import cfw_package as B,cfw_trophy_control as T,cfw_self as C
from tools import cfw_voice_diagnostic as D,cfw_voice_diagnostic_check as V
from tools import iso_write as I,title_screen as TS,eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as cpk_build
from tools.verify_archives import compare

VERSION=D.VERSION
OUTPUT=ROOT/'work/output/builds'/VERSION
IMAGE=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}-voice-diagnostic.iso'
PROOF=ROOT/f'work/ui/cfw_voice_diagnostic_verified_{VERSION}.json'
EBOOT='/PS3_GAME/USRDIR/EBOOT.BIN'
EFF=E.ARCHIVE


def load(path):return json.loads(path.read_text('utf8'))


def parent():
    seal=load(ROOT/'work/ui/local_release_0.5.53.json')
    proof=load(T.PROOF)
    if sha256_file(T.PROOF)!=seal['final_readback_sha256'] or sha256_file(T.OUTPUT/'build.json')!=proof['build_sha256']:
        raise ValueError('0.5.53 proof changed')
    parent52=load(ROOT/'work/ui/local_release_0.5.52.json')
    if parent52['iso']['replaced'].get(EFF)!='EFFPS3.CPK':
        raise ValueError('Title archive does not match the verified source inventory')
    if sha256_file(B.PROOF)!=parent52['final_readback_sha256']:
        raise ValueError('0.5.52 proof changed')
    build=load(B.OUTPUT/'build.json')
    if load(B.PROOF)['build_sha256']!=sha256_file(B.OUTPUT/'build.json'):
        raise ValueError('0.5.52 build changed')
    for name,digest in build['outputs'].items():
        if sha256_file(B.OUTPUT/name)!=digest:raise ValueError('Parent output changed: '+name)
    if sha256_file(T.OUTPUT/'TROPHY.TRP')!=T.ORIGINAL_SHA:
        raise ValueError('Restored original trophy package differs')
    if sha256_file(B.FSELF)!=B.FSELF_SHA:raise ValueError('Pinned wrapper tool changed')
    return build,seal,parent52


def plan():
    build,seal,parent52=parent()
    baseline=C.extract_debug((B.OUTPUT/'EBOOT.BIN').read_bytes())
    elf,diagnostic=D.patch(baseline,build)
    checks=V.verify(elf,baseline,build,diagnostic)
    source=E.source_members(E._settings(),[TS.MEMBER],{TS.MEMBER:TS.SOURCE_SHA})[TS.MEMBER]
    title,pixels,_,info=TS.render(source,VERSION)
    TS.verify(source,title,pixels)
    print('0.5.54: observe bank loads and replace only fallback captions; stamp title version.',flush=True)
    print('Native observer cases:',checks['poll_cases'],'; native integration:',len(checks['integration']),
          '; converter models:',checks['native_converter_models_verified'],flush=True)
    print('0.5.53 original trophy package, voice data, audio, fonts and saves preserved.',flush=True)
    return dict(build=build,seal=seal,parent52=parent52,elf=elf,diagnostic=diagnostic,
                checks=checks,title=title,title_info=info)


def preview(build,checks,path):
    import numpy as np
    from PIL import Image
    from tools.ui_build import atlas,cell_xy
    from tools import srvc as S
    from tools import cfw_self as C
    text=checks['actor_and_unknown_cases'][0]['text'].replace('\\n','\n')
    font=atlas((B.OUTPUT/'font_1.bin').read_bytes())
    elf=C.extract_debug((B.OUTPUT/'EBOOT.BIN').read_bytes())
    va=build['executable']['table_va']
    va=int(va,16) if isinstance(va,str) else va
    table=elf[S.va_to_offset(elf,va):S.va_to_offset(elf,va)+4480]
    canvas=Image.new('RGB',(1000,112),(7,17,24))
    widths=[]
    for row,line in enumerate(text.splitlines()):
        pen=20
        for character in line:
            code=build['mapping'][character]
            hi,lo=bytes.fromhex(code)
            index=(hi-0x81)*192+lo-0x40
            x,y=cell_xy(code)
            mask=Image.fromarray((font[y:y+32,x:x+32]&255).astype(np.uint8))
            canvas.paste((255,255,255),(pen,12+row*40),mask)
            pen+=table[index]
        widths.append(pen-20)
    if max(widths)>960:raise ValueError('Diagnostic readout does not fit caption width')
    path.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(path)
    return dict(path=path.relative_to(ROOT).as_posix(),row_widths=widths,
                simulated_readout_from_unchanged_game_font=True)


def build(state):
    if OUTPUT.exists() or PROOF.exists():raise ValueError('Preserve existing 0.5.54 diagnostic')
    OUTPUT.mkdir(parents=True)
    elf_path=OUTPUT/'program.elf'
    elf_path.write_bytes(state['elf'])
    generated=OUTPUT/'fself-generated.bin'
    subprocess.run([str(B.FSELF),str(elf_path),str(generated)],check=True)
    original=B.original()
    wrapped=C.retain_identity(generated.read_bytes(),original)
    wrapper=C.verify(wrapped,state['elf'],original)
    (OUTPUT/'EBOOT.BIN').write_bytes(wrapped)
    for name in state['build']['outputs']:
        if name not in ('EBOOT.BIN','EFFPS3.CPK','TROPHY.TRP'):
            shutil.copyfile(B.OUTPUT/name,OUTPUT/name)
    shutil.copyfile(T.OUTPUT/'TROPHY.TRP',OUTPUT/'TROPHY.TRP')
    for name in B.EXTRAS:shutil.copyfile(B.OUTPUT/name,OUTPUT/name)
    with CPK(B.OUTPUT/'EFFPS3.CPK') as arc:
        compressed={r['id'] for r in arc.files if r['id']==TS.MEMBER and r['size']!=r['extract']}
    cpk_build(B.OUTPUT/'EFFPS3.CPK',OUTPUT/'EFFPS3.CPK',{TS.MEMBER:state['title']},compress=compressed)
    isolation=compare(B.OUTPUT/'EFFPS3.CPK',OUTPUT/'EFFPS3.CPK',{TS.MEMBER:state['title']})
    artwork=preview(state['build'],state['checks'],ROOT/f'work/ui/{VERSION}/voice-diagnostic-sample.png')
    report=copy.deepcopy(state['build'])
    report.update(version=VERSION,title_screen=state['title_info'],voice_diagnostic=state['diagnostic'],
        runtime_verified=False,layout_verified=False)
    report['outputs']={name:sha256_file(OUTPUT/name) for name in report['outputs']}
    report['executable']['output_sha256']=sha256(wrapped)
    table=report['executable']['ui_hook']['table']
    table['used_bytes']=(table['used_bytes']+15)&~15
    table['used_bytes']+=D.RESERVED
    table['headroom_bytes']=table['ext_size']-table['used_bytes']
    report['cfw_packaging']=dict(wrapper,original_self_sha256=sha256(original),
        fself_sha256=B.FSELF_SHA,installed=False)
    report['incremental_build']=dict(parent_version='0.5.53',parent_iso_sha256=state['seal']['iso']['sha256'],
        changed_game_files=[EBOOT,EFF],archive_isolation=isolation)
    write_json(OUTPUT/'build.json',report)
    write_json(PROOF,dict(schema=1,version=VERSION,parent_version='0.5.53',
        build_sha256=sha256_file(OUTPUT/'build.json'),parent_delivery_sha256=sha256_file(ROOT/'work/ui/local_release_0.5.53.json'),
        diagnostic=state['diagnostic'],native_execution=state['checks'],self_checks=wrapper,
        title_archive_isolation=isolation,preview=artwork,changed_game_files=[EBOOT,EFF],
        unchanged_game_files=80,original_trophies_preserved=True,fonts_and_audio_unchanged=True,
        hardware_verified=False,runtime_verified=False))


def inventory():
    build,seal,parent52=parent()
    manifest=load(ROOT/'work/tengoku/source_manifest.json')
    replacements={path:B.OUTPUT/name for path,name in parent52['iso']['replaced'].items()}
    replacements[T.T.DISC]=T.OUTPUT/'TROPHY.TRP'
    rows=I.expected_files(replacements,manifest['files'])
    return [dict(path=r['path'],size=r['bytes'],sha256=r['sha256']) for r in rows.values()],seal


def image(apply):
    build=load(OUTPUT/'build.json')
    proof=load(PROOF)
    if sha256_file(OUTPUT/'build.json')!=proof['build_sha256']:raise ValueError('Diagnostic build changed')
    for name,digest in build['outputs'].items():
        if sha256_file(OUTPUT/name)!=digest:raise ValueError('Diagnostic output changed: '+name)
    rows,seal=inventory()
    replacements={EBOOT:OUTPUT/'EBOOT.BIN',EFF:OUTPUT/'EFFPS3.CPK'}
    if EFF not in {r['path'] for r in rows}:raise ValueError('Incorrect title archive path')
    print('Target:',IMAGE,'; two changed logical files; all 82 will be verified in both trees.',flush=True)
    if apply:
        if sha256_file(T.IMAGE)!=seal['iso']['sha256']:raise ValueError('0.5.53 source image changed')
        IMAGE.parent.mkdir(parents=True,exist_ok=True)
        result=I.write(T.IMAGE,IMAGE,replacements,rows)
        result.update(version=VERSION,parent_version='0.5.53',source_iso_sha256=seal['iso']['sha256'],
            changed_game_files=sorted(replacements),hardware_verified=False,runtime_verified=False)
        proof['iso_verification']=result
        write_json(PROOF,proof)
        write_json(IMAGE.with_suffix('.json'),result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('build','iso'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.action=='build':
        state=plan()
        if args.apply:build(state)
    else:image(args.apply)
    if not args.apply:print('DRY RUN: no assets written. No installation or publication.')


if __name__=='__main__':main()
