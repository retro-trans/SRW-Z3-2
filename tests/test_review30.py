"""Native skill composition and fixed-column layout regressions."""
import json,unittest
from tools.common import ROOT
from tools import review30_messages as Q,review30_oracle as O,review30_layout as L,review30_movement as M
from tools import ui_hook as H,eboot_text as E,library_build as B,vwf,ui_layout_text as U

class Review30(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=H.PREPARED.read_bytes()
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.29/build.json').read_text('utf8'))['mapping']
        from tools import native_labels as N
        from tools.ui_build import allocate
        from tools.cpk import CPK
        from tools.pipeline import config,verified_source
        from tools.inventory import FONT
        tokens=set(cls.mapping)|{N.PREFIX+c for r in L.plan()['edits']for c in r['en']if c!='\n'}
        with CPK(verified_source(config(ROOT/'config/tengoku.json'),FONT))as font:
            cls.mapping,_=allocate([font.read(e)for e in font.files if e['id']in(1,3)],tokens,lambda t:[t])
        cls.entries=Q.hook_entries(cls.source,cls.mapping)+M.hook_entries(cls.source,cls.mapping)
        cls.expected={r['key']:r['english']for r in cls.entries}
        base,_=vwf.patch(cls.source,{})
        cls.final,cls.info=H.apply(base,cls.entries)

    def test_native_questions_for_every_skill_and_name_route(self):
        runner=H._Runner(self.final,int(self.info['stub_va'],16),self.info['stub_bytes'])
        read=H._reader(self.final,H._headers(self.final)[2])
        for row in Q.source_rows(self.source):
            for translated in (False,True):
                name=E.encode(row['en'],self.mapping)if translated else row['jp'].encode('cp932')
                old=E.encode('Counter',self.mapping)if translated else 'カウンター'.encode('cp932')
                forms=[(3,False,False,0,0),(2,False,False,0,0)]
                if row['flags']&2:forms += [(3,True,False,0,0),(1,True,False,8,0),(1,True,True,1,3)]
                for kind,leveled,multiple,current,innate in forms:
                    lines,_=O.skill(self.final,name,old,kind,leveled,multiple,current,innate)
                    for key in filter(None,lines):
                        self.assertIn(key,self.expected,(row['record'],kind))
                        pointer,_=runner.run(key+b'\0')
                        self.assertEqual(read(pointer,len(self.expected[key])+1),self.expected[key]+b'\0')

    def test_all_learning_keys_reach_exact_english(self):
        runner=H._Runner(self.final,int(self.info['stub_va'],16),self.info['stub_bytes'])
        read=H._reader(self.final,H._headers(self.final)[2])
        for row in self.entries:
            pointer,_=runner.run(row['key']+b'\0')
            self.assertEqual(read(pointer,len(row['english'])+1),row['english']+b'\0')

    def test_layout_fixed_columns_and_isolation(self):
        from tools import battle_layout as A
        source=A.source();planned=L.plan()
        self.assertEqual(json.loads(L.DEST.read_text('utf8')),planned)
        out,_=U.fssa_patch(source,planned['edits'],self.mapping)
        U.verify_fssa(source,out,planned['edits'],self.mapping)
        self.assertGreaterEqual(min(r['gap']for r in planned['bounds']),8)
        self.assertFalse(planned['numeric_coordinates_changed'])

    def test_movement_keeps_four_mask_cells_and_numbers(self):
        entries=M.hook_entries(self.source,self.mapping);self.assertEqual(len(entries),3131)
        for row in entries:
            jp=row['key'].decode('cp932');en=B.decode(row['english'],self.mapping)
            self.assertEqual(len(en.split('/')[-1]),4)
            if '／'in jp:self.assertEqual(int(jp.split('／')[0]),int(en.split('/')[0]))
            for before,after in zip(jp.split('／')[-1],en.split('/')[-1]):
                self.assertEqual(before in ('－','ー'),after in ('－','ー'))

    def test_native_movement_composer_and_converter(self):
        import itertools
        from tools import status_layout as S
        final,_=S.native_patch(self.final,self.source,self.mapping)
        table=H.unicode_table(final)
        for flags in itertools.product((False,True),repeat=4):
            old,_=M.native_mask(self.source,flags);new,_=M.native_mask(final,flags)
            jp=''.join(c if present else 'ー'for c,present in zip('空陸水地',flags))
            english=''.join(S.TERRAIN[c]if present else 'ー'for c,present in zip('空陸水地',flags))
            self.assertEqual(old,jp.encode('utf8'))
            self.assertEqual(new,english.encode('utf8'))
            self.assertEqual(H.convert(new,table),E.encode(english,self.mapping))

    def test_earth_sphere_repair_is_idempotent(self):
        from tools import review30_terms as T
        _,outputs=T.plan();self.assertEqual(outputs,{})

    def test_learning_source_guards(self):
        bad=bytearray(self.source);bad[0xa08910-0x10000]^=1
        with self.assertRaises(ValueError):Q.source_rows(bytes(bad))

if __name__=='__main__':unittest.main()
