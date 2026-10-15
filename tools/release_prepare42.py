"""Prepare verified 0.5.42 patches using the established reader-facing notes."""
import argparse,copy,json,subprocess
from tools.common import ROOT,write_json

VERSION='0.5.42'

def plan(commit):
    from tools.game_build import VERSION as current
    if current!=VERSION:raise ValueError('Wrong current build')
    folder=ROOT/'work/output/builds'/VERSION;out=ROOT/'work/output/releases'/VERSION
    evidence=json.loads((ROOT/'work/ui'/('review42_verified_'+VERSION+'.json')).read_text('utf8'))
    image_path=ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.iso')
    image=json.loads(image_path.with_suffix('.json').read_text('utf8'))
    if image!=evidence['iso_verification'] or image_path.stat().st_size!=image['bytes']:
        raise ValueError('Release image differs from final readback')
    if (evidence['news']['paragraphs'],evidence['news']['scenario_occurrences'],len(evidence['psyco_waves']),
        evidence['keyword_popup']['description_variants'],image['files_verified_each_tree'])!=(22,38,8,286,82):
        raise ValueError('Incomplete release evidence')
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if actual!=commit:raise ValueError('Source commit must be a full commit')
    old_folder=ROOT/'work/output/releases/0.5.41'
    cfg=copy.deepcopy(json.loads((old_folder/'release-local.json').read_text('utf8')))
    cfg.update(version=VERSION,source_commit=commit)
    for row in cfg['patches']:
        row['patch']=row['patch'].replace('0.5.41',VERSION);row['target']=str(image_path)
    if {r['source_version']for r in cfg['patches']}!={'original','0.5.40'}:
        raise ValueError('Upgrade route must be from public 0.5.40')
    tool=ROOT/'work/output/release-tools-v0.5.4'
    tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if tool_commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Pinned release SDK differs')
    notes=(ROOT/'docs/RELEASE_0.5.41.md').read_text('utf8').replace('0.5.41',VERSION)
    prior=json.loads((ROOT/'work/output/iso/0.5.41/Tengoku-hen-English-0.5.41.json').read_text('utf8'))
    prior_source=json.loads((ROOT/'work/output/builds/0.5.41/source_provenance.json').read_text('utf8'))
    notes=notes.replace(prior['sha256'],image['sha256']).replace(f"{prior['bytes']:,}",f"{image['bytes']:,}")
    notes=notes.replace(prior_source['source_commit'],commit)
    # The archived notes were finalized after 0.5.41 validation. Its patch
    # sizes and successful-roundtrip prose are not evidence for this build.
    validation_start=notes.index('Both patches passed complete ISO decode round trips')
    validation_end=notes.index('### What changed since 0.5.40',validation_start)
    notes=notes[:validation_start]+'''The two routes must reconstruct the same complete ISO. `SHA256SUMS.txt`
verifies downloads and `VALIDATION.json` records complete patch round trips.
Preparation uses official Retro Trans **0.5.4**; successful validation of both
routes is required before publication. Publication and live catalog
verification remain pending.

'''+notes[validation_end:]
    old_intro='This update fixes the linked-keyword description window still displaying\nJapanese in 0.5.40, including Messenger and Meganoid.'
    intro='''This update translates missed deployment terrain rows, separates crowded
deployment labels, corrects Psyco Waves, and fits/translates war-front reports.
It also includes the linked-keyword popup fix prepared after 0.5.40.'''
    if old_intro not in notes:raise ValueError('Release intro template changed')
    notes=notes.replace(old_intro,intro)
    start=notes.index('### What changed since 0.5.40');end=notes.index('### RPCS3 compatibility',start)
    changes='''### What changed since 0.5.40

- **Deployment:** translates seven missed movement-type blocks (45 terrain
  rows). Air, ground, water and underground use the existing compact cells.
  `Left:`, `Sel.` and `MV` clear the remaining count, Team heading and
  movement bracket/value.
- **Terminology:** uses the requested **Psyco Waves** spelling and capitalization
  for both glossary aliases and all eight active dialogue references.
- **War-front reports:** supplies the complete English paragraphs before the
  game splits them into rows. Covers 22 messages at 38 scenario bindings.
  The Northern Europe headline uses two centered lines; the South America
  and Pacific Rim report displays both English rows. All report rows fit.
- **Linked-keyword popups:** includes the separate popup archive correction
  prepared in 0.5.41. All 143 entries and both description variants are
  translated, including Messenger, Meganoid, Avalon and NERV.

The earlier font, Back Log, mission-condition and selection fixes remain.
Current letter shapes and spacing are retained; selected yellow captions use
the original thinner-bordered font. The font archive is identical to 0.5.40.

Checks read back every changed terrain row, all eight compiled terminology
references and all 286 popup descriptions. The real native row-copy code,
installed English lookup and centering helpers are exercised for the news
reports. The final ISO checks all 82 files through both filesystem trees.
`VALIDATION.json` records both complete patch round trips. In-game visual
confirmation of **0.5.42** remains pending.

'''
    notes=notes[:start]+changes+notes[end:]
    notes=notes.replace('the correction delivers them to the missed popup data source.',
        'the correction delivers them to the missed popup data source. The terminology\nchange follows the user\'s explicit spelling preference.')
    return folder,out,cfg,notes,tool_commit

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    folder,out,cfg,notes,tool_commit=plan(a.source_commit)
    print(json.dumps(cfg,indent=2));print(notes)
    if not a.apply:print('DRY RUN: no release files written.');return
    doc=ROOT/'docs'/('RELEASE_'+VERSION+'.md')
    if (out/'release-local.json').exists()or doc.exists():raise ValueError('Preserve existing release preparation')
    write_json(out/'release-local.json',cfg);doc.write_text(notes,encoding='utf8')
    write_json(folder/'source_provenance.json',dict(source_commit=a.source_commit,
        release_tool_version='0.5.4',release_tool_commit=tool_commit))

if __name__=='__main__':main()
