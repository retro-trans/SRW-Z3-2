"""Reconstruct the HMAC-verified Tengoku program ELF as RPCS3 WriteElf does.

Non-program payloads are omitted by that loader, so this is not a byte-exact
reconstruction of the pre-SELF developer ELF. Source and output hashes pin
this implementation to the independently disassembled Tengoku revision.
"""
import hashlib
import hmac
import struct
import zlib
from tools.common import sha256
from tools.vwf import ELF_SHA256

EBOOT = '/PS3_GAME/USRDIR/EBOOT.BIN'
SELF_SHA256 = 'bbe0c92d6c7b94f83dc1bf7fcd553602267029b59dedde599464367b3d1f3f8f'


def decrypt(data):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    if sha256(data) != SELF_SHA256:
        raise ValueError('unexpected Tengoku SELF source')
    magic, version, rev, kind, mo, hs, size = struct.unpack_from('>IIHHIQQ',data)
    if (magic,version,rev,kind) != (0x53434500,2,0x1c,1):
        raise ValueError('unsupported SELF revision')
    ext = struct.unpack_from('>10Q',data,32)
    header = data[ext[2]:ext[2]+64]
    phoff, shoff = struct.unpack_from('>QQ',header,32)
    phsz, phn, shsz, shn = struct.unpack_from('>4H',header,54)
    ph = data[ext[3]:ext[3]+phsz*phn]
    segments = [struct.unpack_from('>IIQQQQQQ',ph,i*phsz) for i in range(phn)]
    def aes(raw,key,mode):
        d = Cipher(algorithms.AES(key),mode).decryptor()
        return d.update(raw)+d.finalize()
    # Public APP 0x1c keyset in RPCS3 Crypto/key_vault.cpp.
    key = bytes.fromhex('CFF025375BA0079226BE01F4A31F346D79F62CFB643CA910E16CF60BD9092752')
    iv = bytes.fromhex('FD40664E2EBBA01BF359B0DCDF543DA4')
    mi = aes(data[mo+32:mo+96],key,modes.CBC(iv))
    if mi[16:32] != bytes(16) or mi[48:64] != bytes(16):
        raise ValueError('invalid metadata key padding')
    mh = aes(data[mo+96:hs],mi[:16],modes.CTR(mi[32:48]))
    _,_,n,nkeys,*_ = struct.unpack_from('>Q6I',mh)
    keys = mh[32+n*48:32+n*48+nkeys*16]
    out = bytearray(size)
    out[:64] = header
    out[phoff:phoff+len(ph)] = ph
    verified, omitted = [], []
    for i in range(n):
        off,count,typ,idx,hashed,si,enc,ki,vi,comp = struct.unpack_from('>QQ8I',mh,32+i*48)
        raw = data[off:off+count]
        if enc == 3:
            raw = aes(raw,keys[ki*16:ki*16+16],modes.CTR(keys[vi*16:vi*16+16]))
        elif enc != 1:
            raise ValueError('unsupported section encryption')
        auth = keys[si*16:si*16+96]
        if typ != 2:
            omitted.append({'type':typ,'index':idx,'bytes':count,'hmac_verified':False})
            continue
        if hashed != 2 or not hmac.compare_digest(hmac.new(auth[32:],raw,hashlib.sha1).digest(),auth[:20]):
            raise ValueError('section HMAC mismatch: %d (type %d)' % (i,typ))
        if comp == 2: raw = zlib.decompress(raw)
        s = segments[idx]
        if len(raw) != s[5] or s[2]+len(raw)>size or idx in verified:
            raise ValueError('program payload extent mismatch')
        out[s[2]:s[2]+len(raw)] = raw
        verified.append(idx)
    if set(verified) != {i for i,s in enumerate(segments) if s[0] == 1}:
        raise ValueError('not all program loads authenticated')
    out[shoff:shoff+shsz*shn] = data[ext[4]:ext[4]+shsz*shn]
    # Verify every allocated file-backed section lies in an authenticated LOAD.
    for i in range(shn):
        _,typ,flags,va,off,count,*_ = struct.unpack_from('>IIQQQQIIQQ',out,shoff+i*shsz)
        if flags & 2 and typ != 8 and count:
            if not any(s[0]==1 and s[2]<=off and off+count<=s[2]+s[5]
                       and va-off==s[3]-s[2] for s in segments):
                raise ValueError('unauthenticated allocated section')
    if sha256(out) != ELF_SHA256:
        raise ValueError('reconstructed program ELF differs from reviewed baseline')
    return bytes(out), {'source_sha256':SELF_SHA256,'baseline_elf_sha256':ELF_SHA256,
        'program_sections_hmac_verified':verified,'omitted_metadata':omitted,
        'all_allocated_sections_verified':True,'developer_elf_digest_match':False,
        'format':'RPCS3 program ELF; original non-program payloads omitted'}
