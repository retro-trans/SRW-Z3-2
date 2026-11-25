"""Bind immutable native stage constants without runtime global lookups.

Read the original Vita stage_require.lua, resolve its literal declarations,
and substitute only code identifier references. Comments, strings, table
fields and all unrelated bytes survive exactly. Never invent flag offsets.
"""
import bisect
import re
import struct
from collections import Counter,defaultdict
from tools.cpk import CPK
from tools.common import sha256
from tools import vita_source as V

SHARED='CommonData/KuroData/LUACPK.cpk'
STAGE='DATA/STAGE/STGZ3OF2.cpk'
IDENT=re.compile(rb'[A-Za-z_][A-Za-z0-9_]*')
NUMBER=re.compile(rb'(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)')
OPEN=re.compile(rb'\[(=*)\[')


def tokens(raw):
    """Lua 5.1 code tokens, retaining exact spans; strings are opaque."""
    out=[];i=0
    while i<len(raw):
        c=raw[i]
        if c in b' \t\r\n\v\f':i+=1;continue
        start=i;comment=raw[i:i+2]==b'--'
        if comment:i+=2
        long=OPEN.match(raw,i)
        if long:
            end=raw.find(b']'+long[1]+b']',long.end())
            V.need(end>=0,'Unclosed Lua long literal/comment')
            i=end+len(long[1])+2
            if not comment:out.append(('string',start,i,raw[start:i]))
            continue
        if comment:
            end=raw.find(b'\n',i);i=len(raw) if end<0 else end+1;continue
        if c in (34,39):
            i+=1
            while i<len(raw) and raw[i]!=c:i+=2 if raw[i]==92 else 1
            V.need(i<len(raw),'Unclosed Lua quoted literal');i+=1
            out.append(('string',start,i,raw[start:i]));continue
        m=NUMBER.match(raw,i) if 48<=c<=57 else IDENT.match(raw,i)
        if m:
            i=m.end();out.append(('number' if 48<=c<=57 else 'name',start,i,m[0]));continue
        if raw[i:i+3]==b'...':i+=3
        elif raw[i:i+2] in (b'==',b'~=',b'<=',b'>=',b'..'):i+=2
        else:i+=1
        out.append(('symbol',start,i,raw[start:i]))
    return out


def declarations(raw):
    ends=[m.start() for m in re.finditer(b'\n',raw)];lines=defaultdict(list)
    for t in tokens(raw):lines[bisect.bisect_left(ends,t[1])].append(t)
    result={}
    for line,ts in lines.items():
        V.need(len(ts)>=3 and ts[0][0]=='name' and ts[1][3]==b'=',
               'Native definitions contain a non-declaration statement')
        name=ts[0][3];parts=[t[3] for t in ts[2:] if t[3]!=b';']
        V.need(name not in result,'Native constant is reassigned')
        def atom(p):
            if p in result:return result[p]
            if re.fullmatch(rb'-?\d+|0[xX][0-9a-fA-F]+',p):return str(int(p,16 if p.lower().startswith(b'0x') else 10)).encode()
            if re.fullmatch(rb'"[0-9]+"|true|false',p):return p
            raise ValueError('Unsupported native constant atom: '+repr(p))
        if len(parts)==2 and parts[0]==b'-':parts=[b'-'+parts[1]]
        if len(parts)==1:value=atom(parts[0])
        else:
            V.need(len(parts)%2==1 and all(p==b'+' for p in parts[1::2]),'Unsupported native constant expression')
            value=str(sum(int(atom(p)) for p in parts[::2])).encode()
        result[name]=value
    V.need(len(result)==6481 and result[b'LOCAL_FLAG']==b'0' and result[b'BATTLE_FLAG']==b'128',
           'Native definition inventory changed')
    return result


def bind(raw,constants):
    ts=tokens(raw);edits=[];counts=Counter();function_pending=False;function_args=0;depth=0
    local_line=None
    for j,(kind,a,z,value) in enumerate(ts):
        prev=ts[j-1][3] if j else None;nxt=ts[j+1][3] if j+1<len(ts) else None
        if local_line is not None and (b'\n' in raw[local_line:a] or prev==b'='):local_line=None
        if value==b'local':local_line=z
        if value==b'function':function_pending=True
        if value==b'(':
            depth+=1
            if function_pending:function_args=depth;function_pending=False
        elif value==b')':
            if function_args==depth:function_args=0
            depth-=1
        if kind!='name' or value not in constants:continue
        if prev in (b'.',b':'):continue
        V.need(nxt!=b'=' and prev not in (b'local',b'for',b'function') and not function_args and local_line is None,
               'Native shared constant is declared/shadowed by script: '+value.decode())
        edits.append((a,z,b'('+constants[value]+b')'));counts[value.decode()]+=1
    out=bytearray();position=0;spans=[]
    for a,z,replacement in edits:
        out+=raw[position:a];spans.append((len(out),len(replacement),raw[a:z]));out+=replacement;position=z
    out+=raw[position:]
    restored=bytearray(out)
    for a,n,original in reversed(spans):restored[a:a+n]=original
    V.need(bytes(restored)==raw and out.count(b'\n')==raw.count(b'\n'),'Constant binding escaped identifier spans')
    return bytes(out),dict(references=sum(counts.values()),names=dict(counts))


def apply(stage_members):
    with CPK(V.PLAIN/SHARED) as c:
        shared={r['id']:c.read(r) for r in c.files}
    constants=declarations(shared[1]);result={};reports={};padding={}
    # The native shared-Lua loader caches nine fixed lengths in EBOOT. Keep
    # those source extents intact, including the unchanged stage_require.
    sizes=[len(shared[i]) for i in range(9)]
    data=(V.WORK/'executables/segment-1.bin').read_bytes()
    pattern=struct.pack('<9I',*sizes);size_table=data.find(pattern)
    V.need(size_table>=0 and data.find(pattern,size_table+1)<0,'Native shared-Lua cached lengths differ')
    with CPK(V.PLAIN/STAGE) as c:
        stage={r['id']:stage_members.get(r['id'],c.read(r)) for r in c.files}
    for rel,members in ((STAGE,stage),(SHARED,shared)):
        changed={};checks=[]
        for mid,raw in members.items():
            if b'\0' in raw[:32] or (rel==SHARED and mid==1):continue
            output,check=bind(raw,constants)
            if output!=raw:
                if rel==SHARED:
                    V.need(len(output)<=len(raw),'Bound shared Lua outgrew its fixed native cache extent')
                    padding[mid]=len(raw)-len(output)
                    output+=b' '*padding[mid]
                changed[mid]=output;checks.append(dict(member=mid,input_sha256=sha256(raw),output_sha256=sha256(output),**check))
        result[rel]=changed;reports[rel]=checks
    # Keep all existing language/art changes as well as newly bound members.
    result[STAGE]={**stage_members,**result[STAGE]}
    return result,dict(source_definitions_sha256=sha256(shared[1]),constants=len(constants),
                       native_shared_cache=dict(data_offset=size_table,member_bytes=sizes,padding_bytes=padding,
                                                all_original_lengths_preserved=True),
                       native_values_verified=True,comments_strings_and_other_code_preserved=True,archives=reports)
