"""Tengoku dialogue name readers: translate defaults without editing saves.

The three leaf getters are called exclusively by the $n/$f/$l/$F display
substitution builder at 0x1fb2b8. Custom names and the saved name order survive.
"""
import struct

from tools.common import sha256
from tools import eboot_text, ui_hook, vwf

READERS = (
    (0x1faae0,0x8062c394,-0x3c6c,'ヒビキ','Hibiki'),
    (0x1faae8,0x8062c398,-0x3c68,'ヒビキ','Hibiki'),
    (0x1faaf0,0x8062c39c,-0x3c64,'カミシロ','Kamishiro'),
)
FULL_SURNAME_RETURNS = (0x1fb484,0x1fb718)
CONSUMER = (0x1fb2b8,0x1fb740)
CONSUMER_SHA = '224acc7708834b6144d392f4a6154ce0cc2c0bfd9951c7ea2842c67f841d9584'
SEPARATOR=(0x1fba2c,0x8062c3c4)


def plan(elf,mapping):
    if sha256(elf)!=vwf.ELF_SHA256:
        raise ValueError('Name readers require the verified Tengoku baseline')
    payloads = [('name:'+en,eboot_text.encode(en,mapping)+b'\0') for en in ('Hibiki','Kamishiro','K.')]
    payloads += [('name:separator',eboot_text.encode(' ',mapping)+b'\0')]
    return dict(payloads=payloads)


def stub(reader,addresses):
    _,original,_,jp,en = reader
    words,labels,fixups = [],{},[]
    def emit(word): words.append(word)
    def d(op,reg,base,off): emit(op | reg<<21 | base<<16 | (off&65535))
    def cmp(reg,value): d(0x2c000000,0,reg,value)
    def pointer(reg,va):
        d(0x3c000000,reg,0,va>>16)
        emit(0x60000000 | reg<<21 | reg<<16 | (va&65535))
    def br(op,label):
        fixups.append((len(words),op,label)); emit(0)
    emit(original)
    emit(0x7d800026)                       # mfcr r12
    cmp(3,0); br(0x41820000,'return')
    for i,byte in enumerate(jp.encode('cp932')+b'\0'):
        d(0x88000000,0,3,i); cmp(0,byte); br(0x40820000,'return')
    if en=='Kamishiro':
        emit(0x7d6802a6)                   # mflr r11
        for ret in FULL_SURNAME_RETURNS:
            pointer(10,ret)
            emit(0x7c0b5040)              # cmplw r11,r10
            br(0x41820000,'length')
        br(0x48000000,'english')
        labels['length'] = len(words)
        d(0x80000000,9,2,-0x3c68)
        cmp(9,0); br(0x41820000,'english')
        d(0x38000000,10,0,0)
        labels['scan'] = len(words)
        d(0x88000000,0,9,0); cmp(0,0); br(0x41820000,'english')
        d(0x38000000,9,9,1); d(0x38000000,10,10,1)
        cmp(10,21); br(0x41800000,'scan')
        # Each replacement value has 40 bytes plus NUL. Normal names use the
        # full surname; only $F with a long custom nickname abbreviates the
        # default surname. Custom nickname bytes are never changed/truncated.
        pointer(3,addresses['name:K.']); br(0x48000000,'return')
    labels['english'] = len(words)
    pointer(3,addresses['name:'+en])
    labels['return'] = len(words)
    emit(0x7d8ff120)                       # mtcrf 255,r12
    emit(0x4e800020)
    for i,op,label in fixups:
        delta = 4*(labels[label]-i)
        words[i] = op | (delta & (0x3fffffc if op==0x48000000 else 0xfffc))
    return b''.join(struct.pack('>I',w) for w in words)


def separator_stub(addresses):
    """Use a space for the two translated defaults; preserve custom-name style."""
    words=[SEPARATOR[1],0x7d800026];fix=[]
    def emit(w):words.append(w)
    def d(op,r,b,off):emit(op|r<<21|b<<16|(off&65535))
    for off,jp in ((-0x3c68,'ヒビキ'),(-0x3c64,'カミシロ')):
        d(0x80000000,9,2,off);d(0x2c000000,0,9,0);fix.append((len(words),0x41820000));emit(0)
        for n,b in enumerate(jp.encode('cp932')+b'\0'):
            d(0x88000000,0,9,n);d(0x2c000000,0,0,b);fix.append((len(words),0x40820000));emit(0)
    va=addresses['name:separator'];d(0x3c000000,3,0,va>>16);emit(0x60630000|(va&65535))
    end=len(words);emit(0x7d8ff120);emit(0x4e800020)
    for n,op in fix:words[n]=op|((end-n)*4&65535)
    return b''.join(struct.pack('>I',w)for w in words)


def apply(elf,planned,addresses):
    phoff,_,phs,_ = ui_hook._headers(elf)
    first,second = phs[:2]
    if first[:5]!=ui_hook.PH0_BASE or first[5]!=first[6]:
        raise ValueError('Unexpected runtime-name code segment')
    read = ui_hook._reader(elf,phs)
    if sha256(read(CONSUMER[0],CONSUMER[1]-CONSUMER[0]))!=CONSUMER_SHA:
        raise ValueError('Dialogue name consumer changed')
    for key,payload in planned['payloads']:
        if read(addresses[key],len(payload))!=payload:
            raise ValueError('Runtime name payload differs')
    out = bytearray(elf)
    start = first[5]
    cursor = (start+15)&~15
    ranges,stubs = [],[]
    for reader in READERS:
        site,original,_,_,en = reader
        if read(site,8)!=struct.pack('>II',original,0x4e800020):
            raise ValueError('Runtime name leaf changed')
        code = stub(reader,addresses)
        end = cursor+len(code)
        if end>second[2] or any(elf[cursor:end]):
            raise ValueError('Runtime-name executable gap occupied/exhausted')
        va = cursor+first[3]
        out[cursor:end] = code
        offset = site-first[3]
        struct.pack_into('>I',out,offset,ui_hook.branch(site,va))
        ranges += [(cursor,end),(offset,offset+4)]
        stubs.append(dict(site=site,stub_va=va,bytes=len(code),english=en))
        cursor = (end+15)&~15
    site,original=SEPARATOR
    if read(site,8)!=struct.pack('>II',original,0x4e800020):raise ValueError('Full-name separator getter changed')
    code=separator_stub(addresses);end=cursor+len(code);va=cursor+first[3]
    if end>second[2]or any(elf[cursor:end]):raise ValueError('Separator executable gap occupied')
    out[cursor:end]=code;offset=site-first[3];struct.pack_into('>I',out,offset,ui_hook.branch(site,va))
    ranges += [(cursor,end),(offset,offset+4)]
    separator=dict(site=site,stub_va=va,bytes=len(code),custom_names_preserved=True)
    struct.pack_into('>QQ',out,phoff+32,end,end)
    ranges.append((phoff+32,phoff+48))
    restored = bytearray(out)
    for a,b in ranges:
        restored[a:b] = elf[a:b]
    if restored!=elf:
        raise ValueError('Runtime-name patch changed unrelated bytes')
    return bytes(out),dict(readers=stubs,separator=separator,consumer_sha256=CONSUMER_SHA,
        modified_file_ranges=ranges,save_buffers_modified=False,
        full_name_capacity=41,long_custom_nickname_surname='K.',runtime_verified=False)
