English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update fixes the linked-keyword description window still displaying
Japanese in 0.5.40, including Messenger and Meganoid.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.40** ISO, and choose **Latest (0.5.41)**. Write a
new output image and keep your source. These instructions apply once the
prepared release is published and its catalog refresh is verified.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.41-from-original.xdelta` |
| Exact English 0.5.40 | `SRW-Z3-2-PS3-English-0.5.41-from-0.5.40.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.41-from-original.xdelta" "Tengoku-hen-English-0.5.41.iso"
```

Use the patch matching your input version and keep checksum checks enabled.
`BUILD-MANIFEST.json` lists exact identities; folder dumps and repacked images
are not substitutes for these ISO inputs.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.40 ISO: **5,289,541,632 bytes**, SHA-256
  `f80b9be177a4040b92488b745c9594906b2794ffa746787334a0eed974066fe4`.
- Patched 0.5.41 ISO: **5,289,607,168 bytes**, SHA-256
  `34c53111145196f8c8a86cf660fca989bab209758822b08e6e5a0da1bea37686`.

Both patches passed complete ISO decode round trips and reproduced the exact
target hash above. `SHA256SUMS.txt` verifies the downloads; `VALIDATION.json`
records the successful round trips. Official Retro Trans **0.5.4** release
validation passed for all five delivery assets. Downloads are **204.2 MB**
from original or **126.8 KB** from 0.5.40. Publication and live catalog
verification are pending.

### What changed since 0.5.40

- **Linked-keyword popups:** translates all **143 entries**, including both
  description variants (**286 descriptions**), in the separate archive this
  screen actually loads. This includes Messenger, Meganoid, Avalon and NERV.
- **Complete English prose:** wraps the existing reviewed translations and
  expands the text pool. Preserves lookup names, series, entry order, IDs and
  flags so keyword links continue to identify the same entries.
- **Corrected coverage check:** checks the actual deployed popup archive.
  Earlier checks covered the Library archive and executable dictionary but
  missed this third copy; they did not prove the popup was translated.

All other 0.5.40 game assets are retained, apart from the title version stamp.
The earlier font, Back Log, selection and mission-condition fixes remain.

The old bug was confirmed by read-only live inspection: all 143 popup records
and 572 fields matched the unchanged Japanese archive. The corrected archive
passes complete record and compressed-file readback. Sixteen focused checks
pass; all 82 ISO files are verified through both filesystem trees. Matching
parent-asset hashes retain earlier regression evidence. In-game visual
confirmation of **0.5.41** remains pending.

### RPCS3 compatibility

**RPCS3 only.** Physical PS3 and Vita support is not claimed.

Close RPCS3 and back up your installation before updating. Move only
`dev_hdd0/game/BLJS10299_DATA`, if present, to a backup outside `dev_hdd0/game`
so the game reinstalls the corrected popup archive. Preserve savedata and
other games. Fresh-boot the new image and load an in-game save; emulator
save states can retain the old Japanese popup data.

Test several keyword links, their scrolling and both description variants.
Include the build number and a screenshot with reports.

### What's included

English story dialogue, battle captions, pilot/mech/weapon text, Library and
keyword descriptions, and translated menu, skill, Spirit and mission-condition
text. Coverage does not establish that every screen is translated or fully
proofread. The malformed result-screen team name and provisional wording and
battle-caption limits remain recorded. No Vita package is included.

### How it was translated

AI-assisted drafts are checked against the glossary, edited and revised with
playtesting feedback. This update uses the existing English descriptions;
the correction delivers them to the missed popup data source.

### Acknowledgements

Thanks to the playtesters reporting missing text and providing screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the game patches. GitHub's automatic source archives
contain project sources and documentation, not an ISO. Source-dependent tools
require locally supplied game data. Build-source commit: `9de7c2b39653e08b99f1e5eeb7532265ac83507e`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
