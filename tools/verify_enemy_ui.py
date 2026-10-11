"""Read back enemy Spirit bands and execute the reported map-name draw path."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json
from tools import battle_layout as B, ui_hook as H, ppc_exec as P
from tools import eboot_text as E, ui_catalog as U, library_build as L

SHOTS = (('enemy-map-name', 'cc14343e-bfc0-4db1-978a-0cae24b29df8'),
         ('enemy-spirit-band', '0829cc7c-b0ae-47a8-9ca4-50fdc19bfffb'))


def name_cases(elf, mapping, table_va):
    """Execute the installed centered renderer up to its actual glyph drawer.

    Check the full translated name and the empty overlay caption separately.
    These are the two distinct paths implicated by a stray native glyph drawn
    over an otherwise correct English name. No renderer calls are mocked.
    """
    mem = P.Memory()
    phs = H._headers(elf)[2]
    for seg in phs[:2]:
        mem.map(seg[3], elf[seg[2]:seg[2]+seg[5]], writable=seg == phs[1])
    mem.map(0x40000000, bytes(0x4000))
    mem.map(0x41000000, bytes(0x2000))
    mem.map(0x42000000, bytes(0x100))
    mem.write(H.TOC+H.STATE_DISP, struct.pack('>I', 0x41000000))
    widths = mem.read(table_va, 4480)
    cases = []
    for text in ('Daimon Police', 'Genion', ''):
        raw = E.encode(text, mapping)
        units = sum(widths[(a-0x81)*192+b-0x40] for a,b in zip(raw[::2], raw[1::2]))
        for mode in (0, 1):
            mem.write(0x42000000, raw+b'\0')
            mem.write(0x41000000, bytes(0x2000))
            for at in (0x54, 0x5c):
                mem.write(0x41000000+at, struct.pack('>f', 28))
            mem.write(0x410000ac, struct.pack('>H', mode))
            m = P.Machine(mem)
            m.r = [0x770000+i for i in range(32)]
            m.r[1] = 0x40003f00; m.r[2] = H.TOC; m.r[3] = 0x42000000
            m.r[7] = 1; m.r[8] = 0
            m.f[1] = 639.5; m.f[2] = 361.; m.f[3] = 1.; m.lr = 0x152000
            before = (m.r[1], m.r[2], m.r[27:32], m.lr)
            m.pc = 0x149bc
            m.run({0x14158}, limit=50000)
            if m.r[7] != 1 or mem.read(m.r[3], len(raw)+1) != raw+b'\0':
                raise ValueError('Map-name renderer supplies stray bytes: '+text)
            if abs(m.f[1]-(639.5-units*28/64)) > .0001:
                raise ValueError('Map-name centering differs: '+text)
            if (m.f[2], m.f[3]) != (361., 1.):
                raise ValueError('Map-name draw coordinates differ')
            if (m.r[1], m.r[2], m.r[27:32], m.lr) != before:
                raise ValueError('Map-name renderer lost caller state')
            cases.append(dict(text=text, mode=mode, raw_hex=raw.hex(),
                              drawer_pointer=m.r[3], left=m.f[1], steps=m.steps))
    return cases


def verify(version):
    from tools.verify_category_ui import verify as previous
    from tools.cpk import CPK
    prior = previous(version)
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text(encoding='utf8'))
    mapping = build['mapping']; elf = (folder/'EBOOT.BIN').read_bytes()
    names = name_cases(elf, mapping, build['executable']['table_va'])
    original = B.source()
    originals = {at:r for r in U.fssa_strings(original) for at in r['widget_offsets']}
    with CPK(folder/'AIDDATAPACK.CPK') as c:
        final = c.read(next(e for e in c.files if e['id'] == 0))
    grow = len(final)-len(original)
    widgets = {at:r for r in U.fssa_strings(final, decode=lambda b:L.decode(b, mapping))
               for at in r['widget_offsets']}
    bands = []
    for at, src in originals.items():
        if not src['text'].startswith('熱魂闘閃'):
            continue
        expected = ''.join(B.FLAGS[ch] for ch in src['text'])
        raw = E.encode(expected, mapping); actual = widgets[at+grow]['raw']
        if actual != raw or len(actual) != len(src['raw']):
            raise ValueError('Final Spirit band changed its slot order')
        if final[at+grow+4:at+grow+32] != original[at+4:at+32]:
            raise ValueError('Final Spirit band changed geometry or flags')
        labels = [B.TINY[ch] for ch in expected]
        if '／' in src['text'] and labels[13:17] != ['Fy', '/', 'Di', 'An']:
            raise ValueError('Enemy separator differs')
        bands.append(dict(widget_offset=at, labels=labels, bytes=len(raw),
                          enemy_separator='／' in src['text']))
    if len(bands) != 5 or sum(r['enemy_separator'] for r in bands) != 2:
        raise ValueError('Spirit band family coverage differs')
    shots = []
    for label, ident in SHOTS:
        src = Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest = ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src = dest
        shots.append(dict(issue=label, source=str(src), saved_path=str(dest),
                          sha256=sha256_file(src), runtime_confirmation=False))
    return dict(schema=1, version=version, map_name_draw_cases=names, spirit_bands=bands,
                enemy_separator='/', separator_advance=32, screenshots=shots,
                prior_verification=prior, iso_verification=prior['iso_verification'],
                runtime_verified=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version', default='0.5.18'); ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(); result = verify(args.version)
    print('Map-name draw cases:', len(result['map_name_draw_cases']))
    print('Spirit bands:', len(result['spirit_bands']), 'Enemy separator:', result['enemy_separator'])
    print('ISO:', result['iso_verification'])
    if args.apply:
        for shot in result['screenshots']:
            dest = Path(shot['saved_path']); dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and sha256_file(dest) != shot['sha256']:
                raise ValueError('Reported screenshot collision')
            if Path(shot['source']) != dest:shutil.copyfile(shot['source'], dest)
        write_json(ROOT/'work/ui'/('enemy_ui_verified_'+args.version+'.json'), result)
    else:print('DRY RUN: no evidence or screenshots written.')


if __name__ == '__main__':main()
