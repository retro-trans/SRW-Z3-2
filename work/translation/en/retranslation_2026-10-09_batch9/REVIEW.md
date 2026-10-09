# Fresh retranslation: Sousuke rescue and Left-Behind Sea routes

Completed **5,583 records in 79 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: alternate routes: Sousuke rescue stages 17-22, Left-Behind Sea stages 26-29, and remaining choice D-Traders. Coverage follows the repository dialogue plan.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 922 / 922 | 12 | PASS |
| 2 | 900 / 900 | 12 | PASS |
| 3 | 916 / 916 | 13 | PASS |
| 4 | 937 / 937 | 14 | PASS |
| 5 | 950 / 950 | 12 | PASS |
| 6 | 958 / 958 | 16 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 79 active prior translation files and their archived copies match their starting hashes. The glossary has 35 appended entries and 0 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 9 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

43 source rows were absent from the archived prior drafts; these are newly covered and included in the differing-row count. Exact IDs are in `prior_coverage_gaps.json`.

## Coordinator source sampling and editorial review

Reviewed 219 source/English samples across all 79 slices, with additional neighboring context where needed. This is not a second full independent proofread.

- 20 representative source/draft rows read across dlg_2041_00..06. No sampled meaning defects; 306:t_101:2 'By ending your life' is a genuine cross-row means continuation, confirmed against prior and following rows. Model-only Rk-91/92 pending glossary token substitution.
- Seven samples reviewed across dlg_2044_04..06; agent3 asked to restore subject in 336:t_025:1 and verb/subject in evaluative 336:t_105:8 and scan analogous clauses.
- Reviewed six more samples in2042_00/01 and34samples across agent2's twelve slices. Requested restoration of weapon development at335:t_1:12; asked agent2 to verify self-withdrawal versus invitational plural at329:t_3:70.
- 15samples across2042_02/03 and2045_00..02 read; no meaning defects identified. Source-context check confirms Patrick Colasour identity335:t_1:27. Added Earth qualifier requested330:t_022:3; captain narrative clarified. Caption shape sweep requested agent2 restoration for five caption layouts.
- 13additional samples read across2042_04 and2045_03..06. Development335:t_1:12 and Earth-humanity330:t_022:3 corrections source-rechecked; O-Kon335:t_1:102 correctly uses mask object token. Allagent2captionlayouts verified by own fullaudit. M9 shorttoken substitution deferred to mechanicalpass.
- Six samples read across2046_00/01. Exactnames scan earlier4/7Overman references normalized with separate ledger; active9owners handletwo refs.
- Six samples across2046_03/04 source-reviewed; no new meaning defects. Brussels term source confirmed and added.
- Five samples in2046_02/07 and2220_00 reviewed. ELS full expansion347:t_2:77 verified and newtoken appended. Asked agent4 to join completed though-clause800:t_10:11. Parent verified336:t_001:16/347:t_1:42/306:t_000:6 grammar repairs and Overman identity342:t_111:0; requested natural sensory collocation in lastrow.
- Six samples2054_00/01 read; askedagent4 torestore It at395:t_1:95 andsource-review/report galaxy echo395:t_1:45.
- Six samples2054_02/03 preserve meaning andrequestdirection. Latebriefs10-12 nowexplicitlysaved-draftgrammarpatterns andcaption audits.
- 25 representative rows reviewed across2054_04,2055_00..04,2056_07/08,2057_00; no sampled meaning changes required. Gargantia full formal Evolvers name added proposed literal; Earth-type Hideauze/Pilot Interface+System/Kugel Fleet composition resolved. Macross call signs source-reviewed and added.
- 15 samples across2054_05/06,2056_00,2057_01/02 read. Asked agent6 to restore settled grammar419:t_1:208 after context and confirm genuine echo419:t_1:158. Arm Raker cockpit term researched/added.
- 19 more samples read across2054_07,2056_01/02,2057_03..06: no new defects. Agent6 confirms Mel's419:t_1:208 question refers to feelings and will restore full clause. Guarded Fire literals in earlier64:t_104:4,70:t_004:3 Breast Fire and224:t_10:52 Basara shout from erroneous Noin alias tokenization.
- Source recheck verifies800:t_10:11 and395:t_1:95 repaired. Six samples2056_03/2057_07 prompted attachment of artificial concession413:t_3:82 and full assessment420:t_020:12.
- Six samples2056_04/2057_08 read; preserved assessment direction and attacks' force, no new defects.
- Three samples2057_09 read; source+neighbor review420:t_045:2 confirms she is Elunaluna, no gender correction needed.
- Final15samples across2056_05/06,2057_10,2230/2240/2250 read, all79slices sampled. No additional meaningdefects.
- Fullbatch strictPASS5583 and60captionsspacingPASS. Rechecked413:t_3:82 and420:t_020:12 attached/fullclauses. Agent6foundandrestored9standalone!rows accidentallymisreadashelpercaptionmarkers; finalstrictcheckafterrepair required. Addedmarkerwarningto10-12briefs.
- Afteragent4stopped, parentrevieweduncertainty348:t_012:3; agent5readsource+8neighbors andconfirmedunknownrecipient. Replaced unjustifiedhimwithsingularthey before namepass; exactledgerneutral_pronoun_correction.json; affectedstrictPASS.
- All six agents EDITS STOPPED before names. Final namepass9rows including exactM9alias, genericmessenger347:t_1:64 guarded by source context. Thirty-five append-onlyglossaryterms; all79prior/activehashes verified. Forty-three source rows absent prior drafts newlycovered.

Official is the existing glossary category, including wiki-supported forms; licensed localization is not implied. Proposed terms remain provisional.

Source-reviewed terminology correction 414:t_042:3: Whole-corpus exact Japanese review; apply batch11 researched Queen of Roses / Fold Wave terminology, retaining plural suffix. Original source and prior snapshots preserved. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed terminology correction 414:t_044:4: Whole-corpus exact Japanese review; apply batch11 researched Queen of Roses / Fold Wave terminology, retaining plural suffix. Original source and prior snapshots preserved. Exact edit is in post_review_corrections.json; hash refreshed.
