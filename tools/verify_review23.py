"""Read back complete static missions, deployment templates and canonical names."""
import argparse,json,re,shutil,struct
from pathlib import Path
from collections import Counter
from tools.common import ROOT,sha256_file,write_json
from tools import review23_layout as A,review23_names as N,mission_display as D,mission_text as M
from tools import ui_hook as H,library_build as L,battle_layout as B,ui_catalog as U,menu_layout as F
from tools.cpk import CPK

SHOTS=(('unlock','8a49ef40-96af-4cd7-9f5a-1051b18e6dde'),
       ('missions','3ea81647-d6f1-45d6-8e36-83f44c2671e8'),
       ('Sacks','4b9be642-ceac-4eff-92c7-45494804c237'),
       ('deployment','8f7857a5-884a-46af-b33c-16aa7fd5b1e2'),
       ('Giltar','6d30c538-f115-4d31-8358-471ccfb08b60'))

def name_coverage():
    from tools import dialogue_build as Q,voice_build as V,eboot_text as E
    from tools.library_text import load_translations
    counts=Counter();hits=Counter();resolver=E.resolver()
    def check(category,text):
        if not isinstance(text,str):return
        text=L.expand(text,resolver);counts[category]+=1
        for old,new in N.REPLACEMENTS.items():
            if re.search(r'\b'+old+r'\b',text):raise ValueError('Obsolete name in '+category)
            hits[new]+=len(re.findall(r'\b'+new+r'\b',text))
    for row in Q.translations().values():check('dialogue',row['en'])
    for row in V.translations().values():check('battle_voice',row['en'])
    entries,errors=load_translations()
    if errors:raise ValueError(errors)
    for table in entries.values():
        for _,row in table.values():
            for field in N.FIELDS-{'en'}:check('library',row.get(field))
    for row in E.load()['strings'].values():check('executable',row.get('en'))
    if any(not hits[n]for n in N.REPLACEMENTS.values()):raise ValueError('Canonical names missing')
    return dict(fields_examined=dict(counts),canonical_occurrences=dict(hits),obsolete_spellings=0)

def verify(version):
    from tools.verify_review22 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2]);info=build['executable']['ui_hook']
    runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    from tools.ui_vwf_build import raster
    from tools.ui_build import FACE
    from functools import lru_cache
    @lru_cache(None)
    def width_of(c):return raster(c,FACE)[1]if c in mapping else 32
    rendered=M.plan(width_of);cases=D.copy_cases(elf,rendered,mapping);lookups=[]
    for row in D.hook_entries(H.PREPARED.read_bytes(),rendered,mapping):
        pointer,steps=runner.run(row['key']+b'\0')
        if read(pointer,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Complete mission lookup differs')
        lookups.append(dict(id=row['id'],english_bytes=len(row['english']),steps=steps))
    from tools import squad_text as S,dialogue as Q
    stage=D.stage_text(rendered);members=[];squads=S.plan()
    with CPK(folder/'STGZ3OF2.cpk')as c:
        by_id={e['id']:e for e in c.files}
        for mid in M.members():
            expected=S.rebuild_member(mid,stage,squads,mapping)
            if expected is None:expected=(Q.MEMBERS/('%05d.bin'%mid)).read_bytes()
            if c.read(by_id[mid])!=expected:raise ValueError('Final mission/squad member differs')
            members.append(mid)
    source=B.source();layout=A.plan()
    if json.loads(A.DEST.read_text(encoding='utf8'))!=layout:raise ValueError('Deployment source bindings stale')
    with CPK(folder/'AIDDATAPACK.CPK')as c:final=c.read(next(e for e in c.files if e['id']==0))
    grow=len(final)-len(source);widgets={a:r for r in U.fssa_strings(final,decode=lambda raw:L.decode(raw,mapping))for a in r['widget_offsets']}
    for e in layout['edits']:
        at=e['widget_offset'];to=at+grow
        if widgets[to]['raw']!=F.encode(e,mapping):raise ValueError('Deployment caption differs')
        if final[to+4:to+32]!=source[at+4:at+32]:raise ValueError('Deployment value/flag geometry changed')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review23-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        layout=layout,mission_native_copy_cases=cases,mission_lookup_cases=lookups,mission_members=members,
        name_coverage=name_coverage(),screenshots=shots,runtime_verified=False,
        proofreading=dict(reviewer='review23_mission_wording',assigned_conditions=5,source_rows_examined=9,meaning_changes=0),
        sr_condition='Defeat all other enemies before shooting down the Tenth Angel.',
        unlock_coverage='Carried from 0.5.20: all 23 conditions and 24 D-Trader item announcements, including Grade 3/Fox Mask.')

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args();result=verify(a.version)
    print('Mission copy/lookup cases:',len(result['mission_native_copy_cases']),len(result['mission_lookup_cases']))
    print('Deployment widgets:',len(result['layout']['edits']),'Canonical names:',result['name_coverage'])
    print('ISO:',result['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review23_verified_'+a.version+'.json'),result)

if __name__=='__main__':main()
