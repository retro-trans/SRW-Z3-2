# Fresh retranslation: stages 19–28

Completed **4,609 records in 63 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: stages 19-28 on route A: Macross Quarter 19-20, joined MQ/Hive 21-22, common 23-25, continent 26-28, and 2220/2221 choice scenes. This continues the previous batch’s route A.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 744 / 744 | 11 | PASS |
| 2 | 810 / 810 | 11 | PASS |
| 3 | 745 / 745 | 10 | PASS |
| 4 | 751 / 751 | 10 | PASS |
| 5 | 750 / 750 | 10 | PASS |
| 6 | 809 / 809 | 11 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts, text format and measured three-line limits pass. No untranslated rows or unknown glossary tokens remain.

All 63 active prior translation files and their archived copies match their starting hashes. The glossary has 19 appended entries and one explicitly reviewed correction to an existing term; all other existing entries are unchanged. Coordinator normalization changed 29 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Points for wording review

- The fresh English differs from the previous draft in 3,660 records. The per-agent reports record source and neighboring context reads, retained fragments, and uncertain decisions.
- At 282:t_10:22, Grace means Feldt's surname; its separate token avoids confusing her with Macross's Grace. Unidentified recipients at 295:t_006:3 and 295:t_102:0 use neutral “them.”
- Gepe-whatever, Dark Smile, Powered Sisters, Jin Great Company, Hick Kappei and Chuu have source-based proposed renderings. The Colony Alliance Forces and Emissary of the End titles also remain proposed.
- The existing proposed nickname Busupea is now Ugly Duo, retaining Kappei's insult and AG's objection. This is the one correction to an existing glossary term; its original value remains in the baseline and correction audit.
- The Gunleon “Gan-gnoring” joke at 295:t_003:5, Daitarn/daring wordplay at 371:t_3:38, and bamboo stalk/livestock malapropism at 372:t_018:1–3 are adaptations. The last preserves the confused meanings but cannot reproduce the Japanese homophone.
- Asuka's “smart aleck” in 353:t_2:106 stays unattributed because its precise target is unclear. Straus's identity is not inferred from the name; an original character's “men” statement stays as that character's belief.

`coordinator_sampling.json` identifies sampled meaning checks and corrections. `glossary_additions.json` records additions and the exact existing-term correction; research is in `work/glossary/research/retranslation_batch3_20261007.json`. Meaning review and in-game layout review remain separate from the passing structural and measured-fit checks.

## Caption layout corrections - 2026-10-09

Restored 27 captions to source field separators and line layout. Exact before/after edits are in post_review_corrections.json; manifest hashes refreshed. Original completion counts remain historical. Active/prior/before_name_pass files unchanged.

## Late glossary normalization - 2026-10-09

Updated 28 rows after source-gated literal review. Exact before/after text is in post_review_corrections.json; current hashes refreshed. Original completion counts remain historical.

Source-reviewed grammar correction 231:t_017:23: Whole-corpus exact-source callsign scan: Ozma speaking or Cathy addressing Ozma; replace composed Skull callsign with researched full Skull 1 token. Preserve identity. Exact edit is in post_review_corrections.json; hash refreshed.
