"""Battle voice for the game build: translated lines -> SRVC.BIN edits.

The English comes from work/translation/en/voice/gNNN.json (`lines`, keyed
"<block>:<pool offset>"). Tokens are expanded with the library glossary; each
segment between the game's literal two-character break `\\n` is encoded with
the build's font mapping (Latin -> allocated cells, 「」 -> the game's cp932),
and the break itself stays the raw bytes 5C 6E. tools/voice_write.build does
the rebuild, the executable table rewrite and the independent readback.
"""
import json

from tools import library_build as lb
from tools import srvc
from tools.voice import ANSWERS, BREAK


def translations():
    """{string id: {'jp', 'en'}} for every translated voice line."""
    rows = {}
    for path in sorted(ANSWERS.glob('g*.json')):
        for sid, line in json.loads(path.read_text(encoding='utf-8'))['lines'].items():
            if line.get('en'):
                if sid in rows:
                    raise ValueError('voice string %s appears in two group files' % sid)
                rows[sid] = {'jp': line['jp'], 'en': line['en']}
    return rows


def expanded(rows, resolver):
    return {sid: lb.expand(row['en'], resolver) for sid, row in rows.items()}


def characters(texts):
    chars = set()
    for text in texts:
        for seg in text.split(BREAK):
            chars.update(c for c in seg if ord(c) < 0x80)
    return chars


def encode(text, mapping):
    return b'\\n'.join(lb.encode(seg, mapping) for seg in text.split(BREAK))


def edits(data, tab, rows, texts):
    """One 'string'-scope edit per translated pool string."""
    blocks = srvc.parse(data, tab)
    out = []
    for sid, row in rows.items():
        b, off = map(int, sid.split(':'))
        if b >= len(blocks) or off not in blocks[b].offs:
            raise ValueError('voice string %s is not referenced by its block' % sid)
        out.append({'block': b, 'k': blocks[b].offs.index(off), 'jp': row['jp'],
                    'text': texts[sid], 'scope': 'string'})
    return out
