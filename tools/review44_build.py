"""Build the reported capitalization/reward/menu fixes on certified 0.5.43."""
import argparse,copy,json,re,shutil,struct,subprocess
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import review44_text as R,ui_layout_text as U,ui_hook as H,eboot_text as E
from tools import library_build as L,library_text as LT,dialogue as D,dialogue_build as DB
from tools import title_screen as T,eff_art as EF
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.44';BASE=ROOT/'work/output/builds/0.5.43'
CHANGED={'EBOOT.BIN','AIDDATAPACK.CPK','STGZ3OF2.SDAT','EFFPS3.CPK','MTZKN_PT.CPK'}


def dictionary_patch(elf,mapping):
    grouped,rows=R.U.checked();changes={rid:pair for rid,pair in R.HELP.items()}
    changes.update({rid:(old,R.plan()['reward_catalog'][rid])for rid,old in R.OLD_REWARDS.items()})
    read=H._reader(elf,H._headers(elf)[2]);mask,slots=struct.unpack('>II',read(H.EXT_VA+8,8))
    index={};slot_at={}
    for i in range(mask+1):
        _,key,en,n,_=struct.unpack('>IIIHH',read(slots+i*16,16))
        if key:
            raw=read(key,n);index[raw]=en;slot_at[raw]=slots+i*16
    replacements={};cases=[];key_values={}
    for rid,(old,new)in changes.items():
        if rows[rid]['en']!=new:raise ValueError('Canonical UI correction is stale')
        for src in grouped[rid]:
            key=src['raw']if src['encoding']=='cp932'else H.utf8_key(src['raw'],H.PREPARED.read_bytes())
            if key not in index:raise ValueError('Parent UI lookup binding missing: '+src['id'])
            a=E.encode(old,mapping,utf8_source=src['encoding']=='utf-8')+b'\0'
            z=(R.caption_encoded(new,mapping)if new.startswith('　')else E.encode(new,mapping,utf8_source=src['encoding']=='utf-8'))+b'\0';va=index[key]
            if read(va,len(a))!=a:raise ValueError('Parent UI value differs: '+src['id'])
            if va in replacements and replacements[va]!=(a,z):raise ValueError('Shared UI value has conflicting corrections')
            if any(va<p<va+len(a)for p in index.values()):raise ValueError('UI output allocation contains another value pointer')
            replacements[va]=(a,z);key_values[key]=z;cases.append(dict(id=src['id'],key_hex=key.hex(),english=new))
    out=bytearray(elf);spans=[];read_phs=H._headers(elf)[2]
    def put(va,raw):
        seg=next(p for p in read_phs if p[3]<=va<p[3]+p[5]);at=seg[2]+va-seg[3]
        out[at:at+len(raw)]=raw;spans.append([at,at+len(raw)])
    parent=json.loads((BASE/'build.json').read_text('utf8'))['executable']['ui_hook']['table']
    cursor=(parent['used_bytes']+15)&~15;appended={}
    for va,(old,new)in replacements.items():
        if len(new)<=len(old):put(va,new+bytes(len(old)-len(new)));continue
        if cursor+len(new)>parent['ext_size']:raise ValueError('Dictionary headroom exhausted')
        target=H.EXT_VA+cursor
        if read(target,len(new))!=bytes(len(new)):raise ValueError('Reserved dictionary headroom occupied')
        put(target,new);appended[new]=target;cursor+=len(new)
    for key,new in key_values.items():
        if new in appended:put(slot_at[key]+8,struct.pack('>I',appended[new]))
    restored=bytearray(out)
    for a,z in spans:restored[a:z]=elf[a:z]
    if restored!=elf:raise ValueError('Dictionary correction changed unrelated bytes')
    return bytes(out),dict(values=len(replacements),modified_file_ranges=spans,cases=cases,code_and_keys_unchanged=True,
        used_bytes=max(cursor,parent['used_bytes']),headroom_bytes=parent['ext_size']-max(cursor,parent['used_bytes']))


def numeric_cases(elf):
    from tools import ppc_exec as P
    mem=P.Memory()
    for n,seg in enumerate(H._headers(elf)[2][:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=n==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x200));cases=[]
    mem.write(0x41000068,struct.pack('>f',28));mem.write(0x41000070,struct.pack('>f',17))
    for bound in R.plan()['bounds'][:3]:
        for value in (0,9,99,500,750,999,9999,99999,999999,9999999,99999999):
            vm=P.Machine(mem);vm.r[1]=0x40003000;vm.r[2]=H.TOC;vm.r[28]=value;vm.pc=0x14f10
            vm.run({0x14ba0,0x14ba4},limit=2000);digits=vm.r[24]
            if digits!=len(str(value)):raise ValueError('Native reward digit count differs')
            vm.r[27]=0x41000000;vm.f[31]=780;vm.pc=0x14f5c;vm.run({0x14bb4},limit=vm.steps+100)
            left=vm.f[31]-2;gap=left-bound['right']
            if gap<8:raise ValueError('Reward label overlaps live number')
            cases.append(dict(label=bound['label'],value=value,digits=digits,conservative_left=left,gap=gap,steps=vm.steps))
    return cases


def caption_cases(elf,b,hook):
    """Selected native keys and preloaded English must reach the same origin."""
    from tools import ppc_exec as P
    from tools.ui_description_layout import advance
    mem=P.Memory()
    for n,seg in enumerate(H._headers(elf)[2][:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=n==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000));mem.map(0x42000000,bytes(0x100))
    mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000));cases=[]
    labels={r['english']:bytes.fromhex(r['key_hex'])for r in hook['cases']if r['english'].startswith('　')}
    for text,key in labels.items():
        span=32+sum(map(advance,text[1:]));encoded=R.caption_encoded(text,b['mapping'])
        for path,raw in (('selected-key',key),('preloaded',encoded)):
            for mode in (0,1):
                mem.write(0x42000000,raw+b'\0');mem.write(0x41000000,bytes(0x2000))
                for at in (0x54,0x5c):mem.write(0x41000000+at,struct.pack('>f',31))
                mem.write(0x410000ac,struct.pack('>H',mode));vm=P.Machine(mem)
                vm.r=[0x770000+r for r in range(32)];vm.r[1]=0x40003f00;vm.r[2]=H.TOC;vm.r[3]=0x42000000;vm.r[7]=1;vm.r[8]=0
                vm.f[1]=640;vm.f[2]=360;vm.f[3]=1.;vm.lr=0x152000
                before=(vm.r[1],vm.r[2],vm.r[27:32],vm.lr);vm.pc=0x149bc;vm.run({0x14158},limit=50000)
                expected=640-span*31/64
                if abs(vm.f[1]-expected)>.0001:raise ValueError('Deployment caption origin differs: '+path+' '+text)
                if (vm.f[2],vm.f[3])!=(360,1.)or(vm.r[1],vm.r[2],vm.r[27:32],vm.lr)!=before:raise ValueError('Caption changes caller state')
                cases.append(dict(english=text,path=path,mode=mode,left=vm.f[1],width=span*31/32,center=640,steps=vm.steps))
    if len(cases)!=20:raise ValueError('Deployment caption-state inventory changed')
    return cases


def ui_check(old,new,mapping):
    from tools import menu_layout as M
    original=R.B.source();a=len(old)-len(original);b=len(new)-len(original)
    before={at-a:r for r in R.U.fssa_strings(old,decode=lambda r:r.hex())for at in r['widget_offsets']}
    after={at-b:r for r in R.U.fssa_strings(new,decode=lambda r:r.hex())for at in r['widget_offsets']}
    edits={e['widget_offset']:e for e in R.plan()['edits']}
    if before.keys()!=after.keys():raise ValueError('UI identities changed')
    for at,row in before.items():
        edit=edits.get(at,{})
        if after[at]['raw']!=(M.encode(edit,mapping)if edit else row['raw']):raise ValueError('Unrelated widget text changed')
        old_state=old[at+a+4:at+a+32];state=bytearray(new[at+b+4:at+b+32])
        if 'x'in edit:state[:4]=old_state[:4]
        if 'mode'in edit:state[19]=old_state[19]
        if state!=old_state:raise ValueError('Unrelated widget geometry or state changed')
    # Mapped blank cells preserve 32 units without triggering native-width fallback.
    from tools import ui_build as F
    for fid in (1,3):
        page=F.atlas((BASE/('font_%d.bin'%fid)).read_bytes())
        for token in (' ','@menu-pad:4','@menu-pad:1'):
            x,y=F.cell_xy(mapping[token])
            if page[y:y+32,x:x+32].any():raise ValueError('Indentation padding is visible')
    return dict(widgets=len(before),edited_widgets=len(edits),numeric_positions=3,
        padding_invisible=True,font_and_row_spacing_unchanged=True)


def stages(prior):
    active=DB.translations();affected={rid:r for rid,r in active.items()if '$$コロニーレーザー$$'in r['en']}
    if len(affected)!=13:raise ValueError('Colony Laser dialogue inventory changed')
    terms=json.loads(LT.GLOSSARY.read_text('utf8'))['terms'];old_terms=copy.deepcopy(terms)
    next(t for t in old_terms if t['token']=='コロニーレーザー')['en']='colony laser'
    resolver=LT.Resolver(terms);old_resolver=LT.Resolver(old_terms);width=lambda c:prior['widths'].get(c,32)
    members={};audit=[]
    with CPK(BASE/'STGZ3OF2.cpk')as arc:
        for mid in sorted({int(rid.split(':')[0])for rid in affected}):
            rendered={};before={}
            for record in D.records(mid):
                rid=record['id']
                if rid not in active:continue
                rendered[rid]=DB.render(active[rid],record,resolver,width)
                before[rid]=DB.render(active[rid],record,old_resolver,width)
                if rid in affected:
                    if 'Colony Laser'not in rendered[rid]:raise ValueError('Canonical term did not expand')
                    if record['jp'].partition('\n')[0].strip()and len(rendered[rid].split('\n'))>4:raise ValueError('Changed speech exceeds three lines')
                    audit.append(dict(id=rid,english=rendered[rid]))
            old=arc.read(next(r for r in arc.files if r['id']==mid))
            if DB.rebuild_member(mid,before,prior['mapping'])!=old:raise ValueError('Parent stage differs beyond capitalization')
            members[mid]=DB.rebuild_member(mid,rendered,prior['mapping'])
    return members,audit


def libraries(prior):
    library=LT.load_library();entries,errors=LT.load_translations()
    if errors:raise ValueError(errors)
    rendered=L.plan(library,entries,json.loads(LT.GLOSSARY.read_text('utf8'))['terms'])
    replacements={};audit=[];normal=lambda s:' '.join(s.replace('　',' ').split())
    from tools.source_text import library_fields
    for kind,name in (('keyword','MTZKN_KW.CPK'),('pilot','MTZKN_PT.CPK'),('robot','MTZKN_RT.CPK')):
        rows={}
        with CPK(BASE/name)as arc:
            for row in arc.files:
                old=arc.read(row);fields={tag:L.wrap(rendered[kind][row['id']][tag],lambda c:prior['widths'].get(c,32))for tag in ('DSCR','DSC2')}
                payloads={tag:L.encode(text,prior['mapping'])for tag,text in fields.items()};new=L.rebuild(old,payloads)
                if new==old:continue
                decoded=bytes(v if v in (0,0x5e)else v^0x5e for v in old);changed=[]
                for f in library_fields(old)[1]:
                    tag=f['tag']
                    if tag not in payloads:continue
                    raw=decoded[f['offset']:f['offset']+f['bytes']]
                    if raw==payloads[tag]:continue
                    previous=L.decode(raw,prior['mapping']);wanted=re.sub(r'\bcolony\s+laser\b','Colony Laser',normal(previous),flags=re.I)
                    if normal(fields[tag])!=wanted:raise ValueError('Library change exceeds capitalization: '+str((kind,row['id'],tag)))
                    changed.append(tag)
                rows[row['id']]=new;audit.append(dict(archive=name,id=row['id'],fields=changed))
        if rows:replacements[name]=rows
    if set(replacements)!={'MTZKN_PT.CPK'}:raise ValueError('Unexpected Library archive changes')
    return replacements,audit


def plan():
    from tools.pipeline import config
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Current version differs')
    prior=json.loads((BASE/'build.json').read_text('utf8'));proof=ROOT/'work/ui/review43_verified_0.5.43.json'
    ready=json.loads((ROOT/'work/ui/local_release_0.5.43.json').read_text('utf8'))
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Certified parent proof changed')
    for name,digest in prior['outputs'].items():
        if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
    ui=U.plan(config(ROOT/'config/tengoku.json'),prior['mapping'])
    with CPK(BASE/'AIDDATAPACK.CPK')as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    checked=ui_check(old,ui['members'][0],prior['mapping'])
    elf,hook=dictionary_patch((BASE/'EBOOT.BIN').read_bytes(),prior['mapping']);native=numeric_cases(elf);captions=caption_cases(elf,prior,hook)
    stage,dialogue=stages(prior);lib,library=libraries(prior)
    raw=EF.source_members(EF._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
    return dict(prior=prior,ui=ui,ui_check=checked,elf=elf,hook=hook,native=native,captions=captions,stage=stage,
        dialogue=dialogue,libraries=lib,library_audit=library,title=title,title_info=info,parent_proof_sha256=sha256_file(proof))


def build(p):
    folder=ROOT/'work/output/builds'/VERSION
    if folder.exists():raise ValueError('Preserve existing candidate')
    folder.mkdir(parents=True);b=copy.deepcopy(p['prior'])
    for name in b['outputs']:
        if name not in CHANGED:shutil.copyfile(BASE/name,folder/name)
    for name in ('font_1.bin','font_3.bin','rpw.bin'):shutil.copyfile(BASE/name,folder/name)
    (folder/'EBOOT.BIN').write_bytes(p['elf']);archives={}
    changes=dict(p['libraries'],**{'AIDDATAPACK.CPK':{0:p['ui']['members'][0]},'EFFPS3.CPK':{229:p['title']},'STGZ3OF2.cpk':p['stage']})
    for name,members in changes.items():
        with CPK(BASE/name)as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
        build_cpk(BASE/name,folder/name,members,compress=compressed);archives[name]=compare(BASE/name,folder/name,members)
    from tools.pipeline import config
    tool=str(config(ROOT/'config/tengoku.json')['offline_sdat_tool']);sdat=folder/'STGZ3OF2.SDAT';cpk=folder/'STGZ3OF2.cpk';back=folder/'STGZ3OF2.roundtrip.cpk'
    subprocess.run([tool,'-e',str(cpk),str(sdat)]+DB.NPDATA_ENCRYPT,capture_output=True,check=True)
    subprocess.run([tool,'-d',str(sdat),str(back),'0'],capture_output=True,check=True)
    if back.read_bytes()!=cpk.read_bytes():raise ValueError('Stage encryption round trip failed')
    back.unlink()
    b.update(version=VERSION,title_screen=p['title_info'],runtime_verified=False,layout_verified=False,
        ui_context_text=p['ui']['report']['context_text'],review44=dict(ui=p['ui_check'],hook=p['hook'],native_rewards=p['native'],
        dialogue=p['dialogue'],library=p['library_audit'],caption_cases=p['captions']))
    b['extra_art']['AIDDATAPACK.CPK']=dict(archive=archives['AIDDATAPACK.CPK'],members_verified=U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui']))
    b['extra_art']['EFFPS3.CPK']=dict(archive=archives['EFFPS3.CPK'],title=p['title_info'])
    b['stage_archive'].update(cpk_sha256=sha256_file(cpk),sdat_sha256=sha256_file(sdat),roundtrip_verified=True)
    b['review44']['library_archive']=archives['MTZKN_PT.CPK']
    b['executable']['output_sha256']=sha256(p['elf']);b['executable']['review44_dictionary']=p['hook']
    for key in ('used_bytes','headroom_bytes'):b['executable']['ui_hook']['table'][key]=p['hook'][key]
    for name in b['outputs']:
        actual=sha256_file(folder/name)
        if name not in CHANGED and actual!=p['prior']['outputs'][name]:raise ValueError('Copied asset differs')
        b['outputs'][name]=actual
    b['incremental_build']=dict(parent_version='0.5.43',parent_build_sha256=sha256_file(BASE/'build.json'),parent_proof_sha256=p['parent_proof_sha256'],
        unchanged_fonts=True,unchanged_mapping=True,unchanged_advances=True,changed_stage_members=sorted(p['stage']),archive_isolation=archives)
    write_json(folder/'build.json',b);print('Built 0.5.44: Colony Laser, reward rows and deployment menus.',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    print('UI:',data['ui_check']);print('Native reward cases:',len(data['native']));print('Dictionary values/keys:',data['hook']['values'],len(data['hook']['cases']))
    print('Colony Laser dialogue:',len(data['dialogue']),'Library:',data['library_audit'])
    if a.apply:build(data)
    else:print('DRY RUN: no game assets written.')

if __name__=='__main__':main()
