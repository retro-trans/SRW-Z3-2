English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update fits D-Command labels and help, the palace location caption,
the long Target Lock part name and one timed narration row. It includes
the requested **Chaos Caper** spelling.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.44** ISO, and choose **Latest (0.5.45)** after this
prepared release is published and its catalog refresh is verified.
Write a new output image and keep your source.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.45-from-original.xdelta` |
| Exact English 0.5.44 | `SRW-Z3-2-PS3-English-0.5.45-from-0.5.44.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.45-from-original.xdelta" "Tengoku-hen-English-0.5.45.iso"
```

Keep checksum checks enabled. `BUILD-MANIFEST.json` lists exact input and
output identities; folder dumps and repacked images are not substitutes.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**, SHA-256
  `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Patched 0.5.45 ISO: **5,289,607,168 bytes**, SHA-256
  `bc1edfb8c1a38a9190834b5ea0bbc1887cf4c6fa1ca8e404e54fa250d22d8c7e`.

Both patches passed complete ISO reconstruction checks and reproduced the
exact target checksum above. Official Retro Trans **0.5.4** validated all five
delivery assets. Downloads are **204.2 MB** from original or **21.0 MB** from
0.5.44. `SHA256SUMS.txt` verifies downloads and `VALIDATION.json` records both
successful round trips.
Publication and live catalog verification remain pending.

### What changed since 0.5.44

- **D-Commands:** removes retained bullet glyphs from all six labels using
  invisible spacing. Selected, preloaded and disabled labels retain their
  geometry and styles. Keep Combo's complete effect fits its two footer rows.
- **Location caption:** displays Wrath Babylon Imperial Palace and Spirit
  Quanta Absorption System on two centered lines, clear of the portrait.
- **Power parts:** uses `Hyperdim. Target Lock` so the name clears the stock
  counts. The part's effects, stats and counts are unchanged.
- **Narration:** retains every word of the reported project-contribution
  sentence and uses the existing narrower alphabet for that timed row.
  Its original timing and adjacent rows remain intact.
- **Terminology:** uses **Chaos Caper** in both dialogue references and
  confirms the spelling in the active glossary and glossary seed.

Ten installed lookups and 48 selected/preloaded command-origin cases pass.
The palace caption passes native centering at three sizes. All 4,803 widgets
retain their geometry and states; only the six-row command text changes.
Readback checks the changed script members, unchanged part stats, fonts and
other archive members. Both ISO filesystem trees verify all 82 files.
In-game visual confirmation of **0.5.45** remains pending.

The final regression run passed 347 tests, with one check skipped (348 total).

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Fresh-boot the new image and load an in-game save. Emulator save states can
retain older text. Back up your installation and savedata before updating.
When updating from a version older than 0.5.44, follow its cache-reinstall
instructions for the corrected keyword-popup archive; preserve savedata.

Test D-Command selection and help, the palace caption, Target Lock stock counts
and the reported narration. Include the build number and screenshots in reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary and revised with playtest
feedback. This update fits existing English without dropping the narration's
words or changing item effects. Chaos Caper follows the user's spelling.

### Acknowledgements

Thanks to the playtesters reporting missing text and supplying screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the patches. GitHub's automatic source archives contain
project sources and documentation, not an ISO. Source-dependent tools require
locally supplied game data. Build-source commit: `2e5f9491d15704f517a7c5ac65628b2b2af48a21`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
