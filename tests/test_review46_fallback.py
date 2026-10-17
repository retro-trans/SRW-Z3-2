"""Exercise empty and live pilot-name consumers without changing the font or saves."""
import json,unittest,struct
from tools.common import ROOT
from tools import review46_fallback as F,ui_hook as H
class EmptyPilotNameEncoding(unittest.TestCase):
 def test_native_fallbacks_and_live_names_use_the_expected_bytes(self):
  folder=ROOT/'work/output/builds/0.5.45';b=json.loads((folder/'build.json').read_text('utf8'))
  elf=(folder/'EBOOT.BIN').read_bytes();out,report=F.apply(elf,b['executable']['ui_hook']['table'])
  checks=F.native_cases(out)
  self.assertEqual(len(checks),12)
  self.assertEqual(sum(c.get('live_name_pointer_preserved',False)for c in checks),3)
  restored=bytearray(out)
  for a,z in report['modified_file_ranges']:restored[a:z]=elf[a:z]
  self.assertEqual(bytes(restored),elf)
  rd=H._reader(out,H._headers(out)[2])
  for c in report['cases']:
   self.assertEqual(rd(c['original_va'],len(bytes.fromhex(c['before_hex']))),bytes.fromhex(c['before_hex']))
   self.assertEqual(rd(c['patched_va'],len(bytes.fromhex(c['after_hex']))),bytes.fromhex(c['after_hex']))
 def test_unexpected_fallback_source_is_rejected(self):
  folder=ROOT/'work/output/builds/0.5.45';b=json.loads((folder/'build.json').read_text('utf8'));elf=bytearray((folder/'EBOOT.BIN').read_bytes())
  at=H.TOC+F.CASES[0][0]-0x10000;elf[at:at+4]=bytes(4)
  with self.assertRaisesRegex(ValueError,'binding changed'):F.apply(bytes(elf),b['executable']['ui_hook']['table'])
if __name__=='__main__':unittest.main()
