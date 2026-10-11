import itertools,json,struct,unittest
import numpy as np
from tools import review22_layout as L,native_labels as N,ui_build as F
from tools import battle_layout as B,ui_catalog as U,ui_layout_text as W
from tools import parts_movement as M,status_layout as S,ui_hook as H,tutorial_layout as T
from tools import eboot_text as E,library_build as R
from tests.test_ui_hook import fw

class Review22UI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=B.source();cls.plan=L.plan();cls.original=H.PREPARED.read_bytes()
        cls.mapping={chr(c):fw(chr(c)).hex()for c in range(32,127)}
        chars=set(''.join(r['en']for r in cls.plan['edits']))-{'\n'}
        cls.mapping.update({N.PREFIX+c:bytes((0x87,0x40+i)).hex()for i,c in enumerate(sorted(chars))})
        cls.grouped,cls.rows=U.checked()

    def test_original_fill_and_outline_masks_are_not_reweighted(self):
        for c in set('TeamFundsTop PPNeed:EffectMoveArmorMob.HitRangeLeftTotalType:')-{' '}:
            glyph,width=N.raster(c);actual=F.glyph_pixels(glyph)
            x,y=F.cell_xy(chr(ord(c)+0xfee0).encode('cp932').hex());original=N.page()[y:y+32,x:x+32]
            # Both fill and outline preserve every native nonblank texel and
            # its vertical position; only horizontal blank margins move.
            for row in range(32):
                self.assertEqual(original[row][original[row]!=0].tolist(),actual[row][actual[row]!=0].tolist())
            self.assertGreaterEqual(width,1);self.assertLessEqual(width,32)
            self.assertEqual(actual.dtype,np.dtype('uint16'))

    def test_labels_keep_native_colors_states_pitch_and_separate_values(self):
        out,_=W.fssa_patch(self.source,self.plan['edits'],self.mapping);grow=len(out)-len(self.source)
        W.verify_fssa(self.source,out,self.plan['edits'],self.mapping)
        decoded={a:r for r in U.fssa_strings(out,decode=lambda b:R.decode(b,self.mapping))for a in r['widget_offsets']}
        for row in self.plan['edits']:
            at=row['widget_offset'];self.assertEqual(decoded[at+grow]['text'],row['en'])
            self.assertEqual(out[at+grow+8:at+grow+16],self.source[at+8:at+16])
            self.assertEqual(out[at+grow+21:at+grow+23],self.source[at+21:at+23])
            self.assertEqual(out[at+grow+24:at+grow+32],self.source[at+24:at+32])
            self.assertEqual(out[at+grow+23],row.get('mode',self.source[at+23]))
        self.assertGreaterEqual(min(b['gap']for b in self.plan['bounds']),6)
        broken=bytearray(out);broken[0x9bf04+grow+12]^=1
        with self.assertRaises(ValueError):W.verify_fssa(self.source,bytes(broken),self.plan['edits'],self.mapping)

    def test_fixed_help_rows_fit_columns_and_panel_without_new_rows(self):
        report=T.report(self.grouped,self.rows,E.resolver())
        self.assertEqual(sum(r['budget']==320 for r in report['rows']),23)
        for row in report['rows']:
            self.assertNotIn('\n',row['text']);self.assertLessEqual(row['width'],row['budget'])
        # Formatting controls never contribute glyph width or lose their place.
        raw='1\x0bSong1\x01';self.assertEqual(T.width(raw),T.width('Song'))
        self.assertEqual(T.profile(raw,[dict(id='aid:6:363')])[0],raw)
        with self.assertRaises(ValueError):T.profile('W'*200,[dict(id='aid:6:363')])

    def test_parts_formatter_all_eight_movement_masks_and_isolation(self):
        mapping={token:bytes((0x87,0x40+i)).hex()for i,token in enumerate(S.TINY)}
        base,_=S.native_patch(self.original,self.original,mapping);out,report=M.apply(base,self.original)
        self.assertEqual(report['cells'],3)
        for bits in itertools.product((False,True),repeat=3):
            text='';expected=b''
            for present,(va,jp,en)in zip(bits,M.CELLS):
                if present:
                    text+=out[va-0x10000:va-0x10000+3].decode('utf8');expected+=bytes.fromhex(mapping[S.CELL[en]])
                else:text+='－';expected+='－'.encode('cp932')
            self.assertEqual(H.utf8_key(text.encode('utf8'),out),expected)
        broken=bytearray(base);broken[0x855db2-0x10000]^=1
        with self.assertRaises(ValueError):M.apply(bytes(broken),self.original)

if __name__=='__main__':unittest.main()
