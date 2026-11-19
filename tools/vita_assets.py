"""Transfer source-bound English data and native P8 font cells to PCSG00494.

No PS3 executable bytes or platform textures are transplanted. Changes to Lua
are literal bodies only; all Vita commands and platform-specific data survive.
"""
import argparse
import json
import re
import struct
import numpy as np
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK
from tools import vita_source as V, ui_build as F, squad_text as Q
from tools.vita.font_gxt import FontPage, index_for_code

PARENT = ROOT/'work/output/builds/0.5.51'
LONG = re.compile(rb'(?<!--)\[\[(.*?)\]\]',re.S)


def voice(data_segment):
    """Find the complete native block table by values, never PS3 addresses."""
    from tools import srvc
    old=(ROOT/'work/tengoku/prepared/SRVC.BIN').read_bytes()
    native=(V.PLAIN/'DATA/BTLC/SRVC.BIN').read_bytes()
    english=(PARENT/'SRVC.BIN').read_bytes()
    V.need(old==native,'Native voice source differs')
    before=srvc.read_table((ROOT/'work/tengoku/prepared/EBOOT.elf').read_bytes(),len(old))
    after=srvc.read_table((PARENT/'EBOOT.BIN').read_bytes(),len(english))
    a,b=srvc.parse(old,before),srvc.parse(english,after)
    V.need(len(a)==len(b)==368,'Native voice block count differs')
    for x,y in zip(a,b):
        V.need(old[x.base:x.offs_at]==english[y.base:y.offs_at], 'Voice selection metadata changed')
    pattern=struct.pack('<%dI'%len(before),*before);at=data_segment.find(pattern)
    V.need(at>=0 and at%4==0 and data_segment.find(pattern,at+1)<0,'Native voice table is not unique')
    output=bytearray(data_segment);output[at:at+len(pattern)]=struct.pack('<%dI'%len(after),*after)
    return bytes(output),dict(data_offset=at,table_bytes=len(pattern),blocks=len(a),
        source_sha256=sha256(native),output_sha256=sha256(english),metadata_preserved=True)


def normal(raw):
    return raw.replace(b'\r\n',b'\n')


def stage_member(source, english, vita):
    old, new, native = [list(LONG.finditer(raw)) for raw in (source,english,vita)]
    V.need(len(old)==len(new)==len(native),'Stage long-literal structure differs')
    edits=[]
    for a,b,c in zip(old,new,native):
        if a.group(1) == b.group(1):continue
        V.need(normal(a.group(1)) == normal(c.group(1)), 'Translated stage source differs on Vita')
        edits.append((c.start(1),c.end(1),b.group(1)))
    oldq,newq,nativeq=[Q.scan(raw) for raw in (source,english,vita)]
    V.need(len(oldq)==len(newq),'PS3 quoted-literal structure changed')
    index={}
    for a,b in zip(oldq,newq):
        if a['raw']==b['raw']:continue
        key=(tuple(a['ctx']),a['raw'])
        V.need(key not in index or index[key]==b['raw'],'Ambiguous translated quoted literal')
        index[key]=b['raw']
    mapped=set()
    for c in nativeq:
        key=(tuple(c['ctx']),c['raw'])
        if key in index:
            edits.append((c['start'],c['end'],index[key]));mapped.add(key)
    V.need(mapped==set(index),'Translated quoted literal lacks a source-bound Vita counterpart')
    result=bytearray();pos=0;spans=[]
    for a,z,data in sorted(edits):
        V.need(pos<=a<z<=len(vita),'Overlapping Lua edits')
        result+=vita[pos:a];spans.append((len(result),len(data),vita[a:z]));result+=data;pos=z
    result+=vita[pos:]
    # Independently recover the exact Vita source outside the edited bodies.
    restored=bytearray(result)
    for offset,length,source_body in reversed(spans):
        restored[offset:offset+length]=source_body
    V.need(bytes(restored)==vita,'Stage edits escaped language literal bodies')
    return bytes(result),dict(long_literals=sum(a.group(1)!=b.group(1) for a,b in zip(old,new)),
                              quoted_literals=len(edits)-sum(a.group(1)!=b.group(1) for a,b in zip(old,new)))


def stages():
    paths=(ROOT/'work/tengoku/prepared/STGZ3OF2.dec.cpk',PARENT/'STGZ3OF2.cpk',V.PLAIN/'DATA/STAGE/STGZ3OF2.cpk')
    with CPK(paths[0]) as a,CPK(paths[1]) as b,CPK(paths[2]) as c:
        old={r['id']:a.read(r) for r in a.files};new={r['id']:b.read(r) for r in b.files};native={r['id']:c.read(r) for r in c.files}
    V.need(old.keys()==new.keys()==native.keys(),'Stage member IDs differ')
    members,report={},[]
    for mid in old:
        if old[mid]==new[mid]:continue
        raw,changes=stage_member(old[mid],new[mid],native[mid])
        members[mid]=raw
        report.append(dict(member=mid,source_sha256=sha256(native[mid]),output_sha256=sha256(raw),**changes))
    return members,report


def fonts():
    build=json.loads((PARENT/'build.json').read_text('utf8'))
    result,checks={},[]
    with CPK(V.PLAIN/'DATA/TABATA/TPACKVITA.cpk') as archive:
        rows={r['id']:r for r in archive.files}
        for mid in (1,3):
            original=archive.read(rows[mid]);page=FontPage(original)
            V.need(page.bits==8 and max(page.indices())<=15,'Unused P8 palette bank is occupied')
            cells={index_for_code(int(code,16)) for code in build['mapping'].values()}
            V.need(cells<=page.blank_cells(),'Translated font allocation overlaps native ink')
            atlas=F.atlas((PARENT/f'font_{mid}.bin').read_bytes())
            pixels=bytearray(page.indices());out=bytearray(original)
            # New smooth fill-only palette entries never affect original indices
            # 0..15. Both palettes share white fill/alpha, so no outline is added.
            ramp=[round(255*i/127) for i in range(128)]
            lut=[min(range(128),key=lambda i:abs(ramp[i]-v))+16 for v in range(256)]
            base=64+page.pixels
            for palette in range(2):
                for i,alpha in enumerate(ramp):
                    off=base+palette*1024+(i+16)*4
                    out[off:off+4]=bytes((255,255,255,alpha))
            aa,bb=[p[3::4][:16] for p in page.palettes]
            quant={}
            for index in cells:
                y,x=divmod(index,128);tile=atlas[y*32:y*32+32,x*32:x*32+32]
                for row in range(32):
                    offset=(y*32+row)*4096+x*32
                    for col in range(32):
                        word=int(tile[row,col]);outer,fill=word>>8,word&255
                        if outer==fill:value=lut[fill]
                        else:
                            if word not in quant:quant[word]=min(range(16),key=lambda i:(aa[i]-outer)**2+(bb[i]-fill)**2)
                            value=quant[word]
                        pixels[offset+col]=value
            out[64:64+page.pixels]=pixels
            restored=bytearray(out)
            for index in cells:
                y,x=divmod(index,128)
                for row in range(32):
                    off=64+(y*32+row)*4096+x*32
                    restored[off:off+32]=original[off:off+32]
            for palette in range(2):
                off=base+palette*1024+16*4
                restored[off:off+128*4]=original[off:off+128*4]
            V.need(restored==original,'Font changes escaped blank cells and unused palette entries')
            result[mid]=bytes(out)
            checks.append(dict(member=mid,translated_cells=len(cells),native_pixels_and_used_palettes_unchanged=True,
                no_added_ordinary_outline=True,normal_alpha_max_error=max(abs(ramp[lut[v]-16]-v) for v in range(256)),
                source_sha256=sha256(original),output_sha256=sha256(out)))
    return result,checks


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('stage','font'));p.add_argument('--apply',action='store_true');a=p.parse_args()
    members,report=stages() if a.action=='stage' else fonts()
    print(a.action,':',len(members),'members;',sum(r.get('long_literals',0) for r in report),'long literals;',sum(r.get('quoted_literals',0) for r in report),'quoted literals.')
    if a.action=='font':print(json.dumps(report,indent=2))
    if a.apply:
        folder=V.WORK/'asset_plans'/a.action;V.need(not folder.exists(),'Preserve existing asset plan');folder.mkdir(parents=True)
        for mid,raw in members.items():(folder/f'{mid:05d}.bin').write_bytes(raw)
        write_json(folder/'plan.json',dict(schema=1,title_id=V.TITLE,members=report))
    else:print('DRY RUN: no assets written.')


if __name__=='__main__':main()
