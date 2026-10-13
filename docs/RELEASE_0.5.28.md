# 0.5.28 — Complete map defeat quotes

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. [Public playtest release](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.28);
in-game visual confirmation remains pending.

## Apply

In [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
**Refresh catalog**, select either your original Japanese ISO or the exact
public 0.5.18 ISO in **Automatic**, then select **Latest** (0.5.28).
Choose a new output ISO. Both routes produce the same verified image.

For manual patching, use **Apply xdelta** with the asset whose `from` version
matches your input. `BUILD-MANIFEST.json` records each exact input/output hash
and size; keep checksum checks enabled. Game images are not distributed.

- Original Japanese ISO: 4,888,199,168 bytes;
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Public 0.5.18 ISO: 5,284,429,824 bytes;
  SHA-256 `1139b7c2dbe8d7ce0de50e73f5480e2f2f19aff06b053a6855281e3772e34db4`.
- Patched 0.5.28 ISO: 5,288,361,984 bytes;
  SHA-256 `25cde8ca3973a4ab7196380b8bd75dde582d45e61832a5fb08927a8008bb3a24`.

## Included

- Translate all 23 assembled item-unlock conditions, all 24 D-Trader item
  announcements, and all nine selectable Full Upgrade Bonus confirmations.
- Repair both two-color Custom Bonus award headers and the matching Ace Bonus
  header, keeping their native font, colors, icons and row pitch.
- Translate all 35 trophy names/descriptions and the trophy-set title in both
  metadata variants. Preserve IDs, hidden flags, grades, triggers and all icons.
- Correct Heero Yuy and Crowe Bluest in the glossary, Library, executable
  names, dialogue token expansions and pilot surname pieces; preserve Yui Ikari.
- Center Raise Stats / Learn Skills in all four training tab states; separate
  Owned / Cost / Left from PP and restore readable six-stat / four-terrain labels.
- Fit all nine Z Crystal effect names, including Grade 5, before the unchanged
  numeric cost column; shorten its headings to Effect / Cost.
- Separate Z Crystal payment text from the live amount and align selected
  Yes / No words with their neutral row in every confirmation state.
- Fit all 23 tutorial selector titles into their two columns. Keep every
  tutorial body in its original row, with measured English widths and controls.
- Shorten Combat Record and Power Parts captions around unchanged numbers,
  names, arrows and category choices. Match both emblem footer caption paths.
- Use the game's original Latin fill and outline masks for the reported yellow
  labels, retaining their native color, baseline and row pitch.
- Translate the Power Parts formatter's separate Air / Ground / Water table;
  preserve all eight movement masks, separators, and both comparison columns.
- Relocate all 262 static mission conditions through ten-byte display keys,
  keeping complete English beyond the native UI's 128-byte intermediate field.
  Preserve the existing substitution route for all 25 live-name/counter conditions.
- Correct Sacks and Giltar throughout active name fields, Library and glossary
  expansions. Preserve the other user-selected canonical spellings.
- Fit deployment headers around the remaining count; translate all seven
  repeated movement templates and compact selection/movement captions.
- Translate assembled Clear Report Z-Chip and funds rows, remove their
  numeric padding, and retain live amounts. Center the three per-pilot PP rows.
- Separate Weapon and RANK in both upgrade list footers and shorten the
  right header. Preserve the upgrade values, bars, native colors and font masks.
- Fit deployment commands inside their buttons; shorten the team-count
  caption and suppress its redundant suffix around the unchanged number.
- Space and center all seven Gargantia fleet commander's room captions;
  preserve both blank rows and use their final expanded font widths.
- Correct Ameria in the active glossary and location captions, including
  all dialogue tokens that expand to that name.
- Separate both Team Setup headings from Next and its unchanged live count.
- Restore the normal font for Mao's Baal explanation using reviewed complete
  wording that fits three rows and retains its keyword link.
- Translate all 22 player-facing stage GIFT reports (97 occurrences), including
  Sub Order and D-Trader unlocks, item grants, AG bonuses and upgrade refunds.
- Translate composed skill levels, including Newtype Lv 2, without changing
  required levels, selection predicates or colors.
- Use an English space in the default Hibiki Kamishiro full name; keep custom
  name strings and savedata unchanged.
- Audit all 686 full weapon names and 606 list names against the sibling
  Jigoku project. Expand fitting abbreviations, including Radiant Wave Surger;
  retain seven width-bound forms and eight reviewed full-name meaning exceptions.
- Apply Zuul / Emperor Zuul throughout active names and expanded prose;
  preserve the unrelated Gundam Geara Zulu and Rozen Zulu names.
- Wrap all 800 dialogue records using the runtime team-name token with room
  for the six full-width cells of Z-BLUE. Preserve wording, links and controls.
- Translate all independent lines of the three map save confirmations,
  including Save complete / Continue playing, preserving save and choice behavior.
- Translate all 249 native map defeat-quote entries (178 distinct strings),
  including Nigel's quote and nonverbal entries. Preserve pilot selection and modes.
- Review all 176 verbal barks with speaker context; apply 21 meaning fixes and
  preserve retreats, bailout commands and interrupted sentences.

- Shorter Link question and PP bonus labels, preserving counts and totals.
- Default protagonist names translated in the independent mission-condition
  substitution routine; custom names, name order and saved bytes preserved.
- Compact Library Name caption, aligned SR Point award layers and a single
  highlighted bonus amount with its separate English prefix.
- English world-map domination caption; percentage digits and animation retained.
- English UI, menu/help wrapping and alignment, full Library descriptions,
  scenario chart, English title logo, retro-trans credit and version footer.
- All 197 narration records, 104 ordinary stage title variants, 83 terrain
  names, assembled Spirit targets and default-name mission conditions.
- Focus/Foc terminology, native outlined fonts, readable stat/training labels,
  compact Spirit indicators, and the enemy band's English slash between Fy and Di.
- Native caption fallback repair for stray kanji over names/blank labels.
- All 63,553 fresh dialogue records and 48,143
  battle-voice strings retained from the previous public release.

## Verification and compatibility

All 82 disc files passed both filesystem-tree checks. The final executable's
translation bindings, mission name substitution stores, reward captions,
domination atlas, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. The upgrade additions also pass 80 final
lookup cases, 23 native report compositions and nine native bonus questions;
the trophy pack passes complete text/structure/icon readback and SHA-1 checks.
Both patches passed complete ISO decode round trips and Retro Trans 0.5.4
release validation. Each reproduced the verified target image exactly.
All 262 static mission keys pass the native copier and final drawer lookup
checks; all 110 mission members pass complete archive readback. The 12
deployment edits preserve numeric fields and movement-cell spacing. The
expanded active-text audit confirms Sacks and Giltar without old spellings.
Twenty native Clear Report executions cover zero, ordinary and large
amounts, with row canaries and unchanged values. Eleven label edits and all
deployment command lookup variants pass final readback and measured bounds.
The reported Rescue Unit and Target Lock reports and complete Episode 11
SR condition pass final native lookup. All seven room captions and Mao's
normal-font row pass full stage-member readback and measured text bounds.
Both Team Setup header states preserve font settings and live counter text.
The expanded active-text audit rejects obsolete Amerria spellings.
The complete stage-report and composed skill lookup sets pass final execution
checks. All weapon-name pointers and widths pass archive readback. The default
name separator passes instruction tests with custom-name and null guards.
All runtime team-name dialogue members pass complete final archive readback;
all independent save-line keys pass final lookup execution. The shared Library
Name caption and all Library fields mentioning Zuul pass exact final readback.
The expanded active-text audit rejects obsolete Xul and Zul spellings.
All 249 native quote-state stores and all 249 RPW quote cells pass final
execution/readback checks. The real selector preserves pilot codes, its alias,
unknown-code behavior and sentinel. Every quote fits its native composition
buffer and speech panel. Original quote strings and consumer code are retained.

Regression suite: 287 passed, two optional checks skipped. Four focused
native-quote/audit checks passed after the audit serialization repair.
The meaning review records retained ambiguities, including Code: White's
existing inferred "save us" in an interrupted line; see UI_REVIEW28.md.


**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. The separately reported
malformed result-screen team name remains unresolved. Provisional wording and
battle-caption limitations remain recorded in the project reports.

Fresh-boot the new image and load an in-game save; emulator save states can
retain older code. Follow the prior release's installation-cache update notes
if RPCS3 continues to load old installed fonts/text. Preserve savedata.

Build sources: `b3485bbcb508106357b2b88d92eb209c65a210c5`. Release tool: Retro Trans **0.5.4**,
commit `8edfb2e1c0d0c74df67107d80803177cc5939079`. See CHANGELOG.md for individual fixes.
