"""Write a Tengoku test ISO that keeps the original disc layout.

Ported from Jigoku's platforms/ps3/preserved_iso.py and cfw_package.stamp_disc,
with Tengoku's title ID, file count and multi-extent reader. Dry run by default.

The original ISO is copied; each replaced file is APPENDED on a sector boundary
and its record in BOTH the primary and Joliet trees is repointed. The stale UDF
tree is zeroed so no reader finds it, and the PS3 disc header gets one
whole-disc plaintext region (the image is already decrypted). Nothing trusts
the writer's own offsets: the finished image is re-parsed and every file is
hashed through each tree against the expected contents.

RPCS3 only: the EBOOT is a plain ELF. A real console would need a fake-SELF
wrapper, which Tengoku has not tested.
"""
import argparse
import json
import shutil
import struct
from pathlib import Path

from tools.common import ROOT, contained, sha256_file, write_json
from tools.isoread import ISO9660, SECTOR
from tools.pipeline import config

TITLE = b'BLJS-10299'
BLOCK = 4 << 20
UDF_VRS = (b'BEA01', b'NSR02', b'NSR03', b'TEA01', b'BOOT2', b'CDW02')
JOLIET = (b'%/@', b'%/C', b'%/E')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def descriptors(fh):
    """[(kind, lba, descriptor bytes)] for the primary and Joliet trees."""
    found = []
    for lba in range(16, 64):
        fh.seek(lba * SECTOR)
        d = fh.read(SECTOR)
        require(d[1:6] == b'CD001', 'invalid volume descriptor')
        if d[0] == 255:
            return found
        if d[0] == 1:
            found.append(('primary', lba, d))
        elif d[0] == 2 and d[88:91] in JOLIET:
            found.append(('joliet', lba, d))
    raise ValueError('no descriptor terminator')


def walk(fh, descriptor, joliet):
    """{path: [(record offset, lba, size, flags)]} plus every owned sector."""
    files, owned = {}, set()
    table = struct.unpack_from('<I', descriptor, 132)[0]
    for off, fmt in ((140, '<I'), (144, '<I'), (148, '>I'), (152, '>I')):
        lba = struct.unpack_from(fmt, descriptor, off)[0]
        if lba:
            owned.update(range(lba, lba + -(-table // SECTOR)))
    root = descriptor[156:156 + 34]
    pending = [('', struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0])]
    seen = set()
    while pending:
        prefix, lba, size = pending.pop()
        if lba in seen:
            continue
        seen.add(lba)
        owned.update(range(lba, lba + -(-size // SECTOR)))
        fh.seek(lba * SECTOR)
        data = fh.read(size)
        pos = 0
        while pos < len(data):
            length = data[pos]
            if not length:
                pos = (pos // SECTOR + 1) * SECTOR
                continue
            rec = data[pos:pos + length]
            raw = rec[33:33 + rec[32]]
            if raw not in (b'\x00', b'\x01'):
                name = (raw.decode('utf-16-be') if joliet else raw.decode('ascii')).rsplit(';', 1)[0]
                elba, esize, flags = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0], rec[25]
                path = prefix + '/' + name
                if flags & 2:
                    pending.append((path, elba, esize))
                else:
                    files.setdefault(path.upper(), []).append((lba * SECTOR + pos, elba, esize, flags))
                    owned.update(range(elba, elba + -(-esize // SECTOR)))
            pos += length
    return files, owned


def udf_sectors(fh, total):
    """Every sector that makes the UDF tree discoverable (recognition + anchors + sequences)."""
    found, lba = [], 16
    while True:
        fh.seek(lba * SECTOR)
        head = fh.read(6)
        lba += 1
        if head[1:6] != b'CD001' or head[0] == 255:
            break
    while True:
        fh.seek(lba * SECTOR)
        head = fh.read(6)
        if head[1:6] not in UDF_VRS:
            break
        found.append(lba)
        lba += 1
    for anchor in sorted({256, total - 256, total - 1}):
        if not 256 <= anchor < total:
            continue
        fh.seek(anchor * SECTOR)
        tag = fh.read(32)
        if len(tag) == 32 and struct.unpack_from('<H', tag, 0)[0] == 2:
            found.append(anchor)
            for off in (16, 24):
                length, loc = struct.unpack_from('<II', tag, off)
                found.extend(range(loc, loc + -(-length // SECTOR)))
    return sorted(set(found))


def stamp_disc(path):
    """One whole-disc plaintext region, PS3 identifier and volume size (ps3netsrv padding)."""
    sectors = path.stat().st_size // SECTOR
    padding = 32 + (-sectors % 32)
    sectors += padding
    with path.open('r+b') as fh:
        fh.seek(0, 2)
        fh.write(bytes(padding * SECTOR))
        system = bytearray(16 * SECTOR)
        struct.pack_into('>IIII', system, 0, 1, 0, 0, sectors - 1)
        system[SECTOR:SECTOR + 12] = b'PlayStation3'
        system[SECTOR + 16:SECTOR + 48] = TITLE.ljust(32, b' ')
        fh.seek(0)
        fh.write(system)
        for kind, lba, _ in descriptors(fh):
            fh.seek(lba * SECTOR + 80)
            fh.write(struct.pack('<I', sectors) + struct.pack('>I', sectors))
    return sectors


def write(source, image, replacements, manifest):
    """replacements: {disc path: local file}; manifest: source files with sha256."""
    require(not image.exists(), 'refusing to overwrite ' + str(image))
    known = {f['path'].upper() for f in manifest}
    for disc in replacements:
        require(disc.upper() in known, 'not on the source disc: ' + disc)
    expected = expected_files(replacements, manifest)
    print('Copying source ISO...', flush=True)
    shutil.copyfile(source, image)
    with image.open('r+b') as fh:
        trees = descriptors(fh)
        require(sorted(k for k, _, _ in trees) == ['joliet', 'primary'], 'expected one primary and one Joliet tree')
        total = fh.seek(0, 2)
        require(total % SECTOR == 0, 'unaligned source ISO')
        records, owned = {}, set(range(16, 16 + len(trees) + 1))
        for kind, _, d in trees:
            files, sectors = walk(fh, d, kind == 'joliet')
            records[kind] = files
            owned |= sectors
        udf = udf_sectors(fh, total // SECTOR)
        require(not owned.intersection(udf), 'UDF sectors overlap ISO9660 data')
        next_lba = total // SECTOR
        for disc in sorted(replacements):
            local = replacements[disc]
            size = local.stat().st_size
            require(size < 2 ** 32, 'file too large for one extent: ' + disc)
            for kind in ('primary', 'joliet'):
                require(len(records[kind].get(disc.upper(), [])) == 1,
                        'replaced file must have exactly one %s record: %s' % (kind, disc))
            lba = next_lba
            fh.seek(lba * SECTOR)
            with local.open('rb') as src:
                shutil.copyfileobj(src, fh, BLOCK)
            fh.write(bytes(-size % SECTOR))
            next_lba += -(-size // SECTOR)
            for kind in ('primary', 'joliet'):
                off = records[kind][disc.upper()][0][0]
                fh.seek(off + 2)
                fh.write(struct.pack('<I', lba) + struct.pack('>I', lba))
                fh.seek(off + 10)
                fh.write(struct.pack('<I', size) + struct.pack('>I', size))
        for lba in udf:
            fh.seek(lba * SECTOR)
            fh.write(bytes(SECTOR))
    sectors = stamp_disc(image)
    return verify(image, expected, sectors, source)


def expected_files(replacements, manifest):
    expected = {f['path'].upper(): {'path': f['path'], 'bytes': f['size'], 'sha256': f['sha256']} for f in manifest}
    for disc, local in replacements.items():
        expected[disc.upper()] = {'path': disc, 'bytes': local.stat().st_size, 'sha256': sha256_file(local)}
    return expected


def primary_names(source):
    """Joliet path -> primary path. The primary tree holds shortened ISO9660
    names (KANJI_FIX.BN for KANJI-FIX.BN), so the trees pair by first extent."""
    with ISO9660(source, joliet=True) as iso:
        joliet = {e['extents'][0]['lba']: p.upper() for p, e in iso.walk()}
    with ISO9660(source, joliet=False) as iso:
        primary = {e['extents'][0]['lba']: p.upper() for p, e in iso.walk()}
    require(set(joliet) == set(primary), 'primary and Joliet trees list different files')
    return {joliet[lba]: primary[lba] for lba in joliet}


def verify(image, expected, sectors, source):
    with image.open('rb') as fh:
        system = fh.read(16 * SECTOR)
        require(struct.unpack_from('>IIII', system) == (1, 0, 0, sectors - 1), 'stale disc regions')
        require(system[SECTOR + 16:SECTOR + 26] == TITLE, 'wrong title ID')
        require(not udf_sectors(fh, image.stat().st_size // SECTOR), 'UDF tree still discoverable')
    names = primary_names(source)
    for joliet in (True, False):
        print('Verifying %s tree...' % ('Joliet' if joliet else 'primary'), flush=True)
        with ISO9660(image, joliet=joliet) as iso:
            actual = {path.upper(): entry for path, entry in iso.walk()}
            keys = {k if joliet else names[k]: k for k in expected}
            require(set(actual) == set(keys), 'disc inventory changed')
            for name, key in keys.items():
                want, entry = expected[key], actual[name]
                require(entry['size'] == want['bytes'], 'size mismatch: ' + want['path'])
                import hashlib
                h = hashlib.sha256()
                for block in iso.blocks(entry):
                    h.update(block)
                require(h.hexdigest() == want['sha256'], 'content mismatch: ' + want['path'])
    return {'image': str(image), 'bytes': image.stat().st_size, 'sectors': sectors,
            'files_verified_each_tree': len(expected), 'udf': 'absent', 'plaintext_regions': 1,
            'sha256': sha256_file(image)}


def main():
    from tools.game_build import LIBRARY, VERSION
    from tools.inventory import RPW, FONT
    from tools.self_elf import EBOOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', default='work/output/builds/' + VERSION)
    parser.add_argument('--out', default='work/output/iso/%s/Tengoku-hen-English-%s.iso' % (VERSION, VERSION))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--verify-only', action='store_true', help='re-verify an image already written')
    args = parser.parse_args()
    settings = config(ROOT / 'config/tengoku.json')
    build = contained(ROOT / 'work', ROOT / args.build)
    image = contained(ROOT / 'work', ROOT / args.out)
    manifest = json.loads((settings['work'] / 'source_manifest.json').read_text(encoding='utf-8'))
    report = json.loads((build / 'build.json').read_text(encoding='utf-8'))
    replacements = {EBOOT: build / 'EBOOT.BIN', RPW: build / 'RPW_DATA.CPK', FONT: build / 'TPACKPS3.CPK'}
    replacements.update({path: build / Path(path).name for path in LIBRARY.values()})
    if 'STGZ3OF2.SDAT' in report['outputs']:
        from tools.dialogue_build import STAGE_ARCHIVE
        replacements[STAGE_ARCHIVE] = build / 'STGZ3OF2.SDAT'
    if 'SRVC.BIN' in report['outputs']:
        from tools.srvc import SRVC
        replacements[SRVC] = build / 'SRVC.BIN'
    # Further archives the build replaced (art packs...): {disc path: output name}.
    for disc, name in report.get('disc_files', {}).items():
        if disc in replacements:
            raise ValueError('disc file listed twice: ' + disc)
        replacements[disc] = build / name
    for disc, local in replacements.items():
        require(sha256_file(local) == report['outputs'][local.name], 'build output changed: ' + local.name)
        print('%-52s <- %s (%d bytes)' % (disc, local.name, local.stat().st_size))
    print('source:', settings['iso'])
    print('output:', image)
    if args.verify_only:
        result = verify(image, expected_files(replacements, manifest['files']),
                        image.stat().st_size // SECTOR, Path(settings['iso']))
    elif not args.apply:
        print('DRY RUN: no image written')
        return
    else:
        image.parent.mkdir(parents=True, exist_ok=True)
        result = write(Path(settings['iso']), image, replacements, manifest['files'])
    result.update(version=VERSION, build=str(build), replaced={d: l.name for d, l in replacements.items()},
                  source_iso_sha256=manifest['iso_sha256'], rpcs3_only=True, runtime_verified=False)
    write_json(image.with_suffix('.json'), result)
    print('VERIFIED %s: %d files through both trees; sha256 %s' % (image.name, result['files_verified_each_tree'], result['sha256']))


if __name__ == '__main__':
    main()
