"""Execute every narration binding in the final build and verify original timing."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import ui_hook as H, eboot_text as E, ppc_exec as P
from tools import narration_catalog as N, ui_catalog as U
from tools.opening_narration import profile
from tools.ui_description_layout import advance, condensed_advance

SHOTS = ('e1d49cd3-8a43-4f46-a986-be88ab67796c',
    '9a5adfbb-8911-4b67-a5db-10b8b3d95a6b',
    'c1da51c6-e522-4204-adcb-9ea575031b63',
    'a94c0449-f988-493a-858b-8d91489f6f71')


def centered_cases(elf, captions):
    mem = P.Memory()
    phs = H._headers(elf)[2]
    for seg in phs[:2]:
        mem.map(seg[3], elf[seg[2]:seg[2]+seg[5]], writable=seg==phs[1])
    mem.map(0x40000000, bytes(0x4000))
    mem.map(0x41000000, bytes(0x2000))
    mem.map(0x42000000, bytes(0x200))
    mem.write(H.TOC+H.STATE_DISP, struct.pack('>I',0x41000000))
    cases = []
    for row, width in captions:
        mem.write(0x42000000, row['raw']+b'\0')
        for quad in (28,40):
            for mode in (0,1):
                mem.write(0x41000000, bytes(0x2000))
                mem.write(0x41000054, struct.pack('>f',quad))
                mem.write(0x410000ac, struct.pack('>H',mode))
                m = P.Machine(mem)
                m.r[1]=0x40003f00; m.r[2]=H.TOC; m.r[3]=0x42000000
                m.r[7]=1; m.r[8]=0
                m.f[1]=640.; m.f[2]=360.; m.f[3]=1.; m.lr=0x152000
                m.pc=0x149bc
                m.run({0x14a68,0x14a2c,0x14ac4},limit=50000)
                actual_width=width*quad/32
                if m.pc!=0x14a68 or abs(m.f[1]+actual_width/2-640.)>.0001:
                    raise ValueError('Narration uses native Japanese width instead of English: '+row['id'])
                if m.f[1]<0 or m.f[1]+actual_width>1280:
                    raise ValueError('Centered narration exceeds the screen')
                if m.f[30]!=360. or m.f[31]!=1. or m.r[31]!=0x42000000:
                    raise ValueError('Narration caller state changed')
                cases.append(dict(id=row['id'],quad=quad,mode=mode,left=m.f[1],width=actual_width,center=640.))
    return cases


def verify(version):
    from tools.verify_ui_review import verify as previous
    from tools.pipeline import config, verified_source
    from tools.aid_art import ARCHIVE
    from tools.cpk import CPK
    prior = previous(version)
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text(encoding='utf-8'))
    mapping = build['mapping']
    elf = (folder/'EBOOT.BIN').read_bytes()
    read = H._reader(elf,H._headers(elf)[2])
    hook = build['executable']['ui_hook']
    runner = H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
    with CPK(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE)) as original, CPK(folder/'AIDDATAPACK.CPK') as final:
        rows = N.sources(original)
        a = {e['id']:e for e in original.files}
        b = {e['id']:e for e in final.files}
        for mid in {r['member'] for r in rows}:
            if original.read(a[mid])!=final.read(b[mid]):
                raise ValueError('Narration text, page order or timing bytes changed: %d'%mid)
    english = U.translations()
    captions = []
    reported = []
    for row in rows:
        rid = sha256(row['text'].encode('utf-8'))[:20]
        en, condensed = profile(english[rid]['en'])
        active_mapping = mapping
        if condensed:
            from tools.dialogue_layout import PREFIX
            active_mapping = dict(mapping)
            active_mapping.update({token[len(PREFIX):]:code for token,code in mapping.items() if token.startswith(PREFIX)})
        expected = E.encode(en,active_mapping)
        pointer, steps = runner.run(row['raw']+b'\0')
        if pointer==0x50000000 or read(pointer,len(expected)+1)!=expected+b'\0':
            raise ValueError('Narration has no correct final English binding: '+row['id'])
        width = sum(map(condensed_advance if condensed else advance,en))
        captions.append(dict(id=row['id'],member=row['member'],record=row['record'],page=row['page'],
            translation_id=rid,en=en,condensed=condensed,units=width,steps=steps))
        if row['id'] in ('aid:20:19a','aid:20:4f4','aid:21:14','aid:22:14'):
            reported.append((row,width))
    shots = []
    from PIL import Image
    for index,ident in enumerate(SHOTS,1):
        source = Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest = ROOT/'work/ui/screenshots'/('reported-'+version+'-narration-%d.png'%index)
        if not source.exists(): source=dest
        with Image.open(source) as im: size=list(im.size)
        shots.append(dict(source=str(source),saved_path=str(dest),pixel_size=size,sha256=sha256_file(source)))
    return dict(schema=1,version=version,captions_executed=len(captions),unique_captions=len({r['translation_id'] for r in captions}),
        narration_members_unchanged=sorted({r['member'] for r in rows}),
        native_center_cases=centered_cases(elf,reported),rows=captions,screenshots=shots,
        prior_verification=prior,iso_verification=prior['iso_verification'],runtime_verified=False,
        input_sha256={p:sha256_file(ROOT/p) for p in ('tools/narration_catalog.py','tools/narration_translation.py',
            'tools/ui_catalog.py','tools/verify_narration.py','tests/test_narration_catalog.py',
            'work/ui/narration_catalog.json','work/translation/en/ui/expanded/narration.json')})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.5.16'); ap.add_argument('--apply',action='store_true')
    args=ap.parse_args(); report=verify(args.version)
    print('Narration bindings executed:',report['captions_executed'])
    print('Unchanged narration members:',len(report['narration_members_unchanged']))
    print('Native centered draw cases:',len(report['native_center_cases']))
    print('ISO:',report['iso_verification'])
    if args.apply:
        for shot in report['screenshots']:
            dest=Path(shot['saved_path']); dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and sha256_file(dest)!=shot['sha256']: raise ValueError('Screenshot collision')
            if Path(shot['source'])!=dest: shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('narration_verified_'+args.version+'.json'),report)
    else: print('DRY RUN: no screenshots or verification evidence written.')


if __name__=='__main__': main()
