"""Execute diagnostic hooks with guarded memory and real text conversion."""
import struct
from tools import cfw_self as C, srvc as S, ppc_exec as P, ui_hook as H
from tools import cfw_voice_diagnostic as D, library_runtime as L, eboot_text as E

CTX=0x20000000
STREAM=0x21000000
BUFFER=0x22000000
STACK=0x30000000
ENGINE=0x31000000
STRINGS=0x32000000
STOP=0x40000000


class Harness:
    def __init__(self,elf,report):
        self.elf,self.report=elf,report
        self.mem=P.Memory()
        for kind,flags,off,va,_pa,size,_memsz,_align in C.program_headers(elf)[1]:
            if kind==1 and size:
                self.mem.map(va,elf[off:off+size],bool(flags&2))
        self.mem.map(CTX,bytes(0x10000))
        self.mem.map(STREAM,bytes(0x100))
        self.mem.map(BUFFER,bytes(0x10000))
        self.mem.map(STACK,bytes(0x8000))
        self.mem.map(ENGINE,bytes(0x1000))
        self.mem.map(STRINGS,bytes(0x1000))

    def word(self,at):return int.from_bytes(self.mem.read(at,4),'big')
    def put(self,at,value):self.mem.write(at,struct.pack('>I',value))
    def toc(self,disp):return self.word(S.TOC_BASE+disp)

    def string(self,at):
        raw=bytearray()
        while len(raw)<8192:
            byte=self.mem.read(at+len(raw),1)
            if byte==b'\0':return bytes(raw)
            raw+=byte
        raise ValueError('Unterminated diagnostic string')

    def machine(self,pc):
        m=P.Machine(self.mem)
        m.r=[0x77000000+i for i in range(32)]
        m.r[1],m.r[2]=STACK+0x4000,S.TOC_BASE
        m.pc,m.lr,m.ctr,m.cr,m.ca=pc,STOP,0x12345678,0x87654321,1
        m.f=[float(i)+.25 for i in range(32)]
        return m

    def poll(self,bank,buffer=BUFFER):
        self.put(STREAM+0x28,S.TABLE_VA)
        self.mem.write(STREAM+0x2c,struct.pack('>H',bank))
        m=self.machine(D.POLL)
        m.r[0],m.r[31]=buffer,STREAM
        before=m.r[:],m.cr,m.lr,m.ctr,m.ca,m.f[:]
        m.run({D.POLL+4},limit=1000)
        if (m.r,m.cr,m.lr,m.ctr,m.ca,m.f)!=before:
            raise ValueError('Read-observer hook changed machine registers')
        if self.word(STREAM+0x20)!=buffer:
            raise ValueError('Original buffer-pointer store was not replayed')
        state=self.report['state_va']
        rows=[struct.unpack('>4I',self.mem.read(state+16+i*16,16)) for i in range(8)]
        row=next(r for r in rows if r[0]==buffer)
        table=S.read_table(self.elf)
        expected=(buffer,bank,table[bank],table[bank+1]-table[bank]) if bank<S.NBLOCKS else (buffer,0xffffffff,0xffffffff,0xffffffff)
        if row!=expected:
            raise ValueError('Read-observer cache differs from the actual bank table')
        return row

    def prepare(self,bank=3,version=3,lines=214,channel=0,actor=0,cue=0,flag=1,
                cached=True,null=False):
        self.mem.write(CTX,bytes(0x2000))
        self.mem.write(BUFFER,struct.pack('<BBBBHH',version,74,0,0,0,lines))
        slot=(64 if channel>1 else 0)+actor*32
        if channel<=3 and actor<=1:self.put(CTX+slot,0 if null else BUFFER)
        entry=CTX+0x80+channel*0xec
        self.mem.write(entry,struct.pack('>HHBBHI',cue,0,0,flag,0,0))
        self.put(entry+0xc0,1)
        self.put(entry+0xc4,0)
        if cached and not null:self.poll(bank)
        return entry

    def format(self,channel=0,actor=0):
        m=self.machine(D.FALLBACK)
        m.r[24],m.r[22],m.r[25]=channel,actor,CTX
        m.r[29]=CTX+0x80+channel*0xec
        before=m.r[:],m.cr,m.lr,m.ctr,m.ca,m.f[:]
        context=self.mem.read(CTX,0x2000)
        m.run({D.FALLBACK+4},limit=3000)
        expected=before[0][:]
        expected[27]=self.report['text_va']
        if (m.r,m.cr,m.lr,m.ctr,m.ca,m.f)!=(expected,*before[1:]):
            raise ValueError('Fallback hook changed registers beyond its text pointer')
        if self.mem.read(CTX,0x2000)!=context:
            raise ValueError('Fallback observer changed selection/context data')
        raw=self.string(m.r[27])
        if len(raw)+1>134:raise ValueError('Diagnostic caption exceeds capacity')
        inverse={v:k for k,v in L.LETTERS.items()}
        text=''.join(inverse.get(c,c) for c in raw.decode('utf8'))
        return raw,text


def verify(elf,baseline,build,report):
    h=Harness(elf,report)
    poll_cases=0
    for bank in range(S.NBLOCKS):
        h.poll(bank)
        poll_cases+=1
    for bank in (0xffff,1,2,3,4,5,6,7,8,9,10):
        h.poll(bank,BUFFER+0x100*(bank&15))
        poll_cases+=1
    cases=[]
    for channel in range(4):
        for actor in range(2):
            h=Harness(elf,report)
            h.prepare(channel=channel,actor=actor,version=0x86,lines=0,cue=0x1234)
            raw,text=h.format(channel,actor)
            expected='0.5.54 B003 H86 N0000\\nO003520 S032E0 F1C1234'
            if text!=expected:raise ValueError('Diagnostic actor/side binding differs: '+text)
            cases.append(dict(channel=channel,actor=actor,text=text,utf8_bytes=len(raw)))
    for null,cached in ((False,False),(True,False)):
        h=Harness(elf,report)
        h.prepare(version=3,lines=0x1234,null=null,cached=cached)
        raw,text=h.format()
        expected='0.5.54 BFFF HFF NFFFF\\nOFFFFFF SFFFFF F1C0000' if null else '0.5.54 BFFF H03 N1234\\nOFFFFFF SFFFFF F1C0000'
        if text!=expected:raise ValueError('Unknown bank diagnostic does not stay bounded')
        cases.append(dict(null=null,cached=cached,text=text,utf8_bytes=len(raw)))
    oracle=H.ConverterOracle(elf)
    conversions=0
    for text in (cases[0]['text'],'0.5.54 BFFF HFF NFFFF\\nOFFFFFF SFFFFF FFCFFFF'):
        display=text.replace('\\n','\n')
        source=''.join('\n' if c=='\n' else L.LETTERS[c] for c in display).encode('utf8')
        wanted=E.encode(display,build['mapping'])+b'\0\0'
        for model in ('A','B'):
            actual,fill,_steps=oracle.run(source,model)
            if actual[:len(wanted)]!=wanted or any(b!=fill for b in actual[len(wanted):]):
                raise ValueError('Native diagnostic UTF-8 conversion differs')
            conversions+=1
    integration=[]
    for flag in (0,1):
        results=[]
        for candidate in (baseline,elf):
            current=Harness(candidate,report)
            current.prepare(flag=flag,cue=7,version=0x86 if flag else 3,
                            lines=0 if flag else 214,cached=candidate==elf)
            current.put(current.toc(-0x6018),ENGINE)
            current.mem.write(ENGINE+0x21c,struct.pack('>H',100))
            current.put(current.toc(-0x6014)+0x88,STRINGS)
            current.mem.write(STRINGS,b'Test pilot\0')
            quote=E.encode('Test quote.',build['mapping'])
            current.mem.write(STRINGS+0x100,quote+b'\0')
            current.put(CTX+0x1c,STRINGS+0x100)
            current.mem.write(CTX+0x1037,b'\xa6\xb7')
            calls=[]
            def done(m,value=0):m.r[3],m.pc=value,m.lr
            def play(m):calls.append(m.r[4]);done(m)
            def copy(m):
                destination=m.r[3]
                current.mem.write(destination,current.string(m.r[4])+b'\0')
                done(m,destination)
            def copy_n(m):
                destination=m.r[3]
                raw=current.string(m.r[4])[:m.r[5]]
                current.mem.write(destination,raw+bytes(m.r[5]-len(raw)))
                done(m,destination)
            def find(m):
                source,needle=current.string(m.r[3]),current.string(m.r[4])
                offset=source.find(needle)
                done(m,m.r[3]+offset if offset>=0 else 0)
            m=current.machine(0x12e4bc)
            m.r[3:7]=[CTX,0,0,0]
            m.hooks={0x2a340:lambda m:done(m),0x2a978:play,
                     0x68f88c:copy,0x68a504:find,0x68fca0:copy_n}
            m.run({STOP},limit=5000)
            caption=current.string(CTX+0xfb3)
            if len(caption)+1>134 or current.mem.read(CTX+0x1037,2)!=b'\xa6\xb7':
                raise ValueError('Native caption construction crossed its buffer')
            results.append((caption,calls,current.mem.read(CTX,0x2000)))
        old,new=results
        if old[1]!=new[1] or new[1]!=([] if flag else [7]):
            raise ValueError('Diagnostic changed voice-play calls')
        before,after=bytearray(old[2]),bytearray(new[2])
        before[0xfb3:0x1039]=after[0xfb3:0x1039]
        if before!=after:raise ValueError('Diagnostic changed native state outside caption')
        if not flag and old[0]!=new[0]:raise ValueError('Ordinary voiced quote changed')
        if flag:
            inverse={v:k for k,v in L.LETTERS.items()}
            visible=''.join(inverse.get(c,c) for c in new[0].decode('utf8'))
            if visible!='0.5.54 B003 H86 N0000\nO003520 S032E0 F1C0007':
                raise ValueError('Native caption builder clipped/misformatted diagnostic')
        integration.append(dict(fallback_flag=flag,voice_play_calls=new[1],
            caption_bytes=len(new[0]),native_caption_builder_verified=True))
    return dict(poll_cases=poll_cases,actor_and_unknown_cases=cases,integration=integration,
        native_converter_models_verified=conversions,all_gprs_cr_lr_ctr_xer_and_fprs_preserved=True,
        original_poll_store_replayed=True,selection_context_unchanged=True,
        fonts_unicode_table_and_data_load_layout_unchanged=True,
        hardware_verified=False)
