# Library entries: Tengoku vs Jigoku

Generated 2026-09-29 by `python -m tools.library_compare --apply`.
Report: `work/glossary/library_jigoku_match.json` (ids, short names and
statuses only; no descriptions).

Jigoku's three `MTZKN_*.CPK` archives are copied read-only from the original
Jigoku ISO into ignored `work/jigoku_ref/` and hash-checked. Tengoku's come
from the verified extraction. Entry ids differ between the games, so entries
are paired by name, then by identical or similar (>= 0.6) description for
renamed entries. Each Jigoku entry pairs once; extra same-name Tengoku variants
share their closest Jigoku entry (`name_shared`).

## Result

| Status | Keyword | Pilot | Robot | Total |
|---|---:|---:|---:|---:|
| identical (every field) | 15 | 45 | 9 | 69 |
| same_description (only image/voice/pilot/series fields differ) | 0 | 91 | 133 | 224 |
| minor_edit (description similarity >= 0.9) | 6 | 51 | 26 | 83 |
| partly_rewritten (0.5 to 0.9) | 16 | 139 | 54 | 209 |
| rewritten (< 0.5) | 4 | 16 | 13 | 33 |
| new in Tengoku | 102 | 197 | 96 | 395 |
| **Tengoku entries** | 143 | 539 | 331 | 1,013 |
| Jigoku-only (not in Tengoku) | 100 | 74 | 33 | 207 |

All 618 paired entries have a Jigoku English description in
`E:/Projects/SRW Z3/translation/library/`, and the report records the Jigoku
English name where its glossary has one.

- 293 descriptions are unchanged: Jigoku's English text can be reused after
  a glossary check.
- Most edited descriptions keep Jigoku's text and add a paragraph about later
  events (pilots: in 101 of the 170 changed main descriptions, all of the
  Jigoku text survives and text is only added). Reuse the
  Jigoku English and translate only the changed part.
- Keywords are mostly new: Tengoku's glossary terms are story-specific.

## Review before reuse

- `name_changed: true` (10 entries): renamed or shortened names. Most are
  genuine (アマノ → オオタ・カズミ, ＤＥＭ → ＤＥＭコーポレーション), but
  アンゲロイＣＡＮ ← アンゲロイＧＥＭ is probably a different unit sharing a
  description template.
- `review_partial_name_jigoku_ids`: possible matches by partial name, never
  paired automatically. 法皇テオ８世 → テオ８世 is real; プラント / インプラント is not.
- `name_shared`: same-name variants (e.g. several ＥＬＳ or エヴァンゲリオン初号機
  entries). Check which form each one describes.
- Pairing is not identity review. The report keeps `identities_reviewed: false`.
