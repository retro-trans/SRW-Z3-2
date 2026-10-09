"""Audit fresh translation coverage without treating old active English as fresh work."""
import argparse,json
from collections import Counter
from tools import dialogue as d
from tools import dialogue_retranslate as r
from tools.common import ROOT,sha256_file,write_json

def audit(validate=False):
    source=d.plan_rows();expected={x['id']:x['sha'] for x in source}
    assigned=[];completed=set();items=[];errors=[]
    for batch in range(1,13):
        r.configure(batch)
        scope={x['id']:x['sha'] for x in source if x['stage'] in r.STAGES};assigned.extend(scope)
        path=r.RUN/'manifest.json';m=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        state=m.get('state','not_started');done=state in ('draft_complete_validated','draft_complete_fit_review_required')
        observed={};batch_errors=[]
        for f in sorted((r.RUN/'drafts').glob('*.json')):
            data=json.loads(f.read_text(encoding='utf-8'));info=m.get('slices',{}).get(f.stem)
            if info is None:batch_errors.append('Unassigned file '+f.name);continue
            for rid,row in data.get('rows',{}).items():
                if rid in observed:batch_errors.append('Duplicate '+rid)
                observed[rid]=row.get('sha')
                if not row.get('en','').partition('\n')[2].strip():batch_errors.append('Empty speech '+rid)
            if done:
                if sha256_file(f)!=info.get('draft_sha256'):batch_errors.append('Draft hash mismatch '+f.name)
                report=data.get('report',{})
                if report.get('rows_examined')!=len(data['rows']) or report.get('left_untranslated'):batch_errors.append('Incomplete examination '+f.name)
        if any(scope.get(k)!=v for k,v in observed.items()):batch_errors.append('Unexpected source IDs/fingerprints')
        if done and observed!=scope:batch_errors.append('Completed manifest does not cover expected source')
        strict=None
        if validate and done:strict=r.check()
        if done and not batch_errors:completed.update(observed)
        errors.extend('Batch%d: %s'%(batch,e) for e in batch_errors)
        item=dict(batch=batch,scope=r.SCOPE,run=str(r.RUN.relative_to(ROOT)),expected_rows=len(scope),drafted_rows=len(observed),state=state,recorded_validation=m.get('validation'),current_strict_validation=strict,errors=batch_errors)
        items.append(item)
        print('Batch %d: %d/%d drafted; %s; recorded check=%s%s'%(batch,len(observed),len(scope),state,m.get('validation'),'; ERRORS='+str(len(batch_errors)) if batch_errors else ''))
    if set(assigned)!=set(expected) or len(assigned)!=len(expected):errors.append('Batch plan is not an exact source partition')
    result=dict(schema=1,objective='Freshly retranslate the entire player-facing dialogue plan through the ending, alternate routes and bonus dialogue',source_rows=len(expected),completed_source_rows=len(completed),remaining_source_rows=len(set(expected)-completed),source_partition_exact=not (set(assigned)!=set(expected) or len(assigned)!=len(expected)),batches=items,errors=errors,all_fresh_coverage_complete=completed==set(expected) and not errors,current_checks_run=validate,known_build_issue='Batch5 604:t_6:4 retains eleven full Sphere names and requires four lines; layout review before build.',limitations=['Coverage and hashes do not replace human source meaning review.','A recorded PASS is historical until --validate reruns checks against the current glossary.','No promotion/build/deployment is implied.'])
    print('Fresh completed coverage: %d/%d; remaining %d; audit errors %d'%(len(completed),len(expected),result['remaining_source_rows'],len(errors)))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--validate',action='store_true');a=p.parse_args()
    result=audit(a.validate)
    if a.apply:write_json(ROOT/'work/translation/en/retranslation_progress.json',result)
    else:print('DRY RUN: coverage metadata only; no translations changed.')
    if result['errors']:raise SystemExit(1)

if __name__=='__main__':main()
