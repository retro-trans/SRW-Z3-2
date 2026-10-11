"""Translate the parts comparison's own three fixed UTF-8 movement cells."""
import struct
from tools.common import sha256
from tools import ui_hook as H,status_layout as S,vwf

CELLS=((0x855dae,'空','Air'),(0x855db2,'陸','Grd'),(0x855db6,'水','Wtr'))

def apply(elf,original):
    if sha256(original)!=vwf.ELF_SHA256:raise ValueError('Parts movement baseline changed')
    read=H._reader(original,H._headers(original)[2])
    if struct.unpack('>I',read(H.TOC-0x15a8,4))[0]!=0x855c0c:raise ValueError('Parts movement table binding changed')
    for va in (0x3150e8,0x31532c):
        if read(va,4)!=bytes.fromhex('83a2ea58'):raise ValueError('Parts formatter source changed')
    out=bytearray(elf);ranges=[]
    for va,jp,en in CELLS:
        at=va-0x10000;raw=jp.encode('utf8')+b'\0'
        if elf[at:at+4]!=raw:raise ValueError('Parts movement cell changed')
        out[at:at+4]=S.CELL[en].encode('utf8')+b'\0';ranges.append((at,at+4))
    restored=bytearray(out)
    for a,b in ranges:restored[a:b]=elf[a:b]
    if restored!=elf:raise ValueError('Parts movement changed unrelated bytes')
    return bytes(out),dict(cells=3,modified_file_ranges=ranges,consumers=[0x3150e8,0x31532c],runtime_verified=False)
