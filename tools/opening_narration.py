"""Fingerprint-bound opening narration; timing and fixed records stay pristine."""
import struct
from tools.common import sha256

MEMBER = 19
MEMBER_SHA = 'e5015c3ff555f6b20aa0e6c20473e59d57ee3efec1be804ab0e7326d29194b73'
PAGES = (
    (0x14c,0x19a,0x1e8,0x236),
    (0x5de,0x62c,0x67a,0x6c8,0x716,0x764),
    (0x800,0x84e,0x89c,0x8ea,0x938),
    (0xe66,0xeb4,0xf02,0xf50,0xf9e,0xfec),
    (0x151a,0x1568,0x15b6,0x1604,0x1652,0x16a0),
    (0x1d06,),
)


def sources(blob):
    if sha256(blob)!=MEMBER_SHA:
        raise ValueError('Opening narration source changed')
    rows = []
    for page,offsets in enumerate(PAGES,1):
        for at in offsets:
            if (at-20)%78:
                raise ValueError('Narration record boundary changed')
            raw = blob[at:blob.index(0,at,at+78)]
            rows.append(dict(id='aid:19:%x'%at,family='opening',text=raw.decode('cp932'),
                raw=raw,encoding='cp932',offset=at,member=MEMBER,page=page))
    return rows


def validate(text):
    return profile(text)[0]


def profile(text):
    from tools.ui_description_layout import advance,condensed_advance
    if '\n' in text or '\\n' in text:
        raise ValueError('Opening narration must fit its single timed line')
    if sum(map(advance,text))<=900:
        return text,False
    if sum(map(condensed_advance,text))>900:
        raise ValueError('Opening narration must fit its single timed line')
    return text,True
