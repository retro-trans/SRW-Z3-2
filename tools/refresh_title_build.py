"""Refresh only the EFFPS3 title candidate in an existing local testing build."""
import argparse
import json
import shutil
from tools import eff_art as E
from tools.common import ROOT, sha256_file, write_json
from tools.pipeline import verified_source
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.5.10');ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    from tools.game_build import VERSION
    if args.version!=VERSION:raise ValueError('Only the current local builder version can be refreshed')
    folder=ROOT/'work/output/builds'/args.version;report_path=folder/'build.json'
    report_sha=sha256_file(report_path);report=json.loads(report_path.read_text(encoding='utf-8'))
    if report['version']!=args.version:raise ValueError('Candidate build version differs')
    for name,digest in report['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Candidate output changed: '+name)
    settings=E._settings();art=E.plan(settings,title_version=args.version)
    print('Refresh EFFPS3 only:',art['report']['title_screen'])
    print('Other matched files:',len(report['outputs'])-1)
    if not args.apply:
        print('DRY RUN: no candidate changed.');return
    candidate=folder/'EFFPS3.title-candidate.CPK'
    if candidate.exists():raise ValueError('Title candidate already exists')
    source=verified_source(settings,E.ARCHIVE)
    build_cpk(source,candidate,art['members'],compress=art['compress'])
    checked=E.verify_archive(candidate,art)
    archive_report=compare(source,candidate,art['members'])
    if sha256_file(report_path)!=report_sha:raise ValueError('Build report changed during refresh')
    target=folder/'EFFPS3.CPK'
    if sha256_file(target)!=report['outputs']['EFFPS3.CPK']:raise ValueError('Effect candidate changed during refresh')
    backup=ROOT/'work/output/scratch'/('title-'+args.version+'-before-inset.CPK')
    if backup.exists():raise ValueError('Title rollback copy already exists')
    shutil.copyfile(target,backup)
    report['outputs']['EFFPS3.CPK']=sha256_file(candidate)
    report['title_screen']=art['report']['title_screen']
    report['extra_art']['EFFPS3.CPK']=dict(archive=archive_report,members_verified=checked)
    candidate.replace(target)
    write_json(report_path,report)
    print('Verified title archive refreshed; other matched files preserved.')


if __name__=='__main__':main()
