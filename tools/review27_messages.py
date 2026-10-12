"""Source-bound individual lines of the three map save confirmations."""
import argparse,json
from tools.common import ROOT,sha256,write_json
from tools import eboot_text as E,ui_hook as H,library_build as L

DEST=ROOT/'work/translation/en/ui/review27_messages.json'
VAS=('0x892668','0x8926d8','0x892748')

def plan():
    rows={r['va']:r for r in E.records()};active=E.load()['strings'];strings={}
    for va in VAS:
        row=rows[va];jp=row['jp'];en=active[jp]['en']
        if row['family']!='system_message'or row['usage']!='display'or row['encoding']!='utf-8':raise ValueError('Save message source changed')
        if len(jp.split('\n'))!=2 or len(en.split('\n'))!=2:raise ValueError('Save message row structure changed')
        for n,(source,english)in enumerate(zip(jp.split('\n'),en.split('\n'))):
            previous=strings.setdefault(source,dict(en=english,occurrences=[]))
            if previous['en']!=english:raise ValueError('Save line has contradictory English')
            previous['occurrences'].append(dict(va=va,offset=int(row['offset'],16),line=n,
                source_message_sha256=sha256(jp.encode('utf8'))))
    if len(strings)!=5:raise ValueError('Save prompt coverage changed')
    return dict(schema=1,version='0.5.27',strings=strings,source_messages=3,line_occurrences=6)

def hook_entries(elf,mapping):
    data=plan()
    if json.loads(DEST.read_text('utf8'))!=data:raise ValueError('Save line plan stale')
    rows={r['va']:r for r in E.records()};entries=[]
    for jp,row in data['strings'].items():
        for occ in row['occurrences']:
            whole=rows[occ['va']]['jp'].encode('utf8')+b'\0';at=occ['offset']
            if elf[at:at+len(whole)]!=whole:raise ValueError('Save message bytes changed')
        key=H.utf8_key(jp.encode('utf8'),elf);english=E.encode(row['en'],mapping)
        entries.append(dict(id='review27:save:'+sha256(jp.encode('utf8'))[:12],key=key,english=english))
    return entries

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    for jp,row in data['strings'].items():print(repr(jp),'->',repr(row['en']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no save prompt data written.')

if __name__=='__main__':main()
