"""Shared local-output and provenance helpers (Python 3.8+)."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def contained(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    if root != path and root not in path.parents:
        raise ValueError('path escapes output root: %s' % path)
    return path


def destination(root, relative):
    # Reject Windows drive/ADS names even when testing on another platform.
    parts = relative.replace('\\', '/').split('/')
    if not parts or any(p in ('', '.', '..') or ':' in p for p in parts):
        raise ValueError('unsafe archive path: %r' % relative)
    return contained(root, Path(root).joinpath(*parts))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A report can be regenerated; binary outputs use exclusive creation.
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.replace(str(temporary), str(path))
