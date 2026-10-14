# Spirit terminology, Inazuma Kick and numbered missions — 0.5.29

The user's reports follow public 0.5.28. Match the requested Z3 convention:
[Break = 直撃, Fury = 闘志](https://www.akurasu.net/wiki/Super_Robot_Wars/Z3/Spirits).
Retain the other selected Spirit names. Update names, badges, native compact
flags, bonus descriptions and the trophy referring to Break. Match every
active Inazuma Kick weapon/glossary/voice reference and its answer copies.

## Numbered condition failure

The original mission composer at `0x1aa6e8–0x1aa91c` prefixes victory/defeat
text with `１．`, `２．` or `３．`, from the TOC table at `0x99b354`.
It stores a 103-byte row: two state bytes and a 101-byte text buffer.
The static ten-byte translation keys pass this composer intact, but the
previous drawer dictionary matched only the unprefixed key. SR conditions
could match while numbered victory/defeat conditions showed internal keys.
The earlier tests executed the bounded copier and dictionary separately;
they missed the intermediate numbering step.

Cover all four prefix states for every static condition: 262 × 4 = 1,048 native compositions.
Keep the native numbering, colors, row state, original source strings,
selection IDs and gameplay logic. Reserve two full-width cells for each
numbered English line; continued lines use the native two-cell indentation.
Execute the actual composer for every case before the real drawer lookup,
with canaries after the native row. Guard the whole composer and prefix table.

Use one short key per wrapped English line, separated by native newlines.
Continuation keys carry a source-bound line suffix and match the native
two-cell indentation. The actual composer now counts each line, so subsequent
conditions reserve the correct vertical space. Each drawer replacement is
a single line; it cannot silently add rows the surrounding UI did not count.

Episode 23's visible keys are `条件１７１` (Defeat all enemies) and
`条件１５５` (An allied battleship is shot down). This shared fix covers every
chapter using those and the other static conditions, including all three
numbered slots. The 25 live-name/counter conditions keep their substitution
path, with wrapping that reserves up to 40 bytes for names and 20 for counters.
All expanded rows fit 96 bytes, leaving four bytes for numbering/indentation
and one NUL inside the native 101-byte text field. Complete strings fit the
302-byte native condition field. Execute substitution followed by numbering
for every condition, in four prefix states with default and maximum-size
custom values: 200 additional cases, preserving values and field/row canaries.

Meaning review examined all 25 live conditions and 79 source rows including
siblings. Only one long SR condition needed shorter wording. It still requires
victory condition 2 within four turns, at least four Angeloi Arca shootdowns,
and at least two enemy shootdowns EACH by Setsuko, Rand, Crowe and the live
protagonist. Its worst expanded size after wrapping is 289 bytes. Keep all
numbers, glossary tokens, authored paragraph breaks and placeholder counts.
The English-only review and decisions are in `review29_live_audit.json`.

## Delivery

Prepare original-game and public-0.5.28 Retro Trans patches. Describe only
changes since public 0.5.28 in the release notes. This request authorizes fixes
and preparation; publication of 0.5.29 still requires explicit consent.
Final archive, executable, ISO and patch verification do not claim in-game
visual confirmation.
