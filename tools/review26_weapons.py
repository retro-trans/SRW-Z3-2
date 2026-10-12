"""Audit every weapon against the sibling project; expand fitting list names."""
import argparse,json
from functools import lru_cache
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import rpw_text as R
REFERENCE=Path('E:/Projects/SRW Z3')
DEST=ROOT/'work/ui/review26_weapon_audit.json'
WIDTH=440 # name begins at x84; next table begins x538; retain14px clearance

@lru_cache(None)
def width(text):
    from tools.ui_vwf_build import raster
    return sum(raster(c)[1]for c in text)*31/32

def plan():
    src=REFERENCE/'localization/messages/weapons.json';loc=REFERENCE/'localization/locales/en/weapons.json'
    jp=json.loads(src.read_text('utf8'))['messages'];en=json.loads(loc.read_text('utf8'))['messages']
    reference={row['source']:en[rid]['text']for rid,row in jp.items()if rid in en}
    names=R.load_names();slots=R.slots(R.load_rpw());cap=R.caps(slots)
    short={s['jp']:s for s in slots if s['family']=='weapon_short'};full=names['strings']['weapon'];changes=[];audit=[]
    for key,row in sorted(full.items()):
        other=reference.get(key);audit.append(dict(source=key,english=row['en'],reference=other,status='unique-to-tengoku'if other is None else 'identical'if other==row['en']else 'reviewed-meaning-exception'))
    for key,s in sorted(short.items()):
        if key not in reference or key not in full:continue
        current=R.text_for(s,names,cap[('weapon',3)]);wanted=full[key]['en']
        if width(wanted)>WIDTH or current==wanted:continue
        changes.append(dict(source=key,old=current,new=wanted,width_px=width(wanted)))
        names['strings']['weapon_short'][key]=dict(en=wanted,source='review26: sibling weapon consistency; measured 440px list bound; reviewed full-name terminology retained')
    return dict(schema=1,version='0.5.26',reference_source_sha256=sha256_file(src),reference_english_sha256=sha256_file(loc),
        full_names=len(full),short_names=len(short),shared_full=sum(r['reference']is not None for r in audit),
        shared_short=len(set(short)&set(reference)),full_name_exceptions=[r for r in audit if r['status']=='reviewed-meaning-exception'],
        changes=changes,comparison=audit,runtime_verified=False),names

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data,names=plan()
    print('All full/list names:',data['full_names'],data['short_names'],'shared:',data['shared_full'],data['shared_short'])
    for row in data['changes']:print(repr(row['old']),'->',repr(row['new']),row['width_px'])
    print('Reviewed meaning exceptions:',len(data['full_name_exceptions']))
    if a.apply:
        write_json(R.NAMES,names)
        if data['changes']or not DEST.exists():write_json(DEST,data)
    else:print('DRY RUN: no data written.')
if __name__=='__main__':main()
