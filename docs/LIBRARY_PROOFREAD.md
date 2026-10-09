# Library proofreading (meaning)

For proofreaders of the Tengoku library English. Read `BASE_RULES.md` ("When
translating any kind of text", the pro-drop rules, "When proofreading") and
`docs/LIBRARY_STYLE.md`, then your brief in `work/tengoku/proofread_briefs/`.

Each brief entry shows the Japanese, the current English (with a short hash),
the English and researched gender of the entry's own names, the gender of every
person named by a token, and the translators' own notes.

## What to fix

Compare every sentence with the Japanese. Fix what is **wrong**; leave what is
merely different. Do not rewrite a sentence because you would phrase it
differently, and do not "improve" style.

1. **Mistranslation**: wrong meaning, wrong referent, reversed direction
   (who did what to whom), wrong number, rank, date or tense of events.
2. **Omission**: a clause, sentence or detail in the Japanese is missing.
3. **Addition**: the English says something the Japanese does not (common in
   sentences kept from Jigoku: e.g. "Londo Bell's flagship", "the class").
4. **Omitted subject** (pro-drop is grammar): where the entry settles who, the
   English states it. Keep a passive or impersonal form only where the entry
   and its neighbours genuinely do not settle it, and list each such place in
   `report.kept_omissions` with the reason.
5. **Pronouns**: use he/she only when the brief's researched gender says
   male/female. A wrong pronoun is a defect (for example Toma is male). Where
   the old rules made a translator repeat a name in every sentence for a
   character whose gender is now known, replace the repetition with the
   pronoun: that is a defect of the old rule, not a style preference. Gender
   `unknown`: no he/she. `not applicable`: "it".
6. **Rules**: ASCII only outside tokens, American spelling, no manual line
   wrapping, one `\n` between paragraphs, single quotes for titles and speech.

## Do not touch

- **Tokens** (`$$...$$`) and their English. Names are settled; do not change a
  token, even if you would spell the name differently. If a token points to the
  wrong person or thing, report it in `report.name_issues`; do not edit it.
- **Literal English names** (a name written as plain text instead of a token):
  leave them. A script handles names after your fixes. List any you notice in
  `report.name_issues`.
- `DSC2` null stays null.

## Output

Write `work/translation/en/library_proofread/<brief name>.json`, UTF-8, and
nothing else. Save it early and rewrite it as you go, so work survives an
interruption; if it exists when you start, continue from it.

```json
{
  "schema": 1,
  "batch": "proof_pt_000",
  "fixes": [
    {"kind": "pilot", "id": 3, "field": "DSCR", "english_sha256": "325910d012d3af31",
     "new": "the full corrected English of that field",
     "reason": "omission: the Japanese says ... ; pro-drop: subject is Kappei"}
  ],
  "report": {
    "entries_in_batch": 40, "entries_examined": 40,
    "kept_omissions": ["pilot 12 DSCR 'was destroyed': the entry does not say who"],
    "name_issues": ["pilot 20 DSCR: 'Londo Bell' is literal English"],
    "uncertain": ["pilot 7: read 彼 as Kouzuki, not the father"]
  }
}
```

- One fix per field: `new` is the **whole** corrected field text, and
  `english_sha256` is the hash shown in the brief for that field. When a
  sentence is shared by DSCR and DSC2, fix both fields.
- Every fix states its reason and its category.
- Validate before finishing: the JSON parses, and each `new` keeps every token
  of the original unless your reason explains why.
- Report `entries_examined` honestly and every call you were unsure of.
