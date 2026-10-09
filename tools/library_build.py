"""Render Tengoku library (encyclopedia) entries into game bytes.

Prose tokens expand through the library glossary; names come from the terms
bound to each library field. Text is wrapped to the measured panel width
(38 fullwidth cells = 1216 VWF units: 8,153 of the Japanese lines are exactly
38 cells) and encoded as one allocated font cell per Latin character, cp932
for anything Japanese, LF for line breaks. Records keep their original order,
header and every field this module does not translate.
"""
import json
import re
import struct
import unicodedata
from pathlib import Path

from tools import library_compare as lc
from tools.library_text import NAME_FIELDS, SERIES_FIELD, TOKEN, Resolver, placeholder
from tools.source_text import library_fields

VOICE_ACTORS = Path(__file__).resolve().parents[1] / 'work/glossary/library_voice_actors.json'
# 、 and ／ separate people; ・ joins the parts of one katakana name (リディ・マーセナス).
NAME_SEPARATORS = re.compile(r'([、／])')
LINE_UNITS = 38 * 32
INDENT = '　'            # the Japanese paragraph indent, drawn from the original font
FULLWIDTH = 32
STAT_FIELDS = ('HEIT', 'WEIT')


def expand(text, resolver):
    """Expand $$tokens$$; capitalize a token's lower-case English at a sentence start."""
    out, starts, pos = [], [], 0
    for m in TOKEN.finditer(text):
        out.append(text[pos:m.start()])
        term, problem = resolver.resolve(m.group(1))
        if problem or not term['en']:
            raise ValueError('unresolved token %s: %s' % (m.group(0), problem or 'no English'))
        english = term['en']
        if m.group(2):
            english = english[0].lower() + english[1:]
        starts.append(sum(len(p) for p in out))
        out.append(english)
        pos = m.end()
    out.append(text[pos:])
    result = list(''.join(out))
    for i in starts:
        before = ''.join(result[:i]).rstrip(" '")
        if result[i].islower() and (not before or before.endswith(('.', '!', '?', '\n'))):
            result[i] = result[i].upper()
    return ''.join(result)


def stat(text):
    """'５７．０ｍ' -> '57.0m', '－－－' -> '---'."""
    return unicodedata.normalize('NFKC', text).replace('−', '-')


def wrap(text, width_of, units=LINE_UNITS):
    """Word-wrap each paragraph to `units`; paragraphs start with the Japanese indent."""
    lines = []
    for paragraph in text.split('\n'):
        line, used = INDENT, width_of(INDENT)
        for word in paragraph.split(' '):
            w = sum(width_of(c) for c in word)
            gap = width_of(' ') if line.strip(INDENT) else 0
            if used + gap + w <= units:
                line, used = line + (' ' if gap else '') + word, used + gap + w
                continue
            if line.strip(INDENT):
                lines.append(line)
            line, used = '', 0
            while sum(width_of(c) for c in word) > units:     # a word wider than a line
                cut = 1
                while sum(width_of(c) for c in word[:cut + 1]) <= units:
                    cut += 1
                lines.append(word[:cut])
                word = word[cut:]
            line, used = word, sum(width_of(c) for c in word)
        lines.append(line)
    return '\n'.join(lines)


def encode(text, mapping):
    out = bytearray()
    for ch in text:
        if ch == '\n':
            out += b'\n'
        elif ch in mapping:
            out += bytes.fromhex(mapping[ch])
        else:
            out += ch.encode('cp932')     # Japanese text stays in the game's own font
    return bytes(out)


def decode(data, mapping):
    inverse = {bytes.fromhex(code): ch for ch, code in mapping.items()}
    out, i = [], 0
    while i < len(data):
        if data[i] == 0x0a:
            out.append('\n'); i += 1
        elif data[i:i + 2] in inverse:
            out.append(inverse[data[i:i + 2]]); i += 2
        elif data[i] >= 0x81:
            out.append(data[i:i + 2].decode('cp932')); i += 2
        else:
            out.append(data[i:i + 1].decode('ascii')); i += 1
    return ''.join(out)


def name_text(kind, tid, field, record, by_target):
    """English for a name field, or None to keep the original bytes."""
    jp = (record['text'][field] or '').strip()
    if placeholder(jp):
        return None
    term = by_target.get((kind, tid, field))
    if not term or not term['en']:
        return None
    if field == SERIES_FIELD[kind] and jp.startswith('「') and jp.endswith('」'):
        return '「%s」' % term['en']
    return term['en']


def load_voice_actors():
    """{Japanese credit: romanized}; placeholders are never looked up."""
    return json.loads(VOICE_ACTORS.read_text(encoding='utf-8'))['actors']


def voice_actor(text, catalog):
    """Fail closed: a new or changed credit must be researched, not guessed."""
    credit = (text or '').strip()
    if placeholder(credit):
        return None
    if credit not in catalog:
        raise ValueError('unmapped voice actor credit: %r' % credit)
    return catalog[credit]


def pilot_names(text, resolver):
    """Robot PLTN: each name (joined by 、・／) through the glossary; placeholders kept."""
    value = (text or '').strip()
    if placeholder(value) or value.startswith('※'):
        return None
    parts = NAME_SEPARATORS.split(value)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(', ')
            continue
        term, problem = resolver.resolve(part)
        if problem or not term['en']:
            raise ValueError('PLTN name without English: %r' % part)
        out.append(term['en'])
    return ''.join(out)


def render(kind, tid, record, entry, resolver, by_target, actors=None):
    """Unwrapped English per translated field: {tag: text}."""
    fields = {}
    for field in NAME_FIELDS[kind] + (SERIES_FIELD[kind],):
        text = name_text(kind, tid, field, record, by_target)
        if text is not None:
            fields[field] = text
    if kind == 'robot' and 'PLTN' in record['text']:
        text = pilot_names(record['text']['PLTN'], resolver)
        if text is not None:
            fields['PLTN'] = text
    if kind == 'pilot' and actors is not None and 'ACTR' in record['text']:
        text = voice_actor(record['text']['ACTR'], actors)
        if text is not None:
            fields['ACTR'] = text
    for field in STAT_FIELDS:
        if field in record['text'] and record['text'][field]:
            fields[field] = stat(record['text'][field])
    dscr = expand(entry['DSCR'], resolver)
    fields['DSCR'] = dscr
    fields['DSC2'] = expand(entry['DSC2'], resolver) if entry.get('DSC2') is not None else dscr
    return fields


def rebuild(raw, payloads):
    """Original obfuscated record -> record with `payloads` {tag: bytes} replaced."""
    data = bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in raw)
    _, fields = library_fields(raw)
    body = b''
    for f in fields:
        payload = payloads.get(f['tag'], data[f['offset']:f['offset'] + f['bytes']])
        body += f['tag'].encode('ascii') + struct.pack('<I', len(payload)) + payload
    block = b'DATA' + struct.pack('<I', len(body)) + body
    out = data[:16] + b'DSIZ' + struct.pack('<I', len(block)) + block
    return bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in out)


def plan(library, entries, terms):
    """{kind: {tid: {tag: unwrapped text}}} for every library entry."""
    resolver = Resolver(terms)
    by_target = {(tg['archive'], tg['tengoku_id'], tg['field']): t for t in terms for tg in t['targets']}
    actors = load_voice_actors()
    result = {}
    for kind, (tengoku, _, _) in library.items():
        result[kind] = {}
        for tid, record in sorted(tengoku.items()):
            _, entry = entries[kind][str(tid)]
            result[kind][tid] = render(kind, tid, record, entry, resolver, by_target, actors)
    return result


def characters(rendered):
    """Every character that needs a Latin font cell."""
    chars = set()
    for texts in rendered.values():
        for fields in texts.values():
            for text in fields.values():
                chars.update(c for c in text if c != '\n' and ord(c) < 0x80)
    return chars
