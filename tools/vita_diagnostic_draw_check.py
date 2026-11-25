"""Run the real native UTF-8 converter and glyph loop for hardware diagnostics.

Only the platform UTF-8-to-UTF-16 library and GPU submission helpers are
stubbed. Native conversion tables, color/control parsing, glyph selection,
line positioning and all installed translation hooks execute unchanged.
"""
import struct
from tools import vita
from tools import vita_source as V
from tools.vita_arm_check import Machine, bits, number
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *


def read_string(u,at,cap=8192):
    out=bytearray()
    for i in range(cap):
        b=bytes(u.mem_read(at+i,1))
        if b==b'\0':return bytes(out)
        out+=b
    raise ValueError('Native diagnostic string exceeds bounded extent')


def verify(raw,audit):
    machine=Machine(raw,audit['base_arm']);u=machine.u
    source=0x9000c000;converted=0x81512730;font=0x815126b8
    glyphs=[]
    gpu={0x81012350,0x81012106,0x8101235c,0x81016476,
         0x810121e6,0x8101225e,0x81012224,0x81011a08}
    def calls(uc,pc,size,unused):
        if pc==0x81323a94:
            # This is the platform multibyte-to-wide import. Preserve the
            # game's native converter itself, including its special '1'.
            dest=uc.reg_read(UC_ARM_REG_R0);src=uc.reg_read(UC_ARM_REG_R1)
            text=read_string(uc,src).decode('utf8')
            if dest:uc.mem_write(dest,text.encode('utf-16le')+b'\0\0')
            uc.reg_write(UC_ARM_REG_R0,len(text))
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        elif pc in gpu:
            if pc==0x810121e6:uc.reg_write(UC_ARM_REG_R0,0x9000a000)
            elif pc==0x81012224:
                glyphs.append(dict(index=uc.reg_read(UC_ARM_REG_R9),
                    x=number(uc.reg_read(UC_ARM_REG_S0)),y=number(uc.reg_read(UC_ARM_REG_S1)),
                    color=struct.unpack('<I',uc.mem_read(0x9000a014,4))[0]))
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    handle=u.hook_add(UC_HOOK_CODE,calls)
    def convert(text):
        u.mem_write(source,text+b'\0');u.reg_write(UC_ARM_REG_R0,source)
        u.reg_write(UC_ARM_REG_LR,0x90000001)
        u.emu_start(0x8100e9b1,0x90000000,count=100000)
        return read_string(u,converted)
    # Reproduce the actual 0.1.2 bug: ASCII 1 followed by '.' emits a color
    # operation whose operand is '.'-1 = 45, rather than a digit glyph.
    old=convert(b'Vita diagnostic 0.1.2\nEventCheck_BtlAfter\nerror line 1')
    V.need(b'\x31\x2d' in old,'Did not reproduce 0.1.2 native color-command bug')
    def draw(message):
        u.mem_write(source,message+b'\0')
        u.mem_write(font,bytes(0x78))
        for off in (0x14,0x18,0x1c,0x20):u.mem_write(font+off,struct.pack('<f',24))
        for off in (0x60,0x64):u.mem_write(font+off,struct.pack('<I',0xffffffff))
        u.mem_write(font+0x68,struct.pack('<I',3))
        u.reg_write(UC_ARM_REG_R0,source);u.reg_write(UC_ARM_REG_R1,0)
        u.reg_write(UC_ARM_REG_S0,bits(32));u.reg_write(UC_ARM_REG_S1,bits(10))
        u.reg_write(UC_ARM_REG_S2,bits(1));u.reg_write(UC_ARM_REG_LR,0x90000001)
        glyphs.clear()
        u.emu_start(0x8100eac1,0x90000000,count=500000)
        V.need(u.reg_read(UC_ARM_REG_PC)==0x90000000,'Native drawer did not reach its normal return')
        return list(glyphs)
    old_glyphs=draw(b'Vita diagnostic 0.1.2\nEventCheck_BtlAfter\nerror line 1')
    prefix=len('Vita diagnostic 0.')
    V.need(all(g['color']==0xffffffff for g in old_glyphs[:prefix]) and
           all(g['color']>>24==0 for g in old_glyphs[prefix:]),
           'Did not reproduce the tester photo: opaque prefix then transparent remaining glyphs')
    # Obtain messages by running the new error handler, not a host-side
    # facsimile of its escaping/formatting.
    obj,state,top,string,callback=0x90002000,0x90003000,0x90004010,0x90005000,0x90007000
    samples=[]
    errors=(b"[string \"stage\"]:11: attempt to call global 'SC_TEST1' (a nil value)",
            b'not enough memory',b'long 1 error '*70)
    for error in errors:
        u.mem_write(obj,bytes(0x300));u.mem_write(obj+4,struct.pack('<I',state))
        u.mem_write(state+8,struct.pack('<I',top))
        u.mem_write(top-16,struct.pack('<4I',string,0,4,0))
        u.mem_write(string,bytes(12)+struct.pack('<I',len(error))+error+b'\0')
        u.mem_write(callback,b'EventCheck_BtlAfter\0')
        u.reg_write(UC_ARM_REG_R4,callback);u.reg_write(UC_ARM_REG_R5,obj)
        u.emu_start(audit['entry']|1,audit['continuation'],count=100000)
        message=read_string(u,obj+0x198)
        native=convert(message)
        # Only newline is one byte in this safe native stream. All other
        # characters must map to the original two-byte glyph, never controls.
        expected=bytearray()
        decoded=message.decode('utf8')
        for char in decoded:
            if char=='\n':expected+=b'\n'
            else:
                table=(0x8139c710 if ord(char)<128 else 0x8137c710)
                expected+=bytes(u.mem_read(table+ord(char)*2,2))
        V.need(native==bytes(expected),'Native conversion lost or reinterpreted diagnostic text')
        glyphs[:]=draw(message)
        V.need(len(glyphs)==len(decoded.replace('\n','')),'Native drawer dropped diagnostic glyphs')
        V.need(all(g['color']==0xffffffff and 32<=g['x']<=1232 and 10<=g['y']<400 for g in glyphs),
               'Native diagnostic glyphs are transparent or offscreen')
        V.need(len({g['y'] for g in glyphs})==len([line for line in decoded.split('\n') if line]),
               'Native drawer lost diagnostic lines')
        samples.append(dict(utf8_message=decoded,native_bytes_hex=native.hex(),glyph_count=len(glyphs),
                            lines=len(set(g['y'] for g in glyphs)),all_opaque_and_onscreen=True))
    u.hook_del(handle)
    return dict(native_utf8_converter_executed=True,native_glyph_loop_executed=True,
                diagnostic_0_1_2_color_command_reproduced=True,draw_cases=len(samples),draw_samples=samples,
                diagnostic_0_1_2_transparent_suffix_reproduced=True,
                graphics_submission_stubbed=True,physical_console_tested=False)
