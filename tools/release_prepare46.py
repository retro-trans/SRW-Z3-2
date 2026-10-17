"""Prepare the original and public-0.5.44 Retro Trans routes without publishing."""
import argparse, json, subprocess, re
from tools.common import ROOT, write_json

VERSION='0.5.46'


def plan(commit):
    proof=json.loads((ROOT/f'work/ui/review46_verified_{VERSION}.json').read_text('utf8'))
    if (len(proof['no_pilot_cases'])!=12 or proof['stages']['all_records']!=63553
        or len(proof['stages']['dialogue_records'])!=424 or proof['widgets_checked']!=4803
        or proof['native_keyword_descriptions']['owned_consumer_cases']!=572
        or len(proof['carried_command_origins'])!=48 or len(proof['carried_palace_origins'])!=3
        or not proof['font_codes_artwork_and_advances_unchanged']):
        raise ValueError('Incomplete screenshot verification')
    raw_log=(ROOT/f'work/output/scratch/startup-{VERSION}-tests.log').read_bytes()
    test_log=raw_log.decode('utf-16'if raw_log[:2]in(b'\xff\xfe',b'\xfe\xff')else'utf-8-sig')
    tested=re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?',test_log)
    if not tested:raise ValueError('A complete successful regression run is required')
    run,skip=int(tested[1]),int(tested[2]or 0)
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

This update uses **Herald / Heralds** for the original faction, corrects the
empty-pilot name display, and fits conversion-part names, the fundraising
heading and the ability-status indicator. It also includes the prepared
D-Command, palace-caption, Target Lock and narration fixes, plus **Chaos Caper**.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.44** ISO, and choose **Latest (0.5.46)** after this
prepared release is published and its catalog refresh is verified.
Write a new output image and keep your source.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.46-from-original.xdelta` |
| Exact English 0.5.44 | `SRW-Z3-2-PS3-English-0.5.46-from-0.5.44.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.46-from-original.xdelta" "Tengoku-hen-English-0.5.46.iso"
```

Keep checksum checks enabled. `BUILD-MANIFEST.json` lists exact input and
output identities; folder dumps and repacked images are not substitutes.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**, SHA-256
  `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Patched 0.5.46 ISO: **{target['bytes']:,} bytes**, SHA-256
  `{target['sha256']}`.

Both routes must reconstruct this complete target image before delivery.
`SHA256SUMS.txt` verifies downloads and `VALIDATION.json` records complete
patch round trips. Preparation uses official Retro Trans **0.5.4**.
Publication and live catalog verification remain pending.

### What changed since 0.5.44

- **Heralds:** uses the requested faction name in 424 dialogue records,
  battle text, Library descriptions and linked-keyword popup copies. Singular
  references use Herald. Evangelion Angels, Aquarion Shadow Angels and the
  pilot Angel retain their own names.
- **Empty-pilot display:** corrects the fallback name encoding used when a
  unit has no assigned pilot. Live pilot-name pointers and unit stats stay intact.
- **Conversion parts:** fits `Emerg. Deploy Booster`, `Light Config.` and
  `Assault Config.` in the existing selected-name boxes and lists.
- **Fundraising:** shortens the heading to `Funds` and separates its remaining
  pilot caption from the live count.
- **Unit Stats:** fits the status label as `Ability Active`.
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

Readback checks the 424 affected dialogue records, changed Library entries,
all actual linked-keyword popup entries and the installed UI lookups. Twelve
native no-pilot / live-name cases and 572 native keyword consumer cases pass.
Both font pages, the font allocation and all letter advances are unchanged.
All 4,803 widget identities and styles are checked; only the remaining-pilot
caption changes position. Both ISO filesystem trees verify all 82 files.
The full regression run passes **{run-skip} tests**, with **{skip}** optional
check skipped. In-game visual confirmation of **0.5.46** remains pending.

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Close RPCS3 and back up your installation before updating. Move only
`dev_hdd0/game/BLJS10299_DATA`, if present, to a backup outside
`dev_hdd0/game` so the game reinstalls the updated assets, including the
keyword-popup archive. Preserve savedata and other games. Fresh-boot the
new image and load an in-game save; emulator save states can retain old text.

Test Bonta-kun without a pilot, conversion parts, fundraising, the Unit Stats
ability indicator and Herald references. Please also check the carried
D-Command, palace caption, Target Lock and narration fixes. Include the build
number and screenshots in reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary and revised with playtest
feedback. This update follows the requested Herald terminology and fits existing
English without changing item effects or the current ordinary letter shapes.
Chaos Caper follows the user's spelling.

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
