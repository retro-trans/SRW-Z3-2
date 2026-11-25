"""Prepare hardware-only 0.1.3 Lua diagnostics over sealed Vita 0.1.1.

Keep the error and its lockout intact; expose the callback and Lua error in
the existing 256-byte native error label. No exception is swallowed, no game
logic or permissions change. Does not install, publish, or claim a fix.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile
from tools import vita
from tools import vita_arm as A, vita_source as V, vita_release as R
from tools.vita import self_decrypt as S
from tools.common import ROOT, sha256, sha256_file, write_json

VERSION='0.1.3'
BASE=ROOT/'work/output/vita/builds/0.1.1'
OUTPUT=ROOT/'work/output/vita/diagnostics'/VERSION
SITE=0x81103038
CONTINUE=0x81103060
BASE_SHA='bf5a9b1aa45d400b0750a32169046a8929395f71fdb446be84d0e55dd4afe3f0'
PAINT={
    0x811033d8:('movs r0,#32','movs r0,#24'),
    0x8110340a:('movs r0,#32','movs r0,#24'),
    0x811033ea:('movt r0,#0x4420','movt r0,#0x4200'),
    0x8110341c:('movt r1,#0x4420','movt r1,#0x4200'),
    0x811033fa:('bl 0x8100f5f4','bl 0x8100eac0'),
    0x8110342c:('bl 0x8100f5f4','bl 0x8100eac0'),
}


def literal(label,raw):
    return label+':\n.byte '+','.join(str(b) for b in raw+b'\0')+'\n'


def code(address,version=VERSION):
    source='''
        push.w {r0-r12,lr}
        mrs r0,apsr
        push {r0}
        mov r8,r4
        add.w r9,r5,#0x198
        mov r0,r9
        movs r1,#0
        movw r2,#256
    clear:
        strb r1,[r0],#1
        subs r2,#1
        bne clear
        mov r10,r9
        add.w r11,r9,#254
        movs r7,#0
        adr.w r0,header
        bl append
        mov r0,r8
        bl append
        adr.w r0,newline
        bl append
        ldr r0,[r5,#4]
        cmp r0,#0
        beq unknown
        ldr r0,[r0,#8]
        cmp r0,#0
        beq unknown
        ldr r1,[r0,#-8]
        cmp r1,#4
        bne unknown
        ldr r0,[r0,#-16]
        cmp r0,#0
        beq unknown
        adds r0,#16
        bl append
        b done
    unknown:
        adr.w r0,fallback
        bl append
    done:
        movs r0,#0
        strb.w r0,[r10]
        str r9,[sp,#4]
        str r9,[sp,#20]
        str r0,[sp,#28]
        pop {r0}
        msr apsr_nzcvq,r0
        pop.w {r0-r12,lr}
    '''+f'b.w {CONTINUE}\n'+'''
    append:
        cmp r0,#0
        beq appended
    next_byte:
        cmp r10,r11
        bhs appended
        ldrb r1,[r0],#1
        cmp r1,#0
        beq appended
        cmp r1,#13
        beq next_byte
        cmp r1,#9
        it eq
        moveq r1,#32
        cmp r1,#0x7e
        it hi
        movhi r1,#63
        cmp r1,#10
        beq line_break
        cmp r7,#44
        blo ordinary
        cmp r1,#32
        beq line_break
        cmp r7,#50
        blo ordinary
        cmp r1,#0x80
        blo wrap
        cmp r1,#0xc0
        blo ordinary
    wrap:
        movs r2,#10
        strb r2,[r10],#1
        movs r7,#0
        cmp r10,r11
        bhs appended
    ordinary:
        cmp r1,#0x31
        bne store_byte
        sub.w r2,r11,r10
        cmp r2,#3
        blo appended
        movs r2,#0xef
        strb r2,[r10],#1
        movs r2,#0xbc
        strb r2,[r10],#1
        movs r1,#0x91
    store_byte:
        strb r1,[r10],#1
        adds r7,#1
        b next_byte
    line_break:
        movs r1,#10
        strb r1,[r10],#1
        movs r7,#0
        b next_byte
    appended:
        bx lr
    .align 2
    '''
    source+=literal('header',f'Vita diagnostic {version}\n'.encode())
    source+=literal('newline',b'\n')
    source+=literal('fallback',b'No string error object')
    return A.asm(source,address)


def candidate(version=VERSION):
    old=(BASE/'components/eboot.bin').read_bytes()
    V.need(sha256(old)==BASE_SHA,'Sealed 0.1.1 executable changed')
    original=(V.WORK/'executables/segment-0.bin').read_bytes()
    info=S.parse(old)
    segments={i:old[s[0]:s[0]+s[1]] for i,s in enumerate(info['infos'])}
    plan=json.loads((V.WORK/'arm_candidate_v2/plan.json').read_text('utf8'))
    address=(A.TEXT_END+plan['code_bytes']+15)&~15
    hook=code(address,version)
    V.need(address+len(hook)<A.WORDS,'Diagnostic exceeds unused native text gap')
    text=bytearray(segments[0]);at=SITE-A.TEXT_BASE;cave=address-A.TEXT_BASE
    V.need(text[at:at+4]==original[at:at+4]==A.asm('adds.w r4,r5,#0x198',SITE),
           'Native error-handler entry differs')
    V.need(not any(text[cave:cave+len(hook)]),'Diagnostic cave is occupied')
    text[at:at+4]=A.asm(f'b.w {address}',SITE)
    text[cave:cave+len(hook)]=hook
    for site,(before,after) in PAINT.items():
        off=site-A.TEXT_BASE;old_bytes=A.asm(before,site);new_bytes=A.asm(after,site)
        V.need(len(old_bytes)==len(new_bytes) and text[off:off+len(old_bytes)]==original[off:off+len(old_bytes)]==old_bytes,
               'Native error-label paint site differs')
        text[off:off+len(old_bytes)]=new_bytes
    restored=bytearray(text);restored[at:at+4]=segments[0][at:at+4]
    restored[cave:cave+len(hook)]=segments[0][cave:cave+len(hook)]
    for site,(before,_) in PAINT.items():
        off=site-A.TEXT_BASE;size=len(A.asm(before,site))
        restored[off:off+size]=segments[0][off:off+size]
    V.need(restored==segments[0],'Unrelated executable code changed')
    segments[0]=bytes(text)
    result=S.make_fself(info,segments)
    readback=S.parse(result)
    for i,s in enumerate(readback['infos']):
        V.need(result[s[0]:s[0]+s[1]]==segments[i],'SELF segment readback differs')
    restored_file=bytearray(result)
    text_off,text_size,_,_=readback['infos'][0]
    old_off,old_size,_,_=info['infos'][0]
    V.need((text_off,text_size)==(old_off,old_size),'Diagnostic changed SELF text extent')
    restored_file[text_off:text_off+text_size]=old[old_off:old_off+old_size]
    V.need(restored_file==old,'Diagnostic changed SELF metadata, auth or unrelated file bytes')
    audit=dict(schema=1,title_id=V.TITLE,version=version,base_version='0.1.1',
               diagnostic_only=True,fix_claimed=False,base_sha256=BASE_SHA,
               output_sha256=sha256(result),entry=SITE,continuation=CONTINUE,
               cave=address,code_bytes=len(hook),buffer_bytes=256,max_message_bytes=254,
               paint_sites={hex(k):v for k,v in PAINT.items()},logical_x=32,font_pixels=24,max_line_cells=50,
               non_ascii_error_bytes='shown as ? to keep diagnostic valid for the UTF-8 drawer',
               ascii_one_escaped_as_fullwidth_utf8=True,
               original_error_lockout_preserved=True,permissions_and_relocations_unchanged=True,
               unrelated_segments_preserved=True,base_arm=plan)
    return result,audit


def verify(raw,audit):
    from tools.vita_arm_check import Machine,REGS
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_R5,
        UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_CPSR,UC_ARM_REG_S0,UC_ARM_REG_S1,UC_ARM_REG_S2)
    cases=0
    for text_shift,data_shift in ((0,0),(0x10000,0x50000)):
        m=Machine(raw,audit['base_arm'],text_shift,data_shift);u=m.u
        obj,state,top,string,callback=0x90002000,0x90003000,0x90004010,0x90005000,0x90007000
        # Every changed instruction is PC relative, including all ADR literals.
        for error in (b"attempt to call global 'SC_TEST' (a nil value)",
                      b'not enough memory',b'',b'x'*4096,b'error: \xe3\x81\x82\tend\r\n',
                      b'[string "stage"]:42: '+b'long error '*120):
            for kind in (4,0):
                u.mem_write(obj,bytes(0x300));u.mem_write(obj+4,struct.pack('<I',state))
                u.mem_write(obj+0x198,b'!'*256+b'GUARD')
                u.mem_write(state+8,struct.pack('<I',top))
                u.mem_write(top-16,struct.pack('<4I',string,0,kind,0))
                u.mem_write(string,bytes(12)+struct.pack('<I',len(error))+error+b'\0')
                u.mem_write(callback,b'EventCheck_BtlAfter\0')
                for i,r in enumerate(REGS):
                    if i!=14:u.reg_write(r,0x12345000+i*4)
                u.reg_write(UC_ARM_REG_R4,callback);u.reg_write(UC_ARM_REG_R5,obj)
                u.reg_write(UC_ARM_REG_CPSR,0xA8000030)
                before=[u.reg_read(r) for r in REGS]
                fp=[u.reg_read(UC_ARM_REG_S0+i) for i in range(32)]
                u.emu_start((SITE+text_shift)|1,CONTINUE+text_shift,count=200000)
                V.need(u.reg_read(UC_ARM_REG_PC)==CONTINUE+text_shift,'Diagnostic did not return')
                message=bytes(u.mem_read(obj+0x198,261))
                V.need(message.endswith(b'GUARD') and message[254:256]==b'\0\0',
                       'Diagnostic error label guard differs: '+repr(message))
                text=message.split(b'\0')[0]
                V.need(text.startswith(f'Vita diagnostic {audit["version"]}\nEventCheck_BtlAfter\n'.encode().replace(b'1',b'\xef\xbc\x91')),'Missing diagnostic identity/callback')
                V.need(max(map(len,text.decode('utf8').split('\n')))<=50,'Diagnostic exceeds native line budget')
                V.need(b'1' not in text,'ASCII one would become a native color command')
                V.need((b'No string error object' in text)==(kind!=4),'Error object type handling differs')
                if kind==4 and len(error)<100:
                    printable=bytes(x if x<=126 else 63 for x in error).replace(b'\t',b' ').replace(b'\r',b'')
                    printable=printable.replace(b'1',b'\xef\xbc\x91')
                    V.need(text.replace(b'\n',b' ').endswith(printable.replace(b'\n',b' ')),'Underlying Lua error differs')
                for i,r in enumerate(REGS):
                    wanted={0:obj+0x198,4:obj+0x198,6:0}.get(i,before[i])
                    V.need(u.reg_read(r)==wanted,'Diagnostic changed live register '+str(i))
                V.need(u.reg_read(UC_ARM_REG_CPSR)&0xF8000000==0xA8000000,'Diagnostic changed live flags')
                V.need(fp==[u.reg_read(UC_ARM_REG_S0+i) for i in range(32)],'Diagnostic changed floating registers')
                cases+=1
        # Execute both actual native error-paint callers. Intercept only the
        # shared font setup/drawer to inspect the real incoming coordinates.
        from tools.vita_arm_check import number
        painted=[];font=[]
        def calls(uc,pc,size,unused):
            if pc==0x81110ad8+text_shift:
                font.append(uc.reg_read(UC_ARM_REG_R0))
                uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
            elif pc==0x8100eac0+text_shift:
                painted.append((uc.reg_read(UC_ARM_REG_R0),number(uc.reg_read(UC_ARM_REG_S0)),
                                number(uc.reg_read(UC_ARM_REG_S1)),number(uc.reg_read(UC_ARM_REG_S2))))
                uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        hook=u.hook_add(UC_HOOK_CODE,calls)
        for entry in (0x811033ce,0x81103400):
            u.mem_write(obj+0x298,b'\1');u.reg_write(UC_ARM_REG_R0,obj)
            u.reg_write(UC_ARM_REG_LR,0x90000001)
            u.emu_start((entry+text_shift)|1,0x90000000,count=1000)
            V.need(font[-1]==24 and painted[-1]==(obj+0x198,32.0,10.0,1.0),'Native diagnostic paint geometry differs')
            cases+=1
        u.hook_del(hook)
    return dict(native_execution_cases=cases,independent_text_data_shifts=True,
                buffer_guards_verified=True,live_registers_verified=True,native_paint_callers_executed=True,
                actual_physical_console_tested=False,actual_error_reproduced=False)


def run(apply=False):
    raw,audit=candidate();audit.update(verify(raw,audit))
    from tools.vita_diagnostic_draw_check import verify as verify_draw
    audit.update(verify_draw(raw,audit))
    print(json.dumps({k:v for k,v in audit.items() if k!='base_arm'},indent=2),flush=True)
    if not apply:
        print('DRY RUN: no diagnostic delivery written.');return audit
    V.need(not OUTPUT.exists(),'Preserve an existing diagnostic build')
    OUTPUT.mkdir(parents=True)
    eboot=OUTPUT/'eboot.bin';eboot.write_bytes(raw)
    original=V.PLAIN/'eboot.bin'
    delta=OUTPUT/f'VITA-PCSG00494-{VERSION}-diagnostic-eboot.xdelta'
    V.need(sha256_file(R.XD)==R.XD_SHA,'Patch engine changed')
    subprocess.run([str(R.XD),'-e','-s',str(original),str(eboot),str(delta)],check=True)
    with tempfile.TemporaryDirectory(prefix='check-',dir=OUTPUT) as temp:
        decoded=Path(temp)/'eboot.bin'
        subprocess.run([str(R.XD),'-d','-s',str(original),str(delta),str(decoded)],check=True)
        V.need(sha256_file(decoded)==audit['output_sha256'],'Diagnostic delta roundtrip differs')
    profile=json.loads((ROOT/'work/output/vita/releases/0.1.1/VITA-REPATCH.json').read_text('utf8'))
    profile=copy.deepcopy(profile)
    profile.update(build=VERSION,name='SRW Z3 Tengoku-hen - HARDWARE DIAGNOSTIC (not a fix)')
    patches=[]
    for row in profile['files']:
        if row['path']=='eboot.bin':
            V.need(row['target']['sha256']==BASE_SHA,'Hardware baseline differs')
            row.update(target=R.B.describe(eboot),patch=dict(name=delta.name,**R.B.describe(delta)))
            patches.append(delta)
        else:
            patch=ROOT/'work/output/vita/releases/0.1.1'/row['patch']['name']
            V.need(R.B.describe(patch)=={k:row['patch'][k] for k in ('bytes','sha256')},'Sealed base patch differs')
            patches.append(patch)
    R.hardware.validate(profile)
    manifest=OUTPUT/R.hardware.MANIFEST;write_json(manifest,profile)
    archive=OUTPUT/f'SRW-Z3-Tengoku-v{VERSION}-Vita-rePatch-DIAGNOSTIC-patches.zip'
    R.seal_zip(archive,R.hardware.MANIFEST,profile,patches)
    with R.hardware.archive_description(archive) as (readback,_,__):
        V.need(readback==profile,'Diagnostic Retro Trans archive differs')
    guide=(
        f'Tengoku-hen physical Vita diagnostic {VERSION}\n\n'
        'DIAGNOSTIC ONLY: this does not fix the freeze or change the error lockout.\n'
        'Use with the English 0.1.1 rePatch overlay for PCSG00494 v01.00.\n'
        'Close the game. Keep a backup of ux0:/rePatch/PCSG00494/eboot.bin.\n'
        'Copy rePatch/PCSG00494/eboot.bin from this update over that one file.\n'
        'Keep all other 0.1.1 overlay files. Start normally and repeat the first battle.\n'
        f'If the freeze occurs, photograph every line beginning Vita diagnostic {VERSION}.\n'
        'This corrects the 0.1.2 diagnostic text truncation. It can replace that diagnostic directly.\n'
        'Non-ASCII error bytes appear as ?; the Lua error and callback names normally use ASCII.\n'
        'The title artwork still says 0.1.1; only the failure message identifies this diagnostic.\n'
        'Restore the backed-up 0.1.1 eboot.bin to remove the diagnostic. Saves are unchanged.\n\n'
        'Retro Trans alternative: use the DIAGNOSTIC-patches.zip with the original\n'
        'PCSG00494 v01.00 PKG and matching work.bin; choose physical-Vita rePatch.\n'
        'That archive reconstructs the complete 0.1.1 overlay plus this diagnostic.\n'
        'Do not install it into Vita3K as a PKG. No physical-console success is claimed.\n')
    (OUTPUT/'README.txt').write_text(guide,encoding='utf8')
    update=OUTPUT/f'Tengoku-hen-{VERSION}-physical-Vita-DIAGNOSTIC-update.zip'
    with zipfile.ZipFile(update,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('README.txt',guide)
        z.writestr('rePatch/PCSG00494/eboot.bin',raw)
    with zipfile.ZipFile(update) as z:
        V.need(z.testzip() is None and sha256(z.read('rePatch/PCSG00494/eboot.bin'))==audit['output_sha256'],
               'Diagnostic update ZIP differs')
    audit.update(retro_trans_archive_verified=True,original_eboot_delta_roundtrip=True,
                 update_zip_verified=True,artifacts={p.name:R.B.describe(p) for p in (archive,update,delta,manifest,eboot)})
    write_json(OUTPUT/'audit.json',audit)
    (OUTPUT/'SHA256SUMS.txt').write_text(''.join(f'{sha256_file(p)}  {p.name}\n' for p in (archive,update,delta,manifest,eboot)),encoding='ascii')
    print('Prepared hardware diagnostic:',update,flush=True)
    return audit


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true')
    run(p.parse_args().apply)


if __name__=='__main__':main()
