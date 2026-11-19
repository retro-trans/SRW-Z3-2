"""PCSG00494-native Thumb hooks; no installation or publication.

Guard the inspected Tengoku instruction sites, preserve incoming LR with
B.W trampolines (the keyword callback carries a live row in LR), and append
only relative SCE pointer relocations. Never use PS3 machine instructions.
"""
import argparse
import copy
import json
import struct
from tools.common import ROOT, sha256, write_json
from tools import vita_source as V, vita_elf as E, ui_hook as H
from tools.vita import self_decrypt as S
from tools.vita.font_gxt import index_for_code
from tools.vita_assets import voice
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_LITTLE_ENDIAN

SOURCE_SHA='1afa15e315e28b8c384f834c4069f286a59d42cf144e44de2a0b83ce23792fd7'
TEXT_BASE=0x81000000
TEXT_END=TEXT_BASE+4408004
TEXT_LIMIT=0x81435000
WORDS=TEXT_LIMIT-16
# The native ASSF canvas is 1280x720; the Vita framebuffer scales it to
# 960x544. Font drawer coordinates remain in the declared logical canvas.
CANVAS_CENTER=640
SITES={
    'draw':(0x8100eb00,'vmov.f32 s0, #-1.0'),
    'advance':(0x8100ef3a,'vadd.f32 s18,s18,s21'),
    'description':(0x81149968,'adds r0,r2,#0; str r1,[sp,#0x18]'),
    'piece_end':(0x81149aa4,'add.w r9,r9,r0,asr #1'),
    'normal':(0x81149e1e,'mla r1,r3,r4,r1'),
    'mode1':(0x81149f30,'mla r1,r3,r4,r1'),
    'keyword':(0x8114a0d8,'mla r2,r3,r7,r2'),
    'substitution':(0x8114a4ea,'mla r1,r5,r10,r8'),
    'center':(0x8100f642,'vmul.f32 s0,s0,s1'),
}


def asm(text,address):
    data,_=Ks(KS_ARCH_ARM,KS_MODE_THUMB|KS_MODE_LITTLE_ENDIAN).asm(text,address)
    V.need(data is not None,'Thumb assembly failed')
    return bytes(data)


def parent_rows():
    build=json.loads((ROOT/'work/output/builds/0.5.51/build.json').read_text('utf8'))
    elf=(ROOT/'work/output/builds/0.5.51/EBOOT.BIN').read_bytes()
    ph=H._headers(elf)[2];read=H._reader(elf,ph)
    source=H.slot_map(read);rows={}
    for key,pointer in source.items():
        n=min(H.MAX_ENGLISH_EXTENT+2,ph[1][3]+ph[1][5]-pointer)
        raw=read(pointer,n);end=H.extent(raw,cap=H.MAX_ENGLISH_EXTENT)
        V.need(end is not None,'Unterminated certified English')
        rows[key]=raw[:end]
    # Centering receives UTF-8 before the drawer's conversion. Add complete
    # decoded source aliases only; no prefix, fuzzy, or substring lookup.
    for key,value in list(rows.items()):
        if b'\0' in key:continue
        try:text=key.decode('cp932')
        except UnicodeDecodeError:continue
        alias=text.encode('utf8')
        if alias!=key and alias not in rows:rows[alias]=value
    widths=bytearray([32]*4480)
    for token,code in build['mapping'].items():
        width=build['widths'][token]
        V.need(1<=width<=32,'Invalid parent glyph metric')
        widths[index_for_code(int(code,16))]=width
    return rows,bytes(widths),build['mapping']


def table(rows):
    count=1
    while count<len(rows)*2:count*=2
    blob=bytearray(8+16*count);struct.pack_into('<II',blob,0,count-1,8)
    occupied=set()
    for key,value in sorted(rows.items()):
        V.need(key and len(key)<65536 and len(value)<65536,'Invalid table extent')
        h=H.fnv1a(key);slot=h&(count-1)
        while slot in occupied:slot=(slot+1)&(count-1)
        occupied.add(slot);kp=len(blob);blob+=key+b'\0';vp=len(blob);blob+=value+b'\0'
        struct.pack_into('<IIIHH',blob,8+slot*16,h,kp,vp,len(key),len(value))
    return bytes(blob)


def code(mapping):
    blob=bytearray();entries={}
    def emit(name,text):
        while (TEXT_END+len(blob))%4:blob.extend(b'\0')
        at=TEXT_END+len(blob);entries[name]=at;blob.extend(asm(text,at));return at
    # r0=input, r1=1 UTF-8/C string or 0 native SJIS/control tokens;
    # output r0 is exact replacement or unchanged input. Internal NUL operands
    # (notably the color close) are included in the length and hash.
    lookup=emit('lookup',f'''
        push.w {{r1-r11,r12,lr}}
        mov r7,r0
        mov r6,r1
        mov r3,r0
        movs r5,#0
        movw r4,#0x9dc5
        movt r4,#0x811c
        movw r8,#0x0193
        movt r8,#0x0100
    hash_loop:
        ldrb r2,[r3],#1
        cmp r2,#0
        beq hashed
        eor.w r4,r4,r2
        mul r4,r4,r8
        adds r5,#1
        cmp r6,#0
        bne hash_loop
        cmp r2,#10
        beq hash_loop
        cmp r2,#0x2e
        beq hash_loop
        cmp r2,#0x2f
        beq hashed
        ldrb r2,[r3],#1
        eor.w r4,r4,r2
        mul r4,r4,r8
        adds r5,#1
        b hash_loop
    hashed:
        adr.w r0,#{WORDS}
        ldr r1,[r0]
        add r0,r1
        ldr r8,[r0]
        ldr r9,[r0,#4]
        add r9,r0
        and.w r6,r4,r8
    slot:
        add.w r10,r9,r6,lsl #4
        ldr r1,[r10,#4]
        cmp r1,#0
        beq original
        ldr r2,[r10]
        cmp r2,r4
        bne next_slot
        ldrh r2,[r10,#12]
        cmp r2,r5
        bne next_slot
        add r1,r0
        mov r2,r7
        mov r3,r5
    compare:
        cmp r3,#0
        beq found
        ldrb r11,[r1],#1
        ldrb r12,[r2],#1
        cmp r11,r12
        bne next_slot
        subs r3,#1
        b compare
    found:
        ldr r1,[r10,#8]
        add r0,r1
        b finished
    next_slot:
        adds r6,#1
        and.w r6,r6,r8
        b slot
    original:
        mov r0,r7
    finished:
        pop.w {{r1-r11,r12,pc}}
    ''')
    pointer=emit('scratch',f'adr.w r0,#{WORDS+4}; ldr r1,[r0]; add r0,r1; bx lr')
    scene=int.from_bytes(bytes.fromhex(mapping['@scene-center']),'little')
    headline=int.from_bytes(bytes.fromhex(mapping['@headline-center']),'little')
    measure=emit('measure',f'''
        push.w {{r2-r8,lr}}
        mov r2,r0
        ldrh r3,[r2]
        movw r8,#{scene}
        cmp r3,r8
        beq skip_marker
        movw r8,#{headline}
        cmp r3,r8
        bne measure_begin
    skip_marker:
        adds r2,#2
    measure_begin:
        adr.w r6,#{WORDS+4}
        ldr r3,[r6]
        add r6,r3
        adds r6,#4
        movs r4,#0
        movs r5,#0
        movs r7,#0
    measure_loop:
        ldrb r3,[r2],#1
        cmp r3,#0
        beq measure_done
        cmp r3,#0x2f
        beq measure_done
        cmp r3,#10
        beq measure_line
        cmp r3,#13
        beq measure_loop
        cmp r3,#0x2e
        beq measure_loop
        cmp r3,#0x30
        blo glyph
        cmp r3,#0x39
        bhi glyph
        adds r2,#1
        b measure_loop
    glyph:
        ldrb r8,[r2],#1
        subs r3,#0x81
        movs r0,#192
        mul r3,r3,r0
        add r3,r8
        subs r3,#64
        movw r0,#4480
        cmp r3,r0
        bhs wide_glyph
        ldrb r3,[r6,r3]
        cmp r3,#32
        bhs glyph_add
        movs r5,#1
        b glyph_add
    wide_glyph:
        movs r3,#32
    glyph_add:
        add r4,r3
        b measure_loop
    measure_line:
        cmp r4,r7
        it hi
        movhi r7,r4
        movs r4,#0
        b measure_loop
    measure_done:
        cmp r4,r7
        it hi
        movhi r7,r4
        mov r0,r7
        mov r1,r5
        pop.w {{r2-r8,pc}}
    ''')
    # Hook wrappers preserve every GPR, flag and incoming LR except their
    # declared result. Explicit branches preserve callbacks' live LR values.
    save='push.w {r0-r12,lr}; mrs r0,apsr; push {r0}; '
    restore='pop {r0}; msr apsr_nzcvq,r0; pop.w {r0-r12,lr}; '
    # Save the translated r7 in its stack slot before restoring GPRs.
    emit('draw',save+f'''
        vpush {{s0-s3}}
        mov r0,r7; movs r1,#0; bl {lookup}
        mov r7,r0; str r7,[sp,#48]
        ldrh r1,[r7]
        movw r2,#{scene}; cmp r1,r2; beq scene_origin
        movw r2,#{headline}; cmp r1,r2; bne draw_done
        movs r6,#1; b marked_origin
    scene_origin:
        movs r6,#0
    marked_origin:
        adds r7,#2; str r7,[sp,#48]
        mov r0,r7; bl {measure}
        vmov s0,r0; vcvt.f32.u32 s0,s0,#5
        vldr s1,[r5,#0x14]; vmul.f32 s0,s0,s1
        vmov.f32 s1,#0.5; vmul.f32 s0,s0,s1
        movw r0,#0; movt r0,#0x4420; vmov s1,r0
        vsub.f32 s18,s1,s0
        cmp r6,#0; beq draw_done
        vldr s0,[r5,#0x18]; vmov.f32 s1,#0.5
        vmul.f32 s0,s0,s1; vsub.f32 s17,s17,s0
    draw_done:
        vpop {{s0-s3}}
        '''+restore+f'vmov.f32 s0,#-1.0; b.w {SITES["draw"][0]+4}')
    emit('description',save+f'''mov r0,r2; cmp r0,#0; beq desc_done;
        movs r1,#0; bl {lookup};
    desc_done:
        str r0,[sp,#4]; '''+restore+f'''adds r0,r0,#0; str r1,[sp,#0x18];
        b.w {SITES["description"][0]+4}''')
    # Runtime glyph advance and MtV piece cursor share one new float.
    emit('advance',save+f'''
        vpush {{s0-s1}}
        vmov.f32 s0,s21
        movw r0,#4480
        cmp r9,r0
        bhs advance_old
        bl {pointer}
        adds r0,#4
        ldrb r0,[r0,r9]
        cmp r0,#32
        beq advance_old
        vmov s0,r0
        vcvt.f32.u32 s0,s0,#5
        vmul.f32 s0,s0,s19
    advance_old:
        vadd.f32 s18,s18,s0
        bl {pointer}
        vldr s1,[r0]
        vadd.f32 s1,s1,s0
        vstr s1,[r0]
        vpop {{s0-s1}}
        '''+restore+f'b.w {SITES["advance"][0]+4}')
    for name,target,base,column in (('normal','r1','r1','r3'),('mode1','r1','r1','r3'),
             ('keyword','r2','r2','r3'),('substitution','r1','r8','r10')):
        emit(name,f'add.w {target},{base},{column},asr #7; '+save+
             f'bl {pointer}; movs r1,#0; str r1,[r0]; '+restore+f'b.w {SITES[name][0]+4}')
    emit('piece_end',save+f'''
        vpush {{s0}}
        bl {pointer}
        vldr s0,[r0]
        vcvt.s32.f32 s0,s0,#7
        vmov r0,s0
        add r9,r0
        str r9,[sp,#44]
        vpop {{s0}}
        '''+restore+f'b.w {SITES["piece_end"][0]+4}')
    emit('center',save+f'''
        vpush {{s0-s3}}
        mov r0,r6
        cmp r5,#0
        ite eq
        moveq r1,#1
        movne r1,#0
        bl {lookup}
        cmp r0,r6
        bne center_measure
        cmp r5,#0
        beq center_old
    center_measure:
        bl {measure}
        cmp r1,#0
        beq center_old
        vmov s0,r0; vcvt.f32.u32 s0,s0,#5
        ldr r0,[sp,#20]
        vldr s1,[r0,#0x14]
        vmul.f32 s0,s0,s1
        b center_done
    center_old:
        vldr s0,[sp]; vldr s1,[sp,#4]
        vmul.f32 s0,s0,s1
    center_done:
        vstr s0,[sp]
        vpop {{s0-s3}}
        '''+restore+f'b.w {SITES["center"][0]+4}')
    V.need(TEXT_END+len(blob)<WORDS,'Thumb hooks exceed original text/data gap')
    return bytes(blob),entries


def plan():
    original=(E.OUTPUT/'eboot-original-plain.self').read_bytes()
    V.need(sha256(original)==SOURCE_SHA,'Unknown Tengoku Vita baseline')
    info=S.parse(original);p0,p1=info['phdrs'][:2]
    V.need(p0[2]+p0[4]==TEXT_END and p1[2]==TEXT_LIMIT,'Unexpected native memory layout')
    segs={i:original[s[0]:s[0]+s[1]] for i,s in enumerate(info['infos'])}
    rows,widths,mapping=parent_rows();dictionary=table(rows)
    native,entries=code(mapping);text=bytearray(segs[0])+bytearray(TEXT_LIMIT-TEXT_END)
    text[TEXT_END-TEXT_BASE:TEXT_END-TEXT_BASE+len(native)]=native
    sites=[]
    for name,(address,instruction) in SITES.items():
        if name not in entries:continue
        at=address-TEXT_BASE;old=asm(instruction,address);branch=asm(f'b.w {entries[name]}',address)
        V.need(len(old)==len(branch)==4 and text[at:at+4]==old,'Native instruction differs: '+name)
        text[at:at+4]=branch
        sites.append(dict(name=name,address=address,original_hex=old.hex(),patched_hex=branch.hex()))
    scratch=(p1[2]+p1[5]+15)&~15
    voice_data,voice_report=voice(segs[1])
    data=bytearray(voice_data);data+=bytes(scratch-p1[2]-len(data))+bytes(4)+widths
    while len(data)%16:data.append(0)
    target=p1[2]+len(data);data+=dictionary
    reloc=bytearray()
    for word,location in ((WORDS,target),(WORDS+4,scratch)):
        struct.pack_into('<I',text,word-TEXT_BASE,(location-word)&0xffffffff)
        reloc+=struct.pack('<III',0x310,location-p1[2],word-TEXT_BASE)
    V.need(info['phdrs'][3][0]==0x60000000,'Unexpected relocation segment')
    segs[0]=bytes(text);segs[1]=bytes(data);segs[3]+=reloc
    updated=copy.deepcopy(info);headers=[list(p) for p in info['phdrs']]
    for i in (0,1):headers[i][4]=headers[i][5]=len(segs[i])
    headers[3][4]=len(segs[3]);cursor=52+32*len(headers)
    for i in sorted(range(len(headers)),key=lambda i:info['phdrs'][i][1]):
        align=max(16,headers[i][7]);cursor=(cursor+align-1)&-align
        headers[i][1]=cursor;cursor+=len(segs[i])
    updated['phdrs']=[tuple(p) for p in headers];updated['elen']=cursor
    result=S.make_fself(updated,segs)
    restored=bytearray(text[:p0[4]])
    for row in sites:
        at=row['address']-TEXT_BASE;restored[at:at+4]=bytes.fromhex(row['original_hex'])
    V.need(restored==original[info['infos'][0][0]:info['infos'][0][0]+p0[4]],'Unrelated ARM code changed')
    restored_data=bytearray(data[:p1[4]]);at=voice_report['data_offset'];size=voice_report['table_bytes']
    data_origin=info['infos'][1][0]
    restored_data[at:at+size]=original[data_origin+at:data_origin+at+size]
    V.need(restored_data==original[info['infos'][1][0]:info['infos'][1][0]+p1[4]],'Unrelated original data changed')
    report=dict(schema=1,title_id=V.TITLE,source_sha256=SOURCE_SHA,output_sha256=sha256(result),
        sites=sites,code_bytes=len(native),entries=entries,table_entries=len(rows),table_bytes=len(dictionary),
        width_cells=4480,translated_font_cells=len(mapping),scratch_va=scratch,table_va=target,
        text_pointer_words=WORDS, added_relocations_hex=reloc.hex(),
        original_code_and_unrelated_data_preserved=True, voice_table=voice_report,original_relocations_preserved=True,
        arm_execution_verified=False,center_hook_pending=False,runtime_verified=False)
    return result,report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result,report=plan()
    print('Native ARM hooks:',len(report['sites']),'; code bytes:',report['code_bytes'],'; table entries:',report['table_entries'])
    print('Pending: independent ARM execution verification; not a ready game build.')
    if a.apply:
        folder=V.WORK/'arm_candidate_v2';V.need(not folder.exists(),'Preserve existing candidate');folder.mkdir()
        (folder/'eboot.bin').write_bytes(result);write_json(folder/'plan.json',report)
    else:print('DRY RUN: no executable written.')


if __name__=='__main__':main()
