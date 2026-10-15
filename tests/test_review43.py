import json,unittest
from tools.common import ROOT
from tools import review43_text as R,review43_build as B,ui_layout_text as U,eboot_text as E,status_layout as S
from tools.ui_coverage import member,ui_string_table
from tools.cpk import CPK


class ReportedMapCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=json.loads((B.BASE/'build.json').read_text('utf8'))
        cls.mapping=cls.parent['mapping']

    def test_phase_native_centering_and_separate_trans_am_question(self):
        from tools.pipeline import config,verified_source
        from tools.aid_art import ARCHIVE
        source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),5)
        edits=R.plan()['table_fragments']
        suffix=next(e for e in json.loads(U.CATALOG.read_text('utf8'))['table_fragments']if e['table_row_id']==4)
        sb=U.table_patch(source,edits+[suffix],self.mapping)
        elf,report=B.command_patch((B.BASE/'EBOOT.BIN').read_bytes(),self.mapping)
        checks=B.native_cases(elf,self.parent,sb)
        self.assertEqual(len(checks['phase_origins']),14)
        self.assertTrue(all(r['center']==640 and r['left']>80 for r in checks['phase_origins']))
        self.assertEqual([r['english']for r in checks['command_lookups']],['Trans-Am','Activate Trans-Am?'])
        self.assertEqual(len(checks['command_caption_cases']),4)
        self.assertEqual(len(report['modified_file_ranges']),1)

    def test_components_translate_before_composition_and_keep_slots(self):
        from tools.pipeline import config,verified_source
        from tools.aid_art import ARCHIVE
        source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),5)
        p=R.plan();self.assertEqual(p,json.loads(R.DEST.read_text('utf8')))
        before=ui_string_table(source);out=U.table_patch(source,p['table_fragments'],self.mapping)
        after=ui_string_table(out,decode=lambda r:r.hex());changed={e['table_row_id']for e in p['table_fragments']}
        self.assertEqual(len(before),len(after))
        for a,b in zip(before,after):
            if a['id']not in changed:self.assertEqual(a['raw'],b['raw'])
        for i,name in enumerate(('Air','Grd','Wtr','Und')):
            self.assertEqual(after[91+i]['raw'],E.encode(S.CELL[name],self.mapping))
            self.assertEqual(len(after[91+i]['raw']),2)
        import itertools
        for flags in itertools.product((False,True),repeat=4):
            mask=b''.join(after[91+i]['raw']if flag else 'ー'.encode('cp932')for i,flag in enumerate(flags))
            self.assertEqual(len(mask),8)

    def test_aboard_clears_count_without_changing_state(self):
        p=R.plan();source=R.B.source()
        out,report=U.fssa_patch(source,p['edits'],self.mapping)
        self.assertEqual(report['widgets'],3)
        self.assertLess(p['aboard_bounds']['right'],p['aboard_bounds']['count_left']-20)
        for edit in p['edits']:
            at=edit['widget_offset'];grow=len(out)-len(source)
            self.assertEqual(source[at+4:at+32],out[at+grow+4:at+grow+32])

    def test_tenshi_article_preserves_other_angel_terms(self):
        from tools.dialogue_build import translations
        rows=translations()
        self.assertIn('...A $$テンシ$$.',rows['598:t_5:36']['en'])
        self.assertFalse(any('an $$テンシ$$'in r['en'].lower() for r in rows.values()))
        self.assertTrue(any('an $$天翅$$'in r['en']for r in rows.values()))

if __name__=='__main__':unittest.main()
