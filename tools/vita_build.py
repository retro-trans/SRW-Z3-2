"""Assemble pinned PCSG00494 0.1.4 components; no installation/publication."""
import argparse
import json
from pathlib import Path
import shutil
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import vita_source as V, vita_elf as E, cpkpatch, verify_archives,vita_storage
from tools.vita import self_decrypt as S
from tools.vita_assets import PARENT,voice
from tools.cpk import CPK

VERSION='0.1.4'
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


def member_plans(audit,constant_report=None):
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
    # Stamp this Vita build using the original source-bound title texture.
    # The rest of the sealed artwork plans remain unchanged.
    from tools import title_screen,vita_art
    native_rel='DATA/anime/effvita.cpk'
    parent=next(p for p in (ROOT/'work/tengoku/source/PS3_GAME/USRDIR').rglob('*') if p.name.lower()=='effps3.cpk')
    with CPK(parent) as a,CPK(V.PLAIN/native_rel) as b:
        old=a.read(next(r for r in a.files if r['id']==229))
        native=b.read(next(r for r in b.files if r['id']==229))
    result[native_rel][229]=vita_art.transfer(old,title_screen.render(old,VERSION)[0],native)[0]
    from tools import vita_lua_constants as L
    V.need(describe(V.PLAIN/L.SHARED)==audit['files'][L.SHARED],'Native shared definitions archive changed')
    bound,report=L.apply(result[L.STAGE])
    result.update(bound)
    if constant_report is not None:constant_report.update(report)
    return result


def executable():
    folder=V.WORK/'arm_candidate_v2';raw=(folder/'eboot.bin').read_bytes()
    plan=json.loads((folder/'plan.json').read_text('utf8'))
    proof=json.loads((V.WORK/'arm_execution_v2.json').read_text('utf8'))
    V.need(sha256(raw)==plan['output_sha256']==proof['candidate_sha256'] and proof['native_cases']>=44638,
           'Missing matching native execution proof')
    V.need(plan['voice_table']['output_sha256']==sha256_file(PARENT/'SRVC.BIN'),'Voice table/source mismatch')
    # Keep the source-certified 0.1.1 translation hooks and the now-verified
    # error display for any further hardware reports. No generic error bypass.
    from tools import vita_hardware_diagnostic as D,vita_diagnostic_draw_check as Draw
    updated,diagnostic=D.candidate(VERSION)
    checks={**D.verify(updated,diagnostic),**Draw.verify(updated,diagnostic)}
    V.need(diagnostic['base_sha256']==sha256(raw),'Diagnostic base differs from certified ARM hooks')
    plan=dict(plan,output_sha256=sha256(updated),diagnostic={k:v for k,v in diagnostic.items() if k!='base_arm'})
    proof=dict(proof,candidate_sha256=sha256(updated),base_candidate_sha256=sha256(raw),
               original_translation_hooks_unchanged=True,diagnostic_checks=checks)
    return updated,plan,proof


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
    print('Checking original sources and bound English asset plans...',flush=True)
    audit=json.loads((V.WORK/'source_audit.json').read_text('utf8'))
    bindings={};assets=member_plans(audit,bindings);eboot,arm,proof=executable();plain_modules,module_report=modules()
    semantic=json.loads((V.WORK/'first-battle-20261121/lua-binding-check-02/proof.json').read_text('utf8'))
    V.need(semantic.get('binding_plan_sha256')==sha256(json.dumps(bindings,sort_keys=True,separators=(',',':')).encode())
           and semantic['physical_error_reproduced'] and semantic['first_stage_missing_globals_corrected'],
           'Missing source-bound Lua regression proof')
    # Revalidate every source file, not only files selected for translation.
    for rel,row in audit['files'].items():V.need(describe(V.PLAIN/rel)==row,'Source inventory fingerprint differs')
    voice((E.OUTPUT/'segment-1.bin').read_bytes())
    summary=dict(schema=1,version=VERSION,title_id=V.TITLE,parent_ps3_version='0.5.51',
        archives={rel:len(v) for rel,v in assets.items()},original_files=len(audit['files']),
        native_execution_cases=proof['native_cases'],voice_blocks=368,modules=len(plain_modules),
        native_constant_bindings=bindings,native_constant_semantics=semantic,
        source_intake_verified=True,gameplay_tested=False,hardware_auth_available=False)
    display={k:v for k,v in summary.items() if k not in ('native_constant_bindings','native_constant_semantics')}
    display['constant_binding_summary']={rel:dict(scripts=len(rows),references=sum(x['references'] for x in rows))
                                         for rel,rows in bindings['archives'].items()}
    display['lua_semantic_checks']=semantic['summary']
    print(json.dumps(display,indent=2),flush=True)
    if not apply:print('DRY RUN: no game build written.');return summary
    OUTPUT.mkdir(parents=True);game=OUTPUT/'components';game.mkdir()
    archive_checks={};storage_checks={}
    prior_folder=ROOT/'work/output/vita/builds/0.1.1'
    prior=json.loads((prior_folder/'build.json').read_text('utf8'))
    for rel,members in assets.items():
        target=game/rel;target.parent.mkdir(parents=True,exist_ok=True)
        previous=prior_folder/'components'/rel
        # Reuse only an exact, independently rechecked archive. The versioned
        # title and any changed storage mode necessarily fail these guards.
        reusable=False
        if previous.is_file() and rel in prior['files'] and describe(previous)==prior['files'][rel]:
            try:
                storage=vita_storage.verify(V.PLAIN/rel,previous)
                check=verify_archives.compare(V.PLAIN/rel,previous,members)
            except ValueError:pass
            else:reusable=True
        if reusable:
            shutil.copyfile(previous,target)
            V.need(describe(target)==prior['files'][rel],'Reused archive copy differs')
            archive_checks[rel]=check;storage_checks[rel]=storage
            print('Rechecked unchanged archive',rel,flush=True)
            continue
        compressed=vita_storage.compression_ids(V.PLAIN/rel,members)
        cpkpatch.build(V.PLAIN/rel,target,members,compress=compressed,workers=4)
        archive_checks[rel]=verify_archives.compare(V.PLAIN/rel,target,members)
        storage_checks[rel]=vita_storage.verify(V.PLAIN/rel,target)
        print('Rebuilt and independently verified',rel,flush=True)
    for rel,raw in dict(plain_modules,**{'eboot.bin':eboot}).items():
        target=game/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    target=game/'DATA/BTLC/SRVC.BIN';shutil.copyfile(PARENT/'SRVC.BIN',target)
    files={p.relative_to(game).as_posix():describe(p) for p in sorted(game.rglob('*')) if p.is_file()}
    summary.update(files=files,source_files=audit['files'],archives_verified=archive_checks,
                   native_arm=arm,native_execution=proof,module_conversion=module_report,
                   native_storage=storage_checks,title_screen_version=VERSION)
    write_json(OUTPUT/'build.json',summary)
    print('Sealed local component build:',OUTPUT,flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();run(a.apply)


if __name__=='__main__':main()
