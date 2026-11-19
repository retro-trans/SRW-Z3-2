"""Native P8 and linear RGBA GXT edits, confined to explicit pixel masks."""
from functools import lru_cache
import struct
import numpy as np
from PIL import Image


def need(ok,message):
    if not ok:raise ValueError(message)


@lru_cache(maxsize=32)
def order(width,height):
    need(width&(width-1)==height&(height-1)==0,'Unsupported swizzle dimensions')
    bits=min(width,height).bit_length()-1
    x,y=np.meshgrid(np.arange(width,dtype=np.uint32),np.arange(height,dtype=np.uint32))
    result=np.zeros_like(x)
    for i in range(bits):result|=((y>>i)&1)<<(2*i);result|=((x>>i)&1)<<(2*i+1)
    result|=((x>>bits) if width>=height else (y>>bits))<<(2*bits)
    return result.ravel()


class Page:
    def __init__(self,data,base,index):
        need(data[base:base+8]==b'GXT\0\x03\0\0\x10','Wrong GXT version')
        count,start,total,p4,p8=struct.unpack_from('<5I',data,base+8)
        need(p4==0 and index<count and base+start+total<=len(data),'Invalid GXT extents')
        off,size,pal,flags,kind,fmt,w,h,mips=struct.unpack_from('<6IHHI',data,base+32+index*32)
        need(kind in (0,0x60000000) and flags==0 and mips==1,'Unsupported GXT layout')
        self.base=base;self.index=index;self.w=w;self.h=h;self.start=base+off;self.size=size;self.fmt=fmt
        self.data=data;self.order=order(w,h) if kind==0 else None;self.palette=None
        if fmt==0x95000000:
            need(p8==count and pal==0 and size==w*h,'Unsupported P8 layout')
            self.palette=np.frombuffer(data,dtype=np.uint8,count=1024,offset=base+start+total-p8*1024+index*1024).reshape(256,4)
        elif fmt==0x0c000000:need(p8==0 and size==w*h*4,'Unsupported RGBA layout')
        else:need(False,'Unsupported GXT pixel format '+hex(fmt))

    def pixels(self):
        raw=np.frombuffer(self.data,dtype=np.uint8,count=self.size,offset=self.start)
        if self.palette is not None:
            if self.order is not None:raw=raw[self.order]
            return self.palette[raw].reshape(self.h,self.w,4).copy()
        raw=raw.reshape(-1,4)
        if self.order is not None:raw=raw[self.order]
        return raw.reshape(self.h,self.w,4).copy()

    def image(self):return Image.fromarray(self.pixels(),'RGBA')

    def paint(self,out,pixels,mask):
        need(pixels.shape==(self.h,self.w,4) and mask.shape==(self.h,self.w),'Invalid native image geometry')
        positions=np.flatnonzero(mask.ravel());values=pixels.reshape(-1,4)[positions]
        physical=self.order[positions] if self.order is not None else positions
        if self.palette is None:
            raw=np.frombuffer(out,dtype=np.uint8,count=self.size,offset=self.start).reshape(-1,4);raw[physical]=values
            return positions.size*4
        unique,inverse=np.unique(values,axis=0,return_inverse=True)
        # Compare premultiplied colors so invisible source RGB cannot add fringes.
        def premult(v):
            v=v.astype(np.float32);v[:,:3]*=v[:,3:4]/255;return v
        palette=premult(self.palette);colors=premult(unique);nearest=[]
        for i in range(0,len(colors),2048):
            distance=((colors[i:i+2048,None]-palette[None])**2).sum(axis=2)
            nearest.extend(distance.argmin(axis=1))
        matched=np.asarray(nearest,dtype=np.uint8)[inverse]
        raw=np.frombuffer(out,dtype=np.uint8,count=self.size,offset=self.start);raw[physical]=matched
        return positions.size


def pages(data):
    result=[];at=0
    while True:
        at=data.find(b'GXT\0',at)
        if at<0:break
        count,start,total=struct.unpack_from('<3I',data,at+8)
        need(0<count<64 and at+start+total<=len(data),'Invalid GXT chain')
        result.extend((at,i) for i in range(count));at+=start+total
    return result
