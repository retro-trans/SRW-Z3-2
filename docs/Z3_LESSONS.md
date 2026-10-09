# Translation and engineering lessons carried from Jigoku-hen

Prepared 2026-09-11 for Tengoku-hen. Read with `../BASE_RULES.md`.
The base rules are preserved verbatim. This guide explains how to apply them
without repeating failures encountered in Z3; it does not make old numeric
IDs, runtime addresses, budgets or historical guesses valid for a new game.

Sources: Jigoku's BASE_RULES.md, CLAUDE.md, work/tr/CONVENTIONS.md,
docs/TRANSLATING.md, docs/MESSAGE_CLASS_AUDIT.md, HANDOFF.md and the verified
source-format comparison in docs/TENGOKU_PORTING.md. No new external naming
research was performed as part of this transfer.

## 1. Preserve meaning, identity and context

- Translate the actual source record. Read neighboring records and the
  scene before resolving an ambiguous speaker, pronoun, title or referent.
- A portrait ID, generated cast list, weapon-name match or heuristic unit
  label is a lead, not proof. Jigoku reused identifiers across unrelated
  characters; a voice bank can contain multiple cockpit speakers.
- Never infer gender from a name, honorific, portrait ID or guessed speaker.
  Use neutral wording when unresolved and report the uncertainty.
- Match the character's established register. Do not turn a normal speaker
  into all-caps shouting merely because a previous draft did so; AG's normal
  sentence case was a specific Z3 correction.
- Preserve distinct meanings. Different Japanese lines must not be collapsed
  into one stock English bark solely to save space. Identical strings may
  still need different English when context or speaker differs.
- Correct errors, not harmless stylistic variation. A prior shipped rendering
  is useful precedent, not proof; documented corrections supersede it.

## 2. Keep one terminology source of truth

- Reuse canonical names and researched identities from the shared glossary,
  with provenance and an explicit official/proposed/ambiguous status.
  Do not invent spellings from memory or let every translator decide again.
- The base rule preferring wiki terminology over a conflicting draft remains
  intact. Verify that a reference describes the same character/term first.
  A same-name match is not evidence of the same entity. Record unresolved
  reference conflicts instead of silently choosing an unrelated entry.
- Once glossary expansion is ported, write an existing glossary term as
  `$$japanese$$`, including speaker-name lines. Keep suffixes outside:
  `$$term$$s`, `$$term$$'s`; use supported `|lc` only when appropriate.
- Never invent a token or a discriminator. Look it up in the target glossary;
  unresolved or ambiguous references must fail validation. Until a target
  glossary and expansion/checking pipeline exist, treat tokens as an authoring
  convention, not something safe to inject into game text.
- Keep display spelling aligned across prose, pilot/unit names, weapon names,
  menus and encyclopedia entries. Do not retranslate an attack independently
  of its reviewed weapon-list name.
- Match the Japanese source and semantic role before converting literal
  English to a token. English-only replacement corrupts common words such as
  An, Lady, Boss, Zero and Princess.
- Two tokens may expand to the same English today but identify different
  entities. An unchanged render after replacement does NOT prove the token
  was correct; a future rename exposes the error.
- Numeric discriminators and game record IDs must be rebuilt for Tengoku.
  Never copy Jigoku's `#333`, `#168`, or similar numbers on faith.

### Concrete ambiguity lessons

- Rei Ayanami and Ray Lovelock share レイ; two Dorothys belong to different
  series. Resolve from dialogue, series and relationships, not portrait IDs.
- Lelouch's Zero is not Wing Gundam Zero. The Mazinger pilot Boss is not
  Mao being addressed as 'Boss'. Lady Une is not a generic 'lady'.
- Suzune addressed as 'Miss' is not the unrelated named pilot Sensei.
- A keyword named Princess is not every princess in the story.
- Pilot and robot senses may share a name. Select the right entity/field,
  even when both currently have identical English.
- Inspect context for short English terms too: AG, PS, Fa, UN and An can be
  valid names. Short length is not a reason to exclude them automatically.

## 3. A screenshot is a report, not the coverage boundary

When a screenshot exposes untranslated text, overlap or wrong wording:

1. Identify the actual display source. The same Japanese can exist in Lua,
   RPW, encyclopedia data, executable strings and artwork. Changing a copy
   that is not rendered does not fix the screen.
2. Inventory the whole related family from original source data, independently
   of the current translation list: all effects, terrain labels, unlock
   reports, mission conditions, commands or other relevant members.
3. Include numbered forms, spaces, line breaks, per-line rendering, name
   substitutions, escaped Lua strings and dynamically assembled variants.
4. Review meaning and fit for every variant; one blanket replacement is not
   a substitute for a category audit.
5. Add a missing-coverage regression check. Show source totals, translated
   totals, exclusions and unresolved cases. A deliberate missing translation
   should make the check fail, not silently disappear from the denominator.

Do not say 'all translated' because every entry in a hand-picked dictionary
has English. Unexpected source formats must be reported, not silently skipped.

## 4. Mission conditions need their gameplay roles

- Determine the role from the scenario operation table and surrounding logic,
  not just the Japanese sentence or which character's name appears.
- Victory objective example: 'Shoot down X.'
- Defeat event example: 'X is shot down.'
- Never mechanically translate both as 'Defeat X' or both as 'X is defeated'.
  These examples are not templates for unrelated objectives such as reaching
  a position, surviving, protecting a unit or completing a timed sequence.
- Preserve thresholds and equality, turn limits, timing, retreat behavior,
  faction restrictions, ordering, alternatives, and all required units.
- Keep SR-point requirements separate from victory/defeat semantics.
- Review numbered and unnumbered variants, wrapped lines and displayed names
  separately from internal aliases. Jigoku's Hibiki internal/display-name
  difference caused whole families of missing translations.
- Change wording, not gameplay condition logic, unless explicitly requested.

## 5. Preserve runtime syntax and record identity

- Preserve each control code, placeholder, keyword-link count and order.
  `《》` links bind positionally to their keyword-ID arrays in Jigoku.
  Confirm the same linkage in Tengoku before rewriting them.
- Preserve counts of player-name and other placeholders (`$n`, `$l`, `$c`,
  etc.), format specifiers such as `%s`, and their required ordering. Discover
  Tengoku's vocabulary; do not assume Jigoku's list is exhaustive.
- `$c` was a player-named squad in Jigoku. It is not translatable prose and
  must not be duplicated. Verify its role in Tengoku as with other controls.
- Distinguish literal backslash-n sequences from actual line breaks according
  to the specific file parser. Never blindly normalize one into the other.
- Preserve Lua syntax and delimiters. `--[[...]]` can be a comment rather
  than dialogue. Encoded text must not accidentally introduce a closing `]]`.
- Bind each answer to source archive/member, event, ordinal, speaker and
  source fingerprint as available. A hash of Japanese alone is not a unique
  line ID; identical silence lines occur for different characters.
- Source drift, duplicate assignments, missing records and unresolved tokens
  must be reported before merging. Never overwrite someone else's answer.

## 6. Storage space and screen space are different constraints

- Honor the base rule's goal: do not damage a translation merely to fit the
  original Japanese byte slot. Provide safe relocation/rebuilding support.
- Relocation is legal only after understanding every consumer: pool bases,
  pointer fields, read windows, size fields, indices and runtime capacities.
  Appending a string outside the block actually loaded by the game is not
  valid relocation, even if a desktop parser can read it.
- Jigoku's battle pools became growable when their executable block table
  was updated together with SRVC. The older 'in-place only forever' notes
  were superseded. Tengoku still needs independent table/buffer verification.
- Do not repoint binaries by blindly scanning for matching integers. Derive
  actual record structure and pointer columns; matching integers may be
  gameplay values rather than addresses.
- Screen width remains finite after relocation. Measure rendered width with
  the actual font, scaling and runtime-expanded placeholders. Avoid guesses
  based only on character count, byte length or Japanese/English ratios.
- Abbreviate or rephrase while preserving full meaning when a real display
  limit requires it. Never silently truncate. Flag cases that still cannot fit.
- Test alignment, overlap, overflow, padding and multiple screen contexts.
  A label appearing in two screens may have two different widths or anchors.
- Jigoku's 36-cell battle-line estimate, font free cells and padding codes
  are not measured Tengoku limits. Re-inventory unused/reserved glyphs.

## 7. Inherited prose conventions and their limits

Use consistent prior choices where they apply to the same context:

- Use straight apostrophes and `...` for ordinary ellipses; a standalone
  silent Japanese quote used nine dots in Jigoku. Unknown speakers use `???`.
- Do not introduce em dashes or double hyphens as prose punctuation. This is
  not permission to modify `--` in Lua code/comments or other syntax.
- Preserve thought-versus-spoken-line presentation. Jigoku used fullwidth
  thought parentheses, and dialogue/title/banner forms varied by field;
  validate glyph support before carrying those shapes into Tengoku.
- Preserve rank distinctions. The inherited convention is 'Lt. Colonel' for
  中佐, distinct from 大佐. Naval or character-specific established titles
  need context, not a global military-rank replacement.
- Do not settle open honorific/rank disputes independently in each slice.
  Record the question and existing usage, then make one reviewed project
  decision and a corpus-wide checked update if approved.

`reference/JIGOKU_CONVENTIONS.md` preserves the full historical examples.
It is NOT executable configuration or a ready-made Tengoku glossary. It
contains evolving counts, source-project paths, settled spellings, open
questions and inconsistent example IDs (including older Ray examples).
Look up identities rather than copying those numbers. Validate old naming
decisions before making them new-game canon; do not silently 'correct'
established spellings per slice.

## 8. Translation/proofreading workflow

- The inherited default slice is 80 consecutive records. Change it only
  deliberately for a task; supply adjacent context as read-only material.
  This rule describes assignment shape, not standing permission to delegate.
- Briefs must carry the applicable rules, source identities, glossary,
  speaker/context warnings, field-specific constraints and unique answer path.
  A rule only present in a handoff but absent from translator briefs was a
  known source of drift.
- Before merging, run the target's translation, name, placeholder, coverage
  and width checks. Tool names in historical notes do not mean those tools
  have been ported here. Never report an unrun check as passed.
- Report records examined versus records assigned, checker results, reused
  translation candidates, new terminology decisions and unresolved cases.
- Correct a bad name throughout the relevant corpus, not one screenshot.
  Dry-run and inspect samples first. Apply semantic edits before final
  canonical-name normalization so stale answers cannot reintroduce errors.
- Keep reviewed names in the translators' do-not-redecide list. Reuse valid
  existing translations, but match source/context instead of record numbers.
- Keep temporary files in designated ignored work locations, not the project
  root; use task/slice-unique names. Preserve concurrent and unrelated edits.

## 9. Verify the artifact, not just the writer's assumptions

- Test no-op round trips against pristine files before changing content.
- Read back the built archive/file independently; verify untouched bytes,
  records, cue metadata and archive members stay untouched as appropriate.
  A checker sharing the writer's incorrect offsets can certify the same bug.
- Source-coverage tests, binary checks, and visual/runtime tests answer
  different questions. Passing one is not proof of the others.
- For fonts, keyword positioning and UI geometry, test worst cases in-game.
  An extracted texture preview is not a live screenshot.
- For dialogue, confirm both subtitle display and voice playback. Keep the
  executable, dialogue table, text encodings and font atlas from one build.
- Ship every required artifact through the normal build, never as a forgotten
  manual post-build patch. Verify manifests and decode distribution patches.
- Keep statuses separate: source edited, built, automated tests passed,
  visually verified, installed locally, packaged as ISO, and published.
  A build directory does not mean a matching ISO exists.

## 10. Installed data, release identity and provenance

- Installed game data can override the new disc. Jigoku's missing text/voice
  incident revealed an original Japanese dialogue cache paired with a new
  executable expecting an expanded table. Compare actual hashes and lengths.
- Discover Tengoku's own cache path; never assume Jigoku's BLJS10256_DATA
  path. Close the game before an authorized cache change, prefer a recoverable
  backup, and never confuse installed game data with user saves.
- Keep pristine sources immutable. A previously deployed folder is no longer
  a pristine input just because it still has the original directory name.
- Do not copy game-specific constants or already encoded outputs between games.
- Use a separate Tengoku build counter. Once its initial version is chosen,
  each successful complete build increments its final component by one.
  Failed builds do not consume numbers; packaging the same build does not
  consume another. Never relabel different bytes as an existing version.
- If a title footer displays a version, derive it from that same build's
  version and validate agreement with its manifest.
- Record changes, evidence, limitations and pending runtime tests in the
  same session. Commit authored tools/translations/docs, not game dumps.

## Before accepting any batch

- [ ] Every assigned record examined or explicitly flagged.
- [ ] Speaker, referents and ambiguous glossary senses checked in context.
- [ ] Meaning, numbers, timing and gameplay-role distinctions retained.
- [ ] Tokens, placeholders, links and record identity verified.
- [ ] No accidental missing translations hidden by a hand-picked inventory.
- [ ] Display fit tested, or explicitly labeled unmeasured.
- [ ] Safe storage/reader compatibility established before binary changes.
- [ ] Actual checker outcomes recorded; visual/runtime limits stated.
- [ ] Changes documented; unrelated files and user data preserved.
