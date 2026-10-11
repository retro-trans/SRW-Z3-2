import struct
import unittest
from tools import category_ui as C,operation_layout as O,ui_hook as H,ui_layout_text as F
from tools import eboot_text as E,status_layout as S,ui_catalog as U
from tools.ui_description_layout import advance
from tools.ui_vwf_build import raster
from tests.test_ui_hook import fw


class CategoryUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.elf=H.PREPARED.read_bytes()
        cls.mapping={chr(c):fw(chr(c)).hex()for c in range(32,127)}
        cls.mapping.update({token:bytes((0x87,0x40+i)).hex()for i,token in enumerate(S.TINY)})
        cls.source=C.B.source();cls.plan=C.plan()
        cls.widgets={a:r for r in U.fssa_strings(cls.source)for a in r['widget_offsets']}

    def test_actual_episode_numbers_and_branch_headings(self):
        stages=O.episodes(self.elf)
        self.assertEqual(len(stages),104)
        self.assertEqual(sum(map(len,stages.values())),126)
        self.assertEqual(stages[(1,'新地球皇国')],[184,185])
        self.assertEqual(stages[(62,'果てなき世界')],[306,307,308,309])
        entries={r['key']:r['english']for r in O.hook_entries(self.elf,self.mapping)}
        translations=E.load()['strings']
        from tools import library_build as L
        for n,jp in stages:
            number=str(n).translate(str.maketrans('0123456789','０１２３４５６７８９'))
            title=E.unshow(L.expand(translations[jp]['en'],E.resolver()))
            for gap in ('',' ','　'):
                key=H.utf8_key(('第'+number+'話'+gap+'『'+jp+'』').encode('utf8'),self.elf)
                self.assertEqual(entries[key],E.encode('Episode %d: %s'%(n,title),self.mapping))

    def test_targets_and_complete_map_attribute_family(self):
        targets=C.assembled_targets(self.elf)
        self.assertEqual(len(targets),16)
        self.assertEqual(targets['味方単体'],'One Ally')
        self.assertEqual(targets['敵全体'],'All Foes')
        for text in targets.values():self.assertLess(sum(map(advance,text))*28/32+4,150)
        terrain=C.terrain_rows()
        self.assertEqual(len(terrain),83)
        self.assertIn('平地',terrain);self.assertIn('崖',terrain)
        self.assertNotIn('崇',terrain)
        for text in terrain.values():
            self.assertTrue(text.isascii())
            self.assertLessEqual(sum(map(advance,text))*28/32,300)
        broken=bytearray(self.elf);broken[0xa0de3e-0x10000]^=1
        with self.assertRaises(ValueError):C.assembled_targets(bytes(broken))

    def test_dynamic_movement_training_and_mission_keys(self):
        entries=C.hook_entries(self.elf,self.mapping)
        by_key={r['key']:r['english']for r in entries}
        self.assertEqual(len(by_key),len(entries))
        self.assertEqual(by_key['空陸－－'.encode('cp932')],
            E.encode(S.TERRAIN['空']+S.TERRAIN['陸']+'－－',self.mapping))
        self.assertEqual(by_key['格：\n射：'.encode('cp932')],E.encode(S.CELL['CQB']+'\n'+S.CELL['RNG'],self.mapping))
        missions=[r for r in entries if r['id'].startswith('category:mission-name:')]
        self.assertEqual(len(missions),19)
        for row in missions:
            self.assertIn('ヒビキ'.encode('cp932'),row['key'])
            self.assertNotIn('ヒビキ'.encode('cp932'),row['english'])
        self.assertNotIn('ヒビキ'.encode('cp932'),by_key)

    def test_immutable_values_pitch_and_measured_column_clearance(self):
        edits=self.plan['edits'];built,_=F.fssa_patch(self.source,edits,self.mapping)
        F.verify_fssa(self.source,built,edits,self.mapping)
        grow=len(built)-len(self.source)
        for row in edits:
            at=row['widget_offset']
            self.assertEqual(built[at+grow+4:at+grow+16],self.source[at+4:at+16])
            self.assertEqual(built[at+grow+21:at+grow+32],self.source[at+21:at+32])
            if '\n' in row['en']:
                quad=row['font_metrics'][3]
                if at in (0x9d824,0x9d844,0x9d864):
                    cells=len(self.widgets[at]['text'].split('\n')[0])
                    self.assertEqual((cells,self.source[at+20]),(2,20))
                    budget=cells*self.source[at+20]
                else:budget=65
                for text in row['en'].split('\n'):
                    self.assertLess(sum(map(advance,text))*quad/32+4,budget)
        training={r['widget_offset']:r for r in edits}
        first=struct.unpack_from('>f',self.source,0x9d824+4)[0]*640+640
        title=struct.unpack_from('>f',self.source,0x9d804+4)[0]*640+640
        self.assertLess(title+sum(map(advance,training[0x9d804]['en']))*28/32+4,first)
        corrupt=bytearray(built);corrupt[0x9d844+grow+21]^=1
        with self.assertRaises(ValueError):F.verify_fssa(self.source,bytes(corrupt),edits,self.mapping)
        self.assertEqual(sum(r['en']=='Foc'for r in edits),23)

    def test_larger_terrain_ink_retains_cell_width(self):
        for word in ('Air','Grd','Wtr','Spc','Und'):
            glyph,width=raster(S.CELL[word]);box=glyph.getbbox()
            self.assertEqual(width,32)
            self.assertGreaterEqual(box[3]-box[1],15)
            self.assertLessEqual(box[2]-box[0],28)


if __name__=='__main__':unittest.main()
