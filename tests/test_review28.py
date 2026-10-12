"""Exercise the native map quote selector, state stores and source guards."""
import json,unittest
from tools import review28_quotes as Q,ui_hook as H,vwf


class DefeatQuotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=H.PREPARED.read_bytes();cls.planned=Q.plan(cls.source)
        # The native pointer/store oracle does not require a previous build.
        cls.mapping={chr(c):format(0xe040+n,'04x')for n,c in enumerate(range(32,127))}
        patched,_=vwf.patch(cls.source,{})
        patched,info=H.apply(patched,[],Q.payloads(cls.planned,cls.mapping))
        cls.final,cls.report=Q.apply(patched,cls.planned,info['table']['payload_vas'])

    def test_native_selector_and_state(self):
        evidence=Q.verify(self.final,self.planned,self.mapping)
        self.assertEqual(len(evidence['store_cases']),249)
        self.assertEqual(evidence['aliases_preserved'],1)
        self.assertGreaterEqual(len(evidence['selector_cases']),250)
        self.assertEqual(evidence['store_cases'][67]['english'],'「Damn!\n This disgraces the Tri-Stars...!」')

    def test_guards_reject_selection_and_source_drift(self):
        for va in (Q.TABLE,Q.TOC_SLOT,Q.GETTER[0],Q.STORE[0],Q.COMPOSER[0]):
            bad=bytearray(self.source);bad[va-0x10000]^=1
            with self.assertRaises(ValueError):Q.plan(bytes(bad))

    def test_native_copy_buffer_and_panel(self):
        self.assertEqual(self.planned['distinct_quotes'],178)
        for row in self.planned['rows']:
            self.assertLessEqual(row['composition_reserved_bytes'],256)
            self.assertLessEqual(max(row['row_widths']),960)
            self.assertLessEqual(len(row['row_widths']),3)

    def test_saved_audit_matches_current_quote_plan(self):
        self.assertEqual(json.loads(Q.DEST.read_text(encoding='utf8')),self.planned)

if __name__=='__main__':unittest.main()
