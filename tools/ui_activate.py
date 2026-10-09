"""Activate the reviewed VWF build in the registered local test game and cache.

Dry-run by default. Requires RPCS3 to be closed. The two installed cache paths
were discovered and matched by hash in Tengoku; they are not Jigoku settings.
Original ISO, extracted sources and saves are never destinations.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools.inventory import RPW, FONT
from tools.self_elf import EBOOT

VERSION = 'ui-0.1.1-vwf'
GAME = ROOT/'work/tengoku/game-ui-0.1.0'
FRESH = ROOT/('work/output/game-'+VERSION)
CACHE = Path('E:/RPCS3/dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO')
BACKUP = ROOT/('work/tengoku/activations/'+VERSION)


def require_closed():
    check = subprocess.run(['powershell.exe','-NoProfile','-Command',
        '@(Get-Process -Name rpcs3 -ErrorAction SilentlyContinue).Count'],
        capture_output=True,text=True,check=True)
    if check.stdout.strip() != '0':
        raise ValueError('RPCS3 must be closed before activation')


def plan():
    require_closed()
    registry = Path('E:/RPCS3/config/games.yml').read_text(encoding='utf-8')
    registered = [line.split(': ',1)[1].strip().strip('"\'') for line in registry.splitlines()
                  if line.startswith('BLJS10299: ')]
    if len(registered)!=1 or Path(registered[0]).resolve()!=GAME.resolve():
        raise ValueError('registered Tengoku game path changed')
    old = json.loads((GAME/'ui_patch_manifest.json').read_text(encoding='utf-8'))
    new = json.loads((FRESH/'ui_patch_manifest.json').read_text(encoding='utf-8'))
    if old['build']!='ui-0.1.0' or new['build']!=VERSION:
        raise ValueError('unexpected deployment identity/version')
    for manifest,version in ((old,'ui-0.1.0'),(new,VERSION)):
        if manifest['title_id']!='BLJS10299' or manifest['build_manifest_sha256']!=sha256_file(
                ROOT/('work/output/builds/'+version+'/build.json')):
            raise ValueError('build provenance changed')
    previous = {r['path']:r for r in old['files']}
    current = {r['path']:r for r in new['files']}
    changed = {p.lstrip('/') for p in (EBOOT,RPW,FONT)}
    if len(previous)!=82 or previous.keys()!=current.keys():
        raise ValueError('disc manifest scope changed')
    if {p for p in current if current[p]!=previous[p]}!=changed:
        raise ValueError('unexpected changed disc files')
    jobs=[]
    def job(target,source,before,after):
        if sha256_file(target)!=before or sha256_file(source)!=after:
            raise ValueError('activation input drift: '+str(target))
        temporary=target.with_name(target.name+'.'+VERSION+'.tmp')
        if temporary.exists():raise ValueError('staging path exists: '+str(temporary))
        jobs.append({'target':str(target),'source':str(source),'before_sha256':before,
                     'after_sha256':after,'temporary':str(temporary)})
    for p in (EBOOT,RPW,FONT):
        p=p.lstrip('/')
        job(GAME/p,FRESH/p,previous[p]['sha256'],current[p]['sha256'])
    for name,p in (('DATA0014.DAT',RPW),('DATA0141.DAT',FONT)):
        p=p.lstrip('/')
        job(CACHE/name,FRESH/p,previous[p]['sha256'],current[p]['sha256'])
    job(GAME/'ui_patch_manifest.json',FRESH/'ui_patch_manifest.json',
        sha256_file(GAME/'ui_patch_manifest.json'),sha256_file(FRESH/'ui_patch_manifest.json'))
    if BACKUP.exists():raise ValueError('activation backup already exists')
    return jobs


def copy_verified(source,target,expected):
    with Path(source).open('rb') as inp, Path(target).open('xb') as out:
        shutil.copyfileobj(inp,out,4<<20)
    if sha256_file(target)!=expected:raise ValueError('copy readback mismatch: '+str(target))


def activate(jobs):
    require_closed()
    BACKUP.mkdir(parents=True,exist_ok=False)
    for i,j in enumerate(jobs):
        j['backup']=str(BACKUP/('%02d-'%i+Path(j['target']).name))
        copy_verified(j['target'],j['backup'],j['before_sha256'])
    write_json(BACKUP/'activation.json',{'version':VERSION,'state':'backed_up','files':jobs})
    staged,committed=[],[]
    try:
        for j in jobs:
            staged.append(j)
            copy_verified(j['source'],j['temporary'],j['after_sha256'])
        require_closed()
        for j in jobs:
            if sha256_file(j['target'])!=j['before_sha256']:
                raise ValueError('target changed during staging')
        for j in jobs:
            os.replace(j['temporary'],j['target'])
            committed.append(j)
            if sha256_file(j['target'])!=j['after_sha256']:
                raise ValueError('activation readback mismatch')
        write_json(BACKUP/'activation.json',{'version':VERSION,'state':'activated',
            'files':jobs,'game_files_verified':3,'cache_files_verified':2,
            'runtime_verified':False,'layout_verified':False})
    except BaseException:
        for j in reversed(committed):
            copy_verified(j['backup'],j['temporary'],j['before_sha256'])
            os.replace(j['temporary'],j['target'])
        for j in staged:
            temp=Path(j['temporary'])
            if temp.exists():temp.unlink()
        write_json(BACKUP/'activation.json',{'version':VERSION,'state':'rolled_back','files':jobs})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    jobs=plan()
    for j in jobs:
        print(j['target'])
        print('  '+j['before_sha256']+' -> '+j['after_sha256'])
    print('Recoverable backup: '+str(BACKUP))
    if args.apply:
        activate(jobs)
        print('Activated: three game files, two cache files and deployment manifest verified.')
    else:print('DRY RUN: no files written')

if __name__=='__main__':main()
