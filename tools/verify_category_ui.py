"""Execute the final category bindings and measure unchanged native stat slots."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from PIL import Image
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import category_ui as C,ui_hook as H,eboot_text as E,ui_catalog as U,library_build as L
from tools.ui_description_layout import advance

SHOTS=(('stage-heading','5d7db515-7e4e-4623-b359-02930ff80d61'),
       ('unit-stats','af3112c6-7db6-437d-8d40-79aeddfb3104'),
       ('map-terrain','4f11d99e-d4fc-47c2-aead-871e23eed679'),
       ('spirit-target','21870c60-5c45-4cc4-b387-e24054b0e80e'),
       ('training','dd753387-e27e-4690-921a-c702992ead25'))


def verify(version):
    from tools.verify_narration import verify as previous
    from tools.cpk import CPK
    from tools import operation_layout as O
    prior=previous(version)
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes()
    read=H._reader(elf,H._headers(elf)[2]);h=build['executable']['ui_hook']
    runner=H._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    bindings=[]
    for row in C.hook_entries(H.PREPARED.read_bytes(),mapping):
        ptr,steps=runner.run(row['key']+b'\0')
        if read(ptr,len(row['english'])+1)!=row['english']+b'\0':
            raise ValueError('Final category lookup differs: '+row['id'])
        bindings.append(dict(id=row['id'],key_sha256=sha256(row['key']),steps=steps,
                             en=L.decode(row['english'],mapping)))
    # These dynamically selected first-column labels do not have a fixed
    # FSSA string pointer. Check their final hook values as well.
    dynamic=[]
    for jp,en in (('格闘','CQB'),('射撃','RNG')):
        raw=H.utf8_key(jp.encode('utf8'),H.PREPARED.read_bytes())
        ptr,steps=runner.run(raw+b'\0');expected=E.encode(en,mapping)
        if read(ptr,len(expected)+1)!=expected+b'\0':
            raise ValueError('First stat column differs: '+jp)
        width=sum(map(advance,en))*28/32
        # The actual outer ink reaches the same right edge as the advance
        # for CQB/RNG. Require two units of clearance, not another four-unit
        # outline already included in the native two-mask glyph.
        if width+2>=65:raise ValueError('First stat column intrudes into value')
        dynamic.append(dict(en=en,width=width,steps=steps))
    source=C.B.source();plan=C.plan()
    originals={at:r for r in U.fssa_strings(source)for at in r['widget_offsets']}
    if json.loads(C.DEST.read_text(encoding='utf8'))!=plan:raise ValueError('Stale category data')
    with CPK(folder/'AIDDATAPACK.CPK')as a:
        final=a.read(next(e for e in a.files if e['id']==0))
    grow=len(final)-len(source)
    widgets={at:r for r in U.fssa_strings(final,decode=lambda b:L.decode(b,mapping))for at in r['widget_offsets']}
    columns=[]
    for row in plan['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['raw']!=E.encode(row['en'],mapping):raise ValueError('Final category widget text differs')
        if final[target+4:target+16]!=source[at+4:at+16]or final[target+21:target+32]!=source[at+21:at+32]:
            raise ValueError('Native value positions, row pitch or flags changed')
        if 'font_metrics'in row:
            if final[target+16:target+21]!=bytes(row['font_metrics']):raise ValueError('Final label metrics differ')
            widths=[sum(map(advance,line))*row['font_metrics'][3]/32 for line in row['en'].split('\n')]
            budget=(len(originals[at]['text'].split('\n')[0])*source[at+20]
                    if at in (0x9d824,0x9d844,0x9d864)else 65)
            if max(widths)+4>=budget:raise ValueError('Final stat label intrudes into a value')
            columns.append(dict(widget_offset=at,en=row.get('display_labels',row['en']),widths=widths,value_start=budget,
                                original_xy=row['source_xy'],row_pitch=source[at+21]))
    targets=C.assembled_targets(H.PREPARED.read_bytes())
    for label in targets.values():
        if sum(map(advance,label))*28/32+4>=150:raise ValueError('Target caption exceeds its field')
    screenshots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src=dst
        with Image.open(src)as im:size=list(im.size)
        screenshots.append(dict(issue=label,source=str(src),saved_path=str(dst),pixel_size=size,
                                sha256=sha256_file(src),runtime_confirmation=False))
    stages=O.episodes(H.PREPARED.read_bytes())
    return dict(schema=1,version=version,stage_titles=len(stages),stage_records=sum(map(len,stages.values())),
        terrain_names=len(C.terrain_rows()),map_attribute_members=128,target_combinations=targets,
        executed_category_bindings=bindings,dynamic_stat_columns=dynamic,stat_columns=columns,
        all_focus_widgets=23,terrain_cap_height=16,terrain_advance=32,screenshots=screenshots,
        prior_verification=prior,iso_verification=prior['iso_verification'],runtime_verified=False,
        input_sha256={p:sha256_file(ROOT/p)for p in ('tools/category_ui.py','tools/operation_layout.py',
            'tools/status_layout.py','tools/battle_layout.py','tools/ui_layout_text.py','tools/verify_category_ui.py',
            'tests/test_category_ui.py','work/translation/en/ui/category_layout.json',
            'work/translation/en/ui/terrain_names.json','work/ui/terrain_catalog.json')})


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.5.17');ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=verify(args.version)
    print('Stage variants:',data['stage_titles'],'Terrain names:',data['terrain_names'],
          'Category lookups:',len(data['executed_category_bindings']))
    print('Stat columns:',data['stat_columns']);print('ISO:',data['iso_verification'])
    if args.apply:
        for row in data['screenshots']:
            dest=Path(row['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists()and sha256_file(dest)!=row['sha256']:raise ValueError('Screenshot collision')
            if Path(row['source'])!=dest:shutil.copyfile(row['source'],dest)
        write_json(ROOT/'work/ui'/('category_ui_verified_'+args.version+'.json'),data)
    else:print('DRY RUN: no screenshots or evidence written.')


if __name__=='__main__':main()
