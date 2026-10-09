# Fresh dialogue retranslation completed
2026-10-09

All 63,553 player-facing dialogue records have fresh English drafts across 12 batches and 857 slices. This covers main story, endings, alternate routes, ace-pilot conversations, guidance and previews. The excluded test map is outside the player-facing plan.

Six GPT-6.1 Sol / medium translators were assigned per batch in concurrency-limited waves. Translators read Japanese with neighboring context, documented uncertainties and deliberate cuts, and completed saved-draft checks before coordinator name normalization. Quantified coordinator sampling logs for batches 4-12 cover 1,901 rows across 662 slices. Earlier batches retain review findings in their reports. This was not a second full independent meaning proofread.

| Batch | Records | Slices | Current validation |
| --- | ---: | ---: | --- |
| 1 | 3,888 | 54 | PASS |
| 2 | 5,802 | 78 | PASS |
| 3 | 4,609 | 63 | PASS |
| 4 | 5,643 | 75 | PASS |
| 5 | 7,096 | 95 | Layout review: one row |
| 6 | 6,828 | 91 | PASS |
| 7 | 5,515 | 70 | PASS |
| 8 | 7,116 | 98 | PASS |
| 9 | 5,583 | 79 | PASS |
| 10 | 6,085 | 81 | PASS |
| 11 | 3,019 | 42 | PASS |
| 12 | 2,369 | 31 | PASS |

The final coverage audit confirms an exact source partition, no missing or duplicated records, matching source fingerprints and draft hashes, and zero incomplete examination reports. Current structural checks pass. Caption layout checks show no differences, and all five original U+0431 source characters retain their counts. The source-glyph regression suite passes.

The final glossary normalization audit found zero further changes across all 12 batches. Five token-identity candidates were individually reviewed: three mothership references and two equivalent-name variants. All five retain the correct identity; their decisions are recorded in completion_token_audit.json.

One measured-fit exception remains: batch 5 row 604:t_6:4 in dlg_2086_02 enumerates eleven complete Sphere names and needs four lines in a three-line box. Its meaning is preserved. Resolve the layout before promotion or a game build.

Provisional names, difficult puns and context-dependent readings remain explicitly documented in the slice reports and glossary research. A passing structural check is not proof that every editorial judgment is final.

Drafts remain in work/translation/en/retranslation_2026-10-09_batchN/drafts/. Starting prior files and before-normalization snapshots are preserved. Exact later corrections have audit ledgers. No active-translation promotion, ISO build, deployment or in-game validation was performed; this work does not create a release version.

Evidence: work/translation/en/retranslation_progress.json, each batch's REVIEW.md / review_notes.json / coordinator_sampling.json / validation.log, work/translation/en/completion_token_audit.json, and the final completion audit JSON.
