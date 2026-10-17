English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update corrects **Lowen** and **Schlan**, translates D-Trader purchase
questions, aligns their Yes/No display and fits the **Sphere Act** command.
It includes the prepared Heralds, conversion-part, no-pilot display and other
screen-fitting corrections, plus **Chaos Caper**.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.44** ISO, and choose **Latest (0.5.47)** after this
prepared release is published and its catalog refresh is verified.
Write a new output image and keep your source.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.47-from-original.xdelta` |
| Exact English 0.5.44 | `SRW-Z3-2-PS3-English-0.5.47-from-0.5.44.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.47-from-original.xdelta" "Tengoku-hen-English-0.5.47.iso"
```

Keep checksum checks enabled. `BUILD-MANIFEST.json` lists exact input and
output identities; folder dumps and repacked images are not substitutes.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**, SHA-256
  `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Patched 0.5.47 ISO: **5,289,607,168 bytes**, SHA-256
  `7d8c0842d2a7f4602c160cf268c359fa62b4ed7e4da9b2d630213a80c4cf5359`.

Both routes must reconstruct this complete target image before delivery.
`SHA256SUMS.txt` verifies downloads and `VALIDATION.json` records complete
patch round trips. Preparation uses official Retro Trans **0.5.4**.
Publication and live catalog verification remain pending.

### What changed since 0.5.44

- **Names:** uses Lowen and Schlan in linked dialogue, their full-name aliases,
  the Library and keyword popups. These spellings are protected for proofreading.
- **D-Trader:** translates the full purchase sentence, including the live item
  name, for all 78 Power Part records. Both original and already translated
  names are supported. The separate confirmation question remains in English.
- **Yes/No:** stores explicit English with matching grey and selected-word
  positions in all generic question states, retaining native colors and input.
- **Sphere command:** uses `Sphere Act` inside the existing button. Descriptive
  ability text keeps the full wording.
- **Heralds:** uses Herald / Heralds for the original faction. Evangelion
  Angels, Aquarion Shadow Angels, the pilot Angel and Tenshi remain distinct.
- **Empty-pilot display:** corrects fallback-name encoding while preserving
  live pilot names and all unit stats.
- **Conversion parts:** fits `Emerg. Deploy Booster`, `Light Config.` and
  `Assault Config.` in the selected-name boxes and lists.
- **Fundraising / Unit Stats:** fits `Funds`, its remaining-pilot caption,
  and the status indicator `Ability Active`.
- **D-Commands:** removes retained bullet glyphs from all six labels using
  invisible spacing. Keep Combo's full effect fits its two footer rows.
- **Location caption:** splits Wrath Babylon Imperial Palace and Spirit
  Quanta Absorption System into two centered, portrait-safe lines.
- **Power parts:** uses `Hyperdim. Target Lock` to clear the stock counts.
- **Narration:** keeps every word of the project-contribution sentence using
  the existing narrower alphabet for that timed row.
- **Terminology:** preserves **Chaos Caper**, Colony Laser and Psyco Waves.

Readback verifies all 156 purchase lookup keys and 156 cases through the real
purchase constructor, 316 native purchase/Sphere caption centers,
24 choice-origin cases, all 4,803 widgets and
3 affected dialogue records. Changed Library entries,
actual keyword popup data and native keyword consumers are checked.
Font pages, allocation and letter advances are unchanged. Both ISO filesystem
trees verify all 82 files. The full regression run passes **353 tests**,
with **1** optional check skipped. In-game visual confirmation remains pending.

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Close RPCS3 and back up your installation before updating. Move only
`dev_hdd0/game/BLJS10299_DATA`, if present, to a backup outside
`dev_hdd0/game` so the game reinstalls the updated assets, including the
keyword-popup archive. Preserve savedata and other games. Fresh-boot the
new image and load an in-game save; emulator save states can retain old text.

Test both choices in the D-Trader purchase question, the Sphere command and
the reported Lowen / Schlan dialogue. Also check the carried Heralds,
no-pilot, conversion-part, fundraising and ability-indicator corrections.
Include the build number and screenshots in reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary and revised with playtest
feedback. This update follows the requested character names and translates
the complete assembled purchase message without changing item effects or fonts.

### Acknowledgements

Thanks to the playtesters reporting missing text and supplying screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the patches. GitHub's automatic source archives contain
project sources and documentation, not an ISO. Source-dependent tools require
locally supplied game data. Build-source commit: `db3c2f6987acf83153b449145a285d8a5bd446d5`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
