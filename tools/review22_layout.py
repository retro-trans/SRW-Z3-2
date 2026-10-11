"""Screenshot-bound labels with original Latin masks and unchanged live values."""
import argparse,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U,native_labels as N

DEST=ROOT/'work/translation/en/ui/review22_layout.json'

def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']};edits=[];bounds=[]
    def bind(at,en,x=None,quad=None,native=False,right=None):
        row=widgets[at]
        edit=dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),
            notes='Keep native colors, row pitch, state, and all separately drawn values.')
        if x is not None:edit['x']=(x-640)/640
        if quad is not None:
            metrics=list(source[at+16:at+21]);metrics[2]=quad-2;metrics[3]=quad
            edit['font_metrics']=metrics
        if native:edit['font_style']='native-label'
        if right is not None:
            left=x if x is not None else 640+struct.unpack_from('>f',source,at+4)[0]*640
            size=quad or source[at+19]
            span=max(N.width(line,size)for line in en.split('\n'))
            if left+span+6>right:raise ValueError('Label overlaps live value: '+en)
            bounds.append(dict(widget_offset=at,left=left,width=span,right=right,gap=right-left-span))
        edits.append(edit)
    for at in (0x955e4,0x95664):bind(at,'Z Chips for this effect.',x=500)
    from tools.review19_layout import width
    left=639.5-width('Yes / No',25)/2;no_left=left+width('Yes / ',25)
    for at,en,x in ((0x99384,'Yes',left),(0x993c4,'No',no_left),
                    (0x99404,'Yes',left),(0x99444,'No',no_left)):
        bind(at,en,x=x);edits[-1]['mode']=source[at+23]&~0x40
    for at,en,right in ((0x9bf04,'Team',224),(0x9bf24,'Funds',329),
                        (0x9bf44,'SR Points',373),(0x9bf64,'Top PP',719),
                        (0x9bf84,'Most Kills',719),(0x9bfa4,'Ace Pilots',846),
                        (0x9bfc4,'Emblems',570),(0x9bfe4,'Records',493)):
        bind(at,en,quad=26,native=True,right=right)
    bind(0x9c044,'')
    # These captions also form the prefix of the native composed footer.
    # Keep their 28px geometry, so the original colored overlay agrees.
    bind(0x9ba84,'Need:',native=True)
    bind(0x9baa4,'Effect:',native=True)
    bind(0x9df24,'Left  Total',x=1104,quad=24,native=True,right=1270)
    bind(0x9df44,'Type:',native=True,right=809)
    bind(0x9df64,'Move\n\n\n\nArmor\nMob.\nHit',quad=26,native=True,right=180)
    bind(0x9e044,'\n'*7+'Range\nEffect\n',quad=26,native=True,right=252)
    bind(0x9dfe4,'Team',x=72.5,quad=26,native=True,right=180)
    for at in (0x9dfa4,0x9e004,0x9e024):bind(at,'')
    bind(0x89964,'Terr.')
    bind(0x899a4,'Spec.')
    return dict(schema=1,version='0.5.22',source_member_sha256=sha256(source),edits=edits,
        bounds=bounds,original_latin_font_page=1,numeric_coordinates_changed=False,runtime_verified=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');a=ap.parse_args();data=plan()
    for e in data['edits']:print(hex(e['widget_offset']),repr(e['en']),e.get('font_style'))
    print('Minimum label/value gap:',min(b['gap']for b in data['bounds']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no layout data written.')

if __name__=='__main__':main()
