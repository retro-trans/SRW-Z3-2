# Super Robot Taisen Z3: Tengoku-hen — translation project

Development repository for the PS3 English translation of **Dai-3-Ji
Super Robot Taisen Z: Tengoku-hen** (BLJS10299).

The repository follows the source-only approach of
[SRW-Z3](https://github.com/retro-trans/SRW-Z3), retaining this project's existing
folder layout. It contains translations, glossary research, ROM-hacking tools
and validation evidence. Supply your own game dump; disc images, extracted
game files and Japanese script dumps remain local.

## Current status

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

The [0.5.2 playtest release](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.2)
uses an original-to-English ISO xdelta patch. Download it, then use Retro
Trans's **Apply xdelta** mode. See
[0.5.2 installation and compatibility notes](docs/RELEASE_0.5.2.md). This
playtest prerelease is outside the public Automatic catalog.
