"""Prepare the actual linked-keyword archive on certified public 0.5.40."""
import argparse,copy,json,shutil
from tools.common import ROOT,contained,sha256_file,write_json
from tools.pipeline import config,verified_source
from tools import keyword_popup as K,title_screen as T,eff_art as E
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.41'
BASE=ROOT/'work/output/builds/0.5.40'
ADDED='MTV_ALL_KEYWORD_DEF.CPK'
CHANGED={'EFFPS3.CPK',ADDED}

def plan():
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Popup builder version differs')
    prior=json.loads((BASE/'build.json').read_text(encoding='utf8'))
    ready=json.loads((ROOT/'work/ui/local_release_0.5.40.json').read_text(encoding='utf8'))
    proof=ROOT/'work/ui/review40_verified_0.5.40.json'
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Certified parent proof changed')
    for name,digest in prior['outputs'].items():
        if sha256_file(BASE/name)!=digest:raise ValueError('Certified parent output changed: '+name)
    settings=config(ROOT/'config/tengoku.json');keywords=K.plan(settings,prior['mapping'])
    raw=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
    return dict(prior=prior,keywords=keywords,title=title,title_info=info,settings=settings,
                parent_proof_sha256=sha256_file(proof))

def build(p):
    folder=contained(ROOT/'work/output/builds',ROOT/'work/output/builds'/VERSION)
    if folder.exists():raise ValueError('Preserve existing candidate: '+VERSION)
    folder.mkdir(parents=True);report=copy.deepcopy(p['prior'])
    for name in report['outputs']:
        if name!='EFFPS3.CPK':shutil.copyfile(BASE/name,folder/name)
    for name in ('font_1.bin','font_3.bin','rpw.bin','STGZ3OF2.cpk'):shutil.copyfile(BASE/name,folder/name)
    src=verified_source(p['settings'],K.DISC)
    build_cpk(src,folder/ADDED,p['keywords']['members'],compress=True)
    report['extra_art'][ADDED]=dict(archive=compare(src,folder/ADDED,p['keywords']['members']),
                                   members_verified=K.verify_archive(folder/ADDED,p['keywords']))
    report['disc_files'][K.DISC]=ADDED;report['outputs'][ADDED]=sha256_file(folder/ADDED)
    with CPK(BASE/'EFFPS3.CPK')as arc:
        row=next(r for r in arc.files if r['id']==229);compressed={229}if row['size']!=row['extract']else set()
    build_cpk(BASE/'EFFPS3.CPK',folder/'EFFPS3.CPK',{229:p['title']},compress=compressed)
    report['extra_art']['EFFPS3.CPK']=dict(archive=compare(BASE/'EFFPS3.CPK',folder/'EFFPS3.CPK',{229:p['title']}),title=p['title_info'])
    report.update(version=VERSION,title_screen=p['title_info'],keyword_popup=p['keywords']['report'],
                  runtime_verified=False,layout_verified=False)
    for name in report['outputs']:
        actual=sha256_file(folder/name)
        if name not in CHANGED and actual!=p['prior']['outputs'][name]:raise ValueError('Copied asset differs: '+name)
        report['outputs'][name]=actual
    report['incremental_build']=dict(parent_version='0.5.40',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],unchanged_executable=True,unchanged_fonts=True,
        unchanged_mapping=True,unchanged_advances=True,unchanged_stage_wrapper=True)
    write_json(folder/'build.json',report);print('Built 0.5.41: live popup archive and title stamp.')

def main():
    a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args();p=plan()
    print('Popup archive:',{k:v for k,v in p['keywords']['report'].items()if k!='entries'})
    if args.apply:build(p)
    else:print('DRY RUN: no game assets written.')

if __name__=='__main__':main()
