"""Original trophy restoration must preserve the entire surrounding game."""
import unittest
from tools import cfw_trophy_control as C, trophy_text as T
from tools.common import sha256


class TrophyControlTests(unittest.TestCase):
    def test_source_difference_is_limited_to_two_localized_metadata_files(self):
        original, audit = C.audit()
        self.assertEqual(sha256(original), C.ORIGINAL_SHA)
        self.assertEqual(audit['changed_members'], ['TROP.SFM', 'TROP_00.SFM'])
        self.assertEqual(audit['original_member_count'], 40)
        for row in audit['comments']:
            self.assertEqual(row['original_comment_bytes'], [352])
            self.assertEqual(row['translated_comment_count'], 0)

    def test_native_config_ids_icons_and_comment_bytes_return_exactly(self):
        original, _ = C.audit()
        final = (C.OUTPUT/'TROPHY.TRP').read_bytes()
        self.assertEqual(final, original)
        for expected, actual in zip(T.unpack(original), T.unpack(final)):
            self.assertEqual(actual['header'], expected['header'])
            self.assertEqual(actual['data'], expected['data'])

    def test_completed_image_proof_changes_only_the_disc_trophy_package(self):
        proof = C.load(C.PROOF)
        self.assertEqual(proof['version'], '0.5.53')
        self.assertEqual(proof['changed_game_files'], [T.DISC])
        self.assertEqual(proof['unchanged_game_files'], 81)
        self.assertTrue(proof['executable_byte_identical'])
        self.assertTrue(proof['original_trophy_package_restored'])
        self.assertEqual(proof['title_artwork_version'], '0.5.52')
        self.assertFalse(proof['hardware_verified'])
        self.assertEqual(proof['iso_verification']['files_verified_each_tree'], 82)
        C.verify(proof['iso_verification'])


if __name__ == '__main__':
    unittest.main()
