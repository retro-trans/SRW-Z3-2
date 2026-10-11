"""Preview a verified current release, with original and public upgrade patches."""
import argparse
import json
import subprocess
from pathlib import Path
from tools.common import ROOT, write_json


def main():
    from tools.game_build import VERSION
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--version', default=VERSION)
    p.add_argument('--upgrade-from', default='0.5.2')
    p.add_argument('--apply', action='store_true')
    a = p.parse_args(); version = a.version
    if version != VERSION:raise ValueError('Only the current verified build can be released')
    folder = ROOT/'work/output/builds'/version
    iso = ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.iso')
    build = json.loads((folder/'build.json').read_text(encoding='utf8'))
    image = json.loads(iso.with_suffix('.json').read_text(encoding='utf8'))
    evidence = json.loads((ROOT/'work/ui'/('enemy_ui_verified_'+version+'.json')).read_text(encoding='utf8'))
    settings = json.loads((ROOT/'config/tengoku.json').read_text(encoding='utf8'))
    if build['version'] != version or image['version'] != version or evidence['version'] != version:
        raise ValueError('Mixed release versions')
    if image != evidence['iso_verification'] or image['bytes'] != iso.stat().st_size:
        raise ValueError('Release image differs from final verification')
    if build['dialogue_records'] != 63553 or image['files_verified_each_tree'] != 82:
        raise ValueError('Incomplete release coverage')
    actual = subprocess.check_output(['git','rev-parse',a.source_commit+'^{commit}'],cwd=ROOT,text=True).strip()
    if actual != a.source_commit:raise ValueError('Release sources need a full commit')
    def patch(source,source_version):
        return dict(patch='SRW-Z3-2-PS3-English-'+version+'-from-'+source_version+'.xdelta',
                    edition='jp-bljs10299',language='en',source_version=source_version,
                    source_format='iso',target_format='iso',source=str(source),target=str(iso))
    patches = [patch(Path(settings['iso']),'original')]
    old = ROOT/'work/output/iso'/a.upgrade_from/('Tengoku-hen-English-'+a.upgrade_from+'.iso')
    old_manifest = json.loads(old.with_suffix('.json').read_text(encoding='utf8'))
    if old_manifest['version'] != a.upgrade_from or old_manifest['bytes'] != old.stat().st_size:
        raise ValueError('Public upgrade source differs')
    patches.append(patch(old,a.upgrade_from))
    tool = ROOT/'work/output/release-tools-v0.5.4'
    tool_commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=tool,text=True).strip()
    cfg = dict(game_id='srw-z3-tengoku-ps3',game_name='Super Robot Taisen Z3: Tengoku-hen (PS3)',
               platform='PS3',version=version,source_commit=a.source_commit,patches=patches)
    notes = f'''# {version} — Accumulated UI and translation fixes (RPCS3 playtest)

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. This public release includes the fixes previously supplied as
local builds 0.5.3–0.5.17 and the enemy Spirit band separator repair.

## Apply

In [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
**Refresh catalog**, select either your original Japanese ISO or the exact
public {a.upgrade_from} ISO in **Automatic**, then select **Latest** ({version}).
Choose a new output ISO. Both routes produce the same verified image.

For manual patching, use **Apply xdelta** with the asset whose `from` version
matches your input. `BUILD-MANIFEST.json` records each exact input/output hash
and size; keep checksum checks enabled. Game images are not distributed.

- Original Japanese ISO: {Path(settings['iso']).stat().st_size:,} bytes;
  SHA-256 `{image['source_iso_sha256']}`.
- Public {a.upgrade_from} ISO: {old_manifest['bytes']:,} bytes;
  SHA-256 `{old_manifest['sha256']}`.
- Patched {version} ISO: {image['bytes']:,} bytes;
  SHA-256 `{image['sha256']}`.

## Included

- English UI, menu/help wrapping and alignment, full Library descriptions,
  scenario chart, English title logo, retro-trans credit and version footer.
- All 197 narration records, 104 ordinary stage title variants, 83 terrain
  names, assembled Spirit targets and default-name mission conditions.
- Focus/Foc terminology, native outlined fonts, readable stat/training labels,
  compact Spirit indicators, and the enemy band's English slash between Fy and Di.
- Native caption fallback repair for stray kanji over names/blank labels.
- All 63,553 fresh dialogue records and {build['battle_voice']['voice_strings']:,}
  battle-voice strings retained from the previous public release.

## Verification and compatibility

All 82 disc files passed both filesystem-tree checks. The final executable's
translation bindings, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. Each patch receives a complete ISO decode
round trip and Retro Trans 0.5.4 release validation before publication.

**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. Provisional wording and
battle-caption limitations remain recorded in the project reports.

Fresh-boot the new image and load an in-game save; emulator save states can
retain older code. Follow the prior release's installation-cache update notes
if RPCS3 continues to load old installed fonts/text. Preserve savedata.

Build sources: `{a.source_commit}`. Release tool: Retro Trans **0.5.4**,
commit `{tool_commit}`. See CHANGELOG.md for individual fixes.
'''
    print(json.dumps(cfg,indent=2));print(notes)
    if not a.apply:print('DRY RUN: no release files written.');return
    dest = ROOT/'work/output/releases'/version/'release-local.json'
    doc = ROOT/'docs'/('RELEASE_'+version+'.md')
    if dest.exists() or doc.exists():raise ValueError('Release preparation already exists')
    write_json(dest,cfg);doc.write_text(notes,encoding='utf8')
    write_json(folder/'source_provenance.json',dict(source_commit=a.source_commit,
               release_tool_version='0.5.4',release_tool_commit=tool_commit))


if __name__ == '__main__':main()
