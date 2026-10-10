"""Promote verified fresh dialogue drafts; preview unless --apply is supplied."""
import argparse
import json
import shutil
import hashlib
from collections import defaultdict
from tools import dialogue as d, dialogue_retranslate as r
from tools.common import ROOT, sha256_file, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    p.add_argument('--repair', action='store_true', help='Complete an audited earlier promotion using its preserved backup')
    args = p.parse_args()
    expected = {row['id']: row['sha'] for row in d.plan_rows()}
    found, files = {}, []
    backup = ROOT / 'work/output/retranslation-promotion-0.5.2'
    if args.repair:
        assert (backup / 'prior_active').is_dir()
    else:
        assert not backup.exists(), 'Promotion backup already exists'
    for batch in range(1, 13):
        r.configure(batch)
        manifest = json.loads((r.RUN / 'manifest.json').read_text(encoding='utf-8'))
        assert manifest['state'] in ('draft_complete_validated', 'draft_complete_fit_review_required')
        assert r.check(), 'Current strict check failed for batch %d' % batch
        for name, info in manifest['slices'].items():
            source = r.RUN / 'drafts' / (name + '.json')
            assert sha256_file(source) == info['draft_sha256'], str(source)
            old = d.TRANSLATIONS / source.name
            prior = backup / 'prior_active' / old.name if args.repair else old
            assert sha256_file(prior) == info['prior_sha256'], 'Prior file changed: ' + str(prior)
            rows = json.loads(source.read_text(encoding='utf-8'))['rows']
            for rid, row in rows.items():
                assert rid not in found and expected.get(rid) == row['sha'], rid
                found[rid] = row['sha']
            files.append((source, old))
    assert found == expected
    grouped = defaultdict(list)
    for source, old in files:
        grouped[old].append(source)
    retired = []
    for stale in d.TRANSLATIONS.glob('*.json'):
        if stale in grouped:
            continue
        stale_rows = json.loads(stale.read_text(encoding='utf-8')).get('rows', {})
        assert set(stale_rows) <= set(expected), 'Unexpected legacy source IDs: ' + str(stale)
        prior = backup / 'prior_active' / stale.name if args.repair else stale
        assert sha256_file(stale) == sha256_file(prior), 'Unexpected legacy edit: ' + str(stale)
        retired.append({'file': stale.name, 'rows': len(stale_rows), 'sha256': sha256_file(stale)})
        print('Retire old slice (preserved in backup):', stale.name, 'rows:', len(stale_rows))
    planned = []
    for old, sources in grouped.items():
        if len(sources) == 1:
            payload = sources[0].read_bytes()
        else:
            datasets = [json.loads(x.read_text(encoding='utf-8')) for x in sources]
            merged = dict(datasets[0], rows={}, names={})
            reports = []
            for source, data in zip(sources, datasets):
                assert not set(merged['rows']) & set(data['rows'])
                merged['rows'].update(data['rows'])
                for key, value in data.get('names', {}).items():
                    merged['names'].setdefault(key, value)
                reports.append({'source': str(source.relative_to(ROOT)), 'report': data['report']})
            merged['report'] = {'rows_in_slice': len(merged['rows']), 'rows_examined': len(merged['rows']),
                                'left_untranslated': [], 'merged_fresh_reports': reports}
            payload = (json.dumps(merged, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            print('Merge route-choice file:', old.name, 'rows:', len(merged['rows']))
        if args.repair:
            allowed = {sha256_file(x) for x in sources} | {hashlib.sha256(payload).hexdigest()}
            assert sha256_file(old) in allowed, 'Unexpected active edit: ' + str(old)
        planned.append((sources, old, payload))
    print('Promote %d fresh slices into %d files, %d unique records; backup: %s' %
          (len(files), len(planned), len(found), backup.relative_to(ROOT)))
    print('Sample:', files[0][0].relative_to(ROOT), '->', files[0][1].relative_to(ROOT))
    if not args.apply:
        print('DRY RUN: no files changed.')
        return
    if not args.repair:
        shutil.copytree(d.TRANSLATIONS, backup / 'prior_active')
    for item in retired:
        stale = d.TRANSLATIONS / item['file']
        assert stale.resolve().parent == d.TRANSLATIONS.resolve()
        assert sha256_file(stale) == sha256_file(backup / 'prior_active' / stale.name)
        stale.unlink()
    changes = []
    for sources, old, payload in planned:
        before = sha256_file(backup / 'prior_active' / old.name)
        old.write_bytes(payload)
        assert sha256_file(old) == hashlib.sha256(payload).hexdigest()
        changes.append({'file': old.name, 'sources': [str(x.relative_to(ROOT)) for x in sources],
                        'before_sha256': before, 'after_sha256': sha256_file(old)})
    write_json(ROOT / 'work/translation/en/retranslation_promotion_0.5.2.json',
               {'schema': 1, 'version': '0.5.2', 'records': len(found), 'fresh_slices': len(files), 'files': len(planned),
                'backup': str(backup.relative_to(ROOT)), 'retired_old_slices': retired, 'changes': changes})
    print('Fresh drafts promoted; originals preserved.')


if __name__ == '__main__':
    main()
