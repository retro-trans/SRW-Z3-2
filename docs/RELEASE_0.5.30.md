# 0.5.30 — Skill questions, D-Trader and battleship layout, Spirit and mission fixes

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. Prepared locally; creating or publishing a GitHub release
requires the user's explicit consent for this version.

## Apply

Once published, in [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
**Refresh catalog**, select either your original Japanese ISO or the exact
public 0.5.28 ISO in **Automatic**, then select **Latest** (0.5.30).
Choose a new output ISO. Both routes produce the same verified image.

For manual patching, use **Apply xdelta** with the asset whose `from` version
matches your input. `BUILD-MANIFEST.json` records each exact input/output hash
and size; keep checksum checks enabled. Game images are not distributed.

- Original Japanese ISO: 4,888,199,168 bytes;
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Public 0.5.28 ISO: 5,288,361,984 bytes;
  SHA-256 `25cde8ca3973a4ab7196380b8bd75dde582d45e61832a5fb08927a8008bb3a24`.
- Patched 0.5.30 ISO: 5,289,279,488 bytes;
  SHA-256 `57294ceeeb4b7d31250e88ef7c10c5b20bc7a3a30f553ed8d8a1cfd469d140e5`.

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



## Verification and compatibility

All 82 disc files passed both filesystem-tree checks. The final executable's
translation bindings, mission name substitution stores, reward captions,
domination atlas, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. The upgrade additions also pass 80 final
lookup cases, 23 native report compositions and nine native bonus questions;
the trophy pack passes complete text/structure/icon readback and SHA-1 checks.
Both patches passed complete ISO decode round trips and Retro Trans 0.5.4
release validation. All five delivery assets passed size/checksum readback.
The regression suite passed 301 checks with two optional checks skipped;
seven focused checks passed after the final skill-name-field correction.
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


**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. The separately reported
malformed result-screen team name remains unresolved. Provisional wording and
battle-caption limitations remain recorded in the project reports.

Fresh-boot the new image and load an in-game save; emulator save states can
retain older code. Follow the prior release's installation-cache update notes
if RPCS3 continues to load old installed fonts/text. Preserve savedata.

Build sources: `b66746a2b416f808a1ad085037ef8c422becd10f`. Release tool: Retro Trans **0.5.4**,
commit `8edfb2e1c0d0c74df67107d80803177cc5939079`. See CHANGELOG.md for individual fixes.
