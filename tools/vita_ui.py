"""Port sealed English widgets to source-matched native ASSF/T2BS resources.

Only language pointers, explicitly changed layout fields and appended strings
are transferred. Native coordinates retain their pixel-center adjustment.
"""
import argparse
import json
import math
import struct
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK
from tools import vita_source as V
from tools.vita_assets import PARENT


def u32(data, at, endian):
    return struct.unpack_from(endian+'I', data, at)[0]


def widgets(data, endian):
    base,end,first,last=[u32(data,p,endian) for p in (32,36,72,76)]
    V.need((last-first)%32==0 and end<=first<last<=len(data), 'Invalid widget sections')
    return base,end,first,last


def assf(source, english, native):
    V.need(source[:4]==english[:4]==b'FSSA' and native[:4]==b'ASSF', 'Wrong widget format')
    base,end,first,last=widgets(source,'>')
    nb,ne,nf,nl=widgets(native,'<'); eb,ee,ef,el=widgets(english,'>')
    grow=ee-end
    V.need((nb,ne,nf,nl)==(base,end,first,last) and (eb,ef,el)==(base,first+grow,last+grow),
           'Native/English widget topology differs')
    V.need(source[base:end]==native[base:end]==english[base:end], 'Widget source pools differ')
    out=bytearray(native[:end]+english[end:ee]+native[end:]);allowed=set(range(end,ee));changed=0
    parent_restored=bytearray(english[:end]+english[ee:])
    for at in range(0x10,0x7c,4):
        old=u32(native,at,'<')
        V.need(old==u32(source,at,'>'), 'Native section topology differs')
        if old>=end:struct.pack_into('<I',out,at,old+grow)
        parent_restored[at:at+4]=source[at:at+4]
    for at in range(first,last,32):
        e=at+grow
        V.need(u32(source,at,'>')==u32(native,at,'<') and source[at+12:at+32]==native[at+12:at+32],
               'Native widget identity differs')
        if source[at:at+32]==english[e:e+32]:continue
        parent_restored[at:at+32]=source[at:at+32]
        changed+=1
        struct.pack_into('<I',out,e,u32(english,e,'>'))
        for off in (4,8):
            a,b,c=[struct.unpack_from(t+'f',v,p+off)[0] for v,p,t in
                   ((source,at,'>'),(english,e,'>'),(native,at,'<'))]
            V.need(all(math.isfinite(v) for v in (a,b,c)) and abs(a-c)<0.005,
                   'Native widget geometry differs beyond pixel-center adjustment')
            if a!=b:struct.pack_into('<f',out,e+off,c+(b-a))
        # Fields +12..31 are byte-sized in both platforms, not swapped words.
        out[e+12:e+32]=english[e+12:e+32]
        allowed.update(range(e,e+32))
    # Twelve-byte element records contain X/Y floats followed by native flags.
    start,stop=[u32(source,p,'>') for p in (80,84)]
    V.need((stop-start)%12==0,'Invalid element section');elements=0
    for at in range(start,stop,12):
        e=at+grow
        if source[at:at+12]==english[e:e+12]:continue
        V.need(source[at+8:at+12]==english[e+8:e+12], 'Unsupported element field edit')
        elements+=1
        parent_restored[at:at+8]=source[at:at+8]
        for off in (0,4):
            a,b,c=[struct.unpack_from(t+'f',v,p+off)[0] for v,p,t in
                   ((source,at,'>'),(english,e,'>'),(native,at,'<'))]
            V.need(all(math.isfinite(v) for v in (a,b,c)) and abs(a-c)<0.005,'Native element geometry differs')
            if a!=b:struct.pack_into('<f',out,e+off,c+(b-a));allowed.update(range(e+off,e+off+4))
    restored=bytearray(out[:end]+out[ee:])
    for at in range(0x10,0x7c,4):restored[at:at+4]=native[at:at+4]
    for at in allowed:
        if at>=ee:restored[at-grow]=native[at-grow]
    V.need(restored==native,'Widget changes escaped bound fields/appendix')
    V.need(parent_restored==source,'An English parent edit was not ported')
    return bytes(out),dict(widgets=changed,elements=elements,appended_bytes=grow,
                          original_pool_and_native_geometry_preserved=True)


def table_rows(data,endian):
    size=u32(data,24,endian);table=32+size;pool=table+16
    V.need(size%4==0 and pool+u32(data,table+8,endian)==len(data),'Invalid text table')
    rows=[]
    for at in range(32,table,4):
        pos=pool+u32(data,at,endian);V.need(pool<=pos<len(data),'Invalid text pointer')
        stop=data.find(b'\0',pos);V.need(stop>=pos,'Unterminated table string');rows.append(data[pos:stop])
    return pool,rows


def text_table(source, english, native):
    V.need(source[:4]==english[:4]==b'SB2T' and native[:4]==b'T2BS','Wrong native string table')
    p,a=table_rows(source,'>');q,b=table_rows(english,'>');r,c=table_rows(native,'<')
    V.need(p==q==r and a==c and len(a)==len(b),'Text table identities differ')
    out=bytearray(native);count=0
    restored_parent=bytearray(english[:len(source)])
    for i,(old,new) in enumerate(zip(a,b)):
        if old==new:continue
        struct.pack_into('<I',out,32+4*i,len(out)-r);out+=new+b'\0';count+=1
        restored_parent[32+4*i:36+4*i]=source[32+4*i:36+4*i]
    struct.pack_into('<I',out,r-8,len(out)-r)
    V.need(table_rows(out,'<')[1]==b,'Native table readback mismatch')
    restored_parent[p-8:p-4]=source[p-8:p-4]
    V.need(restored_parent==source,'An English table edit was not ported')
    return bytes(out),dict(rows=count)


def plan():
    ps3=next(p for p in (ROOT/'work/tengoku/source/PS3_GAME/USRDIR').rglob('*') if p.name.lower()=='aiddatapack.cpk')
    out,report={},[]
    with CPK(ps3) as a,CPK(PARENT/'AIDDATAPACK.CPK') as b,CPK(V.PLAIN/'DATA/AIDDATA/AIDDataPack.cpk') as c:
        indexes=[{r['id']:r for r in v.files} for v in (a,b,c)]
        for mid,fn in ((0,assf),(5,text_table)):
            old,en,native=[v.read(ix[mid]) for v,ix in zip((a,b,c),indexes)]
            raw,info=fn(old,en,native);out[mid]=raw
            report.append(dict(member=mid,source_sha256=sha256(native),output_sha256=sha256(raw),**info))
    return out,report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    out,info=plan();print(json.dumps(info,indent=2))
    if a.apply:
        folder=V.WORK/'asset_plans/ui';V.need(not folder.exists(),'Preserve existing UI candidate');folder.mkdir(parents=True)
        for mid,raw in out.items():(folder/f'{mid:05d}.bin').write_bytes(raw)
        write_json(folder/'plan.json',dict(schema=1,title_id=V.TITLE,members=info))
    else:print('DRY RUN: no native widgets written.')


if __name__=='__main__':main()
