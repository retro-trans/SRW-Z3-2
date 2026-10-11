"""Verify Focus/Foc and native outlined font masks in the final test build."""
import argparse
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from tools.common import ROOT,sha256_file,write_json
from tools import ui_catalog,ui_hook,eboot_text,ui_build,ui_vwf_build,focus_terminology


def verify(version):
    from tools.verify_briefing_levelup import verify as previous
    from tools.pipeline import config,verified_source
    from tools.inventory import FONT
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    from tools.cpk import CPK
    from tools import library_build
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    elf=(folder/'EBOOT.BIN').read_bytes();read=ui_hook._reader(elf,ui_hook._headers(elf)[2])
    h=build['executable']['ui_hook'];runner=ui_hook._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    if focus_terminology.plan():raise ValueError('Active UI Focus terminology remains stale')
    if any(focus_terminology.MORALE.search(r['en'])for r in ui_catalog.translations().values()):
        raise ValueError('Morale remains in the active UI catalogue')
    settings=config(ROOT/'config/tengoku.json');source=member(verified_source(settings,ARCHIVE))
    with CPK(folder/'AIDDATAPACK.CPK')as a:built= a.read(next(e for e in a.files if e['id']==0))
    grow=len(built)-len(source)
    by_widget={at:r for r in ui_catalog.fssa_strings(built,decode=lambda raw:library_build.decode(raw,mapping))
               for at in r['widget_offsets']}
    expected=eboot_text.encode('Foc',mapping);stats=[]
    for row in ui_catalog.fssa_strings(source):
        if row['text']!='気力':continue
        for at in row['widget_offsets']:
            raw=by_widget[at+grow]['raw']
            if raw!=expected:
                pointer,_=runner.run(raw+b'\0')
                if read(pointer,len(expected)+1)!=expected+b'\0':raise ValueError('Final stat widget does not display Foc')
            stats.append(at)
    if len(stats)!=23:raise ValueError('Focus widget inventory changed')
    if by_widget[0x8f864+grow]['raw']!=eboot_text.encode('Eff.',mapping):raise ValueError('Effect caption remains crowded')
    fonts=[];references=[]
    with CPK(verified_source(settings,FONT))as original,CPK(folder/'TPACKPS3.CPK')as final:
        for mid in (1,3):
            before=original.read(next(e for e in original.files if e['id']==mid))
            after=final.read(next(e for e in final.files if e['id']==mid))
            a=ui_build.atlas(before);b=ui_build.atlas(after);restored=b.copy()
            outlined=0
            for token,code in mapping.items():
                x,y=ui_build.cell_xy(code);glyph,width=ui_vwf_build.raster(token)
                pixels=b[y:y+32,x:x+32]
                if not np.array_equal(pixels&255,np.asarray(glyph)):
                    raise ValueError('Final glyph fill differs from Z3 font shape')
                if not np.array_equal(pixels,ui_build.glyph_pixels(glyph)):
                    raise ValueError('Final native outline mask differs')
                if np.any(((pixels>>8)>0)&((pixels&255)==0)):outlined+=1
                restored[y:y+32,x:x+32]=a[y:y+32,x:x+32]
            if after[:128]!=before[:128]or not np.array_equal(restored,a):
                raise ValueError('Font cells outside the new allocation changed')
            for c in 'ＬｖＳＰ':
                x,y=ui_build.cell_xy(c.encode('cp932').hex());g=a[y:y+32,x:x+32]
                if not np.array_equal(g,b[y:y+32,x:x+32]):raise ValueError('Native Lv/SP glyph changed')
                high,low=g>>8,g&255
                if not np.all(high>=low)or not np.any((high>0)&(low==0)):
                    raise ValueError('Native Lv/SP two-mask reference changed')
                references.append(dict(page=mid,char=c,outline_only_pixels=int(np.count_nonzero((high>0)&(low==0)))))
            fonts.append(dict(page=mid,cells=len(mapping),outlined_cells=outlined,other_cells_unchanged=True))
    src=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-40e1e023-eaac-4cc2-b314-2d2dd75ded52.png')
    dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-focus-style.png')
    if not src.exists():src=dest
    with Image.open(src)as im:size=list(im.size)
    return dict(schema=1,version=version,focus_widgets=stats,stat_label='Foc',description_term='Focus',
        font_masks=fonts,native_reference=references,fill_and_advances_unchanged=True,
        prior_verification=prior,iso_verification=prior['iso_verification'],runtime_verified=False,
        screenshot=dict(source=str(src),saved_path=str(dest),pixel_size=size,sha256=sha256_file(src)),
        source_sha256={p:sha256_file(ROOT/p)for p in ('tools/ui_build.py','tools/latin_font.py',
            'tools/focus_terminology.py','tools/verify_focus_style.py','tests/test_focus_style.py',
            'work/glossary/ui_stats.json')})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.14')
    ap.add_argument('--apply',action='store_true');args=ap.parse_args();data=verify(args.version)
    print('Foc widgets:',len(data['focus_widgets']));print('Native font masks:',data['font_masks'])
    print('ISO:',data['iso_verification'])
    if args.apply:
        s=data['screenshot'];dest=Path(s['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists()and sha256_file(dest)!=s['sha256']:raise ValueError('Screenshot collision')
        if Path(s['source'])!=dest:shutil.copyfile(s['source'],dest)
        write_json(ROOT/'work/ui'/('focus_style_'+args.version+'.json'),data)
    else:print('DRY RUN: no screenshot or evidence written.')


if __name__=='__main__':main()
