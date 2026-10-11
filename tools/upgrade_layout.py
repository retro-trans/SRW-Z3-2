"""Compose each two-color bonus award once, preserving native styles."""
import argparse,json,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.review19_layout import width

DEST=ROOT/'work/translation/en/ui/upgrade_layout.json'

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits=[];lines=[]
    for tail_at,subject_at,subject in ((0x8bee4,0x8bf04,'Custom Bonus'),
                                      (0x9a004,0x9a024,'Custom Bonus'),
                                      (0x99de4,0x99e04,'Ace Bonus')):
        tail=' obtained.'
        center=640+struct.unpack_from('>f',source,tail_at+4)[0]*640
        start=center-(width(subject)+width(tail))/2
        for at,en,x in ((subject_at,subject,start),(tail_at,tail,start+width(subject))):
            row=widgets[at]
            edits.append(dict(widget_offset=at,en=en,x=(x-640)/640,
                mode=source[at+23]&~0x40,source_sha256=sha256(row['raw']),
                source_widget_sha256=sha256(source[at:at+32]),
                notes='Measured two-color award; preserve native font, color, icon, y and row pitch.'))
        lines.append(dict(subject=subject,subject_at=subject_at,tail_at=tail_at,
                          left=start,join=start+width(subject),right=start+width(subject)+width(tail),center=center))
    return dict(schema=1,version='0.5.20',source_member_sha256=sha256(source),edits=edits,lines=lines,runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();d=plan()
    for r in d['lines']:print(r)
    if a.apply:write_json(DEST,d)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
