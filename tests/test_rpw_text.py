import struct
import unittest

from tools import rpw_text
from tools.source_text import rpw_chunks


def chunk(name, body):
    return (b'<chunk-head>' + name.encode().ljust(8, b'\0') + struct.pack('<II', 56 + len(body), len(body)) +
            body + b'<chunk-foot>' + struct.pack('<I', 28) + b'<endofchunk>')


def fixture():
    """A minimal RPW: the pool, every SCHEMA chunk with one or two records, the Spirit chunk and an index table."""
    pool = '－－\0ガンダム\0ビームライフル\0アムロ\0レイ\0「うわっ！\n　脱出する！」\0'.encode('cp932')
    off = {}
    p = 0
    for s in pool.split(b'\0')[:-1]:
        off[s.decode('cp932')] = p
        p += len(s) + 1
    body = {'j-string': pool}
    for name, (stride, cols) in rpw_text.SCHEMA.items():
        words = [7] * stride * 2                 # 7 = an ordinary integer that is not a string start
        for col in cols:
            words[col] = words[stride + col] = 0
        body[name] = struct.pack('<%dI' % len(words), *words)
    w = [7] * 16
    w[0:3] = [off['レイ'], off['アムロ'], off['レイ']]
    w[8:11] = [off['アムロ'], off['レイ'], off['アムロ']]
    body['pilot-nw'] = struct.pack('<16I', *w)
    r = [7] * 48
    r[2] = r[3] = off['ガンダム']
    r[26] = r[27] = 0
    body['robot'] = struct.pack('<48I', *r)
    wp = [7] * 26
    wp[3] = wp[4] = off['ビームライフル']
    wp[16] = wp[17] = 0
    body['weapon'] = struct.pack('<26I', *wp)
    body['deadmsg'] = struct.pack('<6I', off['「うわっ！\n　脱出する！」'], 1, 2, 0, 1, 2)
    body['spirit'] = struct.pack('<%dI' % 220, *([0] * 220))
    body['ridwpidx'] = struct.pack('<4I', off['ガンダム'], 1, off['アムロ'], 2)   # index table: looks like pointers
    order = ['j-string', 'pilot-nw', 'robot', 'weapon', 'sk-pri', 'spirit', 'boost-p', 'pro-name', 'deadmsg', 'ridwpidx']
    chunks = b''.join(chunk(n, body[n]) for n in order)
    total = 60 + len(chunks)
    return (b'<mt>prod#1'.ljust(20, b'\0') + b'1.00' + struct.pack('<II', total, total - 60) + chunks +
            b'<file--foot>' + bytes(16))


def enc(text):
    return text.encode('cp932')


class RpwTextTest(unittest.TestCase):
    def test_slots_follow_schema(self):
        raw = fixture()
        rows = rpw_text.slots(raw)
        by = {s['id']: s['jp'] for s in rows}
        self.assertEqual(by['pilot-nw:0:1'], 'アムロ')
        self.assertEqual(by['robot:0:2'], 'ガンダム')
        self.assertEqual(by['deadmsg:0:0'], '「うわっ！\n　脱出する！」')
        self.assertFalse(any(s['chunk'] == 'ridwpidx' for s in rows))

    def test_schema_drift_refused(self):
        raw = bytearray(fixture())
        c = next(c for c in rpw_chunks(bytes(raw)) if c['name'] == 'robot')
        struct.pack_into('<I', raw, c['body_offset'] + 8, 99999)
        with self.assertRaises(ValueError):
            rpw_text.slots(bytes(raw))

    def test_patch_repoints_only_cells_and_keeps_everything_else(self):
        raw = fixture()
        rows = {s['id']: s for s in rpw_text.slots(raw)}
        cells = []
        for sid, en in (('pilot-nw:0:1', 'Amuro'), ('pilot-nw:1:2', 'Amuro'), ('pilot-nw:0:2', 'Ray'),
                        ('robot:0:3', 'Gundam'), ('deadmsg:0:0', '「Whoa!\n Bailing out!」')):
            s = rows[sid]
            cells.append({'id': sid, 'pointer_offset': s['pointer_offset'], 'old': s['string'],
                          'raw': enc(en), 'english': en})
        out, grow = rpw_text.patch(raw, cells)
        self.assertEqual(len(out), len(raw) + grow)
        after = {s['id']: s['jp'] for s in rpw_text.slots(out)}
        self.assertEqual(after['pilot-nw:0:1'], 'Amuro')
        self.assertEqual(after['pilot-nw:1:2'], 'Amuro')
        self.assertEqual(after['pilot-nw:0:2'], 'Ray')
        self.assertEqual(after['pilot-nw:0:0'], 'レイ')          # untouched cell keeps the Japanese
        self.assertEqual(after['robot:0:2'], 'ガンダム')
        self.assertEqual(after['deadmsg:0:0'], '「Whoa!\n Bailing out!」')
        idx = next(c for c in rpw_chunks(out) if c['name'] == 'ridwpidx')
        self.assertEqual(out[idx['body_offset']:idx['body_end']],
                         next(raw[c['body_offset']:c['body_end']] for c in rpw_chunks(raw) if c['name'] == 'ridwpidx'))

    def test_patch_refuses_index_tables_and_drift(self):
        raw = fixture()
        idx = next(c for c in rpw_chunks(raw) if c['name'] == 'ridwpidx')
        with self.assertRaises(ValueError):
            rpw_text.patch(raw, [{'id': 'idx', 'pointer_offset': idx['body_offset'], 'old': 5,
                                  'raw': b'X', 'english': 'X'}])
        s = rpw_text.slots(raw)[1]
        with self.assertRaises(ValueError):
            rpw_text.patch(raw, [{'id': s['id'], 'pointer_offset': s['pointer_offset'], 'old': s['string'] + 1,
                                  'raw': b'X', 'english': 'X'}])

    def test_cost_and_unusual(self):
        self.assertEqual(rpw_text.cost('Ab\nC'), 7)
        self.assertEqual(rpw_text.unusual('∀ Gundam'), [])
        self.assertEqual(rpw_text.unusual('ガンダム X'), ['ガ', 'ダ', 'ム', 'ン'])


if __name__ == '__main__':
    unittest.main()
