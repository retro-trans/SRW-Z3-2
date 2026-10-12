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
    p.add_argument('--upgrade-from', default='0.5.18')
    p.add_argument('--apply', action='store_true')
    a = p.parse_args(); version = a.version
    if version != VERSION:raise ValueError('Only the current verified build can be released')
    folder = ROOT/'work/output/builds'/version
    iso = ROOT/'work/output/iso'/version/('Tengoku-hen-English-'+version+'.iso')
    build = json.loads((folder/'build.json').read_text(encoding='utf8'))
    image = json.loads(iso.with_suffix('.json').read_text(encoding='utf8'))
    evidence_prefix=('review25_verified_' if version=='0.5.25' else 'review24_verified_' if version=='0.5.24' else 'review23_verified_' if version=='0.5.23' else 'review22_verified_' if version=='0.5.22' else 'review21_verified_' if version=='0.5.21' else 'upgrade_ui_verified_' if version=='0.5.20' else
                     'review19_verified_' if version=='0.5.19' else 'enemy_ui_verified_')
    if version=='0.5.26':evidence_prefix='review26_verified_'
    if version=='0.5.27':evidence_prefix='review27_verified_'
    evidence = json.loads((ROOT/'work/ui'/(evidence_prefix+version+'.json')).read_text(encoding='utf8'))
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
    label='Room caption spacing, Ameria, Team Setup and dialogue font' if version=='0.5.25' else 'Clear Reports, weapon upgrade and deployment menu layout' if version=='0.5.24' else 'Complete mission conditions, deployment and canonical names' if version=='0.5.23' else 'Native label fonts, tutorial and parts layout' if version=='0.5.22' else 'Canonical names, training and Z Crystal layout' if version=='0.5.21' else 'Upgrade reports, bonus prompts and trophies' if version=='0.5.20' else 'Link, protagonist name and reward UI fixes'
    if version=='0.5.26':label='Stage reports, skill levels, name spacing and weapon consistency'
    if version=='0.5.27':label='Emperor Zuul, full-width team-name wrapping and map save prompts'
    upgrade_notes='''- Translate all 23 assembled item-unlock conditions, all 24 D-Trader item
  announcements, and all nine selectable Full Upgrade Bonus confirmations.
- Repair both two-color Custom Bonus award headers and the matching Ace Bonus
  header, keeping their native font, colors, icons and row pitch.
- Translate all 35 trophy names/descriptions and the trophy-set title in both
  metadata variants. Preserve IDs, hidden flags, grades, triggers and all icons.
''' if version in ('0.5.20','0.5.21','0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27') else ''
    if version in ('0.5.21','0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27'):
        upgrade_notes+='''- Correct Heero Yuy and Crowe Bluest in the glossary, Library, executable
  names, dialogue token expansions and pilot surname pieces; preserve Yui Ikari.
- Center Raise Stats / Learn Skills in all four training tab states; separate
  Owned / Cost / Left from PP and restore readable six-stat / four-terrain labels.
- Fit all nine Z Crystal effect names, including Grade 5, before the unchanged
  numeric cost column; shorten its headings to Effect / Cost.
'''
    if version in ('0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27'):
        upgrade_notes+='''- Separate Z Crystal payment text from the live amount and align selected
  Yes / No words with their neutral row in every confirmation state.
- Fit all 23 tutorial selector titles into their two columns. Keep every
  tutorial body in its original row, with measured English widths and controls.
- Shorten Combat Record and Power Parts captions around unchanged numbers,
  names, arrows and category choices. Match both emblem footer caption paths.
- Use the game's original Latin fill and outline masks for the reported yellow
  labels, retaining their native color, baseline and row pitch.
- Translate the Power Parts formatter's separate Air / Ground / Water table;
  preserve all eight movement masks, separators, and both comparison columns.
'''
    if version in ('0.5.23','0.5.24','0.5.25','0.5.26','0.5.27'):
        upgrade_notes+='''- Relocate all 262 static mission conditions through ten-byte display keys,
  keeping complete English beyond the native UI's 128-byte intermediate field.
  Preserve the existing substitution route for all 25 live-name/counter conditions.
- Correct Sacks and Giltar throughout active name fields, Library and glossary
  expansions. Preserve the other user-selected canonical spellings.
- Fit deployment headers around the remaining count; translate all seven
  repeated movement templates and compact selection/movement captions.
'''
    if version in ('0.5.24','0.5.25','0.5.26','0.5.27'):
        upgrade_notes+='''- Translate assembled Clear Report Z-Chip and funds rows, remove their
  numeric padding, and retain live amounts. Center the three per-pilot PP rows.
- Separate Weapon and RANK in both upgrade list footers and shorten the
  right header. Preserve the upgrade values, bars, native colors and font masks.
- Fit deployment commands inside their buttons; shorten the team-count
  caption and suppress its redundant suffix around the unchanged number.
'''
    review23_verification='''All 262 static mission keys pass the native copier and final drawer lookup
checks; all 110 mission members pass complete archive readback. The 12
deployment edits preserve numeric fields and movement-cell spacing. The
expanded active-text audit confirms Sacks and Giltar without old spellings.
''' if version in ('0.5.23','0.5.24','0.5.25','0.5.26','0.5.27') else ''
    if version in ('0.5.24','0.5.25','0.5.26','0.5.27'):
        review23_verification+='''Twenty native Clear Report executions cover zero, ordinary and large
amounts, with row canaries and unchanged values. Eleven label edits and all
deployment command lookup variants pass final readback and measured bounds.
'''
    if version in ('0.5.25','0.5.26','0.5.27'):
        upgrade_notes+='''- Space and center all seven Gargantia fleet commander's room captions;
  preserve both blank rows and use their final expanded font widths.
- Correct Ameria in the active glossary and location captions, including
  all dialogue tokens that expand to that name.
- Separate both Team Setup headings from Next and its unchanged live count.
- Restore the normal font for Mao's Baal explanation using reviewed complete
  wording that fits three rows and retains its keyword link.
'''
        review23_verification+='''The reported Rescue Unit and Target Lock reports and complete Episode 11
SR condition pass final native lookup. All seven room captions and Mao's
normal-font row pass full stage-member readback and measured text bounds.
Both Team Setup header states preserve font settings and live counter text.
The expanded active-text audit rejects obsolete Amerria spellings.
'''
    if version in ('0.5.26','0.5.27'):
        upgrade_notes+='''- Translate all 22 player-facing stage GIFT reports (97 occurrences), including
  Sub Order and D-Trader unlocks, item grants, AG bonuses and upgrade refunds.
- Translate composed skill levels, including Newtype Lv 2, without changing
  required levels, selection predicates or colors.
- Use an English space in the default Hibiki Kamishiro full name; keep custom
  name strings and savedata unchanged.
- Audit all 686 full weapon names and 606 list names against the sibling
  Jigoku project. Expand fitting abbreviations, including Radiant Wave Surger;
  retain seven width-bound forms and eight reviewed full-name meaning exceptions.
'''
        review23_verification+='''The complete stage-report and composed skill lookup sets pass final execution
checks. All weapon-name pointers and widths pass archive readback. The default
name separator passes instruction tests with custom-name and null guards.
'''
    if version=='0.5.27':
        upgrade_notes+='''- Apply Zuul / Emperor Zuul throughout active names and expanded prose;
  preserve the unrelated Gundam Geara Zulu and Rozen Zulu names.
- Wrap all 800 dialogue records using the runtime team-name token with room
  for the six full-width cells of Z-BLUE. Preserve wording, links and controls.
- Translate all independent lines of the three map save confirmations,
  including Save complete / Continue playing, preserving save and choice behavior.
'''
        review23_verification+='''All runtime team-name dialogue members pass complete final archive readback;
all independent save-line keys pass final lookup execution. The shared Library
Name caption and all Library fields mentioning Zuul pass exact final readback.
The expanded active-text audit rejects obsolete Xul and Zul spellings.
'''
    notes = f'''# {version} — {label}

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. Prepared locally; creating or publishing a GitHub release
requires the user's explicit consent for this version.

## Apply

Once published, in [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
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

{upgrade_notes}
- Shorter Link question and PP bonus labels, preserving counts and totals.
- Default protagonist names translated in the independent mission-condition
  substitution routine; custom names, name order and saved bytes preserved.
- Compact Library Name caption, aligned SR Point award layers and a single
  highlighted bonus amount with its separate English prefix.
- English world-map domination caption; percentage digits and animation retained.
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
translation bindings, mission name substitution stores, reward captions,
domination atlas, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. The upgrade additions also pass 80 final
lookup cases, 23 native report compositions and nine native bonus questions;
the trophy pack passes complete text/structure/icon readback and SHA-1 checks.
Each patch receives a complete ISO decode
round trip and Retro Trans 0.5.4 release validation before publication.
{review23_verification}

**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. The separately reported
malformed result-screen team name remains unresolved. Provisional wording and
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
