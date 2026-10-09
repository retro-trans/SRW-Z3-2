"""Apply a verified Spirit build to a fresh playable Tengoku folder.

All writes stay under work/. Existing game copies, sources and saves are
never overwritten. This does not change RPCS3 registration or launch a game.
"""
import argparse
import json
import shutil
from pathlib import Path
from tools.common import ROOT, contained, destination, sha256_file, write_json
from tools.inventory import RPW,FONT
from tools.pipeline import config, sfo_values
from tools.self_elf import EBOOT


def deploy(settings, build_dir, output, apply=False):
    build_dir=contained(ROOT/'work',build_dir)
    output=contained(ROOT/'work',output)
    if output.exists():raise ValueError('destination already exists')
    report=json.loads((build_dir/'build.json').read_text(encoding='utf-8'))
    source_manifest=json.loads((settings['work']/'source_manifest.json').read_text(encoding='utf-8'))
    if report['title_id']!=settings['title_id'] or source_manifest['title_id']!=settings['title_id']:
        raise ValueError('target title mismatch')
    replacements={RPW:(build_dir/'RPW_DATA.CPK',report['rpw_archive']),
                  FONT:(build_dir/'TPACKPS3.CPK',report['font_archive'])}
    if report.get('encoding') == 'vwf':
        executable = report['executable']
        if (report.get('schema') != 2 or not executable['all_allocated_sections_verified']
                or executable['program_sections_hmac_verified'] != [0,1,2,3,4]
                or executable['narrowed_cells'] != report['letter_cells']):
            raise ValueError('unverified VWF executable build')
        replacements[EBOOT] = (build_dir/'EBOOT.BIN',executable)
    if report['translated_occurrences']!=129 or report['font_archive']['untouched_members_verified']!=133:
        raise ValueError('unexpected patch scope')
    planned=[]
    for row in source_manifest['files']:
        relative=row['path'].lstrip('/')
        source=destination(settings['work']/'source',relative)
        if source.stat().st_size!=row['size'] or sha256_file(source)!=row['sha256']:
            raise ValueError('source drift: '+relative)
        expected=row['sha256']
        if row['path'] in replacements:
            source,patch_report=replacements[row['path']]
            if patch_report['source_sha256']!=expected:
                raise ValueError('patch built against different game source')
            expected=patch_report['output_sha256']
            if sha256_file(source)!=expected:raise ValueError('built archive drift')
        planned.append((relative,source,expected))
    if len(planned)!=82 or len({p[0] for p in planned})!=82:
        raise ValueError('incomplete disc inventory')
    print('Target: '+str(output))
    print('Copy 82 verified disc files; replace '+', '.join(Path(p).name for p in replacements)+'.')
    print('Stages, dialogue and voice data preserved.')
    if not apply:
        print('DRY RUN: no game files written')
        return
    output.mkdir(parents=True,exist_ok=False)
    deployed=[]
    for relative,source,expected in planned:
        target=destination(output,relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as inp, target.open('xb') as out:
            shutil.copyfileobj(inp,out,4<<20)
        if sha256_file(target)!=expected:raise ValueError('deployed file readback failed: '+relative)
        deployed.append({'path':relative,'bytes':target.stat().st_size,'sha256':expected})
    if sfo_values((output/'PS3_GAME/PARAM.SFO').read_bytes())['TITLE_ID']!='BLJS10299':
        raise ValueError('deployed game identity mismatch')
    write_json(output/'ui_patch_manifest.json',{'schema':1,'title_id':'BLJS10299','build':report.get('version','ui-0.1.0'),
               'source_iso_sha256':source_manifest['iso_sha256'],
               'build_manifest_sha256':sha256_file(build_dir/'build.json'),
               'files':deployed,'changed_files':list(replacements),
               'runtime_verified':False,'layout_verified':False,'published':False})
    print('Applied to playable game folder; all 82 copied files verified by readback.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',default='work/output/builds/ui-0.1.1-vwf')
    p.add_argument('--output',default='work/output/game-ui-0.1.1-vwf')
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    deploy(config(ROOT/'config/tengoku.json'),ROOT/a.build,ROOT/a.output,a.apply)

if __name__=='__main__':main()
