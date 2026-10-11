"""Prepare screenshot-bound startup UI fixes; dry run before --apply."""
import argparse
import struct

from tools.common import ROOT, sha256, write_json
from tools import ui_catalog
from tools.ui_description_layout import advance
from tools.ui_coverage import member
from tools.pipeline import config, verified_source
from tools.aid_art import ARCHIVE

DEST = ROOT/'work/ui/startup_layout.json'
LINK_IDS = ('e7444b1f3927e291b6bd','b08119aa07f1754cf177','32f3c89ce347929c7573')
LINE_UNITS = 1180


def wrap_link(text):
    lines = []
    for paragraph in [text.replace('\n',' ')]:
        line = ''
        for word in paragraph.split():
            if sum(map(advance,word))>LINE_UNITS:
                raise ValueError('Link explanation word exceeds panel')
            joined = (line+' '+word).strip()
            if sum(map(advance,joined))>LINE_UNITS and line:
                lines.append(line)
                line = word
            else:
                line = joined
        if line:
            lines.append(line)
    if len(lines)>6 or '\n'.join(lines).split()!=text.split():
        raise ValueError('Link explanation exceeds six lines or lost words')
    return '\n'.join(lines)


def plan():
    grouped, translations = ui_catalog.checked()
    source = member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))
    by_widget = {at:r for r in ui_catalog.fssa_strings(source) for at in r['widget_offsets']}
    edits = []
    def bind(at,notes,**changes):
        row = by_widget[at]
        edits.append(dict(widget_offset=at,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            source_xy=list(struct.unpack_from('>ff',source,at+4)),notes=notes,**changes))
    for rid in LINK_IDS:
        for row in grouped[rid]:
            if row.get('member')!=0:
                continue
            for at in row['widget_offsets']:
                bind(at,'Wrap full explanation within six 38 px lines, preserving every word.',
                     en=wrap_link(translations[rid]['en']))
    # The centred wrapper measures Japanese before the draw-time substitution.
    # Keep the selector's original text/count/flags; move its anchor by the
    # difference between the Japanese and rendered English prefix before No.
    # Japanese prefix: two Yes glyphs, space, slash, space = 5 * 25 px.
    shift = (sum(map(advance,'Yes / '))*25/32 - 5*25)/640
    for at in (0x993c4,0x99444):
        x = struct.unpack_from('>f',source,at+4)[0]
        bind(at,'Align selected No with the grey English No; retain selector flags and original measurement.',x=x+shift)
    at = 0x91844
    bind(at,'Squad label ends before the editable name; English label with 16 px extra gap.',
         en='Squad:',x=struct.unpack_from('>f',source,at+4)[0]-.025)
    return dict(schema=1,source_member_sha256=sha256(source),edits=edits,
        link_layout=dict(line_units=LINE_UNITS,glyph_size=28,line_pitch=38,max_lines=6),
        viewport=dict(width=1280,height=720),runtime_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    data = plan()
    for edit in data['edits']:
        print(hex(edit['widget_offset']),repr(edit.get('en')),edit.get('x'))
    if args.apply:
        write_json(DEST,data)
        print('Wrote screenshot-bound startup UI plan.')
    else:
        print('DRY RUN: no files written.')


if __name__=='__main__':
    main()
