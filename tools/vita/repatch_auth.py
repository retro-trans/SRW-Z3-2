"""Keep only rePatch's authority/capability fields; never publish raw auth."""
import struct


def sanitize(data,authority):
    if len(data)!=0x90 or struct.unpack_from('<Q',data)[0]!=authority or not any(data[0x10:0x50]):
        raise ValueError('Expected a matching 144-byte Tengoku-hen console auth dump')
    # rePatch's auth hook reads the authority and copies [0x10,0x50).
    # Padding, shared secrets and the license-key region are never retained.
    # https://github.com/dots-tb/rePatch-reDux0/blob/master/repatch.c
    return data[:8]+bytes(8)+data[0x10:0x50]+bytes(0x40)
