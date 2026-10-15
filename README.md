# Super Robot Taisen Z3: Tengoku-hen — translation project

Development repository for the PS3 English translation of **Dai-3-Ji
Super Robot Taisen Z: Tengoku-hen** (BLJS10299).

The repository follows the source-only approach of
[SRW-Z3](https://github.com/retro-trans/SRW-Z3), retaining this project's existing
folder layout. It contains translations, glossary research, ROM-hacking tools
and validation evidence. Supply your own game dump; disc images, extracted
game files and Japanese script dumps remain local.

## Current status

Public testing currently uses [**0.5.44**](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.44). It
includes the accumulated keyword-popup, deployment and news corrections,
plus the phase/map-panel fixes and [latest reward/menu corrections](docs/REWARD_MENUS_0.5.44.md).
Retro Trans supports automatic updates from the original Japanese ISO or the
exact English 0.5.40 image. Refresh its catalog to select the latest release.

Fresh dialogue drafts cover **63,553 records in 857 slices across 12 batches**,
including alternate routes, endings, ace talks and previews.
See [the completion report](docs/FRESH_RETRANSLATION_COMPLETION.md).

Fresh drafts live in `work/translation/en/retranslation_*/drafts/` and were
promoted to `work/translation/en/dialogue/` for **0.5.2**. Five long records,
including the full eleven-Sphere list, use a condensed alphabet. The complete
wording is preserved. The new build still needs in-game playtesting. Recorded
validation is evidence from the local source workspace, not a promise that
source-dependent checks run in a fresh clone.

UI, library and voice work have separate coverage notes in [HANDOFF.md](HANDOFF.md).
The [current UI gap audit](docs/UI_COVERAGE_2026-10-10.md) compares the released
build with Jigoku and identifies substantial untranslated menu/help paths.
The [0.5.3 UI expansion](docs/UI_EXPANSION_0.5.3.md) supplies reviewed
translations across the complete 2,499-ID expansion catalogue and a local
testing build. Live layouts and 23 generated-message bindings remain pending.
The [0.5.4 startup fixes](docs/STARTUP_UI_0.5.4.md) address the five reported
screenshots: explanation wrapping, selected No alignment, naming overlap,
opening narration and the default MC name inside dialogue.
The [0.5.5 font build](docs/FONT_0.5.5.md) matches SRW Z3's Rodin Bold
letter raster and spacing, with recalculated wrapping.
The [0.5.6 link/menu fixes](docs/LINK_LAYOUT_0.5.6.md) address speaker-name,
dialogue and backlog link geometry, prologue headings, the SR Point explanation
and command-caption centering.
The [0.5.7 menu layouts](docs/MENU_LAYOUT_0.5.7.md) center the remaining map,
Spirit and save captions, shorten crowded tabs and fix the Tactical Situation
heading and team counter.
The [0.5.8 status layouts](docs/STATUS_LAYOUT_0.5.8.md) translate the new-save
question and movement types, compact terrain/stat labels, separate pilot
full names and fit the Mech/Weapon Stats captions into their native fields.
The [0.5.9 battle layouts](docs/BATTLE_LAYOUT_0.5.9.md) fit battle-preview,
map-popup and transformation labels, restore compact Spirit indicators,
translate Debris Field, remove the result Score suffix and fit Fast beside Cancel.
The [0.5.10 title screen](docs/TITLE_SCREEN_0.5.10.md) adds the English logo,
Heavenly Prison Chapter subtitle, retro-trans credit and matching build version.
The [0.5.11 intermission and Library fixes](docs/INTERMISSION_LIBRARY_0.5.11.md)
shorten and align intermission menus, connect every linked glossary description
to English, remove Library caption quotes and translate the scenario chart.
The [0.5.12 date, briefing and level-up checks](docs/BRIEFING_LEVELUP_0.5.12.md)
verify the centered date drawer, translate the three military-report lines,
compact the reversed DEF/SKL pair and remove the shared Score suffix.
The [0.5.13 enemy-fleet narration](docs/FLEET_NARRATION_0.5.13.md) translates
the two missing descent-to-Earth captions with their original row timing.
The [0.5.14 Focus and font changes](docs/FOCUS_STYLE_0.5.14.md) use Focus/Foc
for the Ki stat and restore the native outline masks used by Lv/SP labels.
The historical **0.5.18** build fixes the enemy Spirit band's slash separator and
includes the accumulated UI fixes in a new public release. The user tests
public releases, so separate local testing builds are insufficient delivery.
The [0.5.17 category and stat fixes](docs/CATEGORY_UI_0.5.17.md) connect
ordinary stage headings, all 83 map terrain names and assembled Spirit targets,
and improve stat/training label spacing. The [0.5.16 narration pass](docs/NARRATION_0.5.16.md) connects all 197
full-screen narration records, including 154 missing unique translations and
later story introductions. It retains the [0.5.15 UI fixes](docs/UI_REVIEW_0.5.15.md), which repair stray kanji in
native captions, enlarge level-up labels, align intermission and settings text,
and translate the concluding narration.
Repository creation does not publish a game patch. The user handles emulator
navigation.

## Layout

| Path | Contents |
| --- | --- |
| `work/glossary/` | Terminology, character profiles and research |
| `work/ui/` | UI dimensions, bindings, layout metadata and audits |
| `work/translation/en/` | UI, library and dialogue translations, batch drafts and reviews |
| `work/translation/en/voice_text/` | English-only voice exports with source fingerprints |
| `tools/`, `tests/` | Extraction, patching, translation checks and regression tests |
| `docs/` | Build notes, translation style, setup and completion reports |
| `config/` | Portable example; personal configuration is ignored |
| `work/output/`, `work/tengoku/`, `incoming/` | Local-only builds, game data and incoming files |

## Getting started

Read [AGENTS.md](AGENTS.md), [BASE_RULES.md](BASE_RULES.md) and
[HANDOFF.md](HANDOFF.md). See [local source setup](docs/LOCAL_SOURCE_DATA.md)
for dependencies and fresh-clone limits. Core tools use Python 3.8+; texture
tools also need NumPy and Pillow.

Copy `config/tengoku.example.json` to ignored `config/local.json`, supply your
paths, and inspect before extracting:

```powershell
python -m tools.pipeline --config config/local.json inspect
python -m tools.pipeline --config config/local.json extract
```

Mutating project commands generally preview changes first; inspect output
before adding `--apply`. See [the pipeline guide](docs/PIPELINE.md) and
[ISO build notes](docs/BUILD_ISO.md) for the separate build process.

## Releases

Every new release must work with
[Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).
See [release preparation](docs/RETRO_TRANS_RELEASES.md). Versions use `0.x.y`;
repository administration does not assign a build version.

[Public release 0.5.28](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.28)
includes an original-to-English ISO patch and a direct upgrade from public
**0.5.18**. Both patches passed complete ISO round trips and hosted checksum
verification. In Retro Trans, click **Refresh catalog**,
select the matching original Japanese or public 0.5.18 ISO, and choose **Latest**.
Manual **Apply xdelta** is also available. This is a playtest release; in-game
testing remains pending.
