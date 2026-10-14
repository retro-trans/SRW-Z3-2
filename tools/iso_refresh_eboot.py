"""Refresh only a same-size EBOOT in the current private candidate ISO."""
import argparse,json
from tools.common import ROOT,sha256,sha256_file
from tools.isoread import ISO9660,SECTOR
from tools.game_build import VERSION

def main():
    p=argparse.ArgumentParser();p.add_argument('--new-build',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    old=ROOT/'work/output/builds'/VERSION;new=(ROOT/a.new_build).resolve()
    image=(ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.iso')).resolve()
    if not new.is_relative_to((ROOT/'work/output/builds').resolve())or not image.is_relative_to((ROOT/'work/output/iso'/VERSION).resolve()):raise ValueError('Candidate path escapes its workspace')
    reports=[json.loads((folder/'build.json').read_text('utf8'))for folder in (old,new)]
    if any(r['version']!=VERSION for r in reports):raise ValueError('Mixed candidate versions')
    if set(reports[0]['outputs'])!=set(reports[1]['outputs']):raise ValueError('Candidate file inventory changed')
    for name in reports[0]['outputs']:
        for folder,report in zip((old,new),reports):
            if sha256_file(folder/name)!=report['outputs'][name]:raise ValueError('Candidate file changed: '+name)
        if name!='EBOOT.BIN'and reports[0]['outputs'][name]!=reports[1]['outputs'][name]:raise ValueError('Non-executable output changed: '+name)
    before=(old/'EBOOT.BIN').read_bytes();after=(new/'EBOOT.BIN').read_bytes()
    if len(before)!=len(after):raise ValueError('Executable size changed; rebuild the complete ISO instead')
    entries=[]
    for joliet in (True,False):
        with ISO9660(image,joliet=joliet)as iso:
            entry=next(e for path,e in iso.files()if path=='/PS3_GAME/USRDIR/EBOOT.BIN')
            if iso.read(entry)!=before:raise ValueError('ISO executable differs from the verified prior candidate')
            entries.append(entry)
    if entries[0]['extents']!=entries[1]['extents']or entries[0]['size']!=len(after):raise ValueError('Directory trees disagree on the executable allocation')
    print('Only EBOOT differs; all other 12 candidate files are byte-identical.')
    print('Same-size executable:',len(after),'bytes;',sha256(before),'->',sha256(after))
    print('ISO allocation:',entries[0]['extents'])
    if not a.apply:print('DRY RUN: no image changed.');return
    rollback=ROOT/'work/output/scratch'/('EBOOT-'+VERSION+'-before-name-field.bin')
    if rollback.exists():raise ValueError('Executable rollback copy already exists')
    rollback.write_bytes(before)
    cursor=0
    with image.open('r+b')as stream:
        for extent in entries[0]['extents']:
            stream.seek(extent['lba']*SECTOR);stream.write(after[cursor:cursor+extent['size']]);cursor+=extent['size']
        stream.flush()
    if cursor!=len(after):raise ValueError('Incomplete executable refresh')
    for joliet in (True,False):
        with ISO9660(image,joliet=joliet)as iso:
            entry=next(e for path,e in iso.files()if path=='/PS3_GAME/USRDIR/EBOOT.BIN')
            if iso.read(entry)!=after:raise ValueError('Refreshed executable readback differs')
    print('Candidate executable refreshed; run full ISO verification before delivery.')
if __name__=='__main__':main()
