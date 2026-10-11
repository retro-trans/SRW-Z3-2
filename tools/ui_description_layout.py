"""Measured VWF wrapping using the conservative Jigoku description panels.

Skill: 740 px; part: 540 px, at a 28 px live glyph size, three lines.
These are reference budgets; Tengoku screenshots still require runtime QA.
"""
import functools

PIXELS = {'skills': 740, 'parts': 540}
GLYPH_SIZE = 28
MAX_LINES = 3


@functools.lru_cache(maxsize=None)
def advance(char):
    from tools.ui_vwf_build import raster
    try:
        return raster(char)[1] if 32 <= ord(char) < 127 else 32
    except ValueError:
        return 32


def wrap(text, units, width_of=advance):
    """Move whitespace only; reject any word or complete meaning that won't fit."""
    lines = ['']
    for word in text.replace('\\n', ' ').split():
        if sum(width_of(c) for c in word)>units:
            raise ValueError('Description word exceeds line width: '+word)
        joined = (lines[-1]+' '+word).strip()
        if sum(width_of(c) for c in joined)>units and lines[-1]:
            lines.append(word)
        else:
            lines[-1] = joined
    if len(lines)>MAX_LINES:
        raise ValueError('Complete description exceeds three lines')
    return '\n'.join(lines)


def render(text, sources):
    return profile(text,sources)[0]


def condensed_advance(char):
    from tools.dialogue_layout import advance as scaled
    return scaled(advance(char)) if ord(char)<128 else 32


def profile(text,sources):
    families = {s['family'] for s in sources} & set(PIXELS)
    if not families:
        return text,False
    units = int(min(PIXELS[f] for f in families)*32/GLYPH_SIZE)
    try:
        return wrap(text,units),False
    except ValueError:
        return wrap(text,units,condensed_advance),True


def report(grouped, translations, resolver):
    from tools import library_build as lb, eboot_text
    rows = {}
    for rid, sources in grouped.items():
        if not any(s['family'] in PIXELS for s in sources):
            continue
        text,condensed = profile(eboot_text.unshow(lb.expand(translations[rid]['en'],resolver)),sources)
        measure = condensed_advance if condensed else advance
        rows[rid] = dict(lines=len(text.split('\n')),
            condensed=condensed,
            max_line_units=max(sum(measure(c) for c in line) for line in text.split('\n')))
    return dict(descriptions=len(rows),max_lines=max(r['lines'] for r in rows.values()),
        budgets_pixels=PIXELS,glyph_size=GLYPH_SIZE,reference='SRW Z3 description panels',
        condensed_descriptions=sum(r['condensed'] for r in rows.values()),runtime_verified=False,rows=rows)
