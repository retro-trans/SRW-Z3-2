"""Final report, skill-level, default-name and whole weapon-table readback."""
import argparse,json,shutil,struct
from pathlib import Path
from functools import lru_cache
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import review26_messages as G,review26_weapons as W,rpw_text as R,ui_hook as H,eboot_text as E,library_build as L,runtime_names as N
from tools.cpk import CPK
SHOTS=(('stage-report','4265647b-be86-40f7-97f2-d02f9c00565e'),('name-dot','4ed336c4-0a01-48d7-be4b-79b342f321d5'),('skill-level','c4197ab7-2a1f-4c5d-88df-5d074b7b73a4'),('sr-condition','ef318207-dd52-4259-87a7-5eb5406ef588'),('weapons','3b511bbe-dcc2-4f51-9fcf-b6d69d237324'))

def full_name(elf,mapping,given='ヒビキ',family='カミシロ'):
    """Run the native full-name caller, patched getters and separator end to end."""
    from tools import ppc_exec as P
    mem=P.Memory();fields=bytearray(0x40)
    for off,va in ((0,0x41000000),(4,0x41000100),(0x2c,0x41000200)):struct.pack_into('>I',fields,off,va)
    mem.map(H.TOC-0x3c68,fields)
    mem.map(0x41000000,given.encode('cp932')+b'\0');mem.map(0x41000100,family.encode('cp932')+b'\0');mem.map(0x41000200,'・'.encode('cp932')+b'\0')
    for seg in H._headers(elf)[2][:2]:mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
    stack=mem.map(0x40000000,b'\x88'*0x3000)
    def string(at):
        result=bytearray()
        while mem.read(at+len(result),1)!=b'\0':
            result+=mem.read(at+len(result),1)
            if len(result)>128:raise ValueError('Name escaped bounded field')
        return bytes(result)
    def strcpy(m):mem.write(m.r[3],string(m.r[4])+b'\0');m.pc=m.lr
    def strcat(m):mem.write(m.r[3],string(m.r[3])+string(m.r[4])+b'\0');m.pc=m.lr
    m=P.Machine(mem);m.r=[0x90000+n for n in range(32)];m.r[1]=0x40000100;m.r[2]=H.TOC;m.pc=0x1fb444
    m.hooks={0x68f88c:strcpy,0x68f400:strcat};m.run({0x1fb494},limit=2000)
    raw=string(0x40000170)
    expected=(E.encode('Hibiki',mapping)if given=='ヒビキ'else given.encode('cp932'))+(E.encode(' ',mapping)if (given,family)==('ヒビキ','カミシロ')else '・'.encode('cp932'))+(E.encode('Kamishiro',mapping)if family=='カミシロ'else family.encode('cp932'))
    if raw!=expected or len(raw)>40:raise ValueError('Native full-name composer differs')
    if mem.read(0x41000000,len(given.encode('cp932'))+1)!=given.encode('cp932')+b'\0':raise ValueError('Custom name bytes changed')
    if stack[0x170+len(raw)+1:0x199]!=b'\x88'*(0x199-0x170-len(raw)-1):raise ValueError('Name row canary changed')
    return dict(default_given=given=='ヒビキ',default_family=family=='カミシロ',bytes=len(raw),steps=m.steps)

def verify(version):
    from tools.verify_review25 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'));mapping=build['mapping']
    elf=(folder/'EBOOT.BIN').read_bytes();read=H._reader(elf,H._headers(elf)[2]);info=build['executable']['ui_hook'];runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes'])
    entries=G.hook_entries(H.PREPARED.read_bytes(),mapping);lookups=[]
    for row in entries:
        pointer,steps=runner.run(row['key']+b'\0')
        if read(pointer,len(row['english'])+1)!=row['english']+b'\0':raise ValueError('Final report/level lookup differs: '+row['id'])
        lookups.append(dict(id=row['id'],key_sha256=sha256(row['key']),steps=steps))
    # Every original GIFT literal remains native; translation happens at drawing.
    from tools import squad_text as S,mission_text as M
    gifts=G.plan();mids=sorted({x['member']for r in gifts['strings'].values()for x in r['occurrences']});counts={jp:0 for jp in gifts['strings']}
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        index={r['id']:r for r in arc.files}
        for mid in mids:
            for lit in S.scan(arc.read(index[mid])):
                if any(k=='{'and (nm or b'').startswith(b'GIFT')for k,nm,i in lit['ctx']):
                    jp=M.unescape(lit['raw'])
                    if jp in counts:counts[jp]+=1
    if any(counts[jp]!=len(r['occurrences'])for jp,r in gifts['strings'].items()):raise ValueError('Stage report literal coverage changed')
    # Read every weapon pointer independently out of the final RPW pool.
    source=R.load_rpw();slots=R.slots(source);names=R.load_names();cap=R.caps(slots)
    with CPK(folder/'RPW_DATA.CPK')as arc:final=arc.read(arc.files[0])
    js,pool=R.pool_of(final);weapons=[]
    for s in slots:
        if s['chunk']!='weapon' or not R.needs_text(s['jp']):continue
        pointer=struct.unpack_from('<I',final,s['pointer_offset'])[0];raw=pool[pointer:pool.index(b'\0',pointer)];en=R.text_for(s,names,cap[('weapon',s['col'])])
        if L.decode(raw,mapping)!=en:raise ValueError('Final weapon table differs')
        if s['col']==3 and W.width(en)>W.WIDTH:raise ValueError('Final weapon name exceeds screen column')
        weapons.append(dict(id=s['id'],english=en,width_px=W.width(en)))
    audit=json.loads(W.DEST.read_text('utf8'));fresh,_=W.plan()
    if fresh['changes']or fresh['comparison']!=audit['comparison']or fresh['reference_english_sha256']!=audit['reference_english_sha256']:raise ValueError('Weapon consistency evidence stale')
    namecases=[full_name(elf,mapping,g,f)for g,f in [('ヒビキ','カミシロ'),('Custom','カミシロ'),('ヒビキ','Custom'),('Custom','Name')]]
    @lru_cache(None)
    def width(c):
        from tools.ui_vwf_build import raster
        return raster(c)[1]if c in mapping else 32
    from tools import mission_display as MD
    conditions=[r for r in MD.hook_entries(H.PREPARED.read_bytes(),M.plan(width),mapping)if 'Within 4 turns' in L.decode(r['english'],mapping)and '99999' in L.decode(r['english'],mapping)]
    if len(conditions)!=1:raise ValueError('Episode13 SR condition missing')
    r=conditions[0];p,steps=runner.run(r['key']+b'\0')
    if read(p,len(r['english'])+1)!=r['english']+b'\0':raise ValueError('Episode13 condition corrupted')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png');dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review26-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],lookup_cases=lookups,
        stage_reports=dict(player_strings=22,player_occurrences=97,total_occurrences=sum(counts.values()),members=mids),weapon_cells=weapons,
        weapon_audit_sha256=sha256_file(W.DEST),expanded_weapon_names=len(audit['changes']),full_name_cases=namecases,
        sr_condition=dict(english=L.decode(r['english'],mapping),steps=steps),screenshots=shots,runtime_verified=False,
        proofreading=dict(reviewer='review26_wording',dialogue_rows_examined=31,gift_strings_examined=24,related_mission_conditions_examined=8,shared_full_weapons_examined=440))

def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args();data=verify(a.version)
    print('Lookup cases',len(data['lookup_cases']),'Weapon cells',len(data['weapon_cells']),'Expanded',data['expanded_weapon_names']);print('SR:',data['sr_condition']['english']);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in data['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Reported screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review26_verified_'+a.version+'.json'),data)
if __name__=='__main__':main()
