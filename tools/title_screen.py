"""English title sprites and Z3-style footer, bound to Tengoku member 229."""
import argparse
import re
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tools import eff_art as E, gtf
from tools.common import ROOT, sha256, sha256_file, write_json

MEMBER = 229
SOURCE_SHA = '5f6d8d307e6b8e7e4704c048d07be030c9f49a17d79120a9c78e6de1c91d9277'
ASSETS = ROOT/'work/ui/textures/assets/title'
ASSET_SHA = {
    'wordmark-generated.png': '74656a4041153deb74bcb32260f5005089f7ee6dbc4d80e63ac9b97aae475826',
    'subtitle-generated.png': 'd6bfb0328de482f3079ec6e555ee580d7b083611faf1869c334ced0a50629114',
}
FOOTER = (912, 640, 1252, 696)
FOOTERS = {0:FOOTER,6:(858,610,1198,666),10:FOOTER}
URL = 'github.com/retro-trans'
SLICES = ((0, 208, 0), (216, 216, 166), (440, 208, 332))
PREVIEW = ROOT/'work/ui/textures/title'


def asset(name):
    path = ASSETS/name
    if sha256_file(path) != ASSET_SHA[name]:
        raise ValueError('Title artwork changed: '+name)
    with Image.open(path) as image:
        if image.mode != 'RGBA' or image.getextrema()[3] != (0, 255):
            raise ValueError('Title artwork must have real transparency')
        return image.copy()


def fit(image, size, top=None):
    """Pack generated art into a native sprite without changing its aspect."""
    image = image.crop(image.getchannel('A').getbbox())
    ratio = min((size[0]-4)/image.width, (size[1]-4)/image.height)
    packed = image.resize((round(image.width*ratio), round(image.height*ratio)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', size)
    y = (size[1]-packed.height)//2 if top is None else top
    if y+packed.height > size[1]-2:
        raise ValueError('Title sprite would overflow')
    canvas.alpha_composite(packed, ((size[0]-packed.width)//2, y))
    return canvas


def footer(version):
    if not re.fullmatch(r'0\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Invalid title version')
    from tools.ui_build import FACE
    scale = 4
    width, height = FOOTER[2]-FOOTER[0], FOOTER[3]-FOOTER[1]
    canvas = Image.new('RGBA', (width*scale, height*scale))
    face = ImageFont.truetype(str(FACE), 18*scale)
    for text, bottom in (('v'+version, 26), (URL, height)):
        l,t,r,b = face.getbbox(text, stroke_width=scale)
        if r-l >= (width-4)*scale or b-t > 24*scale:
            raise ValueError('Title footer would overflow')
        ink = Image.new('RGBA', (r-l, b-t))
        ImageDraw.Draw(ink).text((-l,-t), text, font=face, fill=(240,246,255,255),
            stroke_width=scale, stroke_fill=(5,12,32,240))
        canvas.alpha_composite(ink, (width*scale-ink.width, bottom*scale-ink.height))
    return canvas.resize((width,height), Image.Resampling.LANCZOS)


def audit(source):
    if sha256(source) != SOURCE_SHA or E.gtf_base(source) != 0x7c7d0:
        raise ValueError('Title animation source changed')
    tex = {t['id']:t for t in gtf.textures(source)}
    for tid,size in {0:(1280,720),1:(864,304),2:(536,192),6:(1280,720),10:(1280,720),12:(648,192)}.items():
        t = tex[tid]
        if (t['width'],t['height']) != size or t['fmt'] != gtf.LINEAR_ARGB:
            raise ValueError('Title texture geometry changed')
    rows = [(1,(0,0,861,300),428), (2,(0,0,536,187),832)]
    rows += [(12,(x,0,w,192),410) for x,w,_ in SLICES]
    for tid,rect,count in rows:
        if len(E.rect_records(source,tid,rect)) != count:
            raise ValueError('Title sprite animation references changed')
    return tex


def render(source, version):
    tex = audit(source)
    word = fit(asset('wordmark-generated.png'), (861,300))
    subtitle = fit(asset('subtitle-generated.png'), (536,187), top=32)
    data = gtf.paint(source,tex[1],(0,0,861,300),np.asarray(word))
    data = gtf.paint(data,tex[2],(0,0,536,187),np.asarray(subtitle))
    # Original character quads overlap. Repack overlapping windows of the
    # same full subtitle, rather than splitting at the atlas's unused gaps.
    full = subtitle.resize((540,192),Image.Resampling.LANCZOS)
    for x,width,logical in SLICES:
        tile = full.crop((logical,0,logical+width,192))
        data = gtf.paint(data,tex[12],(x,0,width,192),np.asarray(tile))
    stamp = footer(version)
    for tid,box in FOOTERS.items():
        image = gtf.to_image(gtf.decode(source,tex[tid]))
        image.alpha_composite(stamp,box[:2])
        data = gtf.paint(data,tex[tid],(box[0],box[1],stamp.width,stamp.height),
            np.asarray(image.crop(box)))
    intended = {tex[i].key:gtf.decode(data,tex[i])for i in (0,1,2,6,10,12)}
    verify(source,data,intended)
    info = dict(version=version,credit=URL,footer_box=list(FOOTER),footer_boxes=FOOTERS,footer_textures=[0,6,10],
        wordmark='3rd SUPER ROBOT WARS',subtitle='HEAVENLY PRISON / CHAPTER',
        subtitle_top=32,
        member=MEMBER,source_sha256=SOURCE_SHA,output_sha256=sha256(data),
        assets=ASSET_SHA,animated_subtitle_slices=SLICES,animation_bytes_unchanged=True,
        native_z_unchanged=True,runtime_verified=False)
    return data,intended,{},info


def verify(source,built,intended):
    E.verify_member(source,built,intended)
    tex = audit(source)
    restored = built
    boxes = {1:[(0,0,861,300)],2:[(0,0,536,187)],
        12:[(x,0,w,192)for x,w,_ in SLICES]}
    boxes.update({i:[(b[0],b[1],b[2]-b[0],b[3]-b[1])]for i,b in FOOTERS.items()})
    for tid,rects in boxes.items():
        original = gtf.decode(source,tex[tid])
        for x,y,w,h in rects:
            restored = gtf.paint(restored,tex[tid],(x,y,w,h),original[y:y+h,x:x+w])
    if restored != source:
        raise ValueError('Title change escaped approved pixel rectangles')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.5.10');ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();source=E.source_members(E._settings(),[MEMBER],{MEMBER:SOURCE_SHA})[MEMBER]
    built,pixels,_,info=render(source,args.version)
    print(info)
    if args.apply:
        PREVIEW.mkdir(parents=True,exist_ok=True)
        for (base,tid),array in pixels.items():
            gtf.to_image(array).save(PREVIEW/('title-%s-t%d.png'%(args.version,tid)))
        # A source-bound settled frame, for checking sprite continuity only.
        # This is a texture composition, not an emulator screenshot.
        textures={t['id']:t for t in gtf.textures(built)}
        frame=gtf.to_image(gtf.decode(built,textures[0]))
        for p in (0x35018,0x35050,0x35088,0x350c0,0x350f8,0x35130):
            _,x,y,w,h,flags,mode,tid=struct.unpack_from('>8H',source,p)
            xy=E.quad_xy(source,p)
            tile=gtf.to_image(gtf.decode(built,textures[tid])).crop((x,y,x+w,y+h))
            size=(round((xy[2]-xy[0])*4/3),round((xy[5]-xy[1])*4/3))
            frame.alpha_composite(tile.resize(size,Image.Resampling.LANCZOS),
                (round((xy[0]+480)*4/3),round((xy[1]+270)*4/3)))
        frame.save(PREVIEW/('title-%s-frame-preview.png'%args.version))
        write_json(ROOT/'work/translation/en/ui/title_screen.json',info)
    else:print('DRY RUN: no title metadata or previews written.')


if __name__=='__main__':main()
