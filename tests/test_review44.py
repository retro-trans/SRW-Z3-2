import json,unittest,subprocess
from unittest.mock import patch
from tools.common import ROOT
from tools import review44_text as R,review44_build as B,ui_layout_text as U,ui_hook as H,eboot_text as E


class RewardAndDeploymentCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=json.loads((B.BASE/'build.json').read_text('utf8'));cls.mapping=cls.parent['mapping']

    def test_colony_laser_uses_both_capitals_in_all_affected_dialogue(self):
        members,rows=B.stages(self.parent)
        self.assertEqual(set(members),{598,604,605});self.assertEqual(len(rows),13)
        for row in rows:
            self.assertIn('Colony Laser',row['english']);self.assertNotIn('colony laser',row['english'])
        captions=[r for r in rows if 'Control Room'in r['english']]
        self.assertEqual(len(captions),3)
        # This historical capitalization build must use its recorded source,
        # rather than replaying later Herald edits against the 0.5.43 fixture.
        commit=json.loads((ROOT/'work/output/builds/0.5.44/source_provenance.json').read_text('utf8'))['source_commit']
        def source(path):
            return json.loads(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT))
        terms=source('work/glossary/library_terms.json')['terms']
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'work/translation/en/library'],cwd=ROOT,text=True).splitlines()
        entries={kind:{}for kind in ('keyword','pilot','robot')}
        for path in paths:
            if not path.endswith('.json'):continue
            data=source(path);kind=data['kind']
            for key,value in data['entries'].items():entries[kind][key]=(path.rsplit('/',1)[-1],value)
        render=B.L.plan
        with patch.object(B.L,'plan',side_effect=lambda library,_entries,_terms:render(library,entries,terms)):
            changes,audit=B.libraries(self.parent)
        self.assertEqual(set(changes),{'MTZKN_PT.CPK'});self.assertEqual(len(audit),10)

    def test_rewards_keep_native_values_and_clear_every_digit_boundary(self):
        cases=B.numeric_cases((B.BASE/'EBOOT.BIN').read_bytes());self.assertEqual(len(cases),33)
        self.assertTrue(all(r['gap']>=8 for r in cases))
        self.assertEqual({r['label']for r in cases},{'PP each:','EXP each:','Kills each:'})
        self.assertTrue(any(r['value']==750 for r in cases))
        source=R.B.source();plan=R.plan()
        self.assertEqual(plan,json.loads(R.DEST.read_text('utf8')))
        out,_=U.fssa_patch(source,plan['edits'],self.mapping,plan['element_edits'])
        checked=B.ui_check(source,out,self.mapping);self.assertEqual(checked['numeric_positions'],3)
        grow=len(out)-len(source)
        for edit in plan['element_edits']:
            at=edit['element_offset'];self.assertEqual(out[at+grow+4:at+grow+12],source[at+4:at+12])

    def test_bullet_replacement_is_blank_and_preserves_both_states(self):
        from tools import ui_build as F
        plan=R.plan();by_at={e['widget_offset']:e for e in plan['edits']}
        self.assertEqual(by_at[0x979a4]['en'],by_at[0x979c4]['en'])
        for at in (0x979a4,0x979c4,0xab8a4):
            self.assertNotIn('・',by_at[at]['en']);self.assertIn('　',by_at[at]['en'])
            self.assertFalse(any(k in by_at[at]for k in ('x','y','mode','font_metrics')))
        for fid in (1,3):
            page=F.atlas((B.BASE/('font_%d.bin'%fid)).read_bytes())
            for token in (' ','@menu-pad:4','@menu-pad:1'):
                x,y=F.cell_xy(self.mapping[token]);self.assertFalse(page[y:y+32,x:x+32].any())

    def test_installed_dictionary_delivers_short_menu_and_blank_prefixes(self):
        elf,report=B.dictionary_patch((B.BASE/'EBOOT.BIN').read_bytes(),self.mapping)
        old=self.parent['executable']['ui_hook'];runner=H._Runner(elf,int(old['stub_va'],16),old['stub_bytes'])
        read=H._reader(elf,H._headers(elf)[2]);self.assertEqual(report['values'],9)
        for row in report['cases']:
            ptr,_=runner.run(bytes.fromhex(row['key_hex'])+b'\0')
            expected=(R.caption_encoded(row['english'],self.mapping)if row['english'].startswith('　')else E.encode(row['english'],self.mapping))+b'\0'
            self.assertIsNotNone(ptr);self.assertEqual(read(ptr,len(expected)),expected)
        bound=next(r for r in R.plan()['bounds']if r['label']=='Mech/Wpn Upg')
        self.assertLessEqual(bound['right']+6,bound['button_right'])
        self.assertEqual(len(B.caption_cases(elf,self.parent,report)),20)

if __name__=='__main__':unittest.main()
