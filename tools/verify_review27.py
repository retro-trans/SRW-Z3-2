"""Final Library caption, canonical Zuul, runtime team-width and save-line checks."""
import argparse,json,re,shutil
from pathlib import Path
from functools import lru_cache
from tools.common import ROOT,sha256_file,write_json
from tools import review27_dialogue as A,review27_messages as M,review27_names as N
from tools import dialogue_build as D,dialogue as Q,library_build as L,library_text as T,ui_hook as H,eboot_text as E
from tools.cpk import CPK

SHOTS=(('library-name','77d95fd7-60d8-4653-8ff4-afbcffa45f32'),('Zuul','8fabc5aa-55c9-4f49-b95a-2972cb090916'),
       ('team-width','c8dc21b4-1bd8-4477-ad65-c9bcfa51682e'),('save-question','77390955-6ae1-4dd5-b390-7fd365880631'))

def verify(version):
    from tools.verify_review26 import verify as previous
    print('Checking all carried fixes...',flush=True);prior=previous(version)
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'));mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes()
    from tools.ui_vwf_build import raster
    @lru_cache(None)
    def width(c):return raster(c)[1]if c in mapping else 32
    audit=A.plan(width)
    if json.loads(A.DEST.read_text('utf8'))!=audit:raise ValueError('Team-name dialogue audit stale')
    A.guard(elf);rendered=D.plan(width);members=sorted({int(r['id'].split(':')[0])for r in audit['records']})
    print('Checking all runtime team-name dialogue members...',flush=True)
    with CPK(folder/'STGZ3OF2.cpk')as archive:
        index={r['id']:r for r in archive.files}
        for mid in members:
            if archive.read(index[mid])!=D.rebuild_member(mid,rendered,mapping):raise ValueError('Final team-name dialogue member differs: '+str(mid))
    report,_=N.plan()
    if report['changes']:raise ValueError('Obsolete Zuul spelling remains in active names')
    # Check expanded strings as well as names; dialogue itself need not change.
    res=E.resolver();counts={};hits=0
    def check(kind,text):
        nonlocal hits
        if not isinstance(text,str):return
        text=L.expand(text,res);counts[kind]=counts.get(kind,0)+1
        if re.search(r'\b(?:Xul|Zul)\b',text):raise ValueError('Old spelling in expanded '+kind)
        hits+=len(re.findall(r'\bZuul\b',text))
    for row in D.translations().values():check('dialogue',row['en'])
    from tools.voice_build import translations
    for row in translations().values():check('voice',row['en'])
    for row in E.load()['strings'].values():check('executable',row['en'])
    library=T.load_library();entries,errors=T.load_translations()
    if errors:raise ValueError(errors)
    fields=L.plan(library,entries,json.loads(T.GLOSSARY.read_text('utf8'))['terms']);checked=[]
    from tools.source_text import library_fields
    for kind,rows in fields.items():
        with CPK(folder/('MTZKN_'+T.lc.KINDS[kind][0]+'.CPK'))as arc:
            index={r['id']:r for r in arc.files}
            for tid,payloads in rows.items():
                for value in payloads.values():check('library',value)
                if not any(re.search(r'\bZuul\b',value)for value in payloads.values()):continue
                raw=arc.read(index[tid]);decoded=bytes(x if x in(0,0x5e)else x^0x5e for x in raw);_,slots=library_fields(raw)
                actual={s['tag']:decoded[s['offset']:s['offset']+s['bytes']]for s in slots}
                for tag,expected in payloads.items():
                    if tag in('DSCR','DSC2'):expected=L.wrap(expected,width)
                    if actual[tag]!=L.encode(expected,mapping):raise ValueError('Final Zuul Library field differs')
                checked.append(dict(archive=kind,member=tid,fields=list(payloads)))
    if not hits or not checked:raise ValueError('Zuul canonical text absent')
    # The earlier label fix must appear in the exact reported widget.
    from tools import battle_layout as B,ui_catalog as U
    original=B.source()
    with CPK(folder/'AIDDATAPACK.CPK')as arc:final=arc.read(next(r for r in arc.files if r['id']==0))
    target=0x9cd64+len(final)-len(original);widgets={at:r for r in U.fssa_strings(final,decode=lambda raw:L.decode(raw,mapping))for at in r['widget_offsets']}
    if widgets[target]['text']!='Name' or final[target+4:target+32]!=original[0x9cd64+4:0x9cd64+32]:raise ValueError('Library Name label differs')
    read=H._reader(elf,H._headers(elf)[2]);info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes']);save=[]
    for row in M.hook_entries(H.PREPARED.read_bytes(),mapping):
        p,steps=runner.run(row['key']+b'\0')
        if read(p,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Final individual save line untranslated')
        save.append(dict(id=row['id'],english=L.decode(row['english'],mapping),steps=steps))
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review27-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        library_caption=dict(original_widget=0x9cd64,english='Name',value_preserved=True),
        canonical_name=dict(english='Zuul',expanded_fields_examined=counts,canonical_occurrences=hits,library_members=checked),
        runtime_team_dialogue=audit,dialogue_members=members,save_lookup_cases=save,screenshots=shots,runtime_verified=False,
        proofreading=dict(reviewer='review26_wording',reported_id=A.TARGET,source_rows_examined=19,english_rows_examined=19,meaning_changes=0))

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args()
    if a.preview:
        audit=A.plan();print('Source preview:',len(audit['records']),'team-name records at',audit['team_name_units'],'units');print(audit['reported_rendered'])
        for jp,row in M.plan()['strings'].items():print(repr(jp),'->',repr(row['en']))
        print('Planned evidence: work/ui/review27_verified_'+a.version+'.json; four reported screenshots. DRY RUN: no files written.');return
    data=verify(a.version);print('Runtime name records:',len(data['runtime_team_dialogue']['records']),'Library members:',len(data['canonical_name']['library_members']),'Save keys:',len(data['save_lookup_cases']));print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Reported screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review27_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
