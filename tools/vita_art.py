"""Transfer sealed English pixels to source-corresponding Vita GXT pages.

Native palettes, texture metadata and unedited animation data are retained.
Artwork is decoded and requantized; PS3 texture bytes are never installed.
"""
import argparse
import json
import struct
import numpy as np
from PIL import Image
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK
from tools import vita_source as V, gtf, title_screen
from tools.vita_assets import PARENT
from tools.vita.gxt import Page,pages

ARCHIVES=(('DATA/tabata/TPACKVITA.cpk','TPACKPS3.CPK','tpack_art_v2'),
          ('DATA/AIDDATA/AIDDataPack.cpk','AIDDATAPACK.CPK','aid_art'),
          ('DATA/anime/effvita.cpk','EFFPS3.CPK','effect_art'),
          ('DATA/BTLC/CMN.cpk','CMN.CPK','battle_art'),
          ('DATA/BTLC/OP.cpk','OP.CPK','opening_art'))


def transfer(old,new,native,allow_scale=False):
    a,b=gtf.textures(old),gtf.textures(new);c=pages(native)
    V.need(len(a)==len(b)==len(c),'Native texture count differs')
    out=bytearray(native);restored_ps3=bytearray(new);audit=[];allowed=np.zeros(len(native),dtype=np.bool_)
    for page_number,(before,after,(base,index)) in enumerate(zip(a,b,c)):
        if old[before.offset:before.offset+before.size]==new[after.offset:after.offset+after.size]:continue
        x,y=gtf.decode(old,before),gtf.decode(new,after)
        V.need(x.shape==y.shape,'English texture geometry changed');mask=np.any(x!=y,axis=2)
        if not mask.any():continue
        if allow_scale:
            # Repaint complete authored startup rectangles. A per-pixel diff
            # leaves native glyph edges behind after resolution conversion.
            build=json.loads((PARENT/'build.json').read_text('utf8'))
            rectangles=build['texture_art']['startup_notices']['regions'][str(page_number)]
            region=np.zeros(mask.shape,dtype=np.bool_)
            for left,top,right,bottom in rectangles:region[top:bottom,left:right]=True
            V.need(not np.any(mask & ~region),'Startup edit escapes approved rectangles');mask=region
        page=Page(native,base,index)
        if (page.w,page.h)!=(before.width,before.height):
            original=page.pixels()
            if page.w>=before.width and page.h>=before.height:
                # Episode atlases have a larger, transparent Vita allocation,
                # with identical original ink at identical UV coordinates.
                overlap=original[:before.height,:before.width]
                V.need(np.array_equal(overlap[:,:,3],x[:,:,3]) and
                    not original[before.height:,:,3].any() and not original[:,before.width:,3].any(),
                    'Native padded atlas content differs')
                padded=original.copy();padded[:before.height,:before.width]=y;y=padded
                expanded=np.zeros((page.h,page.w),dtype=np.bool_);expanded[:before.height,:before.width]=mask;mask=expanded
            else:
                V.need(allow_scale and (before.width,before.height,page.w,page.h)==(1280,720,960,544),
                       'Native texture geometry differs')
                y=np.asarray(Image.fromarray(y,'RGBA').resize((page.w,page.h),Image.Resampling.LANCZOS)).copy()
                mask=np.asarray(Image.fromarray(mask.astype(np.uint8)*255,'L').resize((page.w,page.h),Image.Resampling.BOX))>0
        positions=np.flatnonzero(mask.ravel());physical=page.order[positions] if page.order is not None else positions
        if page.palette is None:
            for ch in range(4):allowed[page.start+physical*4+ch]=True
        else:allowed[page.start+physical]=True
        count=page.paint(out,y,mask)
        restored_ps3[after.offset:after.offset+after.size]=old[before.offset:before.offset+before.size]
        audit.append(dict(base=base,texture=index,width=page.w,height=page.h,edited_pixel_bytes=count))
    # Native animation VM is a different-endian resource. Do not silently
    # discard parent changes to it; callers must supply explicit native edits.
    outside=np.flatnonzero(np.frombuffer(old,dtype=np.uint8)!=np.frombuffer(restored_ps3,dtype=np.uint8))
    V.need(len(old)==len(new),'Parent art resized')
    if len(outside):
        first=a[0].gtf;native_first=c[0][0]
        V.need(first==native_first and all(i<first for i in outside),'Animation structure/offset differs')
        # ASSF animation operands at these guarded sites are 16-bit values.
        # Preserve every other Vita byte, including mixed-endian color words.
        for at in sorted({int(i)//2*2 for i in outside}):
            if native[at:at+2]==old[at:at+2][::-1]:payload=new[at:at+2][::-1]
            else:
                # Vertex RGBA bytes have the same order on both platforms.
                # The only authored color edits hide obsolete glyph quads.
                V.need(native[at:at+2]==old[at:at+2] and new[at:at+2]==b'\0\0',
                       'Native animation operand source differs at '+hex(at))
                payload=b'\0\0'
            out[at:at+2]=payload;allowed[at:at+2]=True
        audit.append(dict(animation_operand_words=len({int(i)//2 for i in outside}),
                          source_values_verified=True))
    changed=np.frombuffer(native,dtype=np.uint8)!=np.frombuffer(out,dtype=np.uint8)
    V.need(not np.any(changed & ~allowed),'Native art escaped pixel masks')
    return bytes(out),audit


def changed_rows(a,b):
    old={r['id']:r for r in a.files};new={r['id']:r for r in b.files}
    V.need(old.keys()==new.keys(),'Parent art member IDs changed')
    return [i for i in new if (old[i]['size'],old[i]['extract'])!=(new[i]['size'],new[i]['extract']) or
        a.buf[old[i]['offset']:old[i]['offset']+old[i]['size']]!=b.buf[new[i]['offset']:new[i]['offset']+new[i]['size']]]


def run(group,apply=False):
    rel,parent,folder=next(r for r in ARCHIVES if r[2]==group)
    ps3=next(p for p in (ROOT/'work/tengoku/source/PS3_GAME/USRDIR').rglob('*') if p.name.lower()==parent.lower())
    dest=V.WORK/'asset_plans'/folder
    if apply:V.need(not dest.exists(),'Preserve existing art candidate')
    result={};report=[]
    with CPK(ps3) as a,CPK(PARENT/parent) as b,CPK(V.PLAIN/rel) as c:
        indexes=[{r['id']:r for r in v.files} for v in (a,b,c)]
        mids=changed_rows(a,b)
        if parent=='TPACKPS3.CPK':mids=[i for i in mids if i not in (1,3)]
        if parent=='AIDDATAPACK.CPK':mids=[i for i in mids if i not in (0,5)]
        for mid in mids:
            old,en,native=[v.read(ix[mid]) for v,ix in zip((a,b,c),indexes)]
            if old==en:continue
            if parent=='EFFPS3.CPK' and mid==229:en=title_screen.render(old,'0.1.0')[0]
            try:raw,info=transfer(old,en,native,parent=='TPACKPS3.CPK' and mid==0)
            except ValueError as exc:raise ValueError(group+' member '+str(mid)+': '+str(exc)) from exc
            V.need(raw!=native,'Empty artwork replacement')
            result[mid]=raw;report.append(dict(member=mid,source_sha256=sha256(native),output_sha256=sha256(raw),textures=info))
            print(group,mid,len(info),'pages',flush=True)
    print(group,':',len(result),'members;',sum(len(r['textures']) for r in report),'textures',flush=True)
    if apply:
        dest.mkdir(parents=True)
        for mid,raw in result.items():(dest/f'{mid:05d}.bin').write_bytes(raw)
        write_json(dest/'plan.json',dict(schema=1,title_id=V.TITLE,members=report,archive=rel,runtime_verified=False))
        # Representative texture exports for visual checks; never called game screenshots.
        preview=V.WORK/'previews'/folder;preview.mkdir(parents=True,exist_ok=True)
        picks=[report[0],report[-1]] if report else []
        if parent=='EFFPS3.CPK':picks=[r for r in report if r['member']==229]
        for row in picks:
            for info in row['textures']:
                if 'texture' in info:Page(result[row['member']],info['base'],info['texture']).image().save(preview/f"{row['member']:05d}-{info['base']:08x}-{info['texture']:02d}.png")
    else:print('DRY RUN: no artwork written.')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('group',choices=[r[2] for r in ARCHIVES]);p.add_argument('--apply',action='store_true');a=p.parse_args()
    run(a.group,a.apply)


if __name__=='__main__':main()
