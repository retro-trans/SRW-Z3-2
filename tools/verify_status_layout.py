"""Read back the testing build's status repairs; dry run before saving evidence."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT,sha256_file,sha256,write_json
from tools import status_layout as sl,ui_hook,ppc_exec as p,eboot_text

SHOTS=(('save-new','0d478949-3b3f-4e27-a8eb-b669e12bc23b',(208,497,2102,436)),
       ('unit-stats','c3acbd5b-e46b-4220-a58a-41398bf469d8',(504,249,1873,271)),
       ('pilot-stats','f04d40db-0ba4-4ec1-a094-db0933a6b806',(883,316,1515,601)),
       ('mech-stats','a145682e-f22e-489b-af47-ccbd1ed1ce85',(124,748,2320,507)),
       ('weapon-costs','a40d67c0-391f-490c-a252-fbf5950c168c',(132,223,2260,1031)),
       ('weapon-types','e78714cc-e4a1-4ab7-b328-b577725e9206',(127,223,2292,1038)))


def verify(version):
    from tools.verify_link_layout import verify as links
    from tools.cpk import CPK
    from tools.ui_build import atlas,cell_xy
    from tools.ui_vwf_build import raster
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    from tools import ui_layout_text,menu_layout
    import numpy as np
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    layout=links(version)
    elf=(folder/'EBOOT.BIN').read_bytes();phs=ui_hook._headers(elf)[2];read=ui_hook._reader(elf,phs)
    mapping=build['mapping'];specs=sl.save_specs(mapping)
    if specs!=build['executable']['link_layout']['save_center']:raise ValueError('Save marker plan drift')
    rows={r['id']:r for r in build['executable']['link_layout']['code']}
    hook=build['executable']['ui_hook'];runner=ui_hook._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
    entries=sl.hook_entries(ui_hook.PREPARED.read_bytes(),mapping)
    for entry in entries:
        pointer,_=runner.run(entry['key']+b'\0')
        if read(pointer,len(entry['english'])+1)!=entry['english']+b'\0':raise ValueError('Final status/name dictionary differs')
    centers=[]
    widths=read(build['executable']['table_va'],4480)
    for n,(jp,en) in enumerate(sl.CAPTIONS):
        entry=entries[n];raw=entry['english']
        codes=zip(raw[2::2],raw[3::2]);units=sum(widths[(a-0x81)*192+b-0x40]for a,b in codes)
        for quad in (25,28,31,36):
            mem=p.Memory()
            for seg in phs[:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=seg==phs[1])
            mem.map(0x40000000,bytes(0x3000));mem.map(0x41000000,bytes(0x100))
            mem.map(0x42000000,raw+b'\0',writable=False)
            mem.write(0x41000054,struct.pack('>f',quad))
            m=p.Machine(mem);m.r=[0x990000+i for i in range(32)];m.r[1]=0x40001800
            m.r[30]=0x41000000;m.r[31]=0x42000000;m.f=[i+.25 for i in range(32)]
            m.f[31]=639.5-len(jp)*quad/2;m.cr=0xb3c7a965;m.lr=0xdead00
            before=(m.r[:],m.f[:],m.cr,m.lr);m.pc=rows['drawer origin']['va']
            m.run({0x141ac},limit=10000)
            if abs(m.f[31]+units*quad/64-639.5)>.0001 or m.r[31]!=0x42000002:
                raise ValueError('Final split-save caption does not center')
            if any(m.r[r]!=before[0][r]for r in set(range(32))-{31}) or any(m.f[f]!=before[1][f]for f in set(range(32))-{31}) or (m.cr,m.lr)!=before[2:]:
                raise ValueError('Final split-save helper clobbers state')
            centers.append(dict(text=en,quad=quad,left=m.f[31],width=units*quad/32,center=639.5,steps=m.steps))
    final_table=ui_hook.unicode_table(elf)
    for token in sl.TINY:
        if ui_hook.convert(token.encode('utf8'),final_table)!=bytes.fromhex(mapping[token]):raise ValueError('Final compact Unicode mapping differs')
    for va in sl.MOVEMENT:
        for n,jp in enumerate('空陸水地'):
            if read(va+n*8,8)!=sl.TERRAIN[jp].encode('utf8')+bytes(5):raise ValueError('Final movement slot differs')
    for va,jp,en in sl.SPECIAL:
        if read(va,len(jp.encode('utf8'))+1)!=(en.encode('utf8')+b'\0').ljust(len(jp.encode('utf8'))+1,b'\0'):
            raise ValueError('Final restricted movement slot differs')
    glyph_rows=[]
    with CPK(folder/'TPACKPS3.CPK')as archive:
        pages={e['id']:atlas(archive.read(e))for e in archive.files if e['id']in(1,3)}
    for token in list(sl.TINY)+list(sl.MARKERS.values()):
        from tools.ui_build import glyph_pixels
        glyph,width=raster(token);x,y=cell_xy(mapping[token]);expected=glyph_pixels(glyph)
        if width!=32 or read(build['executable']['table_va']+y//32*128+x//32,1)!=b' ':raise ValueError('Compact glyph lost native pitch')
        for page in pages.values():
            if not np.array_equal(page[y:y+32,x:x+32],expected):raise ValueError('Final compact font ink differs')
        glyph_rows.append(dict(token=token,label=sl.TINY.get(token,''),code=mapping[token],advance=32,ink_box=glyph.getbbox()))
    shots=[]
    for label,ident,box in SHOTS:
        source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not source.exists():source=dest
        from PIL import Image
        with Image.open(source)as img:size=list(img.size)
        shots.append(dict(issue=label,source=str(source),saved_path=str(dest),sha256=sha256_file(source),
            pixel_size=size,observed_region=dict(x=box[0],y=box[1],width=box[2],height=box[3],approximate=True),runtime_confirmation=False))
    plan=json.loads(sl.DEST.read_text(encoding='utf8'))
    if plan!=sl.plan():raise ValueError('Final status plan is stale')
    iso_path=ROOT/('work/output/iso/%s/Tengoku-hen-English-%s.json'%(version,version))
    iso=json.loads(iso_path.read_text(encoding='utf8'))if iso_path.exists()else None
    if iso and (iso['version']!=version or iso['files_verified_each_tree']!=82):raise ValueError('ISO verification differs')
    return dict(schema=1,version=version,final_elf_sha256=sha256(elf),matched_files=layout['matched_files'],
        widgets=len(plan['edits']),status_dictionary_cases=len(entries),save_centers=centers,
        compact_cells=glyph_rows,movement_patch=build['executable']['status_layout'],screenshots=shots,
        all_legacy_layout_helpers_verified=layout['helpers_verified'],
        source_sha256={f:sha256_file(ROOT/f)for f in ('tools/status_layout.py','tools/verify_status_layout.py',
            'tests/test_status_layout.py','work/translation/en/ui/status_layout.json','work/translation/en/ui/aiddata_art.json')},
        iso_verification=iso,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.8');ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=verify(args.version)
    print('Verified:',data['matched_files'],'matched files;',data['widgets'],'widgets;',data['status_dictionary_cases'],'status/name dictionary cases.')
    for row in data['save_centers']:print(row)
    for row in data['compact_cells']:print(row['label'],row['code'],row['ink_box'])
    if args.apply:
        for shot in data['screenshots']:
            dest=Path(shot['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists()and sha256_file(dest)!=shot['sha256']:raise ValueError('Screenshot collision')
            if Path(shot['source'])!=dest:shutil.copyfile(shot['source'],dest)
        write_json(ROOT/('work/ui/status_layout_'+args.version+'.json'),data)
    else:print('DRY RUN: no evidence/screenshots written.')

if __name__=='__main__':main()
