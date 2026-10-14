# First UI translation batch: Spirit commands

Current naming correction (2026-10-14): the user's Z3 convention is **Break**
for 直撃 and **Fury** for 闘志, corroborated by the
[Z3 Spirit list](https://www.akurasu.net/wiki/Super_Robot_Wars/Z3/Spirits).
Compact flags are Br and Fy respectively. The earlier naming choices below
are historical and are superseded for these two commands.

Prepared and source-checked 2026-09-11. This batch translates the original
Tengoku RPW Spirit table. It is now built and applied to a separate game copy;
see `UI_VWF.md` for the current VWF build and completed game/cache activation, or
`UI_BUILD.md` for the earlier pair-cell build. In-game display and fit remain
unverified. The sections below
document the earlier authoring milestone and its then-open integration work.

## Scope and evidence

- Source: `COMMONDATA/MTDATA/RPW_DATA.CPK`, member 0, chunk `spirit`.
- The target chunk is 880 bytes. The smallest consistent candidate stride is
  20 bytes: 44 records, with words 1/2/3 pointing to names, effect abbreviations
  and descriptions. Every one of the 132 fields resolves to an original
  j-string start. All 44 triples were read and reviewed. Words 0/4 remain
  uninterpreted; no gameplay metadata is changed.
- Records 1–42 are command records, including seven plus variants. Record 43
  is the unknown-state placeholder. Record 0 is the empty/no-command sentinel.
- **132/132 fields examined; 129 translated; 3 explicitly excluded** to retain
  the empty sentinel. There are 43 translated name fields, 43 abbreviation
  fields and 43 description fields. This counts occurrences, not unique strings.
- `work/ui/schemas/rpw_spirit.json` pins the target archive/member/chunk hashes
  and records the structural evidence. These are Tengoku measurements, not
  numeric bindings copied from Jigoku.

## Authored files and validation

- `work/glossary/glossary.json`: first partial target glossary, containing only 42
  Spirit command terms. It is suitable for this UI authoring checker; character,
  stage and voice identities are still unbound, and binary integration is false.
- `work/translation/en/ui/spirit_commands.json`: each field has a target occurrence ID,
  pointer location, source Japanese, text/record fingerprint, English, review
  status, reference IDs and rationale. Command names use `$$熱血#spirit$$`-style
  tokens, and descriptions use the same terms for explicitly quoted commands.
- `work/ui/spirit_audit.json`: separate active audit copied from the empty
  template and populated for this table's names/descriptions/abbreviations.
  All other family totals remain unknown; no family is closed.
- `tools/ui_spirits.py`: rereads pristine RPW, checks coverage and identities,
  resolves target terms, checks numeric values/control syntax/line counts and
  exports text for review. It has no binary patch or deployment operation.

```powershell
python -m tools.ui_spirits check
python -m tools.ui_spirits export
python -m tools.ui_spirits export --apply
python -m tools.ui_spirits related
python -m tools.ui_spirits related --apply
```

The exports already exist under `work/tengoku/ui/`. Commands refuse to overwrite
them. `spirit_commands/review.md` is the readable English review;
`spirit_commands/validated_text.json` holds the checked text and unverified
rendering flags. The active JSON files remain the authoring source of truth.

The complete suite now has **27 passing tests**, including 13 new tests for
translation coverage, wrong identities with identical English, numeric changes,
unknown markers, unresolved terms, source drift and foreign archive bindings.
The scalar checker recognizes narrow equivalences such as `Doubles` and `2`,
or `Halves` and `半分`; it does not prove translation meaning or screen fit.

## Terminology and meaning review

Names retain the inherited user-selected Spirit naming convention: Valor,
Soul, Fighting Spirit, Alert, Persist, Wall, Zeal, Fury and the other reviewed
names. The source of those choices is the unchanged `spirits.json` and
`repair_notes/SPIRIT_NAMES.md` reference. The original selected
[Spirit Commands page](https://superrobotwars.fandom.com/wiki/Spirit_Commands)
could not be fetched during this session; no claim of a fresh verification of
that page is made. The target terms are marked proposed project terminology,
with their source identities reviewed, rather than official localization.

The Tengoku-specific [Akurasu Spirit table](https://akurasu.net/wiki/Super_Robot_Wars/Z3.2/Spirits)
was used for a limited effect/target cross-check. Its alternate English labels
do not replace the inherited selected naming convention. Japanese target text
remains the basis for the translated effects; the wiki's Snipe summary omits
the range-1 exclusion that is explicit in the game source, so that exclusion
is retained. No extra gameplay effects or bug descriptions were added.

Source-driven corrections/clarifications from the inherited descriptions:

- **Bonds:** restores 5000 HP to all allied units, rather than suggesting only
  one allied team. The target table distinguishes it from Faith's selected
  team, and the Tengoku wiki corroborates the all-allies scope.
- **Fury:** retains both defensive abilities and skills; identifies ALL-attack
  penalties without confusing them with map/AoE weapons.
- **Focus / Focus+:** retain the source's distinction that the bonus affects
  final hit and evasion rates.
- **Accel:** lasts until movement; avoids implying a different action consumes it.
- **Faith:** states that each unit in the selected team receives the recovery.
- **Trust / Resupply:** explicitly retain the single-unit target. Resupply also
  retains its no-Morale-loss exception.

Other valid reference wording was retained. Damage multipliers, recovery
amounts, durations, critical-hit priority, map/range-1 exclusions and command
combinations were checked against each target record. Plus variants retain
separate occurrence bindings and their original effect descriptions.

The inherited `spirit_hook.json` note that plus variants differ only in SP cost
is not adopted as a Tengoku fact. Their target metadata words differ, and the
Tengoku wiki describes team-wide targeting. This batch preserves each source
description and leaves all metadata unchanged; actual targeting/rendering still
needs verification. Identical description text does not establish identical
runtime behavior.

Abbreviations describe active effects. Attune therefore shares `St` with
Strike, Bless shares `Lu` with Luck, and Cheer shares `Ga` with Gain. They are
not necessarily initials of the selected command. The two-letter English
forms are source proposals; no Jigoku compact glyph slots were imported.

## Broader family search and remaining work

A bounded scan searched all 120,363 entries in the existing mixed-source
discovery index for `精神` or quoted target Spirit names. All **299** matching
spans were reread from their original member bytes and fingerprint-checked:
152 stage literals, 43 RPW strings and 104 AIDDATAPACK runs. Eight source strings
are already bound in this Spirit table; **291 candidates need classification**.
These include ordinary dialogue about mental states and embedded design notes,
so they are not a count of untranslated UI. Dialogue remains for other agents.
Evidence: `work/tengoku/ui/spirit_related_candidates.json`.

The scan did not cover executable code/strings, library descriptions, artwork,
all generated variants or every possible source encoding. It does not establish
absence elsewhere. The reference Hope/Revival names have no record in this
particular 44-record table; their absence from the whole game is not asserted.

An embedded note in Tengoku AIDDATAPACK member 0 at byte 342470 describes a
29-character, two-line Spirit description area. That is a useful investigation
lead, not an English width limit or measured runtime behavior. The longest
authored English line is currently 57 characters; actual font metrics, scaling
and widget bounds remain unmeasured. No text was truncated to a Japanese slot.

Before integration, identify the actual draw consumers and their pointer use,
verify the target font/encoding, provide safe text storage, and test names,
descriptions and compact badges in all relevant states. Shared j-strings need
per-occurrence handling: Soul's name and abbreviation point at the same source
string but require `Soul` and `So`. No global Japanese-to-English replacement
can safely represent that distinction.

No game binary, original image, emulator, installed data or saves changed.
