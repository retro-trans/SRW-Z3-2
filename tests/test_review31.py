"""Verify full SR slots, their actual reported phases and the former overflow."""
import json, unittest
from tools.common import ROOT
from tools import mission_panel as P, mission_display as D, mission_text as M
from tools import ui_hook as H, library_build as L, vwf, review31_sr as A
from tools.cpk import CPK


class Review31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = json.loads((ROOT/'work/output/builds/0.5.30/build.json').read_text('utf8'))['mapping']
        cls.rendered = M.plan(D.advance)
        source, _ = vwf.patch(H.PREPARED.read_bytes(), {})
        cls.entries = D.hook_entries(H.PREPARED.read_bytes(), cls.rendered, cls.mapping)
        cls.final, cls.info = H.apply(source, cls.entries)

    def test_every_sr_in_actual_four_row_panel_and_drawer(self):
        cases = P.sr_cases(self.final, self.rendered, self.mapping)
        self.assertEqual(len(cases), 210)
        self.assertEqual(len({r['source_sha256'] for r in cases}), 101)
        self.assertLessEqual(max(r['rows'] for r in cases), 4)
        wanted = {r['key']: r['english'] for r in self.entries}
        read = H._reader(self.final, H._headers(self.final)[2])
        runner = H._Runner(self.final, int(self.info['stub_va'], 16), self.info['stub_bytes'])
        for case in cases:
            for raw, english in zip(case['keys'], case['english']):
                key = bytes.fromhex(raw); pointer, _ = runner.run(key+b'\0')
                self.assertEqual(read(pointer, len(wanted[key])+1), wanted[key]+b'\0')
                self.assertEqual(L.decode(wanted[key], self.mapping), english)

    def test_old_candidate_reproduces_all_six_panel_overflows(self):
        failed = 0
        with CPK(ROOT/'work/output/builds/0.5.30/STGZ3OF2.cpk') as arc:
            for member, fingerprint, _, _ in A.EDITS:
                source = (M.dlg.MEMBERS/('%05d.bin' % member)).read_bytes()
                raw = arc.read(next(r for r in arc.files if r['id'] == member))
                for old, compiled in zip(M.tables(source), M.OP.finditer(raw)):
                    for (_, jp), literal in zip(old[1], M.LIT.finditer(compiled.group(1))):
                        if A.sha256(jp.encode('cp932')) != fingerprint:
                            continue
                        text = M.unescape_bytes(literal.group(1))
                        with self.assertRaisesRegex(ValueError, 'four-row panel'):
                            P.assemble(self.final, [text], [0, -1, -1, -1, -1, -1, -1, 0])
                        failed += 1
        self.assertEqual(failed, 6)

    def test_reported_requirements_survive_native_phase_and_lookup(self):
        from tools import squad_text as S
        stages = D.stage_text(self.rendered); wanted = {r['key']: r['english'] for r in self.entries}
        for member, requirement in ((234, 'any damage.'), (280, '6 or more enemies.')):
            raw = S.rebuild_member(member, stages, S.plan(), self.mapping)
            for table in M.OP.finditer(raw):
                strings = [M.unescape_bytes(r.group(1)) for r in M.LIT.finditer(table.group(1))]
                for phase in P.phases(table):
                    records, _ = P.assemble(self.final, strings, phase, phase)
                    payloads = [L.decode(wanted[r['text']], self.mapping) for r in records['sr'] if r['active']]
                    text = ' '.join(payloads)
                    if text != 'None':
                        self.assertIn(requirement, text)
                        self.assertEqual(len(payloads), 2)

    def test_reviewed_wording_is_source_bound_and_idempotent(self):
        audit, outputs = A.plan()
        self.assertFalse(outputs)
        self.assertEqual(len(audit['changes']), 6)
        self.assertTrue(all(r['rows'] == 4 for r in audit['changes']))
        bad = bytearray(self.final); bad[P.PANEL[0]-0x10000] ^= 1
        with self.assertRaisesRegex(ValueError, 'assembler changed'):
            P.assemble(bytes(bad), [b'x'], [0, -1, -1, -1, -1, -1, -1, 0])


if __name__ == '__main__':
    unittest.main()
