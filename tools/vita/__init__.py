"""Tengoku Vita adapters with isolated, pinned local binary dependencies."""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parents[2]
for _path in (_root/'work/output/tool-deps/pillow-12.3.0',
              _root/'work/output/tool-deps/vita-py312win64'):
    if _path.is_dir():
        sys.path.insert(0, str(_path))
