"""Bounded native PPC controls for simultaneous missing speech/ellipsis captions.

Runs in local interpreter memory only. No game files or installed data change.
The audio engine, C string helpers, speaker lookup and upstream rule choice are
modeled boundaries; this is not a physical-console reproduction.
"""
import struct
from tools import srvc as S, cfw_self as C, ppc_exec as P


def readback(elf, data, original_elf):
    table=S.read_table(elf,len(data))
    original_table=S.read_table(original_elf)
    ranges=((S.START_READ_VA,0x1390fc),(S.PARSER_VA,0x139238),
            (S.PARTIAL_READ_VA,0x13c1b0),(0x12e4bc,0x12e7e8),(0x12eb28,0x12f000))
    for lo,hi in ranges:
        at,old_at=S.va_to_offset(elf,lo),S.va_to_offset(original_elf,lo)
        if elf[at:at+hi-lo] != original_elf[old_at:old_at+hi-lo]:
            raise ValueError('Native voice control code changed: '+hex(lo))
    blocks=S.parse(data,table)
    candidates=[(b,k) for b in blocks
        if data[original_table[b.i]] != S.VERSION
        for k,(cue,flag) in enumerate(b.cues) if cue&0xffff and flag<256]
    if not candidates:
        raise ValueError('No voiced-bank mismatch control available')
    bank,line=candidates[0]
    cases=[]
    for wrong_table in (False,True):
        memory=P.Memory()
        for kind,flags,off,va,_pa,size,_memsz,_align in C.program_headers(elf)[1]:
            if kind==1 and size:
                memory.map(va,elf[off:off+size],bool(flags&2))
        context,buffer,engine,strings,stack,stop=(0x20000000,0x21000000,
            0x22000000,0x23000000,0x24000000,0x25000000)
        stream=context+0x4000
        chosen_table=original_table if wrong_table else table
        lo,hi=chosen_table[bank.i:bank.i+2]
        memory.map(context,bytes(0x5000))
        memory.map(buffer,bytes(hi-lo))
        memory.map(engine,bytes(0x1000))
        memory.map(strings,bytes(0x1000))
        memory.map(stack,bytes(0x2000))
        def u32(at):
            return int.from_bytes(memory.read(at,4),'big')
        def put32(at,value):
            memory.write(at,struct.pack('>I',value))
        def toc(displacement):
            return u32(S.TOC_BASE+displacement)
        def string(at):
            out=bytearray()
            while len(out)<8192:
                byte=memory.read(at,1)
                if byte==b'\0':
                    return bytes(out)
                out+=byte
                at+=1
            raise ValueError('Unterminated modeled C string')
        def machine(pc,argument=context):
            m=P.Machine(memory)
            m.pc=pc
            m.r[1],m.r[2],m.r[3]=stack+0x1000,S.TOC_BASE,argument
            m.lr=stop
            return m
        def done(m,value=0):
            m.r[3],m.pc=value,m.lr
        if wrong_table:
            memory.write(S.TABLE_VA,S.pack_table(original_table))
        memory.write(stream+0x28,struct.pack('>IH',S.TABLE_VA,bank.i))
        requests=[]
        def read(m):
            if string(m.r[3]) != S.PATH_STRING or m.r[6] != stream:
                raise ValueError('Unexpected native voice read')
            offset,length=m.r[4],m.r[5]
            if (offset,length) != (lo,hi-lo) or hi>len(data):
                raise ValueError('Unexpected native read window')
            requests.append((offset,length))
            memory.write(buffer,data[offset:offset+length])
            done(m)
        m=machine(S.START_READ_VA,stream)
        m.hooks[0x22a84]=read
        m.run({stop},limit=200)
        if len(requests)!=1:
            raise ValueError('Native voice read did not run once')
        header=memory.read(buffer,8).hex()
        m=machine(S.PARSER_VA)
        m.r[4]=buffer
        m.run({stop},limit=200)
        parsed_lines=int.from_bytes(memory.read(buffer+6,2),'little')
        # Supply controlled actor metadata and one deterministic rule result.
        # The invalid-header case takes the native empty-bank branch first.
        put32(context+0x20,strings+0x200)
        put32(context+0xf90,strings+0x400)
        put32(toc(-0x6018),engine)
        memory.write(engine+0x21c,struct.pack('>H',65535))
        put32(toc(-0x6014)+0x88,strings)
        memory.write(strings,b'Test pilot\0')
        memory.write(strings+0x100,struct.pack('<4H',0,1,line,1))
        memory.write(toc(-0x6028)+0x27,b'\1')
        m=machine(0x12eb28)
        m.hooks={0x12e108:lambda m:done(m,strings+0x100),
                 0x126ca8:lambda m:done(m,0)}
        m.run({stop},limit=1500)
        entry_flag=memory.read(context+0x85,1)[0]
        calls=[]
        def play(m):
            calls.append(m.r[4])
            done(m)
        def copy(m):
            destination=m.r[3]
            memory.write(destination,string(m.r[4])+b'\0')
            done(m,destination)
        def find(m):
            text,needle=string(m.r[3]),string(m.r[4])
            index=text.find(needle)
            done(m,m.r[3]+index if index>=0 else 0)
        def copy_n(m):
            destination=m.r[3]
            raw=string(m.r[4])[:m.r[5]]
            memory.write(destination,raw+bytes(m.r[5]-len(raw)))
            done(m,destination)
        m=machine(0x12e4bc)
        m.hooks={0x2a340:lambda m:done(m,0),0x2a978:play,
                 0x68f88c:copy,0x68a504:find,0x68fca0:copy_n}
        m.run({stop},limit=1500)
        caption=string(context+0xfb3)
        fallback='\u300c\u2026\u2026\u2026\u300d'.encode('utf8')
        expected=(fallback if wrong_table else
                  S.string_at(data,bank.pool+bank.offs[line]).replace(b'\\n',b'\n'))
        expected_calls=[] if wrong_table else [bank.cues[line][0]&0xffff]
        if caption!=expected or calls!=expected_calls or bool(entry_flag)!=wrong_table:
            raise ValueError('Native coupled quote/voice control differs')
        if parsed_lines != (0 if wrong_table else bank.n6):
            raise ValueError('Native parser did not produce the expected line count')
        cases.append(dict(control='original_table_with_English_data' if wrong_table else
            'paired_English_table_and_data',bank=bank.i,line=line,
            read_offset=lo,read_length=hi-lo,loaded_header_hex=header,
            native_parsed_line_count=parsed_lines,prepared_entry_flag=entry_flag,
            voice_play_calls=calls,ellipsis_caption=caption==fallback,
            expected_caption_verified=True))
    return dict(cases=cases,original_control_code_byte_identical=True,
        native_entry_builder_va='0x12eb28',native_playback_selector_va='0x12e4bc',
        fallback_flag_branch_va='0x12e594',fallback_caption_load_va='0x12e700',
        fallback_caption_source_va=hex(S.word(elf,S.TOC_BASE-0x5fec)),
        mocked_boundaries=['stream completion','upstream rule choice',
            'speaker lookup','audio engine','C string helpers'],
        seeded_default_entry=dict(cue_id=0,fallback_flag=1),
        actual_hardware_loaded_header_and_entry_flag_unknown=True,
        physical_console_failure_reproduced=False,
        demonstrates_both_symptoms_from_one_mismatched_bank=True)
