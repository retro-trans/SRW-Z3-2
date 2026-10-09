import copy
import struct
import unittest

from tools.source_text import rpw_chunks
from tools.ui_build import encode, decode, pairs, patch_rpw, verify_rpw


def fixture():
    def chunk(name, body):
        return (b'<chunk-head>'+name.encode().ljust(8,b'\0')+
                struct.pack('<II',56+len(body),len(body))+body+
                b'<chunk-foot>'+struct.pack('<I',28)+b'<endofchunk>')
    pool=b'original\0shared\0'
    records=b''.join(struct.pack('<5I',0xdeadbeef,9,9,0,0x12345678) for _ in range(44))
    # Include an unrelated integer equal to an old string offset.
    chunks=chunk('j-string',pool)+chunk('spirit',records)+chunk('other',struct.pack('<4I',9,0,9,0))
    total=60+len(chunks)
    raw=b'<mt>prod#1'.ljust(20,b'\0')+b'1.00'+struct.pack('<II',total,total-60)+chunks+b'<file--foot>'+bytes(16)
    spirit=next(c for c in rpw_chunks(raw) if c['name']=='spirit')
    entries=[]
    for i in range(1,44):
        for c,role in enumerate(('name','abbreviation','description'),1):
            entries.append({'pointer_offset':spirit['body_offset']+20*i+4*c,
                            'string_body_offset':9 if c<3 else 0,
                            'rendered_en': ('Alpha','Ab','A longer line.\nOne ally.') [c-1],
                            'occurrence_id':'rpw:0:spirit:%d:%s'%(i,role)})
    mapping={p:bytes((0x86,0x40+i)).hex() for i,p in enumerate(sorted({p for r in entries for p in pairs(r['rendered_en'])}))}
    return raw,entries,mapping


class UIBuildTests(unittest.TestCase):
    def test_shared_text_separates_roles_and_preserves_metadata(self):
        raw,entries,mapping=fixture()
        patched,edits,grow=patch_rpw(raw,entries,mapping)
        self.assertGreater(grow,0)
        self.assertNotEqual(edits[0]['new'],edits[1]['new'])
        self.assertEqual(edits[0]['new'],edits[3]['new'])
        verify_rpw(raw,patched,edits,mapping)

    def test_incomplete_duplicate_and_foreign_pointer_rejected(self):
        raw,entries,mapping=fixture()
        for change in ('missing','duplicate','foreign','stale'):
            rows=copy.deepcopy(entries)
            if change=='missing': rows.pop()
            elif change=='duplicate':rows.append(rows[0])
            elif change=='foreign':rows[0]['pointer_offset']-=4
            else:rows[0]['string_body_offset']=7
            with self.assertRaises(ValueError):patch_rpw(raw,rows,mapping)

    def test_readback_detects_unrelated_mutation(self):
        raw,entries,mapping=fixture()
        patched,edits,_=patch_rpw(raw,entries,mapping)
        damaged=bytearray(patched)
        other=next(c for c in rpw_chunks(patched) if c['name']=='other')
        damaged[other['body_offset']]=8
        with self.assertRaisesRegex(ValueError,'unrelated'):verify_rpw(raw,bytes(damaged),edits,mapping)

    def test_readback_detects_redirected_pointer(self):
        raw,entries,mapping=fixture()
        patched,edits,grow=patch_rpw(raw,entries,mapping)
        damaged=bytearray(patched)
        struct.pack_into('<I',damaged,edits[0]['source_pointer_offset']+grow,9)
        with self.assertRaisesRegex(ValueError,'pointer'):verify_rpw(raw,bytes(damaged),edits,mapping)

    def test_pair_encoding_preserves_odd_lines_and_symbols(self):
        text="Abc 10% + ?\nZ"
        mapping={p:bytes((0x86,0x40+i)).hex() for i,p in enumerate(pairs(text))}
        self.assertEqual(decode(encode(text,mapping),mapping),text)
        with self.assertRaises(ValueError):decode(b'\x86',mapping)


if __name__=='__main__':unittest.main()
