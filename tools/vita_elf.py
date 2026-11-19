"""Read/decode PCSG00494 executables locally; no license values in reports."""
import argparse
import json
from pathlib import Path
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import vita_source as V
from tools.vita import self_decrypt as S

OUTPUT = V.WORK/'executables'
REFERENCE = V.DEPS/'self_reference/sce_utils.cpp'
REFERENCE_SHA = 'aa70c0dcfc912ead27abb2040cba0d9c2f3b543ecf7c5baa7c56c4459270a7d3'


def plan():
    audit = json.loads((V.WORK/'source_audit.json').read_text('utf8'))
    V.need(audit['title_id'] == V.TITLE, 'Wrong source audit')
    V.need(sha256_file(REFERENCE) == REFERENCE_SHA, 'Public SELF format reference changed')
    source = (V.PLAIN/'eboot.bin').read_bytes()
    V.need(sha256(source) == audit['files']['eboot.bin']['sha256'], 'Source executable changed')
    with V.LICENSE.open('rb') as stream:
        rif = stream.read(513)
    V.need(len(rif) == 512 and rif[0x17:0x20] == V.TITLE.encode(), 'License identity mismatch')
    info, segments = S.decode_segments(source, rif[0x50:0x60], REFERENCE.read_text('utf8'))
    candidate = S.make_fself(info, segments)
    report = dict(schema=1, title_id=V.TITLE, original_self_sha256=sha256(source),
        plain_self_sha256=sha256(candidate), reference_sha256=REFERENCE_SHA,
        program_headers=[list(row) for row in info['phdrs']],
        segment_sha256={str(i):sha256(raw) for i,raw in segments.items()},
        plain_self_bytes=len(candidate), license_values_logged=False,
        runtime_verified=False, translation_applied=False)
    return candidate, segments, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    candidate, segments, report = plan()
    print('PCSG00494 executable decoded;',len(segments),'segments; ELF program headers:')
    print(json.dumps(report['program_headers']))
    print('Plain SELF SHA-256:',report['plain_self_sha256'])
    if args.apply:
        V.need(not OUTPUT.exists(), 'Preserve existing decoded executable baseline')
        OUTPUT.mkdir(parents=True)
        (OUTPUT/'eboot-original-plain.self').write_bytes(candidate)
        for index, raw in segments.items():
            (OUTPUT/f'segment-{index}.bin').write_bytes(raw)
        write_json(OUTPUT/'baseline.json',report)
    else:
        print('DRY RUN: no executable or report written.')


if __name__ == '__main__':
    main()
