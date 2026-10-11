"""Source-bound concluding narration; keep its two timed rows intact."""
import argparse
from tools.common import ROOT,sha256,write_json
from tools import fleet_narration as F,opening_narration as O

OFFSETS=(0x654,0x6a4)
ENGLISH=('It was the beginning of a new battle...',
         'the beginning of a battle without end.')
DEST=ROOT/'work/translation/en/ui/expanded/endless.json'


def sources(blob):
    if sha256(blob)!=F.MEMBER_SHA:raise ValueError('Concluding narration source changed')
    return [dict(id='aid:27:%x'%at,family='opening',member=27,page=2,offset=at,
        raw=blob[at:blob.index(0,at,at+80)],encoding='cp932',
        text=blob[at:blob.index(0,at,at+80)].decode('cp932'))for at in OFFSETS]


def plan():
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    rows=sources(member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),27))
    return dict(schema=1,strings={sha256(r['text'].encode('utf8'))[:20]:dict(
        en=O.validate(en),reviewed=True,
        notes='Meaning reviewed against seven surrounding source rows: three briefing, '
              'two fleet and these two concluding rows. Ominous narration following '
              'the fleet descent. Deliberate ellipsis and sentence continuation retained; '
              'second row inherits It was from the first. Original timing unchanged.')
        for r,en in zip(rows,ENGLISH)})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=plan()
    for rid,row in data['strings'].items():print(rid,row['en'],O.profile(row['en'])[1])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no translations written.')


if __name__=='__main__':main()
