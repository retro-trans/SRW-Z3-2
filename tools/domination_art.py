"""Translate the domination caption without changing animated numbers."""
import argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tools import gtf,eff_art
from tools.common import ROOT,sha256
from tools.ui_build import FACE

MEMBER=239
SOURCE_SHA='e1d10a0523179d14ed6319d3e65c8a7182c1382c84298840402fd5753459f419'
RECT=(0,64,200,32)
TEXT='New Earth Empire Control'


def render(raw):
    if sha256(raw)!=SOURCE_SHA:raise ValueError('Domination HUD source changed')
    tex=next(t for t in gtf.textures(raw)if t['index']==1)
    if (tex['width'],tex['height'],tex['fmt'])!=(512,128,133):
        raise ValueError('Domination HUD atlas differs')
    # This caption is progressively revealed; ten final keyframes sample
    # the 312-wide label/dot/percent row. Number sprites use the next row.
    records=eff_art.rect_records(raw,0x101,(0,64,312,32))
    if len(records)!=10:raise ValueError('Domination HUD final animation records differ')
    before=gtf.decode(raw,tex);pixels=before.copy()
    font=ImageFont.truetype(str(FACE),25)
    l,t,r,b=font.getbbox(TEXT)
    ink=Image.new('RGBA',(r-l+4,b-t+4))
    ImageDraw.Draw(ink).text((2-l,2-t),TEXT,font=font,fill=(174,196,241,255))
    # The first live percentage digit occupies x=208; keep an eight-texel
    # gap after the caption, including transparent outline margins.
    scale=min(1,196/ink.width,22/ink.height)
    ink=ink.resize((round(ink.width*scale),round(ink.height*scale)),Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',(200,32));tile.alpha_composite(ink,(2,(32-ink.height)//2))
    x,y,w,h=RECT;pixels[y:y+h,x:x+w]=np.array(tile)
    out=gtf.replace(raw,tex,pixels)
    # Every dot, percent sign, digit, bar, vertex and animation record must
    # remain identical. Restore only the caption rectangle and compare.
    for original in gtf.textures(raw):
        built=next(t for t in gtf.textures(out)if t['index']==original['index'])
        a=gtf.decode(raw,original);b=gtf.decode(out,built)
        if original['index']==1:b[y:y+h,x:x+w]=a[y:y+h,x:x+w]
        if not np.array_equal(a,b):raise ValueError('HUD edit escaped caption rectangle')
    key=(tex['gtf'],tex['index'])
    eff_art.verify_member(raw,out,{key:pixels},{})
    return out,{key:pixels},{},dict(text=TEXT,rectangle=RECT,animation_records_preserved=len(records),
        percentage_digits_unchanged=True,source_sha256=sha256(raw),output_sha256=sha256(out),runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    raw=eff_art.source_members(eff_art._settings(),[MEMBER],{MEMBER:SOURCE_SHA})[MEMBER]
    out,_,_,report=render(raw);print(report)
    if not args.apply:print('DRY RUN: no preview written.');return
    tex=next(t for t in gtf.textures(raw)if t['index']==1)
    sheet=Image.new('RGBA',(1024,158),(20,30,40,255))
    ImageDraw.Draw(sheet).text((8,8),'Original | English native atlas preview (not in-game)',fill='white')
    sheet.alpha_composite(Image.fromarray(gtf.decode(raw,tex)),(0,30))
    sheet.alpha_composite(Image.fromarray(gtf.decode(out,tex)),(512,30))
    path=ROOT/'work/ui/textures/effps3/domination-0.5.19.png'
    path.parent.mkdir(parents=True,exist_ok=True);sheet.convert('RGB').save(path)


if __name__=='__main__':main()
