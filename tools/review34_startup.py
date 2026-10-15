"""Translate the three source-bound startup bitmap notices; preserve the logos."""
import argparse,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tools.common import ROOT,sha256,write_json
from tools import texture_art as A,gtf

DEST=ROOT/'work/translation/en/ui/review34_startup.json'
PREVIEW=ROOT/'work/ui/startup_notices'
SOURCE_SHA='0dc4dcd0d0ecb34d7ea48f09cd84963c571df8a42452c83ffcc50a0401fa5a62'
CREDITS={3:[
    '©Okeanos / "Gargantia on the Verdurous Planet" Production Committee',
    '©GAINAX · Kazuki Nakashima / Aniplex · KDE-J · TV TOKYO · Dentsu',
    '©GAINAX · Kazuki Nakashima / Gurren Lagann Movie Production Committee',
    '©Shoji Gatoh · Shikidouji / Jindai High School Student Council',
    '©Shoji Gatoh · Shikidouji / Full Metal Panic! Film Partners',
    '©Shoji Gatoh · Shikidouji / Mithril',
    '©khara', '©SUNRISE',
    None,
    '©XEBEC · FlyingDog / SOTSU',
    None],
    4:[
    '©SOTSU · SUNRISE',None,
    '©HIKARI PRODUCTION · TMS',
    '©Shinobu Fujiwara / Dancouga Nova Production Committee',
    '©1983 BIGWEST · TMS',
    '©1994, 1997 BIGWEST',
    '©2009, 2011 BIGWEST / Macross F Movie Production Committee',
    '©1998 Shoji Gatoh · Shikidouji / KADOKAWA Fujimi Shobo (Publisher)',
    '©1998 Go Nagai · Ken Ishikawa / Dynamic Planning · "Shin Getter Robo" Production Committee',
    '©2009 Go Nagai / Dynamic Planning · Kuroganeya',
    '©2003 GAINAX / TOP2 Committee',
    '©2004 Shoji Kawamori · SATELIGHT / Project AQUARION']}

def catalog():
    return dict(schema=1,version='0.5.34',source_member_sha256=SOURCE_SHA,
        warning=dict(heading='Caution',paragraphs=[
          "Uploading or distributing game software over the Internet without the rights holder's permission, or knowingly downloading an illegally distributed copy, is strictly prohibited by law.",
          'Thank you for your understanding and cooperation.']),
        copyright_pages={str(k):[dict(row=n,en=s,keep_source_pixels=s is None)for n,s in enumerate(v)]for k,v in CREDITS.items()},
        preserved_screens=[1,2],preserved_english_credit_rows=[[3,8],[3,10],[4,1]],
        references=[
          dict(url='https://fullmetal-panic.jp/',basis='Shoji Gatoh and Shikidouji creator names'),
          dict(url='https://www.ashipro.jp/tv_series/w041a.html',basis='Shinobu Fujiwara and Dancouga Nova Production Committee'),
          dict(url='https://gurrenlagannthemovieusa.com/introduction/',basis='Kazuki Nakashima'),
          dict(url='https://www.selecta-vision.com/catalogos/mazinger-edicion-z-impacto/',basis='Go Nagai / Dynamic Planning / Kuroganeya'),
          dict(url='https://www.crunchyroll.com/ko/news/latest/2015/4/6/gargantia-ova-2nd-part-opening-box-office-is-24-higher-than-1st',basis='Okeanos creator credit'),
          dict(url='https://www.sunrise-inc.co.jp/international/',basis='SUNRISE historical studio spelling retained')],
        notes='Translation of the original game notices; retain all years, owners, separators and production-credit relationships. Do not update the original notice to current ownership or legal wording.')

def source():
    return A.source_members(A._settings(),[0],{0:SOURCE_SHA})[0]

def font(name,size):return ImageFont.truetype(str(A.font_dir()/name),size)

def ink(text,face,size):
    f=font(face,size*3);box=f.getbbox(text);im=Image.new('L',(box[2]-box[0]+6,box[3]-box[1]+6))
    ImageDraw.Draw(im).text((3-box[0],3-box[1]),text,font=f,fill=255)
    im=im.crop(im.getbbox());return im.resize((round(im.width/3),round(im.height/3)),Image.Resampling.LANCZOS)

def wrap(text,f,width):
    lines=[];line=''
    for word in text.split():
        trial=(line+' '+word).strip()
        if line and f.getlength(trial)>width:lines.append(line);line=word
        else:line=trial
    return lines+[line]

def render(original=None,data=None):
    original=original if original is not None else source();data=data or catalog()
    if sha256(original)!=SOURCE_SHA:raise ValueError('Startup source member changed')
    textures=gtf.textures(original)
    if len(textures)!=5 or any((t.width,t.height,t.fmt)!=(1280,720,gtf.LINEAR_ARGB)for t in textures):raise ValueError('Startup screen geometry changed')
    out=original;intended={};regions={};details=[]
    for number in (0,3,4):
        pixels=gtf.decode(original,textures[number]);im=gtf.to_image(pixels);draw=ImageDraw.Draw(im);boxes=[]
        if number==0:
            boxes=[(510,108,770,174),(278,190,1007,580)]
            for box in boxes:draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=(239,239,239,255))
            title=ink(data['warning']['heading'],'SCE-PS3-RD-B-LATIN.TTF',52)
            # The English title has its own centered footprint, inside the original title area.
            if title.width>260:raise ValueError('Warning title exceeds its heading rectangle')
            im.paste((217,55,23,255),(640-title.width//2,118),title)
            y=201;f=font('SCE-PS3-RD-B-LATIN.TTF',32);warning_lines=[]
            for paragraph in data['warning']['paragraphs']:
                lines=wrap(paragraph,f,712);warning_lines+=lines
                for line in lines:
                    glyphs=ink(line,'SCE-PS3-RD-B-LATIN.TTF',32)
                    if glyphs.width>712 or y+glyphs.height>580:raise ValueError('Warning text exceeds its frame')
                    im.paste((102,102,102,255),(286,y),glyphs);y+=43
                y+=19
            if ' '.join(warning_lines).split()!=' '.join(data['warning']['paragraphs']).split():raise ValueError('Warning words lost')
            details.append(dict(screen=0,lines=warning_lines,last_y=y-19))
        else:
            for row in data['copyright_pages'][str(number)]:
                if row['keep_source_pixels']:continue
                n=row['row'];top=(100 if number==3 else 76)+48*n;box=(105,top,1176,top+40)
                draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=(0,0,0,255));boxes.append(box)
                size=30;glyphs=ink(row['en'],'SCE-PS3-MT-R-LATIN.TTF',size)
                if 1058/glyphs.width<0.78:
                    size=26;glyphs=ink(row['en'],'SCE-PS3-MT-R-LATIN.TTF',size)
                ratio=min(1,1058/glyphs.width)
                if ratio<0.78:raise ValueError('Copyright credit needs an additional row')
                if ratio<1:glyphs=glyphs.resize((1058,glyphs.height),Image.Resampling.LANCZOS)
                if glyphs.height>32:raise ValueError('Copyright row crosses its native pitch')
                im.paste((255,255,255,255),(110,top+5),glyphs)
                details.append(dict(screen=number,row=n,en=row['en'],bounds=[110,top+5,110+glyphs.width,top+5+glyphs.height],font_px=size,horizontal_scale=ratio))
        rgba=gtf.from_image(im);out=gtf.replace(out,textures[number],rgba);intended[textures[number].key]=rgba;regions[number]=boxes
    A.verify_member(original,out,intended)
    # Every pixel outside the translated text rectangles, including all alpha and borders, survives.
    for n in (0,3,4):
        keep=np.ones((720,1280),dtype=bool)
        for l,t,r,b in regions[n]:keep[t:b,l:r]=False
        before=gtf.decode(original,textures[n]);after=gtf.decode(out,textures[n])
        if not np.array_equal(before[keep],after[keep]):raise ValueError('Startup background or existing English credit changed')
        if not np.array_equal(before[:,:,3],after[:,:,3]):raise ValueError('Startup alpha changed')
    return out,intended,dict(schema=1,version='0.5.34',source_sha256=SOURCE_SHA,output_sha256=sha256(out),translated_screens=[0,3,4],translated_credit_rows=20,details=details,regions=regions,runtime_verified=False)

def checked():
    data=json.loads(DEST.read_text('utf8'))
    if data!=catalog():raise ValueError('Startup translation bindings stale')
    return data

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
    data=catalog();built,pixels,report=render(data=data)
    for row in report['details']:print(row)
    if not a.apply:print('DRY RUN: no startup translation or preview files written.');return
    write_json(DEST,data);write_json(ROOT/'work/ui/review34_startup_layout.json',report)
    PREVIEW.mkdir(parents=True,exist_ok=True)
    for n in (0,3,4):gtf.to_image(gtf.decode(built,gtf.textures(built)[n])).save(PREVIEW/('english-'+str(n)+'.png'))
    print('Wrote source-bound translation and three native-size preview screens.')

if __name__=='__main__':main()
