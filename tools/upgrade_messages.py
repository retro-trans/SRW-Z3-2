"""Source-table coverage of assembled D-Trader reports and upgrade questions."""
import argparse
import json
import struct
from tools.common import ROOT, sha256, write_json
from tools import ui_hook as H, eboot_text as E, rpw_text as R
from tools.ui_description_layout import advance

DEST=ROOT/'work/translation/en/ui/upgrade_messages.json'
CONDITIONS=(
    'Use Maximum Break', 'Clear Episode 12', None,
    'Earn over 10,000 Z Chips in total', 'Max out the Tactical Combo gauge',
    'Learn Commander at level 4', 'Obtain a Repair Kit, Propellant Tank and Cartridge',
    "Reduce an ally's HP to 20% or less", 'Earn over 3,000,000 funds in total',
    'Train an Ace Pilot', 'Deal over 15,000 damage in one battle',
    'Shoot down 5+ enemies at once with a MAP weapon',
    'Earn Custom Bonuses for 5 mechs', 'Train a pilot with at least 500 total PP earned',
    'Train a pilot with at least 120 SP', 'Use the Drive Spirit Command',
    'Obtain any Emblem', "Upgrade any mech's HP and EN to level 10",
    'Use the Valor Spirit Command', 'Use the Resupply Spirit Command',
    'Attack an enemy from 12 or more spaces away',
    'Learn both Support Atk and Support Def at level 3',
    'Upgrade the Z Crystal to Grade 3', 'Buy at least 5 standard items')
BONUSES={0x8553b0:'Unit/weapon Air ranks S',0x8553dc:'Unit/weapon Ground ranks S',
    0x855408:'Unit/weapon Water ranks S',0x855434:'Unit/weapon Space ranks S',
    0x855460:'Move +1',0x855470:'Weapon range +1',
    0x855486:'Barrier/Armor EN cost halved',0x8554c0:'Power Part slots +1',
    0x855504:'Song range +1'}


def cstring(read,va):
    return read(va,256).split(b'\0')[0]


def source_rows(elf):
    read=H._reader(elf,H._headers(elf)[2])
    # Native getter enumerates 24 records and selects the corresponding
    # condition pointer, including the one already-unlocked/null entry.
    if read(0x310328,16)!=bytes.fromhex('8102ea583800001880e2ea5c394000c0'):
        raise ValueError('D-Trader condition getter changed')
    if struct.unpack('>II',read(H.TOC-0x15a8,8))!=(0x855c0c,0xa2c058):
        raise ValueError('D-Trader source table binding changed')
    if read(0x31c7a8,4)!=bytes.fromhex('8002eb78'):
        raise ValueError('D-Trader report composer changed')
    if read(0x2e9518,20)!=bytes.fromhex('5463103a8122e6407c6307b47c69182e4e800020'):
        raise ValueError('Native bonus-choice getter changed')
    fragments={0x856134:'『',0x856138:'』',0x85613c:'を達成',
        0x856144:'Ｄトレーダーにて',0x856156:'「',0x85615a:'」',0x85615e:'発売',0x856164:'！'}
    for va,jp in fragments.items():
        if cstring(read,va)!=jp.encode('cp932'):raise ValueError('Report fragment changed')
    rows=[]
    names=R.load_names();parts={s['record']:s for s in R.slots(R.load_rpw())
                              if s['chunk']=='boost-p' and s['col']==1}
    for n,en in enumerate(CONDITIONS):
        pointer=struct.unpack('>I',read(0xa2c118+n*4,4))[0]
        if bool(pointer)!=bool(en):raise ValueError('Condition table population changed')
        raw=cstring(read,pointer) if pointer else b''
        record=read(0x855c0c+n*16,16)
        part=parts[struct.unpack_from('>I',record,4)[0]]
        item=R.text_for(part,names)
        if not item:raise ValueError('D-Trader part lacks reviewed name')
        rows.append(dict(index=n,condition_va=pointer,condition_sha256=sha256(raw),
            source_record_sha256=sha256(record),condition_en=en,
            part_record=part['record'],part_name_sha256=sha256(part['jp'].encode('cp932')),
            item_en=item,part_jp=part['jp'],condition_jp=raw.decode('cp932')))
    choices=[]
    table=struct.unpack('>11I',read(0xa26808,44))
    if set(table)-{0x8553a6,0x8554e2}!=set(BONUSES):raise ValueError('Bonus choice coverage changed')
    for va in table:
        if va not in BONUSES:continue
        raw=cstring(read,va)
        choices.append(dict(va=va,source_sha256=sha256(raw),en=BONUSES[va],jp=raw.decode('utf8')))
    for va,text in ((0x8555e2,'「'),(0x8555e6,'」を得ます。')):
        if cstring(read,va)!=text.encode('utf8'):raise ValueError('Bonus question fragment changed')
    return rows,choices


def plan():
    rows,choices=source_rows(H.PREPARED.read_bytes())
    for row in rows:row.pop('part_jp');row.pop('condition_jp')
    for row in choices:row.pop('jp')
    read=H._reader(H.PREPARED.read_bytes(),H._headers(H.PREPARED.read_bytes())[2])
    return dict(schema=1,version='0.5.20',conditions=rows,bonus_choices=choices,
        report_composer_sha256=sha256(read(0x31c798,0x1420)),
        bonus_composer_sha256=sha256(read(0x2f4570,0x780)),
        condition_count=sum(bool(r['condition_en'])for r in rows),item_count=len(rows))


def load():
    data=json.loads(DEST.read_text(encoding='utf8'))
    if data!=plan():raise ValueError('Upgrade message translations/source bindings are stale')
    return data


def characters():
    return set(''.join(r['condition_en'] or '' for r in plan()['conditions'])+
               ''.join(BONUSES.values())+'Condition met: .Now at D-Trader: Gain ""?')


def hook_entries(elf,mapping):
    load();rows,choices=source_rows(elf);out=[]
    def add(key,en,ident):
        width=sum(map(advance,en))*31/32
        if width>1040:raise ValueError('Assembled report exceeds text panel: '+en)
        if H.extent(key+b'\0')!=len(key):raise ValueError('Invalid assembled key')
        out.append(dict(id='upgrade:'+ident,key=key,english=E.encode(en,mapping)))
    for row in rows:
        if row['condition_en']:
            jp='『'+row['condition_jp']+'』を達成'
            add(jp.encode('cp932'),'Condition met: '+row['condition_en']+'.','condition:'+str(row['index']))
        prefix='Ｄトレーダーにて「'.encode('cp932');suffix='」発売！'.encode('cp932')
        # The item getter reads the RPW part name, which is already relocated
        # to native VWF English. Also cover the unpatched source-name route.
        en='Now at D-Trader: '+row['item_en']+'.'
        for kind,name in [('encoded',E.encode(row['item_en'],mapping)),
                          ('native',row['part_jp'].encode('cp932'))]:
            add(prefix+name+suffix,en,'item:'+str(row['index'])+':'+kind)
    for row in choices:
        jp='「'+row['jp']+'」を得ます。'
        add(H.utf8_key(jp.encode('utf8'),elf),'Gain "'+row['en']+'".','bonus:'+hex(row['va']))
    return list({r['key']:r for r in out}.values())


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');a=ap.parse_args()
    data=plan()
    for row in data['conditions']:print(row['index'],row['condition_en'],'=>',row['item_en'])
    print('Upgrade choices:',[r['en']for r in data['bonus_choices']])
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no translation data written.')

if __name__=='__main__':main()
