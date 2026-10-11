# 0.5.18 — Accumulated UI and translation fixes (RPCS3 playtest)

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. This public release includes the fixes previously supplied as
local builds 0.5.3–0.5.17 and the enemy Spirit band separator repair.

## Apply

In [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), choose
**Refresh catalog**, select either your original Japanese ISO or the exact
public 0.5.2 ISO in **Automatic**, then select **Latest** (0.5.18).
Choose a new output ISO. Both routes produce the same verified image.

For manual patching, use **Apply xdelta** with the asset whose `from` version
matches your input. `BUILD-MANIFEST.json` records each exact input/output hash
and size; keep checksum checks enabled. Game images are not distributed.

- Original Japanese ISO: 4,888,199,168 bytes;
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Public 0.5.2 ISO: 5,282,922,496 bytes;
  SHA-256 `3351402913f80937bcf373acd4bdb26fcf1c04ac0dba03be4cedfffca51aca2b`.
- Patched 0.5.18 ISO: 5,284,429,824 bytes;
  SHA-256 `1139b7c2dbe8d7ce0de50e73f5480e2f2f19aff06b053a6855281e3772e34db4`.

## Included

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
translation bindings, Spirit band geometry, name drawer, fonts and stat widths
passed readback/execution checks. Each patch receives a complete ISO decode
round trip and Retro Trans 0.5.4 release validation before publication.

**RPCS3 only.** Physical PS3/Vita compatibility is not claimed. In-game visual
confirmation of this exact build remains pending. Provisional wording and
battle-caption limitations remain recorded in the project reports.

Fresh-boot the new image and load an in-game save; emulator save states can
retain older code. Follow the prior release's installation-cache update notes
if RPCS3 continues to load old installed fonts/text. Preserve savedata.

Build sources: `f620443075739b2e7c58af5e8044142f29d44b9c`. Release tool: Retro Trans **0.5.4**,
commit `8edfb2e1c0d0c74df67107d80803177cc5939079`. See CHANGELOG.md for individual fixes.
