"""Prepare the original and public-0.5.44 Retro Trans routes without publishing."""
import argparse, json, subprocess
from tools.common import ROOT, write_json

VERSION='0.5.45'


def plan(commit):
    proof=json.loads((ROOT/f'work/ui/review45_verified_{VERSION}.json').read_text('utf8'))
    if (len(proof['command_lookups']),len(proof['command_origins']),len(proof['palace_origins']),len(proof['dialogue']))!=(10,48,3,3):
        raise ValueError('Incomplete screenshot verification')
    image=ROOT/f'work/output/iso/{VERSION}/Tengoku-hen-English-{VERSION}.iso'
    target=json.loads(image.with_suffix('.json').read_text('utf8'))
    if target!=proof['iso_verification']:raise ValueError('Release image differs from readback')
    actual=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if actual!=commit:raise ValueError('Source commit must be a full commit')
    tool=ROOT/'work/output/release-tools-v0.5.4'
    tool_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    if tool_commit!='8edfb2e1c0d0c74df67107d80803177cc5939079':raise ValueError('Pinned SDK differs')
    previous=json.loads((ROOT/'work/output/releases/0.5.44/release-local.json').read_text('utf8'))
    cfg={k:previous[k] for k in ('game_id','game_name','platform')}
    cfg.update(version=VERSION,source_commit=commit,patches=[])
    for source_version,source in [('original',previous['patches'][0]['source']),
        ('0.5.44',str(ROOT/'work/output/iso/0.5.44/Tengoku-hen-English-0.5.44.iso'))]:
        cfg['patches'].append(dict(patch=f'SRW-Z3-2-PS3-English-{VERSION}-from-{source_version}.xdelta',
            edition='jp-bljs10299',language='en',source_version=source_version,source_format='iso',
            target_format='iso',source=source,target=str(image)))
    notes=f'''English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update fits D-Command labels and help, the palace location caption,
the long Target Lock part name and one timed narration row. It includes
the requested **Chaos Caper** spelling.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.44** ISO, and choose **Latest (0.5.45)** after this
prepared release is published and its catalog refresh is verified.
Write a new output image and keep your source.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.45-from-original.xdelta` |
| Exact English 0.5.44 | `SRW-Z3-2-PS3-English-0.5.45-from-0.5.44.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.45-from-original.xdelta" "Tengoku-hen-English-0.5.45.iso"
```

Keep checksum checks enabled. `BUILD-MANIFEST.json` lists exact input and
output identities; folder dumps and repacked images are not substitutes.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**, SHA-256
  `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Patched 0.5.45 ISO: **{target['bytes']:,} bytes**, SHA-256
  `{target['sha256']}`.

Both routes must reconstruct this complete target image before delivery.
`SHA256SUMS.txt` verifies downloads and `VALIDATION.json` records complete
patch round trips. Preparation uses official Retro Trans **0.5.4**.
Publication and live catalog verification remain pending.

### What changed since 0.5.44

- **D-Commands:** removes retained bullet glyphs from all six labels using
  invisible spacing. Selected, preloaded and disabled labels retain their
  geometry and styles. Keep Combo's complete effect fits its two footer rows.
- **Location caption:** displays Wrath Babylon Imperial Palace and Spirit
  Quanta Absorption System on two centered lines, clear of the portrait.
- **Power parts:** uses `Hyperdim. Target Lock` so the name clears the stock
  counts. The part's effects, stats and counts are unchanged.
- **Narration:** retains every word of the reported project-contribution
  sentence and uses the existing narrower alphabet for that timed row.
  Its original timing and adjacent rows remain intact.
- **Terminology:** uses **Chaos Caper** in both dialogue references and
  confirms the spelling in the active glossary and glossary seed.

Ten installed lookups and 48 selected/preloaded command-origin cases pass.
The palace caption passes native centering at three sizes. All 4,803 widgets
retain their geometry and states; only the six-row command text changes.
Readback checks the changed script members, unchanged part stats, fonts and
other archive members. Both ISO filesystem trees verify all 82 files.
In-game visual confirmation of **0.5.45** remains pending.

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Fresh-boot the new image and load an in-game save. Emulator save states can
retain older text. Back up your installation and savedata before updating.
When updating from a version older than 0.5.44, follow its cache-reinstall
instructions for the corrected keyword-popup archive; preserve savedata.

Test D-Command selection and help, the palace caption, Target Lock stock counts
and the reported narration. Include the build number and screenshots in reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary and revised with playtest
feedback. This update fits existing English without dropping the narration's
words or changing item effects. Chaos Caper follows the user's spelling.

### Acknowledgements

Thanks to the playtesters reporting missing text and supplying screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the patches. GitHub's automatic source archives contain
project sources and documentation, not an ISO. Source-dependent tools require
locally supplied game data. Build-source commit: `{commit}`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
'''
    return cfg,notes,tool_commit


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-commit',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    cfg,notes,tool_commit=plan(a.source_commit);print(json.dumps(cfg,indent=2));print(notes)
    if not a.apply:print('DRY RUN: no release files written.');return
    path=ROOT/f'work/output/releases/{VERSION}/release-local.json';doc=ROOT/f'docs/RELEASE_{VERSION}.md'
    if path.exists() or doc.exists():raise ValueError('Preserve existing release preparation')
    write_json(path,cfg)
    doc.write_bytes(notes.encode('utf8'))
    write_json(ROOT/f'work/output/builds/{VERSION}/source_provenance.json',dict(source_commit=a.source_commit,
        release_tool_version='0.5.4',release_tool_commit=tool_commit))


if __name__=='__main__':main()
