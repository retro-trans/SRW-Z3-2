"""Export voice translation text without original Japanese scripts.

Preview with python -m tools.voice_repository; add --apply to save.
Exports are review/backup copies, not source-dependent voice build inputs.
"""
import argparse
import hashlib
import json
from tools.common import ROOT, write_json


def export(data):
    if isinstance(data, list):
        return [export(v) for v in data]
    if not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        if key == 'jp':
            if not isinstance(value, str):
                raise ValueError('Unexpected non-text Japanese source')
            if 'repository_source_sha256' in data:
                raise ValueError('Fingerprint field already exists')
            result['repository_source_sha256'] = hashlib.sha256(value.encode('utf-8')).hexdigest()
        else:
            result[key] = export(value)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    base = ROOT / 'work/translation/en'
    planned = []
    row_count = 0
    for family in ('voice', 'voice_new'):
        paths = sorted((base / family).glob('*.json'))
        if not paths:
            raise ValueError('Local source-bearing voice inputs required: ' + family)
        for path in paths:
            original = json.loads(path.read_text(encoding='utf-8'))
            clean = export(original)
            field = 'lines' if family == 'voice' else 'rows'
            assert set(clean[field]) == set(original[field])
            for rid, row in original[field].items():
                assert clean[field][rid].get('en') == row.get('en')
            row_count += len(original[field])
            destination = base / 'voice_text' / family / path.name
            if destination.exists():
                if json.loads(destination.read_text(encoding='utf-8')) != clean:
                    raise ValueError('Existing export differs; review it first: ' + str(destination))
            else:
                planned.append((destination, clean))
    print('Voice records (including overlapping worksets):', row_count)
    print('New English-only export files:', len(planned))
    if planned:
        path, data = planned[0]
        field = 'lines' if 'lines' in data else 'rows'
        rid, row = next(iter(data[field].items()))
        print('Sample:', path.relative_to(ROOT), rid)
        print(json.dumps(row, ensure_ascii=True))
    if args.apply:
        for path, data in planned:
            write_json(path, data)
        print('Exports saved; original working files unchanged.')
    else:
        print('DRY RUN: no files changed.')


if __name__ == '__main__':
    main()
