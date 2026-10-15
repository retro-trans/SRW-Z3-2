"""Final native news-row readback, startup carry checks and prior UI regression."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from tools.common import ROOT, sha256_file, write_json, contained
from tools import review35_news as N
from tools.cpk import CPK

SHOTS = (('counteroffensives', 'd0a2f84e-11d0-41ef-afc5-614b23a46b7e'),
         ('midway-resistance', '15935901-2cbd-4919-afea-6fa9d575bf1f'))


def verify(version):
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text('utf8'))
    for name, digest in build['outputs'].items():
        if sha256_file(folder/name) != digest:
            raise ValueError('Final game asset changed: '+name)
    news = N.verify((folder/'EBOOT.BIN').read_bytes(), build['mapping'],
                    build['executable']['ui_hook'], build['executable']['link_layout'])
    print('All 22 news messages, 13 separate row keys and 26 native origins passed.', flush=True)
    prior_build = json.loads((ROOT/'work/output/builds/0.5.34/build.json').read_text('utf8'))
    # Exact font/startup archive identity carries the independently reviewed
    # three English startup screens, including all 20 translated credit rows.
    if build['outputs']['TPACKPS3.CPK'] != prior_build['outputs']['TPACKPS3.CPK']:
        raise ValueError('Carried startup/font archive changed')
    baseline = ROOT/'work/ui/review34_verified_0.5.34.json'
    ready = json.loads((ROOT/'work/ui/local_release_0.5.34.json').read_text('utf8'))
    if sha256_file(baseline) != ready['final_readback_sha256']:
        raise ValueError('Carried startup proof changed')
    from tools.pipeline import config
    stage_sha = prior_build['stage_archive']['cpk_sha256']
    if sha256_file(folder/'STGZ3OF2.cpk') != stage_sha:
        raise ValueError('Carried stage script bytes changed')
    with tempfile.TemporaryDirectory(prefix='review35-stage-', dir=ROOT/'work/output/scratch') as temp:
        contained(ROOT/'work/output/scratch', temp)
        decoded = Path(temp)/'stage.cpk'
        tool = config(ROOT/'config/tengoku.json')['offline_sdat_tool']
        result = subprocess.run([str(tool), '-d', str(folder/'STGZ3OF2.SDAT'), str(decoded), '0'], capture_output=True)
        if result.returncode or not decoded.exists() or sha256_file(decoded) != stage_sha:
            raise ValueError('Shipped stage encryption changed its verified content')
    from tools import title_screen as T, eff_art as E
    raw = E.source_members(E._settings(), [T.MEMBER], {T.MEMBER: T.SOURCE_SHA})[T.MEMBER]
    expected, pixels, _, title = T.render(raw, version)
    with CPK(folder/'EFFPS3.CPK') as arc:
        actual = arc.read(next(r for r in arc.files if r['id'] == T.MEMBER))
    if actual != expected:
        raise ValueError('Final title version differs')
    T.verify(raw, actual, pixels)
    from tools.verify_review33 import verify as previous
    prior = previous(version)
    shots = []
    for label, ident in SHOTS:
        src = Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst = ROOT/'work/ui/screenshots'/('reported-review35-'+label+'.png')
        if not src.exists():
            src = dst
        shots.append(dict(issue=label, source=str(src), saved_path=str(dst),
                          sha256=sha256_file(src), runtime_confirmation=False))
    return dict(schema=1, version=version, news=news, prior_verification=prior,
                iso_verification=prior['iso_verification'], title=title,
                startup_carried=dict(proof=str(baseline), sha256=sha256_file(baseline),
                    archive_sha256=build['outputs']['TPACKPS3.CPK']),
                decoded_stage_sha256=stage_sha, stage_decryption_verified=True,
                screenshots=shots, runtime_verified=False)


def main():
    from tools.game_build import VERSION
    p = argparse.ArgumentParser(); p.add_argument('--version', default=VERSION)
    p.add_argument('--apply', action='store_true'); p.add_argument('--preview', action='store_true')
    args = p.parse_args()
    if args.preview:
        print('DRY RUN: native news paragraph/draw/origin checks, startup archive identity, title and all carried checks.')
        return
    data = verify(args.version)
    print('ISO:', data['iso_verification']['sha256'])
    if not args.apply:
        print('DRY RUN: no evidence or screenshots written.')
        return
    def archive(report):
        for row in report.get('screenshots', []):
            src, dst = Path(row['source']), Path(row['saved_path'])
            dst.parent.mkdir(parents=True, exist_ok=True)
            if sha256_file(src) != row['sha256']:
                raise ValueError('Screenshot source changed')
            if dst.exists() and sha256_file(dst) != row['sha256']:
                dst = dst.with_name(dst.stem+'-'+row['sha256'][:12]+dst.suffix)
                row['saved_path'] = str(dst)
                if dst.exists() and sha256_file(dst) != row['sha256']:
                    raise ValueError('Screenshot digest collision')
            if src != dst:
                shutil.copyfile(src, dst)
        if 'prior_verification' in report:
            archive(report['prior_verification'])
    archive(data)
    write_json(ROOT/'work/ui'/('review35_verified_'+args.version+'.json'), data)


if __name__ == '__main__':
    main()
