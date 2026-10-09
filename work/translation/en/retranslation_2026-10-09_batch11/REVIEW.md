# Fresh retranslation: remaining late-game routes

Completed **3,019 records in 42 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: alternate routes: Crowe and Char stage 43, Macross Quarter stages 52-54, despair stage 57. Coverage follows the repository dialogue plan.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 484 / 484 | 7 | PASS |
| 2 | 509 / 509 | 8 | PASS |
| 3 | 480 / 480 | 6 | PASS |
| 4 | 493 / 493 | 7 | PASS |
| 5 | 506 / 506 | 7 | PASS |
| 6 | 547 / 547 | 7 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 42 active prior translation files and their archived copies match their starting hashes. The glossary has 18 appended entries and 0 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 15 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Coordinator source sampling and editorial review

Reviewed 120 source/English samples across all 42 slices, with additional neighboring context where needed. This is not a second full independent proofread.

- Agents1/2 began isolated drafting whilebatch10agent6finishes; batch11termsqueueduntilbatch10closed, baselinewillbecapturedthen. No cross-batchglossarymutationduringoverlap.
- 7source/Englishsamples2082_00/2083_02..03readfaithful. Jeussurname574:t_1:34outsidelink reviewed, newaliasqueued; preservekeywordlinkscope.
- 6samples2082_01/2095_00readfaithful; Green/BlueEarthhistoricaldistinctionandAdventAngelidentitypreserved.
- 6samples2082_02/2095_01read; StrikerX3752AIidentityexplicit#pilot, pluralblackAngeloi andInsaraumthreat preserved.
- Official Aquarion EVOL attack page labels 次元隧道弾 Tunnel Bullet; official Astrokings Gunbuster collaboration labels Kazumi Queen of Roses. Queued exact glossary entries with Super Alloy Z. Source corpus scanned: Queen of Roses occurs in older batches and batch11; final late-name audit required.
- Agents1/2 stopped at993 total. Parent reran all15 owned strict checks after queued terms were added: all PASS. Agent1 restored That's a shame at580:t_10:7 and586:t_10:7; Char587:t_001:3 retains unfinished dative without invented predicate/identity. Agent2 Ranka670:t_1:149 first-person death referent source+neighbors corroborated.
- All16 currently researched batch11 terms added after baseline2490d3d4e9354773a5ae52ca59632782ccbad877e29a979106d28fddff8972d5 captured after10 closure. Queen#vajra distinguishes creature from Ziene. Full Fold Wave System distinct from Queen Frontier descriptive amplification system. Nana-chan is verified full nickname allowed by STYLE exception. Dark Wing and two Sousei book title variants remain proposed, licensed English unverified.
- Whole-corpus source reviews found3 prior Rose Queen and5 prior Fold Wave references; eight exact corrections applied across5/6/9, including agent3 source+8neighbor full-predicate Nicola praise652:t_1:48. Six affected slices strict PASS; ledger late_macross_terms_audit.json. Song Lion title separated from4 ordinary-lion references by normalization guard.
- Infinite Palm short form confirmed against official Aquarion EVOL full attack label and existing full token; earlier753:t_066:1 already correctly full token. Takeru671:t_101:1 twins-of-light/darkness epithet remains descriptive, wiki confirms Takeru/Marg pair; no invented second addressee.
- Agent4 stopped493/7 with strict PASS, six captions,49 genuine cuts and9 decisions. Parent read Mikage677:t_012:3 adabana metaphor, Sheryl676:t_3:52 song recipient and Zeus676:t_5:27 Ryoma life context; retained reported interpretations. Agent5 grammar repair requested707:t_000:1 fragment attachment. All35 slices outside final agent sampled; remaining7 are2101_02..08.
- Agent3 independently reviewed source plus eight neighbors for older Element Change commands456:t_016:12 and018:6; restore explicit transfer verbs and approval predicate before full-term normalization. Current671:t_021:0 likewise repaired.
- Agent6 source samples cover all seven slices. Kazumi713:t_108:1 Darling is reported spouse inference; unnamed Alto romantic referent remains unnamed. Adnachiel the General is a baptismal name, confirmed SRW Wiki; full-term normalization covers both exact source occurrences.
- Mechanical Angel713:t_149:0 refers to Aquarion; protect generic Angel word from unrelated emissary name tokenization.

Official is the existing glossary category, including wiki-supported forms; licensed localization is not implied. Proposed terms remain provisional.
