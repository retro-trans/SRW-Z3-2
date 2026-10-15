import json, unittest
from tools.common import ROOT
from tools import review42_layout as D, review42_news as N, ui_layout_text as U
from tools import ui_catalog as C, menu_layout as M, status_layout as S
from tools import ui_hook as H, review35_news as OLD, eboot_text as E, library_build as L


class DeploymentAndNewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=ROOT/'work/output/builds/0.5.42'
        cls.parent=json.loads((ROOT/'work/output/builds/0.5.40/build.json').read_text('utf8'))

    def test_all_repeated_terrain_rows_keep_cell_and_row_geometry(self):
        p=D.plan();s=D.B.source();mapping=self.parent['mapping']
        self.assertEqual(p,json.loads(D.DEST.read_text('utf8')))
        out,_=U.fssa_patch(s,p['edits'],mapping);grow=len(out)-len(s)
        rows={a-grow:r for r in C.fssa_strings(out,decode=lambda r:r.hex())for a in r['widget_offsets']}
        blocks=[r for r in p['edits']if 'font_style'not in r]
        self.assertEqual((len(blocks),sum(e['en'].count(S.CELL['Air'])for e in blocks)),(7,45))
        for edit in blocks:
            at=edit['widget_offset']
            self.assertEqual(rows[at]['raw'],M.encode(edit,mapping))
            # Per-cell colors and positions depend on four cells per row.
            for line in edit['en'].split('\n'):
                if line.strip('　'):self.assertEqual(list(line),[S.CELL[w]for w in ('Air','Grd','Wtr','Und')])
            self.assertEqual(out[at+grow+4:at+grow+32],s[at+4:at+32])

    def test_news_fits_actual_constructor_and_preserves_full_meaning(self):
        p=N.plan();self.assertEqual(p,json.loads(N.DEST.read_text('utf8')))
        self.assertEqual((p['paragraphs'],p['scenario_occurrences']),(22,38))
        before={r['va']:r for r in OLD.plan()['rows']}
        elf=H.PREPARED.read_bytes()
        for row in p['rows']:
            self.assertEqual(' '.join(row['english']),' '.join(before[row['source_va']]['english']))
            copied,_=OLD.native_lines(elf,'\n'.join(row['english']).encode('ascii'))
            self.assertEqual(copied,[line.encode('ascii')for line in row['english']])
            self.assertLessEqual(max(row['spans']),928)
        reported={r['source_va']:r for r in p['rows']}
        self.assertEqual(reported['0x8a1078']['english'],['Northern Europe Front:',
            'Federation & Resistance Launch Counteroffensive'])
        self.assertEqual(reported['0x8a1110']['english'],['South America Front: Federation Launches Counteroffensive',
            'Entire Pacific Rim: All-Out Counteroffensive Begins'])

    def test_exact_psyco_waves_aliases_and_all_active_references(self):
        resolver=E.resolver();terms=json.loads((ROOT/'work/glossary/library_terms.json').read_text('utf8'))['terms']
        aliases={t['token']for t in terms if t.get('en')=='Psyco Waves'}
        self.assertEqual(aliases,{'サイコ・ウェーブ','精神感応波'})
        from tools.dialogue_build import translations
        count=0
        for rid,row in translations().items():
            hits=sum(row['en'].count('$$'+a+'$$')for a in aliases)
            if hits:
                expanded=L.expand(row['en'],resolver)
                self.assertGreaterEqual(expanded.count('Psyco Waves'),hits)
                self.assertNotIn('psycho-Waves',expanded);count+=hits
        self.assertEqual(count,8)

    def test_compiled_scenario_pointers_and_installed_draw_helpers(self):
        if not (self.base/'build.json').exists():self.skipTest('Current compiled build required')
        b=json.loads((self.base/'build.json').read_text('utf8'));elf=(self.base/'EBOOT.BIN').read_bytes()
        result=N.verify(elf,b['mapping'],b['executable']['ui_hook'],b['executable']['link_layout'])
        self.assertEqual(result['scenario_occurrences'],38)
        self.assertEqual(result['paragraphs'],22)
        self.assertGreater(len(result['origin_cases']),60)

if __name__=='__main__':unittest.main()
