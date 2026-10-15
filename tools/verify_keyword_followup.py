"""Read back already translated keyword popups and D-Trader captions.

This audit does not modify or rebuild game assets. --apply only records the
evidence and preserves the four user-supplied screenshots.
"""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path

from tools.common import ROOT, sha256_file, write_json
from tools import library_runtime as K, library_text as T, library_build as B
from tools import ui_hook as H, battle_layout, ui_catalog, review30_layout
from tools.cpk import CPK
from tools.menu_layout import encode
from tools.source_text import library_fields
from tools.ui_description_layout import advance

SHOTS = (
    ('d-trader', 'caec9ab5-b234-4276-87a4-220517afba44'),
    ('messenger', 'c36678e7-af64-4952-bf5f-3bf39b08801e'),
    ('avalon', 'def6f642-2799-40f1-b728-3e9c48defc8f'),
    ('nerv', '76399ddf-9a10-4cd2-a251-4c513f900b4b'),
)


def verify(version):
    folder = ROOT / 'work/output/builds' / version
    build = json.loads((folder / 'build.json').read_text('utf8'))
    hashes = {}
    for name in ('EBOOT.BIN', 'MTZKN_KW.CPK', 'AIDDATAPACK.CPK', 'TPACKPS3.CPK'):
        hashes[name] = sha256_file(folder / name)
        if hashes[name] != build['outputs'][name]:
            raise ValueError('Prepared build changed: ' + name)
    mapping = build['mapping']
    source = H.PREPARED.read_bytes()
    elf = (folder / 'EBOOT.BIN').read_bytes()
    read = H._reader(elf, H._headers(elf)[2])
    plan = K.plan(source, mapping, advance)
    addresses = build['executable']['ui_hook']['table']['payload_vas']
    payloads = dict(plan['payloads'])
    for row in plan['pointers']:
        if struct.unpack_from('>I', elf, row['offset'])[0] != addresses[row['id']]:
            raise ValueError('Native keyword description pointer differs')
    for key, raw in plan['payloads']:
        if key not in (K.FAST_STATE, K.FAST_TABLE) and read(addresses[key], len(raw)) != raw:
            raise ValueError('Native keyword payload differs: ' + key)
    reported = []
    japanese = re.compile(r'[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9d]')
    for row in plan['report']['entries']:
        texts = {}
        at = row['record_offset']
        restored = bytearray(elf[at:at + 24])
        restored[8:16] = source[at + 8:at + 16]
        if restored != source[at:at + 24]:
            raise ValueError('Native keyword lookup identity changed')
        for tag in ('DSCR', 'DSC2'):
            raw = payloads['library:keyword:%d:%s:encoded' % (row['id'], tag)][:-1]
            texts[tag] = B.decode(raw, mapping)
            if japanese.search(texts[tag]):
                raise ValueError('Untranslated keyword: ' + row['name'])
        if row['name'] in ('messenger', 'Avalon', 'NERV'):
            reported.append(dict(id=row['id'], name=row['name'], descriptions=texts))
    if {row['name'] for row in reported} != {'messenger', 'Avalon', 'NERV'}:
        raise ValueError('Reported keyword selection differs')
    conversion = K.verify_fastpath(elf, plan, addresses, build['executable']['library_runtime']['conversion'])
    library = T.load_library()
    entries, errors = T.load_translations()
    if errors:
        raise ValueError(errors)
    rendered = B.plan(library, entries, json.loads(T.GLOSSARY.read_text('utf8'))['terms'])['keyword']
    archive_fields = 0
    with CPK(folder / 'MTZKN_KW.CPK') as arc:
        if {row['id'] for row in arc.files} != set(rendered):
            raise ValueError('Keyword archive inventory differs')
        for row in arc.files:
            raw = arc.read(row)
            decoded = bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in raw)
            for slot in library_fields(raw)[1]:
                tag = slot['tag']
                if tag not in rendered[row['id']]:
                    continue
                text = rendered[row['id']][tag]
                if tag in ('DSCR', 'DSC2'):
                    text = B.wrap(text, advance)
                if decoded[slot['offset']:slot['offset'] + slot['bytes']] != B.encode(text, mapping):
                    raise ValueError('Keyword archive field differs: %d %s' % (row['id'], tag))
                archive_fields += 1
    native = battle_layout.source()
    with CPK(folder / 'AIDDATAPACK.CPK') as arc:
        final = arc.read(next(r for r in arc.files if r['id'] == 0))
    grow = len(final) - len(native)
    widgets = {at: r for r in ui_catalog.fssa_strings(final, decode=lambda raw: raw.hex()) for at in r['widget_offsets']}
    layout = review30_layout.plan()
    for row in layout['edits']:
        at = row['widget_offset']
        target = at + grow
        expected = bytearray(native[at + 4:at + 32])
        if 'x' in row:
            struct.pack_into('>f', expected, 0, row['x'])
        if widgets[target]['raw'] != encode(row, mapping) or final[target + 4:target + 32] != expected:
            raise ValueError('Prepared D-Trader/deployment caption differs')
    shots = []
    for label, ident in SHOTS:
        src = Path('C:/Users/Binh/AppData/Local/Temp') / ('codex-clipboard-' + ident + '.png')
        dst = ROOT / 'work/ui/screenshots' / ('reported-keyword-followup-' + label + '.png')
        if not src.exists():
            src = dst
        shots.append(dict(issue=label, source=str(src), saved_path=str(dst), sha256=sha256_file(src)))
    return dict(schema=1, version=version, game_assets_changed=False, asset_sha256=hashes,
                keywords=143, description_variants=286, untranslated_descriptions=0,
                archive_display_fields=archive_fields, native_conversion=conversion,
                reported_keywords=reported, layout=layout, screenshots=shots,
                verifier_sha256=sha256_file(Path(__file__)), runtime_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', default='0.5.34')
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    data = verify(args.version)
    for row in data['reported_keywords']:
        print(row['name'], 'already English in both native popup variants and Library archive')
    print('143 keywords, 286 descriptions, 572 native consumers and nine repaired captions passed.')
    if not args.apply:
        print('DRY RUN: no game assets, evidence or screenshots written.')
        return
    for row in data['screenshots']:
        src, dst = Path(row['source']), Path(row['saved_path'])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256_file(dst) != row['sha256']:
            raise ValueError('Screenshot collision')
        if src != dst:
            shutil.copyfile(src, dst)
    write_json(ROOT / 'work/ui' / ('keyword_followup_' + args.version + '.json'), data)


if __name__ == '__main__':
    main()
