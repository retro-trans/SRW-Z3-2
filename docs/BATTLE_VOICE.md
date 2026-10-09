# Battle voice lines (DATA/BTLC/SRVC.BIN)

Phase 1, 2026-10-01: research and tooling only. Nothing here has been
translated, built into a release, installed or run in the game. Statuses
below keep "read from the files", "checked by a tool" and "seen in the game"
apart; the last one is empty so far.

## Commands

```powershell
$py = "C:\Users\Binh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m tools.srvc prepare --apply    # pristine SRVC.BIN + program ELF -> work/tengoku/prepared/
& $py -m tools.srvc info               # table location, counts
& $py -m tools.srvc roundtrip          # no-op rebuild must be byte-identical
& $py -m tools.voice_bind --apply      # work/tengoku/voice/blocks.json, lines.json
& $py -m tools.voice_tm --apply        # work/tengoku/voice/tm.json
& $py -m tools.voice_write synthetic --out <scratch dir> --apply
& $py -m unittest discover -s tests
```

`prepare` reads only the verified extraction in `work/tengoku/source`
(hash-checked against `source_manifest.json`) and reconstructs the program
ELF with `tools/self_elf.py`, the same executable `tools/game_build.py`
patches. The source ISO is never opened for writing.

| Tool | Role |
| --- | --- |
| `tools/srvc.py` | Format, executable table location/validation, parser, growable rebuild, table patch |
| `tools/srvc_check.py` | Independent readback (shares no code with the writer) |
| `tools/voice_write.py` | Edit planning (stale/conflict guards), build + verify, synthetic test, output guard |
| `tools/voice_bind.py` | Line -> block/slot/rule/cue; block -> speaker leads; voice-set groups |
| `tools/voice_tm.py` | Exact-Japanese translation memory against Jigoku's shipped English |
| `tests/test_srvc.py` | 16 tests: synthetic fixtures (sparse fake ELF + blocks) and the real file |

Ported from Jigoku's `srvc_blocks.py`, `srvc_identify.py`, `srvc_link.py`,
`voice_pilots.py`, `voice_propagate.py` and `check_voice.py` ideas; no
Jigoku address, block count or table offset is used.

## File format

Pristine file: 3,499,808 bytes. All of the following was read from the file
and checked by `srvc.parse` for every block; the layout matches the
executable's own parser (next section).

```
file  = block[0] .. block[367], back to back, each start 16-aligned
block = [tab[i], tab[i+1])           tab = 369 big-endian u32 in the EBOOT

+0  u8    version   3 in all 368 blocks; the game checks it (see below)
+1  u8    n1        74 in all blocks     -> A: n1 x u32 situation slots
+2  u8    n2                             -> C: n2 x 8 bytes (not decoded)
+3  u8    n3                             -> D: n3 x 4 bytes (not decoded)
+4  u16le n4                             -> B: n4 x 8 bytes selection rules
+6  u16le n6        lines                -> cue: n6 x (u32 cue id, u32 flag)
+8  A, B, C, D, cue, offs[n6] (u32le, relative to the pool), pool
    pool = cp932 NUL-terminated strings, then zeros to the next block
```

- A slot = `(u16 first rule, u8 rule count, u8 flags)`; a B rule =
  `(u16 condition, u16 weight, u16 first line, u16 line count)`.
  Every one of the 78,302 lines is reached through exactly one rule of
  exactly one slot.
- 283 blocks carry lines, 85 are text-free (the first two are 304-byte
  header-only blocks). Largest block 54,016 bytes.
- 78,302 line references; 48,164 per-block distinct strings; 37,187
  distinct strings file-wide. No line points into the middle of a string.
- 3,982 pool strings are not referenced by any line; 59 of those are not
  even valid cp932 (leftover bytes in blocks 31, 61, 74, 118, 215 and
  312). Every referenced string decodes as cp932. The rebuild keeps all of
  them byte for byte.
- Lines open with corner brackets; 12 are thoughts in fullwidth parentheses
  and 25 have trailing fullwidth spaces or no bracket pair. 7,228 distinct
  strings contain a literal two-character backslash-n line break (up to 3
  per line), as in Jigoku. No `$`/`%` placeholders occur.
- One developer placeholder string ("silent, not shown in the real game")
  is used by 166 references; it stays Japanese.
- Differences from Jigoku: 368 blocks instead of 276; the parser checks the
  version byte; cue flag values range 0..8+ instead of 0/3.

## Executable consumers and evidence

Executable: the reconstructed program ELF (`ELF_SHA256` in `tools/vwf.py`).
VA = file offset + 0x10000 for both program segments used here. TOC base
r2 = 0x99fe70 (the r2 of all 33,039 OPD entries).

| What | VA (file offset) | How it was established |
| --- | --- | --- |
| Path string `/app_home/DATA/BTLC/SRVC.BIN` | 0x9eb080 (0x9db080) | Read by the start-read function through TOC slot r2-0x5d74 |
| **Block table, 369 x be32** | **0x9eb0a0 (0x9db0a0)** | Loaded once, by `lwz r10,-0x5b54(r2)` at 0x143574 |
| TOC slot holding the table address | 0x99a31c | The only word in the image equal to 0x9eb0a0 |
| Bank change / load setup | 0x143540..0x1435a0 | Compares resident bank id (`lhz 0x165c(r27)`) with the wanted id (`lhz 0x24(r26)`), stores table base at ctx+0x28 and the id at ctx+0x2c |
| Start read | 0x1390a0 | `&tab[id] = id*4 + table`, path, calls 0x13c164 |
| Partial read | 0x13c164 | offset = tab[id], length = tab[id+1] - tab[id], async read 0x22a84 |
| Poll / buffer pointer | 0x139058 | stores the loaded buffer at ctx+0x20 |
| Block parser | 0x1390fc (caller 0x1434d0) | `lbz r0,0(r4); cmpwi r0,3`; on mismatch zeroes the counts; then walks A, B, C, D, cue, offs, pool exactly as above |
| Function descriptors | TOC r2-0x5b5c -> OPD 0x961100; r2-0x5d70 -> OPD 0x9610f8 | OPD of 0x1390a0 (start read, installed as ctx+0x34 by the loader) and of 0x139058 (poll, installed by start read), both with r2 = 0x99fe70 |
| Install list | 0xa1b2b4 | path -> `/INSCO/` `DATA0046.DAT`, flag 1; no size field |

Validation of the table itself:

- It starts at 0, is strictly increasing and 16-aligned for 369 entries, and
  entry 368 equals the file size (3,499,808). The next word is 0: a different
  file's table (`0, 0x30, 0x213d0, ...`) follows, the same idiom as Jigoku.
- Its 368 starts equal, one for one, the 368 aligned `03 4a` headers found
  by scanning the file, and every block parses completely inside its window
  with only zeros after its pool. So the scan count (368) and the table count
  (368 blocks + 1 sentinel) agree; there is no hidden block.
- Single consumer: one TOC slot points at the table, one instruction loads
  that slot, no `lis/addi` pair builds any address in the table, no other
  word points into it; 0x13c164 and 0x1390fc each have one caller. The only
  other SRVC path reference is the HDD-install list, which has no size.
- No bound check on the bank id was found near the loader (as in Jigoku);
  irrelevant while the block count is unchanged.

`srvc.locate_table()` re-derives all of this at run time from the code
(14 instruction words, the OPD, the path string, the table run) and refuses
an executable where any of it differs. `read_table()` additionally pins the
file offset 0x9db0a0 and 368 blocks.

**Not traced:** where the read buffer is allocated (the request goes to the
generic streaming queue 0x22914 with the computed length; no clamp in that
path), and how the bank id at +0x24 of the unit's voice descriptor is
assigned. The RPW `robot` record has a 0..428 index column that looks like a
bank id but is a running ordinal (its block contents do not match the units),
so it is not used.

## Binding model

Structural (exact, from the file): each line reference has a block (= voice
bank), a slot, a rule with condition and weight, and a sound cue.
`work/tengoku/voice/lines.json` holds all 78,302 with ids `block:k` and the
string id `block:pool offset` used for translation.

Slot labels are **proposed** from reading the lines each slot selects in all
283 blocks; `(?)` marks real doubt. References per label (all 78,302):

| Slot | Label | Refs |
| --- | --- | --- |
| 0 / 1 | attack / counterattack | 13,773 / 15,538 |
| 35-52 | weapon slots 0-17 (attack call-outs; which weapon a number selects is defined outside SRVC) | 10,804 |
| 10 / 11 / 12 / 13 | shot down / heavy / moderate / light damage | 1,342 / 5,095 / 4,941 / 3,769 |
| 15, 16 | evade, special evade | 3,780, 12 |
| 14, 17, 18, 19, 20 | shield, no damage, barrier, phase shift, parry | 100, 542, 803, 2, 2 |
| 2, 26 | support attack, support defense | 1,847, 1,833 |
| 3 | follow-up attack | 645 |
| 4, 5 | team attack focus / split (?) | 800, 797 |
| 7, 8, 9 | special-opponent lines (?) | 2,329, 763, 63 |
| 28 | attack variant (?) | 4,258 |
| 27 | could not retaliate (?) | 2,241 |
| 22 | system/suspend chatter (?) | 994 |
| 21, 23, 24, 25, 29, 30 | cut-in, cannot attack, out of range, out of EN/ammo, special (?) | 494, 66, 388, 194, 87 |

Rule conditions: 0 is the generic pool; 40,477 references sit under a
nonzero condition (class byte << 8 | value, e.g. class 1 opponent types,
class 2 factions, class 3 traits). Their meanings are game data not decoded
here; the samples in `lines.json` make most of them obvious to a reader.

Speaker leads (`blocks.json`, evidence, never a verdict):

| Lead | Blocks |
| --- | --- |
| Jigoku section shares >= 50% of the block's lines (identity from Jigoku's `analysis/voice_identity.json` / docs) | 155 of 283 |
| ... and the recorded pilot resolves to a glossary token | 121 (35,724 refs) |
| Any Jigoku overlap at all | 236 |
| Weapon-name lead (RPW weapon -> `wpn-1r` -> robot name) | 108 |
| Weapon lead reaching a pilot token | 1 (Tengoku's robot PLTN field is mostly a dash or a developer placeholder) |
| No lead | 40 |

`spoken` lists the glossary pilot names a block mentions; these are usually
the people addressed, not the speaker. Blocks sharing >= 90% of the larger
line set form one voice set: 242 groups for 283 blocks (e.g. the Takuma
blocks 2/3). Jigoku's own warnings carry over: weapon matches on common
weapons (beam rifle, funnels) mislead, and Jigoku identities include
descriptive ones ("Neo Zeon grunt pilots") with no token.

## Translation memory

Source: Jigoku `translation/voice_*.json`, 211 documents, 25,743 distinct
Japanese lines with English. Exact match on the full string, brackets and
breaks included; the developer placeholder excluded.

| Measure | Matched | Fresh | Total |
| --- | --- | --- | --- |
| Distinct strings, file-wide | 20,193 | 16,993 | 37,186 |
| Line references | 42,598 | 35,538 | 78,136 |
| Per-block strings (writer granularity) | 26,889 | 21,254 | 48,143 |
| Per voice-set group (translation units) | 23,300 | 19,125 | 42,425 |

38,413 matched references (24,048 per-block strings) come from the Jigoku
section identified as the same voice set. 2,047 matched Japanese strings
have more than one Jigoku English; 639 matches are barks under 8 characters.
The earlier 20,198 figure counted matches against Jigoku's Japanese source;
20,193 have shipped English.

Use the memory as reference, not as answers (BASE_RULES): Jigoku English
uses Jigoku spellings (not this project's `$$token$$` names), a Jigoku-only
character set and a 36-cell estimate; a shared Japanese line can need
different English for a different speaker or situation.

## Writer

`voice_write.build(data, executable, edits, encode)`:

1. Plans edits: `{block, k, jp, text, scope}`. `jp` must equal the file
   (stale guard). `scope: string` replaces the stored string line k uses, so
   every line of that block sharing it changes too (one translation per
   stored string, the normal case); two edits giving one string different
   text are refused. `scope: line` gives a single line its own new string,
   appended to its block's pool, for the rare case where shared Japanese
   needs different English.
2. `srvc.rebuild`: same block count and order; header, A, B, C, D and cue
   tables copied verbatim; counts unchanged; original pool order kept
   including unreferenced strings; original zero tail kept; 16-alignment;
   the new 369-entry table returned. No-op output is byte-identical.
3. `srvc.patch_table` writes only the 1,476 table bytes, after re-validating
   the consumer code and that the table there is the expected original.
4. `srvc_check.verify` (independent): re-reads the table through the loader
   instruction's TOC slot in the NEW executable; requires the executable to
   differ only inside the table; table strictly increasing, aligned, ending
   at the new size; every block's header..cue bytes identical; untouched
   blocks byte-identical; every line's string and its NUL inside its own
   block window and equal to the expected bytes computed from the ORIGINAL
   file; the original pool sequence preserved. Nothing is returned or written
   unless this is clean.

Synthetic test (scratch only): one replaced string in each of the 283 text
blocks, one 2,800-byte growth in the largest block, one per-line split ->
368 blocks, 254 grown, 3,499,808 -> 3,509,088 bytes, largest block 56,800,
readback clean, and re-verified from the files on disk. The ASCII test text
is not the project font encoding; the output must never be deployed.
`voice_write` refuses `E:/RPCS3` and `work/output/iso` as output.

Limits and what the writer does not know:

- **Block size at runtime: unverified.** Estimated English (2 bytes per
  letter, Jigoku lengths where matched, 2.05 x Japanese length otherwise)
  gives ~4.9 MB and a largest block of ~76 KB; 4 blocks would exceed the
  original 54,016-byte maximum. Jigoku shipped grown blocks up to 41,744
  bytes (its original maximum 30,624). Test a deliberately large block in
  the game before relying on it.
- Encoding is the caller's: the build must encode with the same font
  mapping and allocation as the rest of that build. Whether battle text uses
  the same font page/VWF path as dialogue is **unverified**.
- Wired into `tools/game_build.py` since 0.4.1 (`tools/voice_build.py`):
  rebuilt after the VWF patch (`patch(elf, widths)` does not touch the SRVC
  consumer or table), the new SRVC.BIN and that executable ship together,
  and `tools/iso_write.py` carries the resized file.
- Installed data: the game installs SRVC.BIN to the HDD as `DATA0046.DAT`
  under `/INSCO/` (executable install list). An old installed copy with a new
  executable reproduces Jigoku's blank-text incident; check hashes before
  any runtime test and get approval before touching installed data.

## Unverified (runtime and semantics)

- Rendering of any rebuilt line in battle; block-size tolerance; read
  alignment requirements beyond the 16-byte alignment kept.
- Battle text box width. Jigoku's 36 cells was itself an estimate. Tengoku's
  limit is **unknown**: measure from a screenshot with the font actually used
  in battle, including the two-line case.
- Slot labels marked `(?)`, condition codes, C/D arrays, cue flags.
- Unit/pilot -> bank id mapping in the game (the speaker binding is
  content-based).

## Proposed translation workflow

1. Unit of work = voice-set group (`blocks.json` `group`); translate each
   distinct string once per group, propagate to sibling blocks by Japanese.
2. Before briefs: settle the speaker per group from the leads plus a read of
   the lines; record it with its evidence (as Jigoku's
   `analysis/voice_identity.json`) in a reviewed file, and resolve the
   speaker to a glossary token. Generic grunts stay generic.
3. Briefs: slices of at most 80 distinct strings, ordered by slot so a
   reader sees attack, damage, evade and weapon families together; adjacent
   slices read-only. Each row: string id, slot label(s), condition, the
   Japanese, and any TM candidates with their Jigoku section. Include the
   glossary sheet, weapon names as this project ships them, and BASE_RULES
   (gender, pro-drop, full meaning first).
4. Answer format (proposed): `work/translation/en/voice/<group>.json`
   `{"schema": 1, "blocks": [..], "speaker": {"token": "..", "basis": ".."},
   "lines": {"<block>:<pool offset>": {"jp": "..", "en": ".."}}}`; a row may
   add `"scope": "line", "k": n` for a single-line split.
5. Checks before merge: id exists and `jp` matches the pristine file;
   brackets/thought form kept (the writer should add them, as in Jigoku);
   literal backslash-n count kept or deliberately changed; tokens resolve;
   no two different Japanese lines collapse to one English within a group;
   drawable characters for this build's font; width against the measured
   limit once it exists (until then report, do not fail); the placeholder
   line left Japanese; coverage report per group.
6. Build: encode with that build's mapping, `voice_write.build`, ISO with
   both files, then one runtime round trip (a short line, a long two-line
   line and the largest block) before scaling up.

## Reused Jigoku English (2026-10-01)

`python -m tools.voice reuse --apply` wrote `work/translation/en/voice/gNNN.json`
(228 voice-set groups) from the translation memory:

- 26,889 of 48,143 block strings filled from Jigoku English (exact Japanese
  match); 21,254 remain for fresh translation; the 21 developer placeholder
  strings stay Japanese.
- Where Jigoku has several English versions (6,033 strings), the one from the
  Jigoku section identified as the same voice set is chosen (`review:
  same-speaker`, 5,536); 497 have no same-speaker version and take the first
  candidate (`review: conflict`, with `alternatives` listed) — review these.
- English mirrors the Japanese bracket form (「...」, (...)); literal `\n`
  breaks are kept as in Jigoku (counts equal the Japanese everywhere).
- Literal names became glossary tokens where the line's Japanese has the term
  (3,946 tokens); Jigoku spellings that differ from this project were fixed
  (Ryoma, Koji, Shin, Zanbanya -> tokens). Weapon/attack names keep Jigoku's
  English until the interface weapon list is translated, then they must be
  aligned with it.
- Speakers in each file are Jigoku's identification, marked "unreviewed".
- `python -m tools.voice check` validates ids, Japanese, brackets, ASCII and
  tokens (OK). The voice build must expand `$$tokens$$` with the glossary, as
  the dialogue builder does, before encoding.

## Fresh translation (2026-10-02)

- The remaining 21,254 strings were translated in 302 briefs
  (`work/tengoku/voice_briefs/`, `python -m tools.voice export`), answers in
  `work/translation/en/voice_new/`, rules in `docs/BATTLE_VOICE_STYLE.md`.
  `python -m tools.voice merge --apply` copied them into the voice-set files:
  all 48,143 block strings now have English.
- Each voice set's `speaker` was settled from the lines (`token`), with the
  Jigoku guess kept as `jigoku_token` and each brief's proposal as
  `proposed_by_<brief>`. Many sets mix voices (co-pilots, AIs, combo partners);
  the token names the main voice only.
- Open: 695 segments over 36 characters (runtime width unverified), 497 Jigoku
  conflict rows, attack names to align with the translated weapon list, and
  identical Japanese lines in different voice sets that read differently.
