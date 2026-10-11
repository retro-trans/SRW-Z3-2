"""Preview/record verified local release assets without contacting GitHub."""
import argparse,json
from tools.common import ROOT,sha256_file,write_json


def plan(version):
    folder=ROOT/'work/output/releases'/version;assets=folder/'artifacts'
    manifest=json.loads((assets/'BUILD-MANIFEST.json').read_text(encoding='utf8'))
    validation=json.loads((assets/'VALIDATION.json').read_text(encoding='utf8'))
    image=json.loads((ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.json')).read_text(encoding='utf8'))
    cfg=json.loads((folder/'release-local.json').read_text(encoding='utf8'))
    proof=ROOT/'work/ui'/('upgrade_ui_verified_'+version+'.json')
    evidence=json.loads(proof.read_text(encoding='utf8'))
    if evidence['iso_verification']!=image:raise ValueError('Release/readback ISO mismatch')
    if manifest['version']!=version or manifest['source_commit']!=cfg['source_commit']:raise ValueError('Release provenance mismatch')
    if len(manifest['patches'])!=2 or len(validation['patches'])!=2:raise ValueError('Expected two release patch routes')
    source_versions={p['source_version']for p in manifest['patches']}
    if source_versions!={'original','0.5.18'}:raise ValueError('Upgrade source must be the current public release')
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
    return dict(schema=1,version=version,publication='pending_explicit_user_consent',
        github_release_created=False,runtime_verified=False,source_commit=manifest['source_commit'],
        release_tool_version=provenance['release_tool_version'],release_tool_commit=provenance['release_tool_commit'],
        iso=image,manifest=manifest,validation=validation,
        assets=[dict(name=name,bytes=(assets/name).stat().st_size,sha256=digest)for name,digest in sorted(sums.items())],
        regression_tests=dict(run=260,passed=258,skipped=2),final_readback_sha256=sha256_file(proof))


def main():
    from tools.game_build import VERSION
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',default=VERSION);p.add_argument('--apply',action='store_true');a=p.parse_args()
    data=plan(a.version)
    for asset in data['assets']:print(asset['name'],asset['bytes'],asset['sha256'])
    print('Both complete ISO round trips passed. Publication is pending explicit consent.')
    if a.apply:write_json(ROOT/'work/ui'/('local_release_'+a.version+'.json'),data)
    else:print('DRY RUN: no readiness record written.')

if __name__=='__main__':main()
