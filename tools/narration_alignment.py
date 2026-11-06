"""Center every timed narration row through the already installed renderer marker."""
import json
from tools.common import ROOT,sha256
from tools import narration_catalog as N,ui_catalog as U,opening_narration as O,eboot_text as E
from tools import dialogue_layout as A,review32_content as C
from tools.ui_description_layout import advance,condensed_advance

VERSION='0.5.50'

def clean(text):
 if '\n'in text or '\r'in text:raise ValueError('Timed narration must retain its single row')
 return text.strip('　 ')

def encode(text,mapping):
 """`mapping` already selects the ordinary or existing condensed alphabet."""
 if C.CAPTION_MARK not in mapping:raise ValueError('Narration requires the installed centering marker')
 return bytes.fromhex(mapping[C.CAPTION_MARK])+E.encode(clean(text),mapping)

def rows(mapping):
 from tools.pipeline import config,verified_source
 from tools.aid_art import ARCHIVE
 from tools.cpk import CPK
 grouped,english=U.checked();result=[]
 with CPK(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))as arc:source=N.sources(arc)
 for row in source:
  rid=sha256(row['text'].encode('utf8'))[:20]
  if any(r['family']!='opening'for r in grouped[rid]):raise ValueError('Narration key also serves non-narrative UI')
  en,condensed=O.profile(english[rid]['en']);selected=dict(mapping)
  if condensed:selected.update({k[len(A.PREFIX):]:v for k,v in mapping.items()if k.startswith(A.PREFIX)})
  text=clean(en);measure=condensed_advance if condensed else advance;span=sum(map(measure,text));width=span*40/32
  if not text or width>1160:raise ValueError('Timed narration exceeds fullscreen safe bounds')
  result.append(dict(id=row['id'],member=row['member'],record=row['record'],page=row['page'],translation_id=rid,
   key=row['raw'],old=E.encode(en,selected),encoded=encode(en,selected),en=text,condensed=condensed,span_units=span,
   left=640-width/2,right=640+width/2,glyph_quad=40))
 if len(result)!=197 or len({r['key']for r in result})!=189:raise ValueError('Timed narration source inventory differs')
 return result
