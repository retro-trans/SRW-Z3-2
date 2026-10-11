"""Enumerate every timed narration record, without changing its source bytes."""
import json
import struct
from tools.common import ROOT, sha256, write_json

MANIFEST = ROOT / 'work/ui/narration_catalog.json'
SIGNATURE = bytes.fromhex('262b263c')


def records(blob, mid):
    if len(blob) < 20 or blob[4:8] != SIGNATURE:
        raise ValueError('Not a narration member: %s' % mid)
    count = struct.unpack_from('>H', blob)[0]
    capacity = blob[2]
    stride = capacity + 30
    if not capacity or len(blob) != 20 + count * stride:
        raise ValueError('Narration record geometry changed: %s' % mid)
    rows = []
    page = 0
    previous = -2
    for index in range(count):
        at = 20 + index * stride
        cell = blob[at:at + capacity]
        if b'\0' not in cell:
            raise ValueError('Unterminated narration caption')
        raw = cell.split(b'\0', 1)[0]
        if not raw:
            continue
        if index != previous + 1:
            page += 1
        previous = index
        rows.append(dict(id='aid:%d:%x' % (mid, at), family='opening',
            text=raw.decode('cp932'), raw=raw, encoding='cp932', offset=at,
            member=mid, record=index, page=page))
    return rows


def inspect(archive):
    members = {}
    rows = []
    for entry in archive.files:
        blob = archive.read(entry)
        if blob[4:8] != SIGNATURE:
            continue
        mid = entry['id']
        captions = records(blob, mid)
        members[str(mid)] = dict(source_sha256=sha256(blob),
            records=struct.unpack_from('>H', blob)[0], caption_capacity=blob[2],
            stride=blob[2]+30, captions=len(captions))
        rows.extend(captions)
    return dict(schema=1, members=members,
        excluded=dict(member=25, kind='staff-credit roll', signature='2424242a'),
        captions=len(rows), unique_captions=len({r['text'] for r in rows})), rows


def sources(archive):
    report, rows = inspect(archive)
    expected = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if report != expected:
        raise ValueError('Narration inventory differs from reviewed source manifest')
    return rows


def main():
    import argparse
    from tools.cpk import CPK
    from tools.pipeline import config, verified_source
    from tools.aid_art import ARCHIVE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    with CPK(verified_source(config(ROOT/'config/tengoku.json'), ARCHIVE)) as archive:
        report, rows = inspect(archive)
    print(json.dumps(report, indent=2))
    for row in rows[:8]:
        print(row['id'], row['text'])
    if args.apply:
        write_json(MANIFEST, report)


if __name__ == '__main__':
    main()
