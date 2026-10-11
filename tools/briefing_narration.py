"""Source-bound military briefing captions; original rows and timing survive."""
import argparse
from tools.common import ROOT,sha256,write_json
from tools import opening_narration

MEMBER=26
MEMBER_SHA='b7e192b655b02f4c23f16d196427247b796f787b5b6d0535e884173862e638ec'
OFFSETS=(0x16c,0x1c2,0x218)
ENGLISH=(
    'Earth Federation forces: 34.8% of founding strength remaining.',
    'The chain of command is disrupted.',
    'Enemy Sidereal: strength, organization size, all else unknown.',
)
DEST=ROOT/'work/translation/en/ui/expanded/briefing.json'


def sources(blob):
    if sha256(blob)!=MEMBER_SHA:raise ValueError('Briefing source changed')
    rows=[]
    for at in OFFSETS:
        raw=blob[at:blob.index(0,at,at+86)]
        rows.append(dict(id='aid:26:%x'%at,family='opening',text=raw.decode('cp932'),
            raw=raw,encoding='cp932',offset=at,member=MEMBER,page=1))
    return rows


def plan():
    from tools.pipeline import config,verified_source
    from tools.ui_coverage import member
    from tools.aid_art import ARCHIVE
    rows=sources(member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE),MEMBER))
    return dict(schema=1,strings={sha256(row['text'].encode('utf8'))[:20]:dict(
        en=opening_narration.validate(en),reviewed=True,
        notes='Static military report; remaining strength is relative to the Federation founding. '
              'All three source rows reviewed together. Preserve row, timing and complete meaning; '
              'Sidereal follows the glossary. Intentional report fragments in rows 1 and 3.')
        for row,en in zip(rows,ENGLISH)})


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=plan()
    for rid,row in data['strings'].items():print(rid,row['en'],opening_narration.profile(row['en'])[1])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no translations written.')


if __name__=='__main__':main()
