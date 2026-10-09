"""Archive acceptance checks with an independent ITOC metadata reader.

This module does not use the writer's offsets to locate output members.
It verifies storage integrity; executable/runtime consumers remain untested.
Archives are memory-mapped, so a 225 MB uncompressed TPACK build is checked
without copying either file into memory; only one member at a time is.
"""
import json
import mmap
import struct
from contextlib import contextmanager
from pathlib import Path

from tools.common import destination, sha256, sha256_file, write_json
from tools.cpk import CPK
from tools.cpkpatch import build


def utf_rows(blob):
    if blob[:4] != b'@UTF':
        raise ValueError('independent verifier: missing UTF table')
    size = struct.unpack_from('>I', blob, 4)[0]
    rows, strings, payloads, name, columns, stride, count = struct.unpack_from('>IIIIHHI', blob, 8)
    if len(blob) < size + 8 or not 24 <= rows <= strings <= payloads <= size or rows + count * stride > strings:
        raise ValueError('independent verifier: invalid table bounds')

    def value(kind, offset):
        formats = ['B', 'b', 'H', 'h', 'I', 'i', 'Q', 'q', 'f', 'd']
        if kind < 10:
            form = '>' + formats[kind]
            return struct.unpack_from(form, blob, offset)[0], offset + struct.calcsize(form)
        relative = struct.unpack_from('>I', blob, offset)[0]
        if kind == 10:
            begin = 8 + strings + relative
            end = blob.find(b'\0', begin, 8 + payloads)
            if not 8 + strings <= begin < 8 + payloads or end < 0:
                raise ValueError('independent verifier: invalid string')
            return blob[begin:end].decode('utf-8'), offset + 4
        if kind == 11:
            length = struct.unpack_from('>I', blob, offset + 4)[0]
            begin = 8 + payloads + relative
            if begin + length > 8 + size:
                raise ValueError('independent verifier: invalid blob')
            return blob[begin:begin + length], offset + 8
        raise ValueError('independent verifier: unknown type')

    schema, position = [], 32
    for _ in range(columns):
        flag = blob[position]
        label, _ = value(10, position + 1)
        position += 5
        fixed = None
        if flag >> 4 == 3:
            fixed, position = value(flag & 15, position)
        elif flag >> 4 not in (1, 5):
            raise ValueError('independent verifier: unknown storage')
        schema.append((label, flag, fixed))
    if position > 8 + rows:
        raise ValueError('independent verifier: schema overrun')
    output = []
    for index in range(count):
        position = 8 + rows + index * stride
        record = {}
        for label, flag, fixed in schema:
            if flag >> 4 == 1:
                record[label] = 0
            elif flag >> 4 == 3:
                record[label] = fixed
            else:
                record[label], position = value(flag & 15, position)
        if position > 8 + rows + (index + 1) * stride:
            raise ValueError('independent verifier: row overrun')
        output.append(record)
    return output


def _table(data, base):
    """Just the @UTF table at `base` (not the rest of the archive)."""
    if len(data) < base + 8:
        raise ValueError('independent verifier: truncated table')
    return bytes(data[base:base + 8 + struct.unpack_from('>I', data, base + 4)[0]])


@contextmanager
def mapped(path):
    """Read-only bytes-like view of a file (mmap unless it is empty)."""
    with open(path, 'rb') as stream:
        if not Path(path).stat().st_size:
            yield b''
            return
        view = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            yield view
        finally:
            view.close()


def itoc_members(data):
    if data[:4] != b'CPK ':
        raise ValueError('independent verifier: not CPK')
    header = utf_rows(_table(data, 16))[0]
    if not header['ItocOffset'] or header.get('TocOffset'):
        raise ValueError('independent verifier: expected ITOC-only CPK')
    itoc = utf_rows(_table(data, header['ItocOffset'] + 16))[0]
    declared = struct.unpack_from('<Q', data, header['ItocOffset'] + 8)[0]
    utf_size = struct.unpack_from('>I', data, header['ItocOffset'] + 20)[0] + 8
    # CRI's ItocSize includes the 16-byte chunk prefix. The chunk payload
    # length may include trailing padding outside the UTF table.
    if declared < utf_size or header['ItocSize'] < utf_size + 16:
        raise ValueError('independent verifier: ITOC chunk size too small')
    sizes = {}
    for table in ('DataL', 'DataH'):
        if itoc.get(table):
            for row in utf_rows(itoc[table]):
                if row['ID'] in sizes:
                    raise ValueError('independent verifier: duplicate member')
                sizes[row['ID']] = (row['FileSize'], row['ExtractSize'])
    if len(sizes) != header['Files']:
        raise ValueError('independent verifier: member count mismatch')
    offset, align, members = header['ContentOffset'], header['Align'], {}
    if not align or offset % align:
        raise ValueError('independent verifier: invalid alignment')
    for member_id, (stored, decoded) in sorted(sizes.items()):
        if offset + stored > len(data):
            raise ValueError('independent verifier: payload out of bounds')
        members[member_id] = {'offset': offset, 'size': stored, 'extract': decoded,
                              'raw_sha256': sha256(data[offset:offset + stored])}
        offset = ((offset + stored + align - 1) // align) * align
    return header, members


def compare(src, dst, replacement_bytes):
    """Independent acceptance of a rebuilt archive.

    replacement_bytes maps member id -> the DECODED bytes that member must
    read back as. A replacement may be stored raw (FileSize == ExtractSize,
    identical bytes) or CRILAYLA-compressed (then decoded here with the
    reader's decompressor). Untouched members must keep raw bytes and sizes.
    """
    with mapped(src) as original, mapped(dst) as output:
        return _compare(src, dst, original, output, replacement_bytes)


def _compare(src, dst, original, output, replacement_bytes):
    from tools.cpk import decompress_crilayla
    old_header, old = itoc_members(original)
    new_header, new = itoc_members(output)
    if old.keys() != new.keys():
        raise ValueError('round trip changed member identities')
    changed_header_fields = {'ContentSize', 'EnabledDataSize', 'EnabledPackedSize', 'ItocSize'}
    for key in old_header:
        if key not in changed_header_fields | {'ContentOffset'} and old_header[key] != new_header[key]:
            raise ValueError('unexpected CPK header change: ' + key)
    # ContentOffset may only move forward, and only to make room for ITOC growth:
    # the new ITOC must still end before it.
    if new_header['ContentOffset'] != old_header['ContentOffset']:
        itoc_end = new_header['ItocOffset'] + 16 + struct.unpack_from('>I', output, new_header['ItocOffset'] + 20)[0] + 8
        if new_header['ContentOffset'] < old_header['ContentOffset'] or itoc_end > new_header['ContentOffset']:
            raise ValueError('ContentOffset moved without ITOC growth needing it')
        if any(output[itoc_end:new_header['ContentOffset']]):
            raise ValueError('nonzero bytes between ITOC and moved ContentOffset')
    if new_header['ItocSize'] - old_header['ItocSize'] != (
            struct.unpack_from('>I', output, new_header['ItocOffset'] + 20)[0] -
            struct.unpack_from('>I', original, old_header['ItocOffset'] + 20)[0]):
        raise ValueError('ITOC size header did not track table growth')
    compressed = 0
    with CPK(dst) as reader:
        by_id = {e['id']: e for e in reader.files}
        for member_id, entry in new.items():
            if member_id in replacement_bytes:
                raw = replacement_bytes[member_id]
                if entry['extract'] != len(raw):
                    raise ValueError('replacement extract size differs: %d' % member_id)
                stored = output[entry['offset']:entry['offset'] + entry['size']]
                if stored[:8] == b'CRILAYLA' and entry['size'] != len(raw):
                    # Decode once, from the independently located bytes; the
                    # reader must locate exactly the same bytes.
                    if (by_id[member_id]['offset'], by_id[member_id]['size'],
                            by_id[member_id]['extract']) != (entry['offset'], entry['size'], entry['extract']):
                        raise ValueError('reader and verifier disagree on member %d' % member_id)
                    if decompress_crilayla(stored) != raw:
                        raise ValueError('compressed replacement does not decode: %d' % member_id)
                    compressed += 1
                    continue
                if entry['size'] != len(raw) or entry['raw_sha256'] != sha256(raw):
                    raise ValueError('replacement payload or size differs')
                if reader.read(by_id[member_id]) != raw:
                    raise ValueError('replacement readback differs')
            else:
                if (entry['size'], entry['extract'], entry['raw_sha256']) != (old[member_id]['size'], old[member_id]['extract'], old[member_id]['raw_sha256']):
                    raise ValueError('untouched member changed: %d' % member_id)
                # Raw bytes and declared sizes are identical to the source already
                # decompressed during prepare; repeating that work proves nothing new.
    source_sha, output_sha = sha256_file(src), sha256_file(dst)
    return {'members': len(new), 'replaced': len(replacement_bytes), 'untouched_members_verified': len(new) - len(replacement_bytes),
            'replaced_compressed': compressed, 'output_bytes': len(output),
            'source_sha256': source_sha, 'output_sha256': output_sha,
            'byte_identical': len(original) == len(output) and source_sha == output_sha,
            'independent_itoc_check': True}


def verify_workspace(settings):
    from tools.inventory import FONT, LIBRARIES, RPW, UI_ARCHIVES
    from tools.pipeline import source_manifest, verified_source
    output = settings['work'] / 'verification'
    if output.exists():
        raise ValueError('verification output already exists; use a fresh configured workspace')
    manifest = source_manifest(settings)
    # Check selected binary inputs up front; all source outputs were already
    # read back during extraction. Full source verification includes the ISO.
    if sha256_file(settings['iso']) != manifest['iso_sha256']:
        raise ValueError('original ISO fingerprint changed')
    output.mkdir(parents=True)
    verified = 0
    for entry in manifest['files']:
        path = destination(settings['work'] / 'source', entry['path'].lstrip('/'))
        if path.stat().st_size != entry['size'] or sha256_file(path) != entry['sha256']:
            raise ValueError('extracted source drift: ' + entry['path'])
        verified += 1
    print('verified ISO fingerprint and %d extracted files' % verified, flush=True)
    stage = settings['work'] / 'prepared/STGZ3OF2.dec.cpk'
    prepared = json.loads((settings['work'] / 'prepared/inventory_summary.json').read_text(encoding='utf-8'))
    if sha256_file(stage) != prepared['sdat']['decoded_sha256']:
        raise ValueError('prepared stage archive drift')
    sources = [stage] + [verified_source(settings, p) for p in [RPW] + list(LIBRARIES.values()) + UI_ARCHIVES + [FONT]]
    noops = []
    for source in sources:
        target = output / (source.name + '.noop.cpk')
        build(source, target, {})
        result = compare(source, target, {})
        result['archive'] = source.name
        if not result['byte_identical']:
            raise ValueError('no-op archive differs: ' + source.name)
        noops.append(result)
        print('byte-identical rebuild: %s (%d members)' % (source.name, result['members']), flush=True)

    archive = CPK(stage)
    # Force a real 16-bit-to-32-bit ITOC migration without editing dialogue.
    # This is synthetic test content only and must never be deployed.
    itoc = utf_rows(_table(archive.buf, archive._h('ItocOffset') + 16))[0]
    low_ids = [r['ID'] for r in utf_rows(itoc['DataL'])]
    chosen = low_ids[0]
    payload = b'-- SYNTHETIC ARCHIVE STORAGE TEST, NOT GAME CONTENT\n' + b' ' * 70000
    replacement = output / 'synthetic_member.txt'
    replacement.write_bytes(payload)
    target = output / 'stage.synthetic-growth.cpk'
    build(stage, target, {chosen: replacement})
    growth = compare(stage, target, {chosen: payload})
    growth['member_id'] = chosen
    growth['replacement_bytes'] = len(payload)
    report = {'schema': 1, 'title_id': settings['title_id'], 'source_iso_sha256': manifest['iso_sha256'],
              'extracted_files_verified': verified, 'noop_archives': noops, 'synthetic_growth': growth,
              'scope': 'Local storage round trips, not a bootable build', 'runtime_verified': False,
              'sdat_reencryption_verified': False, 'deployed': False}
    write_json(output / 'verification.json', report)
    return report
