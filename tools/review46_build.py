"""Compile the six screenshot corrections with the complete active translations."""
import argparse,json
from tools.common import ROOT,sha256,write_json
from tools import game_build as G,ui_build as F
from tools.pipeline import config
BASE=ROOT/'work/output/builds/0.5.45'
VERSION='0.5.46'
def main():
 a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args()
 if G.VERSION!=VERSION:raise ValueError('Wrong current build version')
 p=G.plan(config(ROOT/'config/tengoku.json'));b=json.loads((BASE/'build.json').read_text('utf8'))
 if p['mapping']!=b['mapping']or p['summary']['latin_font']!=b['latin_font']:raise ValueError('Font allocation or ordinary lettering changed')
 if {c:w for c,(g,w)in p['drawn'].items()}!=b['widths']:raise ValueError('Letter spacing changed')
 glyphs={c:g for c,(g,w)in p['drawn'].items()}
 for fid,raw in p['pages'].items():
  if F.patch_font(raw,p['mapping'],glyphs)!=(BASE/('font_%d.bin'%fid)).read_bytes():raise ValueError('Font artwork changed')
 print('Full source plan passed. Existing letter shapes, outlines, mapping and spacing preserved.',flush=True)
 if args.apply:
  G.build(p,ROOT/'work/output/builds'/VERSION)
  print('Built and decoded the complete candidate.',flush=True)
 else:print('DRY RUN: no game assets written.')
if __name__=='__main__':main()
