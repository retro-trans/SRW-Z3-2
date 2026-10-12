"""Map defeat quotes: translate the native selector's complete display table.

RPW and UI-hook translations do not reach the map dialogue composer. The
selector at 0x1a8028 returns a static three-word record: pilot, mode, text.
Only its text pointer is replaced, with relocated cp932/VWF text.
"""
import argparse,json,re,struct
from functools import lru_cache
from tools.common import ROOT,sha256,write_json
from tools import rpw_text as R,eboot_text as E,ui_hook as H,library_build as L

TABLE=0xa1ca28
COUNT=249
TOC_SLOT=0x99b298
GETTER=(0x1a8028,0x1a80c0)
GETTER_SHA='6a2207500037247793227d84719c4b66975f72a19e305d64db1ce511ae2614db'
STORE=(0x1a7fec,0x1a8018)
STORE_SHA='a9eb61c2e012a81e7fe9ae64b5a56c8bb1fb16dcb07af36f38a8216e36377410'
COMPOSER=(0x1a84e4,0x1a861c)
COMPOSER_SHA='bd53f9e1976356447af7be56d7c7a59fa33fcf7d92ed03ce0bbccfd4ab87e6c7'
TABLE_SHA='b2ecb952313eeac257a0ae93c8c36f73e48569f56481b2d1392c52b36fc6fa7e'
DEST=ROOT/'work/ui/review28_quote_audit.json'


def guard(elf,table=True):
    read=H._reader(elf,H._headers(elf)[2])
    for (a,b),digest in ((GETTER,GETTER_SHA),(STORE,STORE_SHA),(COMPOSER,COMPOSER_SHA)):
        if sha256(read(a,b-a))!=digest:raise ValueError('Defeat quote consumer changed')
    if read(TOC_SLOT,4)!=struct.pack('>I',TABLE):raise ValueError('Defeat table moved')
    if table and sha256(read(TABLE,(COUNT+1)*12))!=TABLE_SHA:raise ValueError('Defeat table changed')
    return read


@lru_cache(None)
def width(c):
    from tools.ui_vwf_build import raster
    return raster(c)[1]if ord(c)<128 else 32


def plan(elf=None,width_of=width):
    elf=H.PREPARED.read_bytes()if elf is None else elf;read=guard(elf)
    raw=R.load_rpw();slots=[s for s in R.slots(raw)if s['family']=='quote']
    if len(slots)!=COUNT:raise ValueError('Defeat quote row count changed')
    names=R.load_names();fallback=E.load()['strings'];rows=[]
    for n,s in enumerate(slots):
        pilot,mode,pointer=struct.unpack('>3I',read(TABLE+n*12,12))
        original,code,flag=struct.unpack_from('<3I',raw,s['pointer_offset'])
        jp=s['jp'];source=jp.encode('cp932')+b'\0'
        if (pilot,mode)!=(code,flag)or read(pointer,len(source))!=source:
            raise ValueError('Static/RPW defeat quote identity differs')
        en=R.text_for(s,names)or fallback.get(jp,{}).get('en')
        if not en or R.unusual(en):raise ValueError('Untranslated defeat quote: '+s['id'])
        if en.count('\n')!=jp.count('\n'):raise ValueError('Defeat quote line layout changed')
        if en.count('「')!=jp.count('「')or en.count('」')!=jp.count('」'):
            raise ValueError('Defeat quote brackets changed')
        if re.search(r'\b(?:Xul|Zul|Sachs|Girtar|Amerria)\b',en):raise ValueError('Old canonical spelling')
        widths=[sum(width_of(c)for c in line)for line in en.split('\n')]
        if len(widths)>3 or max(widths)>960:raise ValueError('Defeat quote exceeds dialogue panel: '+s['id'])
        # Native composer has a 256-byte buffer. Pilot display names are capped
        # at 30 bytes; reserve one LF and one terminating NUL as well.
        encoded=2*sum(ord(c)<128 and c!='\n'for c in en)+sum(len(c.encode('cp932'))for c in en if ord(c)>=128)+en.count('\n')
        if encoded+32>256:raise ValueError('Defeat quote exceeds native composition buffer: '+s['id'])
        rows.append(dict(id=s['id'],ordinal=n,pilot_code=pilot,mode=mode,
            pointer_va=TABLE+n*12+8,source_pointer=pointer,source_bytes=len(source),source_sha256=sha256(source),
            payload_id='defeat-quote:'+sha256(source)[:16],english=en,row_widths=widths,
            encoded_bytes=encoded,composition_reserved_bytes=encoded+32))
    return dict(schema=1,version='0.5.28',table_va=TABLE,table_sha256=TABLE_SHA,
        rows=rows,distinct_quotes=len({r['payload_id']for r in rows}),
        native_getter=GETTER,native_store=STORE,runtime_verified=False)


def payloads(planned,mapping):
    values={r['payload_id']:L.encode(r['english'],mapping)+b'\0'for r in planned['rows']}
    return list(values.items())


def apply(elf,planned,addresses):
    read=guard(elf);out=bytearray(elf);ranges=[]
    for r in planned['rows']:
        va=r['pointer_va'];old=struct.unpack('>I',read(va,4))[0]
        if old!=r['source_pointer']:raise ValueError('Defeat quote pointer drift')
        at=va-0x10000;struct.pack_into('>I',out,at,addresses[r['payload_id']]);ranges.append((at,at+4))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Defeat quote patch escaped pointer fields')
    return bytes(out),dict(rows=len(planned['rows']),distinct_quotes=planned['distinct_quotes'],
        table_va=TABLE,selector_unchanged=True,pilot_codes_unchanged=True,modes_unchanged=True,
        source_strings_unchanged=True,runtime_verified=False)


def verify(elf,planned,mapping):
    """Execute the real native selector and its quote-state stores."""
    from tools import ppc_exec as P
    read=guard(elf,table=False);source=H.PREPARED.read_bytes();original=guard(source)
    cases=[];mem=P.Memory()
    for i,s in enumerate(H._headers(elf)[2][:2]):
        body=elf[s[2]:s[2]+s[5]]+bytes(s[6]-s[5]);mem.map(s[3],body,writable=i==1)
    # Read-only selector alias table and sentinel are unchanged.
    alias_va=struct.unpack('>I',read(TOC_SLOT+4,4))[0];aliases=[]
    for n in range(1000):
        code,alias=struct.unpack('>2I',read(alias_va+n*8,8))
        if code==0xffffffff:break
        aliases.append((code,alias))
    else:raise ValueError('Unbounded defeat alias table')
    if read(alias_va,(len(aliases)+1)*8)!=original(alias_va,(len(aliases)+1)*8):raise ValueError('Defeat aliases changed')
    by_code={}
    for r in planned['rows']:
        by_code.setdefault(r['pilot_code'],r)
        at=r['pointer_va'];pilot,mode,pointer=struct.unpack('>3I',read(at-8,12))
        if (pilot,mode)!=(r['pilot_code'],r['mode']):raise ValueError('Defeat selection metadata changed')
        raw=L.encode(r['english'],mapping)+b'\0'
        if read(pointer,len(raw))!=raw:raise ValueError('Native defeat quote not English')
        if sha256(read(r['source_pointer'],r['source_bytes']))!=r['source_sha256']:raise ValueError('Source string changed')
        # Each native record's store writes pilot, mode and text separately.
        m=P.Machine(mem);m.r[2]=H.TOC;m.r[3]=999;m.r[4]=at-8;m.lr=0x1000;m.pc=STORE[0]
        m.run({0x1000},limit=50);state=struct.unpack('>I',read(H.TOC-0x4bdc,4))[0]
        if mem.read(state,16)!=struct.pack('>4I',pilot,mode,pointer,999):raise ValueError('Native quote store differs')
        cases.append(dict(id=r['id'],english=r['english'],steps=m.steps))
    lookup=[]
    # The real selector preserves aliases, unknown codes and its sentinel.
    for code in list(by_code)+[c for c,_ in aliases]+[0xffffffff,0x12345678]:
        m=P.Machine(mem);m.r[2]=H.TOC;m.r[3]=code;m.lr=0x1000;m.pc=GETTER[0];m.run({0x1000},limit=10000)
        resolved=dict(aliases).get(code,code);expected=by_code.get(resolved)
        want=expected['pointer_va']-8 if expected else 0
        if m.r[3]!=want:raise ValueError('Native defeat selector differs: '+hex(code))
        lookup.append(dict(pilot_code=code,resolved_code=resolved,record_va=want,steps=m.steps))
    return dict(store_cases=cases,selector_cases=lookup,aliases_preserved=len(aliases),runtime_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    print('Native map defeat quotes:',len(data['rows']),'records;',data['distinct_quotes'],'distinct; missing English: 0')
    print('Nigel:',data['rows'][67]['english']);print('Largest composition:',max(r['composition_reserved_bytes']for r in data['rows']),'of 256 bytes')
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no files changed.')

if __name__=='__main__':main()
