# Fresh retranslation: Blue Earth and Dragons Hive routes

Completed **7,116 records in 98 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: alternate routes: Blue Earth stages 4-11, Dragons Hive stages 17-20, and associated choices. Coverage follows the repository dialogue plan.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 1207 / 1207 | 18 | PASS |
| 2 | 1199 / 1199 | 16 | PASS |
| 3 | 1172 / 1172 | 15 | PASS |
| 4 | 1151 / 1151 | 15 | PASS |
| 5 | 1172 / 1172 | 17 | PASS |
| 6 | 1215 / 1215 | 17 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 98 active prior translation files and their archived copies match their starting hashes. The glossary has 30 appended entries and 0 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 28 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

19 source rows were absent from the archived prior drafts; these are newly covered and included in the differing-row count. Exact IDs are in `prior_coverage_gaps.json`.

## Coordinator source sampling and editorial review

Reviewed 272 source/English samples across all 98 slices, with additional neighboring context where needed. This is not a second full independent proofread.

- 99:t_1:75: confirmed 'we will' answers Kamille's preceding future statement; no change.
- Found Patrick Zala token used for Colasour; whole fresh/active corpus scanned, three finalized fresh rows in batches6/7 corrected mechanically after source context review. Separate Colasour token added; exact changes and updated hashes recorded in those batches.
- Added full/short Graham Preventer Lightning aliases, preserving source forms.
- 118:t_104:1: requested full subject and verb for short evaluative statement.
- 141:t_2:72: preserve source Proto qualifier before established Ple Twelve token; franchise source confirms Z3-specific prototype context, no silent removal.
- 124:t_025:8: requested joining adjunct into full within-row sentence, rather than preserving Japanese display split as fragment.
- 142:t_003:8: reviewed compressed four-person comeback statement against source; translator retained suicide-charge contrast and all four participants.
- 129:t_2:3: requested restoration of fullwidth caption separator and all-own-caption spacing scan.
- 129:t_2:5: asked translator to review stacked commander/general titles against descriptive source role.
- 117:t_1:113: canonical Suzune Saijou full-name token used for katakana phonetic variant; retain distinction between spoken name and unknown kanji.
- 130:t_000:2: canonical Geofront token used for punctuated Japanese spelling variant.
- 135:t_1:12: requested preserving Saldias's bluff/probing nuance instead of generic testing.
- 148:t_037:1: requested retaining explicit purpose relationship between returning and retaking New Japan.
- 153:t_1:37: created Relena-specific Darlian token; whole fresh/active corpus scanned, three earlier fresh references in batches5/6 corrected with source review and hash/audit updates.
- 148:t_107:1: requested complete evaluative clause while retaining Saldias's sarcasm.
- 171:t_1:16,75,98 and166:t_039:1: asked translator to restore settled copulas and connect sentence clauses, not preserve Japanese grammatical omission.
- 171:t_1:64: Maki #pilot is the nurse in existing keyword profile; confirmed same person, preserving source-era knowledge.
- Super Coordinator and PLANT Council accepted as canonical token plus compositional descriptor; Clyne Faction and NT-D System added with licensed source evidence.
- 259:t_1:12: requested restoring nickname-derived-from-fighting-style relation, not just style-to-score relation.
- 172:t_009:3 and172:t_102:1: requested subject/verb in acknowledgment and joined within-row continuation.
- 154:t_004:1,014:5 and153:t_3:31: reviewed context confirms contemplative echo, male Riddhe referent and Vist patriarch.
- Gunbuster lengthy warp term follows franchise wiki; preserve complete long name and phonetic repetition, measured fit required.
- 165:t_1:78: context supports Mineva's condemnation in 'It's wrong even so';172:t_006:7 'do it' refers to leading PLANT against team.
- 259:t_1:122: requested copula in short evaluative statement.
- Invader #pilot specifically identifies fused Cowen/Stinger boss; generic creatures use #robot. Scanned whole fresh/active corpus;39 prior fresh generic references corrected mechanically with audit/hash updates. Visible English unchanged.
- 166:t_001:26: requested restored refusal predicate after Char's stay-back order.
- 254:t_009:12: requested retaining chance/fate connection in meeting across vast universe, not mere fact of meeting.
- 117:t_10:12: stopped agent2's missed evaluative copula corrected by agent4 under narrow extra ownership before normalization; source+neighbors reviewed, one exact source occurrence, strict pass.
- 154:t_035:17: requested pre-dawn time metaphor rather than added light; preserves next-row darkest-hour reasoning.
- 254:t_030:10: reviewed preceding Ryoma threat; conditional taunt retains response ellipsis.
- Final caption audit checked80caption rows: exact fullwidth-space counts and line layouts preserved, zero mismatches.
- 259:t_1:24–26: reviewed board/fishcake joke adaptation; theatrical boards preserves setup and chikuwa/kamaboko correction, literal idiom differs as reported.
- 265:t_2:57/60 and88: source confirms altered Suzune speaker headers and explicit this-world Ryoma distinction; retained reported choices.
- 172:t_109:4 and247:t_1:63,254:t_015:10/117:0: source contexts reviewed; reported hai/ash pun limitation and withheld/cryptic referents retained without invented explanation.
- 166:t_039:11: reordered once again before deliberately missing predicate; preserves source interrupted warning and recurrence.
- Name pass dry review excluded Getter within settled plain Getter Reactor; President and Coach identity confirmed.29literal substitutions across28rows applied once after all6stopped.
- Completion audit records19newly covered source IDs absent from prior choice-scene drafts; all98prior files retained starting hashes.

Official is the existing glossary category, including wiki-supported forms; licensed localization is not implied. Proposed terms remain provisional.

Source-reviewed grammar correction 136:t_102:0: Agent10_1 source+8neighbors review confirms Duo mocks Gilter after Lelouch outwits him; parent restores both settled assessment subjects/predicates under BASE_RULES. Zero remains Lelouch. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 166:t_111:0: Whole-corpus scan found three exact source occurrences. Replace composed old Super Coordinator with newly researched Ultimate Coordinator token; adjust article. Kira identity verified from source and neighbors. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 171:t_1:152: Whole-corpus scan found three exact source occurrences. Replace composed old Super Coordinator with newly researched Ultimate Coordinator token; adjust article. Kira identity verified from source and neighbors. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 111:t_3:75: Exact-source whole-corpus compound scan: replace composed Proto-Ple Twelve with new full alias token. Same English expansion and Marida identity retained. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 141:t_2:72: Exact-source whole-corpus compound scan: replace composed Proto-Ple Twelve with new full alias token. Same English expansion and Marida identity retained. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 153:t_2:30: Exact-source whole-corpus compound scan: replace composed Proto-Ple Twelve with new full alias token. Same English expansion and Marida identity retained. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 154:t_004:9: Exact-source whole-corpus compound scan: replace composed Proto-Ple Twelve with new full alias token. Same English expansion and Marida identity retained. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed grammar correction 165:t_1:117: Exact-source whole-corpus compound scan: replace composed Proto-Ple Twelve with new full alias token. Same English expansion and Marida identity retained. Exact edit is in post_review_corrections.json; hash refreshed.
