"""SRW Z3's Rodin Bold single-letter raster geometry, with local allocation.

Matches tools/digraph.raster_letter + ttfglyph.Face.natural in ../SRW Z3:
22px cap, baseline 26, 4x supersampling, 0.5px horizontal stem dilation,
BOX downsampling, 1px advance padding and a 9px blank space.
"""
import functools

CAP = 22
BASE = 26
SS = 4
DILATE = 0.5


@functools.lru_cache(maxsize=None)
def face_font(path):
    from PIL import ImageFont
    probe = ImageFont.truetype(str(path),100)
    _,top,_,bottom = probe.getbbox('H',anchor='ls')
    return ImageFont.truetype(str(path),round(100*CAP/(bottom-top)*SS))


@functools.lru_cache(maxsize=None)
def letter(char,path):
    from PIL import Image, ImageDraw, ImageChops
    if len(char)!=1:
        raise ValueError('Single-letter font requires one character')
    cell = Image.new('L',(32,32))
    if char==' ':
        return cell,9
    font = face_font(path)
    dilation = round(DILATE*SS)
    left,top,right,bottom = font.getbbox(char,anchor='ls')
    advance = round(font.getlength(char)/SS+dilation/SS+1)
    if not 1<=advance<=31:
        raise ValueError('Single-letter font advance exceeds native cell: '+repr(char))
    if right>left and bottom>top:
        ink = Image.new('L',(right-left+2*SS+dilation,bottom-top+2*SS))
        ImageDraw.Draw(ink).text((SS-left,SS-top),char,font=font,anchor='ls',fill=255)
        base = ink.copy()
        for k in range(1,dilation+1):
            ink = ImageChops.lighter(ink,ImageChops.offset(base,k,0))
        small = ink.resize((max(1,round(ink.width/SS)),max(1,round(ink.height/SS))),Image.Resampling.BOX)
        # Same rounded baseline-relative paste and clipped coverage as _blit.
        cell.paste(small,(round(left/SS-1),round(BASE+top/SS-1)))
    return cell,advance


def profile():
    from tools.ui_build import FACE
    from tools.common import sha256_file
    return dict(face=FACE.name,face_sha256=sha256_file(FACE),cap=CAP,baseline=BASE,
        supersampling=SS,horizontal_dilation=DILATE,space_advance=9,advance_padding=1,
        downsampling='BOX',texture='G8B8: outline high byte, fill low byte',outline_radius=2,
        reference='SRW Z3/tools/digraph.py + tools/ttfglyph.py')
