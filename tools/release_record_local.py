"""Preview/record verified local release assets without contacting GitHub."""
import argparse,json
from tools.common import ROOT,sha256_file,write_json


def plan(version):
    folder=ROOT/'work/output/releases'/version;assets=folder/'artifacts'
    manifest=json.loads((assets/'BUILD-MANIFEST.json').read_text(encoding='utf8'))
    validation=json.loads((assets/'VALIDATION.json').read_text(encoding='utf8'))
    image=json.loads((ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.json')).read_text(encoding='utf8'))
    cfg=json.loads((folder/'release-local.json').read_text(encoding='utf8'))
    proof=ROOT/'work/ui'/(('review25_verified_' if version=='0.5.25' else 'review24_verified_' if version=='0.5.24' else 'review23_verified_' if version=='0.5.23' else 'review22_verified_' if version=='0.5.22' else 'review21_verified_' if version=='0.5.21' else 'upgrade_ui_verified_')+version+'.json')
    if version=='0.5.26':proof=ROOT/'work/ui'/('review26_verified_'+version+'.json')
    if version=='0.5.27':proof=ROOT/'work/ui'/('review27_verified_'+version+'.json')
    if version=='0.5.28':proof=ROOT/'work/ui'/('review28_verified_'+version+'.json')
    if version=='0.5.29':proof=ROOT/'work/ui'/('review29_verified_'+version+'.json')
    if version=='0.5.30':proof=ROOT/'work/ui'/('review30_verified_'+version+'.json')
    if version=='0.5.31':proof=ROOT/'work/ui'/('review31_verified_'+version+'.json')
    if version=='0.5.32':proof=ROOT/'work/ui'/('review32_verified_'+version+'.json')
    if version=='0.5.33':proof=ROOT/'work/ui'/('review33_verified_'+version+'.json')
    if version=='0.5.34':proof=ROOT/'work/ui'/('review34_verified_'+version+'.json')
    if version=='0.5.35':proof=ROOT/'work/ui'/('review35_verified_'+version+'.json')
    if version=='0.5.36':proof=ROOT/'work/ui'/('review36_verified_'+version+'.json')
    if version=='0.5.37':proof=ROOT/'work/ui'/('review37_verified_'+version+'.json')
    if version=='0.5.38':proof=ROOT/'work/ui'/('review38_verified_'+version+'.json')
    if version=='0.5.39':proof=ROOT/'work/ui'/('review39_verified_'+version+'.json')
    if version=='0.5.40':proof=ROOT/'work/ui'/('review40_verified_'+version+'.json')
    evidence=json.loads(proof.read_text(encoding='utf8'))
    if evidence['iso_verification']!=image:raise ValueError('Release/readback ISO mismatch')
    if manifest['version']!=version or manifest['source_commit']!=cfg['source_commit']:raise ValueError('Release provenance mismatch')
    if len(manifest['patches'])!=2 or len(validation['patches'])!=2:raise ValueError('Expected two release patch routes')
    source_versions={p['source_version']for p in manifest['patches']}
    previous_public='0.5.28' if version in ('0.5.29','0.5.30','0.5.31','0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40') else '0.5.18'
    if source_versions!={'original',previous_public}:raise ValueError('Upgrade source must be the current public release')
    for patch,report in zip(manifest['patches'],validation['patches']):
        if (patch['target_bytes'],patch['target_sha256'])!=(image['bytes'],image['sha256']):raise ValueError('Patch target differs from final ISO')
        if report['patch']!=patch['patch']or report['roundtrip_verified']is not True or report['target_sha256']!=image['sha256']:
            raise ValueError('Patch lacks successful complete ISO roundtrip')
    sums={}
    for line in (assets/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines():
        digest,name=line.split('  ',1)
        if sha256_file(assets/name)!=digest:raise ValueError('Asset checksum differs: '+name)
        sums[name]=digest
    sums['SHA256SUMS.txt']=sha256_file(assets/'SHA256SUMS.txt')
    if set(sums)!={p.name for p in assets.iterdir()}or len(sums)!=5:raise ValueError('Release asset inventory differs')
    provenance=json.loads((ROOT/'work/output/builds'/version/'source_provenance.json').read_text(encoding='utf8'))
    # Use the actual successful test log parsed by startup verification.
    import re
    log=ROOT/('work/output/scratch/startup-%s-tests.log'%version);raw=log.read_bytes()
    text=raw.decode('utf-16' if raw[:2]in(b'\xff\xfe',b'\xfe\xff')else 'utf-8-sig')
    match=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)',text)
    if not match:raise ValueError('Regression log does not confirm success')
    run,skip=int(match[1]),int(match[2]or 0)
    return dict(schema=1,version=version,publication='pending_explicit_user_consent',
        github_release_created=False,runtime_verified=False,source_commit=manifest['source_commit'],
        release_tool_version=provenance['release_tool_version'],release_tool_commit=provenance['release_tool_commit'],
        iso=image,manifest=manifest,validation=validation,
        assets=[dict(name=name,bytes=(assets/name).stat().st_size,sha256=digest)for name,digest in sorted(sums.items())],
        regression_tests=dict(run=run,passed=run-skip,skipped=skip),final_readback_sha256=sha256_file(proof),
        **(dict(carried_regression_tests=dict(evidence['carried_verification']['regression_tests'],source_version='0.5.35'))
           if version=='0.5.36' else
           dict(carried_regression_tests=dict(evidence['carried_verification']['regression_tests'],source_version='0.5.38'))
           if version=='0.5.39' else
           dict(carried_regression_tests=evidence['carried_verification']['full_regression_tests'],
                carried_ui_checks=dict(evidence['carried_verification']['regression_tests'],source_version='0.5.39'))
           if version=='0.5.40' else {}))


def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args()
    data=plan(a.version)
    for asset in data['assets']:print(asset['name'],asset['bytes'],asset['sha256'])
    print('Both complete ISO round trips passed. Publication is pending explicit consent.')
    if a.apply:write_json(ROOT/'work/ui'/('local_release_'+a.version+'.json'),data)
    else:print('DRY RUN: no readiness record written.')

if __name__=='__main__':main()
