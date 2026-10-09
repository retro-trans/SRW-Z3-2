# Local source data and a fresh clone

Git tracks authored translations, tools, glossary research and review evidence.
Game images, executables, extracted archives, raw texture sheets, fonts and
extensive Japanese scripts remain local. Short glossary names, UI labels and
required `$$Japanese$$` tokens remain tracked.

The original local files are preserved. These paths are ignored:

- `work/tengoku/`, `work/output/`, temporary work folders and `incoming/`.
- `work/ui/reference/`, imported glossary references and texture PNGs.
- `work/translation/en/voice/` and `voice_new/`, which mix translations with
  original Japanese speech.
- `config/tengoku.json` and `config/local.json`, which contain machine paths.

## Voice translations

`work/translation/en/voice_text/{voice,voice_new}/` preserves the voice worksets,
IDs, English, speaker metadata and review decisions. Each `jp` field is replaced
with `repository_source_sha256`, a SHA-256 of the original UTF-8 string.
Overlapping worksets remain separate; their row counts are not unique coverage
counts. These are review/backup exports, not build inputs.

Export with `python -m tools.voice_repository`; inspect the preview, then add
`--apply`. Existing differing exports are refused. Originals are never modified.
Restore your own matching local inputs before running the existing voice
checker or builder; they still require exact Japanese source. Do not bypass
those checks. There is no automatic import of edited exports yet.

## Setup and validation

Core tools require Python 3.8+. Texture tools require NumPy, Pillow and locally
available game fonts. The SDAT utility is an external prerequisite. Copy
`config/tengoku.example.json` to ignored `config/local.json`, set your paths,
and pass `--config config/local.json` to `tools.pipeline`.

See [PIPELINE.md](PIPELINE.md) for extraction and preparation. These steps are
not a complete tested reconstruction of every historical inventory, brief,
font or reference dependency. Some specialized tools retain paths from the
original Windows workspace. Restore matching local backups or adapt paths
before source-dependent checks/builds. Missing inputs do not mean validation
passed.

GitHub smoke checks use synthetic data and require no game files. Full dialogue
and voice checks run locally. Completed retranslation drafts remain isolated
from the old active build inputs.
