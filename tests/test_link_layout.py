import struct
import unittest
from tools import link_layout as ll, ui_hook, ppc_exec as p, operation_layout, mission_text
from tools.common import ROOT
from tests.test_ui_hook import fw


class LayoutExecution(unittest.TestCase):
    def fixture(self):
        mem=p.Memory(); mem.map(0x400000,bytes(0x3000)); mem.map(0x310000,bytes(0x2000))
        widths=bytearray([32]*4480)
        for c in 'SumeragiShikuuMoveTransformSpiritStatusNoYes':
            lead,trail=fw(c); widths[(lead-0x81)*192+trail-0x40]=10+(ord(c)%9)
        mem.map(0x320000,widths,writable=False)
        entries=[dict(id=jp,key=jp.encode('cp932'),english=fw(en)) for jp,en in
                 [('スメラギ','Sumeragi'),('尸空','Shikuu'),('移動','Move'),('変形','Transform')]]
        blob,_=ui_hook.build_table(entries); mem.map(ui_hook.EXT_VA,blob,writable=False)
        lookup=ui_hook.stub(0x300000,back=0x300000,replay=ll.NOP)[:-4]+struct.pack('>I',ll.BLR)
        for va,code in ((0x300000,lookup),(0x300400,ll.lookup_wrapper(0x300400,0x300000)),
                        (0x300500,ll.units(0x300500,0x320000))):
            mem.map(va,code,writable=False)
        m=p.Machine(mem); m.r=[0x990000+i for i in range(32)]; m.r[1]=0x401800
        m.r[2]=ui_hook.TOC; m.f=[i+.25 for i in range(32)]; m.cr=0xb3c7a965; m.lr=0xdead00
        def strlen(vm):
            at=vm.r[3]; n=0
            while mem.read(at+n,1)!=b'\0': n+=1
            vm.r[3]=n; vm.pc=vm.lr
        m.hooks[ui_hook.STRLEN]=strlen
        return m,mem,widths

    def run_code(self,m,mem,code,stops):
        mem.map(0x330000,code,writable=False); m.pc=0x330000; m.run(stops,limit=40000)

    def test_lookup_units_native_fallback_and_registers(self):
        for jp,en in [('スメラギ','Sumeragi'),('尸空','Shikuu'),('未知',None),('', '')]:
            m,mem,widths=self.fixture(); raw=jp.encode('cp932')
            mem.map(0x340000,raw+b'\0',writable=False); m.r[3]=0x340000
            before=m.r[:]; cr=m.cr
            m.pc=0x300400; m.run({0xdead00})
            self.assertEqual(m.r[31],before[31]); self.assertEqual(m.cr,cr)
            for r in set(range(32))-{0,3}: self.assertEqual(m.r[r],before[r])
            m.pc=0x300500; m.run({0xdead00})
            expected=sum(widths[(a-0x81)*192+b-0x40] for a,b in zip(fw(en)[::2],fw(en)[1::2])) if en is not None else p.M64
            self.assertEqual(m.r[3],expected)

    def test_actual_drawer_pen_and_fixed_point_positions(self):
        m,mem,_=self.fixture(); m.r[30]=0x311000; m.f[31]=200.25
        before=(m.r[:],m.f[:],m.cr,m.lr)
        self.run_code(m,mem,ll.drawer_pen(0x330000,0x310000),{0x141ac})
        self.assertEqual(mem.read(0x310400,4),struct.pack('>f',200.25))
        self.assertEqual((m.r,m.f,m.cr,m.lr),before)
        # Execute another stub in a fresh fixture, carrying actual pen values.
        m,mem,_=self.fixture(); m.r[30]=0x311000; m.f[0]=287.875
        mem.write(0x310400,struct.pack('>f',200.25)); before=(m.r[:],m.f[:],m.cr,m.lr)
        self.run_code(m,mem,ll.drawer_pen(0x330000,0x310000,True),{0x14890})
        self.assertEqual(mem.read(0x310404,4),struct.pack('>f',87.625))
        self.assertEqual((m.r,m.f,m.cr,m.lr),before)
        # Fractional advances remain fractional through the link loop.
        m,mem,_=self.fixture(); mem.write(0x310404,struct.pack('>f',87.625))
        self.run_code(m,mem,ll.column(0x330000,0x310000),{0x2209ec})
        self.assertEqual(m.r[9],11216)
        m,mem,_=self.fixture(); style=bytearray(0x40)
        struct.pack_into('>hh',style,0x20,320,580); style[0x2e]=28; style[0x2f]=38
        mem.map(0x340000,style,writable=False)
        m.r[4]=0x340000; m.r[5]=11216; m.r[6]=2; m.r[7]=0x311000; m.r[8]=0x311004
        self.run_code(m,mem,ll.position(0x330000),{0xdead00})
        self.assertEqual(struct.unpack('>II',mem.read(0x311000,8)),(407,656))

    def test_capture_flat_selection_banks_and_record_isolation(self):
        for bank,slot in [(0,0),(1,7),(15,15)]:
            m,mem,_=self.fixture(); m.r[28]=0x311000; m.r[3]=12
            mem.write(m.r[1]+0x70,struct.pack('>II',bank,slot))
            mem.write(0x310404,struct.pack('>f',93.75))
            record_before=mem.read(m.r[28],20)
            self.run_code(m,mem,ll.capture(0x330000,0x310000),{0x21cde0})
            record=mem.read(m.r[28],20)
            self.assertEqual(record[:4]+record[5:],record_before[:4]+record_before[5:])
            self.assertEqual(record[4],12)
            self.assertEqual(mem.read(0x310000+(bank*16+slot)*4,4),struct.pack('>f',93.75))
            m,mem,_=self.fixture(); m.r[4]=bank*16+slot; m.r[3]=0x311000
            mem.write(0x310000+m.r[4]*4,struct.pack('>f',93.75))
            self.run_code(m,mem,ll.secondary(0x330000,0x310000),{0x216a40})
            self.assertEqual(mem.read(m.r[1]+0x78,4),struct.pack('>f',93.75))

    def test_name_width_uses_quad_and_native_pitch_fallback(self):
        for text,en in [('スメラギ','Sumeragi'),('尸空','Shikuu'),('未知',None)]:
            m,mem,widths=self.fixture(); mem.map(0x340000,text.encode('cp932')+b'\0',writable=False)
            m.r[3]=0x340000; m.r[31]=0x311000
            mem.write(0x31100c,struct.pack('>I',22)); mem.write(0x311014,struct.pack('>I',28))
            self.run_code(m,mem,ll.name_width(0x330000,0x300400,0x300500),{0x2aae08})
            expected=(sum(widths[(a-0x81)*192+b-0x40] for a,b in zip(fw(en)[::2],fw(en)[1::2]))*22/32
                      if en else len(text)*28)
            actual=struct.unpack('>f',struct.pack('>I',m.r[3]))[0]
            self.assertEqual(actual,expected)

    def test_primary_matches_scene_and_glossary_identity(self):
        m,mem,_=self.fixture(); m.r[31]=0x345000; m.r[30]=0x311000; m.r[28]=0x346000
        mem.map(0x340000,bytes(0x1000))
        mem.write(0x34000c,struct.pack('>I',0x777))
        # Two records share glossary index; only the right scene may match.
        for slot,scene,x,width in [(2,0x778,400,200),(19,0x777,500,91.25)]:
            rec=struct.pack('>hhBBBBIII',x,580,12,1,28,38,0,scene,9)
            mem.write(0x340100+slot*20,rec); mem.write(0x310000+slot*4,struct.pack('>f',width))
        style=bytearray(0x40); style[0x2d]=26; mem.write(0x340080,style)
        def fixed(value):
            def hook(vm): vm.r[3]=value; vm.pc=vm.lr
            return hook
        m.hooks[0x2177bc]=fixed(0x340000); m.hooks[0x2a9114]=fixed(9)
        m.hooks[0x21c9b0]=fixed(0x340010)
        def get_style(vm):
            self.assertEqual(vm.r[4],0x346000); vm.r[3]=0x340080; vm.pc=vm.lr
        m.hooks[0x2148d0]=get_style
        def slot(vm):
            vm.r[3]=0x340100+vm.r[4]*20 if vm.r[4] in (2,19) else 0; vm.pc=vm.lr
        m.hooks[0x21c730]=slot
        self.run_code(m,mem,ll.primary(0x330000,0x310000),{0x214ab4})
        self.assertEqual(struct.unpack('>ffff',mem.read(0x311000,16)),(500,581,91.25,27))
        self.assertEqual(m.r[31],0x345000)
        self.assertEqual(m.r[28],0x346000)

    def test_utf8_centering_uses_live_quad_cp932_path_stays_native(self):
        cases=[('移動',0,True),('変形',0,True),('未知',0,False),('移動',1,False)]
        for text,encoding,success,alternate in [(*case,alt)for case in cases for alt in (False,True)]:
            m,mem,widths=self.fixture(); mem.map(ui_hook.TOC-0x7f3c,struct.pack('>I',0x340000),writable=False)
            state=bytearray(0x1200); struct.pack_into('>f',state,0x54,22); mem.map(0x340000,state)
            mem.map(0x350000,text.encode('utf8')+b'\0',writable=False)
            m.r[31]=0x350000; m.r[30]=encoding; m.f[29]=1140
            m.cr=(m.cr&~2) if alternate else (m.cr|2)
            cr=m.cr; saved=m.r[31]
            def converter(vm):
                mem.write(0x3400b8,text.encode('cp932')+b'\0'); vm.cr=0; vm.pc=vm.lr
            m.hooks[ui_hook.CONVERTER[0]]=converter
            self.run_code(m,mem,ll.center(0x330000,0x300400,0x300500),{0x14a68,0x14a2c,0x14ac4})
            self.assertEqual(m.r[31],saved)
            if success:
                en={'移動':'Move','変形':'Transform'}[text]
                w=sum(widths[(a-0x81)*192+b-0x40] for a,b in zip(fw(en)[::2],fw(en)[1::2]))*22/32
                self.assertEqual(m.pc,0x14a68); self.assertEqual(m.f[1],1140-w/2)
            else:
                self.assertEqual(m.pc,0x14ac4 if alternate else 0x14a2c); self.assertEqual(m.cr,cr)
                if alternate: self.assertEqual(m.r[3:6],[0x350000,0,encoding])

    def test_cp932_and_alternate_font_centering_preserve_selectors(self):
        selectors=[list(struct.unpack('>'+'H'*len(word),fw(word))) for word in ('No','Yes')]
        for text in ('移動','変形','No','Yes','未知','N','Ye',''):
            for alternate in (False,True):
                m,mem,widths=self.fixture()
                mem.map(ui_hook.TOC-0x7f3c,struct.pack('>I',0x340000),writable=False)
                state=bytearray(0x1200); struct.pack_into('>f',state,0x54,31); mem.map(0x340000,state)
                raw=fw(text) if text.isascii() else text.encode('cp932')
                mem.map(0x350000,raw+b'\0',writable=False)
                m.r[31]=0x350000; m.r[30]=1; m.f[29]=639.5
                m.cr=(m.cr&~2) if alternate else (m.cr|2); cr=m.cr
                before=m.r[:]; lr=m.lr
                self.run_code(m,mem,ll.center(0x330000,0x300400,0x300500,selectors),
                              {0x14a68,0x14a2c,0x14ac4})
                fallback=text in ('No','Yes','未知')
                if fallback:
                    self.assertEqual(m.pc,0x14ac4 if alternate else 0x14a2c)
                    self.assertEqual(m.cr,cr)
                    if not alternate:self.assertEqual(m.r[0],0x350000)
                    if alternate: self.assertEqual(m.r[3:6],[0x350000,0,1])
                else:
                    en={'移動':'Move','変形':'Transform'}.get(text,text)
                    units=sum(widths[(a-0x81)*192+b-0x40]for a,b in zip(fw(en)[::2],fw(en)[1::2]))
                    self.assertEqual(m.pc,0x14a68)
                    self.assertAlmostEqual(m.f[1],639.5-units*31/64)
                self.assertEqual(m.lr,lr)
                for reg in (1,2,27,28,29,30,31): self.assertEqual(m.r[reg],before[reg])

    def test_native_fallback_reaches_drawer_with_original_caption(self):
        """Run past the helper through the native CP932 count and draw tail."""
        source=ui_hook.PREPARED.read_bytes()
        for text in ('ＯＮ','ＯＦＦ','　','未知'):
            m,mem,widths=self.fixture()
            raw=text.encode('cp932')
            mem.map(0x350000,raw+b'\0',writable=False)
            native=bytearray(source[0x149bc-0x10000:0x14ae4-0x10000])
            struct.pack_into('>I',native,0x14a24-0x149bc,ui_hook.branch(0x14a24,0x330000))
            mem.map(0x149bc,native,writable=False)
            mem.map(0x330000,ll.center(0x330000,0x300400,0x300500,[]),writable=False)
            mem.map(ui_hook.TOC-0x7f3c,struct.pack('>I',0x340000),writable=False)
            mem.map(ui_hook.TOC-0x7f0c,struct.pack('>f',-.5),writable=False)
            state=bytearray(0x1200)
            struct.pack_into('>f',state,0x54,28)
            struct.pack_into('>f',state,0x5c,28)
            mem.map(0x340000,state)
            m.r[3]=0x350000;m.r[7]=1;m.r[8]=0;m.f[1]=639.5;m.f[2]=361;m.f[3]=1
            initial=(m.r[1],m.r[2],m.r[27:32],m.lr)
            m.pc=0x149bc;m.run({0x14158},limit=40000)
            self.assertEqual(m.r[3],0x350000)
            self.assertEqual(m.r[7],1)
            self.assertEqual(mem.read(m.r[3],len(raw)+1),raw+b'\0')
            self.assertEqual(m.f[1],639.5-len(text)*14)
            self.assertEqual((m.f[2],m.f[3]),(361,1))
            self.assertEqual((m.r[1],m.r[2],m.r[27:32],m.lr),initial)

    def test_heading_return_translates_before_widget_draws_text(self):
        m,mem,_=self.fixture(); mem.map(0x350000,'移動'.encode('cp932')+b'\0',writable=False)
        m.r[31]=0x350000; mem.write(m.r[1]+0xc0,struct.pack('>Q',0xbeef00))
        self.run_code(m,mem,ll.heading(0x330000,0x300400),{0x1dd17c})
        self.assertEqual(mem.read(m.r[31],len(fw('Move'))+1),fw('Move')+b'\0')
        self.assertEqual(m.r[0],0xbeef00)

    def test_actual_source_patch_and_prologue_dictionary(self):
        source=ui_hook.PREPARED.read_bytes()
        from tools import vwf
        executable,spacing=vwf.patch(source,{})
        out,report=ui_hook.hook(executable,[],require_srvc=False,payloads=[(ll.STATE,ll.PAYLOAD)])
        patched,layout=ll.apply(out,source,report['table']['payload_vas'][ll.STATE],spacing['table_va'])
        self.assertTrue(layout['identity_and_navigation_preserved'])
        bad=bytearray(out); bad[0x216a3c-0x10000]^=1
        with self.assertRaises(ValueError): ll.apply(bytes(bad),source,report['table']['payload_vas'][ll.STATE],spacing['table_va'])
        rows=operation_layout.hook_entries(source,{chr(c):fw(chr(c)).hex() for c in range(32,127)})
        keys={row['key']:row['english'] for row in rows}
        from tools import eboot_text
        english=fw('Prologue 1: '+eboot_text.load()['strings']['時獄の果てに']['en'])
        for gap in ('',' ','　'):
            key=ui_hook.utf8_key(('プロローグ第１話'+gap+'『時獄の果てに』').encode('utf8'),source)
            self.assertEqual(keys[key],english)
        # Native SR splitter: 103-byte slot, two color bytes and one NUL.
        row=next(e['en'] for e in mission_text.load()['strings'].values() if
            e['en'].startswith('This scenario has no SR Point.') and '\n' in e['en'])
        self.assertEqual(len(row.splitlines()),3)
        self.assertTrue(all(len(fw(line))<=100 for line in row.splitlines()))

    def test_scene_fallback_and_registration_keep_native_keys(self):
        for explicit in (0,0x771100):
            m,mem,_=self.fixture(); m.r[3]=0x311000
            mem.write(0x31100c,struct.pack('>I',0x772200))
            def scene(vm): vm.r[3]=explicit; vm.pc=vm.lr
            def manager(vm): vm.r[3]=0x311000; vm.pc=vm.lr
            m.hooks[0x212488]=scene; m.hooks[0x2177bc]=manager
            self.run_code(m,mem,ll.scene(0x330000),{0x21ce0c})
            self.assertEqual(m.r[3],explicit or 0x772200)
        for name,en in [('尸空','Shikuu'),('未登録',None)]:
            m,mem,_=self.fixture(); raw=name.encode('cp932')+b'\0'
            mem.map(0x340000,raw,writable=False); m.r[3]=0x311000; m.r[4]=0x340000
            before=mem.read(0x340000,len(raw))
            self.run_code(m,mem,ll.compare(0x330000,0x300400),{0x68f738})
            self.assertEqual(m.r[3],0x311000); self.assertEqual(m.lr,0xdead00)
            if en: self.assertEqual(mem.read(m.r[4],len(fw(en))),fw(en))
            else: self.assertEqual(m.r[4],0x340000)
            self.assertEqual(mem.read(0x340000,len(raw)),before)


if __name__=='__main__': unittest.main()
