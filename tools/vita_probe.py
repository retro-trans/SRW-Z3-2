"""Propose Tengoku-native ARM sites from unique Jigoku context fingerprints.

These are read-only analysis candidates, not accepted patch addresses. Every
site still needs native instruction/control-flow and execution verification.
"""
import argparse
from collections import Counter
import json
import zipfile
from tools.common import sha256, write_json
from tools import vita_source as V, vita_elf as E
from tools.vita import self_decrypt as S
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

LEGACY = V.DEPS/'english_pilot_01_install/SRW-Z3-Vita-English-pilot-01-install.zip'
LEGACY_SHA = '14414068b44fa8ded7f9acb467dceddb4cd02c88845a4109a6e811960cc985d1'
SITES = dict(advance=0x81007370, normal=0x810DA058, mode1=0x810DA0F2,
    keyword=0x810DA1FE, substitution=0x810DA48A, piece_end=0x810D9F4E,
    draw=0x81006E50, description=0x810D9DD8, center=0x81007974)


def propose():
    with zipfile.ZipFile(LEGACY) as archive:
        old = archive.read('PCSG00264/eboot.bin')
    V.need(sha256(old)==LEGACY_SHA,'Legacy Vita reference differs')
    oi=S.parse(old); ob=oi['phdrs'][0][2]; off,size,_,_=oi['infos'][0]; old=old[off:off+size]
    current=(E.OUTPUT/'segment-0.bin').read_bytes()
    info=json.loads((E.OUTPUT/'baseline.json').read_text('utf8')); base=info['program_headers'][0][2]
    output={}
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    for name,va in SITES.items():
        votes=Counter()
        for back in (-64,-48,-32,-24,-16,-8,0,4,8,16,24,32):
            for n in (8,12,16,24,32):
                pattern=old[va-ob+back:va-ob+back+n]
                pos=current.find(pattern)
                if pos>=0 and current.find(pattern,pos+1)<0 and (pos-back)%2==0:
                    votes[base+pos-back]+=1
        candidates=[]
        for address,count in votes.most_common(3):
            at=address-base
            candidates.append(dict(address=address, unique_context_votes=count,
                original_site_bytes=old[va-ob:va-ob+4].hex(), candidate_site_bytes=current[at:at+4].hex(),
                disassembly=[dict(address=a, instruction=m+' '+o) for a,_,m,o in md.disasm_lite(
                    current[at-16:at+32],address-16)]))
        output[name]=dict(reference_address=va,candidates=candidates)
    return dict(schema=1,title_id=V.TITLE,reference_sha256=LEGACY_SHA,
                source_text_sha256=sha256(current), sites=output, patch_sites_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result=propose()
    for name,row in result['sites'].items():
        print(name,[(hex(r['address']),r['unique_context_votes'],r['original_site_bytes']==r['candidate_site_bytes']) for r in row['candidates']])
    if a.apply:write_json(V.WORK/'arm_site_candidates.json',result)
    else:print('DRY RUN: no analysis report written.')


if __name__=='__main__':main()
