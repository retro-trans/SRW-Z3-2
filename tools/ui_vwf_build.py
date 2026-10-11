"""Build a matched Tengoku VWF executable, Spirit archive and font. Dry-run first."""
import argparse
import json
from tools.common import ROOT, contained, sha256_file, write_json
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.inventory import RPW, FONT
from tools.pipeline import config, verified_source
from tools.ui_spirits import load_and_validate
from tools.ui_build import FACE, allocate, atlas, cell_xy, patch_font, patch_rpw
from tools.verify_archives import compare
from tools.self_elf import decrypt, EBOOT
from tools.vwf import patch

VERSION = 'ui-0.1.1-vwf'


def raster(token, face=FACE):
    from PIL import Image, ImageDraw, ImageFont
    from tools.menu_layout import PADS
    if token in PADS: return Image.new('L',(32,32)),PADS[token]
    from tools.status_layout import TINY,MARKERS,raster_tiny
    if token in TINY:return raster_tiny(TINY[token],face)
    if token in MARKERS.values():return Image.new('L',(32,32)),32
    from tools import battle_layout
    if token in battle_layout.TINY:return battle_layout.raster_tiny(battle_layout.TINY[token],face)
    from tools import dialogue_layout as layout
    for prefix,scale in ((layout.PREFIX,layout.SCALE),(layout.TIGHT_PREFIX,layout.TIGHT_SCALE)):
        if token.startswith(prefix):
            glyph, width = raster(token[len(prefix):], face)
            narrow = glyph.resize((round(32 * scale), 32), Image.Resampling.LANCZOS)
            cell = Image.new('L', (32, 32))
            cell.paste(narrow, (0, 0))
            return cell, layout.advance(width,scale)
    badge = token.startswith('@badge:')
    text = token[7:] if badge else token
    if not badge:
        from tools.latin_font import letter
        return letter(text,face)
    font = ImageFont.truetype(str(face),116)
    hb = font.getbbox('H',anchor='ls')
    scale = (12 if badge else 22)*4/(hb[3]-hb[1])
    canvas = Image.new('L',(128,128))
    if text == ' ': return canvas.resize((32,32)),9
    box = font.getbbox(text,anchor='ls')
    natural = Image.new('L',(box[2]-box[0]+8,box[3]-box[1]+8))
    ImageDraw.Draw(natural).text((4-box[0],4-box[1]),text,font=font,anchor='ls',fill=255)
    width,height = max(1,round(natural.width*scale)),max(1,round(natural.height*scale))
    if badge: width=min(width,104)
    elif width>128: raise ValueError('single glyph exceeds cell: '+text)
    glyph = natural.resize((width,height),Image.Resampling.LANCZOS)
    left = (128-width)//2 if badge else max(0,round((box[0]-4)*scale))
    top = round((22 if badge else 25)*4+(box[1]-4)*scale)
    if top < 0 or top+height>128 or left+width>128:
        raise ValueError('glyph would clip: '+repr(text))
    canvas.paste(glyph,(left,top))
    advance = 32 if badge else round(font.getlength(text)*scale/4+1)
    if not badge and not 1 <= advance <= 31:
        raise ValueError('glyph advance outside narrow range')
    return canvas.resize((32,32),Image.Resampling.LANCZOS),advance


def plan(settings):
    rows = load_and_validate(settings)['entries']
    font_path, rpw_path = verified_source(settings,FONT), verified_source(settings,RPW)
    font = CPK(font_path)
    pages = {e['id']:font.read(e) for e in font.files if e['id'] in (1,3)}
    if set(pages) != {1,3}: raise ValueError('missing font page')
    tokens = set()
    for row in rows:
        if row['occurrence_id'].endswith(':abbreviation'):
            tokens.add('@badge:'+row['rendered_en'])
        else: tokens.update(row['rendered_en'].replace('\n',''))
    mapping,free = allocate(list(pages.values()),tokens,lambda t:[t])
    drawn = {t:raster(t) for t in mapping}
    glyphs = {t:g for t,(g,w) in drawn.items()}
    widths = {}
    for token,code in mapping.items():
        x,y = cell_xy(code)
        if drawn[token][1] != 32: widths[y//32*128+x//32] = drawn[token][1]
    r = CPK(rpw_path)
    rpw,edits,grow = patch_rpw(r.read(r.files[0]),rows,mapping,'vwf')
    elf,source_report = decrypt(verified_source(settings,EBOOT).read_bytes())
    executable,exec_report = patch(elf,widths)
    exec_report.update(source_report)
    summary = {'schema':2,'version':VERSION,'title_id':'BLJS10299','encoding':'vwf',
        'translated_occurrences':len(edits),'allocated_cells':len(mapping),
        'letter_cells':len(widths),'badge_cells':len(mapping)-len(widths),
        'available_blank_cells':free,'new_pool_bytes':grow,
        'face_sha256':sha256_file(FACE),'executable':exec_report,
        'runtime_verified':False,'layout_verified':False}
    return dict(summary=summary,mapping=mapping,glyphs=glyphs,drawn=drawn,pages=pages,
        rpw=rpw,edits=edits,executable=executable,font_path=font_path,rpw_path=rpw_path)


def build(p, output):
    from PIL import Image,ImageDraw
    output = contained(ROOT/'work',output)
    output.mkdir(parents=True,exist_ok=False)
    members = {}
    for fid,raw in p['pages'].items():
        modified = patch_font(raw,p['mapping'],p['glyphs'])
        restored = atlas(modified).copy()
        for code in p['mapping'].values():
            x,y = cell_xy(code)
            restored[y:y+32,x:x+32] = atlas(raw)[y:y+32,x:x+32]
        if raw[:128]+restored.tobytes()!=raw: raise ValueError('unallocated font changed')
        members[fid] = output/('font_%d.bin'%fid)
        members[fid].write_bytes(modified)
    rp = output/'rpw.bin'; rp.write_bytes(p['rpw'])
    build_cpk(p['rpw_path'],output/'RPW_DATA.CPK',{0:rp})
    build_cpk(p['font_path'],output/'TPACKPS3.CPK',members)
    ep = output/'EBOOT.BIN'; ep.write_bytes(p['executable'])
    if sha256_file(ep)!=p['summary']['executable']['output_sha256']:
        raise ValueError('executable readback mismatch')
    report = dict(p['summary'],mapping=p['mapping'],edits=p['edits'],
        widths={t:w for t,(g,w) in p['drawn'].items()},
        rpw_archive=compare(p['rpw_path'],output/'RPW_DATA.CPK',{0:p['rpw']}),
        font_archive=compare(p['font_path'],output/'TPACKPS3.CPK',
                             {fid:path.read_bytes() for fid,path in members.items()}))
    write_json(output/'build.json',report)
    # Atlas geometry only: the game scales each glyph with its live quad size.
    preview = Image.new('RGB',(1450,86*len(p['edits'])),'#18202c')
    draw = ImageDraw.Draw(preview)
    for n,edit in enumerate(p['edits']):
        y=n*86
        draw.text((4,y),edit['occurrence_id'],fill='white')
        for line_n,line in enumerate(edit['english'].split('\n')):
            tokens = ['@badge:'+line] if edit['occurrence_id'].endswith(':abbreviation') else list(line)
            x=90
            for token in tokens:
                glyph,width=p['drawn'][token]
                if x+32>preview.width: raise ValueError('preview exceeds line width')
                preview.paste('white',(x,y+16+32*line_n,x+32,y+48+32*line_n),glyph)
                x+=width
    preview.save(output/'font_preview.png')
    preview.crop((0,0,1450,1032)).save(output/'font_preview_sample.png')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='work/output/builds/'+VERSION)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    p=plan(config(ROOT/'config/tengoku.json'))
    print(json.dumps(p['summary'],indent=2))
    for edit in p['edits']:
        print('%s: %s (%d bytes)'%(edit['occurrence_id'],edit['english'].replace('\n',' / '),edit['bytes']))
    if args.apply:
        build(p,ROOT/args.output)
        print('Built and read back matched executable, font and Spirit archives. Runtime pending.')
    else: print('DRY RUN: no outputs written')

if __name__=='__main__':main()
