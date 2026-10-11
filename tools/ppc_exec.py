"""Small big-endian PPC64 decoder and interpreter for bounded oracle tests.

Pure Python, no Capstone: it runs under the bundled Python. Only the
instruction forms used by the code it is pointed at are implemented (the
UI hook stub, the game's UTF-8 -> cp932 converter at 0x13b38 and the libc
strlen at 0x68a2ac). Anything else raises `Unsupported`, so an unexpected
instruction can never be silently skipped. Memory is a set of explicit
regions; touching anything outside them raises `Fault`.

This is instruction-level testing of user-mode integer code, not a PS3
emulator: no MSR, exceptions, caches, timing or system calls.
"""
import struct

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1


class Unsupported(Exception):
    pass


class Fault(Exception):
    pass


def sext(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v


def mask64(mb, me):
    """PowerPC MASK(mb, me) with bit 0 = MSB, wrapping when mb > me."""
    def ones_from(b):        # bits b..63 set
        return (1 << (64 - b)) - 1 if b < 64 else 0
    if mb <= me:
        return ones_from(mb) & ~ones_from(me + 1) & M64
    return (ones_from(mb) | (~ones_from(me + 1) & M64)) & M64


def rotl64(v, n):
    n &= 63
    v &= M64
    return ((v << n) | (v >> (64 - n))) & M64 if n else v


def rotl32(v, n):
    v &= M32
    d = (v << 32) | v
    return rotl64(d, n)


SPR = {8: 'lr', 9: 'ctr', 1: 'xer'}


def decode(w, pc=0):
    """word -> (mnemonic, args tuple). Raises Unsupported for unknown forms."""
    op = w >> 26
    rt, ra, rb = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
    simm, uimm = sext(w, 16), w & 0xffff
    if op == 14: return ('addi', rt, ra, simm)
    if op == 15: return ('addis', rt, ra, simm)
    if op == 7: return ('mulli', rt, ra, simm)
    if op == 24: return ('ori', ra, rt, uimm)
    if op == 25: return ('oris', ra, rt, uimm)
    if op == 26: return ('xori', ra, rt, uimm)
    if op == 28: return ('andi.', ra, rt, uimm)
    if op == 29: return ('andis.', ra, rt, uimm)
    if op in (10, 11):
        if w & (1 << 22):
            raise Unsupported('cmp reserved bit')
        bf, l = (w >> 23) & 7, (w >> 21) & 1
        return ('cmpli' if op == 10 else 'cmpi', bf, l, ra, uimm if op == 10 else simm)
    if op == 18:
        li = sext(w & 0x3fffffc, 26)
        target = li if w & 2 else (pc + li) & M64
        return ('bl' if w & 1 else 'b', target)
    if op == 16:
        bo, bi = rt, ra
        bd = sext(w & 0xfffc, 16)
        target = bd if w & 2 else (pc + bd) & M64
        return ('bc', bo, bi, target, w & 1)
    if op == 19:
        xo = (w >> 1) & 0x3ff
        if xo == 16: return ('bclr', rt, ra, w & 1)
        if xo == 528: return ('bcctr', rt, ra, w & 1)
        raise Unsupported('op19 xo %d' % xo)
    if op == 21:
        return ('rlwinm', ra, rt, rb, (w >> 6) & 31, (w >> 1) & 31, w & 1)
    if op == 20:
        return ('rlwimi', ra, rt, rb, (w >> 6) & 31, (w >> 1) & 31, w & 1)
    if op == 30:
        sh = rb | ((w >> 1) & 1) << 5
        raw = (w >> 5) & 0x3f
        m = ((raw & 1) << 5) | (raw >> 1)
        xo = (w >> 2) & 7
        names = {0: 'rldicl', 1: 'rldicr', 2: 'rldic', 3: 'rldimi'}
        if xo not in names:
            raise Unsupported('op30 xo %d' % xo)
        return (names[xo], ra, rt, sh, m, w & 1)
    if op == 31:
        xo10 = (w >> 1) & 0x3ff
        xo9 = (w >> 1) & 0x1ff
        rc = w & 1
        if xo10 == 0 or xo10 == 32:
            bf, l = (w >> 23) & 7, (w >> 21) & 1
            return ('cmp' if xo10 == 0 else 'cmpl', bf, l, ra, rb)
        xnames = {28: 'and', 444: 'or', 316: 'xor', 124: 'nor', 60: 'andc', 24: 'slw', 536: 'srw',
                  27: 'sld', 539: 'srd', 792: 'sraw'}
        # XO forms (OE=0 only). None of these 9-bit codes equals a 10-bit X-form code used here.
        xo_names = {266: 'add', 40: 'subf', 104: 'neg', 202: 'addze', 235: 'mullw', 233: 'mulld',
                    8: 'subfc', 10: 'addc'}
        if xo10 in xo_names:
            return (xo_names[xo10], rt, ra, rb, rc)
        if xo9 in xo_names:
            raise Unsupported('XO form with OE=1')
        if xo10 in xnames:
            return (xnames[xo10], ra, rt, rb, rc)
        if xo10 in (954, 922, 986, 26, 58):
            return ({954: 'extsb', 922: 'extsh', 986: 'extsw', 26: 'cntlzw', 58: 'cntlzd'}[xo10], ra, rt, rc)
        if xo10 == 824: return ('srawi', ra, rt, rb, rc)
        if xo10 == 75: return ('mulhw', rt, ra, rb, rc)
        loads = {87: ('lbzx', 1), 23: ('lwzx', 4), 279: ('lhzx', 2), 21: ('ldx', 8)}
        stores = {215: ('stbx', 1), 151: ('stwx', 4), 407: ('sthx', 2), 149: ('stdx', 8)}
        if xo10 in loads: return (loads[xo10][0], rt, ra, rb, loads[xo10][1])
        if xo10 in stores: return (stores[xo10][0], rt, ra, rb, stores[xo10][1])
        if xo10 == 19:
            if w & (1 << 20):
                raise Unsupported('mfocrf')
            return ('mfcr', rt)
        if xo10 == 144:
            return ('mtcrf', rt, (w >> 12) & 0xff)
        if xo10 in (339, 467):
            spr = ra | rb << 5
            if spr not in SPR:
                raise Unsupported('spr %d' % spr)
            return ('mfspr' if xo10 == 339 else 'mtspr', rt, SPR[spr])
        if xo10 == 278: return ('dcbt',)
        if xo10 == 983: return ('stfiwx', rt, ra, rb)
        raise Unsupported('op31 xo %d' % xo10)
    if op == 59:
        xo = (w >> 1) & 31
        if xo in (20,21): return ('fsubs' if xo==20 else 'fadds',rt,ra,rb)
        if xo==25: return ('fmuls',rt,ra,(w>>6)&31)
        if xo==29 and not w&1:return ('fmadds',rt,ra,(w>>6)&31,rb)
    if op == 63:
        xo = (w >> 1) & 1023
        if xo==72 and not w&1:return ('fmr',rt,rb)
        if xo in (846,12,15): return ({846:'fcfid',12:'frsp',15:'fctiwz'}[xo],rt,rb)
    dforms = {32: ('lwz', 4, 0), 33: ('lwzu', 4, 1), 34: ('lbz', 1, 0), 35: ('lbzu', 1, 1),
              40: ('lhz', 2, 0), 41: ('lhzu', 2, 1), 42: ('lha', 2, 0),
              36: ('stw', 4, 0), 37: ('stwu', 4, 1), 38: ('stb', 1, 0), 39: ('stbu', 1, 1),
              44: ('sth', 2, 0), 45: ('sthu', 2, 1),
              48: ('lfs', 4, 0), 50: ('lfd', 8, 0), 52: ('stfs', 4, 0), 54: ('stfd', 8, 0)}
    if op in dforms:
        name, size, upd = dforms[op]
        return (name, rt, ra, simm, size, upd)
    if op in (58, 62):
        sub = w & 3
        ds = sext(w & 0xfffc, 16)
        names = {(58, 0): 'ld', (58, 1): 'ldu', (58, 2): 'lwa', (62, 0): 'std', (62, 1): 'stdu'}
        if (op, sub) not in names:
            raise Unsupported('DS form %d/%d' % (op, sub))
        n = names[(op, sub)]
        return (n, rt, ra, ds, 4 if n == 'lwa' else 8, n in ('ldu', 'stdu'))
    raise Unsupported('primary opcode %d (word %08x)' % (op, w))


class Memory:
    def __init__(self):
        self.regions = []      # [base, bytearray, writable]

    def map(self, base, data, writable=True):
        self.regions.append([base, bytearray(data), writable])
        return self.regions[-1][1]

    def _find(self, addr, n):
        for base, buf, wr in self.regions:
            if base <= addr and addr + n <= base + len(buf):
                return buf, addr - base, wr
        raise Fault('unmapped access %#x+%d' % (addr, n))

    def read(self, addr, n):
        buf, off, _ = self._find(addr, n)
        return bytes(buf[off:off + n])

    def write(self, addr, data):
        buf, off, wr = self._find(addr, len(data))
        if not wr:
            raise Fault('write to read-only %#x' % addr)
        buf[off:off + len(data)] = data


class Machine:
    """r[0..31] 64-bit, cr 32-bit (cr0 = top nibble), lr, ctr, xer CA only, f[] as floats."""

    def __init__(self, memory, fetch=None):
        self.mem = memory
        self.r = [0] * 32
        self.f = [0.0] * 32
        self.cr = 0
        self.lr = 0
        self.ctr = 0
        self.ca = 0
        self.pc = 0
        self.fetch = fetch or (lambda pc: struct.unpack('>I', memory.read(pc, 4))[0])
        self.hooks = {}       # pc -> callable(machine); must set pc
        self.cache = {}
        self.steps = 0

    # -- helpers
    def ea(self, ra, d):
        return ((self.r[ra] if ra else 0) + d) & M64

    def setcr(self, field, value_lt, value_gt):
        bits = 8 if value_lt else 4 if value_gt else 2
        sh = 28 - 4 * field
        self.cr = (self.cr & ~(0xf << sh)) | (bits << sh)

    def rc(self, v):
        s = sext(v, 64)
        self.setcr(0, s < 0, s > 0)

    def crbit(self, bi):
        return (self.cr >> (31 - bi)) & 1

    def run(self, stop, limit=1000000):
        while self.pc not in stop:
            if self.pc in self.hooks:
                self.hooks[self.pc](self)
                continue
            self.step()
            if self.steps > limit:
                raise Fault('step limit')
        return self

    def step(self):
        pc = self.pc
        ins = self.cache.get(pc)
        if ins is None:
            ins = self.cache[pc] = decode(self.fetch(pc), pc)
        self.steps += 1
        self.pc = (pc + 4) & M64
        n = ins[0]
        r = self.r
        if n == 'addi':
            _, t, a, s = ins; r[t] = ((r[a] if a else 0) + s) & M64
        elif n == 'addis':
            _, t, a, s = ins; r[t] = ((r[a] if a else 0) + (s << 16)) & M64
        elif n == 'mulli':
            _, t, a, s = ins; r[t] = (sext(r[a], 64) * s) & M64
        elif n in ('ori', 'oris', 'xori', 'andi.', 'andis.'):
            _, a, s, u = ins
            if n == 'ori': r[a] = r[s] | u
            elif n == 'oris': r[a] = r[s] | (u << 16)
            elif n == 'xori': r[a] = r[s] ^ u
            elif n == 'andi.': r[a] = r[s] & u; self.rc(r[a])
            else: r[a] = r[s] & (u << 16); self.rc(r[a])
        elif n in ('cmpi', 'cmp', 'cmpli', 'cmpl'):
            _, bf, l, a, b = ins
            x = r[a]
            y = b if n in ('cmpi', 'cmpli') else r[b]
            if n in ('cmpi', 'cmp'):
                x = sext(x, 64 if l else 32)
                if n == 'cmp': y = sext(y, 64 if l else 32)
            else:
                x &= M64 if l else M32
                y &= M64 if l else M32
            self.setcr(bf, x < y, x > y)
        elif n in ('b', 'bl'):
            if n == 'bl': self.lr = self.pc
            self.pc = ins[1]
        elif n == 'bc':
            _, bo, bi, target, lk = ins
            if lk: self.lr = self.pc
            if self.branch_ok(bo, bi): self.pc = target
        elif n in ('bclr', 'bcctr'):
            _, bo, bi, lk = ins
            target = (self.lr if n == 'bclr' else self.ctr) & ~3 & M64
            if lk: self.lr = self.pc
            if self.branch_ok(bo, bi, n == 'bcctr'): self.pc = target
        elif n in ('rlwinm', 'rlwimi'):
            _, a, s, sh, mb, me, rc = ins
            m = mask64(mb + 32, me + 32)
            rot = rotl32(r[s], sh)
            r[a] = (rot & m) if n == 'rlwinm' else ((rot & m) | (r[a] & ~m & M64))
            if rc: self.rc(r[a])
        elif n in ('rldicl', 'rldicr', 'rldic', 'rldimi'):
            _, a, s, sh, m, rc = ins
            rot = rotl64(r[s], sh)
            if n == 'rldicl': r[a] = rot & mask64(m, 63)
            elif n == 'rldicr': r[a] = rot & mask64(0, m)
            elif n == 'rldic': r[a] = rot & mask64(m, 63 - sh)
            else:
                mk = mask64(m, 63 - sh); r[a] = (rot & mk) | (r[a] & ~mk & M64)
            if rc: self.rc(r[a])
        elif n in ('add', 'subf', 'neg', 'addze', 'mullw', 'mulld', 'mulhw', 'subfc', 'addc'):
            _, t, a, b, rc = ins
            if n == 'add': r[t] = (r[a] + r[b]) & M64
            elif n == 'subf': r[t] = (r[b] - r[a]) & M64
            elif n == 'neg': r[t] = (-r[a]) & M64
            elif n == 'addze':
                s = r[a] + self.ca; self.ca = s >> 64; r[t] = s & M64
            elif n == 'mullw': r[t] = (sext(r[a], 32) * sext(r[b], 32)) & M64
            elif n == 'mulld': r[t] = (sext(r[a], 64) * sext(r[b], 64)) & M64
            elif n == 'mulhw': r[t] = ((sext(r[a],32)*sext(r[b],32))>>32)&M64
            elif n == 'subfc':
                s = (~r[a] & M64) + r[b] + 1; self.ca = s >> 64; r[t] = s & M64
            else:
                s = r[a] + r[b]; self.ca = s >> 64; r[t] = s & M64
            if rc: self.rc(r[t])
        elif n in ('and', 'or', 'xor', 'nor', 'andc', 'slw', 'srw', 'sld', 'srd', 'sraw'):
            _, a, s, b, rc = ins
            x, y = r[s], r[b]
            if n == 'and': v = x & y
            elif n == 'or': v = x | y
            elif n == 'xor': v = x ^ y
            elif n == 'nor': v = ~(x | y) & M64
            elif n == 'andc': v = x & ~y & M64
            elif n == 'slw': v = 0 if y & 0x20 else ((x & M32) << (y & 31)) & M32
            elif n == 'srw': v = 0 if y & 0x20 else (x & M32) >> (y & 31)
            elif n == 'sld': v = 0 if y & 0x40 else (x << (y & 63)) & M64
            elif n == 'srd': v = 0 if y & 0x40 else x >> (y & 63)
            else:
                k = y & 0x3f; sx = sext(x, 32)
                v = (sx >> (k if k < 32 else 31)) & M64
                self.ca = 1 if sx < 0 and (sx & ((1 << min(k, 32)) - 1)) else 0
            r[a] = v
            if rc: self.rc(v)
        elif n in ('extsb', 'extsh', 'extsw', 'cntlzw', 'cntlzd'):
            _, a, s, rc = ins
            x = r[s]
            if n == 'extsb': v = sext(x, 8) & M64
            elif n == 'extsh': v = sext(x, 16) & M64
            elif n == 'extsw': v = sext(x, 32) & M64
            elif n == 'cntlzw': v = 32 - (x & M32).bit_length()
            else: v = 64 - x.bit_length()
            r[a] = v
            if rc: self.rc(v)
        elif n == 'srawi':
            _, a, s, sh, rc = ins
            sx = sext(r[s], 32)
            r[a] = (sx >> sh) & M64
            self.ca = 1 if sx < 0 and (sx & ((1 << sh) - 1)) else 0
            if rc: self.rc(r[a])
        elif n in ('lbzx', 'lwzx', 'lhzx', 'ldx'):
            _, t, a, b, size = ins
            r[t] = int.from_bytes(self.mem.read(((r[a] if a else 0) + r[b]) & M64, size), 'big')
        elif n in ('stbx', 'stwx', 'sthx', 'stdx'):
            _, s, a, b, size = ins
            self.mem.write(((r[a] if a else 0) + r[b]) & M64, (r[s] & ((1 << (8 * size)) - 1)).to_bytes(size, 'big'))
        elif n == 'mfcr':
            r[ins[1]] = self.cr
        elif n == 'mtcrf':
            _, s, fxm = ins
            m = 0
            for i in range(8):
                if fxm & (0x80 >> i): m |= 0xf << (28 - 4 * i)
            self.cr = (self.cr & ~m) | (r[s] & m)
        elif n == 'mfspr':
            _, t, spr = ins
            r[t] = {'lr': self.lr, 'ctr': self.ctr, 'xer': self.ca << 29}[spr]
        elif n == 'mtspr':
            _, s, spr = ins
            if spr == 'lr': self.lr = r[s]
            elif spr == 'ctr': self.ctr = r[s]
            else: self.ca = (r[s] >> 29) & 1
        elif n=='fmr':
            _,t,b=ins;self.f[t]=self.f[b]
        elif n in ('fcfid','frsp','fctiwz'):
            _,t,b=ins
            if n=='fcfid':
                bits=struct.unpack('>Q',struct.pack('>d',self.f[b]))[0]
                self.f[t]=float(sext(bits,64))
            elif n=='frsp':
                self.f[t]=struct.unpack('>f',struct.pack('>f',self.f[b]))[0]
            else:
                value=int(self.f[b])
                if not -(1<<31)<=value<(1<<31): raise Unsupported('fctiwz integer range')
                self.f[t]=struct.unpack('>d',struct.pack('>Q',value & M32))[0]
        elif n=='fmadds':
            # Native caption geometry uses exact binary single-precision
            # coordinates; round once after multiply/add, not after multiply.
            _,t,a,c,b=ins
            self.f[t]=struct.unpack('>f',struct.pack('>f',self.f[a]*self.f[c]+self.f[b]))[0]
        elif n in ('fmuls','fadds','fsubs'):
            _,t,a,b=ins
            v=(self.f[a]*self.f[b] if n=='fmuls' else
               self.f[a]+self.f[b] if n=='fadds' else self.f[a]-self.f[b])
            self.f[t]=struct.unpack('>f',struct.pack('>f',v))[0]
        elif n=='stfiwx':
            _,s,a,b=ins
            bits=struct.unpack('>Q',struct.pack('>d',self.f[s]))[0]
            self.mem.write(self.ea(a,r[b]),struct.pack('>I',bits & M32))
        elif n == 'dcbt':
            pass
        elif n in ('lwz', 'lwzu', 'lbz', 'lbzu', 'lhz', 'lhzu', 'lha', 'ld', 'ldu', 'lwa'):
            _, t, a, d, size, upd = ins
            addr = self.ea(a, d)
            v = int.from_bytes(self.mem.read(addr, size), 'big')
            if n in ('lha', 'lwa'): v = sext(v, 8 * size) & M64
            r[t] = v
            if upd: r[a] = addr
        elif n in ('stw', 'stwu', 'stb', 'stbu', 'sth', 'sthu', 'std', 'stdu'):
            _, s, a, d, size, upd = ins
            addr = self.ea(a, d)
            self.mem.write(addr, (r[s] & ((1 << (8 * size)) - 1)).to_bytes(size, 'big'))
            if upd: r[a] = addr
        elif n in ('lfs', 'lfd'):
            _, t, a, d, size, _u = ins
            raw = self.mem.read(self.ea(a, d), size)
            self.f[t] = struct.unpack('>f' if size == 4 else '>d', raw)[0]
        elif n in ('stfs', 'stfd'):
            _, s, a, d, size, _u = ins
            self.mem.write(self.ea(a, d), struct.pack('>f' if size == 4 else '>d', self.f[s]))
        else:
            raise Unsupported(n)

    def branch_ok(self, bo, bi, is_ctr=False):
        ctr_ok = True
        if not bo & 4:
            if is_ctr:
                raise Unsupported('bcctr with CTR decrement')
            self.ctr = (self.ctr - 1) & M64
            ctr_ok = (self.ctr != 0) != bool(bo & 2)
        cond_ok = bool(bo & 0x10) or self.crbit(bi) == ((bo >> 3) & 1)
        return ctr_ok and cond_ok
