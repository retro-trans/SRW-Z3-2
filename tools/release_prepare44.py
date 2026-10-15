"""Prepare validated 0.5.44 delivery routes and reader-facing notes, without publishing."""
import argparse,copy,json,subprocess
from tools.common import ROOT,write_json

VERSION='0.5.44'


def plan(commit):
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Wrong current build')
    folder=ROOT/'work/output/builds'/VERSION;out=ROOT/'work/output/releases'/VERSION
    proof=json.loads((ROOT/'work/ui'/('review44_verified_'+VERSION+'.json')).read_text('utf8'))
    image_path=ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.iso');image=json.loads(image_path.with_suffix('.json').read_text('utf8'))
    if image!=proof['iso_verification']or image_path.stat().st_size!=image['bytes']:raise ValueError('Final image differs')
    if (len(proof['dialogue']),len(proof['library']),len(proof['reward_cases']),len(proof['command_lookups']))!=(13,10,33,14):
        raise ValueError('Incomplete current evidence')
    if len(proof['caption_cases'])!=20:raise ValueError('Missing selected/preloaded caption measurements')
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if actual!=commit:raise ValueError('Source commit must be a full commit')
    cfg=copy.deepcopy(json.loads((ROOT/'work/output/releases/0.5.43/release-local.json').read_text('utf8')));cfg.update(version=VERSION,source_commit=commit)
    for row in cfg['patches']:row['patch']=row['patch'].replace('0.5.43',VERSION);row['target']=str(image_path)
    if {r['source_version']for r in cfg['patches']}!={'original','0.5.40'}:raise ValueError('Upgrade route is not public 0.5.40')
    tool=ROOT/'work/output/release-tools-v0.5.4';tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if tool_commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Pinned SDK differs')
    notes=(ROOT/'docs/RELEASE_0.5.43.md').read_text('utf8').replace('0.5.43',VERSION)
    prior=json.loads((ROOT/'work/output/iso/0.5.43/Tengoku-hen-English-0.5.43.json').read_text('utf8'))
    provenance=json.loads((ROOT/'work/output/builds/0.5.43/source_provenance.json').read_text('utf8'))
    notes=notes.replace(prior['sha256'],image['sha256']).replace(f"{prior['bytes']:,}",f"{image['bytes']:,}").replace(provenance['source_commit'],commit)
    start=notes.index('This update');end=notes.index('### Apply',start)
    notes=notes[:start]+'''This update uses Colony Laser consistently, separates Sub Order rewards
from their values, fits the deployment upgrade caption, and removes the
unwanted glyphs before deployment command labels. It includes the prepared
keyword-popup, deployment, news and map-panel fixes after public 0.5.40.

'''+notes[end:]
    start=notes.index('Both patches passed complete ISO reconstruction checks');end=notes.index('### What changed since 0.5.40',start)
    notes=notes[:start]+'''The two routes must reconstruct the same complete ISO. `SHA256SUMS.txt`
verifies downloads and `VALIDATION.json` records complete patch round trips.
Preparation uses official Retro Trans **0.5.4**; successful validation of both
routes is required before publication. Publication and live catalog
verification remain pending.

'''+notes[end:]
    mark='### What changed since 0.5.40\n\n'
    notes=notes.replace(mark,mark+'''- **Colony Laser:** preserves both capitals in the glossary, all 13 active
  dialogue references, and ten affected Library records, including room headings.
- **Sub Order results:** uses `EXP each:`, `PP each:` and `Kills each:` beside
  separate aligned values. Labels clear the number field through eight digits.
- **Deployment menus:** uses `Mech/Wpn Upg` within the existing button. Replaces
  the retained Japanese bullet prefixes with invisible spacing in both selection
  states; menu letters keep their current shapes and indentation.
''')
    start=notes.index('Checks read back the deployed movement components');end=notes.index('### RPCS3 compatibility',start)
    notes=notes[:start]+'''Checks read back all 13 compiled dialogue references, ten Library records,
seven affected widgets and three moved numeric endpoints. The installed native
numeric code runs at every tested digit boundary; all 33 reward cases clear
their labels. Fourteen native dictionary lookups deliver the corrected menu
text, and twenty native caption cases keep selected and preloaded labels
aligned. Font archives and advances are unchanged. Earlier phase/Trans-Am checks
pass again, and the final ISO verifies all 82 files through both filesystem
trees. In-game visual confirmation of **0.5.44** remains pending.

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
