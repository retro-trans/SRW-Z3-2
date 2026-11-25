"""Capture the original Tengoku Lua failure through Vita3K's local guest debugger.

Diagnostic only: no game file edits, no input injection, no exception suppression.
The debugger must be enabled in the isolated test runtime before launch.
"""
import argparse
import json
import re
import socket
import struct
from pathlib import Path
from tools.common import ROOT, write_json

FAILURE = 0x81103038


class Guest:
    def __init__(self, port=2159):
        self.stream = socket.create_connection(('127.0.0.1', port), timeout=10)

    def receive(self, count):
        result=bytearray()
        while len(result)<count:
            part=self.stream.recv(count-len(result))
            if not part:
                raise EOFError('Guest debugger disconnected')
            result+=part
        return bytes(result)

    def request(self, text, timeout=10):
        payload = text.encode('ascii')
        self.stream.settimeout(timeout)
        self.stream.sendall(b'$'+payload+b'#'+f'{sum(payload)&255:02x}'.encode())
        while self.receive(1) != b'$':
            pass
        result = bytearray()
        while True:
            c = self.receive(1)
            if c == b'#':
                break
            result += c
        checksum = self.receive(2)
        if checksum != f'{sum(result)&255:02x}'.encode():
            raise ValueError('Guest debugger packet checksum differs')
        self.stream.sendall(b'+')
        return result.decode('ascii')

    def memory(self, address, size):
        result = self.request(f'm{address:x},{size:x}')
        if result.startswith('E'):
            raise ValueError('Guest address unavailable: '+hex(address))
        return bytes.fromhex(result)

    def u32(self, address):
        return struct.unpack('<I', self.memory(address, 4))[0]


def capture(output, seconds=1800):
    guest = Guest()
    try:
        # Source-bound original instructions at the native error branch.
        observed = guest.memory(FAILURE, 4)
        original = (ROOT/'work/vita/executables/segment-0.bin').read_bytes()
        if observed != original[FAILURE-0x81000000:FAILURE-0x81000000+4]:
            raise ValueError('Unexpected native error handler; refusing breakpoint')
        result = guest.request(f'Z0,{FAILURE:x},2')
        if result != 'OK':
            raise ValueError('Guest refused the diagnostic breakpoint: '+result)
        print('Armed native Lua failure breakpoint; game resumed.', flush=True)
        stop = guest.request('vCont;c', timeout=seconds)
        thread = re.search(r'thread:([0-9a-fA-F]+)',stop)
        if thread:
            guest.request('Hg'+thread.group(1))
        registers = bytes.fromhex(guest.request('g'))
        words = struct.unpack('<'+'I'*(len(registers)//4), registers)
        report = dict(stop=stop, registers={f'r{i}':hex(x) for i,x in enumerate(words[:16])},
                      native_error_breakpoint=hex(FAILURE), diagnostic_only=True)
        if words[15] & ~1 != FAILURE:
            raise ValueError('Unexpected guest stop: '+json.dumps(report))
        obj = words[5]
        state = guest.u32(obj+4)
        top = guest.u32(state+8)
        value = guest.memory(top-16, 16)
        pointer = struct.unpack_from('<I', value)[0]
        kind = struct.unpack_from('<I', value,8)[0]
        report.update(callback=guest.memory(words[4],96).split(b'\0')[0].decode('ascii','replace'),
                      lua_state=hex(state), lua_error_value_hex=value.hex())
        if kind==4:
            # Native lua_tolstring returns TString + 0x10; its length is at +0x0c.
            length=guest.u32(pointer+12)
            if length>4096:
                raise ValueError('Unexpected native Lua error string extent')
            raw=guest.memory(pointer+16,length)
            report.update(lua_error_bytes_hex=raw.hex(),lua_error=raw.decode('utf8','backslashreplace'))
        else:
            report.update(lua_error_type=kind)
        write_json(output,report)
        print('Captured native Lua error:',output,flush=True)
        guest.request(f'z0,{FAILURE:x},2')
        # No continuation request after collecting the diagnostic stop.
        return report
    finally:
        guest.stream.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'work/vita/first-battle-20261121/lua-failure.json')
    parser.add_argument('--seconds',type=int,default=1800)
    args=parser.parse_args()
    capture(args.output,args.seconds)


if __name__=='__main__':
    main()
