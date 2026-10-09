# Fresh retranslation: ace talks, guidance and previews

Completed **2,369 records in 31 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: remaining dialogue: ace pilot talks, guidance scenario, and next-episode previews. Coverage follows the repository dialogue plan.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 400 / 400 | 5 | PASS |
| 2 | 400 / 400 | 5 | PASS |
| 3 | 400 / 400 | 5 | PASS |
| 4 | 415 / 415 | 6 | PASS |
| 5 | 400 / 400 | 5 | PASS |
| 6 | 354 / 354 | 5 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 31 active prior translation files and their archived copies match their starting hashes. The glossary has 16 appended entries and 1 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 1 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Coordinator source sampling and editorial review

Reviewed 88 source/English samples across all 31 slices, with additional neighboring context where needed. This is not a second full independent proofread.

- All five agent1 slices sampled:15 source/English pairs. Requested full predicate for853:t_19:7 short agreement before final audit.
- Ikue spelling variant 郁恵 occurs four times; source/food context and Akurasu Ikue's Snack support existing 郁絵 token. Earlier three use established identity correctly.
- Eight researched terms added after batch11 completion baseline a05c2f7fbc88a55a4f0582b9d6accd091124a653f916408e214b6d3a79f11cb8. DRAGOON official Bandai Namco spelling; Robovitan B provisional exact-B rendering. Luca Ghost UAV Simon explicitly separate from pilot; John/Peter proposed English Bible-name variants. Aquarion Mars/Luna robots separate from pilot homonyms. Exact corpus/context reviewed.
- Six samples from2500_10..11 reviewed: Rei Evangelion identity, Lelouch Zero response, Aquarion ace-conversation contexts retained. Whole-corpus token candidate audit1-11 reviewed four candidates: three explicit Celestial Being mothership references correctly use ship token; Quantum Burst punctuation variants refer to same researched ability, no semantic correction required.
- Agent1 completed400/5, all strict checks PASS, restored short predicates and corrected stale pun notes before stopping.26cuts18uncertainties reported, all five +16neighbor windows recorded. Parent reviewed fire-under-employees adaptation, Nataku homophone loss and Shinn-san hardship: uncertain sound loss documented, no external explanatory dialogue added.
- Agent2 allfive slices sampled15rows. Matching Gamlin trailing-off clauses and AG interrupted offer retained; Canaria elliptical dedication has restored subject/verb. Pilot Simon reference853:t_84:5 distinguishes Gurren drill from Luca UAV.
- Agent2 stopped400/5 with all final strictPASS;416unique source IDs,480window observations;358distinct source hashes no repeat mismatch, original standalone ! retained,0captions. Pun adaptations retained with documented loss.
- Desire777 three identical lines remain provisional humorous service label; no verified external facility identification. Parent source-reviewed853:t_118:15 proposed chant actions; actual source explicitly requests spread legs, flex biceps and genital-reveal gesture, so retain crude joke without inventing franchise identity.
- Tutorial UI wording aligned with ui/eboot.json and UI mission entries, not prior dialogue: Lecture Plates, Combat Record, 3rd Super Robot Wars Z Tengoku-hen / Jigoku-hen without colon. Tag Battle System retained plain UI label.
- All400 agent3 rows sampled acrossfive slices; caption/no-content sentinels avoided, farewell/chant/spoken-noun rows preserved by source. Additional draft source sample861:t_066:3 Riddhe rank kept Ensign per source.
- Twelve batch12 terms currently researched. Space Fill matches existing Jigoku-derived UI label; Monomolecular Cutter and TDD-1 match actual UI names. Valor/Alert confirmed in separate UI glossary as prior Jigoku spirit rendering; remain plain menu labels in dialogue rather than unresolved cross-glossary tokens.
- Agent3 completed 400 rows in five slices; all final strict checks PASS, zero captions or repeat mismatches, 50 source cuts/formulae and 19 uncertainty notes. Repaired causal endings at 853:t_118:20 and 119:20 to full clauses while retaining the reason connection.
- Parent source review caught 861:t_027:7 Aegis-ship pun accidentally changing the ship from target to weapon; agent4 asked to restore target and permission question across identical repetitions. Agent5 asked to restore finite predicates at 861:t_079:5 and 081:7, where English had introduced noun fragments.
- Aichi Prefecture confirmed by prefectural government; descriptive pen name Super Robot Wars Fan stays plain quoted. Winged emissary retains 翅者 orthographic joke without inventing a deity. Venus short robot name added separately from full Venus A; Dr. Shikishima uses existing surname token.
- Agents4 and5 stopped after all 815 rows passed final checks. Agent4 reports 42 cuts/27 decisions; agent5 reports34 cuts/20 decisions. Aegis target restored, same-row nominal fragments repaired, actual source interruptions retained. Anne's missing profile researched and updated with explicit before/after ledger; no name change.
- Agent6 spirit references checked against separate UI glossary: Gain, Vigor, Alert, Persist (not Guts for 根性 or Flash for 閃き). Umasugi WAVE and Morisoba radio references researched against official SRW blog and SRW Wiki; proposed romanizations added. Nono-Noriko uses composed existing name tokens and documented joke adaptation.
- All31 slices source-sampled, including final354 rows. Token audit candidate853:t_81:6 is a verified same-character Sakuya kana/kanji alias, not a mistaken character; whole-corpus scan found no other mixed-script use. No correction merely for a different but correct token.
- Final preview slang is translated as player-facing text: MG5 meaning expanded, Nono-Noriko remains transparent combination of established names with reported sound-chain adaptation. Original controls and source-era game titles preserved.
- Agent6 completed 354 rows in five slices and stopped edits after all strict checks passed. Read 426 source-window rows, 362 unique. Final saved-text audit covered every owned row; 21 deliberate source cuts and four adaptation uncertainties remain documented.
- Final cross-slice source review confirmed the repeated fictional reader pen name at 861:t_048:6. Agent5 replaced generic 'a big SRW fan' with quoted 'Super Robot Wars Fan' to match 047:6 and 047:15, then passed the strict check and stopped edits. All six translators stopped before normalization.

Official is the existing glossary category, including wiki-supported forms; licensed localization is not implied. Proposed terms remain provisional.
