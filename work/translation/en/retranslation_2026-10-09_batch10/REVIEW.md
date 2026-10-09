# Fresh retranslation: Neo Zeon and Amalgam routes

Completed **6,085 records in 81 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: alternate routes: Neo Zeon stages 36-40 and Amalgam stages 36-40. Coverage follows the repository dialogue plan.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 985 / 985 | 13 | PASS |
| 2 | 1060 / 1060 | 14 | PASS |
| 3 | 1046 / 1046 | 14 | PASS |
| 4 | 1009 / 1009 | 13 | PASS |
| 5 | 987 / 987 | 13 | PASS |
| 6 | 998 / 998 | 14 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 81 active prior translation files and their archived copies match their starting hashes. The glossary has 34 appended entries and 0 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 7 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Coordinator source sampling and editorial review

Reviewed 238 source/English samples across all 81 slices, with additional neighboring context where needed. This is not a second full independent proofread.

- 13 source/English samples read across2069_00..02 and2070_05/06; requestdirection and Relena titleidentity preserved. NewSide1 andAprilius/surnamealiases source+neighbor reviewed.
- 15 additional samples2069_03..06/2071_00 read, no sampled defects. GN Big Cannon source context and wiki armament matched.
- 10 samples2069_07/2070_00/2071_01/2072_04 read; genuine cross-row thought continuation497:t_113:2 connects precedingmissionstatement. Rey#pt136SEED identity andRelena fullDarlian preserved.
- Preserve original U+0431 sourceglyph atthreebatch10rows; checker now exactsource-count gated with5regressiontestsPASS, encoderCP932roundtripPASS. Appearanceunverified; noheartguess. Added Legend, ZAFT Red, Zero#wing_zero, GobiDesert, BusterRifle aftersource+neighbors/evidence review.
- 24 further samples2070_01..04/2071_02..03/2072_05..06read; askedagent3 restorearrivalverb515:t_027:4.
- 12 samples2071_04..06/2073_00 read; AG Yes he did supported by Char question. Agent2 repairing Haman comparison and preceding missing do it. Three terms researched; Colony is game-specific variant of anime Side sphere.
- 24 samples2071_07/2072_00..03/2073_01..03 read. Requested Haman purposeclauseattachment509:t_108:7 andfullassessment520:t_2:64. Confirmedagent3savedarrivalverb515:t_027:4. HistoricalHeero#keyword distinguishesleaderfrompilot.
- 12samples2073_04/2074_01..03faithful;526:t_1:128readneighborsconfirmshewasanswer. TermsAxionFoundation/BlackBerets/Falke/Marieadded;NikeroIslandretainsprovisionalexistingNikero,noverifiedEnglishspelling.
- 15samples2074_04..07/2073_05read. Requestedagent3natural因縁phrasing520:t_2:379 andspecific343cutreport. Chanted533:t_006:6 provisionalphoneticZetsu/In/A/Gou/Goku/Shuu basedKishukuritualwiki; no invented亜meaning; voiceunverified.
- 11samples2073_06/2074_08/2075_00/2075_05read. RequestedOzmaDynamiteExplosionpun naturalpredicate; agent4preservesKurzmisquote(adore)vsAlcorrectlove; dimensionalcageplainconsistent across6sourceoccurrences; Siberiatokenadded.
- 10samples2073_07/2075_01/2075_06/2076_00read; RostinaenumerationandKallencrossrowthoughtretainedappropriately, no sampleddefects.
- 12samples2075_02..03/2076_01..02read; Theo712thPopeidentificationandWisemanrevivalpreserved, no sampleddefects.
- 39samples2073_08..09/2074_00/2075_04/2076_03..05/2077_00..02read. Agent4eventreport532:t_2:229needsverb(requested). LiteralProtoPleTwelvewillfulltoken. SourcesexualdetailKurzMao544:t_1:45preserved. Requestedagent3secondopinionQueenidentity503:t_004:4 andMaridaunnamedcaregiver502:t_10:14..18.
- Final6samplesagent5read; requested544:t_2:179missingpredicate and544:t_2:265fullsecondquestion. Sousuke544:t_2:43contextverifiedgenuinehesitationtosaviorclaim.
- Agent3read-onlysecondopinionandparentcitedsourcereview:503:t_004:4queenstronglyRelena, fromGuin's502:t_1:35/49/66QueenRelenatitle; keepcurrentplainqueen(lowercaseordinarythirdpersontitle), noidentityreplacement. 502:t_10:14..18unnamedcaregiverstronglyAlbertofrom502:t_3:49..51/59..61,selfmale68; retainmalepronounsbutnotexplicitname. Existingd.NAME_SKIPQueen=NoneprotectstitlesfromChronoaliasnormalization.
- Agent6initial6samples2077_05..06read; requested544:t_3:14Almost->fullpredicate and16accompanimentpromise, basedneighbors.
- Agent6samples2077_07..08readfaithful; exactphoneticサガラ・ソウスケ545:t_003:5usesexistingfull相良宗介tokenaftercontextverification.
- 4samples2077_09..10readfaithful; Kurzretainsrejectionofdehumanizingsniperideal.
- 6samples2078_00..01read; requested550:t_1:98explanatorypredicateafterInotherwords.
- Final coordinator sampling covered all81 slices. Caption audit found69 captions with0 layout differences; source-name collision audit found0 candidates before normalization. XL-2, full XL-3 booster and XL-3 exact designations added after Bandai/source review. Existing Ed Bruiser Sachs token retained; no duplicate name created.
- All six translators confirmed EDITS STOPPED. Agent6 final57 cuts/4 notes reviewed:550:t_4:10 explicitly says kare, supporting him for unnamed helper without invented identity. Restored full predicates544:t_3:14/16,550:t_1:98; agent5 repaired544:t_1:11 after source review. Name dry run exposed Prince Freedom as Kira nickname rather than Freedom machine; researched full nickname token added, so final seven normalizations preserve identity.

Official is the existing glossary category, including wiki-supported forms; licensed localization is not implied. Proposed terms remain provisional.
