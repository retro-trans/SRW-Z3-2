# Local source and archive pipeline

Implemented 2026-09-11. Python 3.8+ and the standard library are sufficient.
The initial run used `C:/Python/python.exe` (3.8.2, 32-bit). No packages were
installed. The offline SDAT utility is an explicit external prerequisite.

## Commands

Run from the project root. Mutating commands default to a dry run; inspect the
planned paths and samples before repeating with `--apply`.

```powershell
python -m tools.pipeline inspect
python -m tools.pipeline extract
python -m tools.pipeline extract --apply
python -m tools.pipeline prepare
python -m tools.pipeline prepare --apply
python -m tools.pipeline verify
python -m tools.pipeline verify --apply
python -m unittest discover -s tests -v
```

`config/tengoku.json` contains the Tengoku ISO path, expected title ID, offline
SDAT utility path and a workspace under `work/`. For another local layout,
create ignored `config/local.json` and pass
`python -m tools.pipeline --config config/local.json <command>`.

The initial extraction/preparation/verification outputs already exist. These
commands deliberately refuse to overwrite their output directories. For a new
experiment, use a fresh configured workspace, or preserve/rename the relevant
generated output directory before regenerating that step. Never treat edited
outputs as pristine source inputs. The tools have no deployment commands.

## Stages and boundaries

| Stage | Implemented behavior | Limit |
| --- | --- | --- |
| Inspect | Joliet-aware file inventory and PARAM.SFO title check | ISO9660/Joliet only; not a UDF writer |
| Extract | Streams every extent, joins logical files, checks output hashes, records ISO fingerprint | Refuses existing output directory |
| Prepare | Offline SDAT decrypt, strict CPK reads, source/literal and library inventories, UI discovery candidates | No semantic identity approval or translation |
| Verify | Rechecks ISO/source hashes, eight byte-identical rebuilds, synthetic DataH growth, separate ITOC metadata reader | Storage acceptance only; no game launch |

`tools/cpk.py` reads ITOC/TOC metadata and CRILAYLA, checking member identities,
bounds and declared sizes. Inputs larger than **64 MiB** are rejected explicitly
to avoid exhausting 32-bit Python. The whole disc was extracted, including its
larger archives, but those larger CPK contents have not been inspected.

The ITOC writer rejects unknown IDs, existing destinations and auxiliary TOCs.
Untouched payloads retain their compressed bytes. Replacements are stored
uncompressed; a row that outgrows 16-bit sizes migrates to DataH. Migration
must fit the original ITOC padding and cannot overwrite nonzero unknown data.
No executable/runtime consumer is assumed to accept a grown archive.

For a reviewed local archive experiment:

```powershell
python -m tools.cpk list work/tengoku/prepared/STGZ3OF2.dec.cpk
python -m tools.cpkpatch input.cpk output.cpk --replace 1=replacement.lua
# Review the member and file above, then append --apply to write a new output.
```

Archive replacement IDs are read from Tengoku metadata. The example `1` is an
illustration of the CLI, not a translated stage, voice bank or identity mapping.
The production source pipeline never reads the reference `.py.txt` repairs.

## Generated evidence

All paths below are relative to `work/tengoku/` and ignored by source control.

| Output | Meaning |
| --- | --- |
| `source_manifest.json` | Source ISO hash, title, logical paths, extents, lengths and extracted SHA-256 values |
| `prepared/stage_index.json` | All 876 member hashes, text classification, literal counts and source-comment scene hints |
| `prepared/stage_long_literals.json` | Literal source candidates with member/offset/fingerprint and preceding context; not approved dialogue assignments |
| `prepared/rpw_inventory.json` | Validated chunk boundaries and 5,535 original string slots; pointer schemas unverified |
| `prepared/library_inventory.json` | Ordered source fields and original member identities for all three encyclopedias |
| `prepared/glossary_candidates.json` | 1,883 candidate name-field bindings with legacy references kept separate; no approved English/tokens |
| `prepared/ui_candidates.json` | Mixed-source candidates, per-occurrence locations, discovery methods and reference-match leads |
| `prepared/artwork_inventory.json` | 135 member hashes and header bytes; no glyph allocation or artwork translation |
| `prepared/inventory_summary.json` | Counts, source/archive fingerprints, SDAT utility hash, explicit unverified states |
| `verification/verification.json` | Source recheck, archive round trips and synthetic growth evidence |

The UI discovery set contains **120,363** candidates, including all lexed stage
literals, all RPW string slots, and heuristic printable NUL-delimited cp932 runs
from LUACPK/AIDDATAPACK. **4,192** candidates have exact Japanese reference
matches. Neither number measures UI coverage or reviewed translation. Source
comments, executable labels, runtime assembly, escaped/split forms, UTF-8 text
and artwork require further scoped work. A reference match does not establish
screen role, meaning, font encoding or safe replacement.

Source inventory found **66,919** stage long literals and **283** members with
scene hints, agreeing with the earlier parser probe counts. Comment/quoted-string
handling is now lexical. Event, ordinal-in-event, speaker and gameplay-stage
bindings remain unresolved; other agents must not receive these as verified
dialogue assignments. Voice-line extraction and translation are not implemented.

## Verified milestone

- Original ISO SHA-256:
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- **82** logical files extracted and rechecked; `WP.CPK` is **1,580,686,480**
  bytes assembled from two noncontiguous extents.
- SDAT decrypted offline to a CPK with SHA-256
  `4e34cdedf96394a133ab80784b49f702029ca314685fa6421557ee3c97c318ea`.
- Stage, RPW, KW, PT, RT, LUACPK, AIDDATAPACK and TPACK rebuilt byte-identically
  (**8 archives / 2,088 members**).
- A **70,052-byte synthetic** replacement forced a real DataL-to-DataH move in
  the stage CPK and preserved **875** untouched members. That output contains
  test data and must never be deployed.
- **14** tests passed: malformed/valid ISO records, joining streamed extents,
  path containment, long Joliet names, Lua comments/quotes/byte offsets, CPK
  no-op preservation, growth into an empty DataH, multiple migrations, shrinking,
  unknown-ID rejection and refusal to overwrite source/output files.

## Port provenance

The first UI authoring layer is now available separately from these archive
stages: `python -m tools.ui_spirits check` validates the 42-command Spirit
batch and its partial target glossary. Exported review text remains unencoded
and has not been inserted into the game. See `docs/UI_SPIRITS.md`.

The source project was read only. These reviewed source versions informed
the port; they are not imported binary configuration:

| Source tool | Original SHA-256 | Port |
| --- | --- | --- |
| `isoread.py` | `30d1f8ac2574898d27b3721531f3b63eeed7edf778065dfe50bb01a4f4c4b9d7` | Reworked reader with multi-extent aggregation and strict paths/bounds |
| `cpk.py` | `b89d952845af115971b5428cc7574736f873a893a020e974d2fcf55b853dfd7b` | Reviewed reader plus size, identity, decompression and output safeguards |
| `cpkpatch.py` | `90014142d17ee296fb4e5365101f4d8374da20ac7e032c57b7e22f8684ad24b9` | ITOC rebuild logic with strict IDs/output checks and cumulative ItocSize repair |

Offline `make_npdata.exe` SHA-256:
`d1e0d0f9d4d5cf44616ca0a31560fb38b3997793e15027ea92097da005d1054e`.
No RPCS3 launch/stop, cache change, save change, game patch or release occurred.

Next: independent executable/font analysis, verified stage/record bindings,
UI consumer and RPW schema audits, reviewed target glossary, SDAT re-encryption
and an authorized minimal runtime round trip. No font cells, voice tables,
display budgets or installed-data paths have been carried over from Jigoku.
