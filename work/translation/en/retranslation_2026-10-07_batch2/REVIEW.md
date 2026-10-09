# Fresh retranslation: stages 9–18

Completed **5,802 records in 78 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: Green Earth stages 9–11, common stages 12–16, Macross Quarter stages 17–18, and the 2210/2211 choice scenes. This continues the previous batch’s route A.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 953 / 953 | 13 | PASS |
| 2 | 992 / 992 | 13 | PASS |
| 3 | 971 / 971 | 13 | PASS |
| 4 | 971 / 971 | 13 | PASS |
| 5 | 936 / 936 | 12 | PASS |
| 6 | 979 / 979 | 14 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts, text format and measured three-line limits pass. No untranslated rows or unknown glossary tokens remain.

All 78 active prior translation files and their archived copies match their starting hashes. Existing glossary entries are unchanged; 20 new entries were appended. Coordinator normalization changed 63 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Points for wording review

- Stage 9–10 comedy includes the Twin Tail food joke, moe/fired-up wordplay, fictional weapon names and insect/meteorite wordplay. Translators recorded their readings; proposed weapon spellings remain provisional.
- Suzune's teasing at 177:t_1:289–295 may contain cultural allusions. The draft preserves the stated meaning without introducing an unsupported English reference.
- Kinoshita's address at 182:t_1:31 is rendered as “future brother-in-law,” an inferred relationship joke. The agent flags it for review.
- Later notes cover fujoshi wordplay, improvised attack names, interrupted requests, technical terminology during Kaname's interference, and deliberately unfinished thoughts.
- At 224:t_3:72 the unnamed emissary stays unnamed. The draft does not identify the speaker as Advent without source support.

The complete per-slice notes, including context reads and retained fragments, are in `review_notes.json`. Existing terminology remains authoritative; new provisional forms are marked in the glossary and backed by the batch research file.

## Generic Invader identity correction — 2026-10-09

Corrected 6 generic-species tokens; boss-specific references remain unchanged. Visible English unchanged; exact edits in `post_review_corrections.json`, manifest hashes refreshed. Original completion counts above are historical.

## Caption layout corrections - 2026-10-09

Restored 23 captions to source field separators and line layout. Exact before/after edits are in post_review_corrections.json; manifest hashes refreshed. Original completion counts remain historical. Active/prior/before_name_pass files unchanged.

## Late glossary normalization - 2026-10-09

Updated 15 rows after source-gated literal review. Exact before/after text is in post_review_corrections.json; current hashes refreshed. Original completion counts remain historical.

Source-reviewed grammar correction 88:t_001:26: Whole-corpus exact-source callsign scan: Ozma speaking or Cathy addressing Ozma; replace composed Skull callsign with researched full Skull 1 token. Preserve identity. Exact edit is in post_review_corrections.json; hash refreshed.
