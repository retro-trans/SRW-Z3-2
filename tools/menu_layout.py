"""Preview screenshot-bound map-menu, report and settings widget repairs."""
import argparse
import struct
from tools.common import ROOT, sha256, write_json
from tools import ui_catalog
from tools.ui_coverage import member
from tools.pipeline import config, verified_source
from tools.aid_art import ARCHIVE
from tools.ui_description_layout import advance

DEST = ROOT/'work/translation/en/ui/menu_layout.json'
COMMAND_CENTER = 1140.0
COUNTER_SHIFT = -64.0
PADS = {'@menu-pad:1':1,'@menu-pad:2':2,'@menu-pad:4':4}
COMMAND_LEFT = 1030.0


def encode(edit,mapping):
    from tools.eboot_text import encode as plain
    if edit.get('blank_bullet'):
        from tools.review44_text import caption_encoded
        return caption_encoded(edit['en'],mapping)
    if 'icon_column' in edit:
        from tools.review32_layout import guide_encoded
        return guide_encoded(edit,mapping)
    if edit.get('font_style')=='native-label':
        from tools.native_labels import PREFIX
        selected=dict(mapping)
        for char in set(edit['en'])-{'\n'}:selected[char]=mapping[PREFIX+char]
        return plain(edit['en'],selected)
    if 'line_center' not in edit: return plain(edit['en'],mapping)
    spec=edit['line_center']; out=[]
    if spec['quad']!=31 or spec['center_x']!=COMMAND_CENTER or spec['left_x']!=COMMAND_LEFT:
        raise ValueError('Command geometry changed')
    for line in edit['en'].split('\n'):
        if not line: out.append(b''); continue
        units=sum(map(advance,line))
        padding=round((spec['center_x']-spec['left_x'])*32/spec['quad']-units/2)
        if padding<0 or units*spec['quad']/32>220: raise ValueError('Command caption exceeds button')
        spaces,remainder=divmod(padding,advance(' '))
        prefix=plain(' '*spaces,mapping)
        for value in (4,2,1):
            while remainder>=value:
                prefix+=bytes.fromhex(mapping['@menu-pad:%d'%value]); remainder-=value
        out.append(prefix+plain(line,mapping))
    return b'\n'.join(out)


def plan():
    source = member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))
    widgets = {at:r for r in ui_catalog.fssa_strings(source) for at in r['widget_offsets']}
    edits = []
    def bind(at, expected, note, **changes):
        row = widgets[at]
        if row['text'] != expected: raise ValueError('Menu source changed: %#x'%at)
        edits.append(dict(widget_offset=at,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            source_xy=list(struct.unpack_from('>ff',source,at+4)),notes=note,**changes))
    bind(0xab904,'\n　　検索\n\n　作戦目的\n　戦況報告\n　システム\n',
         'Center every nonempty command line in the native button column.',
         x=(COMMAND_LEFT-640)/640,en='\nSearch\n\nObjectives\nBattle Report\nSystem\n',
         line_center=dict(center_x=COMMAND_CENTER,left_x=COMMAND_LEFT,quad=31))
    bind(0xab924,'\n　　\n　部隊表\n　\n\n\n途中セーブ',
         'Center Unit List and Quick Save in the same column; retain blank lines.',
         x=(COMMAND_LEFT-640)/640,en='\n\nUnit List\n\n\n\nQuick Save',
         line_center=dict(center_x=COMMAND_CENTER,left_x=COMMAND_LEFT,quad=31))
    for at in range(0x96e24,0x96f24,32):
        n=1 if (at-0x96e24)//32%2==0 else 2
        bind(at,'システム設定'+chr(0xff10+n),
             'Shorten both tab labels in every native selection/visibility state.',en='Settings %d'%n)
    for at in (0x96f64,0x97144):
        bind(at,'特殊能力','Shorten the Spirit-screen ability tab; keep its center and state.',en='Abilities')
    bind(0x98564,'総壊滅チーム数\n　　　総撃墜数\n　　　被撃墜数',
         'Retain cumulative team/unit statistics with a shorter first caption.',
         en='Teams Defeated\nTotal Kills\nUnits Lost')
    at=0x98544
    bind(at,'隊','Move the team-count suffix 64 native pixels left with its separate numeric element.',
         x=struct.unpack_from('>f',source,at+4)[0]+COUNTER_SHIFT/640)
    # Type 15 elements select 20-byte numeric styles, independently of text
    # widgets. Style 45 uses right alignment: its endpoint and the suffix
    # must move together. Adjacent elements are the unit kills/loss counters.
    at=0xb7fb8
    raw=source[at:at+12]
    if struct.unpack('>ffHBB',raw)[2:]!=(45,15,0):
        raise ValueError('Team numeric element changed')
    elements=[dict(element_offset=at,source_element_sha256=sha256(raw),
        source_xy=list(struct.unpack_from('>ff',raw)),
        x=struct.unpack_from('>f',raw)[0]+COUNTER_SHIFT/640,
        notes='Move the right-aligned live team number with its Teams suffix; preserve numeric style and value.')]
    return dict(schema=1,version='0.5.7',source_member_sha256=sha256(source),edits=edits,
        element_edits=elements,
        viewport=dict(width=1280,height=720),
        command_center=COMMAND_CENTER,counter_shift=COUNTER_SHIFT,
        short_caption_widths={s:sum(map(advance,s))*size/32 for s,size in
            [('Teams Defeated',25),('Settings 1',31),('Settings 2',31),('Abilities',31)]},
        runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--apply',action='store_true')
    args=ap.parse_args(); data=plan()
    for row in data['edits']:
        print(hex(row['widget_offset']),repr(row.get('en')),row.get('x'),row.get('centered'))
    for row in data['element_edits']:
        print('Numeric element',hex(row['element_offset']),row['source_xy'],'-> x',row['x'])
    print('Caption widths:',data['short_caption_widths'])
    if args.apply: write_json(DEST,data)
    else: print('DRY RUN: no translations or layout data written.')


if __name__=='__main__': main()
