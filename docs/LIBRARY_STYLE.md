# Library translation style

For translators of Tengoku library (encyclopedia) entries. Read this, your
brief in `work/tengoku/library_briefs/<batch>.md` and the generated glossary
sheet `work/tengoku/library_briefs/GLOSSARY.md`. `BASE_RULES.md` applies in
full; the points below are how it applies to the library.

## Output

Write `work/translation/en/library/<batch>.json`, UTF-8:

```json
{
  "schema": 1,
  "kind": "pilot",
  "entries": {
    "12": {
      "source_sha256": {"DSCR": "...", "DSC2": "..."},
      "origin": "agent:pt_012",
      "DSCR": "English description",
      "DSC2": null
    }
  },
  "names": {
    "ワッ太": {"kind": "pilot", "en": "Watta", "evidence": "akurasu Z3.2 Pilot Database: Watta Takeo"}
  },
  "report": {
    "entries_in_batch": 40,
    "entries_examined": 40,
    "left_untranslated": [],
    "uncertain": ["pilot 12: ...what you decided and why..."]
  }
}
```

- Copy `source_sha256` exactly from the brief. It binds the English to the
  Japanese it translates.
- `DSC2`: `null` when the brief says DSC2 is the same as DSCR. Otherwise
  translate it in full (it is usually DSCR plus a later update; reuse your
  DSCR English for the shared sentences).
- Check your file: `python -m tools.library_text check --file <batch>.json`.
  Fix every ERROR. Names reported as "not in the glossary" are expected when
  you used a new name; list each one in `names`.

## Text

1. **ASCII only.** Straight quotes and `'` apostrophes, `-`, `...`. No curly
   quotes, em dashes, ellipsis characters or fullwidth characters outside tokens.
2. **Do not wrap.** The Japanese is hard-wrapped every ~38 characters, often
   mid-word. A new paragraph starts with a fullwidth space (`　`). Join the
   wrapped lines; separate paragraphs with a single `\n`; no leading spaces.
3. **Translate everything, in order.** Write the full meaning first. Do not
   shorten or drop the end of a sentence. There is no length limit here; the
   builder wraps and fits the text.
4. **Readings in parentheses are furigana** (`巨蟹（きょかい）`): drop them.
5. **Keep control codes and placeholders** (`$n`, `$l` and similar) exactly.
6. **Style of the existing library.** Follow the Jigoku English in your brief:
   past-tense narrative, a first line such as `President of Takeo General
   Company. Age 12.`, quoted speech and titles in single quotes.
   **American spelling**, as in the Jigoku English (`-ize`, `center`, `defense`).
7. **Context across entries.** An entry may repeat or continue another one
   (a keyword about a person who also has a pilot entry, for example). Search
   the other briefs in `work/tengoku/library_briefs/` and the finished files in
   `work/translation/en/library/` and keep the shared sentences consistent.

## Names are tokens

Every name of a person, unit, organisation, place, series or story term that
is in the glossary sheet is written as a token, never as literal English:

```
$$スフィア$$ reacts to his will.   ->  The Sphere reacts to his will.
three $$スフィア$$s                ->  three Spheres
a $$スフィア|lc$$ bearer           ->  a sphere bearer
```

- Suffixes (plural, possessive) stay outside the token. `|lc` lower-cases the
  first letter; there is nothing else.
- Use the token exactly as the sheet lists it. If the sheet lists `レイ#pt231`
  and `レイ#pt394`, pick the one this entry means; a bare ambiguous token is an error.
- A glossary English you think is wrong: keep the token and say so in
  `report.uncertain`. Do not work around it with literal English.
- A name not in the sheet: write it as `$$<Japanese exactly as in the source>$$`
  and add it to `names` with proposed English and evidence. Check
  `work/glossary/reference/sources/akurasu_z3.2_*.wiki` (Tengoku's pilot
  database, mech list and series) and `akurasu_srw_glossary.wiki` before
  inventing a romanization. When the wiki and the corpus disagree, the wiki
  wins. Your proposals are suggestions only: the orchestrator settles every
  name once for the whole library, and prose never changes because of it.
- `PENDING` in your brief means the entry's own name has no English yet:
  still use its token, and propose English in `names`.

## Meaning

- **Jigoku reference.** Many entries existed in Jigoku, and your brief shows
  the Jigoku Japanese and English. Where a Tengoku sentence is unchanged, keep
  the Jigoku English sentence (the two games must read the same). Translate new
  or changed sentences yourself, and check every kept sentence against the
  Tengoku Japanese: a small change (a date, a rank, a tense) must not be missed.
- **Gender.** Use he/she only when the Japanese or the glossary settles it
  (彼/彼女, 少年/少女, 息子/娘, 兄/姉, 男/女 and similar, or the entry is about a
  known character). Never infer gender from a name. Otherwise repeat the name
  or use they/them.
- **Pro-drop is grammar, not style** (BASE_RULES). A library entry is about
  one person, unit or term, so the entry itself usually settles who did what:
  write that subject, and check a verb survived too. Keep the ambiguity (a
  passive or impersonal construction) only where the entry and its neighbours
  genuinely do not settle who. Check the direction of requests and favours
  before choosing a construction. Restoring a subject is not padding.
- **Flag every kept omission.** Each place where you kept the source's
  omission goes in `report.uncertain`, with the entry id and why the text does
  not settle it. A subjectless line reads fine in English, so only the
  translator comparing against the Japanese can catch it.
- **Spoilers are the game's.** Translate what the entry says; do not add
  knowledge from outside the game.
- **Uncertainty is worth reporting.** List every call you were unsure of in
  `report.uncertain`, even if the entry is finished: a referent you inferred,
  a term you could not identify, a tie you broke.
- If an entry cannot be translated with confidence, leave it out of `entries`,
  list it in `report.left_untranslated` and say why.
