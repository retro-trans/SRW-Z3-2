# First-ten retranslation — 2026-10-07

Completed a fresh English draft of **3,888 records in 54 slices**, using six GPT-6.1 Sol agents with medium reasoning, in two waves of three.

Scope follows the established first-ten play-order batch: two prologues, stages 1–8 on Green Earth, plus the 2200/2201 route-choice scenes. It does not mean numbered stages 1–10 or both routes.

| Agent | Examined / assigned | Slices | Check |
| --- | ---: | ---: | --- |
| 1 | 669 / 669 | 10 | PASS |
| 2 | 625 / 625 | 8 | PASS |
| 3 | 644 / 644 | 9 | PASS |
| 4 | 647 / 647 | 9 | PASS |
| 5 | 648 / 648 | 9 | PASS |
| 6 | 655 / 655 | 9 | PASS |

Validation: all assigned IDs and source fingerprints match; speaker headers, control-code counts, keyword-link counts and text format pass. There are zero unknown glossary tokens, zero untranslated rows, and zero measured three-line overflow warnings. The isolated checker now treats unknown tokens and overflows as failures.

All 54 active previous translation files and their preserved copies still match the starting hashes. Existing glossary entries are unchanged; 13 sourced or explicitly provisional terms were appended. A reviewed token pass and two targeted substitutions changed 33 fresh-draft rows. The original agent drafts remain in `before_name_pass/`; the earlier project draft remains in `prior/`.

The new draft is in `drafts/`. It has not been promoted into the active build inputs, built, deployed, or checked in-game. Coordinator review covered samples and flagged terminology, not a second complete meaning proofread.

## Decisions and review points

- Food label: unified the two proposed forms as Grilled Trident, following the sourced glossary decision.
- Sirius: used a separate faction token in 51:t_1:37; the character entry stays unchanged.
- Pinion Halberd: spelling confirmed by the licensed Good Smile product listing.
- Proposed names remain reviewable: Galaxy Ramen, Volunteer Club, Central Continent, Closer Pass, Sniper Casanovas, Lightbugs, Beal, Mr. Triangler, Reactor, Sirius.
- Review the adapted mothership/explosion joke (40:t_012:0–1), sniper nickname joke (51:t_1:225–226), Mari’s unspecified smell comparison (34:t_038:0), and Bevel’s broadly described chest condition (69:t_1:29). Intentional interruptions and unresolved referents are documented in the per-slice reports.

`review_notes.json` aggregates the original agent notes, including historical uncertainties subsequently resolved by the coordinator. `coordinator_changes.json` records exact row edits; `glossary_additions.json` and the linked research file record terminology evidence; `validation.log` records the final checks. No new Japanese dialogue dumps were created.

## Caption layout corrections - 2026-10-09

Restored 1 captions to source field separators and line layout. Exact before/after edits are in post_review_corrections.json; manifest hashes refreshed. Original completion counts remain historical. Active/prior/before_name_pass files unchanged.

Source-reviewed grammar correction 33:t_1:29: Agent9_4 source+8neighbors review: Misato acknowledges Gendo's order, no genuine cut; restore subject and verb. Exact edit is in post_review_corrections.json; hash refreshed.

## Late glossary normalization - 2026-10-09

Updated 10 rows after source-gated literal review. Exact before/after text is in post_review_corrections.json; current hashes refreshed. Original completion counts remain historical.

Source-reviewed grammar correction 76:t_003:16: Whole-corpus exact-source callsign scan: Ozma speaking or Cathy addressing Ozma; replace composed Skull callsign with researched full Skull 1 token. Preserve identity. Exact edit is in post_review_corrections.json; hash refreshed.
