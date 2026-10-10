"""Preview release configuration/notes for verified 0.5.2; --apply saves them."""
import argparse
import json
import subprocess
from pathlib import Path
from tools.common import ROOT, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    p.add_argument('--source-commit', required=True)
    args = p.parse_args()
    version = '0.5.2'
    patch = 'SRW-Z3-2-PS3-English-0.5.2-from-original.xdelta'
    build_dir = ROOT / 'work/output/builds' / version
    iso = ROOT / 'work/output/iso/0.5.2/Tengoku-hen-English-0.5.2.iso'
    build = json.loads((build_dir / 'build.json').read_text(encoding='utf-8'))
    image = json.loads(iso.with_suffix('.json').read_text(encoding='utf-8'))
    settings = json.loads((ROOT / 'config/tengoku.json').read_text(encoding='utf-8'))
    assert build['version'] == image['version'] == version
    assert build['dialogue_records'] == 63553 and image['files_verified_each_tree'] == 82
    assert image['bytes'] == iso.stat().st_size
    assert subprocess.check_output(['git', 'rev-parse', args.source_commit + '^{commit}'], cwd=str(ROOT), text=True).strip() == args.source_commit
    tool = ROOT / 'work/output/release-tools-v0.5.4'
    tool_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(tool), text=True).strip()
    config = dict(game_id='srw-z3-tengoku-ps3',
                  game_name='Super Robot Taisen Z3: Tengoku-hen (PS3)', platform='PS3',
                  version=version, source_commit=args.source_commit,
                  patches=[dict(patch=patch, edition='jp-bljs10299', language='en', source_version='original',
                                source_format='iso', target_format='iso', source=settings['iso'], target=str(iso))])
    notes = f'''# 0.5.2 — Fresh English dialogue retranslation (RPCS3 playtest)

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. This is the first release in the SRW-Z3-2 repository.

## Apply

Download the release assets. In [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools),
use **Apply xdelta**, select your matching original Japanese ISO and
`{patch}`, and choose a new output ISO. This playtest prerelease is not enrolled in
the public Automatic catalog. Retro Trans 0.5.4 was used for release validation.

Alternatively:

```text
xdelta3 -d -s "original-japanese.iso" "{patch}" "Tengoku-hen-English-0.5.2.iso"
```

This patch accepts only the exact original input below. Other versions,
folder dumps, repacked ISOs and Vita packages are not interchangeable. Keep
checksums enabled and preserve your original image.

- Original Japanese ISO: **{Path(settings['iso']).stat().st_size:,} bytes**,
  SHA-256 `{image['source_iso_sha256']}`.
- Patched 0.5.2 ISO: **{image['bytes']:,} bytes**,
  SHA-256 `{image['sha256']}`.

`BUILD-MANIFEST.json` records complete input, output and patch identities.
`SHA256SUMS.txt` verifies downloads; `VALIDATION.json` records the full-image
decode round trip. Only patches and protocol metadata are distributed.

## Included

- Fresh English dialogue: **63,553 records**, including main story, alternate
  routes, endings, ace talks, guidance and previews.
- Five long records use a separate 85% horizontal VWF alphabet. All wording
  and eleven full Sphere names are retained. Font cells, advances and encoded
  text are matched; each rendered speech block fits the three-line budget.
- Existing UI, Spirit, mission-condition, name-table, team-name, artwork and
  encyclopedia translations, plus **{build['battle_voice']['voice_strings']:,} battle-voice strings**.
- Six shared route-choice filenames are merged by ID; the build rejects
  incomplete or duplicate dialogue coverage.

## RPCS3 compatibility and limitations

**RPCS3 only.** This build uses a plain ELF executable; physical PS3 and Vita
support are not claimed. This is a playtest prerelease. Boot, gameplay and
live readability of this exact build remain unverified. Coverage checks do
not prove every screen or wording is final; provisional names and difficult
interpretations remain recorded in the project reports.

Close RPCS3 before updating. Back up your installation and move only the old
`dev_hdd0/game/BLJS10299_DATA` installation-cache folder to a backup outside
`dev_hdd0/game`, allowing the new build to reinstall matching fonts and battle
text. **Preserve savedata and other games.** Fresh-boot the image and load an
in-game save; emulator save states can retain older code/resources.

The paired SRVC and EBOOT pass independent readback. Four voice blocks exceed
the original largest block; runtime block limits and battle-text layout still
need playtesting. Some estimated battle-caption lengths remain flagged.

Build sources: `{args.source_commit}`. Release tool: Retro Trans **0.5.4**,
commit `{tool_commit}`. All 82 disc files are verified through both filesystem
trees; the stage SDAT passes encrypt/decrypt round trip. Report issues with
the build number and a screenshot.
'''
    print(json.dumps(config, indent=2))
    print(notes)
    if not args.apply:
        print('DRY RUN: no files written.')
        return
    local = ROOT / 'work/output/releases/0.5.2/release-local.json'
    document = ROOT / 'docs/RELEASE_0.5.2.md'
    assert not local.exists() and not document.exists()
    write_json(local, config)
    document.write_text(notes, encoding='utf-8')
    write_json(build_dir / 'source_provenance.json', dict(source_commit=args.source_commit,
               release_tool_version='0.5.4', release_tool_commit=tool_commit))


if __name__ == '__main__':
    main()
