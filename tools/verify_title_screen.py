"""Verify translated title and matching footer in the final testing archive."""
import argparse
import json
import shutil
from pathlib import Path
from tools import title_screen as T, eff_art as E
from tools.cpk import CPK
from tools.common import ROOT, sha256_file, write_json


def verify(version):
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf-8'))
    if build['version']!=version:raise ValueError('Build version differs')
    source=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    expected,pixels,_,info=T.render(source,version)
    with CPK(folder/'EFFPS3.CPK')as archive:
        built=archive.read(next(e for e in archive.files if e['id']==T.MEMBER))
    if built!=expected:raise ValueError('Title logo or footer does not match this build')
    T.verify(source,built,pixels)
    if build['title_screen']!=json.loads(json.dumps(info)):
        raise ValueError('Title build report differs')
    from tools.verify_startup_ui import verify as startup
    from tools.verify_battle_layout import verify as battle
    prior=startup(version);layout=battle(version)
    shot=Path('C:/Users/Binh/AppData/Local/Temp/codex-clipboard-824be348-2262-43fa-af11-559744e0c058.png')
    saved=ROOT/'work/ui/screenshots'/('reported-'+version+'-title.png')
    if not shot.exists():shot=saved
    return dict(schema=1,version=version,title=info,final_archive_sha256=sha256_file(folder/'EFFPS3.CPK'),
        source_sha256={name:sha256_file(ROOT/name)for name in ('tools/title_screen.py',
            'tools/verify_title_screen.py','tools/refresh_title_build.py','tests/test_title_screen.py',
            'tools/eff_art.py','tools/game_build.py')},
        reported_screenshot=dict(source=str(shot),saved_path=str(saved),sha256=sha256_file(shot)),
        prior_startup_verification=prior,prior_battle_verification=layout,
        iso_verification=prior['iso'],runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.5.10');ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=verify(args.version)
    print('Title:',data['title']['wordmark'],'/',data['title']['subtitle'])
    print('Footer: v'+args.version,'/',data['title']['credit'])
    print('Tests:',data['prior_startup_verification']['regression_tests'])
    print('ISO:',data['iso_verification'])
    if args.apply:
        shot=data['reported_screenshot'];dest=Path(shot['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists()and sha256_file(dest)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dest:shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('title_screen_'+args.version+'.json'),data)
    else:print('DRY RUN: no evidence or screenshots written.')


if __name__=='__main__':main()
