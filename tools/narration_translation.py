"""Preview reviewed narration drafts and promote complete, measured English."""
import argparse
import json
from tools.common import ROOT, write_json
from tools.opening_narration import profile
from tools.ui_description_layout import advance, condensed_advance

BRIEFS = ROOT / 'work/tengoku/narration_briefs'
DEST = ROOT / 'work/translation/en/ui/expanded/narration.json'


def plan():
    from tools.ui_catalog import translations
    corpus = json.loads((BRIEFS/'all.json').read_text(encoding='utf-8'))['rows']
    existing = translations()
    if DEST.exists():
        for rid in json.loads(DEST.read_text(encoding='utf-8'))['strings']:
            existing.pop(rid, None)
    drafts = {}
    reviews = []
    for index in range(1,4):
        data = json.loads((BRIEFS/('review_%d.json'%index)).read_text(encoding='utf-8'))
        reviews.append(data.get('review_report', data.get('report')))
        for rid, row in data['strings'].items():
            if rid in drafts and drafts[rid]['en'] != row['en']:
                raise ValueError('Narration reviewers differ on shared caption: '+rid)
            drafts[rid] = row
    expected = {r['translation_id'] for r in corpus}
    if set(drafts) != expected:
        raise ValueError('Review does not cover the full narration corpus')
    added = {}
    widths = []
    for rid, row in drafts.items():
        if not row.get('reviewed') or not row.get('en'):
            raise ValueError('Unreviewed narration: '+rid)
        text, condensed = profile(row['en'])
        width = sum(map(condensed_advance if condensed else advance, text))
        widths.append(dict(id=rid, units=width, condensed=condensed))
        if rid in existing:
            if existing[rid]['en'] != text:
                raise ValueError('Existing narration meaning change requires separate review: '+rid)
        else:
            added[rid] = dict(en=text, reviewed=True, notes=row.get('notes',
                'Full narration review with adjacent timed records.'))
    return dict(schema=1, strings=added), dict(schema=1, version='0.5.16',
        captions=len(corpus), unique_captions=len(expected), added_unique_captions=len(added),
        reviewed_existing_unique=len(expected)-len(added), review_reports=reviews,
        line_limit_units=900, widths=widths, runtime_verified=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    translation, report = plan()
    print('Full narration:', report['captions'], 'captions;', report['added_unique_captions'], 'new unique translations')
    for rid, row in list(translation['strings'].items())[:10]:
        print(rid, row['en'])
    print('Maximum line units:', max(r['units'] for r in report['widths']))
    if args.apply:
        write_json(DEST, translation)
        write_json(ROOT/'work/ui/narration_review_0.5.16.json', report)
    else:
        print('DRY RUN: no translations or review evidence written.')


if __name__ == '__main__': main()
