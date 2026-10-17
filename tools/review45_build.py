"""Build the four screenshot fixes and Chaos Caper on certified public 0.5.44."""
import argparse, copy, json, shutil, struct, subprocess
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import review45_text as R, ui_catalog as U, ui_hook as H, eboot_text as E
from tools import library_text as LT, library_build as L, dialogue as D, dialogue_build as DB
from tools import ui_layout_text as UI, title_screen as T, eff_art as EF, rpw_text as RP
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare
from tools.pipeline import config

VERSION = R.VERSION
BASE = ROOT / 'work/output/builds/0.5.44'
CHANGED = {'EBOOT.BIN','AIDDATAPACK.CPK','RPW_DATA.CPK','STGZ3OF2.SDAT','EFFPS3.CPK'}
OLD_CAPTION = '　\n　　\n'+'　'*4+'～$$ラース・バビロン$$ Imperial Palace　$$霊子吸収システム$$～'


def dictionary(elf, b):
    grouped, rows = U.checked()
    edits = dict(R.help_changes(), **R.FOOTER)
    edits[R.MENU_ID] = (R.menu_text('・'),R.menu_text('　'))
    edits[R.NARRATION_ID] = (R.NARRATION,R.NARRATION)
    read = H._reader(elf,H._headers(elf)[2])
    mask, slots = struct.unpack('>II',read(H.EXT_VA+8,8)); entries = {}
    for i in range(mask+1):
        _, key, en, n, _ = struct.unpack('>IIIHH',read(slots+i*16,16))
        if key: entries[read(key,n)] = (en,slots+i*16)
    out = bytearray(elf); spans=[]; cases=[]; values={}
    table = b['executable']['ui_hook']['table']; cursor=(table['used_bytes']+15)&~15
    def put(va, raw):
        seg = next(p for p in H._headers(elf)[2] if p[3]<=va<p[3]+p[5])
        at=seg[2]+va-seg[3]; out[at:at+len(raw)]=raw; spans.append((at,at+len(raw)))
    for rid,(old,new) in edits.items():
        if rows[rid]['en']!=new: raise ValueError('Stale corrected UI: '+rid)
        for source in grouped[rid]:
            key=source['raw'] if source['encoding']=='cp932' else H.utf8_key(source['raw'],H.PREPARED.read_bytes())
            va,slot=entries[key]; old_bytes=E.encode(old,b['mapping'])+b'\0'
            if read(va,len(old_bytes))!=old_bytes: raise ValueError('Public UI differs: '+rid)
            if rid in R.CAPTION_IDS:
                from tools.review44_text import caption_encoded
                new_bytes=caption_encoded(new,b['mapping'])+b'\0'
            elif rid==R.NARRATION_ID:
                from tools.dialogue_layout import PREFIX
                selected=dict(b['mapping']); selected.update({c:b['mapping'][PREFIX+c] for c in set(new)})
                new_bytes=E.encode(new,selected)+b'\0'
            else: new_bytes=E.encode(new,b['mapping'])+b'\0'
            if va in values and values[va]!=(old_bytes,new_bytes): raise ValueError('Conflicting dictionary alias')
            values[va]=(old_bytes,new_bytes)
            cases.append(dict(id=rid,key_hex=key.hex(),english=new,encoded_hex=new_bytes.hex(),slot=slot,old_va=va))
    targets={}
    for va,(old,new) in values.items():
        if any(va<p<va+len(old) for p,_ in entries.values()): raise ValueError('Nested dictionary value')
        if len(new)<=len(old): put(va,new+bytes(len(old)-len(new))); targets[va]=va
        else:
            if cursor+len(new)>table['ext_size'] or read(H.EXT_VA+cursor,len(new))!=bytes(len(new)):
                raise ValueError('Reserved UI headroom unavailable')
            targets[va]=H.EXT_VA+cursor; put(targets[va],new); cursor+=len(new)
    for case in cases:
        if targets[case['old_va']]!=case['old_va']: put(case['slot']+8,struct.pack('>I',targets[case['old_va']]))
    restored=bytearray(out)
    for a,z in spans: restored[a:z]=elf[a:z]
    if restored!=elf: raise ValueError('Unrelated executable bytes changed')
    result=bytes(out); stub=b['executable']['ui_hook']; runner=H._Runner(result,int(stub['stub_va'],16),stub['stub_bytes'])
    final_read=H._reader(result,H._headers(result)[2])
    for case in cases:
        ptr,steps=runner.run(bytes.fromhex(case['key_hex'])+b'\0'); wanted=bytes.fromhex(case['encoded_hex'])
        if ptr is None or final_read(ptr,len(wanted))!=wanted: raise ValueError('Installed caption lookup failed')
        case['steps']=steps
    return result,dict(cases=cases,values=len(values),modified_file_ranges=spans,
        used_bytes=max(cursor,table['used_bytes']),headroom_bytes=table['ext_size']-max(cursor,table['used_bytes']))


def stages(b):
    active=DB.translations(); terms=json.loads(LT.GLOSSARY.read_text('utf8'))['terms']; old_terms=copy.deepcopy(terms)
    next(t for t in old_terms if t.get('token')=='カオス・カペル')['en']='Chaos Kapel'
    current, prior=LT.Resolver(terms),LT.Resolver(old_terms); width=lambda c:b['widths'].get(c,32)
    wanted={'611:t_016:2','688:t_3:67',R.CAPTION_ID}; changed={}; audit=[]
    with CPK(BASE/'STGZ3OF2.cpk') as arc:
        for mid in (611,628,688):
            before={}; after={}
            for record in D.records(mid):
                rid=record['id']
                if rid not in active: continue
                entry=active[rid]; old=dict(entry,en=OLD_CAPTION) if rid==R.CAPTION_ID else entry
                if entry['sha']!=record['sha']: raise ValueError('Dialogue fingerprint changed')
                before[rid]=DB.render(old,record,prior,width); after[rid]=DB.render(entry,record,current,width)
                if before[rid]!=after[rid]:
                    if rid not in wanted: raise ValueError('Unrelated dialogue changed')
                    audit.append(dict(id=rid,english=after[rid]))
            original=arc.read(next(r for r in arc.files if r['id']==mid))
            if DB.rebuild_member(mid,before,b['mapping'])!=original: raise ValueError('Public stage source mismatch')
            changed[mid]=DB.rebuild_member(mid,after,b['mapping'])
    if {r['id'] for r in audit}!=wanted: raise ValueError('Incomplete stage corrections')
    return changed,audit


def part(b):
    old=(BASE/'rpw.bin').read_bytes(); needle=L.encode(R.PART_OLD,b['mapping'])+b'\0'
    if old.count(needle)!=1: raise ValueError('Part-name allocation is not unique')
    new=L.encode(R.PART_NEW,b['mapping'])+b'\0'; at=old.index(needle)
    out=old[:at]+new+bytes(len(needle)-len(new))+old[at+len(needle):]
    restored=out[:at]+needle+out[at+len(needle):]
    if restored!=old: raise ValueError('Unrelated RPW data changed')
    return out,dict(offset=at,old=R.PART_OLD,new=R.PART_NEW,bytes_preserved=len(out)==len(old))


def plan():
    from tools.game_build import VERSION as current
    if current!=VERSION: raise ValueError('Wrong build version')
    b=json.loads((BASE/'build.json').read_text('utf8'))
    proof=ROOT/'work/ui/review44_verified_0.5.44.json'; ready=json.loads((ROOT/'work/ui/local_release_0.5.44.json').read_text('utf8'))
    if sha256_file(proof)!=ready['final_readback_sha256']: raise ValueError('Public readback evidence changed')
    for name,digest in b['outputs'].items():
        if sha256_file(BASE/name)!=digest: raise ValueError('Public asset changed: '+name)
    elf,hook=dictionary((BASE/'EBOOT.BIN').read_bytes(),b)
    stage,dialogue=stages(b); rpw,part_info=part(b); ui=UI.plan(config(ROOT/'config/tengoku.json'),b['mapping'])
    raw=EF.source_members(EF._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,info,report=T.render(raw,VERSION); T.verify(raw,title,pixels)
    return dict(prior=b,elf=elf,hook=hook,stage=stage,dialogue=dialogue,rpw=rpw,part=part_info,ui=ui,
                title=title,title_info=report,parent_proof_sha256=sha256_file(proof))


def build(p):
    folder=ROOT/'work/output/builds'/VERSION
    if folder.exists(): raise ValueError('Preserve existing candidate')
    folder.mkdir(parents=True); b=copy.deepcopy(p['prior'])
    for name in b['outputs']:
        if name not in CHANGED: shutil.copyfile(BASE/name,folder/name)
    for name in ('font_1.bin','font_3.bin'): shutil.copyfile(BASE/name,folder/name)
    (folder/'EBOOT.BIN').write_bytes(p['elf']); (folder/'rpw.bin').write_bytes(p['rpw'])
    members={ 'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},'RPW_DATA.CPK':{0:p['rpw']},
              'EFFPS3.CPK':{229:p['title']},'STGZ3OF2.cpk':p['stage'] }
    audits={}
    for name,replacements in members.items():
        with CPK(BASE/name) as arc: compressed={r['id'] for r in arc.files if r['id'] in replacements and r['size']!=r['extract']}
        build_cpk(BASE/name,folder/name,replacements,compress=compressed)
        audits[name]=compare(BASE/name,folder/name,replacements)
    tool=str(config(ROOT/'config/tengoku.json')['offline_sdat_tool'])
    cpk=folder/'STGZ3OF2.cpk'; sdat=folder/'STGZ3OF2.SDAT'; back=folder/'stage-roundtrip.cpk'
    subprocess.run([tool,'-e',str(cpk),str(sdat)]+DB.NPDATA_ENCRYPT,capture_output=True,check=True)
    subprocess.run([tool,'-d',str(sdat),str(back),'0'],capture_output=True,check=True)
    if back.read_bytes()!=cpk.read_bytes(): raise ValueError('Stage encryption round trip failed')
    back.unlink()
    b.update(version=VERSION,title_screen=p['title_info'],runtime_verified=False,layout_verified=False,
        review45=dict(hook=p['hook'],dialogue=p['dialogue'],part=p['part']))
    b['executable']['output_sha256']=sha256(p['elf'])
    for key in ('used_bytes','headroom_bytes'): b['executable']['ui_hook']['table'][key]=p['hook'][key]
    b['stage_archive'].update(cpk_sha256=sha256_file(cpk),sdat_sha256=sha256_file(sdat),roundtrip_verified=True)
    for name in b['outputs']: b['outputs'][name]=sha256_file(folder/name)
    b['incremental_build']=dict(parent_version='0.5.44',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],archive_isolation=audits,
        unchanged_fonts=True,unchanged_mapping=True,unchanged_advances=True,changed_stage_members=[611,628,688])
    write_json(folder/'build.json',b)
    print('Built 0.5.45: four screenshot fixes and Chaos Caper.',flush=True)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--apply',action='store_true'); args=p.parse_args(); data=plan()
    print('Lookup cases:',len(data['hook']['cases']),'Changed dialogue:',data['dialogue'],'Part:',data['part'])
    if args.apply: build(data)
    else: print('DRY RUN: no game assets written.')


if __name__=='__main__': main()
