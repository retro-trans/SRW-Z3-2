# Fresh retranslation: stages 49–58

Completed **6,828 records in 91 slices**, using six GPT-6.1 Sol agents at medium reasoning in two waves of three.

Scope: stages 49-58 on route A: common 49-51, Getter 52-54, common 55-56, hope 57, common 58, and 2250/2251 choice scenes. This continues the previous batch’s route A.

| Agent | Examined / assigned | Slices | Validation |
| --- | ---: | ---: | --- |
| 1 | 1102 / 1102 | 14 | PASS |
| 2 | 1185 / 1185 | 17 | PASS |
| 3 | 1120 / 1120 | 15 | PASS |
| 4 | 1113 / 1113 | 14 | PASS |
| 5 | 1121 / 1121 | 15 | PASS |
| 6 | 1187 / 1187 | 16 | PASS |

All assigned IDs and source fingerprints match. Speaker headers, control-code counts, keyword-link counts and text format pass. No untranslated rows or unknown glossary tokens remain. Measured three-line limits pass.

All 91 active prior translation files and their archived copies match their starting hashes. The glossary has 18 appended entries and 0 explicitly reviewed existing-term corrections; all other existing entries are unchanged. Coordinator normalization changed 82 rows; the original agent outputs remain in `before_name_pass/`.

The fresh draft is in `drafts/`; `prior/` preserves the previous project draft. `review_notes.json` collects the agents’ context decisions, retained omissions and uncertainties. `coordinator_changes.json` records exact row edits; `validation.log` records the final checks.

Coordinator meaning review covered samples and flagged issues, not a second independent proofread of every row. Proposed terminology and interpretation notes remain reviewable. No new Japanese dialogue dumps were created. The fresh draft has not been promoted, built, deployed or checked in-game.

## Coordinator source sampling and editorial review

Reviewed 262 source/English samples across all 91 slices, with neighboring context for flagged questions. This is not a second full independent proofread.

- 628:t_1:12: requested authoritative lowercase dimensional-power token.
- 634:t_4:25: requested explicit subject and verb in Felt's confirmation report.
- 641:t_018:4: preceding three El Millenium arrivals confirm plural referent; no change.
- 658:t_2:8-9: adjacent continuation supplies the main predicate; cross-row sentence preserved.
- 659:t_021:0: requested complete predicate in Shinji's battle report.
- 635:t_047:3: Banagher identifies Setsuna's voice immediately before; he is a supported referent.
- 659:t_112:3: requested explicit enemy subject for taking lives; corrected dangling modifier and matching branch variants.
- 628:t_3:57: source name is interrupted hiragana Ai...kun; existing Ai-kun token identifies Ranka's pet without gender inference.
- 634:t_1:78-80: source sentence spans Feldt's intervening reaction; English retains the cross-row completion.
- 640:t_1:115/119: source itself alternates Year 3 and Year 2 for Class 4; retained both numbers and the agent's continuity warning.
- 641:t_016:52: genetic-fear context supports blood metaphor; preserve agent's uncertainty about an eventual settled lore term.
- 683:t_056:2: requested a full predicate for Heero's mission acknowledgement under the project's strict pro-drop rule.
- 682:t_2:98: requested connecting Nicola's explanatory complement to its main clause instead of an artificial sentence fragment.
- 682:t_4:22: requested an explicit copula in Nono's identification of Jung as first Galactic Federation president.
- 688:t_2:9: requested lowercase dimensional-power token in running speech.
- 689:t_039:4-6: requested full question predicate; Suzune asks about the origin of Maki's love, not when it began. White's answer deliberately continues across two rows.
- 688:t_10:39: research identifies O-Kon as Tria's fox mask, not a nickname for Tria; use object reference and provisional romanization.
- 688:t_10:34: requested explicit copula in Tsine's praise of Tria.
- 701:t_100:2: prior Vildark question asks whether Kappei is his equal, confirming comparative stronger than you; no change.
- 701:t_115:6: requested connecting Vildark's power description to its predicate instead of an artificial second sentence fragment.
- 718:t_1:8-12: checked 120 million years versus 12,000 years in adjacent lore lines; distinct time references are preserved.
- 701:t_114:0 and701:t_137:8: name-pass preview caught Mechanical Angel matching the unrelated Angels term and generic messenger matching Gargantia's occupation; excluded both tokenizations.
- 629:t_006:30/007:31: after checking all five source occurrences, normalized Superdimensional Cinderella to the existing Super-Dimensional Cinderella glossary token.
- 640:t_1:186: name-pass preview exposed a verbless location reply; requested explicit subject/copula from the translator before normalization.

Official is the existing glossary category, including wiki-supported spellings; it does not assert licensed English localization. Proposed terms remain provisional.

## Subsequent identity correction — 2026-10-09

Corrected 2 Patrick tokens to the newly disambiguated Colasour entry; visible English is unchanged. See `post_review_corrections.json` for exact rows and evidence. Manifest hashes updated; initial review counts above describe the original completion pass.

## Darlian identity correction — 2026-10-09

Corrected 2 Darlian tokens to the Relena entry. Visible English is unchanged; exact edits are in `post_review_corrections.json`, with manifest hashes refreshed. Original completion counts above are historical.

## Generic Invader identity correction — 2026-10-09

Corrected 14 generic-species tokens; boss-specific references remain unchanged. Visible English unchanged; exact edits in `post_review_corrections.json`, manifest hashes refreshed. Original completion counts above are historical.

## Caption layout corrections - 2026-10-09

Restored 13 captions to source field separators and line layout. Exact before/after edits are in post_review_corrections.json; manifest hashes refreshed. Original completion counts remain historical. Active/prior/before_name_pass files unchanged.

Source-reviewed grammar correction 628:t_1:51: Agent10_1 source+8neighbors review: Heero acknowledges Nunnally; restore settled subject and verb. Zero is Lelouch. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed terminology correction 652:t_1:48: Whole-corpus exact Japanese review; apply batch11 researched Queen of Roses / Fold Wave terminology, retaining plural suffix. Original source and prior snapshots preserved. Agent11_3 independently read source plus eight neighbors and proposed this full-subject-and-verb praise; parent reviewed. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed terminology correction 652:t_1:18: Whole-corpus exact Japanese review; apply batch11 researched Queen of Roses / Fold Wave terminology, retaining plural suffix. Original source and prior snapshots preserved. Exact edit is in post_review_corrections.json; hash refreshed.

Source-reviewed terminology correction 658:t_2:8: Whole-corpus exact Japanese review; apply batch11 researched Queen of Roses / Fold Wave terminology, retaining plural suffix. Original source and prior snapshots preserved. Exact edit is in post_review_corrections.json; hash refreshed.

Adnachiel full name correction 701:t_014:3: Both exact corpus occurrences reviewed with source and neighbors. Normalize full researched Adnachiel the General baptismal name; no English meaning change. See post_review_corrections.json; hash refreshed.
