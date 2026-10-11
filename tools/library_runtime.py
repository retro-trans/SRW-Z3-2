"""Relocate all native linked-term descriptions before the popup splits lines."""
import struct
from tools import eboot_text as E, ui_hook as H, library_text as L, library_build as B, vwf
from tools.common import sha256

COUNT=143
LETTERS={c:chr(0xe100+ord(c)-32) for c in map(chr,range(32,127))}
FAST_STATE='library:conversion-state'
FAST_TABLE='library:conversion-table'
GUARDS={0x13f4c:0x4bfffbed,0x13f50:0x80e280c4,0x13f54:0x386700b8,
        0x14998:0x4bfff1a1,0x1499c:0x83c280c4,0x149a0:0x3bfe00b8}


def dispatch(va,state,table):
    """Owned UTF-8 ranges select complete pre-encoded prose, including slices.

    Other strings tail-call the untouched native converter. This avoids its
    4096-byte UTF-16 stack array and shared output buffer for long descriptions.
    """
    from tools.link_layout import Asm,BLR
    a=Asm(va);a.ptr(12,state);a.d(0x38000000,0,0,0);a.d(0x90000000,0,12,0);a.ptr(4,table)
    a.label('scan');a.d(0x80000000,5,4,0);a.d(0x2f800000,0,5,0);a.br(0x419e0000,'native')
    a.e(0x7f832840);a.br(0x419c0000,'next') # cmplw cr7,r3,r5
    a.d(0x80000000,6,4,4);a.e(0x7f833040);a.br(0x419d0000,'next')
    a.d(0x80000000,7,4,8)
    a.label('offset');a.e(0x7f832840);a.br(0x419e0000,'hit')
    a.d(0x88000000,8,5,0);a.d(0x38000000,9,0,1);a.d(0x38000000,10,0,1)
    a.d(0x2b800000,0,8,0x80);a.br(0x419c0000,'step')
    a.d(0x38000000,9,0,2);a.d(0x38000000,10,0,2)
    a.d(0x2b800000,0,8,0xe0);a.br(0x419c0000,'step');a.d(0x38000000,9,0,3)
    a.label('step');a.x(0x7c000214,5,5,9);a.x(0x7c000214,7,7,10);a.br(0x48000000,'offset')
    a.label('hit');a.d(0x90000000,7,12,0);a.d(0x38000000,3,0,0);a.e(BLR)
    a.label('next');a.d(0x38000000,4,4,12);a.br(0x48000000,'scan')
    a.label('native');a.jump(H.CONVERTER[0]);return a.code()


def converted_pointer(va,state,drawer=False):
    from tools.link_layout import Asm
    a=Asm(va);a.ptr(12,state)
    a.d(0x80000000,30 if drawer else 7,2,H.STATE_DISP)
    a.d(0x80000000,31 if drawer else 3,12,0)
    a.d(0x2f800000,0,31 if drawer else 3,0);a.br(0x409e0000,'done')
    a.d(0x38000000,31 if drawer else 3,30 if drawer else 7,0xb8)
    a.label('done');a.jump(0x149a4 if drawer else 0x13f58);return a.code()


def apply_fastpath(elf,original,planned,addresses):
    for va,word in GUARDS.items():
        if struct.unpack_from('>I',original,va-0x10000)[0]!=word or struct.unpack_from('>I',elf,va-0x10000)[0]!=word:
            raise ValueError('Library converter consumer changed: %#x'%va)
    table=b''.join(struct.pack('>III',addresses[key],addresses[key]+len(raw)-1,addresses[key+':encoded'])
        for key,raw in planned['payloads'] if key.startswith('library:keyword:') and not key.endswith(':encoded'))+bytes(12)
    phoff,_,phs,_=H._headers(elf);first,second=phs[:2]
    cursor=(first[5]+15)&~15;base=first[3]+cursor;state=addresses[FAST_STATE]
    codes=((base,dispatch(base,state,addresses[FAST_TABLE])),
           (base+256,converted_pointer(base+256,state)),(base+384,converted_pointer(base+384,state,True)))
    out=bytearray(elf);allowed=set();read=H._reader(elf,phs)
    def put(va,data,zero=False):
        at=va-0x10000
        if zero and read(va,len(data))!=bytes(len(data)):raise ValueError('Library reserved payload occupied')
        out[at:at+len(data)]=data;allowed.update(range(at,at+len(data)))
    put(addresses[FAST_TABLE],table,True)
    for va,code in codes:
        at=va-first[3]
        if at+len(code)>second[2] or any(elf[at:at+len(code)]):raise ValueError('Library RX gap exhausted')
        out[at:at+len(code)]=code;allowed.update(range(at,at+len(code)))
    end=max(va-first[3]+len(code) for va,code in codes)
    struct.pack_into('>QQ',out,phoff+32,end,end);allowed.update(range(phoff+32,phoff+48))
    for site in (0x13f4c,0x14998):put(site,struct.pack('>I',H.branch(site,base)|1))
    for site,target in ((0x13f50,base+256),(0x1499c,base+384)):
        put(site,struct.pack('>II',H.branch(site,target),0x60000000))
    if len(out)!=len(elf) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(elf,out))):
        raise ValueError('Library fast path escaped checked spans')
    H.unicode_table(bytes(out)) # native converter code is still pristine
    return bytes(out),dict(owned_ranges=COUNT*2,state_va=state,table_va=addresses[FAST_TABLE],
        code=[dict(va=va,bytes=len(code))for va,code in codes],native_converter_unchanged=True,
        descriptions_draw_from_read_only_pool=True,runtime_verified=False)


def verify_fastpath(elf,planned,addresses,report):
    """Execute the shipped consumer instructions for every owned description."""
    from tools import ppc_exec as P
    phs=H._headers(elf)[2];mem=P.Memory()
    for i,seg in enumerate(phs[:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=i==1)
    mem.map(0x48000000,b'ordinary\0',writable=False)
    m=P.Machine(mem);cases=0
    owned=[(key,raw)for key,raw in planned['payloads'] if key.startswith('library:keyword:') and not key.endswith(':encoded')]
    read=H._reader(elf,phs)
    for key,raw in owned:
        for drawer in (False,True):
            m.r=[0x770000+i for i in range(32)];m.r[1]=0x40003f00;m.r[2]=H.TOC
            m.r[3]=addresses[key];before=m.r[:];m.lr=0x1234;m.pc=0x14998 if drawer else 0x13f4c
            m.run({0x149a4 if drawer else 0x13f58},limit=m.steps+20000)
            if m.r[31 if drawer else 3]!=addresses[key+':encoded']:
                raise ValueError('Native keyword conversion pointer differs: '+key)
            if m.r[30 if drawer else 7]!=H.STATE_VA or any(m.r[r]!=before[r] for r in (1,2,29)):
                raise ValueError('Native keyword consumer state differs')
            encoded=dict(planned['payloads'])[key+':encoded']
            if read(m.r[31 if drawer else 3],len(encoded))!=encoded:raise ValueError('Native prose pool differs')
            cases+=1
    # A substring inside the longest UTF-8 payload must select the matching
    # CP932 byte offset. Line copies fall back to the original converter.
    key,raw=max(owned,key=lambda item:len(item[1]));offset=raw.rfind(b'\n')+1
    m.r[3]=addresses[key]+offset;m.lr=0x1234;m.pc=report['code'][0]['va']
    m.run({0x1234},limit=m.steps+100000)
    expected=addresses[key+':encoded']+len(H.convert(raw[:offset],H.unicode_table(elf)))
    if int.from_bytes(mem.read(report['state_va'],4),'big')!=expected:raise ValueError('Library substring offset differs')
    m.r[3]=0x48000000;m.pc=report['code'][0]['va']
    m.run({H.CONVERTER[0]},limit=m.steps+30000)
    if m.r[3]!=0x48000000 or mem.read(report['state_va'],4)!=bytes(4):raise ValueError('Native converter fallback differs')
    for drawer in (False,True):
        m.pc=report['code'][2 if drawer else 1]['va'];m.run({0x149a4 if drawer else 0x13f58},limit=m.steps+1000)
        if m.r[31 if drawer else 3]!=H.STATE_VA+0xb8:raise ValueError('Native consumer fallback differs')
    if mem.read(H.STATE_VA+0xb8,8192)!=read(H.STATE_VA+0xb8,8192):raise ValueError('Library prose modified shared native text buffer')
    return dict(owned_consumer_cases=cases,substring_cases=1,fallback_cases=3,machine_steps=m.steps)


def native_patch(elf,original,mapping):
    out=bytearray(elf);ranges=[]
    for ch,token in LETTERS.items():
        at=H.UTAB_VA-0x10000+0x100+ord(token)*2
        if original[at:at+2]!=bytes.fromhex('81a1') or elf[at:at+2]!=bytes.fromhex('81a1'):
            raise ValueError('Library private converter cell is occupied')
        if ch not in mapping:continue
        out[at:at+2]=bytes.fromhex(mapping[ch]);ranges.append((at,at+2))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Library converter escaped its cells')
    return bytes(out),dict(converter_cells=len(ranges),modified_file_ranges=ranges)


def plan(elf,mapping,width_of):
    if sha256(elf)!=vwf.ELF_SHA256:raise ValueError('Keyword table baseline changed')
    library=L.load_library();entries,_=L.load_translations()
    import json
    terms=json.loads(L.GLOSSARY.read_text(encoding='utf-8'))['terms']
    rendered=B.plan(library,entries,terms)['keyword']
    converted_elf,_=native_patch(elf,elf,mapping)
    read=H._reader(elf,H._headers(elf)[2])
    def string(va):
        out=bytearray()
        for n in range(8192):
            c=read(va+n,1)
            if c==b'\0':return bytes(out).decode('utf8')
            out+=c
        raise ValueError('Native keyword string is unterminated')
    payloads={}; pointers=[];audit=[]
    # Records are grouped by initial kana; their index is the stable Library
    # ID, not the physical row number. Locate the complete six-word shape.
    ph=H._headers(elf)[2][1]; locations={}
    for marker in range(ph[2]+16,ph[2]+ph[5]-4,4):
        if elf[marker:marker+4]!=b'\xff'*4:continue
        tid=struct.unpack_from('>I',elf,marker+4)[0]
        if tid not in library['keyword'][0]:continue
        at=marker-16; vals=struct.unpack_from('>6I',elf,at)
        if not all(0x800000<=va<0x940000 for va in vals[:4]):continue
        record=library['keyword'][0][tid]
        if string(vals[0])!=record['text']['WORD']:continue
        if tid in locations:raise ValueError('Ambiguous native keyword descriptor')
        locations[tid]=at
    if set(locations)!=set(library['keyword'][0]):raise ValueError('Native keyword descriptor coverage incomplete: %d'%len(locations))
    for tid,record in sorted(library['keyword'][0].items()):
        at=locations[tid]
        name,series,d1,d2,flag,index=struct.unpack_from('>6I',elf,at)
        if index!=tid or flag!=0xffffffff:raise ValueError('Native keyword index changed')
        normal=lambda text:'\n'.join(line for line in text.splitlines() if line.strip())
        for va,tag in ((name,'WORD'),(series,'SRCE'),(d1,'DSCR'),(d2,'DSC2')):
            if normal(string(va))!=normal(record['text'][tag] or ''):raise ValueError('Native keyword field differs: %d %s'%(tid,tag))
        for col,tag in ((2,'DSCR'),(3,'DSC2')):
            text=B.wrap(rendered[tid][tag],width_of)
            raw=B.encode(text,mapping)
            # CP932 carrier characters remain genuine UTF-8 input for the
            # existing converter; assert its exact output, including LF.
            utf8=''.join(LETTERS.get(c,c) for c in text).encode('utf8')
            converted=H.convert(utf8,H.unicode_table(converted_elf))
            if converted!=raw:
                mismatch=next((n for n,(a,b)in enumerate(zip(converted,raw))if a!=b),min(len(converted),len(raw)))
                raise ValueError('Keyword carrier converter mismatch: %d %s byte %d (%s != %s)'%
                    (tid,tag,mismatch,converted[mismatch:mismatch+8].hex(),raw[mismatch:mismatch+8].hex()))
            key='library:keyword:%d:%s'%(tid,tag)
            payloads[key]=utf8+b'\0'
            payloads[key+':encoded']=raw+b'\0'
            pointers.append(dict(offset=at+col*4,old=struct.unpack_from('>I',elf,at+col*4)[0],id=key))
        audit.append(dict(id=tid,name=rendered[tid]['WORD'],fields=['DSCR','DSC2'],
                         record_offset=at,source_record_sha256=sha256(elf[at:at+24])))
    if len(audit)!=COUNT:raise ValueError('Incomplete native keyword coverage')
    payloads.update({FAST_STATE:bytes(16),FAST_TABLE:bytes((COUNT*2+1)*12)})
    return dict(payloads=list(payloads.items()),pointers=pointers,inline=[],unresolved=[],
        report=dict(native_keyword_entries=COUNT,native_keyword_descriptions=COUNT*2,
                    entries=audit,
                    original_names_series_indices_preserved=True,runtime_verified=False))
