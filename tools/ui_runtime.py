"""Target-bound printf templates and native UTF-8 system dialogs.

CP932 formatter literals use the matched VWF alphabet while ASCII printf
arguments survive unchanged. Native UTF-8 templates and system dialogs remain
real UTF-8; OS token names are preserved for the game's substitution routine.
"""
import struct

from tools.common import sha256
from tools import ui_catalog, ui_hook, eboot_text, library_build as lb

# These templates describe native save-data metadata and a network wait timer.
# They must remain UTF-8 understood by the OS, never VWF carrier characters.
NATIVE = {'0x89bd70','0x89c2a0','0x8a1868','0x8a1870'}
PRINTF_FRAGMENTS = {'0x9f1310','0x9f13e0','0x9f1250','0x9f1408','0x9f1230','0x9f1378'}


def encode_format(text, mapping):
    out, pos = bytearray(), 0
    def literal(s):
        return eboot_text.encode(s,mapping)
    for match in eboot_text.FORMAT.finditer(text):
        out += literal(text[pos:match.start()]) + match.group(0).encode('ascii')
        pos = match.end()
    return bytes(out + literal(text[pos:]))


def toc_references(elf, source_va):
    """Use only TOC pointer words with actual r2-relative loads in target code."""
    refs = []
    for slot in range(ui_hook.TOC-0x8000,ui_hook.TOC+0x8000,4):
        at = slot-0x10000
        if struct.unpack_from('>I',elf,at)[0] != source_va:
            continue
        load = 32<<26 | 2<<16 | ((slot-ui_hook.TOC)&0xffff)
        sites = [p+0x10000 for p in range(0x200,0x769cdc,4)
            if struct.unpack_from('>I',elf,p)[0]&0xfc1fffff==load]
        if sites:
            refs.append(dict(offset=at,va=slot,consumer_loads=sites))
    return refs


def plan(elf, mapping):
    grouped, rows = ui_catalog.checked()
    res = eboot_text.resolver()
    payloads, pointers, inline, unresolved = [], [], [], []
    for rid, sources in grouped.items():
        en = eboot_text.unshow(lb.expand(rows[rid]['en'],res))
        for source in sources:
            if not source['id'].startswith('eboot:'):
                continue
            at, raw = source['offset'], source['raw']
            if elf[at:at+len(raw)+1] != raw+b'\0':
                raise ValueError('Runtime source fingerprint changed: '+source['id'])
            va = source['id'][6:]
            if source['family']=='system' or va in NATIVE or (source['encoding']=='utf-8' and eboot_text.FORMAT.search(source['text'])):
                encoded = en.encode('utf-8')
                if len(encoded)>len(raw):
                    refs = toc_references(elf,int(va,16))
                    if not refs:
                        unresolved.append(dict(id=source['id'],reason='Duplicate UTF-8 template needs consumer binding before relocation'))
                        continue
                    payloads.append((source['id'],encoded+b'\0'))
                    pointers.extend(dict(r,id=source['id'],old=int(va,16))for r in refs)
                else:
                    inline.append(dict(id=source['id'],offset=at,old=raw+b'\0',new=encoded+b'\0'+bytes(len(raw)-len(encoded))))
            elif eboot_text.FORMAT.search(source['text']) or va in PRINTF_FRAGMENTS:
                encoded = encode_format(en,mapping)+b'\0'
                refs = toc_references(elf,int(va,16))
                if va in PRINTF_FRAGMENTS and len(encoded)>0x51:
                    raise ValueError('Reward report exceeds its measured 81-byte formatter buffer')
                if not refs:
                    # Unreferenced duplicate templates are not executable
                    # consumer evidence; keep originals rather than guess.
                    unresolved.append(dict(id=source['id'],reason='No verified TOC load; duplicate/consumer unresolved'))
                    continue
                payloads.append((source['id'],encoded))
                pointers.extend(dict(r,id=source['id'],old=int(va,16))for r in refs)
            elif source.get('fragment'):
                unresolved.append(dict(id=source['id'],reason='Joined fragment: exact standalone draw covered; assembly consumer still needs binding'))
    return dict(payloads=payloads,pointers=pointers,inline=inline,unresolved=unresolved,
        report=dict(os_occurrences=len(inline),relocated_formats=len(payloads),toc_pointers=len(pointers),
            unresolved=unresolved,runtime_verified=False))


def apply(elf, planned, payload_vas):
    before, out = bytes(elf), bytearray(elf)
    allowed = set()
    def edit(at, raw):
        out[at:at+len(raw)] = raw
        allowed.update(range(at,at+len(raw)))
    for row in planned['inline']:
        at = row['offset']
        if before[at:at+len(row['old'])] != row['old']:
            raise ValueError('OS source drift: '+row['id'])
        edit(at,row['new'])
    _, _, phs, _ = ui_hook._headers(before)
    read = ui_hook._reader(before,phs)
    for row in planned['pointers']:
        if struct.unpack_from('>I',before,row['offset'])[0] != row['old']:
            raise ValueError('Runtime TOC pointer changed: '+row['id'])
        va = payload_vas[row['id']]
        raw = dict(planned['payloads'])[row['id']]
        if read(va,len(raw)) != raw:
            raise ValueError('Runtime relocated payload readback failed')
        edit(row['offset'],struct.pack('>I',va))
    if len(out)!=len(before) or any(a!=b and i not in allowed for i,(a,b)in enumerate(zip(before,out))):
        raise ValueError('Runtime edits escape their checked spans')
    return bytes(out),dict(planned['report'],input_sha256=sha256(before),output_sha256=sha256(out),
        isolation=True,carrier_cells=0)
