# Glossary reference imported from Jigoku-hen

Imported 2026-09-11 at the user's request.

Use `reference/jigoku_glossary.json` (under `work/glossary/`) for established Japanese/English names,
series identity, aliases, source references and ambiguity notes. It is an
unchanged snapshot of `E:/Projects/SRW Z3/analysis/glossary.json`.

## Contents

- 1,141 entries: 34 series, 141 keywords, 709 pilot-name entries and 257
  robot-name entries. Entries are not necessarily distinct characters: full
  names, display names and aliases can have separate records.
- 1,072 entries marked official, 53 proposed and 16 ambiguous in the source.
  These are inherited statuses, not a new research/verification result.
- Every entry retains its English, Japanese, kind, series/source, original
  record identity, field, status and notes; optional aliases and source links
  are preserved. 1,017 entries have a `src` field.
- `reference/sources/akurasu_z3_mechs.txt` and
  `reference/sources/akurasu_z3_pilots.txt` preserve the two existing source
  reference files. They were not refreshed or researched anew during transfer.

## Identity warning: reference, not target configuration

The glossary describes **Jigoku-hen (BLJS10256)**. Its `zukan_id`, numeric
token discriminators, field/record bindings and any voice identifiers are
legacy evidence, NOT Tengoku-hen (BLJS10299) addresses or IDs. Do not pass
this reference directly to a Tengoku builder, name patcher or library writer.

`glossary.json` (this folder) now contains a **partial target authoring glossary**:
42 Spirit command terms, each bound to a reviewed name field in Tengoku's own
RPW table. Its `#spirit` tokens are checked by `tools/ui_spirits.py`; binary
integration remains unverified. It contains no character, stage or voice
identities. See `docs/UI_SPIRITS.md` for scope, provenance and validation.

The 1,883 automatically generated library candidates under `work/` remain
unreviewed and are not part of that active glossary. Expand the database from
Tengoku's own encyclopedia/tables, matching Japanese, kind, series and context.
Preserve provenance and resolve ambiguity before assigning target bindings or
tokens. Never rename this legacy reference to `glossary.json` or clear its IDs
and assume its identities have been resolved for Tengoku.

For prose planning, reuse a spelling when the entity genuinely matches.
Do not interpret an exact Japanese match as universal identity. Pilot versus
robot, Rei versus Ray, and common words such as Boss, Lady and Zero require
the context checks in `docs/Z3_LESSONS.md` (at the project root).

No Tengoku-only entries have been researched or added by this import, and
not every inherited term is necessarily present in Tengoku. Do not silently
rename inherited terms or drop their ambiguous/proposed status.

The SHA-256 transfer manifest is `reference/import_manifest.json`. The source
project remains untouched, and later changes there will not automatically
update this snapshot; reconcile future changes deliberately.
