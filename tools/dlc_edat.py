"""Licensed Tengoku EDAT v4/0x3c codec, preserving original NPD identity.

Format reference: RPCS3 Crypto/unedat.cpp and key_vault.h. Per-user RAP input
is local only. No license conversion or entitlement data is emitted in reports.
Rebuilt payloads have no Sony signature; emulator/modified-system tests remain
required. The original 128-byte NPD, including content ID and dev hash, is kept.
"""
import hashlib,hmac,struct
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.primitives.cmac import CMAC
RAP_KEY=bytes.fromhex('869f7745c13fd890ccf29188e3cc3edf')
PBOX=(12,3,6,4,1,11,15,8,2,7,0,5,10,14,13,9)
E1=bytes.fromhex('a93e1fd67c55a329b75fdda62a95c7a5')
E2=bytes.fromhex('67d45da3296d006a4e7c537bf5538c74')
EDAT_KEY=bytes.fromhex('4ca9c14b01c95309969bec68aa0bc081')
TITLE_KEY=bytes.fromhex('9b515feacf75064981aa604d91a54e97')

def aes(key,data,iv=None,decrypt=False):
 c=Cipher(algorithms.AES(key),modes.ECB()if iv is None else modes.CBC(iv))
 ctx=c.decryptor()if decrypt else c.encryptor();return ctx.update(data)+ctx.finalize()

def cmac(key,data):
 c=CMAC(algorithms.AES(key));c.update(data);return c.finalize()

def rif_key(rap):
 if len(rap)!=16:raise ValueError('Invalid local entitlement input')
 key=bytearray(aes(RAP_KEY,rap,bytes(16),True))
 for _ in range(5):
  for i in PBOX:key[i]^=E1[i]
  for i in range(15,0,-1):key[PBOX[i]]^=key[PBOX[i-1]]
  carry=0
  for p in PBOX:
   value=(key[p]-carry)&255
   if carry!=1 or value!=255:
    carry=int(value<E2[p]);key[p]=(value-E2[p])&255
   else:key[p]=(value-E2[p])&255
 return bytes(key)

def parameters(raw,name):
 if len(raw)<272:raise ValueError('Truncated EDAT header')
 if raw[:4]!=b'NPD\0'or struct.unpack_from('>III',raw,4)!=(4,2,0):raise ValueError('Not supported Tengoku licensed EDAT')
 flags,block,size=struct.unpack_from('>IIQ',raw,128)
 if flags!=0x3c or block!=16384 or not size:raise ValueError('Unsupported EDAT flags/block size')
 if cmac(TITLE_KEY,raw[16:64]+name.encode('ascii'))!=raw[80:96]:raise ValueError('EDAT title authentication failed')
 count=(size+block-1)//block
 if len(raw)!=256+count*32+((size+15)&~15)+16:raise ValueError('EDAT payload bounds differ')
 return block,size,count

def block_keys(raw,key,index):
 seed=raw[96:108]+struct.pack('>I',index);derived=aes(key,seed)
 crypt=aes(EDAT_KEY,derived,bytes(16),True)
 hashed=aes(EDAT_KEY,aes(key,derived),bytes(16),True)+bytes(4)
 return crypt,hashed

def decode(raw,rap,name,require_metadata=False):
 block,size,count=parameters(raw,name);key=rif_key(rap);header_key=aes(EDAT_KEY,key,bytes(16),True)
 if not hmac.compare_digest(cmac(header_key,raw[:160]),raw[160:176]):raise ValueError('EDAT header authentication failed')
 out=bytearray();metadata=[]
 for i in range(count):
  at=256+i*(block+32);meta=raw[at:at+32];metadata.append(meta);n=min(block,size-len(out));padded=(n+15)&~15
  data=raw[at+32:at+32+padded];crypt,hashed=block_keys(raw,key,i)
  wanted=bytes(a^b for a,b in zip(meta[:16],meta[16:]))+meta[16:20]
  if not hmac.compare_digest(hmac.new(hashed,data,hashlib.sha1).digest(),wanted):raise ValueError('EDAT data-block authentication failed')
  out+=aes(crypt,data,raw[64:80],True)[:n]
 valid=hmac.compare_digest(cmac(header_key,b''.join(metadata)),raw[144:160])
 if require_metadata and not valid:raise ValueError('EDAT metadata authentication failed')
 return bytes(out),dict(blocks=count,header_authenticated=True,blocks_authenticated=True,metadata_authenticated=valid,
  content_id=raw[16:64].rstrip(b'\0').decode('ascii'),license=2,version=4)

def rebuild(original,payload,rap,name):
 block,_,_=parameters(original,name);key=rif_key(rap);header_key=aes(EDAT_KEY,key,bytes(16),True)
 out=bytearray(original[:144]+bytes(112));struct.pack_into('>Q',out,136,len(payload));metadata=[]
 for i,start in enumerate(range(0,len(payload),block)):
  plain=payload[start:start+block];plain+=bytes(-len(plain)%16);crypt,hashed=block_keys(original,key,i)
  cipher=aes(crypt,plain,original[64:80]);digest=hmac.new(hashed,cipher,hashlib.sha1).digest()
  tail=digest[16:]+bytes(12);meta=bytes(a^b for a,b in zip(digest[:16],tail))+tail
  metadata.append(meta);out+=meta+cipher
 out+=original[-16:];out[144:160]=cmac(header_key,b''.join(metadata));out[160:176]=cmac(header_key,out[:160])
 # Old retail signatures cannot authenticate changed data; leave signature fields empty.
 if out[:128]!=original[:128]:raise ValueError('Entitlement identity changed')
 decoded,report=decode(bytes(out),rap,name,require_metadata=True)
 if decoded!=payload:raise ValueError('EDAT rebuild round trip failed')
 return bytes(out),dict(report,original_npd_preserved=True,sony_signature=False)
