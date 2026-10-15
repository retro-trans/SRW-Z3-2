"""Translate the MTFL keyword archive actually loaded by linked-term popups.

The executable dictionary and MTZKN_KW are separate copies. This archive is
MTFL/kwrb -> lkke (143 offset/length records) + jstr (XOR-0x7a CP932 pool).
Original lookup names, series, order, flags and IDs remain intact.
"""
import argparse,json,re,struct
from tools.common import ROOT,sha256,write_json
from tools.pipeline import config,verified_source
from tools.cpk import CPK
from tools import library_text as L,library_build as B
from tools.ui_description_layout import advance

DISC='/PS3_GAME/USRDIR/COMMONDATA/MTDATA/MTV_ALL_KEYWORD_DEF.CPK'
SOURCE_SHA='1b259905cfa83b3da22b9d5cf0d954110ae6f68e846548533c91000b6905e212'
COUNT=143
TAGS=('WORD','SRCE','DSCR','DSC2')

def mask(data):
    return bytes(x if x in (0,0x7a) else x^0x7a for x in data)

def parse(raw):
    if raw[:16]!=b'MTFLz2_2'+struct.pack('<I',32)+b'0.94':
        raise ValueError('Keyword MTFL header differs')
    root_end=32+struct.unpack_from('<I',raw,16)[0]
    def chunk(at,tag,header):
        if raw[at:at+4]!=tag:raise ValueError('Keyword chunk tag differs')
        length,head,body=struct.unpack_from('<3I',raw,at+4)
        if head!=header or length!=head+body or at+length>root_end:
            raise ValueError('Keyword chunk bounds differ')
        return at+head,at+length
    start,end=chunk(32,b'kwrb',16)
    if end!=root_end:raise ValueError('Keyword root bounds differ')
    table,table_end=chunk(start,b'lkke',20)
    count=struct.unpack_from('<I',raw,start+16)[0]
    if count!=COUNT or table_end-table!=COUNT*40:raise ValueError('Keyword record count differs')
    pool_at,pool_end=chunk(table_end,b'jstr',16)
    if pool_end!=root_end or not raw[root_end:].startswith(b'ENDoMTFLsrc>'):
        raise ValueError('Keyword trailer differs')
    pool=mask(raw[pool_at:pool_end]);rows=[]
    for index in range(count):
        at=table+index*40;words=struct.unpack_from('<10I',raw,at)
        fields={}
        for i,tag in enumerate(TAGS):
            off,size=words[i*2:i*2+2]
            if off+size>len(pool) or (off+size<len(pool) and pool[off+size]!=0) or b'\0' in pool[off:off+size]:
                raise ValueError('Keyword string bounds differ: row %d %s offset %d size %d end %s'%
                                 (index,tag,off,size,pool[off+size:off+size+1].hex()))
            fields[tag]=dict(offset=off,bytes=size,raw=pool[off:off+size])
        rows.append(dict(id=words[9],flags=words[8],record_offset=at,fields=fields))
    if {r['id']for r in rows}!=set(range(COUNT)) or any(r['flags']!=0xffffffff for r in rows):
        raise ValueError('Keyword IDs/flags differ')
    return dict(rows=rows,pool=pool,pool_at=pool_at,pool_end=pool_end,
                table_start=start,string_chunk=table_end,root_end=root_end)

def source(settings=None):
    settings=settings or config(ROOT/'config/tengoku.json')
    path=verified_source(settings,DISC)
    if sha256(path.read_bytes())!=SOURCE_SHA:raise ValueError('Keyword source archive changed')
    with CPK(path) as arc:
        if [r['id']for r in arc.files]!=[0]:raise ValueError('Keyword source member inventory differs')
        return arc.read(arc.files[0])

def plan(settings,mapping):
    raw=source(settings);parsed=parse(raw)
    library=L.load_library();entries,errors=L.load_translations()
    if errors:raise ValueError(errors)
    rendered=B.plan(library,entries,json.loads(L.GLOSSARY.read_text(encoding='utf8'))['terms'])['keyword']
    original=library['keyword'][0];out=bytearray(raw[:parsed['pool_at']]);pool=bytearray(parsed['pool'])
    # The source's last string ends exactly at the pool boundary. Its loader
    # supplies termination; retain that boundary before appending new strings.
    if pool and pool[-1]!=0:pool+=b'\0'
    allocations={};audit=[]
    normal=lambda text:'\n'.join(x for x in text.replace('\r\n','\n').splitlines()if x.strip())
    for row in parsed['rows']:
        tid=row['id']
        for tag in TAGS:
            if normal(row['fields'][tag]['raw'].decode('cp932'))!=normal(original[tid]['text'][tag]or''):
                raise ValueError('Keyword source identity differs: %d %s'%(tid,tag))
        for tag in ('DSCR','DSC2'):
            encoded=B.encode(B.wrap(rendered[tid][tag],advance),mapping)
            if encoded not in allocations:
                allocations[encoded]=len(pool);pool+=encoded+b'\0'
            i=TAGS.index(tag)
            struct.pack_into('<2I',out,row['record_offset']+i*8,allocations[encoded],len(encoded))
        audit.append(dict(id=tid,name=rendered[tid]['WORD']))
    growth=len(pool)-len(parsed['pool'])
    for at in (16,36,44,parsed['string_chunk']+4,parsed['string_chunk']+12):
        struct.pack_into('<I',out,at,struct.unpack_from('<I',raw,at)[0]+growth)
    out+=mask(pool)+raw[parsed['pool_end']:]
    report=verify(raw,bytes(out),rendered,mapping)
    return dict(members={0:bytes(out)},report=dict(report,source_sha256=SOURCE_SHA,entries=audit),
                original=raw,rendered=rendered,mapping=mapping)

def verify(original,final,rendered,mapping):
    a,b=parse(original),parse(final);fields=0
    if not b['pool'].startswith(a['pool']) or original[a['root_end']:]!=final[b['root_end']:]:
        raise ValueError('Keyword original pool/trailer changed')
    for old,new in zip(a['rows'],b['rows']):
        if (old['id'],old['flags'],old['record_offset'])!=(new['id'],new['flags'],new['record_offset']):
            raise ValueError('Keyword lookup identity changed')
        for tag in ('WORD','SRCE'):
            if old['fields'][tag]!=new['fields'][tag]:raise ValueError('Keyword lookup name/series changed')
        for tag in ('DSCR','DSC2'):
            want=B.encode(B.wrap(rendered[new['id']][tag],advance),mapping)
            if new['fields'][tag]['raw']!=want:raise ValueError('Keyword English prose differs')
            text=B.decode(want,mapping)
            if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',text):raise ValueError('Keyword prose still Japanese')
            fields+=1
    allowed=set()
    for at in (16,36,44,a['string_chunk']+4,a['string_chunk']+12):allowed.update(range(at,at+4))
    for row in a['rows']:allowed.update(range(row['record_offset']+16,row['record_offset']+32))
    if any(x!=y and i not in allowed for i,(x,y)in enumerate(zip(original[:a['pool_at']],final[:b['pool_at']]))):
        raise ValueError('Keyword edit escaped description/length fields')
    return dict(keywords=COUNT,description_variants=fields,source_member_sha256=sha256(original),
                final_member_sha256=sha256(final),source_member_bytes=len(original),final_member_bytes=len(final),
                original_lookup_fields_preserved=True,original_pool_and_trailer_preserved=True,runtime_verified=False)

def verify_archive(path,planned):
    with CPK(path) as arc:
        if [r['id']for r in arc.files]!=[0]:raise ValueError('Keyword archive inventory differs')
        final=arc.read(arc.files[0])
    if final!=planned['members'][0]:raise ValueError('Keyword compiled member differs')
    return verify(planned['original'],final,planned['rendered'],planned['mapping'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--build-version',default='0.5.40');a=p.parse_args()
    build=json.loads((ROOT/'work/output/builds'/a.build_version/'build.json').read_text(encoding='utf8'))
    planned=plan(config(ROOT/'config/tengoku.json'),build['mapping'])
    print(json.dumps(planned['report'],indent=2));print('DRY RUN: no game assets written.')

if __name__=='__main__':main()
