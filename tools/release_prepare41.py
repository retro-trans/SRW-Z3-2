"""Prepare 0.5.41 delivery metadata in the approved reader-facing format."""
import argparse,json,subprocess
from pathlib import Path
from tools.common import ROOT,write_json

def plan(commit):
    from tools.game_build import VERSION
    if VERSION!='0.5.41':raise ValueError('Only the current popup fix may use this preparation')
    folder=ROOT/'work/output/builds'/VERSION;out=ROOT/'work/output/releases'/VERSION
    image_path=ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.iso')
    image=json.loads(image_path.with_suffix('.json').read_text(encoding='utf8'))
    evidence=json.loads((ROOT/'work/ui/review41_verified_0.5.41.json').read_text(encoding='utf8'))
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    if image!=evidence['iso_verification'] or build['version']!=VERSION or image_path.stat().st_size!=image['bytes']:
        raise ValueError('Mixed release build/image evidence')
    if evidence['keyword_popup']['description_variants']!=286 or image['files_verified_each_tree']!=82:
        raise ValueError('Incomplete popup/ISO coverage')
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if commit!=actual:raise ValueError('Release sources require a full commit')
    settings=json.loads((ROOT/'config/tengoku.json').read_text(encoding='utf8'))
    previous=ROOT/'work/output/iso/0.5.40/Tengoku-hen-English-0.5.40.iso'
    old=json.loads(previous.with_suffix('.json').read_text(encoding='utf8'))
    if old['version']!='0.5.40' or previous.stat().st_size!=old['bytes']:raise ValueError('Public upgrade source differs')
    tool=ROOT/'work/output/release-tools-v0.5.4'
    tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if tool_commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Release tool differs')
    def route(source,version):
        return dict(patch='SRW-Z3-2-PS3-English-0.5.41-from-'+version+'.xdelta',edition='jp-bljs10299',
            language='en',source_version=version,source_format='iso',target_format='iso',source=str(source),target=str(image_path))
    cfg=dict(game_id='srw-z3-tengoku-ps3',game_name='Super Robot Taisen Z3: Tengoku-hen (PS3)',
        platform='PS3',version=VERSION,source_commit=commit,patches=[route(Path(settings['iso']),'original'),route(previous,'0.5.40')])
    notes=f'''English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update fixes the linked-keyword description window still displaying
Japanese in 0.5.40, including Messenger and Meganoid.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.40** ISO, and choose **Latest (0.5.41)**. Write a
new output image and keep your source. These instructions apply once the
prepared release is published and its catalog refresh is verified.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.41-from-original.xdelta` |
| Exact English 0.5.40 | `SRW-Z3-2-PS3-English-0.5.41-from-0.5.40.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.41-from-original.xdelta" "Tengoku-hen-English-0.5.41.iso"
```

Use the patch matching your input version and keep checksum checks enabled.
`BUILD-MANIFEST.json` lists exact identities; folder dumps and repacked images
are not substitutes for these ISO inputs.

- Original Japanese ISO: **{Path(settings['iso']).stat().st_size:,} bytes**, SHA-256
  `{image['source_iso_sha256']}`.
- English 0.5.40 ISO: **{old['bytes']:,} bytes**, SHA-256
  `{old['sha256']}`.
- Patched 0.5.41 ISO: **{image['bytes']:,} bytes**, SHA-256
  `{image['sha256']}`.

The two routes must reconstruct the same complete ISO. `SHA256SUMS.txt`
verifies the downloads and `VALIDATION.json` records complete patch round
trips. Release preparation uses Retro Trans **0.5.4**; full validation is
required before publication.

### What changed since 0.5.40

- **Linked-keyword popups:** translates all **143 entries**, including both
  description variants (**286 descriptions**), in the separate archive this
  screen actually loads. This includes Messenger, Meganoid, Avalon and NERV.
- **Complete English prose:** wraps the existing reviewed translations and
  expands the text pool. Preserves lookup names, series, entry order, IDs and
  flags so keyword links continue to identify the same entries.
- **Corrected coverage check:** checks the actual deployed popup archive.
  Earlier checks covered the Library archive and executable dictionary but
  missed this third copy; they did not prove the popup was translated.

All other 0.5.40 game assets are retained, apart from the title version stamp.
The earlier font, Back Log, selection and mission-condition fixes remain.

The old bug was confirmed by read-only live inspection: all 143 popup records
and 572 fields matched the unchanged Japanese archive. The corrected archive
passes complete record and compressed-file readback. Sixteen focused checks
pass; all 82 ISO files are verified through both filesystem trees. Matching
parent-asset hashes retain earlier regression evidence. In-game visual
confirmation of **0.5.41** remains pending.

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Close RPCS3 and back up your installation before updating. Move only
`dev_hdd0/game/BLJS10299_DATA`, if present, to a backup outside `dev_hdd0/game`
so the game reinstalls the corrected popup archive. Preserve savedata and
other games. Fresh-boot the new image and load an in-game save; emulator
save states can retain the old Japanese popup data.

Test several keyword links, their scrolling and both description variants.
Include the build number and a screenshot with reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary, edited and revised with
playtesting feedback. This update uses the existing English descriptions;
the correction delivers them to the missed popup data source.

### Acknowledgements

Thanks to the playtesters reporting missing text and providing screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the game patches. GitHub's automatic source archives
contain project sources and documentation, not an ISO. Source-dependent tools
require locally supplied game data. Build-source commit: `{commit}`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
'''
    return out,folder,cfg,notes,tool_commit

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);p.add_argument('--version',default='0.5.41')
    p.add_argument('--upgrade-from',default='0.5.40');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.version!='0.5.41' or a.upgrade_from!='0.5.40':raise ValueError('Wrong current public upgrade route')
    out,folder,cfg,notes,tool_commit=plan(a.source_commit)
    print(json.dumps(cfg,indent=2));print(notes)
    if not a.apply:print('DRY RUN: no release files written.');return
    doc=ROOT/'docs/RELEASE_0.5.41.md'
    if (out/'release-local.json').exists()or doc.exists():raise ValueError('Preserve existing release preparation')
    write_json(out/'release-local.json',cfg);doc.write_text(notes,encoding='utf8')
    write_json(folder/'source_provenance.json',dict(source_commit=a.source_commit,
        release_tool_version='0.5.4',release_tool_commit=tool_commit))

if __name__=='__main__':main()
