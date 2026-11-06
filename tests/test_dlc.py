"""Source-bound acceptance of the supplied DLC, native scripts and licensed EDATs."""
import json,unittest,zipfile
from unittest.mock import patch
from tools import dlc,dlc_text as T,dlc_build as B,dlc_edat as E,dlc_verify as V,dlc_ui as U
from tools.common import ROOT,sha256
from tools.pipeline import sfo_values

class DLC(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packages=sorted(T.inventory()['packages'],key=lambda p:p['code']);cls.rendered,cls.coverage=T.check()
  cls.mapping=json.loads((B.BASE/'build.json').read_text('utf8'))['mapping']

 def test_complete_source_bound_authoring(self):
  self.assertEqual(self.coverage,dict(total=4666,translated=4666,rendered=4666,errors=[],missing=[]))
  self.assertEqual(len(T.jobs()),78)
  self.assertEqual({p['code']for p in self.packages},{'DLC'+str(n)for n in range(2301,2332)}|{'DLC2334'})
  ui=U.plan();self.assertEqual(ui,json.loads(U.DEST.read_text('utf8')))
  self.assertEqual(tuple(len(ui[k])for k in ('titles','missions','names')),(32,16,146))
  from tools.library_text import apply_settled
  terms=[];apply_settled(terms)
  for row in json.loads((ROOT/'work/glossary/research/dlc_terms.json').read_text('utf8'))['terms']:
   term=next(t for t in terms if t.get('token')==row['token'])
   self.assertEqual(term['en'],row['en']);self.assertEqual(term['targets'],[])

 def test_wrong_source_fingerprint_rejected(self):
  answers=T.answers();rid=next(iter(answers));answers[rid]=dict(answers[rid],sha='not-the-source')
  with patch.object(T,'answers',return_value=answers):
   _,report=T.check()
  self.assertEqual([r['id']for r in report['errors']],[rid])

 def test_all_retail_packages_keep_identity(self):
  sources=dlc.sources();self.assertEqual(len(sources),32)
  for source in sources:
   p=next(p for p in self.packages if p['content_id']==source['cid'])
   self.assertEqual(source['pkg_sha256'],p['pkg_sha256']);self.assertEqual(source['zip_sha256'],p['zip_sha256'])
   self.assertEqual(sha256(source['edat']['data']),p['edat_sha256'])
   self.assertEqual(source['sfo']['TITLE_ID'],'NPJB00692')
  with zipfile.ZipFile(sources[0]['path'])as z:raw=z.read(sources[0]['pkg_name'])
  for broken in (b'',raw[:127],raw[:-1]):
   with self.assertRaises(ValueError):dlc.package(broken)

 def test_all_licensed_edat_authentication_and_roundtrip(self):
  for p in self.packages:
   code=p['code'];name=code+'.EDAT';folder=dlc.WORK/code
   raw=(folder/'package/USRDIR/DLC'/name).read_bytes();rap=(folder/'license.rap').read_bytes()
   plain,auth=E.decode(raw,rap,name,True)
   self.assertEqual(sha256(plain),p['cpk_sha256']);self.assertTrue(auth['metadata_authenticated'])
   encoded,result=E.rebuild(raw,plain,rap,name)
   self.assertEqual(encoded[:128],raw[:128]);self.assertEqual(encoded[176:256],bytes(80))
   self.assertEqual(E.decode(encoded,rap,name,True)[0],plain);self.assertEqual(result['license'],2)
   self.assertFalse(result['sony_signature'])

 def test_wrong_license_filename_and_corruption_rejected(self):
  p=self.packages[0];code=p['code'];folder=dlc.WORK/code;name=code+'.EDAT'
  raw=(folder/'package/USRDIR/DLC'/name).read_bytes();rap=(folder/'license.rap').read_bytes()
  with self.assertRaises(ValueError):E.decode(raw,bytes(16),name,True)
  with self.assertRaises(ValueError):E.decode(raw,rap,'WRONG.EDAT',True)
  for offset in (144,160,256,300):
   broken=bytearray(raw);broken[offset]^=1
   with self.assertRaises(ValueError):E.decode(bytes(broken),rap,name,True)
  for broken in (raw[:128],raw[:-1],raw+b'\0'):
   with self.assertRaises(ValueError):E.decode(broken,rap,name,True)

 def test_caption_roles_and_complete_condensed_speech(self):
  source={r['id']:r for r in T.all_rows()}
  for rid,text in self.rendered.items():
   caption=not source[rid]['jp'].partition('\n')[0].strip('　 ')
   if caption:self.assertFalse(text.partition('\n')[0].strip('　 '))
  text=self.rendered[T.CONDENSED_ID]
  spoken=' '.join(text.partition('\n')[2].split())
  for phrase in ('Land, sea, air','morning, noon, night','run, attack, defend','money, power, women','mother, belly, pay packet','voter base, funds, name recognition'):self.assertIn(phrase,spoken)
  self.assertEqual(len(text.splitlines())-1,3)
  self.assertNotEqual(T.encode_record(T.CONDENSED_ID,text,self.mapping),T.encode_record('ordinary',text,self.mapping))

 def test_system_metadata_changes_only_player_titles(self):
  for p in self.packages:
   raw=(dlc.WORK/p['code']/'package/PARAM.SFO').read_bytes();old=sfo_values(raw);new=sfo_values(B.english_sfo(raw))
   self.assertEqual(set(old),set(new))
   self.assertEqual({k:v for k,v in old.items()if k not in ('TITLE','TITLE_00')},{k:v for k,v in new.items()if k not in ('TITLE','TITLE_00')})
   self.assertTrue(all('English 0.5.49'in new[k]for k in ('TITLE','TITLE_00')))

 def test_final_assets_text_and_program_readback(self):
  report=V.verify();self.assertEqual(report['counts']['dialogue'],4666)
  self.assertEqual(report['counts']['titles'],32);self.assertEqual(len(report['packages']),32)
  self.assertEqual(report['counts']['internal_long_strings_preserved'],357)
  self.assertFalse(report['runtime_verified'])

if __name__=='__main__':unittest.main()
