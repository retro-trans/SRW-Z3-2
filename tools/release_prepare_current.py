"""Preview a verified current release, with original and public upgrade patches."""
import argparse
import json
import subprocess
from pathlib import Path
from tools.common import ROOT, write_json


def main():
    from tools.game_build import VERSION
    if VERSION=='0.5.43':
        from tools.release_prepare43 import main as prepare_map_fixes
        return prepare_map_fixes()
    if VERSION=='0.5.42':
        from tools.release_prepare42 import main as prepare_deployment
        return prepare_deployment()
    if VERSION=='0.5.41':
        from tools.release_prepare41 import main as prepare_popups
        return prepare_popups()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--version', default=VERSION)
    p.add_argument('--upgrade-from', default='0.5.28' if VERSION in ('0.5.29','0.5.30','0.5.31','0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40') else '0.5.18')
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
    if version=='0.5.28':evidence_prefix='review28_verified_'
    if version=='0.5.29':evidence_prefix='review29_verified_'
    if version=='0.5.30':evidence_prefix='review30_verified_'
    if version=='0.5.31':evidence_prefix='review31_verified_'
    if version=='0.5.32':evidence_prefix='review32_verified_'
    if version=='0.5.33':evidence_prefix='review33_verified_'
    if version=='0.5.34':evidence_prefix='review34_verified_'
    if version=='0.5.35':evidence_prefix='review35_verified_'
    if version=='0.5.36':evidence_prefix='review36_verified_'
    if version=='0.5.37':evidence_prefix='review37_verified_'
    if version=='0.5.38':evidence_prefix='review38_verified_'
    if version=='0.5.39':evidence_prefix='review39_verified_'
    if version=='0.5.40':evidence_prefix='review40_verified_'
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
    if version=='0.5.28':label='Complete map defeat quotes'
    if version=='0.5.29':label='Break / Fury, Inazuma Kick and numbered mission conditions'
    if version=='0.5.30':label='Skill questions, D-Trader and battleship layout, Spirit and mission fixes'
    if version=='0.5.31':label='Complete SR conditions, skill questions and UI repairs'
    if version=='0.5.32':label='Centered captions, two-line news, Sub Order and save questions'
    if version=='0.5.33':label='Reward report lines, Arm Rakers and Back Log guides'
    if version=='0.5.34':label='English startup warning and copyright credits, with UI repairs'
    if version=='0.5.35':label='Translated combined war-front updates, with startup and UI repairs'
    if version=='0.5.36':label='Large Funds spacing, two-line news and carried UI repairs'
    if version=='0.5.37':label='Complete Back Log text, large Funds spacing and UI repairs'
    if version=='0.5.38':label='Separate plain lettering and original outlined yellow labels'
    if version=='0.5.39':label='Consistent Allies / Enemies selector and separate font styles'
    if version=='0.5.40':label='Stable Search tabs, consistent side selector and separate font styles'
    upgrade_notes='''- Translate all 23 assembled item-unlock conditions, all 24 D-Trader item
  announcements, and all nine selectable Full Upgrade Bonus confirmations.
- Repair both two-color Custom Bonus award headers and the matching Ace Bonus
  header, keeping their native font, colors, icons and row pitch.
- Translate all 35 trophy names/descriptions and the trophy-set title in both
  metadata variants. Preserve IDs, hidden flags, grades, triggers and all icons.
''' if version in ('0.5.20','0.5.21','0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27','0.5.28') else ''
    if version in ('0.5.21','0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27','0.5.28'):
        upgrade_notes+='''- Correct Heero Yuy and Crowe Bluest in the glossary, Library, executable
  names, dialogue token expansions and pilot surname pieces; preserve Yui Ikari.
- Center Raise Stats / Learn Skills in all four training tab states; separate
  Owned / Cost / Left from PP and restore readable six-stat / four-terrain labels.
- Fit all nine Z Crystal effect names, including Grade 5, before the unchanged
  numeric cost column; shorten its headings to Effect / Cost.
'''
    if version in ('0.5.22','0.5.23','0.5.24','0.5.25','0.5.26','0.5.27','0.5.28'):
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
    if version in ('0.5.23','0.5.24','0.5.25','0.5.26','0.5.27','0.5.28'):
        upgrade_notes+='''- Relocate all 262 static mission conditions through ten-byte display keys,
  keeping complete English beyond the native UI's 128-byte intermediate field.
  Preserve the existing substitution route for all 25 live-name/counter conditions.
- Correct Sacks and Giltar throughout active name fields, Library and glossary
  expansions. Preserve the other user-selected canonical spellings.
- Fit deployment headers around the remaining count; translate all seven
  repeated movement templates and compact selection/movement captions.
'''
    if version in ('0.5.24','0.5.25','0.5.26','0.5.27','0.5.28'):
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
''' if version in ('0.5.23','0.5.24','0.5.25','0.5.26','0.5.27','0.5.28') else ''
    if version in ('0.5.24','0.5.25','0.5.26','0.5.27','0.5.28'):
        review23_verification+='''Twenty native Clear Report executions cover zero, ordinary and large
amounts, with row canaries and unchanged values. Eleven label edits and all
deployment command lookup variants pass final readback and measured bounds.
'''
    if version in ('0.5.25','0.5.26','0.5.27','0.5.28'):
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
    if version in ('0.5.26','0.5.27','0.5.28'):
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
    if version in ('0.5.27','0.5.28'):
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
    if version=='0.5.28':
        upgrade_notes+='''- Translate all 249 native map defeat-quote entries (178 distinct strings),
  including Nigel's quote and nonverbal entries. Preserve pilot selection and modes.
- Review all 176 verbal barks with speaker context; apply 21 meaning fixes and
  preserve retreats, bailout commands and interrupted sentences.
'''
        review23_verification+='''All 249 native quote-state stores and all 249 RPW quote cells pass final
execution/readback checks. The real selector preserves pilot codes, its alias,
unknown-code behavior and sentinel. Every quote fits its native composition
buffer and speech panel. Original quote strings and consumer code are retained.
'''
    baseline_changes='''- Shorter Link question and PP bonus labels, preserving counts and totals.
- Default protagonist names translated in the independent mission-condition
  substitution routine; custom names, name order and saved bytes preserved.
- Compact Library Name caption, aligned SR Point award layers and a single
  highlighted bonus amount with its separate English prefix.
- English world-map domination caption; percentage digits and animation retained.
''' if a.upgrade_from=='0.5.18' else ''
    if version in ('0.5.29','0.5.30','0.5.31','0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes='''- Correct the two Spirit names to the requested Z3 convention: Break ignores
  defensive abilities; Fury guarantees critical hits. Update their compact
  indicators, bonus descriptions and related trophy text.
- Use Inazuma Kick in weapon names, glossary references and battle captions.
- Fix victory and defeat conditions showing internal keys such as 条件１７１.
  Cover all 262 static conditions in all three numbered slots and the
  unnumbered state, across every chapter. Preserve colors and gameplay logic.
- Fit numbered condition text with room for the number and continuation indent.
- Prevent live-name/counter condition truncation with native byte limits and
  room for expanded values. Keep every requirement in the shortened long SR
  condition, including each named pilot's individual shootdown quota.
'''
        review23_verification='''All 1,048 native condition compositions pass the real drawer lookup after
numbering, with row canaries intact. Another 200 cases execute live substitution
then numbering with default and maximum-size values. All 129 Spirit fields, every full/list
Inazuma Kick weapon occurrence and its battle captions pass final readback.
The earlier death-quote, mission, name and UI repairs remain covered by the
carried checks. No in-game visual verification is claimed.
'''
    if version in ('0.5.30','0.5.31','0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Translate the full skill-confirmation category: learning, level increases
  and overwriting an existing skill. Cover every skill name, not only E-Save.
- Translate every movement terrain combination, including numbered masks.
  Separate D-Trader's Move label from its live movement value.
- Fit D-Trader's part-stat labels, terrain heading and owned-item suffix around
  their fixed value fields, keeping the game's original label font.
- Normalize Earth Sphere capitalization throughout dialogue and encyclopedia text.
- Separate battleship selection, ship name, movement, pilot and remaining-unit
  headings from their neighboring columns and live count.
'''
        review23_verification+='''Every new skill/movement draw key passes final lookup; the native learning
composer is exercised for every skill and both source/translated name routes.
All nine changed widgets pass final text/coordinate readback and column bounds.
The four corrected dialogue rows and twelve encyclopedia fields pass archive readback.
'''
    if version in ('0.5.31','0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Restore the complete Episode 20 and 21 SR conditions: no allied battleship
  damage within three turns; one allied pilot shoots down at least six enemies
  before clearing the map. Use separate native rows for every displayed line.
- Fit six additional SR explanations into the actual four-row slot. Keep all
  targets, turn limits, shootdown quotas, attack exceptions and ELS exclusions.
'''
        review23_verification+='''All 101 distinct SR conditions pass 210 executions of the complete native
four-row panel, with both color states and default/maximum live values. The
reported phases and all compiled SR literals pass final archive/drawer readback.
All six former row overruns are reproduced by the regression test and repaired.
'''
    if version in ('0.5.32','0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Center all 517 location captions by their displayed English width, including
  Jindai High School / Old Building / Empty Classroom and Back Log views.
- Fit all eleven long or combined news headlines into two centered lines;
  preserve the complete Wrath Babylon assault-failure wording.
- Separate Sub Order labels from all three pilot counters and remove duplicate
  pilot-word fragments. Fit its guides and both Back Log guide variants around
  the controller icons. Clear Team Setup's movement brackets with MV labels.
- Translate all three native save questions before paragraph copying, including
  Save complete / Continue playing. Preserve save operations and Yes / No.
'''
        review23_verification+='''539 executions verify the caption/news origin helper, full text, font widths
and caller state. All changed guides pass final archive/bounds checks. Native
save paragraph copying and both converter models preserve every English line.
The complete movement-mask translations remain covered by the carried checks.
'''
    if version in ('0.5.33','0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Translate every separately drawn reward-report line, including all AG
  bonus amounts, awards, upgrade refunds and unlock notices. Center the English
  lines without changing rewards or stage logic.
- Correct Arm Rakers capitalization against the glossary. Clear Previous Quote
  and its R1 icon in both Back Log guide variants.
'''
        review23_verification+='''All 22 player-facing reports (97 source occurrences) pass native paragraph
copying and final translation lookup; all 36 whole/line keys pass native centering.
The corrected Arm Rakers dialogue passes compiled archive readback.
'''
    if version in ('0.5.34','0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Translate the full startup warning and all 20 Japanese copyright credit
  rows across both pages. Preserve every rights holder, year and production
  relationship, the existing English credits, logo screens and warning frame.
'''
    if version=='0.5.34':
        review23_verification+='''All three startup screens pass final texture/pixel readback and bounds checks.
Unchanged game files and every other texture/archive member match the verified
0.5.33 data byte for byte. Independently decrypt the rebuilt stage wrapper and
confirm identical script content. Only startup art and the title stamp change.
'''
    if version in ('0.5.35','0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Translate combined war-front updates after the game splits them into
  independently drawn lines: all 13 rows across six messages, including the
  East Asia / eastern North America and Midway / southern Europe updates.
  Center each English row and retain the final three-line worldwide report,
  all route occurrences and the captured-base counts.
'''
        review23_verification+='''All 22 war-front messages pass actual native 128-byte paragraph copying and
final translation lookup. All 13 previously missed rows pass native centering
at both tested font sizes (26 origin cases). All three English startup screens
from verified 0.5.34 are retained.
'''
    if version in ('0.5.36','0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Separate Funds from the full eight-digit amount in all three intermission
  footer layouts. Preserve letter spacing, colors, the numeric field and the
  99,999,999 cap. Retain the centered two-line Central Asia disruption update.
'''
    if version=='0.5.36':
        review23_verification+='''The three Funds x coordinates pass canonical UI readback and byte isolation.
Twelve native cap/digit/alignment cases cover zero, every digit boundary,
the reported amount, the maximum and oversized inputs. The reported Central
Asia headline passes final lookup and both centering sizes. The executable,
fonts, stage wrapper and all other game files are byte-identical to verified
0.5.35; its full regression/native evidence is carried by matching hashes.
'''
    if version in ('0.5.37','0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Fix Back Log corruption when a complete translated entry exceeds its
  native byte buffer. Preserve the full dialogue, including Leonard's reported
  line, and enlarge the separate row buffer for longer English lines.
'''
        review23_verification+='''All 63,553 dialogue entries fit the expanded backlog budgets. Both native
constructors, all 204 formerly over-budget entries, 370 ring shifts, link IDs,
duplicate suppression and resets pass instruction-level checks. All 125 longer
backlog rows and boundary cases pass complete native row copying with stack
canaries and caller restoration. The original split font cell is reproduced.
The backlog fix changes 114 guarded instruction constants relative to 0.5.36.
All other executable bytes and all stage dialogue retain their prior fixes.
In-game confirmation remains pending.
'''
    if version in ('0.5.38','0.5.39','0.5.40'):
        upgrade_notes+='''- Remove the added border from dialogue, narration, names and ordinary
  translated text, preserving the current letter shapes and spacing.
- Keep selected yellow labels in a separate alphabet copied from the game's
  original font, with its thinner native border. Apply that style to Team,
  Mech and Kills across the unit-list pages; preserve original PP / Next-Lv.
'''
        review23_verification+='''Both font pages retain all 301 glyph fills and advances: 260 ordinary cells
have no added border, while 41 native-label cells retain their exact original
fill and border masks. All 19 selected unit-list headers use the separate
alphabet. The font-style changes retain widget geometry, colors and state;
all other widget strings remain identical. Original PP / Next-Lv glyphs,
all unrelated texture members, executable and stage files retain the verified
0.5.37 content. The comparison preview uses actual font masks; emulator visual
confirmation remains pending.
'''
    if version in ('0.5.39','0.5.40'):
        upgrade_notes+='''- Display Allies / Enemies consistently in both map-menu selection states.
  Use the same plural wording, separator, size and positions, with the native
  blue/red colors and selection behavior.
'''
        review23_verification+='''The four selector widgets pass compiled text/style readback and isolation
across all 4,803 widgets. Both choices display the same complete label with
one separator, at 26px and a measured 204.75px width in the 220px button.
The selector-specific changes are limited to four widgets. Fonts, executable,
dialogue and unrelated archive members retain their verified fixes.
'''
    if version=='0.5.40':
        upgrade_notes+='''- Keep Spirit and Skills centered when changing Search tabs by storing
  English in both states before native positioning, like the working Abilities
  tab. Preserve native highlighting, colors and geometry; leave Abilities alone.
'''
        review23_verification+='''All four Search tab widgets contain English before native text measurement.
Both Abilities states and every geometry/style byte across all 4,803 widgets
remain identical to 0.5.39; all other widget text remains identical as well.
The Search fix changes only four text pointers/strings and the version stamp.
Fonts, executable and stage dialogue remain byte-identical to the certified
parent. Twelve instruction-level caption cases reach the real glyph drawer
and preserve the expected centers, text, Y coordinates and caller registers
for both tab states plus the Abilities control. In-game visual confirmation
remains pending.
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

## What changed since last version

Compared with public **{a.upgrade_from}**, the previous public release:

{upgrade_notes}
{baseline_changes}

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
