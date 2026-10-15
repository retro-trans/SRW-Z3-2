"""Compare actual atlas masks, without changing the user's screenshots."""
import argparse
import json
from tools.common import ROOT
from tools import ui_build as F, ui_vwf_build as W, native_labels as N
from tools.review38_build import BASE

DEST=ROOT/'work/ui/fonts/0.5.38-font-comparison.png'


def render():
    import numpy as np
    from PIL import Image,ImageDraw,ImageFont
    build=json.loads((BASE/'build.json').read_text('utf8'))
    old=F.atlas((BASE/'font_1.bin').read_bytes())
    img=Image.new('RGB',(1200,530),'#15332b');draw=ImageDraw.Draw(img)
    label=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    rows=[('Previous ordinary text','All units, take your positions.',False,True),
          ('New ordinary text: same lettering, no added outline','All units, take your positions.',False,False),
          ('Original native glyphs: separate yellow labels','Team   Mech   PP   Next-Lv   Kills',True,False),
          ('New ordinary names and numbers','Nahel Argama   120   500   0',False,False)]
    for i,(caption,text,native,previous) in enumerate(rows):
        y=20+i*125;draw.text((22,y),caption,font=label,fill='#bcddd4');x=22
        for char in text:
            token=N.PREFIX+char if native else char
            glyph,advance=W.raster(token)
            if previous:
                cx,cy=F.cell_xy(build['mapping'][token]);pixels=old[cy:cy+32,cx:cx+32]
            else:pixels=F.glyph_pixels(glyph)
            low=(pixels&255).astype('uint8');high=(pixels>>8).astype('uint8')
            mask=Image.fromarray(high).resize((48,48),Image.Resampling.BILINEAR)
            ink=Image.fromarray(low).resize((48,48),Image.Resampling.BILINEAR)
            img.paste('#000000',(round(x),y+36),mask)
            img.paste('#eddf55' if native else '#ffffff',(round(x),y+36),ink)
            x+=advance*1.5
    return img


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    preview=render();print('Four mask comparisons:',preview.size,'->',DEST)
    if args.apply:DEST.parent.mkdir(parents=True,exist_ok=True);preview.save(DEST)
    else:print('DRY RUN: no preview written.')


if __name__=='__main__':main()
