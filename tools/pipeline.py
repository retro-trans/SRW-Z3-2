"""Local Tengoku source pipeline. Mutating commands default to dry run.

python -m tools.pipeline inspect
python -m tools.pipeline extract --apply
python -m tools.pipeline prepare --apply
python -m tools.pipeline verify --apply
"""
import argparse
import json
import os
import struct
import subprocess
from pathlib import Path

from tools.common import ROOT, contained, destination, sha256_file, write_json
from tools.isoread import ISO9660


def sfo_values(data):
    if data[:4] != b'\0PSF' or len(data) < 20:
        raise ValueError('not a PARAM.SFO')
    _, key_base, value_base, count = struct.unpack_from('<4I', data, 4)
    if not 20 + count * 16 <= key_base <= value_base <= len(data):
        raise ValueError('invalid SFO table bounds')
    values = {}
    for index in range(count):
        key_offset, form, size, maximum, value_offset = struct.unpack_from('<HHIII', data, 20 + index * 16)
        start = key_base + key_offset
        end = data.find(b'\0', start, value_base)
        if not key_base <= start < value_base or end < 0 or size > maximum or value_base + value_offset + maximum > len(data):
            raise ValueError('invalid SFO field')
        key = data[start:end].decode('ascii')
        if key in values:
            raise ValueError('duplicate SFO key')
        payload = data[value_base + value_offset:value_base + value_offset + size]
        if form == 0x204:
            values[key] = payload.rstrip(b'\0').decode('utf-8')
        elif form == 0x404 and size == 4:
            values[key] = struct.unpack('<I', payload)[0]
    return values


def config(path):
    settings = json.loads(Path(path).read_text(encoding='utf-8'))
    if settings.get('schema') != 1 or settings.get('title_id') != 'BLJS10299':
        raise ValueError('configuration is not for Tengoku BLJS10299')
    work = contained(ROOT / 'work', ROOT / settings['workspace'])
    if work == (ROOT / 'work').resolve():
        raise ValueError('use a dedicated directory under work/')
    settings['work'] = work
    return settings


def inspect(settings):
    with ISO9660(settings['iso']) as iso:
        files = list(iso.walk())
        by_path = dict(files)
        values = sfo_values(iso.read(by_path['/PS3_GAME/PARAM.SFO']))
        if values.get('TITLE_ID') != settings['title_id']:
            raise ValueError('ISO title ID does not match configuration')
        return {'schema': 1, 'title_id': values['TITLE_ID'], 'iso_path': str(iso.path.resolve()),
                'iso_bytes': iso.size, 'joliet': iso.joliet,
                'sfo': {k: values[k] for k in ('TITLE_ID', 'TITLE', 'APP_VER', 'VERSION') if k in values},
                'logical_files': len(files), 'logical_bytes': sum(e['size'] for _, e in files),
                'files': [dict(e, path=p) for p, e in files]}


def extract(settings, apply):
    report = inspect(settings)
    output = settings['work'] / 'source'
    # Validate every path before the first write, including case collisions.
    targets = [destination(output, e['path'].lstrip('/')) for e in report['files']]
    if len({str(p).casefold() for p in targets}) != len(targets):
        raise ValueError('case-colliding output paths')
    print('%s: extract %d logical files (%d bytes) to %s' %
          ('APPLY' if apply else 'DRY RUN', report['logical_files'], report['logical_bytes'], output), flush=True)
    for entry in report['files']:
        if len(entry['extents']) > 1:
            print('  JOIN %s: %s -> %d bytes' % (entry['path'], [e['size'] for e in entry['extents']], entry['size']))
    for entry in report['files'][:5]:
        print('  %s (%d bytes)' % (entry['path'], entry['size']))
    if not apply:
        return report
    if output.exists():
        raise ValueError('source output already exists; verify it or use a fresh configured workspace')
    original_stat = Path(settings['iso']).stat()
    report['iso_sha256'] = sha256_file(settings['iso'])
    output.mkdir(parents=True)
    with ISO9660(settings['iso']) as iso:
        for index, (entry, target) in enumerate(zip(report['files'], targets), 1):
            target.parent.mkdir(parents=True, exist_ok=True)
            entry['sha256'] = iso.copy(entry, target)
            if sha256_file(target) != entry['sha256'] or target.stat().st_size != entry['size']:
                raise ValueError('extraction readback failed: ' + entry['path'])
            if index % 10 == 0 or len(entry['extents']) > 1 or index == len(targets):
                print('  verified %d/%d: %s' % (index, len(targets), entry['path']), flush=True)
    current_stat = Path(settings['iso']).stat()
    if (original_stat.st_size, original_stat.st_mtime_ns) != (current_stat.st_size, current_stat.st_mtime_ns):
        raise ValueError('ISO changed during extraction')
    report['readback_verified_files'] = len(targets)
    write_json(settings['work'] / 'source_manifest.json', report)
    return report


def source_manifest(settings):
    report = json.loads((settings['work'] / 'source_manifest.json').read_text(encoding='utf-8'))
    if report['title_id'] != settings['title_id']:
        raise ValueError('source manifest title mismatch')
    return report


def verified_source(settings, path):
    report = source_manifest(settings)
    matches = [e for e in report['files'] if e['path'] == path]
    if len(matches) != 1:
        raise ValueError('source path missing or duplicated in manifest: ' + path)
    entry = matches[0]
    file = destination(settings['work'] / 'source', path.lstrip('/'))
    if file.stat().st_size != entry['size'] or sha256_file(file) != entry['sha256']:
        raise ValueError('pristine source drift: ' + path)
    return file


def prepare(settings, apply):
    from tools.inventory import prepare_inventory
    stage_path = '/PS3_GAME/USRDIR/DATA/STAGE/STGZ3OF2.SDAT'
    source = verified_source(settings, stage_path)
    output = settings['work'] / 'prepared'
    tool = Path(settings['offline_sdat_tool']).resolve()
    if not tool.is_file():
        raise ValueError('offline SDAT utility missing: ' + str(tool))
    print('%s: decrypt %s offline and inventory stage, RPW, library and selected UI archives into %s' %
          ('APPLY' if apply else 'DRY RUN', stage_path, output), flush=True)
    if not apply:
        return
    if output.exists():
        raise ValueError('prepared output already exists; use a fresh workspace for regeneration')
    output.mkdir(parents=True)
    decoded = output / 'STGZ3OF2.dec.cpk'
    result = subprocess.run([str(tool), '-d', str(source), str(decoded), '0'],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
                            cwd=str(output), creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (output / 'sdat-decrypt.log').write_bytes(result.stdout)
    if result.returncode or not decoded.is_file() or decoded.read_bytes()[:4] != b'CPK ':
        raise ValueError('offline SDAT decryption failed; see sdat-decrypt.log')
    provenance = {'tool_path': str(tool), 'tool_sha256': sha256_file(tool),
                  'encrypted_sha256': sha256_file(source), 'decoded_sha256': sha256_file(decoded),
                  'returncode': result.returncode, 'runtime_verified': False}
    report = prepare_inventory(settings, decoded, output)
    report['sdat'] = provenance
    report['source_iso_sha256'] = source_manifest(settings)['iso_sha256']
    write_json(output / 'inventory_summary.json', report)
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)


def verify(settings, apply):
    from tools.verify_archives import verify_workspace
    print('%s: verify extracted files and CPK no-op/growth round trips in %s' %
          ('APPLY' if apply else 'DRY RUN', settings['work'] / 'verification'), flush=True)
    if apply:
        report = verify_workspace(settings)
        print(json.dumps(report, ensure_ascii=True, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(ROOT / 'config/tengoku.json'))
    parser.add_argument('command', choices=('inspect', 'extract', 'prepare', 'verify'))
    parser.add_argument('--apply', action='store_true', help='write local outputs after reviewing the dry run')
    args = parser.parse_args()
    settings = config(args.config)
    try:
        if args.command == 'inspect':
            report = inspect(settings)
            print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=True, indent=2))
            for entry in report['files']:
                print('%12d  %s%s' % (entry['size'], entry['path'], ' [multi-extent]' if len(entry['extents']) > 1 else ''))
        else:
            globals()[args.command](settings, args.apply)
    except (ValueError, OSError, KeyError, struct.error) as error:
        parser.exit(1, 'ERROR: %s\n' % error)


if __name__ == '__main__':
    main()
