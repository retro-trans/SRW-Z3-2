"""Read ISO9660/Joliet, joining consecutive multi-extent file records.

Adapted from the reviewed Jigoku reader; no game-specific constants.
All access is read-only. copy() streams every extent and refuses overwrites.
"""
import hashlib
import struct
from pathlib import Path

SECTOR = 2048
JOLIET_ESCAPES = (b'%/@', b'%/C', b'%/E')


def both32(data, offset):
    little = struct.unpack_from('<I', data, offset)[0]
    big = struct.unpack_from('>I', data, offset + 4)[0]
    if little != big:
        raise ValueError('ISO both-endian u32 mismatch at %d' % offset)
    return little


class ISO9660:
    def __init__(self, path, joliet=True):
        self.path = Path(path)
        self.size = self.path.stat().st_size
        self.fh = self.path.open('rb')
        self.joliet = False
        try:
            primary = supplementary = None
            terminated = False
            for lba in range(16, 256):
                descriptor = self._read_at(lba * SECTOR, SECTOR)
                if descriptor[1:7] != b'CD001\x01':
                    raise ValueError('invalid ISO volume descriptor')
                if descriptor[0] == 255:
                    terminated = True
                    break
                if descriptor[0] == 1:
                    primary = descriptor
                if descriptor[0] == 2 and descriptor[88:91] in JOLIET_ESCAPES:
                    supplementary = descriptor
            if primary is None or not terminated:
                raise ValueError('missing primary descriptor or terminator')
            descriptor = supplementary if joliet and supplementary else primary
            self.joliet = bool(joliet and supplementary)
            little, big = struct.unpack_from('<H', descriptor, 128)[0], struct.unpack_from('>H', descriptor, 130)[0]
            if little != SECTOR or big != SECTOR:
                raise ValueError('unsupported logical block size')
            if both32(descriptor, 80) * SECTOR > self.size:
                raise ValueError('declared volume exceeds image')
            self.root, _ = self._record(descriptor, 156)
            if not self.root['dir']:
                raise ValueError('root record is not a directory')
        except Exception:
            self.close()
            raise

    def close(self):
        self.fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _read_at(self, offset, size):
        if offset < 0 or size < 0 or offset + size > self.size:
            raise ValueError('extent outside ISO bounds')
        self.fh.seek(offset)
        data = self.fh.read(size)
        if len(data) != size:
            raise IOError('short ISO read')
        return data

    def _record(self, data, offset):
        length = data[offset]
        if not length:
            return None, 0
        if length < 34 or offset + length > len(data):
            raise ValueError('truncated ISO directory record')
        record = data[offset:offset + length]
        if 33 + record[32] > length:
            raise ValueError('truncated file identifier')
        if record[1] or record[26] or record[27]:
            raise ValueError('extended attributes/interleaved files unsupported')
        lba, size = both32(record, 2), both32(record, 10)
        if lba * SECTOR + size > self.size:
            raise ValueError('file extent exceeds ISO')
        raw = record[33:33 + record[32]]
        if raw in (b'\x00', b'\x01'):
            name = raw.decode('ascii')
        else:
            name = raw.decode('utf-16-be' if self.joliet else 'ascii')
            name = name.rsplit(';', 1)[0]
            if not name or any(c in name for c in '/\\:') or name in ('.', '..'):
                raise ValueError('unsafe ISO file identifier')
        return {'name': name, 'dir': bool(record[25] & 2), 'flags': record[25],
                'lba': lba, 'size': size}, length

    def _entries(self, parent):
        data = self._read_at(parent['lba'] * SECTOR, parent['size'])
        records = []
        offset = 0
        while offset < len(data):
            record, length = self._record(data, offset)
            if not length:
                offset = (offset // SECTOR + 1) * SECTOR
                continue
            if offset // SECTOR != (offset + length - 1) // SECTOR:
                raise ValueError('directory record crosses sector boundary')
            if record['name'] not in ('\x00', '\x01'):
                records.append(record)
            offset += length
        pending = None
        seen = set()
        for record in records:
            if pending:
                if record['name'] != pending['name'] or record['dir'] or (record['flags'] & ~128) != pending['flags']:
                    raise ValueError('broken multi-extent chain: %s' % pending['name'])
            else:
                if record['name'].casefold() in seen:
                    raise ValueError('duplicate logical path: %s' % record['name'])
                seen.add(record['name'].casefold())
                pending = dict(record, size=0, flags=record['flags'] & ~128, extents=[])
            if record['dir'] and record['flags'] & 128:
                raise ValueError('multi-extent directories unsupported')
            pending['extents'].append({'lba': record['lba'], 'size': record['size']})
            pending['size'] += record['size']
            if not record['flags'] & 128:
                yield pending
                pending = None
        if pending:
            raise ValueError('unterminated multi-extent chain: %s' % pending['name'])

    def walk(self, rec=None, prefix='', ancestors=()):
        rec = self.root if rec is None else rec
        identity = (rec['lba'], rec['size'])
        if identity in ancestors:
            raise ValueError('directory cycle')
        for entry in self._entries(rec):
            path = prefix + '/' + entry['name']
            if entry['dir']:
                yield from self.walk(entry, path, ancestors + (identity,))
            else:
                yield path, entry

    def blocks(self, entry, chunk=4 << 20):
        if chunk <= 0:
            raise ValueError('chunk size must be positive')
        for extent in entry['extents']:
            position = extent['lba'] * SECTOR
            remaining = extent['size']
            while remaining:
                data = self._read_at(position, min(chunk, remaining))
                yield data
                position += len(data)
                remaining -= len(data)

    def read(self, entry, limit=64 << 20):
        if entry['size'] > limit:
            raise ValueError('use streamed copy for files larger than %d bytes' % limit)
        return b''.join(self.blocks(entry))

    def copy(self, entry, destination):
        destination = Path(destination)
        digest = hashlib.sha256()
        # Exclusive output ensures the pristine ISO and prior outputs survive.
        with destination.open('xb') as output:
            for data in self.blocks(entry):
                output.write(data)
                digest.update(data)
        return digest.hexdigest()
