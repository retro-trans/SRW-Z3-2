"""Lay out the warning on the Vita's native panel; keep its original frame."""
import argparse,json
import numpy as np
from PIL import Image,ImageDraw
from tools import vita_source as V,review34_startup as T
from tools.common import sha256,write_json
from tools.cpk import CPK
from tools.vita.gxt import Page


def plan():
    with CPK(V.PLAIN/'DATA/tabata/TPACKVITA.cpk') as archive:
        native=archive.read(next(r for r in archive.files if r['id']==0))
    previous=(V.WORK/'asset_plans/tpack_art_v2/00000.bin').read_bytes()
    page=Page(native,0,0);V.need((page.w,page.h)==(960,544),'Native warning geometry differs')
    pixels=page.pixels();image=Image.fromarray(pixels,'RGBA');draw=ImageDraw.Draw(image)
    rect=(220,95,740,450)
    for x,y in ((220,100),(740,100),(220,450),(740,450)):
        V.need(tuple(pixels[y,x])==(239,239,239,255),'Native warning panel boundary differs')
    draw.rectangle((220,95,739,449),fill=(239,239,239,255))
    text=T.checked()['warning'];ink=T.ink(text['heading'],'SCE-PS3-RD-B-LATIN.TTF',38)
    image.paste((217,55,23,255),(480-ink.width//2,111),ink)
    y=163;lines=[];font=T.font('SCE-PS3-RD-B-LATIN.TTF',23)
    for paragraph in text['paragraphs']:
        for line in T.wrap(paragraph,font,504):
            ink=T.ink(line,'SCE-PS3-RD-B-LATIN.TTF',23)
            V.need(ink.width<=504 and y+ink.height<450,'Native warning overflows')
            image.paste((102,102,102,255),(228,y),ink);y+=32;lines.append(line)
        y+=16
    V.need(' '.join(lines).split()==' '.join(text['paragraphs']).split(),'Warning words changed')
    mask=np.zeros((544,960),dtype=np.bool_);mask[95:450,220:740]=True
    # Restore the complete original warning before repainting its interior.
    out=bytearray(previous);out[page.start:page.start+page.size]=native[page.start:page.start+page.size]
    page.paint(out,np.asarray(image),mask)
    actual=Page(bytes(out),0,0).pixels()
    V.need(np.array_equal(actual[~mask],pixels[~mask]),'Native warning frame changed')
    return bytes(out),dict(member=0,source_sha256=sha256(native),output_sha256=sha256(out),
        native_warning_frame_preserved=True,native_warning_rectangle=list(rect),lines=lines,
        supersedes_plan='tpack_art_v2',superseded_sha256=sha256(previous),runtime_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    raw,report=plan();print(json.dumps(report,indent=2))
    if a.apply:
        folder=V.WORK/'asset_plans/startup_v3';V.need(not folder.exists(),'Preserve startup candidate');folder.mkdir(parents=True)
        (folder/'00000.bin').write_bytes(raw);write_json(folder/'plan.json',dict(title_id=V.TITLE,members=[report]))
        Page(raw,0,0).image().save(V.WORK/'previews/native-warning-final.png')
    else:print('DRY RUN: no warning written.')


if __name__=='__main__':main()
