# Name research

For researchers settling Tengoku library names and character profiles. Read
`BASE_RULES.md` (Ground work) and this file, then your brief in
`work/tengoku/name_research/<group>.md`.

The library descriptions refer to names as `$$token$$`; the build fills in the
glossary English. So your decisions change every entry at once, and you never
edit prose.

## Sources, in order of precedence

1. **User-confirmed** terms (status `confirmed`). Never change them.
2. **Akurasu Tengoku (Z3.2) pages**, saved in `work/glossary/reference/sources/`:
   `akurasu_z3.2_pilot_database.wiki`, `akurasu_z3.2_mech_list.wiki`,
   `akurasu_z3.2_series.wiki`, `akurasu_srw_glossary.wiki`. When the wiki and a
   corpus disagree, the wiki wins.
3. Other akurasu pages (for example the Z, Z2, Z3 or series pages), fetched
   with your web tools. Cite the URL.
4. **Official English** of the source anime or game (licensed release, official
   site, established franchise wiki). Cite the URL.
5. **Jigoku glossary** `work/glossary/reference/jigoku_glossary.json`, then
   Jigoku's shipped library English (quoted in the translators' proposals).
   These are an earlier translation corpus: a sourced wiki or official form
   wins over them (BASE_RULES), except terms with status `confirmed`.

Memory alone is not a source: if you cannot find one, say so and mark the
name `proposed`.

Match the Japanese exactly: the game's spelling can differ from the obvious one
(`キリコ・キュービィー`, not `キュービー`). A name that is only a romanization
with no source is `proposed`, never `official`.

## Output

Write `work/glossary/research/<group>.json` (UTF-8), and nothing else:

```json
{
  "schema": 1,
  "group": "gundam_1",
  "names": [
    {"jp": "ロンド・ベル", "kind": "keyword", "en": "Londo Bell", "status": "official",
     "source": "https://akurasu.net/wiki/... : 'Londo Bell'"},
    {"jp": "ムウ", "kind": "pilot", "token": "ムウ#orguss", "en": "Mu", "status": "proposed",
     "source": "...", "note": "Orguss character; not Mu La Flaga",
     "profile": {"gender": "male", "gender_evidence": "...", "position": "...",
                 "personality": "...", "nickname": "", "sources": ["..."]}}
  ],
  "characters": [
    {"pilot_id": 12, "gender": "female", "gender_evidence": "DSCR: 彼女 / akurasu ...",
     "nickname": "...", "position": "captain of ...", "personality": "calm, ...",
     "sources": ["https://...", "library pilot 12 DSCR"]}
  ],
  "report": {
    "names_in_brief": 66, "names_settled": 64,
    "left_pending": ["X: why"],
    "challenges": ["ガンダムサバーニャ: 'Gundam Zanbanya' should be 'Gundam Sabernya' because ... (source)"],
    "retoken": ["pt_062 entry 68: $$ムウ$$ -> $$ムウ#orguss$$"],
    "uncertain": ["..."]
  }
}
```

- `kind`: `pilot` for any person, `robot` for units, ships and machines,
  `series`, or `keyword` for everything else (organizations, places, terms).
  For a name already in the glossary, keep its kind.
- **Settle every name in your brief**, including those with status
  `proposed`/`ambiguous`: confirm or correct the English with a source.
  A name you cannot settle goes in `left_pending` with the reason.
- **Official or confirmed names you believe are wrong** (the brief marks the
  flagged ones): do not list them in `names`. Put the case, with the source,
  in `report.challenges`. The orchestrator decides.
- **One Japanese name, different people or things** (`ムウ`, `シリウス`,
  `黒い太陽`, `早乙女`): give each its own record with a `token` of the form
  `<Japanese>#<short ascii tag>` (or a `target` binding it to its library
  entry), and list every prose use that must switch in `report.retoken`.
- **English style.** Use the form that reads correctly inside a sentence. No
  brackets, slashes or alternatives in `en`. Use natural capitalization: title
  case only for proper names ('Quantum Brainwaves' is a term, so lower case
  'quantum brainwaves' unless the official English capitalizes it). No leading
  "the" unless it is part of the name.
- **Characters.** For every pilot entry in your brief, fill a `characters`
  record, following BASE_RULES: gender, nickname, personality, position, with
  sources. Gender comes from the Japanese text (彼/彼女, 少年/少女, 息子/娘, 男/女
  and similar), the character's source work or the wiki, never from the name.
  Use `unknown` when nothing settles it, and `not applicable` for AIs and
  creatures without one. Give the evidence either way.
- People mentioned in prose without a pilot entry get a `profile` inside their
  `names` record when your sources settle it.
- Other briefs may share names with yours (the Z original cast is split into
  `original_1a/b/c`). Before finalizing, read the other briefs' lists for your
  names and keep one spelling; report any disagreement in `uncertain`.
