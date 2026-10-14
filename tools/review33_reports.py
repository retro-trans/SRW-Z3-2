"""Source-bound reward report lines, preserving native rewards and paragraph copies."""
import argparse, json, struct
from tools.common import ROOT, sha256, write_json
from tools import review26_messages as G, review32_content as C, ui_hook as H, eboot_text as E
DEST=ROOT/'work/translation/en/ui/review33_reports.json'


def plan():
    strings={}
    for jp,row in G.plan()['strings'].items():
        if row['developer_only']:continue
        source=jp.split('\n');english=row['en'].split('\n')
        if len(source)!=len(english):raise ValueError('Report paragraph pairing changed')
        for key,en in [(jp,row['en']),*zip(source,english)]:
            prior=strings.setdefault(key,dict(en=en,occurrences=[]))
            if prior['en']!=en:raise ValueError('Conflicting report line translation')
            prior['occurrences'].append(dict(source_sha256=row['source_sha256'],count=len(row['occurrences'])))
    read=H._reader(H.PREPARED.read_bytes(),H._headers(H.PREPARED.read_bytes())[2])
    return dict(schema=1,version='0.5.33',player_notices=22,player_occurrences=97,
                strings=strings,native_copy_sha256=sha256(read(0x18c09c,0x158)),runtime_verified=False)


def hook_entries(original,mapping):
    data=plan()
    if json.loads(DEST.read_text('utf8'))!=data:raise ValueError('Report line plan stale')
    from tools.ui_description_layout import advance
    out=[]
    for jp,row in data['strings'].items():
        spans=[sum(map(advance,line))for line in row['en'].split('\n')]
        if max(spans)>1070:raise ValueError('Report line exceeds its panel')
        key=jp.encode('cp932')
        if H.extent(key+b'\0')!=len(key):raise ValueError('Invalid report draw key')
        out.append(dict(id='review33:report:'+sha256(key)[:16],key=key,
                        english=bytes.fromhex(mapping[C.CAPTION_MARK])+E.encode(row['en'],mapping)))
    return out


def native_lines(elf,source):
    """Execute the actual GIFT message branch, including its 128-byte row copies."""
    from tools import ppc_exec as P
    mem=P.Memory()
    for i,seg in enumerate(H._headers(elf)[2][:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=i==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x1000));mem.map(0x42000000,bytes(0x14)+source+b'\0')
    def string(at):
        for n in range(512):
            if mem.read(at+n,1)==b'\0':return mem.read(at,n)
        raise ValueError('Unterminated native report')
    def strchr(vm):
        n=string(vm.r[3]).find(bytes([vm.r[4]&255]));vm.r[3]=vm.r[3]+n if n>=0 else 0;vm.pc=vm.lr
    def memcpy(vm):mem.write(vm.r[3],mem.read(vm.r[4],vm.r[5]));vm.pc=vm.lr
    def strncpy(vm):
        raw=string(vm.r[4])[:vm.r[5]];mem.write(vm.r[3],raw+bytes(vm.r[5]-len(raw)));vm.pc=vm.lr
    vm=P.Machine(mem);vm.r=[0x770000+n for n in range(32)]
    vm.r[1]=0x40003000;vm.r[2]=H.TOC;vm.r[27]=0x42000000;vm.r[30]=0x41000000
    vm.pc=0x18c09c;vm.lr=0xdead0000
    vm.hooks={0x68f52c:strchr,0x6872cc:memcpy,0x68fca0:strncpy};vm.run({0x18c16c},limit=10000)
    count=mem.read(0x41000056,1)[0];lines=[string(0x41000098+n*128)for n in range(count)]
    if lines!=source.split(b'\n'):raise ValueError('Native report clips a source paragraph')
    if mem.read(0x4100029a,1)!=b'\x01':raise ValueError('Native report flag changed')
    return lines,vm.steps


def verify(elf,mapping,hook,layout):
    data=plan();entries=hook_entries(H.PREPARED.read_bytes(),mapping);bykey={r['key']:r for r in entries}
    runner=H._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes']);read=H._reader(elf,H._headers(elf)[2])
    for entry in entries:
        pointer,_=runner.run(entry['key']+b'\0')
        if read(pointer,len(entry['english'])+1)!=entry['english']+b'\0':raise ValueError('Final whole/line report lookup differs')
    copies=[]
    for jp,row in G.plan()['strings'].items():
        if row['developer_only']:continue
        lines,steps=native_lines(elf,jp.encode('cp932'))
        actual=[]
        for line in lines:
            entry=bykey[line];pointer,n=runner.run(line+b'\0')
            if read(pointer,len(entry['english'])+1)!=entry['english']+b'\0':raise ValueError('Final native report line is untranslated')
            actual.append(data['strings'][line.decode('cp932')]['en'])
        if '\n'.join(actual)!=row['en']:raise ValueError('Report loses words or reward amount')
        copies.append(dict(source_sha256=row['source_sha256'],english=row['en'],occurrences=len(row['occurrences']),steps=steps))
    from tools.ui_description_layout import advance
    rows=[(r['id'],r['english'],max(sum(map(advance,line))for line in data['strings'][r['key'].decode('cp932')]['en'].split('\n')),False)for r in entries]
    centered=C.origin_cases(elf,mapping,layout,only_rows=rows)
    return dict(player_notices=22,player_occurrences=97,draw_keys=len(entries),native_report_cases=copies,origin_cases=centered,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args();data=plan()
    for row in data['strings'].values():print(repr(row['en']))
    print('Draw keys:',len(data['strings']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no report bindings written.')

if __name__=='__main__':main()
