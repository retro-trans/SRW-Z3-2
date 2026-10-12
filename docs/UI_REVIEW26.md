# Public 0.5.18 screenshot review: reports, name separator and weapons

Prepared version: 0.5.26. Publication needs explicit consent for this version.
Runtime visual confirmation is pending. Earlier unpublished fixes are included.

1. **Sub Order report:** the source is a GIFT_501 display literal in stage
   members 91 and 169, outside the dialogue and executable catalogs. The full
   GIFT category contains 24 distinct strings / 99 occurrences: 22 player
   notices / 97 occurrences and two developer test strings in member 863.
   All are covered by source-bound drawer translations. Preserve the native
   literals, numeric reward parameters, flags, tables and unlock triggers.
   Translate AG's eight distinct bonus amounts, item/unit grants, both
   upgrade refunds and both Lecture Plate unlocks, alongside Sub Order and
   D-Trader unlock announcements. Check every occurrence in the final archive.

2. **Hibiki's middle dot:** Setsuko records 177:t_1:208 and 177:t_1:264
   contain the unchanged $F placeholder. The native full-name composer
   calls the separator leaf at 0x1fba2c between nickname and surname. The new
   source-guarded leaf returns the encoded English space only when both saved
   components exactly equal the default Japanese names. Custom, null, partial
   and extended names retain the native separator; no save/name field is
   rewritten. The full-name consumer remains byte-for-byte native. Verify the
   caller, both patched name getters, separator and concatenations together.
   Existing custom-name order and surname abbreviation policy remain intact.

3. **Newtype Lv 2:** the base skill already has English in the RPW and
   executable tables. The composed native level string bypasses the base-only
   lookup. Cover all source RPW skill-name bases with the native leveled
   suffix forms, including already encoded English bases, plus the separately
   source-bound Newtype prefix/digit table. Keep every level, skill predicate,
   value, color and native buffer unchanged; English is relocated at drawing.
   The digit table at 0xa2f5a0 covers 0–9. Final exact lookup execution checks
   every generated key, and an altered source prefix must fail verification.

4. **Episode 13 SR condition:** active English is complete: within four turns,
   defeat all other enemies and reduce Shiseiten's HP to 99,999 or less.
   The corrupted screenshot came from the public build's bounded intermediate
   copy. The earlier 0.5.23 repair uses ten-byte static display keys, followed
   by complete relocated English. Check all 262 static keys and all 110 mission
   members again, including the specific Episode 13 final drawer payload.

5. **Weapon consistency:** read the sibling SRW Z3 localization source and
   English catalogs without modifying that project. Audit all 686 active full
   names and all 606 list names; 440 full names and 373 list names share exact
   Japanese sources with Jigoku. Of the shared full names, 432 are identical.
   Preserve eight reviewed differences: Lightning Kick, six Infinity-family
   variants and Super Galaxy Giga Drill Break. These preserve prior meaning
   review and story/voice consistency; sibling Space Galaxy mistranslates Super.
   Expand 75 fitting abbreviated list names to the active complete names,
   including all three Radiant Wave Surger variants. Seven shared names still
   need abbreviations because their full forms exceed the measured width.
   Audit each retained abbreviation and every final weapon pointer.

The screenshot locates weapon names at x84 and the following table at x538.
Use a conservative 440px text bound at the native 31px font, leaving 14px.
This replaces the original 18-character proxy for this relocated display-only
column; the pointer schema and all other name/skill/part byte limits remain.
Measured fit is not a claim of in-game visual testing.

Read-only meaning review `review26_wording` examined 31 dialogue rows around
the two vocatives, all 24 report strings, eight related mission conditions and
all 440 shared full weapons. No source-meaning ambiguity was left unresolved.
All player-facing report translations preserve the complete source meaning.

Evidence: work/ui/review26_weapon_audit.json,
work/translation/en/ui/review26_messages.json and
work/ui/review26_verified_0.5.26.json. Final release evidence records checksums,
both original/0.5.18 patch routes and publication status separately.
