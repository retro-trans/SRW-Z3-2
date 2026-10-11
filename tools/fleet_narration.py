"""Source-bound enemy-fleet narration; preserve fixed rows and timing."""
import argparse
from tools.common import ROOT,sha256,write_json
from tools import opening_narration

MEMBER=27
MEMBER_SHA='8e046c881365f6fb4436d7bb2a4f64a8af18c41b03b69dd6deb0234f63c62c52'
OFFSETS=(0x1a4,0x1f4)
ENGLISH=(
    'Breaching absolute defense lines on all fronts, the enemy fleet',
    'descended toward Earth.',
)
DEST=ROOT/'work/translation/en/ui/expanded/fleet.json'


def sources(blob):
    if sha256(blob)!=MEMBER_SHA:raise ValueError('Fleet narration source changed')
    rows=[]
    for at in OFFSETS:
        raw=blob[at:blob.index(0,at,at+80)]
        rows.append(dict(id='aid:27:%x'%at,family='opening',text=raw.decode('cp932'),
            raw=raw,encoding='cp932',offset=at,member=MEMBER,page=1))
    return rows


def plan():
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    rows=sources(member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),MEMBER))
    return dict(schema=1,strings={sha256(row['text'].encode('utf8'))[:20]:dict(
        en=opening_narration.validate(en),reviewed=True,
        notes='Narration: enemy fleet approaching Earth after the Federation military report. '
              'Both source rows and the following two-row page examined. Meaning review preserves '
              'all fronts, absolute defense lines, enemy fleet subject and descent toward Earth. '
              'Intentional sentence continuation at the source row break; timing unchanged.')
        for row,en in zip(rows,ENGLISH)})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=plan()
    for rid,row in data['strings'].items():print(rid,row['en'],opening_narration.profile(row['en'])[1])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no translations written.')


if __name__=='__main__':main()
