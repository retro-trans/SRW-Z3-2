"""Final caption, normal-font dialogue, name and Team Setup readback."""
import argparse,json,re,shutil,struct
from pathlib import Path
from collections import Counter
from functools import lru_cache
from tools.common import ROOT,sha256_file,write_json
from tools import review25_dialogue as R,review25_layout as A,dialogue_build as D,dialogue as Q
from tools import eboot_text as E,library_build as L,ui_hook as H,ui_catalog as U,battle_layout as B,menu_layout as F
from tools.cpk import CPK
SHOTS=(('caption','94be9a0a-1a5b-4b8c-b9e3-a76e8364c91e'),('Ameria','3414dc25-5b6b-4cab-9062-768ed269a444'),
       ('unlock-rescue','5763f827-e570-4bd9-8363-b35f79d49190'),('unlock-target','f3bc7695-b510-44ee-a3a5-196295788ed6'),
       ('team-setup','36645b04-6360-4412-b4d9-ba7aa18681f1'),('dialogue-font','6e8f2e06-f690-46ae-97eb-77d3cd07d54d'),
       ('sr-condition','df16dcb3-e454-498d-8b4e-9af75a2424a1'))

def name_coverage():
    from tools import voice_build as V
    from tools.library_text import load_translations
    resolver=E.resolver();counts=Counter();hits=0
    def check(kind,text):
        nonlocal hits
        if not isinstance(text,str):return
        text=L.expand(text,resolver);counts[kind]+=1
        if re.search(r'\bAmerria\b',text):raise ValueError('Obsolete location name in active '+kind)
        hits+=len(re.findall(r'\bAmeria\b',text))
    for row in D.translations().values():check('dialogue',row['en'])
    for row in V.translations().values():check('battle_voice',row['en'])
    entries,errors=load_translations()
    if errors:raise ValueError(errors)
    for table in entries.values():
        for _,row in table.values():
            for field in ('DSCR','DSC2','CHFN','CHSN','ROFN','ROSN','WORD'):check('library',row.get(field))
    for row in E.load()['strings'].values():check('executable',row.get('en'))
    art=json.loads((ROOT/'work/translation/en/ui/effps3_art.json').read_text(encoding='utf8'))
    for row in art['entries']:check('location_art',row.get('en'))
    if not hits:raise ValueError('Ameria absent from active text')
    return dict(fields_examined=dict(counts),canonical_occurrences=hits,obsolete_spellings=0)

def verify(version):
    from tools.verify_review24 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    from tools.ui_vwf_build import raster
    from tools.ui_build import FACE
    @lru_cache(None)
    def width(c):return raster(c,FACE)[1]if c in mapping else 32
    rendered=D.plan(width);source={r['id']:r for r in Q.plan_rows()};active=D.translations();captions=[]
    for rid in sorted(R.CAPTION_IDS):
        text=rendered[rid];body=text.split('\n')[2];words=body.lstrip(' ');pad=len(body)-len(words)
        if words!="～ Gargantia Fleet / Fleet Commander's Room ～"or source[rid]['sha']!=R.CAPTION_SHA:raise ValueError('Final reported room caption differs')
        error=pad*width(' ')+sum(map(width,words))/2-Q.BOX_UNITS/2
        if abs(error)>width(' ')/2:raise ValueError('Caption not centered by final widths')
        if text.split('\n')[:2]!=source[rid]['jp'].split('\n')[:2]:raise ValueError('Caption blank rows changed')
        captions.append(dict(id=rid,units=sum(map(width,words)),leading_spaces=pad,center_error_units=error))
    if active[R.MAO_ID]['en']!=R.MAO or R.MAO_ID in build['dialogue_layout']['condensed_records']:raise ValueError('Mao retains condensed profile or unreviewed wording')
    lines=rendered[R.MAO_ID].split('\n')[1:];spans=[sum(width(c)for c in line if c not in D.LINK_MARKS)for line in lines]
    if len(lines)!=3 or max(spans)>Q.BOX_UNITS or rendered[R.MAO_ID].count('《')!=1:raise ValueError('Normal-font explanation loses row/link bounds')
    members=sorted({int(rid.split(':')[0])for rid in R.CAPTION_IDS|{R.MAO_ID}})
    with CPK(folder/'STGZ3OF2.cpk')as archive:
        index={r['id']:r for r in archive.files}
        for mid in members:
            if archive.read(index[mid])!=D.rebuild_member(mid,rendered,mapping):raise ValueError('Final caption/dialogue member differs')
    layout=A.plan()
    if json.loads(A.DEST.read_text(encoding='utf8'))!=layout:raise ValueError('Team Setup plan stale')
    original=B.source()
    with CPK(folder/'AIDDATAPACK.CPK')as archive:final=archive.read(next(r for r in archive.files if r['id']==0))
    grow=len(final)-len(original);widgets={at:r for r in U.fssa_strings(final,decode=lambda raw:L.decode(raw,mapping))for at in r['widget_offsets']}
    old={at:r for r in U.fssa_strings(original)for at in r['widget_offsets']}
    for e in layout['edits']:
        at=e['widget_offset'];target=at+grow
        if final[target+8:target+32]!=original[at+8:at+32]:raise ValueError('Team Setup font/color/live state changed')
        if 'x'in e and final[target+4:target+8]!=struct.pack('>f',e['x']):raise ValueError('Next/counter origin differs')
        if 'en'in e:
            if widgets[target]['raw']!=F.encode(e,mapping):raise ValueError('Team Setup caption differs')
        elif widgets[target]['raw']!=old[at]['raw']:raise ValueError('Live counter source changed')
    for at in (0xa4c24,0xa4c84):
        if any(c in widgets[at+grow]['text']for c in '空陸水地'):raise ValueError('Team Setup movement terrain untranslated')
    upgrade=prior
    while 'native_report_cases'not in upgrade:upgrade=upgrade['prior_verification']
    unlocks=[row for row in upgrade['native_report_cases']if row['index']in (6,20)]
    if len(unlocks)!=2:raise ValueError('Reported unlock paths not executed')
    from tools import mission_text as M,mission_display as MD
    mission=M.plan(width);reported=[row for row in MD.hook_entries(H.PREPARED.read_bytes(),mission,mapping)
        if b''!=row['english'] and "NPCs Lal'C, Nono, Tycho and"in L.decode(row['english'],mapping)]
    if len(reported)!=1:raise ValueError('Reported NPC SR condition missing')
    elf=(folder/'EBOOT.BIN').read_bytes();info=build['executable']['ui_hook'];read=H._reader(elf,H._headers(elf)[2]);runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    row=reported[0];ptr,steps=runner.run(row['key']+b'\0')
    if read(ptr,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Final NPC SR condition corrupt')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review25-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],caption_cases=captions,
        normal_font_record=dict(id=R.MAO_ID,row_widths=spans,keyword_link_preserved=True),dialogue_members=members,layout=layout,
        name_coverage=name_coverage(),reported_native_unlocks=unlocks,reported_sr_condition=dict(text=L.decode(row['english'],mapping),lookup_steps=steps),
        screenshots=shots,runtime_verified=False,proofreading=dict(reviewer='review25_wording',source_dialogue_rows_examined=47,mission_conditions_examined=6))

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args();data=verify(a.version)
    print('Captions:',len(data['caption_cases']),'Dialogue members:',len(data['dialogue_members']),'Normal font rows:',data['normal_font_record']['row_widths'])
    print('Names:',data['name_coverage'],'SR:',data['reported_sr_condition']['text']);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Reported screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review25_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
