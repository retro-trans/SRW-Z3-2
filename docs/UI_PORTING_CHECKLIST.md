# Tengoku UI discovery and replacement checklist

The subsequent [0.5.3 expansion](UI_EXPANSION_0.5.3.md) translates the identified
catalogue and extends its source bindings. Runtime checks and generated-text
consumer work remain; no family is closed.

## Scope and starting state

The current 0.5.2 comparison is in [UI_COVERAGE_2026-10-10.md](UI_COVERAGE_2026-10-10.md),
with source-level evidence in `work/ui/coverage_2026-10-10.json`. It supersedes
early discovery counts as a work plan, without closing any UI family.

Use `work/ui/reference/jigoku_ui/README.md`, `catalogue.json` and
`repair_map.json` as references. Initial target source discovery now exists in
`work/tengoku/prepared/ui_candidates.json`; see `docs/PIPELINE.md` for its scope.
It includes mixed-source candidates and heuristic text runs, not an audited UI
inventory. The first scoped Spirit-table text batch is now in
`work/translation/en/ui/spirit_commands.json`, with its active audit at
`work/ui/spirit_audit.json`; see `docs/UI_SPIRITS.md`. No family is closed,
and runtime verification remains pending. The first scoped binary patch is
applied to a separate game copy; see `docs/UI_BUILD.md`. Imported
reference states and the empty reference audit template remain unchanged.
This checklist does not authorize deployment or release.

The goal is a source-driven inventory of Tengoku UI, not a list of old Japanese
strings to replace blindly. New sequel elements and duplicate rendering paths
must be discovered independently of the reference dictionary.

## Families to audit

- Commands, button prompts, intermission, library navigation and help text.
- Team setup, roster/list rows, movement fields and deployment confirmation.
- Status windows, map popups, battle preview and unknown-value placeholders.
- Search, naming, support menus, network menus and settings.
- Tag Commands, Z Chips, command explanations and result alignment.
- Weapon headings, selection/info tables, attributes and weapon names.
- All weapon effects: descriptions, effect rows and map/battle status badges.
- Maximum Break and assist/support labels, including texture-only artwork.
- Repair costs, rewards, clear reports and skill-triggered results.
- Item unlock conditions, shop notices, trader labels and generated messages.
- Every terrain label, including uncommon map types and display variants.
- Victory, defeat and SR Point conditions across all stages and phase changes.
- Spirit, skill, ability and part names/descriptions, with tutorial references.
- Location/date cards, episode titles, title/footer artwork and other headers.
- Layout regressions: alignment, width, overflow, overlap and all UI states.

The list is a starting taxonomy, not proof that no other UI families exist.
Extend it when target source discovery reveals additional consumers.

## Required evidence per target occurrence

Start a target audit using `tengoku_audit_template.json`. Record at least:

1. Unique occurrence ID, family, source archive/member/path, encoding and source
   fingerprint; locator within the source (not just a Japanese string).
2. Screen, widget and actual rendering consumer; text, dynamic assembly or art.
3. Original Japanese, proposed English, contextual meaning and reviewed glossary
   identities. Link any reused reference IDs without adopting their numeric IDs.
4. Placeholders, argument order, roles, prefixes/suffixes, newlines, significant
   spaces, numeric ranges and every generated/state-dependent variant.
5. Disposition: reused, revised, new, absent or unresolved; search state, evidence
   and reviewer notes. Negative evidence must name the searched scope.
6. Layout bounds, anchor/alignment, font/scale and selected, disabled, empty,
   unknown-value and longest-valid-value states where applicable.
7. Implementation location and source/binary validation results, followed by
   runtime evidence or an explicit unverified status.

Keep unknown totals null, never zero. Count target occurrences independently
from unique keys and distinguish text rows, generated variants and art assets.

## Translation and coverage gates

- Audit a reported defect's entire family across its target consumers, not only
  the screenshot string. Search source text, assembly fragments and artwork.
- Victory objectives describe an action to achieve; defeat conditions describe
  failure events. Infer the actor/target from the mission and phase, not merely
  a shared Japanese suffix. Do not force both into “Defeat <name>” or
  “<name> is defeated.” Preserve turn limits, HP thresholds and exceptions.
- Resolve all multiple-English reference groups by context. Do not overwrite
  a reviewed target translation simply because another old file differs.
- Reuse glossary wording only after entity/series/variant review. Never import
  source token numbers or private-use font slots as target mappings.
- Derive generated variants from target code/data. Old hook offsets and range
  assumptions are examples, not proof of target coverage.
- Review unmatched target records for sequel additions and changed meanings.
  Mark a reference absent only after a documented search; otherwise unresolved.

## Implementation and acceptance gates

- Verify target archive structure, record identities and consumers before edits.
  Reimplement from source; do not run copied `.py.txt` references as tools.
- Preserve control codes, placeholders, storage limits and unrelated bytes.
  Retain reproducible source fingerprints and reversible outputs.
- Measure English fit with the actual target font and widget bounds; check
  anchors, clipping, badges and spacing at the game's normal resolution.
- Check every relevant display path, including texture duplicates and transient
  map/battle labels. A translated weapon effect row does not prove its badge
  is translated, and a translated heading does not prove its menu variants are.
- Validate the built artifact against source expectations, then verify in game
  when authorized. Keep static and runtime results separate; preserve saves.
- Close a family only when its inventory, variants and remaining exceptions are
  accounted for. Report unresolved records and untested screens explicitly.
