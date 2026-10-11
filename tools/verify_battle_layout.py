"""Read back battle UI repairs and preserve the five reported screenshots."""
import argparse
import json
import shutil
from pathlib import Path
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import battle_layout as bl,ui_hook

SHOTS=(('battle-preview','4c5e586c-888c-4e6d-b615-8f930dc4027c',(62,80,2435,1250)),
       ('map-popup','77ac1154-d07e-4144-b87a-4b430f014b2d',(62,160,2435,1190)),
       ('battle-result','33e6a7bb-f9f8-4faa-b9d6-50efb659ace4',(245,485,2090,445)),
       ('fast-forward','5e6ca61c-28c4-417e-bc18-a66e50a68bff',(825,918,910,100)),
       ('transform','e4bca260-05ca-4f47-a33d-527d31964ace',(659,397,1240,774)))


def verify(version):
    from tools.verify_status_layout import verify as status
    from tools.cpk import CPK
    from tools.ui_build import atlas,cell_xy
    from tools.ui_vwf_build import raster
    from tools.ui_description_layout import advance
    from PIL import Image
    import numpy as np
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    legacy=status(version)
    elf=(folder/'EBOOT.BIN').read_bytes();read=ui_hook._reader(elf,ui_hook._headers(elf)[2])
    mapping=build['mapping'];hook=build['executable']['ui_hook']
    runner=ui_hook._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
    entries=bl.hook_entries(ui_hook.PREPARED.read_bytes(),mapping)
    for e in entries:
        pointer,_=runner.run(e['key']+b'\0')
        if read(pointer,len(e['english'])+1)!=e['english']+b'\0':raise ValueError('Battle dictionary readback failed')
    table=ui_hook.unicode_table(elf);glyphs=[]
    with CPK(folder/'TPACKPS3.CPK')as archive:
        pages={e['id']:atlas(archive.read(e))for e in archive.files if e['id']in(1,3)}
    for token,word in bl.TINY.items():
        if ui_hook.convert(token.encode('utf8'),table)!=bytes.fromhex(mapping[token]):raise ValueError('Flag converter differs')
        glyph,width=raster(token);x,y=cell_xy(mapping[token])
        from tools.ui_build import glyph_pixels
        expected=glyph_pixels(glyph)
        if width!=32 or read(build['executable']['table_va']+y//32*128+x//32,1)!=b' ':raise ValueError('Flag native pitch differs')
        for page in pages.values():
            if not np.array_equal(page[y:y+32,x:x+32],expected):raise ValueError('Final flag ink differs')
        glyphs.append(dict(token=token,label=word,code=mapping[token],advance=32,ink_box=glyph.getbbox()))
    plan=json.loads(bl.DEST.read_text(encoding='utf8'))
    if plan!=bl.plan():raise ValueError('Battle layout data is stale')
    shots=[]
    for label,ident,box in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src=dest
        with Image.open(src)as img:size=list(img.size)
        shots.append(dict(issue=label,source=str(src),saved_path=str(dest),sha256=sha256_file(src),
            pixel_size=size,observed_region=dict(x=box[0],y=box[1],width=box[2],height=box[3],
                approximate=True),runtime_confirmation=False))
    widths=[]
    source=bl.source()
    for edit in plan['edits']:
        quad=edit.get('font_metrics',list(source[edit['widget_offset']+16:edit['widget_offset']+21]))[3]
        widths.append(dict(widget_offset=edit['widget_offset'],en=edit['en'],quad=quad,
            source_xy=edit['source_xy'],original_widget_hex=source[edit['widget_offset']:edit['widget_offset']+32].hex(),
            font_metrics=edit.get('font_metrics',list(source[edit['widget_offset']+16:edit['widget_offset']+21])),
            widths=[sum(map(advance,line))*quad/32 for line in edit['en'].split('\n')]))
    return dict(schema=1,version=version,matched_files=len(build['outputs']),final_elf_sha256=sha256(elf),
        widgets=len(plan['edits']),compact_flag_cells=glyphs,dictionary_cases=len(entries),
        terrain=plan['terrain'],caption_widths=widths,screenshots=shots,prior_status_verification=legacy,
        source_sha256={f:sha256_file(ROOT/f)for f in ('tools/battle_layout.py','tools/verify_battle_layout.py',
            'tests/test_battle_layout.py','tools/ui_layout_text.py','work/translation/en/ui/battle_layout.json')},
        iso_verification=legacy['iso_verification'],runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.9')
    ap.add_argument('--apply',action='store_true');args=ap.parse_args();data=verify(args.version)
    print('Verified battle widgets:',data['widgets'],'flag cells:',len(data['compact_flag_cells']),
        'dictionary cases:',data['dictionary_cases'],'matched files:',data['matched_files'])
    print('Terrain:',data['terrain'])
    for row in data['caption_widths']:print(hex(row['widget_offset']),repr(row['en']),row['widths'])
    if args.apply:
        for shot in data['screenshots']:
            dest=Path(shot['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and sha256_file(dest)!=shot['sha256']:raise ValueError('Screenshot collision')
            if Path(shot['source'])!=dest:shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('battle_layout_'+args.version+'.json'),data)
    else:print('DRY RUN: no evidence or screenshots written.')

if __name__=='__main__':main()
