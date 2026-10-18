"""Align the orange requirement word with its complete warning sentence."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance
VERSION='0.5.48'
DEST=ROOT/'work/translation/en/ui/review48_layout.json'
SENTENCE='The following requirements are not met.'
PREFIX='The following '
WORD='requirements'

def plan():
 s=B.source();widgets={a:r for r in U.fssa_strings(s)for a in r['widget_offsets']}
 width=lambda text:sum(map(advance,text))*28/32
 left=639.5-width(SENTENCE)/2;word=left+width(PREFIX);edits=[]
 for at,en,x,jp in ((0x99ac4,SENTENCE,left,'下記の使用条件を満たしていません。'),(0x99ae4,WORD,word,'使用条件')):
  row=widgets[at]
  if row['text']!=jp or s[at+19]!=28:raise ValueError('Weapon warning source changed')
  edits.append(dict(widget_offset=at,en=en,x=(x-640)/640,mode=s[at+23]&~0x40,
   source_sha256=sha256(row['raw']),source_widget_sha256=sha256(s[at:at+32]),
   notes='Measure both labels from the same English sentence; retain native orange emphasis, color and row geometry.'))
 return dict(schema=1,version=VERSION,source_member_sha256=sha256(s),edits=edits,
  bounds=dict(left=left,right=left+width(SENTENCE),word_left=word,word_right=word+width(WORD),quad=28,
   sentence=SENTENCE,highlight=WORD,available=1040),runtime_verified=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan();print(data['bounds'])
 if a.apply:write_json(DEST,data)
 else:print('DRY RUN: no layout data written.')
if __name__=='__main__':main()
