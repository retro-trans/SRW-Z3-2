"""Build the scoped Tengoku Spirit data/font patch; dry-run by default.

Requires Pillow and numpy (available in the bundled Python). No executable
patch, old game addresses, or legacy font allocation is used by this builder.
"""
import argparse
import json
import struct
from pathlib import Path

from tools.common import ROOT, contained, sha256, sha256_file, write_json
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.inventory import RPW, FONT
from tools.pipeline import config, verified_source
from tools.source_text import rpw_chunks
from tools.ui_spirits import load_and_validate
from tools.verify_archives import compare

FACE = Path('E:/RPCS3/dev_flash/data/font/SCE-PS3-RD-R-LATIN.TTF')


def pairs(text):
    return [line[i:i+2].ljust(2) for line in text.split('\n') for i in range(0, len(line), 2)]


def encode(text, mapping, codec='pairs', abbreviation=False):
    if codec == 'vwf':
        tokens = ['@badge:'+text] if abbreviation else list(text)
        return b''.join(b'\n' if t == '\n' else bytes.fromhex(mapping[t]) for t in tokens)
    return b'\n'.join(b''.join(bytes.fromhex(mapping[p]) for p in pairs(line))
                      for line in text.split('\n'))


def decode(data, mapping, codec='pairs'):
    inverse = {bytes.fromhex(code): pair for pair, code in mapping.items()}
    result = []
    for line in data.split(b'\n'):
        if len(line) % 2:
            raise ValueError('odd encoded line')
        tokens = [inverse[line[i:i+2]] for i in range(0, len(line), 2)]
        text = ''.join(t[7:] if codec == 'vwf' and t.startswith('@badge:') else t for t in tokens)
        result.append(text if codec == 'vwf' else text.rstrip(' '))
    return '\n'.join(result)


def atlas(raw):
    import numpy as np
    if len(raw) != 128 + 4096*1120*2 or raw[24] != 0xab or struct.unpack_from('>HH', raw, 32) != (4096, 1120):
        raise ValueError('target font format changed')
    return np.frombuffer(raw[128:], dtype='>u2').reshape(1120, 4096)


def cell_xy(code):
    hi, lo = bytes.fromhex(code)
    if not 0x81 <= hi <= 0x88 or not 0x40 <= lo <= 0xfc or lo == 0x7f:
        raise ValueError('code outside verified font ranges')
    idx = (hi-0x81)*192 + lo-0x40
    y, x = divmod(idx, 128)
    return x*32, y*32


def allocate(pages, texts, tokenize=pairs):
    free = []
    planes = [atlas(raw) for raw in pages]
    for hi in range(0x81,0x89):
        for lo in range(0x40, 0xfd):
            # 0x5B/0x5D are ASCII [ and ]: as a trail byte next to a Lua
            # long-string delimiter they would form [[ or ]] in stage scripts.
            if lo in (0x7f, 0x5b, 0x5d):
                continue
            code = bytes((hi, lo))
            try:
                code.decode('cp932')
            except UnicodeDecodeError:
                pass
            else:
                continue
            x, y = cell_xy(code.hex())
            if all(not a[y:y+32, x:x+32].any() for a in planes):
                free.append(code.hex())
    needed = sorted({pair for text in texts for pair in tokenize(text)})
    if len(needed) > len(free):
        raise ValueError('insufficient verified blank cells: %d needed, %d free' % (len(needed), len(free)))
    return dict(zip(needed, free)), len(free)


def raster(pair, face):
    """Two condensed Latin letters in a 32px cell, supersampled 4x.

    Geometry is local to this font build. Runtime spacing/fit must still be
    measured; it is not taken from Jigoku's atlas or advance constants.
    """
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('L', (128, 128))
    font = ImageFont.truetype(str(face), 116)
    for i, ch in enumerate(pair):
        if ch == ' ':
            continue
        box = font.getbbox(ch, anchor='ls')
        glyph = Image.new('L', (box[2]-box[0]+8, box[3]-box[1]+8))
        ImageDraw.Draw(glyph).text((4-box[0], 4-box[1]), ch, font=font, anchor='ls', fill=255)
        # Cap height 22 atlas texels; preserve the baseline for punctuation.
        hbox = font.getbbox('H', anchor='ls')
        scale = 88.0 / (hbox[3]-hbox[1])
        width = min(56, max(1, round(glyph.width*scale)))
        height = max(1, round(glyph.height*scale))
        glyph = glyph.resize((width, height), Image.Resampling.LANCZOS)
        img.paste(glyph, (i*64 + (64-width)//2, round(104 + (box[1]-4)*scale)))
    return img.resize((32, 32), Image.Resampling.LANCZOS)


def patch_font(raw, mapping, glyphs):
    import numpy as np
    a = atlas(raw).copy()
    for pair, code in mapping.items():
        x, y = cell_xy(code)
        coverage = np.asarray(glyphs[pair], dtype='uint16')
        # Source pages encode coverage in all four nibbles (RGBA4444).
        values = ((coverage + 8)//17).clip(0, 15)*0x1111
        a[y:y+32, x:x+32] = values
    return raw[:128] + a.tobytes()


def patch_rpw(original, entries, mapping, codec='pairs'):
    chunks = rpw_chunks(original)
    js = next(c for c in chunks if c['name'] == 'j-string')
    spirit = next(c for c in chunks if c['name'] == 'spirit')
    allowed = {spirit['body_offset'] + i*20 + c*4 for i in range(1,44) for c in (1,2,3)}
    locations = [r['pointer_offset'] for r in entries]
    if len(locations) != len(set(locations)) or set(locations) != allowed:
        raise ValueError('patch scope is not the complete reviewed Spirit occurrence set')
    suffix, allocated, edits = bytearray(), {}, []
    pool_size = js['body_end'] - js['body_offset']
    base = bytearray(original)
    for row in entries:
        old = struct.unpack_from('<I', original, row['pointer_offset'])[0]
        if old != row['string_body_offset']:
            raise ValueError('pointer drift')
        encoded = encode(row['rendered_en'], mapping, codec,
                         row['occurrence_id'].endswith(':abbreviation'))
        if decode(encoded, mapping, codec) != row['rendered_en']:
            raise ValueError('English encoding changed text')
        if encoded not in allocated:
            allocated[encoded] = pool_size + len(suffix)
            suffix.extend(encoded + b'\0')
        value = allocated[encoded]
        struct.pack_into('<I', base, row['pointer_offset'], value)
        edits.append({'occurrence_id': row['occurrence_id'], 'source_pointer_offset': row['pointer_offset'],
                      'old': old, 'new': value, 'bytes': len(encoded), 'english': row['rendered_en'], 'codec':codec})
    suffix.extend(bytes((-len(suffix)) % 4))
    grow = len(suffix)
    for off in (24, 28, js['offset']+20, js['offset']+24):
        struct.pack_into('<I', base, off, struct.unpack_from('<I', original, off)[0]+grow)
    out = bytes(base[:js['body_end']] + suffix + base[js['body_end']:])
    verify_rpw(original, out, edits, mapping)
    return out, edits, grow


def verify_rpw(original, patched, edits, mapping):
    old = rpw_chunks(original)
    new = rpw_chunks(patched)
    if [c['name'] for c in old] != [c['name'] for c in new]:
        raise ValueError('RPW chunk list changed')
    js = next(c for c in old if c['name']=='j-string')
    nj = next(c for c in new if c['name']=='j-string')
    grow = len(patched)-len(original)
    if patched[nj['body_offset']:nj['body_offset']+js['body_end']-js['body_offset']] != original[js['body_offset']:js['body_end']]:
        raise ValueError('original pool bytes/ordinals changed')
    restored = bytearray(patched[:js['body_end']] + patched[js['body_end']+grow:])
    for edit in edits:
        off = edit['source_pointer_offset']
        actual_off = off + (grow if off >= js['body_end'] else 0)
        ptr = struct.unpack_from('<I', patched, actual_off)[0]
        if ptr != edit['new'] or not js['body_end']-js['body_offset'] <= ptr < nj['body_end']-nj['body_offset']:
            raise ValueError('relocated pointer mismatch')
        pos = nj['body_offset']+ptr
        raw = patched[pos:patched.index(b'\0',pos,nj['body_end'])]
        if decode(raw,mapping,edit.get('codec','pairs')) != edit['english']:
            raise ValueError('binary text readback mismatch')
        struct.pack_into('<I', restored, off, edit['old'])
    for off in (24,28,js['offset']+20,js['offset']+24):
        restored[off:off+4] = original[off:off+4]
    if bytes(restored) != original:
        raise ValueError('unrelated RPW bytes changed')


def plan(settings, face=FACE):
    checked = load_and_validate(settings)
    font_path = verified_source(settings,FONT)
    rpw_path = verified_source(settings,RPW)
    k = CPK(font_path)
    pages = {e['id']:k.read(e) for e in k.files if e['id'] in (1,3)}
    if set(pages)!={1,3}:
        raise ValueError('missing target font pages')
    mapping, free = allocate(list(pages.values()), [r['rendered_en'] for r in checked['entries']])
    r = CPK(rpw_path)
    original = r.read(r.files[0])
    patched, edits, grow = patch_rpw(original, checked['entries'], mapping)
    return {'settings':settings, 'pages':pages, 'mapping':mapping, 'rpw':patched,
            'edits':edits, 'face':face, 'font_path':font_path, 'rpw_path':rpw_path,
            'summary': {'title_id':'BLJS10299', 'translated_occurrences':len(edits),
                        'new_pool_bytes':grow, 'allocated_cells':len(mapping), 'available_blank_cells':free,
                        'font_sha256':sha256_file(font_path), 'face_sha256':sha256_file(face),
                        'runtime_verified':False, 'layout_verified':False}}


def build(planned, output):
    from PIL import Image, ImageDraw
    p = planned
    output = contained(ROOT/'work',output)
    output.mkdir(parents=True, exist_ok=False)
    glyphs = {pair:raster(pair,p['face']) for pair in p['mapping']}
    font_members = {}
    for fid, raw in p['pages'].items():
        modified = patch_font(raw,p['mapping'],glyphs)
        restored = atlas(modified).copy()
        original_plane = atlas(raw)
        for code in p['mapping'].values():
            x,y=cell_xy(code)
            restored[y:y+32,x:x+32] = original_plane[y:y+32,x:x+32]
        if raw[:128]+restored.tobytes()!=raw:
            raise ValueError('unallocated font cells changed')
        path = output/('font_%d.bin'%fid)
        path.write_bytes(modified)
        font_members[fid]=path
    rp=output/'rpw.bin'
    rp.write_bytes(p['rpw'])
    build_cpk(p['rpw_path'],output/'RPW_DATA.CPK',{0:rp})
    build_cpk(p['font_path'],output/'TPACKPS3.CPK',font_members)
    report=dict(p['summary'],schema=1,
                rpw_archive=compare(p['rpw_path'],output/'RPW_DATA.CPK',{0:p['rpw']}),
                font_archive=compare(p['font_path'],output/'TPACKPS3.CPK',
                                     {fid:path.read_bytes() for fid,path in font_members.items()}),
                mapping=p['mapping'],edits=p['edits'])
    write_json(output/'build.json',report)
    # Contact sheet is a texture preview, not a game screenshot.
    preview=Image.new('RGB',(1050, 86*len(p['edits'])), '#18202c')
    draw=ImageDraw.Draw(preview)
    y=0
    for edit in p['edits']:
        draw.text((4,y),edit['occurrence_id'],fill='white')
        for row,line in enumerate(edit['english'].split('\n')):
            for col,pair in enumerate(pairs(line)):
                preview.paste('white',(90+col*32,y+16+row*32,122+col*32,y+48+row*32),glyphs[pair])
        y+=86
    preview.save(output/'font_preview.png')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='work/output/builds/ui-0.1.0')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    p=plan(config(ROOT/'config/tengoku.json'))
    print(json.dumps(p['summary'],indent=2))
    for row in p['edits']:
        print('%s: %s -> +%d (%d bytes)'%(row['occurrence_id'],row['english'].replace('\n',' / '),row['new'],row['bytes']))
    if args.apply:
        build(p,ROOT/args.output)
        print('Built and independently read back both archives. Runtime verification pending.')
    else:
        print('DRY RUN: no outputs written')

if __name__=='__main__':
    main()
