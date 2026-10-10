"""Source-bound layout profiles for exceptional dialogue records."""
CONDENSED = {
    '604:t_6:4': '3a93a41e5e',
    '81:t_1:64': '4e0167391c',
    '117:t_1:76': '8ff07ee44b',
    '599:t_014:12': '3c3d6556d0',
    '634:t_1:123': 'c043db3002',
}
PREFIX = '@condensed:'
SCALE = 0.85


def condensed(rid, entry=None):
    if rid not in CONDENSED:
        return False
    if entry is not None and entry.get('sha') != CONDENSED[rid]:
        raise ValueError('Condensed layout source fingerprint changed: ' + rid)
    return True


def advance(width):
    return max(1, round(width * SCALE))


def mapping_for(rid, mapping):
    if not condensed(rid):
        return mapping
    result = dict(mapping)
    for token, code in mapping.items():
        if token.startswith(PREFIX):
            result[token[len(PREFIX):]] = code
    return result
