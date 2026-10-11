"""Explicit Latin ON/OFF choice widgets, preserving their native centers."""
import argparse
import struct
from tools.common import ROOT,sha256,write_json
from tools import ui_catalog as U,battle_layout as B

DEST=ROOT/'work/translation/en/ui/settings_layout.json'


def plan():
    source=B.source();edits=[]
    for row in U.fssa_strings(source):
        if row['text']not in ('ＯＮ','ＯＦＦ'):continue
        for at in row['widget_offsets']:
            edits.append(dict(widget_offset=at,source_sha256=sha256(row['raw']),
                source_widget_sha256=sha256(source[at:at+32]),
                source_xy=list(struct.unpack_from('>ff',source,at+4)),en=row['text'].translate(
                    str.maketrans('ＯＮＦ','ONF')),notes='Use the same outlined Latin alphabet; native centered choice mode and selection state retained.'))
    return dict(schema=1,version='0.5.15',source_member_sha256=sha256(source),edits=edits,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),row['en'])
    if args.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')


if __name__=='__main__':main()
