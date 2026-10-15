"""Prepare four map-selector widgets on certified 0.5.38; dry-run first."""
import argparse,copy,json,shutil,struct
from tools.common import ROOT,contained,sha256_file,write_json
from tools import review39_selector as S,ui_layout_text as U,title_screen as T,eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.39'
BASE=ROOT/'work/output/builds/0.5.38'
CHANGED={'AIDDATAPACK.CPK','EFFPS3.CPK'}


def ui_check(old,new,mapping):
    from tools.menu_layout import encode
    original=S.B.source();old_grow=len(old)-len(original);new_grow=len(new)-len(original)
    before={a-old_grow:r for r in S.U.fssa_strings(old,decode=lambda r:r.hex()) for a in r['widget_offsets']}
    after={a-new_grow:r for r in S.U.fssa_strings(new,decode=lambda r:r.hex()) for a in r['widget_offsets']}
    edits={e['widget_offset']:e for e in S.plan()['edits']}
    if before.keys()!=after.keys():raise ValueError('UI widget identities differ')
    for at,row in before.items():
        a=old[at+old_grow:at+old_grow+32];b=new[at+new_grow:at+new_grow+32]
        wanted=bytearray(a)
        if at in edits:
            e=edits[at]
            struct.pack_into('>ff',wanted,4,e['x'],e['y']);wanted[16:21]=bytes(e['font_metrics']);wanted[23]=e['mode']
            raw=encode(e,mapping)
        else:raw=row['raw']
        if b[4:]!=wanted[4:] or after[at]['raw']!=raw:raise ValueError('Unexpected widget change: '+hex(at))
    for blue,red in S.PAIRS:
        if after[blue]['raw']+after[red]['raw']!=encode(dict(en=S.PREFIX+S.SUFFIX),mapping):
            raise ValueError('Complete selector wording differs between choices')
    return dict(widgets=len(before),changed_widgets=4,both_states='Allies / Enemies',
                unrelated_widgets_unchanged=True,colors_and_native_state_flags_preserved=True,bounds=S.plan()['bounds'])


def plan():
    from tools.pipeline import config
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Selector builder version differs')
    prior=json.loads((BASE/'build.json').read_text('utf8'))
    ready=json.loads((ROOT/'work/ui/local_release_0.5.38.json').read_text('utf8'))
    proof=ROOT/'work/ui/review38_verified_0.5.38.json'
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Parent proof changed')
    for name,digest in prior['outputs'].items():
        if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
    ui=U.plan(config(ROOT/'config/tengoku.json'),prior['mapping'])
    with CPK(BASE/'AIDDATAPACK.CPK') as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    checked=ui_check(old,ui['members'][0],prior['mapping'])
    raw=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
    return dict(prior=prior,ui=ui,checked=checked,title=title,title_info=info,
                parent_proof_sha256=sha256_file(proof))


def build(p):
    folder=contained(ROOT/'work/output/builds',ROOT/'work/output/builds'/VERSION)
    if folder.exists():raise ValueError('Preserve existing candidate: '+VERSION)
    folder.mkdir(parents=True);report=copy.deepcopy(p['prior'])
    for name in report['outputs']:
        if name not in CHANGED:shutil.copyfile(BASE/name,folder/name)
    for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,folder/name)
    reports={}
    for name,members in {'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},'EFFPS3.CPK':{229:p['title']}}.items():
        with CPK(BASE/name) as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
        build_cpk(BASE/name,folder/name,members,compress=compressed)
        reports[name]=compare(BASE/name,folder/name,members)
    verified=U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui'])
    report.update(version=VERSION,title_screen=p['title_info'],runtime_verified=False,layout_verified=False,
                  ui_context_text=p['ui']['report']['context_text'],map_selector=p['checked'])
    report['extra_art']['AIDDATAPACK.CPK']=dict(archive=reports['AIDDATAPACK.CPK'],members_verified=verified)
    report['extra_art']['EFFPS3.CPK']=dict(archive=reports['EFFPS3.CPK'],title=p['title_info'])
    for name in report['outputs']:report['outputs'][name]=sha256_file(folder/name)
    report['incremental_build']=dict(parent_version='0.5.38',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],unchanged_executable=True,unchanged_fonts=True,
        unchanged_mapping=True,unchanged_advances=True,unchanged_stage_wrapper=True)
    write_json(folder/'build.json',report);print('Built 0.5.39: four selector widgets and title stamp.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();data=plan()
    print('Selector:',data['checked'])
    if args.apply:build(data)
    else:print('DRY RUN: no game assets written.')


if __name__=='__main__':main()
