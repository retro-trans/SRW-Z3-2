"""Center scene captions and fit news headlines before their glyphs are drawn."""
from functools import lru_cache
from tools import library_build as L, eboot_text as E, ui_hook as H
from tools import ui_description_layout as W, dialogue_layout as A

CAPTION_MARK = '@scene-center'
HEADLINE_MARK = '@headline-center'
MARKERS = {CAPTION_MARK, HEADLINE_MARK}
HEADLINE_UNITS = 928  # 1160 pixels at the conservative 40-pixel news font


def caption(text):
    head, _, body = text.partition('\n')
    if head.strip('　 ') or '$' in head:
        return None
    lines = body.split('\n')
    decorated = [i for i, line in enumerate(lines)
                 if line.strip('　 ').startswith('～') and line.strip('　 ').endswith('～')]
    if len(decorated) != 1 or any(line.strip('　 ') for i, line in enumerate(lines) if i not in decorated):
        return None
    index = decorated[0]
    clean = ' '.join(lines[index].strip('　 ').replace('　', ' / ').split())
    if '$' in clean or sum(map(W.advance, clean)) > 1300:
        raise ValueError('Scene caption exceeds the reviewed fullscreen profile')
    lines[index] = clean
    return [head]+lines, index+1


def caption_encoded(text, mapping):
    profile = caption(text)
    if profile is None or CAPTION_MARK not in mapping:
        return None
    lines, index = profile
    encoded = [L.encode(line, mapping) for line in lines]
    encoded[index] = bytes.fromhex(mapping[CAPTION_MARK])+encoded[index]
    return b'\r\n'.join(encoded)


@lru_cache(None)
def headlines():
    active = E.load()['strings']; result = []; resolver=E.resolver()
    for source in E.records():
        va = int(source['va'], 16)
        if source['family'] != 'date_location' or not 0x8a0700 <= va < 0x8a1300:
            continue
        text = E.unshow(L.expand(active[source['jp']]['en'], resolver))
        lines = text.split('\n')
        if len(lines)>2: continue  # The three-row worldwide result is a separate layout.
        if len(lines) == 1 and sum(map(W.advance, text)) <= HEADLINE_UNITS:
            continue
        if len(lines) == 1:
            if ': ' not in text:
                raise ValueError('Long news headline needs a reviewed semantic break')
            front, body = text.split(': ', 1); lines = [front+':', body]
        if len(lines) != 2:
            raise ValueError('News headline must keep two rows')
        prefix = ''
        for candidate in ('', A.PREFIX, A.TIGHT_PREFIX):
            from tools.ui_vwf_build import raster
            measure = W.advance if not candidate else lambda c: raster(candidate+c)[1]
            spans = [sum(map(measure, line)) for line in lines]
            if max(spans) <= HEADLINE_UNITS:
                prefix = candidate; break
        else:
            raise ValueError('Complete news headline exceeds two rows')
        maximum = max(spans); space = measure(' ')
        padded = [' '*round((maximum-span)/2/space)+line for line, span in zip(lines, spans)]
        result.append(dict(va=source['va'], jp=source['jp'], lines=lines, padded=padded,
                           prefix=prefix, spans=spans, source_offset=int(source['offset'], 16)))
    if not any(r['va'] == '0x8a0ad0' for r in result):
        raise ValueError('Reported Wrath Babylon headline is absent')
    return result


def characters():
    tokens = set(MARKERS)
    for row in headlines():
        if row['prefix']:
            tokens.update(row['prefix']+c for line in row['lines'] for c in line)
    return tokens


def hook_entries(original, mapping):
    result = []
    for row in headlines():
        at = row['source_offset']; source = row['jp'].encode('utf8')
        if original[at:at+len(source)+1] != source+b'\0':
            raise ValueError('News headline source changed')
        selected = dict(mapping)
        if row['prefix']:
            selected.update({c: mapping[row['prefix']+c] for line in row['padded'] for c in line})
        result.append(dict(id='review32:headline:'+row['va'], key=H.utf8_key(source, original),
                           english=bytes.fromhex(mapping[HEADLINE_MARK])+L.encode('\n'.join(row['padded']), selected)))
    return result


def units(va, table):
    """Maximum line width for marked content only; native glyphs keep 32 units."""
    from tools.link_layout import Asm, BLR
    a = Asm(va); a.mr(4, 3); a.ptr(5, table)
    for r in (8, 9): a.d(0x38000000, r, 0, 0)
    a.d(0x38000000, 11, 0, 4096)
    a.label('loop'); a.d(0x88000000, 6, 4, 0); a.d(0x2c000000, 0, 6, 0); a.br(0x41820000, 'done')
    a.d(0x2c000000, 0, 6, 10); a.br(0x41820000, 'newline')
    a.d(0x38000000, 6, 6, -0x81); a.d(0x28000000, 0, 6, 0x7b); a.br(0x41810000, 'bad')
    a.d(0x88000000, 7, 4, 1); a.d(0x38000000, 7, 7, -0x40)
    a.d(0x28000000, 0, 7, 0xbc); a.br(0x41810000, 'bad')
    a.d(0x28000000, 0, 6, 7); a.br(0x41810000, 'wide')
    a.d(0x1c000000, 6, 6, 192); a.x(0x7c000214, 6, 6, 7); a.x(0x7c0000ae, 6, 5, 6)
    a.br(0x48000000, 'add')
    a.label('wide'); a.d(0x38000000, 6, 0, 32)
    a.label('add'); a.x(0x7c000214, 8, 8, 6); a.d(0x38000000, 4, 4, 2); a.br(0x48000000, 'tick')
    a.label('newline'); a.e(0x7c084840); a.br(0x40810000, 'reset'); a.mr(9, 8)
    a.label('reset'); a.d(0x38000000, 8, 0, 0); a.d(0x38000000, 4, 4, 1)
    a.label('tick'); a.d(0x38000000, 11, 11, -1); a.d(0x2c000000, 0, 11, 0); a.br(0x40820000, 'loop')
    a.label('bad'); a.d(0x38000000, 3, 0, -1); a.e(BLR)
    a.label('done'); a.e(0x7c084840); a.br(0x40810000, 'max'); a.mr(9, 8)
    a.label('max'); a.mr(3, 9); a.e(BLR)
    return a.code()


def origin(va, state, measure, specs, legacy):
    """Preserve all scratch registers; alter only marked text origins/pointers."""
    from tools.link_layout import Asm, integer_float
    a = Asm(va); a.d(0xf8000001, 1, 1, -0x100)
    for r in range(3, 13): a.d(0xf8000000, r, 1, 0x10+(r-3)*8)
    a.d(0xf8000000, 0, 1, 0x60); a.e(0x7c000026); a.d(0x90000000, 0, 1, 0x68)
    a.e(0x7c0802a6); a.d(0xf8000000, 0, 1, 0x70)
    for f in range(10, 14): a.d(0xd8000000, f, 1, 0x80+(f-10)*8)
    a.d(0x88000000, 9, 31, 0); a.d(0x2c000000, 0, 9, 0); a.br(0x41820000, 'legacy')
    a.d(0xa0000000, 9, 31, 0)
    for i, spec in enumerate(specs):
        a.d(0x28000000, 0, 9, spec['code']); a.br(0x41820000, 'content%d' % i)
    a.br(0x48000000, 'legacy')
    for i, spec in enumerate(specs):
        a.label('content%d' % i); a.d(0x38000000,12,0,int(spec['two_lines']));a.br(0x48000000,'content')
    a.label('content');a.d(0x38000000,31,31,2);a.mr(3,31);a.call(measure)
    a.d(0x2c000000,0,3,-1);a.br(0x41820000,'done')
    integer_float(a,3,10,slot=0xa0);a.d(0xc0000000,11,30,0x54)
    a.e(0xec000032 | 10<<21 | 10<<16 | 11<<6)
    a.ptr(9,0x3c800000);a.d(0x90000000,9,1,0xa8);a.d(0xc0000000,11,1,0xa8)
    a.e(0xec000032 | 10<<21 | 10<<16 | 11<<6)
    a.ptr(9,0x44200000);a.d(0x90000000,9,1,0xa8);a.d(0xc0000000,11,1,0xa8)
    a.x(0xec000028,31,11,10);a.d(0x2c000000,0,12,0);a.br(0x41820000,'done')
    a.d(0xc0000000,10,30,0x60)
    a.ptr(9,0x3f000000);a.d(0x90000000,9,1,0xa8);a.d(0xc0000000,11,1,0xa8)
    a.e(0xec000032 | 10<<21 | 10<<16 | 11<<6);a.x(0xec000028,30,30,10)
    a.br(0x48000000,'done')
    a.label('legacy')
    for i, spec in enumerate(legacy):
        a.d(0x28000000, 0, 9, spec['code']); a.br(0x40820000, 'old%d' % i)
        import struct
        a.ptr(9, struct.unpack('>I', struct.pack('>f', spec['delta_cells']))[0])
        a.d(0x90000000, 9, 1, 0xa8); a.d(0xc0000000, 10, 1, 0xa8); a.d(0xc0000000, 11, 30, 0x54)
        a.e(0xec000032 | 10<<21 | 10<<16 | 11<<6); a.x(0xec00002a, 31, 31, 10)
        a.d(0x38000000, 31, 31, 2); a.br(0x48000000, 'done'); a.label('old%d' % i)
    a.label('done'); a.ptr(9, state); a.d(0xd0000000, 31, 9, 1024)
    for f in range(10, 14): a.d(0xc8000000, f, 1, 0x80+(f-10)*8)
    a.d(0xe8000000, 0, 1, 0x70); a.e(0x7c0803a6)
    a.d(0x80000000, 0, 1, 0x68); a.e(0x7c0ff120)
    a.d(0xe8000000, 0, 1, 0x60)
    for r in range(3, 13): a.d(0xe8000000, r, 1, 0x10+(r-3)*8)
    a.d(0x38000000, 1, 1, 0x100); a.e(0xd3fe004c); a.jump(0x141ac)
    return a.code()


def origin_cases(elf, mapping, report, only_rows=None, quads=None):
    """Execute the installed marker origin helper with real caption/headline bytes."""
    import struct
    from tools import ppc_exec as P, dialogue_build as D
    rows=[];resolver=E.resolver()
    for rid,entry in D.translations().items():
        if entry['en'].partition('\n')[0].strip('　 '):continue
        expanded=L.expand(entry['en'],resolver); profile=caption(expanded)
        if profile:
            lines,index=profile; raw=bytes.fromhex(mapping[CAPTION_MARK])+L.encode(lines[index],mapping)
            rows.append((rid,raw,sum(map(W.advance,lines[index])),False))
    for row,entry in zip(headlines(),hook_entries(H.PREPARED.read_bytes(),mapping)):
        rows.append((row['va'],entry['english'],max(row['spans']),True))
    if only_rows is not None:rows=only_rows
    mem=P.Memory()
    for i,seg in enumerate(H._headers(elf)[2][:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=i==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x1000));mem.map(0x42000000,bytes(0x1000))
    cases=[]
    for rid,raw,span,two_lines in rows:
        for quad in (quads or ((28,40)if two_lines else (28,))):
            mem.write(0x42000000,raw+b'\0');mem.write(0x41000000,bytes(0x1000))
            mem.write(0x41000054,struct.pack('>f',quad));mem.write(0x41000060,struct.pack('>f',quad))
            vm=P.Machine(mem);vm.r=[0x770000+r for r in range(32)]
            vm.r[1]=0x40003f00;vm.r[2]=H.TOC;vm.r[30]=0x41000000;vm.r[31]=0x42000000
            vm.f[30]=360;vm.f[31]=99;vm.cr=0xb3c7a965;vm.lr=0xdead0000
            before=(vm.r[:],vm.f[:],vm.cr,vm.lr);vm.pc=0x141a8
            vm.run({0x141ac},limit=10000)
            expected=640-span*quad/64
            if abs(vm.f[31]-expected)>0.0001 or vm.f[30]!=360-(quad/2 if two_lines else 0):
                raise ValueError('Marked text origin differs: '+rid)
            if vm.r[31]!=0x42000002 or any(vm.r[r]!=before[0][r]for r in range(31)) or vm.cr!=before[2]or vm.lr!=before[3]:
                raise ValueError('Content centering changes caller state')
            if vm.f[10:14]!=before[1][10:14]:raise ValueError('Content centering changes scratch floats')
            cases.append(dict(id=rid,quad=quad,span_units=span,left=expected,center=640,two_lines=two_lines,steps=vm.steps))
    return cases
