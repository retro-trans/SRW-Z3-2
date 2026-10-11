"""Native scenario-chart labels; bounded atlas edits preserve animation."""
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
from tools import gtf
from tools.common import sha256
from tools.ui_build import FACE

SOURCES={234:'efe6330b88458cecac8c4123178c5d94666b692c9735e6ec56e3af884f7bfa8f',
235:'e83e5eeddf4d66667b895338f70103eb871baa06c501360b7900cf229d0b24f7',
236:'c98e889f34cf8f7ab708b18a2b8c95a62a56a552afb9f7da3a6fa1bc0575a096',
237:'336b5c86d1a24a156e13c94388b105b2ab43e769e735f09e55162bc7d9f00a10'}
HEADER=(112,12,432,68)
SUBTITLE=(128,176,1056,384)


def label(text,size,font_size,stroke=0):
    font=ImageFont.truetype(str(FACE),font_size)
    l,t,r,b=font.getbbox(text,stroke_width=stroke)
    ink=Image.new('RGBA',(r-l+8,b-t+8))
    ImageDraw.Draw(ink).text((4-l,4-t),text,font=font,fill='white',stroke_width=stroke,stroke_fill='black')
    scale=min(1,(size[0]-16)/ink.width,(size[1]-8)/ink.height)
    ink=ink.resize((round(ink.width*scale),round(ink.height*scale)),Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',size);tile.alpha_composite(ink,((size[0]-ink.width)//2,(size[1]-ink.height)//2))
    return tile


def render(raw,mid):
    if sha256(raw)!=SOURCES[mid]:raise ValueError('Scenario chart source changed')
    textures={t.index:t for t in gtf.textures(raw)};pix={};out=raw;rects={}
    def paint(index,box,image):
        nonlocal out
        t=textures[index];full=gtf.decode(raw,t);x,y,w,h=box
        full[y:y+h,x:x+w]=np.array(image);pix[t.key]=full;rects[t.key]=box
        out=gtf.replace(out,t,full)
    before=Image.fromarray(gtf.decode(raw,textures[1]));x,y,w,h=HEADER
    clean=before.crop((552,y,616,y+h));tile=Image.new('RGBA',(w,h))
    for xx in range(0,w,clean.width):tile.paste(clean,(xx,0))
    ink=label('Scenario Chart',(w,h),52,2)
    glow=Image.new('RGBA',(w,h),(255,218,60,0));glow.putalpha(ink.getchannel('A').filter(ImageFilter.GaussianBlur(4)))
    tile.alpha_composite(glow);tile.alpha_composite(ink);paint(1,HEADER,tile)
    if mid in (234,236):
        original=Image.fromarray(gtf.decode(raw,textures[2]));x,y,w,h=SUBTITLE
        bed=np.array(original.crop((x,0,x+w,128)).resize((w,h)))
        bed[:,:,:3]//=12;tile=Image.fromarray(bed)
        word='HEAVENLY PRISON' if mid==234 else 'TIME OF HELL'
        ink=label(word,(w,h),140);mask=ink.getchannel('A')
        colors=np.zeros((h,w,4),dtype=np.uint8)
        for xx in range(w):
            f=xx/(w-1);colors[:,xx]=(int(159*(1-f)+131*f),int(30*(1-f)+35*f),int(92*(1-f)+224*f),255)
        if mid==236:colors=colors[:,::-1].copy()
        colored=Image.fromarray(colors);colored.putalpha(mask.point(lambda a:a*3//4))
        glow=colored.copy();glow.putalpha(mask.filter(ImageFilter.GaussianBlur(14)).point(lambda a:a//2))
        tile.alpha_composite(glow);tile.alpha_composite(colored)
        old=original.crop((x,y,x+w,y+h));blend=Image.new('L',(w,h),255);d=ImageDraw.Draw(blend)
        for i in range(20):d.rectangle((i,i,w-1-i,h-1-i),outline=round(i*255/20))
        tile=Image.composite(tile,old,blend);paint(2,SUBTITLE,tile)
    # Restore the only painted rectangles and compare every texture pixel.
    for t in textures.values():
        a=gtf.decode(raw,t);b=gtf.decode(out,t)
        if t.key in rects:
            x,y,w,h=rects[t.key];b[y:y+h,x:x+w]=a[y:y+h,x:x+w]
        if not np.array_equal(a,b):raise ValueError('Chart pixels escaped lettering rectangles')
    return out,pix,{},dict(member=mid,header='Scenario Chart',rectangles={str(k):v for k,v in rects.items()},
                          subtitle=('HEAVENLY PRISON' if mid==234 else 'TIME OF HELL') if mid in (234,236) else None,
                          source_sha256=sha256(raw),output_sha256=sha256(out),runtime_verified=False)


def main():
    import argparse
    from tools import eff_art
    from tools.common import ROOT
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    sources=eff_art.source_members(eff_art._settings(),list(SOURCES),SOURCES)
    for mid,raw in sources.items():
        out,pix,_,info=render(raw,mid)
        print(mid,info['header'],info['subtitle'],info['rectangles'])
        if not args.apply:continue
        target=ROOT/'work/ui/textures/scenario_chart'/('chart-0.5.11-%d.png'%mid)
        indices=(1,2)if mid in (234,236)else(1,)
        sheet=Image.new('RGB',(1280,30+len(indices)*375),'#18202c')
        ImageDraw.Draw(sheet).text((8,7),'Original | English native texture preview (not in-game)',fill='white')
        for n,index in enumerate(indices):
            texture=next(t for t in gtf.textures(raw)if t.index==index)
            for x,data in ((0,raw),(640,out)):
                image=Image.fromarray(gtf.decode(data,texture)).convert('RGB').resize((640,360))
                sheet.paste(image,(x,30+n*375))
        target.parent.mkdir(parents=True,exist_ok=True);sheet.save(target)
    if not args.apply:print('DRY RUN: no previews written.')


if __name__=='__main__':main()
