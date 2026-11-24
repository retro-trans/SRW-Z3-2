"""Native execution and source isolation for the physical-PS3 diagnostic."""
import json
import unittest
from tools import cfw_package as B,cfw_self as C,cfw_voice_diagnostic as D
from tools import cfw_voice_diagnostic_check as V,srvc as S


class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=json.loads((B.OUTPUT/'build.json').read_text('utf8'))
        cls.original=C.extract_debug((B.OUTPUT/'EBOOT.BIN').read_bytes())
        cls.patched,cls.report=D.patch(cls.original,cls.build)

    def test_native_hooks_caption_builder_and_converter(self):
        report=V.verify(self.patched,self.original,self.build,self.report)
        self.assertEqual(report['poll_cases'],379)
        self.assertEqual(len(report['integration']),2)
        self.assertEqual(report['native_converter_models_verified'],4)

    def test_hook_source_drift_refused(self):
        bad=bytearray(self.original)
        bad[S.va_to_offset(bad,D.POLL)+3]^=1
        with self.assertRaises(ValueError):D.patch(bytes(bad),self.build)

    def test_occupied_headroom_refused(self):
        bad=bytearray(self.original)
        bad[S.va_to_offset(bad,self.report['state_va'])]=1
        with self.assertRaises(ValueError):D.patch(bytes(bad),self.build)

    def test_bank_table_and_converter_unchanged(self):
        self.assertEqual(S.read_table(self.patched),S.read_table(self.original))
        from tools import ui_hook as H
        self.assertEqual(H.unicode_table(self.patched),H.unicode_table(self.original))
        old=C.program_headers(self.original)[1]
        new=C.program_headers(self.patched)[1]
        self.assertEqual(old[:2],new[:2])
        self.assertEqual(old[3:],new[3:])
        self.assertEqual(new[2][3],old[2][3])


if __name__=='__main__':unittest.main()
