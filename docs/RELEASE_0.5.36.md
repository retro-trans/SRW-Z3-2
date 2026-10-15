# 0.5.36 — Large Funds spacing, two-line news and carried UI repairs

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. Prepared locally; creating or publishing a GitHub release
requires the user's explicit consent for this version.

## Apply

Once published, in [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
**Refresh catalog**, select either your original Japanese ISO or the exact
public 0.5.28 ISO in **Automatic**, then select **Latest** (0.5.36).
Choose a new output ISO. Both routes produce the same verified image.

For manual patching, use **Apply xdelta** with the asset whose `from` version
matches your input. `BUILD-MANIFEST.json` records each exact input/output hash
and size; keep checksum checks enabled. Game images are not distributed.

- Original Japanese ISO: 4,888,199,168 bytes;
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Public 0.5.28 ISO: 5,288,361,984 bytes;
  SHA-256 `25cde8ca3973a4ab7196380b8bd75dde582d45e61832a5fb08927a8008bb3a24`.
- Patched 0.5.36 ISO: 5,289,541,632 bytes;
  SHA-256 `ba9f823799e3d392d5215ec70765ddcd79a037fb7fa4c487187432c992af1d63`.

## What changed since last version

Compared with public **0.5.28**, the previous public release:

- Correct the two Spirit names to the requested Z3 convention: Break ignores
  defensive abilities; Fury guarantees critical hits. Update their compact
  indicators, bonus descriptions and related trophy text.
- Use Inazuma Kick in weapon names, glossary references and battle captions.
- Fix victory and defeat conditions showing internal keys such as 条件１７１.
  Cover all 262 static conditions in all three numbered slots and the
  unnumbered state, across every chapter. Preserve colors and gameplay logic.
- Fit numbered condition text with room for the number and continuation indent.
- Prevent live-name/counter condition truncation with native byte limits and
  room for expanded values. Keep every requirement in the shortened long SR
  condition, including each named pilot's individual shootdown quota.
- Translate the full skill-confirmation category: learning, level increases
  and overwriting an existing skill. Cover every skill name, not only E-Save.
- Translate every movement terrain combination, including numbered masks.
  Separate D-Trader's Move label from its live movement value.
- Fit D-Trader's part-stat labels, terrain heading and owned-item suffix around
  their fixed value fields, keeping the game's original label font.
- Normalize Earth Sphere capitalization throughout dialogue and encyclopedia text.
- Separate battleship selection, ship name, movement, pilot and remaining-unit
  headings from their neighboring columns and live count.
- Restore the complete Episode 20 and 21 SR conditions: no allied battleship
  damage within three turns; one allied pilot shoots down at least six enemies
  before clearing the map. Use separate native rows for every displayed line.
- Fit six additional SR explanations into the actual four-row slot. Keep all
  targets, turn limits, shootdown quotas, attack exceptions and ELS exclusions.
- Center all 517 location captions by their displayed English width, including
  Jindai High School / Old Building / Empty Classroom and Back Log views.
- Fit all eleven long or combined news headlines into two centered lines;
  preserve the complete Wrath Babylon assault-failure wording.
- Separate Sub Order labels from all three pilot counters and remove duplicate
  pilot-word fragments. Fit its guides and both Back Log guide variants around
  the controller icons. Clear Team Setup's movement brackets with MV labels.
- Translate all three native save questions before paragraph copying, including
  Save complete / Continue playing. Preserve save operations and Yes / No.
- Translate every separately drawn reward-report line, including all AG
  bonus amounts, awards, upgrade refunds and unlock notices. Center the English
  lines without changing rewards or stage logic.
- Correct Arm Rakers capitalization against the glossary. Clear Previous Quote
  and its R1 icon in both Back Log guide variants.
- Translate the full startup warning and all 20 Japanese copyright credit
  rows across both pages. Preserve every rights holder, year and production
  relationship, the existing English credits, logo screens and warning frame.
- Translate combined war-front updates after the game splits them into
  independently drawn lines: all 13 rows across six messages, including the
  East Asia / eastern North America and Midway / southern Europe updates.
  Center each English row and retain the final three-line worldwide report,
  all route occurrences and the captured-base counts.
- Separate Funds from the full eight-digit amount in all three intermission
  footer layouts. Preserve the existing font, colors, numeric field and the
  99,999,999 cap. Retain the centered two-line Central Asia disruption update.



## Verification and compatibility

All 82 disc files passed both filesystem-tree checks. The final executable's
translation bindings, mission name substitution stores, reward captions,
domination atlas, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. The upgrade additions also pass 80 final
lookup cases, 23 native report compositions and nine native bonus questions;
the trophy pack passes complete text/structure/icon readback and SHA-1 checks.
Each patch receives a complete ISO decode
round trip and Retro Trans 0.5.4 release validation before publication.
All 1,048 native condition compositions pass the real drawer lookup after
numbering, with row canaries intact. Another 200 cases execute live substitution
then numbering with default and maximum-size values. All 129 Spirit fields, every full/list
Inazuma Kick weapon occurrence and its battle captions pass final readback.
The earlier death-quote, mission, name and UI repairs remain covered by the
carried checks. No in-game visual verification is claimed.
Every new skill/movement draw key passes final lookup; the native learning
composer is exercised for every skill and both source/translated name routes.
All nine changed widgets pass final text/coordinate readback and column bounds.
The four corrected dialogue rows and twelve encyclopedia fields pass archive readback.
All 101 distinct SR conditions pass 210 executions of the complete native
four-row panel, with both color states and default/maximum live values. The
reported phases and all compiled SR literals pass final archive/drawer readback.
All six former row overruns are reproduced by the regression test and repaired.
539 executions verify the caption/news origin helper, full text, font widths
and caller state. All changed guides pass final archive/bounds checks. Native
save paragraph copying and both converter models preserve every English line.
The complete movement-mask translations remain covered by the carried checks.
All 22 player-facing reports (97 source occurrences) pass native paragraph
copying and final translation lookup; all 36 whole/line keys pass native centering.
The corrected Arm Rakers dialogue passes compiled archive readback.
All 22 war-front messages pass actual native 128-byte paragraph copying and
final translation lookup. All 13 previously missed rows pass native centering
at both tested font sizes (26 origin cases). The startup/font archive remains
byte-identical to verified 0.5.34; its three English startup screens are retained.
The three Funds x coordinates pass canonical UI readback and byte isolation.
Twelve native cap/digit/alignment cases cover zero, every digit boundary,
the reported amount, the maximum and oversized inputs. The reported Central
Asia headline passes final lookup and both centering sizes. The executable,
fonts, stage wrapper and all other game files are byte-identical to verified
0.5.35; its full regression/native evidence is carried by matching hashes.


**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. The separately reported
malformed result-screen team name remains unresolved. Provisional wording and
battle-caption limitations remain recorded in the project reports.

Fresh-boot the new image and load an in-game save; emulator save states can
retain older code. Follow the prior release's installation-cache update notes
if RPCS3 continues to load old installed fonts/text. Preserve savedata.

Build sources: `c411e8022d8bce0dc7edf3b2169cf1ba2300f7b6`. Release tool: Retro Trans **0.5.4**,
commit `8edfb2e1c0d0c74df67107d80803177cc5939079`. See CHANGELOG.md for individual fixes.
