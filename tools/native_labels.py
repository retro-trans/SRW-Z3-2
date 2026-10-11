"""Proportional labels from the game's original full-width Latin masks.

Retain both native G8B8 planes and the original vertical geometry. Only
horizontal blank margins move; do not synthesize a heavier Latin stroke.
"""
import functools
from tools.common import ROOT

PREFIX='@native-label:'

@functools.lru_cache(maxsize=1)
def page():
    from tools.ui_build import atlas,FONT
    from tools.pipeline import config,verified_source
    from tools.cpk import CPK
    with CPK(verified_source(config(ROOT/'config/tengoku.json'),FONT))as archive:
        entry,=[e for e in archive.files if e['id']==1]
        return atlas(archive.read(entry))

@functools.lru_cache(maxsize=None)
def raster(char):
    import numpy as np
    from PIL import Image
    from tools.ui_build import cell_xy
    if len(char)!=1 or not 32<=ord(char)<127:raise ValueError('Native label needs ASCII')
    if char==' ':
        image=Image.new('L',(32,32));image.info['native_g8b8']=np.zeros((32,32),dtype='uint16')
        return image,9
    code=chr(ord(char)+0xfee0).encode('cp932').hex()
    x,y=cell_xy(code);original=page()[y:y+32,x:x+32]
    fill=Image.fromarray((original&255).astype('uint8'));box=fill.getbbox()
    if not box:raise ValueError('Native letter is empty')
    left,_,right,_=box
    # A blank texel precedes the original native outline. Preserve both
    # planes together, including their antialiasing and original baseline.
    outline=Image.fromarray((original>>8).astype('uint8'));outer=outline.getbbox()
    origin=min(left,outer[0]);edge=max(right,outer[2]);span=edge-origin
    if span>32:raise ValueError('Native proportional letter exceeds cell')
    margin=1 if span<32 else 0
    pixels=np.zeros((32,32),dtype='uint16');pixels[:,margin:margin+span]=original[:,origin:edge]
    image=Image.fromarray((pixels&255).astype('uint8'));image.info['native_g8b8']=pixels
    return image,min(32,span+2)

def width(text,quad=28):
    return sum(raster(c)[1]for c in text)*quad/32
