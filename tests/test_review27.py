import unittest
from tools import dialogue as Q,dialogue_build as D,review27_dialogue as A,review27_messages as M,review27_names as N,ui_hook as H

class Review27(unittest.TestCase):
    def test_fullwidth_runtime_team_fits(self):
        # Both the source validator and builder must wrap the rendered name,
        # including in a condensed Latin profile where its native cells stay full.
        w=lambda c:16
        lines=D.wrap_speech(' '.join(['$c']*5),w)
        self.assertEqual(len(lines),2)
        for i,line in enumerate(lines):self.assertLessEqual(Q.speech_units(line,w)+(32 if i else 0),Q.BOX_UNITS)
        self.assertEqual(Q.speech_units('$c',lambda c:1),192)
        self.assertEqual(Q.speech_units('$n',w),144)
        self.assertEqual(Q.speech_units('$$c$$',w),80)

    def test_source_team_name_guard(self):
        elf=H.PREPARED.read_bytes();A.guard(elf)
        changed=bytearray(elf);changed[A.TEAM_OFFSET]^=1
        with self.assertRaisesRegex(ValueError,'Native team'):A.guard(changed)

    def test_all_save_lines_and_source_bindings(self):
        rows=M.plan();self.assertEqual(rows['line_occurrences'],6)
        self.assertEqual(rows['strings']['このままゲームを続けますか？']['en'],'Continue playing?')
        from tools.library_build import characters
        mapping={c:format(0xe040+n,'04x')for n,c in enumerate(sorted(set(''.join(r['en']for r in rows['strings'].values()))))}
        elf=H.PREPARED.read_bytes();keys=M.hook_entries(elf,mapping);self.assertEqual(len(keys),5)
        changed=bytearray(elf);changed[0x882748]^=1
        with self.assertRaisesRegex(ValueError,'Save message bytes'):M.hook_entries(changed,mapping)

    def test_canonical_word_boundaries(self):
        self.assertEqual(N.corrected('Emperor Xul, Zul and Xul\'s avatar.'),"Emperor Zuul, Zuul and Zuul's avatar.")
        self.assertEqual(N.corrected('Geara Zulu / Rozen Zulu'),'Geara Zulu / Rozen Zulu')

if __name__=='__main__':unittest.main()
