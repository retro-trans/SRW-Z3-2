"""Prepare English Search tabs on certified 0.5.39; dry-run first."""
import argparse,copy,json,shutil
from tools.common import ROOT,contained,sha256_file,write_json
from tools import review40_tabs as S,ui_layout_text as U,title_screen as T,eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.40'
BASE=ROOT/'work/output/builds/0.5.39'
CHANGED={'AIDDATAPACK.CPK','EFFPS3.CPK'}


def ui_check(old,new,mapping):
    from tools.menu_layout import encode
    original=S.B.source();a_grow=len(old)-len(original);b_grow=len(new)-len(original)
    before={a-a_grow:r for r in S.U.fssa_strings(old,decode=lambda r:r.hex())for a in r['widget_offsets']}
    after={a-b_grow:r for r in S.U.fssa_strings(new,decode=lambda r:r.hex())for a in r['widget_offsets']}
    edits={e['widget_offset']:e for e in S.plan()['edits']}
    if before.keys()!=after.keys():raise ValueError('UI widget identities differ')
    for at,row in before.items():
        if old[at+a_grow+4:at+a_grow+32]!=new[at+b_grow+4:at+b_grow+32]:
            raise ValueError('Search translation changed geometry or style: '+hex(at))
        wanted=encode(edits[at],mapping) if at in edits else row['raw']
        if after[at]['raw']!=wanted:raise ValueError('Unrelated UI string changed: '+hex(at))
    for at in S.ABILITIES:
        if after[at]['raw']!=encode(dict(en='Abilities'),mapping):raise ValueError('Abilities control changed')
        if old[at+a_grow:at+a_grow+32]!=new[at+b_grow:at+b_grow+32]:
            raise ValueError('Working Abilities record changed')
    changed=sum(before[at]['raw']!=after[at]['raw']for at in before)
    if changed!=4:raise ValueError('Expected four late-lookup tab texts to change')
    for en,pair in S.PAIRS.items():
        if any(after[at]['raw']!=encode(dict(en=en),mapping)for at in pair):
            raise ValueError('Tab is not English before native measurement')
    return dict(widgets=len(before),changed_widgets=changed,preloaded_labels={k:list(v)for k,v in S.PAIRS.items()},
                all_geometry_and_styles_unchanged=True,abilities_unchanged=True,
                unrelated_strings_unchanged=True,bounds=S.plan()['bounds'])


def plan():
    from tools.pipeline import config
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Search builder version differs')
    prior=json.loads((BASE/'build.json').read_text('utf8'))
    ready=json.loads((ROOT/'work/ui/local_release_0.5.39.json').read_text('utf8'))
    proof=ROOT/'work/ui/review39_verified_0.5.39.json'
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
                  ui_context_text=p['ui']['report']['context_text'],search_tabs=p['checked'])
    report['extra_art']['AIDDATAPACK.CPK']=dict(archive=reports['AIDDATAPACK.CPK'],members_verified=verified)
    report['extra_art']['EFFPS3.CPK']=dict(archive=reports['EFFPS3.CPK'],title=p['title_info'])
    for name in report['outputs']:report['outputs'][name]=sha256_file(folder/name)
    report['incremental_build']=dict(parent_version='0.5.39',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],unchanged_executable=True,unchanged_fonts=True,
        unchanged_mapping=True,unchanged_advances=True,unchanged_stage_wrapper=True)
    write_json(folder/'build.json',report);print('Built 0.5.40: four preloaded Search tab texts and title stamp.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();data=plan()
    print('Search tabs:',data['checked'])
    if args.apply:build(data)
    else:print('DRY RUN: no game assets written.')


if __name__=='__main__':main()
