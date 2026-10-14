"""Source-bound Sub Order labels and Back Log guides, around fixed numbers/icons."""
import argparse, struct
from tools.common import ROOT, sha256, write_json
from tools import battle_layout as B, ui_catalog as U, native_labels as N
DEST = ROOT/'work/translation/en/ui/review32_layout.json'


def plan():
    source = B.source(); widgets = {at:r for r in U.fssa_strings(source) for at in r['widget_offsets']}
    edits = []
    def bind(at, english, note, native=False):
        row = widgets[at]
        edit = dict(widget_offset=at, source_sha256=sha256(row['raw']),
                    source_widget_sha256=sha256(source[at:at+32]), en=english, notes=note)
        if native: edit['font_style'] = 'native-label'
        edits.append(edit)
    bind(0x963c4, 'Undeployed:\nCapacity:', 'Clear both fixed numeric fields and retain the native row pitch.', True)
    bind(0x963e4, 'L:', 'Left/remaining abbreviation between the capacity and remaining numeric fields.', True)
    edits[-1]['x']=(254.5-640)/640
    for at in (0x96404, 0x96424):
        bind(at, '', 'Suppress a separately drawn Japanese pilot-word fragment; the complete label is in the main row.')
    bind(0x95f24, ': Fill Slots', 'Fit the guide after Square + R1 without moving either icon.')
    bind(0x95f64, ': Switch Mode', 'Fit the guide after Start inside the grey panel.')
    for at in (0x8bb04, 0x9a1a4):
        bind(at, ': Prev Line\n: Next Line', 'Keep the two rows clear of the quote-guide column.')
    for at in (0x8bb24, 0x9a1c4):
        bind(at, ': Prev Quote (+        : Fast)\n: Next Quote (+        : Fast)', 'Preserve the R1 icon gap in both quote rows.')
        edits[-1]['icon_column'] = dict(left=647.5, suffix=906.5, quad=28,
                                       prefixes=[': Prev Quote (+', ': Next Quote (+'], suffix_text=': Fast)')
    bind(0xa4be4,'MV\nMV','Clear the separately drawn movement brackets in both footer rows.',True)
    edits[-1]['x']=(459.5-640)/640
    # Existing R1 centers: about 878 pixels; the right guide begins at 648.
    # Keep the prefix before the icon, then a blank gap and the Fast suffix.
    from tools.ui_description_layout import advance
    bounds = []
    for label, text, size, width in (('pilot label', 'Undeployed:', 25, 190),
                                   ('capacity label', 'Capacity:', 25, 140),
                                   ('remaining label', 'L:', 25, 28),
                                   ('mode guide', ': Switch Mode', 25, 275),
                                   ('line guide', ': Prev Line', 28, 235),
                                   ('quote guide', ': Prev (+', 28, 200)):
        span = sum((N.raster(c)[1] if label in ('pilot label','capacity label','remaining label') else advance(c))
                   for c in text)*size/32
        if span > width: raise ValueError('Review32 label exceeds its numeric/icon boundary')
        bounds.append(dict(label=label, pixels=span, available=width))
    movement_gap=504.5-459.5-sum(N.raster(c)[1]for c in 'MV')*22/32
    if movement_gap<7:raise ValueError('Team Setup movement header crosses its bracket')
    bounds.append(dict(label='movement bracket gap',pixels=movement_gap,available=45))
    return dict(schema=1, version='0.5.32', source_member_sha256=sha256(source),
                edits=edits, bounds=bounds, numeric_fields_changed=False, runtime_verified=False)


def guide_encoded(edit, mapping):
    from tools.eboot_text import encode
    from tools.ui_description_layout import advance
    spec = edit['icon_column']; out = []
    for prefix in spec['prefixes']:
        used = sum(map(advance, prefix))
        padding = round((spec['suffix']-spec['left'])*32/spec['quad'])-used
        if padding < 56: raise ValueError('Back Log guide leaves no safe icon gap')
        count, remaining = divmod(padding, advance(' '))
        raw = encode(prefix+' '*count, mapping)
        for value in (4,2,1):
            while remaining >= value:
                raw += bytes.fromhex(mapping['@menu-pad:'+str(value)]); remaining -= value
        out.append(raw+encode(spec['suffix_text'], mapping))
    return b'\n'.join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
    data = plan()
    for row in data['edits']: print(hex(row['widget_offset']), repr(row['en']))
    print('Bounds:', data['bounds'])
    if a.apply: write_json(DEST, data)
    else: print('DRY RUN: no layout data written.')


if __name__ == '__main__': main()
