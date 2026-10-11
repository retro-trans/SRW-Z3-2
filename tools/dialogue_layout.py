"""Source-bound layout profiles for exceptional dialogue records."""
CONDENSED = {
    '604:t_6:4': '3a93a41e5e',
    '81:t_1:64': '4e0167391c',
    '117:t_1:76': '8ff07ee44b',
    '599:t_014:12': '3c3d6556d0',
    '634:t_1:123': 'c043db3002',
    '81:t_2:28': 'd4d7a7912c',
    '153:t_1:79': 'bfca89baf1',
    '153:t_3:33': 'eb527edd60',
    '218:t_1:47': '8aea30f429',
    '224:t_3:56': '606ad02f81',
    '265:t_2:68': 'b7b4b46bca',
    '335:t_1:12': '43b6c642d9',
    '335:t_1:155': '716d0facb5',
    '604:t_2:9': '897948c58f',
    '758:t_1:314': '6cb5240bc4',
    '758:t_1:330': 'ad08f2dc47',
}
PREFIX = '@condensed:'
SCALE = 0.85
TIGHT_PREFIX = '@condensed-tight:'
TIGHT_SCALE = 0.8
TIGHT_IDS = {'604:t_6:4'}


def prefix(rid):
    return TIGHT_PREFIX if rid in TIGHT_IDS else PREFIX


def scale(rid):
    return TIGHT_SCALE if rid in TIGHT_IDS else SCALE


def condensed(rid, entry=None):
    if rid not in CONDENSED:
        return False
    if entry is not None and entry.get('sha') != CONDENSED[rid]:
        raise ValueError('Condensed layout source fingerprint changed: ' + rid)
    return True


def advance(width, horizontal_scale=SCALE):
    return max(1, round(width * horizontal_scale))


def mapping_for(rid, mapping):
    if not condensed(rid):
        return mapping
    result = dict(mapping)
    for token, code in mapping.items():
        selected = prefix(rid)
        if token.startswith(selected):
            result[token[len(selected):]] = code
    return result
