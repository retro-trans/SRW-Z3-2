"""Refresh same-size executable/stage files in the current private candidate ISO."""
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
    changed=[]
    for name in reports[0]['outputs']:
        for folder,report in zip((old,new),reports):
            if sha256_file(folder/name)!=report['outputs'][name]:raise ValueError('Candidate file changed: '+name)
        if reports[0]['outputs'][name]!=reports[1]['outputs'][name]:changed.append(name)
    if set(changed)-{'EBOOT.BIN','STGZ3OF2.SDAT'}:raise ValueError('Change exceeds executable/stage refresh scope')
    if 'STGZ3OF2.SDAT'in changed and sha256_file(old/'STGZ3OF2.cpk')!=sha256_file(new/'STGZ3OF2.cpk'):raise ValueError('Decoded stage content changed; rebuild the complete ISO instead')
    paths={'EBOOT.BIN':'/PS3_GAME/USRDIR/EBOOT.BIN','STGZ3OF2.SDAT':'/PS3_GAME/USRDIR/DATA/STAGE/STGZ3OF2.SDAT'}
    updates=[]
    for name in changed:
        before=(old/name).read_bytes();after=(new/name).read_bytes()
        if len(before)!=len(after):raise ValueError('File size changed; rebuild the complete ISO instead')
        entries=[]
        for joliet in (True,False):
            with ISO9660(image,joliet=joliet)as iso:
                entry=next(e for path,e in iso.walk()if path==paths[name])
                if iso.read(entry)!=before:raise ValueError('ISO file differs from the verified prior candidate: '+name)
                entries.append(entry)
        if entries[0]['extents']!=entries[1]['extents']or entries[0]['size']!=len(after):raise ValueError('Directory trees disagree on the allocation')
        print(name,len(after),'bytes;',sha256(before),'->',sha256(after),'allocation:',entries[0]['extents'])
        updates.append((name,before,after,entries[0]))
    print('Unchanged candidate files:',len(reports[0]['outputs'])-len(changed),'; decoded stage content identical.')
    if not a.apply:print('DRY RUN: no image changed.');return
    for name,before,after,entry in updates:
        rollback=ROOT/'work/output/scratch'/(name+'-'+VERSION+'-before-name-field.bin')
        if rollback.exists():raise ValueError('Rollback copy already exists')
        rollback.write_bytes(before)
    with image.open('r+b')as stream:
        for name,before,after,entry in updates:
            cursor=0
            for extent in entry['extents']:
                stream.seek(extent['lba']*SECTOR);stream.write(after[cursor:cursor+extent['size']]);cursor+=extent['size']
            if cursor!=len(after):raise ValueError('Incomplete file refresh')
        stream.flush()
    for name,before,after,entry in updates:
        for joliet in (True,False):
            with ISO9660(image,joliet=joliet)as iso:
                current=next(e for path,e in iso.walk()if path==paths[name])
                if iso.read(current)!=after:raise ValueError('Refreshed file readback differs')
    print('Candidate refreshed; run full ISO verification before delivery.')
if __name__=='__main__':main()
