"""Audit every dialogue entry against the backlog's separate byte budgets."""
import hashlib
import json
from functools import lru_cache
from tools.common import ROOT, sha256
from tools import backlog_storage as B, backlog_verify as V
from tools import dialogue_build as D, dialogue_layout as Q, mission_display as M

REPORTED = '557:t_011:15'


@lru_cache(None)
def corpus():
    mapping = json.loads((ROOT / 'work/output/builds/0.5.36/build.json').read_text('utf8'))['mapping']
    rendered = D.plan(M.advance)
    digest = hashlib.sha256()
    entries, rows = [], []
    reported = None
    maximum_entry = maximum_row = 0
    for rid, text in sorted(rendered.items()):
        raw = D.encode(text, Q.mapping_for(rid, mapping)).replace(b'\r\n', b'\n')
        digest.update(rid.encode('ascii') + b'\0' + raw + b'\0')
        parts = raw.split(b'\n')
        maximum_entry = max(maximum_entry, len(raw))
        maximum_row = max(maximum_row, max(map(len, parts)))
        if len(raw) > B.TEXT - 1 or max(map(len, parts)) > B.LINE_BYTES:
            raise ValueError('Backlog capacity does not cover ' + rid)
        if len(raw) > B.OLD_TEXT - 1:
            entries.append((rid, raw))
        rows.extend((rid, n, part) for n, part in enumerate(parts) if len(part) > 128)
        if rid == REPORTED:
            reported = dict(id=rid, english=text, raw=raw,
                            source_sha=D.translations()[rid]['sha'])
    if reported is None:
        raise ValueError('Reported Leonard entry is missing')
    return dict(mapping=mapping, entries=entries, rows=rows, reported=reported,
                report=dict(dialogue_entries=len(rendered), corpus_sha256=digest.hexdigest(),
                            entries_over_old_limit=len(entries), rows_over_old_limit=len(rows),
                            maximum_entry_bytes=maximum_entry, maximum_row_bytes=maximum_row,
                            reported=dict(id=REPORTED, source_sha=reported['source_sha'],
                                          english=reported['english'], bytes=len(reported['raw']))))


def verify(elf):
    data = corpus()
    # Exercise each over-budget entry in the real 20-entry ring, with the
    # reported line last so its final bytes can be compared directly.
    texts = [raw for _, raw in data['entries']] + [data['reported']['raw']]
    rings = [V.exercise(elf, texts, constructor=ctor) for ctor in (0x23cd34, 0x23ce70)]
    for ring in rings:
        if bytes.fromhex(ring.pop('final_text')) != data['reported']['raw']:
            raise ValueError('Leonard backlog text differs from dialogue text')
    lines = [raw for _, _, raw in data['rows']]
    lines += [b'A' * n for n in (1, 127, 128, 129, 254, 255)]
    return dict(corpus=data['report'], native_ring_cases=rings,
                native_row_cases=V.row_copies(elf, lines), runtime_verified=False)
