"""Preview native Lv/SP versus new outlined Rodin labels; not a game capture."""
import argparse
import numpy as np
from PIL import Image,ImageDraw
from tools.common import ROOT
from tools import ui_build,ui_vwf_build

DEST=ROOT/'work/ui/font/focus-outline-preview-0.5.14.png'


def preview():
    from tools.pipeline import config,verified_source
    from tools.inventory import FONT
    from tools.cpk import CPK
    with CPK(verified_source(config(ROOT/'config/tengoku.json'),FONT))as archive:
        atlas=ui_build.atlas(archive.read(next(e for e in archive.files if e['id']==1)))
    image=Image.new('RGB',(560,200),'#929e9e');draw=ImageDraw.Draw(image)
    draw.text((14,10),'Native Lv / SP masks',fill='black')
    draw.text((14,100),'Outlined Rodin: Foc / Eff. / Tgt. / Dur.',fill='black')
    for y,words,native in ((38,('Ｌｖ','ＳＰ'),True),(128,('Foc','Eff.','Tgt.','Dur.'),False)):
        x=14
        for word in words:
            for char in word:
                if native:
                    xx,yy=ui_build.cell_xy(char.encode('cp932').hex());pixels=atlas[yy:yy+32,xx:xx+32];advance=32
                else:
                    glyph,advance=ui_vwf_build.raster(char);pixels=ui_build.glyph_pixels(glyph)
                outer=(pixels>>8).astype('float32');fill=(pixels&255).astype('float32')
                rgba=np.zeros((32,32,4),dtype='uint8')
                for n,c in enumerate((230,214,64)):rgba[...,n]=np.round(c*fill/np.maximum(outer,1)).astype('uint8')
                rgba[...,3]=outer.astype('uint8')
                cell=Image.fromarray(rgba).resize((48,48),Image.Resampling.NEAREST)
                image.paste(cell,(round(x),y),cell);x+=advance*1.5
            x+=26
    return image


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();im=preview();print('Font-mask simulation:',DEST,im.size)
    if args.apply:DEST.parent.mkdir(parents=True,exist_ok=True);im.save(DEST)
    else:print('DRY RUN: no preview written.')


if __name__=='__main__':main()
