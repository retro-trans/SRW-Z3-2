"""Bind deployment labels and complete terrain blocks before native drawing."""
import argparse, struct
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U, status_layout as S, native_labels as N

DEST = ROOT/'work/translation/en/ui/review42_layout.json'


def plan():
    source = B.source()
    widgets = {a:r for r in U.fssa_strings(source) for a in r['widget_offsets']}
    edits = []; bounds = []
    def bind(at, en, note, native=True):
        row = widgets[at]
        edit = dict(widget_offset=at, en=en, source_sha256=sha256(row['raw']),
                    source_widget_sha256=sha256(source[at:at+32]), notes=note)
        if native: edit['font_style'] = 'native-label'
        edits.append(edit)
        return edit
    for at in (0x9e884, 0xa2044):
        if widgets[at]['text'] != '＜あと　　隊＞': raise ValueError('Deployment counter source changed')
        bind(at, 'Left:', 'Deploy Teams already supplies the noun. Clear the separate live count without moving it.')['x']=(340.5-640)/640
        x = 340.5
        width = N.width('Left:',source[at+19])
        if x+width > 425: raise ValueError('Remaining label touches the live count')
        bounds.append(dict(widget_offset=at, left=x, right=x+width, limit=425))
    for at in (0x9f044, 0xa31c4):
        if widgets[at]['text'] != '選択Ｎｏ．': raise ValueError('Selection heading changed')
        bind(at, 'Sel.', 'Short selection heading clears the separately positioned Team heading.')
        x = 640+struct.unpack_from('>f',source,at+4)[0]*640
        width = N.width('Sel.',source[at+19])
        if x+width > 110: raise ValueError('Selection heading touches Team')
        bounds.append(dict(widget_offset=at, left=x, right=x+width, limit=110))
    for at in (0x9eea4, 0xa2984):
        if widgets[at]['text'] != '移動': raise ValueError('Movement footer changed')
        bind(at, 'MV', 'Short movement label clears the existing bracket and value.')
        width = N.width('MV',source[at+19])
        if 361.5+width > 410: raise ValueError('Movement label touches the bracket')
        bounds.append(dict(widget_offset=at, left=361.5, right=361.5+width, limit=410))
    # These widgets are whole ten-row columns, two-row footers and padded
    # status blocks. The old single-row matcher did not translate them.
    for at,row in widgets.items():
        lines = row['text'].split('\n')
        if len(lines)<2 or not any(line=='空陸水地' for line in lines): continue
        if any(line and line!='空陸水地' and line.strip('　') for line in lines):
            raise ValueError('Mixed movement block needs a separate binding')
        en = ''.join(S.TERRAIN.get(c,c) for c in row['text'])
        bind(at,en,'Translate every terrain cell, retaining rows, blank padding, pitch and per-cell active/dim state.',False)
    blocks = [e for e in edits if 'font_style' not in e]
    if len(blocks)!=7: raise ValueError('Movement block inventory changed')
    return dict(schema=1,version='0.5.42',source_member_sha256=sha256(source),edits=edits,
                bounds=bounds,terrain_blocks=len(blocks),terrain_rows=sum(e['en'].count(S.CELL['Air']) for e in blocks),
                numeric_fields_changed=False,runtime_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for row in data['edits']:print(hex(row['widget_offset']),repr(row['en']))
    print('Terrain blocks/rows:',data['terrain_blocks'],data['terrain_rows']);print('Bounds:',data['bounds'])
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
