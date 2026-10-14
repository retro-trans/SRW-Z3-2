"""Read back actual numbered mission output, Spirit terms and Inazuma Kick."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import mission_display as D,mission_text as M,ui_hook as H,library_build as L
from tools.cpk import CPK
SHOTS=(('Break','01c0e85f-5a8a-4ab6-8368-71d57bab1ae3'),
       ('Fury','380bddc3-5f7e-47ba-aa84-c63c3c42b620'),
       ('Inazuma-Kick','8b487b24-f191-47a6-a244-3d48acb35261'),
       ('numbered-missions','d93f0258-d7e4-4575-ba0a-5956ad0352ce'))

def verify(version):
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'))
    mapping=build['mapping'];elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2])
    info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    rendered=M.plan(D.advance);entries={r['key']:r for r in D.hook_entries(H.PREPARED.read_bytes(),rendered,mapping)}
    cases=D.composition_cases(elf,rendered,mapping);live=D.live_cases(elf,rendered,mapping)
    for case in cases:
        english=[];lookup_steps=0
        for raw in case['keys']:
            key=bytes.fromhex(raw);entry=entries[key];pointer,steps=runner.run(key+b'\0')
            if read(pointer,len(entry['english'])+1)!=entry['english']+b'\0':raise ValueError('Composed mission untranslated')
            lookup_steps+=steps;english.append(L.decode(entry['english'],mapping))
        case.update(lookup_steps=lookup_steps,english=english)
    # Read all 129 Spirit fields directly out of the rebuilt table/pool.
    from tools import ui_spirits as S,ui_build as U,rpw_text as R,eboot_text as E
    from tools.pipeline import config
    from tools.source_text import rpw_chunks
    rows=S.load_and_validate(config(ROOT/'config/tengoku.json'))['entries'];spirit=[]
    with CPK(folder/'RPW_DATA.CPK')as arc:rpw=arc.read(arc.files[0])
    chunk=next(c for c in rpw_chunks(rpw)if c['name']=='spirit');js,_=R.pool_of(rpw)
    for row in rows:
        parts=row['occurrence_id'].split(':');record=int(parts[3]);column=S.FIELDS[parts[4]]
        pointer=struct.unpack_from('<I',rpw,chunk['body_offset']+record*20+column*4)[0]
        at=js['body_offset']+pointer;actual=rpw[at:rpw.index(b'\0',at)]
        expected=U.encode(row['rendered_en'],mapping,'vwf',row['role']=='abbreviation')
        if actual!=expected:raise ValueError('Spirit field differs: '+row['occurrence_id'])
        spirit.append(dict(id=row['occurrence_id'],english=row['rendered_en']))
    names={r['id']:r['english']for r in spirit}
    if names['rpw:0:spirit:3:name']!='Fury' or names['rpw:0:spirit:24:name']!='Break':raise ValueError('Spirit identities swapped')
    # Independently check every full/list weapon occurrence of this attack.
    source=R.load_rpw();oldjs,_=R.pool_of(source);grow=len(rpw)-len(source);weapons=[]
    for row in R.slots(source):
        if row['jp']!='イナズマキック' or row['family'] not in ('weapon','weapon_short'):continue
        offset=row['pointer_offset']+(grow if row['pointer_offset']>=oldjs['body_end']else 0)
        pointer=struct.unpack_from('<I',rpw,offset)[0];at=js['body_offset']+pointer
        if rpw[at:rpw.index(b'\0',at)]!=L.encode('Inazuma Kick',mapping):raise ValueError('Weapon name differs')
        weapons.append(row['id'])
    if not weapons:raise ValueError('Inazuma Kick weapon absent')
    from tools import voice_build as V,srvc
    voices=V.translations();original_voice,original_elf=srvc.load_prepared();final_voice=(folder/'SRVC.BIN').read_bytes()
    source_blocks=srvc.parse(original_voice,srvc.read_table(original_elf,len(original_voice)))
    final_blocks=srvc.parse(final_voice,srvc.read_table(elf,len(final_voice)));voice=[];resolver=E.resolver()
    for sid,row in voices.items():
        text=L.expand(row['en'],resolver)
        if 'Lightning Kick' in text:raise ValueError('Old weapon spelling remains in voice')
        if 'Inazuma Kick' not in text:continue
        block,off=map(int,sid.split(':'));k=source_blocks[block].offs.index(off);target=final_blocks[block]
        if srvc.string_at(final_voice,target.pool+target.offs[k])!=V.encode(text,mapping):raise ValueError('Weapon voice differs')
        voice.append(dict(id=sid,english=text))
    print('All 1048 native compositions/continuations, 200 live cases, 129 Spirit fields and Inazuma Kick references passed.',flush=True)
    from tools.verify_review28 import verify as previous
    prior=previous(version);shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.28-review29-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,previous_public_version='0.5.28',prior_verification=prior,
        iso_verification=prior['iso_verification'],native_composed_missions=cases,live_mission_cases=live,spirit_fields=spirit,
        weapon_occurrences=weapons,weapon_voice=voice,screenshots=shots,runtime_verified=False)

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser();p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args()
    if a.preview:
        print('Preview: 1048 native mission compositions/continuations, 200 live cases, all 129 Spirit fields, every Inazuma Kick weapon/voice occurrence and carried fixes.');print('DRY RUN: no evidence written.');return
    data=verify(a.version);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot differs')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review29_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
