"""Derive sanitized rePatch auth from the original SELF using local work.bin.

No permissions are guessed. reF00D's decrypt_module copies optional type 1
to capabilities and type 3 to attributes; type 2 is NOT exported.
Primary reference: dots-tb/reF00D, f3271bcd010950193cfb6e0331cae89bdb5e96e9,
src/ref00d_kprx_auth.h (blob f278b66bb7aa47b596fd83925bfc5e43e74f9235),
src/ref00d_kprx_auth.c (blob 696e7d51114f6da31d19463615af1cda35346579).
"""
import argparse,json,struct
from pathlib import Path
from tools import vita_source as V,vita_elf as E
from tools.common import sha256,sha256_file,write_json
from tools.vita import self_decrypt as S
from tools.vita.repatch_auth import sanitize

DEST=V.WORK/'derived_auth'
COMMIT='f3271bcd010950193cfb6e0331cae89bdb5e96e9'


def optional_auth(plain,mh,authority,metadata_origin,header_size):
    """Copy only documented permissions, leaving every secret region zero."""
    signature,sigtype,sections,nkeys,length,pad0,pad1=mh
    start=32+sections*48+nkeys*16;end=start+length
    V.need(sigtype==5 and pad0==pad1==0 and length==0x170 and
           0<=start<end<=len(plain) and metadata_origin+end<=signature<=header_size-256,
           'Unsupported optional auth metadata bounds')
    at=start;parts={};seen=[]
    while at<end:
        typ,size,more=struct.unpack_from('<IIQ',plain,at)
        V.need(typ in (1,2,3) and typ not in seen and size=={1:0x30,2:0x110,3:0x30}[typ] and
               at+size<=end and more==int(at+size<end),'Unsupported optional auth header')
        seen.append(typ)
        if typ in (1,3):parts[typ]=plain[at+16:at+48]
        at+=size
    V.need(set(seen)=={1,2,3},'Missing original capability/attribute fields')
    raw=struct.pack('<Q',authority)+bytes(8)+parts[1]+parts[3]+bytes(64)
    return sanitize(raw,authority),seen


def derive(source,rif,title):
    V.need(len(rif)==512 and rif[0x17:0x20]==title.encode(),'Matching local license identity required')
    V.need(sha256_file(E.REFERENCE)==E.REFERENCE_SHA,'SELF reference changed')
    reference=E.REFERENCE.read_text('utf8')
    info,plain,mh=S.decode_metadata(source,rif[0x50:0x60],reference)
    auth,types=optional_auth(plain,mh,info['ai'][0],info['meta']+48+64,info['hlen'])
    return auth,dict(optional_header_types=types,optional_header_bytes=mh[4],
        original_permissions_preserved=True,default_or_borrowed_permissions_used=False,
        individual_seed_exported=False,license_exported=False,secret_regions_zero=True)


def oracle():
    """Independent existing game profile checks extraction, never supplies bytes."""
    root=V.SIBLING/'work/vita'
    license_path=Path('E:/SRWZ3/iso/work.bin')
    source=root/'decrypted_PCSG00264/eboot.bin'
    profile=root/'retro_trans_0.9.6_20261108/VITA-REPATCH.json'
    V.need(all(p.is_file() for p in (license_path,source,profile)),'Missing independent auth reference')
    auth,_=derive(source.read_bytes(),license_path.read_bytes(),'PCSG00264')
    expected=bytes.fromhex(json.loads(profile.read_text('utf8'))['auth']['hex'])
    V.need(auth==expected,'Derived auth differs from independent existing rePatch profile')
    return True


def plan():
    source=(V.PLAIN/'eboot.bin').read_bytes()
    audit=json.loads((V.WORK/'source_audit.json').read_text('utf8'))
    V.need(sha256(source)==audit['files']['eboot.bin']['sha256'],'Original SELF changed')
    auth,details=derive(source,V.LICENSE.read_bytes(),V.TITLE)
    # Source permissions must be independent of the translated executable.
    candidate=json.loads((V.WORK/'arm_candidate_v2/plan.json').read_text('utf8'))
    V.need(S.parse((V.WORK/'arm_candidate_v2/eboot.bin').read_bytes())['ai'][0]==S.parse(source)['ai'][0],
           'Translated executable authority changed')
    return auth,dict(schema=1,title_id=V.TITLE,version='0.1.0',source_self_sha256=sha256(source),
        sanitized_auth_sha256=sha256(auth),auth_bytes=len(auth),source='original SELF + supplied work.bin',
        reference_commit=COMMIT,independent_existing_auth_profile_parity=oracle(),
        native_candidate_sha256=candidate['output_sha256'],physical_gameplay_tested=False,**details)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    auth,report=plan();print(json.dumps(report,indent=2))
    if a.apply:
        V.need(not DEST.exists(),'Preserve existing derived auth');DEST.mkdir(parents=True)
        (DEST/'self_auth.bin').write_bytes(auth);write_json(DEST/'proof.json',report)
    else:print('DRY RUN: no authentication file written.')


if __name__=='__main__':main()
