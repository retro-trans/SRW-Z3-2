import json,re,struct,tempfile,unittest
from pathlib import Path
from tools.common import ROOT
from tools import keyword_popup as K,library_build as B
from tools.pipeline import config,verified_source
from tools.cpkpatch import build as build_cpk

class KeywordPopupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping=json.loads((ROOT/'work/output/builds/0.5.40/build.json').read_text(encoding='utf8'))['mapping']
        cls.settings=config(ROOT/'config/tengoku.json');cls.plan=K.plan(cls.settings,cls.mapping)
        cls.original=cls.plan['original'];cls.final=cls.plan['members'][0]

    def test_public40_missed_the_actual_popup_archive(self):
        image=json.loads((ROOT/'work/output/iso/0.5.40/Tengoku-hen-English-0.5.40.json').read_text(encoding='utf8'))
        self.assertNotIn(K.DISC,image['replaced'])
        rows={r['id']:r for r in K.parse(self.original)['rows']}
        for tid in (27,35,37,97):
            self.assertRegex(rows[tid]['fields']['DSCR']['raw'].decode('cp932'),r'[\u3040-\u30ff\u3400-\u9fff]')

    def test_all_143_entries_and_both_variants_reach_the_native_records(self):
        result=K.verify(self.original,self.final,self.plan['rendered'],self.mapping)
        self.assertEqual((result['keywords'],result['description_variants']),(143,286))
        before,after=K.parse(self.original),K.parse(self.final)
        for old,new in zip(before['rows'],after['rows']):
            self.assertEqual((old['id'],old['flags']),(new['id'],new['flags']))
            for tag in ('WORD','SRCE'):self.assertEqual(old['fields'][tag],new['fields'][tag])
            for tag in ('DSCR','DSC2'):
                want=B.wrap(self.plan['rendered'][new['id']][tag],K.advance)
                self.assertEqual(B.decode(new['fields'][tag]['raw'],self.mapping),want)
                self.assertNotRegex(want,r'[\u3040-\u30ff\u3400-\u9fff]')
                self.assertTrue(all(sum(K.advance(c)for c in line)<=B.LINE_UNITS for line in want.splitlines()))

    def test_growth_retains_original_pool_trailer_and_loader_termination(self):
        a,b=K.parse(self.original),K.parse(self.final)
        self.assertEqual(b['pool'][:len(a['pool'])],a['pool'])
        self.assertEqual(b['pool'][len(a['pool'])],0)
        self.assertEqual(self.original[a['root_end']:],self.final[b['root_end']:])
        self.assertGreater(len(self.final),len(self.original))
        for row in b['rows']:
            for tag in ('DSCR','DSC2'):
                f=row['fields'][tag];self.assertEqual(b['pool'][f['offset']+f['bytes']],0)

    def test_loader_bounds_and_lookup_ids_are_guarded(self):
        row=K.parse(self.final)['rows'][0]
        bad=bytearray(self.final);struct.pack_into('<I',bad,row['record_offset']+16,0xffffffff)
        with self.assertRaisesRegex(ValueError,'bounds'):K.parse(bytes(bad))
        bad=bytearray(self.final);struct.pack_into('<I',bad,row['record_offset']+36,999)
        with self.assertRaisesRegex(ValueError,'IDs/flags'):K.parse(bytes(bad))
        bad=bytearray(self.final);bad[8]^=1
        with self.assertRaisesRegex(ValueError,'header'):K.parse(bytes(bad))

    def test_compressed_archive_reopens_with_complete_english_payload(self):
        with tempfile.TemporaryDirectory()as tmp:
            path=Path(tmp)/'keywords.cpk'
            build_cpk(verified_source(self.settings,K.DISC),path,self.plan['members'],compress=True)
            result=K.verify_archive(path,self.plan)
            self.assertEqual(result['description_variants'],286)

if __name__=='__main__':unittest.main()
