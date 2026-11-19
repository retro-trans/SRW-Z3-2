"""Assemble pinned PCSG00494 0.1.0 components; no installation/publication."""
import argparse
import json
from pathlib import Path
import shutil
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import vita_source as V, vita_elf as E, cpkpatch, verify_archives
from tools.vita import self_decrypt as S
from tools.vita_assets import PARENT,voice
from tools.cpk import CPK

VERSION='0.1.0'
OUTPUT=ROOT/'work/output/vita/builds'/VERSION
PLANS={
 'DATA/STAGE/STGZ3OF2.cpk':('stage',),
 'DATA/tabata/TPACKVITA.cpk':('font','tpack_art_v2','startup_v3'),
 'DATA/AIDDATA/AIDDataPack.cpk':('ui','aid_art'),
 'DATA/anime/effvita.cpk':('effect_art',),
 'DATA/BTLC/CMN.cpk':('battle_art',),
 'DATA/BTLC/OP.cpk':('opening_art',),
}
SHARED={
 'CommonData/MtData/rpw_data.cpk':'RPW_DATA.CPK',
 'CommonData/MtData/MtZkn_KW.cpk':'MTZKN_KW.CPK',
 'CommonData/MtData/MtZkn_Pt.cpk':'MTZKN_PT.CPK',
 'CommonData/MtData/MtZkn_Rt.cpk':'MTZKN_RT.CPK',
 'CommonData/MtData/MtV_all_keyword_def.cpk':'MTV_ALL_KEYWORD_DEF.CPK',
}


def describe(path):return dict(bytes=path.stat().st_size,sha256=sha256_file(path))


def member_plans(audit):
    result={}
    for rel,folders in PLANS.items():
        source=V.PLAIN/rel;V.need(describe(source)==audit['files'][rel],'Native archive changed')
        with CPK(source) as archive:
            ix={r['id']:r for r in archive.files};members={}
            for name in folders:
                folder=V.WORK/'asset_plans'/name;plan=json.loads((folder/'plan.json').read_text('utf8'))
                V.need(plan['title_id']==V.TITLE,'Foreign asset plan')
                for row in plan['members']:
                    mid=row['member']
                    if mid in members:
                        V.need(name=='startup_v3' and mid==0 and sha256(members[mid])==row['superseded_sha256'],
                               'Conflicting member plans')
                    raw=(folder/f'{mid:05d}.bin').read_bytes()
                    V.need(sha256(raw)==row['output_sha256'] and sha256(archive.read(ix[mid]))==row['source_sha256'],
                           'Asset plan fingerprint differs')
                    members[mid]=raw
        result[rel]=members
    original_index={p.name.lower():p for p in (ROOT/'work/tengoku/source/PS3_GAME/USRDIR').rglob('*') if p.is_file()}
    parent=json.loads((PARENT/'build.json').read_text('utf8'))
    for rel,name in SHARED.items():
        V.need(describe(V.PLAIN/rel)==audit['files'][rel],'Native shared archive changed')
        V.need(sha256_file(PARENT/name)==parent['outputs'][name],'Sealed English parent changed')
        members={}
        with CPK(V.PLAIN/rel) as a,CPK(original_index[name.lower()]) as b,CPK(PARENT/name) as c:
            aa,bb,cc=[{r['id']:r for r in z.files} for z in (a,b,c)]
            V.need(aa.keys()==bb.keys()==cc.keys(),'Shared member IDs differ')
            for mid in aa:
                native,old,en=[z.read(ix[mid]) for z,ix in ((a,aa),(b,bb),(c,cc))]
                V.need(native==old,'Shared member source differs')
                if en!=old:members[mid]=en
        result[rel]=members
    return result


def executable():
    folder=V.WORK/'arm_candidate_v2';raw=(folder/'eboot.bin').read_bytes()
    plan=json.loads((folder/'plan.json').read_text('utf8'))
    proof=json.loads((V.WORK/'arm_execution_v2.json').read_text('utf8'))
    V.need(sha256(raw)==plan['output_sha256']==proof['candidate_sha256'] and proof['native_cases']>=44638,
           'Missing matching native execution proof')
    V.need(plan['voice_table']['output_sha256']==sha256_file(PARENT/'SRVC.BIN'),'Voice table/source mismatch')
    return raw,plan,proof


def modules():
    reference=E.REFERENCE.read_text('utf8');V.need(sha256_file(E.REFERENCE)==E.REFERENCE_SHA,'SELF reference changed')
    rif=V.LICENSE.read_bytes();V.need(len(rif)==512 and rif[0x17:0x20]==V.TITLE.encode(),'License identity differs')
    result={};report={}
    for path in sorted((V.PLAIN/'sce_module').glob('*.suprx')):
        rel=path.relative_to(V.PLAIN).as_posix();raw,info=S.convert(path.read_bytes(),rif[0x50:0x60],reference)
        result[rel]=raw;report[rel]=info
    V.need(len(result)==5,'Original module inventory differs')
    return result,report


def run(apply=False):
    V.need(not OUTPUT.exists(),'Preserve an existing sealed Vita build')
    audit=json.loads((V.WORK/'source_audit.json').read_text('utf8'))
    assets=member_plans(audit);eboot,arm,proof=executable();plain_modules,module_report=modules()
    # Revalidate every source file, not only files selected for translation.
    for rel,row in audit['files'].items():V.need(describe(V.PLAIN/rel)==row,'Source inventory fingerprint differs')
    voice((E.OUTPUT/'segment-1.bin').read_bytes())
    summary=dict(schema=1,version=VERSION,title_id=V.TITLE,parent_ps3_version='0.5.51',
        archives={rel:len(v) for rel,v in assets.items()},original_files=len(audit['files']),
        native_execution_cases=proof['native_cases'],voice_blocks=368,modules=len(plain_modules),
        source_intake_verified=True,gameplay_tested=False,hardware_auth_available=False)
    print(json.dumps(summary,indent=2),flush=True)
    if not apply:print('DRY RUN: no game build written.');return summary
    OUTPUT.mkdir(parents=True);game=OUTPUT/'components';game.mkdir()
    archive_checks={}
    for rel,members in assets.items():
        target=game/rel;target.parent.mkdir(parents=True,exist_ok=True)
        cpkpatch.build(V.PLAIN/rel,target,members,compress=True,workers=4)
        archive_checks[rel]=verify_archives.compare(V.PLAIN/rel,target,members)
        print('Rebuilt and independently verified',rel,flush=True)
    for rel,raw in dict(plain_modules,**{'eboot.bin':eboot}).items():
        target=game/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    target=game/'DATA/BTLC/SRVC.BIN';shutil.copyfile(PARENT/'SRVC.BIN',target)
    files={p.relative_to(game).as_posix():describe(p) for p in sorted(game.rglob('*')) if p.is_file()}
    summary.update(files=files,source_files=audit['files'],archives_verified=archive_checks,
                   native_arm=arm,native_execution=proof,module_conversion=module_report)
    write_json(OUTPUT/'build.json',summary)
    print('Sealed local component build:',OUTPUT,flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.apply)


if __name__=='__main__':main()
