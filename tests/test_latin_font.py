import importlib.util
import sys
import unittest

from tools.common import ROOT
from tools.ui_build import FACE
from tools.ui_vwf_build import raster
from tools import latin_font,dialogue_layout


@unittest.skipUnless(FACE.exists(),'PS3 Rodin Bold unavailable')
class LatinFontTests(unittest.TestCase):
    @unittest.skipUnless((ROOT.parent/'SRW Z3/tools/ttfglyph.py').exists(),'SRW Z3 source unavailable')
    def test_ascii_coverage_and_advance_match_reference(self):
        path = ROOT.parent/'SRW Z3/tools'
        sys.path.insert(0,str(path))
        try:
            spec = importlib.util.spec_from_file_location('reference_font_for_test',path/'ttfglyph.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            reference = module.Face(str(FACE),22,26,0,.5)
            for char in map(chr,range(32,127)):
                cell,width = raster(char)
                expected = bytearray(1024)
                if char==' ':
                    advance = 9
                else:
                    image,left,top,advance = reference.natural(char)
                    if image is not None:
                        reference._blit(expected,image,left,26+top)
                    advance = max(1,min(63,round(advance+1)))
                self.assertEqual(cell.tobytes(),bytes(expected),repr(char))
                self.assertEqual(width,advance,repr(char))
        finally:
            sys.path.remove(str(path))

    def test_condensed_glyphs_use_the_same_face_and_matching_advances(self):
        for prefix,scale in ((dialogue_layout.PREFIX,.85),(dialogue_layout.TIGHT_PREFIX,.8)):
            for c in 'Wide punctuation: Wmjg.,':
                normal,width = raster(c)
                glyph,advance = raster(prefix+c)
                self.assertEqual(glyph.size,(32,32))
                self.assertEqual(advance,dialogue_layout.advance(width,scale))
                self.assertEqual(bool(glyph.getbbox()),bool(normal.getbbox()))

    def test_long_ui_keeps_every_word_when_condensed(self):
        from tools import ui_catalog,ui_description_layout,opening_narration,eboot_text,library_build
        grouped,rows = ui_catalog.checked()
        resolver = eboot_text.resolver()
        for rid,sources in grouped.items():
            if not any(s['family'] in ('skills','parts','opening') for s in sources):
                continue
            text = eboot_text.unshow(library_build.expand(rows[rid]['en'],resolver))
            if sources[0]['family']=='opening':
                rendered,condensed = opening_narration.profile(text)
            else:
                rendered,condensed = ui_description_layout.profile(text,sources)
            self.assertEqual(rendered.split(),text.replace('\\n',' ').split())


if __name__=='__main__':
    unittest.main()
