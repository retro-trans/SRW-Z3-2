"""Prepare both 0.5.43 routes and matching release notes; never publish."""
import argparse,copy,json,subprocess
from tools.common import ROOT,write_json

VERSION='0.5.43'


def plan(commit):
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Wrong current build')
    folder=ROOT/'work/output/builds'/VERSION;out=ROOT/'work/output/releases'/VERSION
    evidence=json.loads((ROOT/'work/ui'/('review43_verified_'+VERSION+'.json')).read_text('utf8'))
    image_path=ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.iso')
    image=json.loads(image_path.with_suffix('.json').read_text('utf8'))
    if image!=evidence['iso_verification']or image_path.stat().st_size!=image['bytes']:raise ValueError('Final image differs')
    if (len(evidence['phase']['phase_origins']),len(evidence['terrain_component_rows']),
        len(evidence['terrain_masks']),image['files_verified_each_tree'])!=(14,12,16,82):raise ValueError('Incomplete evidence')
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if actual!=commit:raise ValueError('Source commit must be a full commit')
    cfg=copy.deepcopy(json.loads((ROOT/'work/output/releases/0.5.42/release-local.json').read_text('utf8')))
    cfg.update(version=VERSION,source_commit=commit)
    for row in cfg['patches']:
        row['patch']=row['patch'].replace('0.5.42',VERSION);row['target']=str(image_path)
    if {r['source_version']for r in cfg['patches']}!={'original','0.5.40'}:raise ValueError('Upgrade route is not public 0.5.40')
    tool=ROOT/'work/output/release-tools-v0.5.4'
    tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if tool_commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Pinned SDK differs')
    notes=(ROOT/'docs/RELEASE_0.5.42.md').read_text('utf8').replace('0.5.42',VERSION)
    prior=json.loads((ROOT/'work/output/iso/0.5.42/Tengoku-hen-English-0.5.42.json').read_text('utf8'))
    provenance=json.loads((ROOT/'work/output/builds/0.5.42/source_provenance.json').read_text('utf8'))
    notes=notes.replace(prior['sha256'],image['sha256']).replace(f"{prior['bytes']:,}",f"{image['bytes']:,}")
    notes=notes.replace(provenance['source_commit'],commit)
    start=notes.index('This update');end=notes.index('### Apply',start)
    notes=notes[:start]+'''This update centers the end-phase warning, separates the Aboard count,
translates composed movement cells, corrects “A Tenshi,” and fits Trans-Am.
It includes the deployment, Psyco Waves, war-front and keyword-popup fixes
prepared after public 0.5.40.

'''+notes[end:]
    start=notes.index('Both patches passed complete ISO decode round trips');end=notes.index('### What changed since 0.5.40',start)
    notes=notes[:start]+'''The two routes must reconstruct the same complete ISO. `SHA256SUMS.txt`
verifies downloads and `VALIDATION.json` records complete patch round trips.
Preparation uses official Retro Trans **0.5.4**; successful validation of both
routes is required before publication. Publication and live catalog
verification remain pending.

'''+notes[end:]
    mark='### What changed since 0.5.40\n\n'
    notes=notes.replace(mark,mark+'''- **End phase:** centers the complete warning using the actual widths of
  English text and the live team count. The Yes/No selection keeps its position.
- **Map panel:** replaces the overlapping Aboard/Team fragments with `Aboard:`
  and translates the movement and terrain components before composition.
- **Dialogue:** corrects Syam's “An Tenshi” to “A Tenshi.”
- **Command menu:** uses `Trans-Am`, fitting inside the button. Its separate
  activation question remains `Activate Trans-Am?`.
''')
    start=notes.index('Checks read back every changed terrain row');end=notes.index('### RPCS3 compatibility',start)
    notes=notes[:start]+'''Checks read back the deployed movement components, the corrected stage record
and the command lookup. Native centering runs with seven live counts at two
text sizes. All 4,803 widget states and geometry remain unchanged. News
selectors, copied English rows and centering are checked again; the popup and
font archives match the certified prepared build. The final ISO checks all
82 files through both filesystem trees. `VALIDATION.json` records complete
patch round trips. In-game visual confirmation of **0.5.43** remains pending.

'''+notes[end:]
    return folder,out,cfg,notes,tool_commit


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    folder,out,cfg,notes,tool_commit=plan(a.source_commit);print(json.dumps(cfg,indent=2));print(notes)
    if not a.apply:print('DRY RUN: no release files written.');return
    doc=ROOT/'docs'/('RELEASE_'+VERSION+'.md')
    if (out/'release-local.json').exists()or doc.exists():raise ValueError('Preserve existing release preparation')
    write_json(out/'release-local.json',cfg);doc.write_text(notes,encoding='utf8')
    write_json(folder/'source_provenance.json',dict(source_commit=a.source_commit,release_tool_version='0.5.4',release_tool_commit=tool_commit))

if __name__=='__main__':main()
