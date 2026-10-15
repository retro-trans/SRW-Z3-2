"""Prepare the four reported corrections on certified 0.5.42 assets."""
import argparse,copy,json,shutil,struct,subprocess
from tools.common import ROOT,sha256,sha256_file,write_json
from tools import review43_text as R,ui_layout_text as U,title_screen as T,eff_art as E
from tools import ui_hook as H,eboot_text as ET,dialogue as D,dialogue_build as DB
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.verify_archives import compare

VERSION='0.5.43';BASE=ROOT/'work/output/builds/0.5.42'
CHANGED={'EBOOT.BIN','AIDDATAPACK.CPK','STGZ3OF2.SDAT','EFFPS3.CPK'}


def command_patch(elf,mapping):
    """Redirect exactly one lookup slot to an already allocated English value."""
    phs=H._headers(elf)[2];read=H._reader(elf,phs)
    def offset(va):
        for p in phs:
            if p[3]<=va<p[3]+p[5]:return p[2]+va-p[3]
        raise ValueError('Unmapped dictionary slot')
    def cstr(va):
        out=bytearray()
        for i in range(256):
            b=read(va+i,1)
            if b==b'\0':return bytes(out)
            out+=b
        raise ValueError('Command output did not terminate')
    if read(H.EXT_VA,4)!=H.MAGIC:raise ValueError('Hook dictionary changed')
    mask,slots=struct.unpack('>II',read(H.EXT_VA+8,8));target=[];values=set()
    key='トランザム発動'.encode('cp932');wanted=ET.encode('Trans-Am',mapping)
    for i in range(mask+1):
        at=slots+i*H.SLOT;h,k,en,n,_=struct.unpack('>IIIHH',read(at,H.SLOT))
        if not k:continue
        if read(en,len(wanted)+1)==wanted+b'\0':values.add(en)
        if n==len(key)and read(k,n)==key:target.append((at,en))
    if len(target)!=1 or not values:raise ValueError('Command dictionary bindings differ')
    at,old=target[0]
    if cstr(old)!=ET.encode('Activate Trans-Am',mapping):raise ValueError('Command parent differs')
    out=bytearray(elf);pos=offset(at+8);new=min(values);struct.pack_into('>I',out,pos,new)
    restored=bytearray(out);restored[pos:pos+4]=elf[pos:pos+4]
    if restored!=elf:raise ValueError('Unrelated executable bytes changed')
    return bytes(out),dict(key_sha256=sha256(key),slot_va=at,old_value_va=old,new_value_va=new,
        modified_file_ranges=[[pos,pos+4]],confirmation_question_unchanged=True)


def ui_check(old,new,mapping):
    from tools import ui_catalog as C,menu_layout as M
    original=R.B.source();a=len(old)-len(original);b=len(new)-len(original)
    before={at-a:r for r in C.fssa_strings(old,decode=lambda r:r.hex())for at in r['widget_offsets']}
    after={at-b:r for r in C.fssa_strings(new,decode=lambda r:r.hex())for at in r['widget_offsets']}
    edits={e['widget_offset']:e for e in R.plan()['edits']}
    if before.keys()!=after.keys():raise ValueError('Map panel widget identities changed')
    for at,row in before.items():
        if old[at+a+4:at+a+32]!=new[at+b+4:at+b+32]:raise ValueError('Widget geometry/style changed')
        wanted=M.encode(edits[at],mapping)if at in edits else row['raw']
        if after[at]['raw']!=wanted:raise ValueError('Unrelated widget text changed: '+hex(at))
    return dict(widgets=len(before),all_geometry_and_styles_unchanged=True,
        changed_widgets=sum(before[at]['raw']!=after[at]['raw']for at in before))


def native_cases(elf,b,sb):
    from tools.ui_coverage import ui_string_table
    from tools import review32_content as C,ui_description_layout as W
    rows=ui_string_table(sb,decode=lambda raw:raw.hex());prefix=rows[3]['raw'];suffix=rows[4]['raw'];cases=[]
    # Counts are native fullwidth cells, interleaved with mapped English.
    for n in (0,1,9,11,99,100,999):
        number=''.join(chr(0xff10+int(c))for c in str(n)).encode('cp932')
        span=sum(map(W.advance,'There are  teams that still have actions remaining.'))+len(str(n))*32
        cases.append(('phase:'+str(n),prefix+number+suffix,span,False))
    centered=C.origin_cases(elf,b['mapping'],b['executable']['link_layout'],only_rows=cases,quads=(28,31))
    if any(r['left']<80 or 1280-r['left']>1207 for r in centered):raise ValueError('Phase row exceeds popup')
    report=b['executable']['ui_hook'];runner=H._Runner(elf,int(report['stub_va'],16),report['stub_bytes'])
    read=H._reader(elf,H._headers(elf)[2]);commands=[]
    for jp,en in (('トランザム発動','Trans-Am'),('トランザム発動を行いますか？','Activate Trans-Am?')):
        ptr,steps=runner.run(jp.encode('cp932')+b'\0');wanted=ET.encode(en,b['mapping'])+b'\0'
        if ptr is None or read(ptr,len(wanted))!=wanted:raise ValueError('Installed command lookup differs: '+en)
        commands.append(dict(english=en,steps=steps))
    width=sum(b['widths'][c]for c in 'Trans-Am')*32/32
    if width>200:raise ValueError('Trans-Am exceeds the command width')
    from tools import ppc_exec as P
    mem=P.Memory()
    for n,seg in enumerate(H._headers(elf)[2][:2]):mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=n==1)
    mem.map(0x40000000,bytes(0x4000));mem.map(0x41000000,bytes(0x2000));mem.map(0x42000000,bytes(0x100))
    mem.write(H.TOC+H.STATE_DISP,struct.pack('>I',0x41000000));caption_cases=[]
    raw='トランザム発動'.encode('cp932')
    for quad in (28,32):
        for mode in (0,1):
            mem.write(0x42000000,raw+b'\0');mem.write(0x41000000,bytes(0x2000))
            for at in (0x54,0x5c):mem.write(0x41000000+at,struct.pack('>f',quad))
            mem.write(0x410000ac,struct.pack('>H',mode));vm=P.Machine(mem)
            vm.r=[0x770000+r for r in range(32)];vm.r[1]=0x40003f00;vm.r[2]=H.TOC
            vm.r[3]=0x42000000;vm.r[7]=1;vm.r[8]=0;vm.f[1]=1140;vm.f[2]=160;vm.f[3]=1.;vm.lr=0x152000
            before=(vm.r[1],vm.r[2],vm.r[27:32],vm.lr);vm.pc=0x149bc;vm.run({0x14158},limit=50000)
            span=width*quad/32
            if abs(vm.f[1]+span/2-1140)>.0001 or vm.f[1]<1030 or vm.f[1]+span>1250:
                raise ValueError('Trans-Am caption exceeds its button')
            if (vm.f[2],vm.f[3])!=(160,1.)or(vm.r[1],vm.r[2],vm.r[27:32],vm.lr)!=before:
                raise ValueError('Command centering changes caller state')
            if mem.read(vm.r[3],len(raw)+1)!=raw+b'\0':raise ValueError('Command lookup changed its native input')
            caption_cases.append(dict(quad=quad,mode=mode,left=vm.f[1],right=vm.f[1]+span,center=1140,steps=vm.steps))
    return dict(phase_origins=centered,command_lookups=commands,command_width_at_32=width,command_caption_cases=caption_cases)


def plan():
    from tools.game_build import VERSION as current
    from tools.pipeline import config
    if current!=VERSION:raise ValueError('Incremental version differs')
    prior=json.loads((BASE/'build.json').read_text('utf8'))
    ready=json.loads((ROOT/'work/ui/local_release_0.5.42.json').read_text('utf8'))
    proof=ROOT/'work/ui/review42_verified_0.5.42.json'
    if sha256_file(proof)!=ready['final_readback_sha256']:raise ValueError('Parent proof changed')
    for name,digest in prior['outputs'].items():
        if sha256_file(BASE/name)!=digest:raise ValueError('Parent asset changed: '+name)
    if R.plan()!=json.loads(R.DEST.read_text('utf8')):raise ValueError('Map plan changed')
    ui=U.plan(config(ROOT/'config/tengoku.json'),prior['mapping'])
    with CPK(BASE/'AIDDATAPACK.CPK')as arc:old=arc.read(next(r for r in arc.files if r['id']==0))
    checked=ui_check(old,ui['members'][0],prior['mapping'])
    elf,command=command_patch((BASE/'EBOOT.BIN').read_bytes(),prior['mapping'])
    native=native_cases(elf,prior,ui['members'][5])
    active=DB.translations();records=D.records(598);rendered={}
    for record in records:
        rid=record['id']
        if rid in active:rendered[rid]=DB.render(active[rid],record,ET.resolver(),lambda c:prior['widths'].get(c,32))
    if '...A Tenshi.'not in rendered['598:t_5:36']:raise ValueError('Tenshi correction missing')
    stage=DB.rebuild_member(598,rendered,prior['mapping'])
    with CPK(BASE/'STGZ3OF2.cpk')as arc:old_stage=arc.read(next(r for r in arc.files if r['id']==598))
    old=ET.encode('...An Tenshi.',prior['mapping']);new=ET.encode('...A Tenshi.',prior['mapping'])
    if old_stage.count(old)!=1 or old_stage.replace(old,new)!=stage:
        raise ValueError('Stage member changes more than the reported article')
    raw=E.source_members(E._settings(),[T.MEMBER],{T.MEMBER:T.SOURCE_SHA})[T.MEMBER]
    title,pixels,_,info=T.render(raw,VERSION);T.verify(raw,title,pixels)
    return dict(prior=prior,ui=ui,ui_check=checked,elf=elf,command=command,native=native,stage=stage,
        title=title,title_info=info,parent_proof_sha256=sha256_file(proof),tenshi=rendered['598:t_5:36'])


def build(p):
    folder=ROOT/'work/output/builds'/VERSION
    if folder.exists():raise ValueError('Preserve existing candidate')
    folder.mkdir(parents=True);report=copy.deepcopy(p['prior'])
    for name in report['outputs']:
        if name not in CHANGED:shutil.copyfile(BASE/name,folder/name)
    for name in ('font_1.bin','font_3.bin','rpw.bin'):shutil.copyfile(BASE/name,folder/name)
    (folder/'EBOOT.BIN').write_bytes(p['elf']);archives={}
    for name,members in {'AIDDATAPACK.CPK':{0:p['ui']['members'][0],5:p['ui']['members'][5]},
                         'EFFPS3.CPK':{229:p['title']},'STGZ3OF2.cpk':{598:p['stage']}}.items():
        with CPK(BASE/name)as arc:compressed={r['id']for r in arc.files if r['id']in members and r['size']!=r['extract']}
        build_cpk(BASE/name,folder/name,members,compress=compressed)
        archives[name]=compare(BASE/name,folder/name,members)
    from tools.pipeline import config
    tool=str(config(ROOT/'config/tengoku.json')['offline_sdat_tool'])
    sdat=folder/'STGZ3OF2.SDAT';cpk=folder/'STGZ3OF2.cpk';back=folder/'STGZ3OF2.roundtrip.cpk'
    subprocess.run([tool,'-e',str(cpk),str(sdat)]+DB.NPDATA_ENCRYPT,capture_output=True,check=True)
    subprocess.run([tool,'-d',str(sdat),str(back),'0'],capture_output=True,check=True)
    if back.read_bytes()!=cpk.read_bytes():raise ValueError('Stage encryption round trip differs')
    back.unlink()
    report.update(version=VERSION,title_screen=p['title_info'],runtime_verified=False,layout_verified=False,
        ui_context_text=p['ui']['report']['context_text'],review43=dict(command=p['command'],native=p['native'],
        ui=p['ui_check'],tenshi=p['tenshi']))
    report['extra_art']['AIDDATAPACK.CPK']=dict(archive=archives['AIDDATAPACK.CPK'],members_verified=U.verify_archive(folder/'AIDDATAPACK.CPK',p['ui']))
    report['extra_art']['EFFPS3.CPK']=dict(archive=archives['EFFPS3.CPK'],title=p['title_info'])
    report['stage_archive'].update(cpk_sha256=sha256_file(cpk),sdat_sha256=sha256_file(sdat),roundtrip_verified=True)
    report['executable']['output_sha256']=sha256(p['elf'])
    report['executable']['review43_command']=p['command']
    for name in report['outputs']:
        actual=sha256_file(folder/name)
        if name not in CHANGED and actual!=p['prior']['outputs'][name]:raise ValueError('Copied asset differs')
        report['outputs'][name]=actual
    report['incremental_build']=dict(parent_version='0.5.42',parent_build_sha256=sha256_file(BASE/'build.json'),
        parent_proof_sha256=p['parent_proof_sha256'],unchanged_fonts=True,unchanged_mapping=True,unchanged_advances=True,
        changed_stage_members=[598],archive_isolation=archives)
    write_json(folder/'build.json',report)
    print('Built 0.5.43: phase centering, Aboard/terrain sources, A Tenshi and Trans-Am.',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args();p=plan()
    print('UI:',p['ui_check']);print('Native:',p['native']);print('Dialogue:',p['tenshi'])
    if a.apply:build(p)
    else:print('DRY RUN: no game assets written.')

if __name__=='__main__':main()
