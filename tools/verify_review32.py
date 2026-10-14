"""Read back scene/news centering, Sub Order guides and early save translation."""
import argparse,json,struct,shutil
from pathlib import Path
from collections import Counter
from tools.common import ROOT,sha256_file,write_json
from tools import review32_content as C,review32_save as S,review32_layout as A
from tools import ui_hook as H,dialogue_build as D,library_build as L,ui_catalog as U,battle_layout as B
from tools.cpk import CPK
SHOTS=(('Back-Log','57704784-5195-4a33-9e70-04e897c1c0b1'),('Sub-Order','26704e20-08ed-4175-9d4c-9df0f82c1ac6'),
       ('headline','abff3ee3-c556-4c3c-ba0d-62f8f0bf00af'),('save','e0371241-3757-4dbe-a6d1-8a3ae070427f'),
       ('movement','eaa99a32-a71c-4fc5-af51-93b5debc735c'))


def verify(version):
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'))
    mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2])
    cases=C.origin_cases(elf,mapping,build['executable']['link_layout'])
    if len(cases)!=539:raise ValueError('Incomplete location/news coverage')
    info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    for row in C.hook_entries(H.PREPARED.read_bytes(),mapping):
        pointer,_=runner.run(row['key']+b'\0')
        if read(pointer,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Final news headline differs')
    source=B.source()
    with CPK(folder/'AIDDATAPACK.CPK')as arc:final=arc.read(next(r for r in arc.files if r['id']==0))
    grow=len(final)-len(source);widgets={at:r for r in U.fssa_strings(final,lambda raw:raw.hex())for at in r['widget_offsets']}
    from tools.menu_layout import encode
    for row in A.plan()['edits']:
        at=row['widget_offset'];to=at+grow
        if widgets[to]['raw']!=encode(row,mapping):raise ValueError('Final Sub Order/guide caption differs')
        expected=bytearray(source[at+4:at+32])
        if 'x'in row:struct.pack_into('>f',expected,0,row['x'])
        if final[to+4:to+32]!=expected:raise ValueError('Guide changes unrelated widget state')
    oracle=H.ConverterOracle(elf);save=[]
    for row in build['executable']['save_questions']['rows']:
        pointer=struct.unpack('>I',read(row['pointer_va'],4))[0]
        carrier=read(pointer,row['carrier_bytes'])
        if carrier[-1:]!=b'\0':raise ValueError('Save carrier is unterminated')
        lines,steps=S.native_lines(elf,carrier[:-1]);models=[]
        for line,english in zip(lines,row['english'].split('\n')):
            from tools.eboot_text import encode as english_bytes
            expected=english_bytes(english,mapping)
            for model in ('A','B'):
                converted,fill,n=oracle.run(line,model)
                if converted[:len(expected)+2]!=expected+b'\0\0' or any(v!=fill for v in converted[len(expected)+2:]):
                    raise ValueError('Native save converter clips an English paragraph')
                models.append(dict(model=model,steps=n))
        save.append(dict(source_va=row['source_va'],english=row['english'],native_steps=steps,converter_cases=models))
    from tools.ui_description_layout import advance
    rendered=D.plan(advance);by_member={};caption_count=0
    for rid,text in rendered.items():
        if C.caption(text) is None:continue
        encoded=D.encode(text,mapping);mid=int(rid.split(':')[0]);by_member.setdefault(mid,Counter())[encoded]+=1;caption_count+=1
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        index={r['id']:r for r in arc.files}
        for mid,expected in by_member.items():
            raw=arc.read(index[mid])
            if any(raw.count(encoded)<count for encoded,count in expected.items()):
                raise ValueError('Final scene-caption member omits centered content')
    if caption_count!=517:raise ValueError('Final scene-caption coverage differs')
    print('517 scene captions, 11 two-line headlines, 539 native origin cases, 11 widgets and all save paragraphs passed.',flush=True)
    from tools.verify_review31 import verify as previous
    prior=previous(version);shots=[]
    for label,identifier in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+identifier+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-review32-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,previous_public_version='0.5.28',prior_verification=prior,
                iso_verification=prior['iso_verification'],origin_cases=cases,caption_records=caption_count,
                headline_profiles=[{k:v for k,v in r.items()if k!='jp'}for r in C.headlines()],layout=A.plan(),save_questions=save,
                screenshots=shots,runtime_verified=False)


def main():
    from tools.game_build import VERSION
    ap=argparse.ArgumentParser();ap.add_argument('--version',default=VERSION);ap.add_argument('--apply',action='store_true')
    ap.add_argument('--preview',action='store_true');a=ap.parse_args()
    if a.preview:print('Preview: all marked captions/headlines, fixed guides/counters, native save paragraphs, movement masks and carried checks. DRY RUN: no evidence written.');return
    data=verify(a.version);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        src=Path(shot['source']);dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot differs')
        if src!=dst:shutil.copyfile(src,dst)
    write_json(ROOT/'work/ui'/('review32_verified_'+a.version+'.json'),data)


if __name__=='__main__':main()
