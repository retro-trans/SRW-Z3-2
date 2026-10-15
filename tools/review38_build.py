"""Prepare independent plain/native-label font styles on verified 0.5.37."""
import argparse
import copy
import json
import shutil
from tools.common import ROOT, contained, sha256, sha256_file, write_json
from tools import ui_build as F, ui_vwf_build as W, ui_layout_text as U
from tools import review38_fonts as S, title_screen as T, eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.38'
BASE=ROOT/'work/output/builds/0.5.37'
CHANGED={'TPACKPS3.CPK','AIDDATAPACK.CPK','EFFPS3.CPK'}


def font_check(old,new,mapping):
    import numpy as np
    from tools.native_labels import PREFIX
    before,after=F.atlas(old),F.atlas(new)
    restored=after.copy();plain=native=0
    for token,code in mapping.items():
        x,y=F.cell_xy(code);a=before[y:y+32,x:x+32];b=after[y:y+32,x:x+32]
        expected=F.glyph_pixels(W.raster(token)[0])
        if not np.array_equal(b,expected) or not np.array_equal(a&255,b&255):
            raise ValueError('Font fill changed or final planes differ: '+repr(token))
        if token.startswith(PREFIX):
            if not np.array_equal(a,b):raise ValueError('Existing original-label masks changed')
            native+=1
        else:
            if not np.array_equal(b>>8,b&255):raise ValueError('Ordinary letter retains a border')
            plain+=1
        restored[y:y+32,x:x+32]=a
    if new[:128]+restored.tobytes()!=old:
        raise ValueError('Font changed outside allocated cells')
    return dict(plain_cells=plain,native_label_cells=native,fill_unchanged=True,
                original_cells_unchanged=True,ordinary_outline_radius=0)


def ui_check(old,new,mapping):
    old_rows=U.ui_catalog.fssa_strings(old,decode=lambda raw:raw.hex())
    new_rows=U.ui_catalog.fssa_strings(new,decode=lambda raw:raw.hex())
    delta=len(new)-len(old)
    prior={at:r for r in old_rows for at in r['widget_offsets']}
    final={at-delta:r for r in new_rows for at in r['widget_offsets']}
    source_grow=len(old)-len(S.B.source())
    chosen={e['widget_offset']+source_grow:e for e in S.plan()['edits']}
    if prior.keys()!=final.keys():raise ValueError('UI widget identities changed')
    from tools.menu_layout import encode
    for at,row in prior.items():
        if old[at+4:at+32]!=new[at+delta+4:at+delta+32]:
            raise ValueError('Font selection changed geometry, colors or state')
        expected=encode(chosen[at],mapping) if at in chosen else row['raw']
        if final[at]['raw']!=expected:raise ValueError('Unrelated widget text changed')
    return dict(widgets=len(prior),native_headers=len(chosen),
                all_other_strings_unchanged=True,geometry_and_colors_unchanged=True)


def plan():
    from tools.pipeline import config
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Font builder version differs')
    prior=json.loads((BASE/'build.json').read_text('utf8'))
    proof=ROOT/'work/ui/review37_verified_0.5.37.json'
    ready=json.loads((ROOT/'work/ui/local_release_0.5.37.json').read_text('utf8'))
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Parent proof changed')
    for name,digest in prior['outputs'].items():
        if sha256_file(BASE/name)!=digest:raise ValueError('Parent output changed: '+name)
    mapping=prior['mapping'];drawn={t:W.raster(t) for t in mapping}
    if {t:w for t,(_,w) in drawn.items()}!=prior['widths']:
        raise ValueError('Letter advances changed; incremental font update is unsafe')
    for e in S.plan()['edits']:
        if any('@native-label:'+c not in mapping for c in e['en']):raise ValueError('New font allocation required')
    glyphs={t:g for t,(g,_) in drawn.items()}
    fonts={};font_reports={}
    with CPK(BASE/'TPACKPS3.CPK') as arc:
        for mid in (1,3):
            raw=arc.read(next(r for r in arc.files if r['id']==mid))
            fonts[mid]=F.patch_font(raw,mapping,glyphs)
            font_reports[mid]=font_check(raw,fonts[mid],mapping)
    art=U.plan(config(ROOT/'config/tengoku.json'),mapping)
    with CPK(BASE/'AIDDATAPACK.CPK') as arc:
        old=arc.read(next(r for r in arc.files if r['id']==0))
    ui_report=ui_check(old,art['members'][0],mapping)
    raw=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
    return dict(prior=prior,fonts=fonts,font_reports=font_reports,ui=art,ui_report=ui_report,
                title_bytes=title,title_info=info,parent_proof_sha256=sha256_file(proof))


def build(p):
    from tools.latin_font import profile
    folder=contained(ROOT/'work/output/builds',ROOT/'work/output/builds'/VERSION)
    if folder.exists():raise ValueError('Preserve existing candidate: '+VERSION)
    folder.mkdir(parents=True)
    report=copy.deepcopy(p['prior'])
    for name in report['outputs']:
        if name not in CHANGED:shutil.copyfile(BASE/name,folder/name)
    for name in ('rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,folder/name)
    for mid,data in p['fonts'].items():(folder/('font_%d.bin'%mid)).write_bytes(data)
    replacements={'TPACKPS3.CPK':p['fonts'],'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},
                  'EFFPS3.CPK':{T.MEMBER:p['title_bytes']}}
    archive_reports={}
    for name,members in replacements.items():
        with CPK(BASE/name) as arc:
            compressed={r['id'] for r in arc.files if r['id'] in members and r['size']!=r['extract']}
        build_cpk(BASE/name,folder/name,members,compress=compressed)
        archive_reports[name]=compare(BASE/name,folder/name,members)
    ui_verified=U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui'])
    report.update(version=VERSION,runtime_verified=False,layout_verified=False,latin_font=profile(),
                  title_screen=p['title_info'],ui_context_text=p['ui']['report']['context_text'])
    report['font_styles']=dict(pages=p['font_reports'],unit_list=p['ui_report'])
    report['font_archive']=archive_reports['TPACKPS3.CPK']
    report['extra_art']['AIDDATAPACK.CPK']=dict(archive=archive_reports['AIDDATAPACK.CPK'],members_verified=ui_verified)
    report['extra_art']['EFFPS3.CPK']=dict(archive=archive_reports['EFFPS3.CPK'],title=p['title_info'])
    for name in report['outputs']:report['outputs'][name]=sha256_file(folder/name)
    report['incremental_build']=dict(parent_version='0.5.37',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],unchanged_mapping=True,unchanged_advances=True,
        unchanged_executable=True,unchanged_stage_wrapper=True)
    write_json(folder/'build.json',report)
    print('Built 0.5.38: ordinary borders removed; original native-label alphabet retained; 19 unit-list headers separated.')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    p=plan();print('Font planes:',p['font_reports']);print('UI isolation:',p['ui_report'])
    if args.apply:build(p)
    else:print('DRY RUN: no game files written.')


if __name__=='__main__':main()
