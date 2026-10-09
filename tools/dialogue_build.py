"""Write translated dialogue into Tengoku's stage scripts and rebuild STGZ3OF2.SDAT.

Ported in spirit from Jigoku's patch_lua.py / build_project.py, for Tengoku's
single combined stage archive. Each [[...]] dialogue block of a translated
record is replaced with encoded bytes; every other byte of the member is kept
(the file is rebuilt as bytes, because allocated font codes are unassigned
cp932). Asserted, not hoped for: the record identity and Japanese fingerprint,
the 《》 link count, the control codes, and that no block contains ]].

Control codes ($n, $c, $l, $F, $f) stay raw ASCII so the game still expands
them. Speech is wrapped to the dialogue box with real glyph advances;
continuation lines start with the fullwidth indent, as the Japanese does.
"""
import json
import subprocess
from pathlib import Path

from tools import dialogue as dlg
from tools import library_build as lb
from tools.common import ROOT, sha256
from tools.library_text import GLOSSARY, Resolver

STAGE_ARCHIVE = '/PS3_GAME/USRDIR/DATA/STAGE/STGZ3OF2.SDAT'
DECODED = ROOT / 'work/tengoku/prepared/STGZ3OF2.dec.cpk'
NPDATA_ENCRYPT = ['2', '0', '00', '1', '16', '0', '', '0']   # Jigoku: v3/v4 output is rejected in game
LINK_MARKS = '《》'


def translations():
    rows = {}
    for path in sorted(dlg.TRANSLATIONS.glob('*.json')):
        for rid, entry in json.loads(path.read_text(encoding='utf-8')).get('rows', {}).items():
            rows[rid] = entry
    return rows


def render(entry, record, resolver, width_of):
    """Final text of one record: expanded speaker line + wrapped speech (or caption)."""
    head, _, body = entry['en'].partition('\n')
    head = lb.expand(head, resolver) if '$$' in head else head
    caption = not head.strip('　 ') and '$' not in head
    if caption:
        return head + '\n' + lb.expand(body, resolver)
    out = [head]
    # One 「...」 block per line of the translation (normally one; route-branch
    # records have one per branch); each block wraps on its own.
    for part in body.strip().split('\n'):
        lines = wrap_speech(lb.expand(part.strip(), resolver), width_of)
        out += [('　' + l if i else l) for i, l in enumerate(lines)]
    return '\n'.join(out)


def wrap_speech(speech, width_of):
    units = lambda s: sum(0 if c in LINK_MARKS else width_of(c) for c in s)
    measure = lambda s: units(s.replace('$n', '')) + s.count('$n') * dlg.PROTAGONIST_UNITS
    lines, line = [], ''
    for word in speech.split(' '):
        lead = lb.FULLWIDTH if lines else 0
        trial = (line + ' ' + word) if line else word
        if line and measure(trial) > dlg.BOX_UNITS - lead:
            lines.append(line)
            line = word
        else:
            line = trial
    lines.append(line)
    return lines


def characters(texts):
    chars = set()
    for text in texts:
        for part in dlg.CODES.split(text):
            chars.update(c for c in part if c != '\n' and ord(c) < 0x80)
    return chars


def encode(text, mapping):
    """Mapped cells for Latin text, raw ASCII for control codes, cp932 otherwise; CRLF lines."""
    out, pos = bytearray(), 0
    for m in dlg.CODES.finditer(text):
        out += lb.encode(text[pos:m.start()], mapping)
        out += m.group(0).encode('ascii')
        pos = m.end()
    out += lb.encode(text[pos:], mapping)
    return bytes(out).replace(b'\n', b'\r\n')


def plan(width_of):
    """{record id: final text} for every translated record; asserts identity and structure."""
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver = Resolver(terms)
    rows = {r['id']: r for r in dlg.plan_rows()}
    rendered = {}
    for rid, entry in translations().items():
        record = rows.get(rid)
        if record is None:
            raise ValueError('translation for an unknown record: ' + rid)
        if entry['sha'] != record['sha']:
            raise ValueError('%s: the Japanese changed since translation' % rid)
        text = render(entry, record, resolver, width_of)
        if text.count('《') != record['jp'].count('《'):
            raise ValueError('%s: 《》 link count changed; links bind by position' % rid)
        if sorted(dlg.CODES.findall(text)) != sorted(dlg.CODES.findall(record['jp'])):
            raise ValueError('%s: control codes changed' % rid)
        rendered[rid] = text
    return rendered


def lua_safe(block):
    """True if `block` can sit inside a Lua [[...]] string unchanged."""
    return b']]' not in block and b'[[' not in block and not block.endswith(b']')


def rebuild_member(mid, rendered, mapping):
    """Member bytes with translated blocks replaced; untouched text kept byte for byte."""
    raw = (dlg.MEMBERS / ('%05d.bin' % mid)).read_bytes()
    text = raw.decode('cp932')
    ids = {}
    for ev in dlg.EVENT.finditer(text):
        for n, m in enumerate(dlg.BLOCK.finditer(ev.group(2))):
            ids[ev.start(2) + m.start()] = '%d:%s:%d' % (mid, ev.group(1), n)
    out, pos, changed = bytearray(), 0, 0
    for m in dlg.BLOCK.finditer(text):
        rid = ids.get(m.start())
        if rid not in rendered:
            continue
        block = encode(rendered[rid], mapping)
        if not lua_safe(block):
            raise ValueError('%s: encoded text would break the Lua [[...]] string' % rid)
        out += text[pos:m.start(1)].encode('cp932') + block
        pos = m.end(1)
        changed += 1
    out += text[pos:].encode('cp932')
    if not changed:
        return None
    if text.encode('cp932') != raw:
        raise ValueError('member %d does not round-trip through cp932' % mid)
    return bytes(out)


def build_archive(members, output, npdata):
    """Rebuild the decoded stage CPK with `members`, encrypt it, and prove the round trip."""
    from tools.cpkpatch import build as build_cpk
    staging = output / 'stage_members'
    staging.mkdir(parents=True)
    files = {}
    for mid, data in members.items():
        files[mid] = staging / ('%05d.bin' % mid)
        files[mid].write_bytes(data)
    cpk = output / 'STGZ3OF2.cpk'
    build_cpk(DECODED, cpk, files)
    sdat = output / 'STGZ3OF2.SDAT'
    subprocess.run([str(npdata), '-e', str(cpk), str(sdat)] + NPDATA_ENCRYPT, capture_output=True, text=True)
    if not sdat.exists():
        raise ValueError('make_npdata did not produce the SDAT')
    back = output / 'STGZ3OF2.roundtrip.cpk'
    subprocess.run([str(npdata), '-d', str(sdat), str(back), '0'], capture_output=True, text=True)
    if not back.exists() or back.read_bytes() != cpk.read_bytes():
        raise ValueError('SDAT does not decrypt back to the rebuilt CPK')
    back.unlink()
    return {'members_replaced': len(members), 'cpk_sha256': sha256(cpk.read_bytes()),
            'sdat_sha256': sha256(sdat.read_bytes()), 'sdat_version': 2, 'roundtrip_verified': True}
