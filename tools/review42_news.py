"""Relocate complete news paragraphs before the native 128-byte row splitter.

ASCII UTF-8 input rows fit the constructor's byte limit. Exact draw keys then
select the existing English alphabet and center each row independently.
The original Japanese strings remain intact for other consumers and audits.
"""
import argparse, json, struct
from tools.common import ROOT, sha256, write_json
from tools import ui_hook as H, eboot_text as E, library_build as L, review35_news as N
from tools import review32_content as C, ui_description_layout as W, dialogue_layout as A

DEST=ROOT/'work/translation/en/ui/review42_news.json'
TABLE=0xa1f984


def plan():
    original=H.PREPARED.read_bytes();read=H._reader(original,H._headers(original)[2])
    profiles={r['va']:r for r in C.headlines()};rows=[]
    for row in N.plan()['rows']:
        profile=profiles.get(row['va'])
        lines=profile['lines'] if profile and len(row['english'])==1 else row['english']
        prefix=''
        for prefix in ('',A.PREFIX,A.TIGHT_PREFIX):
            from tools.ui_vwf_build import raster
            measure=W.advance if not prefix else lambda c:raster(prefix+c)[1]
            spans=[sum(map(measure,line)) for line in lines]
            if max(spans)<=C.HEADLINE_UNITS:break
        else:raise ValueError('News line exceeds screen width: '+row['va'])
        raw='\n'.join(lines).encode('ascii')
        if len(lines)>8 or any(not line or len(line.encode('ascii'))>=128 for line in lines):
            raise ValueError('News paragraph exceeds native row allocation')
        bindings=[]
        for index in row['scenario_indices']:
            at=TABLE+index*52+36
            if int.from_bytes(read(at,4),'big')!=int(row['va'],16):raise ValueError('Scenario source binding differs')
            bindings.append(dict(va=at,old=int(row['va'],16)))
        rows.append(dict(id='review42:news:'+row['va'],source_va=row['va'],
            source_sha256=row['source_sha256'],english=lines,prefix=prefix,spans=spans,
            utf8_sha256=sha256(raw),bindings=bindings))
    return dict(schema=1,version='0.5.42',rows=rows,paragraphs=len(rows),
                scenario_occurrences=sum(len(r['bindings'])for r in rows),runtime_verified=False)


def runtime_plan(mapping):
    data=plan()
    if json.loads(DEST.read_text(encoding='utf8'))!=data:raise ValueError('News plan is stale')
    payloads=[];pointers=[]
    for row in data['rows']:
        payloads.append((row['id'],'\n'.join(row['english']).encode('ascii')+b'\0'))
        pointers.extend(dict(id=row['id'],offset=b['va']-0x10000,old=b['old'])for b in row['bindings'])
    return dict(payloads=payloads,pointers=pointers,inline=[],report=dict(paragraphs=data['paragraphs'],
                scenario_occurrences=data['scenario_occurrences'],runtime_verified=False))


def hook_entries(original,mapping):
    out={}
    for row in plan()['rows']:
        selected=dict(mapping)
        if row['prefix']:selected.update({c:mapping[row['prefix']+c]for line in row['english']for c in line})
        for n,line in enumerate(row['english']):
            key=H.utf8_key(line.encode('ascii'),original)
            english=bytes.fromhex(mapping[C.CAPTION_MARK])+L.encode(line,selected)
            if key in out and out[key]['english']!=english:raise ValueError('Conflicting English news row')
            out[key]=dict(id=row['id']+':'+str(n),key=key,english=english)
    return list(out.values())


def verify(elf,mapping,hook,layout):
    data=plan();read=H._reader(elf,H._headers(elf)[2]);original=H.PREPARED.read_bytes()
    from tools import ppc_exec as P
    # The real constructor calls this selector; bind the patched pointers
    # through that instruction path rather than assuming a table address.
    source_read=H._reader(original,H._headers(original)[2])
    for at,size in ((0x184c14,4),(0x1dcbfc,0x34)):
        if read(at,size)!=source_read(at,size):raise ValueError('Native news selector path changed')
    mem=P.Memory()
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    wanted={r['key']:r for r in hook_entries(original,mapping)}
    runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);cases=[]
    for row in data['rows']:
        for binding in row['bindings']:
            machine=P.Machine(mem);machine.r[2]=H.TOC;machine.r[3]=(binding['va']-TABLE-36)//52
            machine.lr=0xdead0000;machine.pc=0x1dcbfc;machine.run({0xdead0000},limit=50)
            if machine.r[3]+36!=binding['va']:raise ValueError('Native selector returns a different scenario')
            va=int.from_bytes(read(machine.r[3]+36,4),'big')
            raw='\n'.join(row['english']).encode('ascii')
            if read(va,len(raw)+1)!=raw+b'\0':raise ValueError('Actual scenario paragraph not relocated')
            lines,steps=N.native_lines(elf,read(va,len(raw)))
            for line in lines:
                key=H.utf8_key(line,original);english=wanted[key]['english'];pointer,_=runner.run(key+b'\0')
                if read(pointer,len(english)+1)!=english+b'\0':raise ValueError('News draw row is not English')
            cases.append(dict(source_va=row['source_va'],scenario_pointer=binding['va'],rows=len(lines),
                              native_selector_steps=machine.steps,native_steps=steps))
    # Exercise the installed origin helper for each actual English row.
    origins=[]
    for row in data['rows']:
        for line,span in zip(row['english'],row['spans']):
            entry=wanted[H.utf8_key(line.encode('ascii'),original)]
            origins.append((entry['id'],entry['english'],span,False))
    centered=C.origin_cases(elf,mapping,layout,only_rows=origins,quads=(28,40))
    return dict(paragraphs=data['paragraphs'],scenario_occurrences=len(cases),native_copy_cases=cases,
                origin_cases=centered,draw_keys=len(wanted),runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['rows']:print(row['source_va'],row['english'],row['spans'])
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no news data written.')

if __name__=='__main__':main()
