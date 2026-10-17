"""Compile the reported names, trader question and Sphere fixes on current sources."""
import argparse,json
from tools.common import ROOT
from tools import game_build as G,ui_build as F
from tools.pipeline import config
BASE=ROOT/'work/output/builds/0.5.46'
VERSION='0.5.47'

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
 if G.VERSION!=VERSION:raise ValueError('Wrong build version')
 data=G.plan(config(ROOT/'config/tengoku.json'));b=json.loads((BASE/'build.json').read_text('utf8'))
 if data['mapping']!=b['mapping']or data['summary']['latin_font']!=b['latin_font']:raise ValueError('Font allocation or lettering changed')
 if {c:w for c,(g,w)in data['drawn'].items()}!=b['widths']:raise ValueError('Letter spacing changed')
 glyphs={c:g for c,(g,w)in data['drawn'].items()}
 for fid,raw in data['pages'].items():
  if F.patch_font(raw,data['mapping'],glyphs)!=(BASE/('font_%d.bin'%fid)).read_bytes():raise ValueError('Font artwork changed')
 print('Complete source plan passed; font artwork, codes and spacing preserved.',flush=True)
 if args.apply:G.build(data,ROOT/'work/output/builds'/VERSION);print('Compiled and decoded the complete candidate.',flush=True)
 else:print('DRY RUN: no game assets written.')
if __name__=='__main__':main()
