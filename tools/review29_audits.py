"""Preview/reconcile current weapon comparison after the canonical correction."""
import argparse,json
from tools.common import ROOT,write_json
from tools import review26_weapons as W

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    old=json.loads(W.DEST.read_text('utf8'));fresh,names=W.plan()
    if fresh['changes']:raise ValueError('Unapplied weapon names remain')
    kick=next(r for r in fresh['comparison']if r['source']=='イナズマキック')
    print('Inazuma Kick comparison:',kick)
    print('Remaining full-name exceptions:',len(fresh['full_name_exceptions']))
    old.update(comparison=fresh['comparison'],full_name_exceptions=fresh['full_name_exceptions'],
        canonical_revision=dict(version='0.5.29',term='Inazuma Kick',date='2026-10-14'))
    if not a.apply:print('DRY RUN: no evidence changed.');return
    write_json(W.DEST,old)

if __name__=='__main__':main()
