"""Colony Laser capitalization, clear Sub Order rewards and deployment captions."""
import argparse,json,re,struct
from tools.common import ROOT,sha256,write_json
from tools import battle_layout as B,ui_catalog as U
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/review44_layout.json'
HELP={'129fca590d7cb35d1a16':('・Select Team','　Select Team'),
      '67dd0320f2664ba08619':('・Prep Menu','　Prep Menu'),
      '80f1868d1e2f6456330f':('・Objectives','　Objectives'),
      'e06a31e6c49aeb8f9743':('・Map Deploy','　Map Deploy'),
      '0bc151d1b5822284c1bc':('・Quick Save','　Quick Save'),
      'abeeb2dda26512d24339':('Mech/Weapon Upgrades','Mech/Wpn Upg')}
REWARDS=((0x96584,0xb6884,84,'PP each:'),(0x965c4,0xb68a8,83,'Kills each:'),(0x96604,0xb68d8,85,'EXP each:'))
OLD_REWARDS={'2e81f68610c82c567824':'Each gained    PP.',
             '07ac4f9a377a056576a3':'Each shot down  enemies.',
             '33090075af7631ea8683':'Each gained    EXP.'}


def caption_encoded(text,mapping):
    """A 32-unit blank prefix composed only of measurable, invisible cells."""
    from tools import eboot_text as E
    prefix=E.encode('   ',mapping)+bytes.fromhex(mapping['@menu-pad:4'])+bytes.fromhex(mapping['@menu-pad:1'])
    out=[]
    for line in text.split('\n'):
        if not line:out.append(b'');continue
        if not line.startswith('　'):raise ValueError('Expected one logical deployment indent')
        out.append(prefix+E.encode(line[1:],mapping))
    return b'\n'.join(out)


def plan():
    source=B.source();widgets={a:r for r in U.fssa_strings(source)for a in r['widget_offsets']}
    edits=[];elements=[];bounds=[]
    def bind(at,en,**kw):
        row=widgets[at];edits.append(dict(widget_offset=at,en=en,source_sha256=sha256(row['raw']),
            source_widget_sha256=sha256(source[at:at+32]),**kw));return edits[-1]
    for at,element,style,en in REWARDS:
        bind(at,en,x=(476.5-640)/640,mode=source[at+23]&~0x40,
            notes='Unit-first per-pilot reward label; separate native value, preserve color, font and row height.')
        raw=source[element:element+12]
        if struct.unpack('>ffHBB',raw)[2:]!=(style,15,0):raise ValueError('Sub Order numeric element changed')
        elements.append(dict(element_offset=element,source_element_sha256=sha256(raw),x=(780-640)/640,
            notes='Move only the number endpoint; preserve the value, alignment style and animation.'))
        style_at=0xae784+style*20;state=source[style_at:style_at+20]
        if state[12:18]!=bytes.fromhex('111c0160000'+str({83:1,84:2,85:3}[style])):
            raise ValueError('Reward numeric geometry changed')
        # Conservative eight-digit number box: 17-unit digit pitch, 28-pixel quad.
        number_left=780-8*17+17-28-2
        right=476.5+sum(map(advance,en))*28/32
        if number_left-right<8:raise ValueError('Sub Order label crosses the native number')
        bounds.append(dict(widget_offset=at,label=en,left=476.5,right=right,number_left=number_left,
            minimum_gap=number_left-right,number_endpoint=780,numeric_style_offset=style_at,
            numeric_style_sha256=sha256(state)))
    for at in (0x979a4,0x979c4):
        if widgets[at]['text']!='・出撃選択へ':raise ValueError('Select Team source changed')
        bind(at,'　Select Team',blank_bullet=True,notes='Replace the menu bullet with 32 units of measurable invisible padding; retain indentation and selection states.')
    bind(0xab8a4,'\n　Prep Menu\n　Objectives\n　Map Deploy\n　Quick Save',
        blank_bullet=True,notes='Retain all five row positions and native indentation; replace bullet glyphs with measurable blank cells.')
    en='\nPilot Training\nPilot Swap\nMech/Wpn Upg\nPower Parts\nSwap Parts\nSearch'
    bind(0xab8c4,en,notes='Preload all submenu lines; shorten the upgrade caption in its existing native row.')
    left=640+struct.unpack_from('>f',source,0xab8c8)[0]*640
    for line in en.split('\n'):
        if not line:continue
        right=left+sum(map(advance,line))*source[0xab8c4+19]/32
        if right+6>518:raise ValueError('Deployment submenu label exceeds its button')
        bounds.append(dict(widget_offset=0xab8c4,label=line,left=left,right=right,button_right=518))
    reward_text={sha256(widgets[at]['text'].encode('utf8'))[:20]:en for at,_,_,en in REWARDS}
    return dict(schema=1,version='0.5.44',source_member_sha256=sha256(source),edits=edits,
        element_edits=elements,bounds=bounds,reward_catalog=reward_text,runtime_verified=False)


def corrections():
    out=[];path=ROOT/'work/glossary/library_terms.json';data=json.loads(path.read_text('utf8'))
    row=next(t for t in data['terms']if t['token']=='コロニーレーザー')
    if row['en']not in ('colony laser','Colony Laser'):raise ValueError('Conflicting Colony Laser term')
    if row['en']!='Colony Laser':
        row.update(en='Colony Laser',status='confirmed',source=row['source']+'; User correction 2026-10-15: Colony Laser, including headings and running speech.')
        out.append((path,data))
    for family in ('dialogue','library','ui'):
        for path in sorted((ROOT/'work/translation/en'/family).rglob('*.json')):
            if family=='ui'and 'expanded'not in path.parts and path.name!='eboot.json':continue
            data=json.loads(path.read_text('utf8'));changed=[0]
            def fix(value,key=None):
                if isinstance(value,dict):
                    for k,v in value.items():value[k]=fix(v,k)
                elif isinstance(value,list):value=[fix(v,key)for v in value]
                elif isinstance(value,str)and key in ('en','DSCR','DSC2'):
                    new=re.sub(r'\bcolony laser\b','Colony Laser',value,flags=re.I)
                    if new!=value:changed[0]+=1
                    value=new
                return value
            fix(data)
            if path.name=='help.json'and family=='ui':
                for rid,(old,new)in HELP.items():
                    row=data['strings'][rid]
                    if row['en']not in (old,new):raise ValueError('Deployment caption changed: '+rid)
                    if row['en']!=new:row.update(en=new,reviewed=True);changed[0]+=1
            if path.name=='menus.json'and family=='ui':
                for rid,en in plan()['reward_catalog'].items():
                    if data['strings'][rid]['en']!=en:data['strings'][rid].update(en=en,reviewed=True);changed[0]+=1
            if changed[0]:out.append((path,data));print(str(path.relative_to(ROOT)),changed[0],'fields')
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
    layout=plan();changes=corrections();print('Reward/menu bounds:',layout['bounds']);print('Changed files:',len(changes))
    if a.apply:
        for path,data in changes:write_json(path,data)
        write_json(DEST,layout)
    else:print('DRY RUN: no translation or layout data written.')

if __name__=='__main__':main()
