"""Read all final native reward lines, Arm Rakers and carried Back Log guides."""
import argparse,json,shutil
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review33_reports as G,review33_names as N,ui_hook as H,dialogue_build as D
from tools.cpk import CPK
SHOTS=(('AG-bonus','26507bf5-b58d-48dd-9317-a589451adf72'),('Arm-Rakers','1a6f29ac-16a3-47af-87ce-77e71de90092'),('Back-Log','7a8cd3a9-19a6-4159-8b11-53be97e02ee5'))

def verify(version):
    folder=ROOT/'work/output/builds'/version;build=json.loads((folder/'build.json').read_text('utf8'))
    elf=(folder/'EBOOT.BIN').read_bytes();mapping=build['mapping']
    reports=G.verify(elf,mapping,build['executable']['ui_hook'],build['executable']['link_layout'])
    names=N.plan()
    if names['edits']:raise ValueError('Arm Raker capitalization regressed')
    from tools.ui_description_layout import advance
    rendered=D.plan(advance);rid='419:t_1:178';text=rendered[rid]
    if 'Arm Rakers'not in text or 'arm Rakers'in text:raise ValueError('Rendered Arm Rakers differs')
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        raw=arc.read(next(r for r in arc.files if r['id']==419))
    if D.encode(text,mapping)not in raw:raise ValueError('Final Arm Rakers row is stale')
    print('22 native report messages / 97 occurrences / 36 whole-and-line keys, centered English and Arm Rakers passed.',flush=True)
    from tools.verify_review32 import verify as previous
    prior=previous(version);shots=[]
    for label,identifier in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+identifier+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-review33-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
                reports=reports,names=names,screenshots=shots,runtime_verified=False)

def main():
    from tools.game_build import VERSION
    ap=argparse.ArgumentParser();ap.add_argument('--version',default=VERSION);ap.add_argument('--apply',action='store_true');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
    if a.preview:print('DRY RUN: reward paragraph/draw/origin execution, final Arm Rakers row and all carried checks; no evidence written.');return
    data=verify(a.version);print('ISO:',data['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    def archive(report):
        for shot in report.get('screenshots',[]):
            src=Path(shot['source']);dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot differs')
            if src!=dst:shutil.copyfile(src,dst)
        if 'prior_verification'in report:archive(report['prior_verification'])
    archive(data);write_json(ROOT/'work/ui'/('review33_verified_'+a.version+'.json'),data)

if __name__=='__main__':main()
