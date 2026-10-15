English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). **RPCS3 playtest build.**

This update translates missed deployment terrain rows, separates crowded
deployment labels, corrects Psyco Waves, and fits/translates war-front reports.
It also includes the linked-keyword popup fix prepared after 0.5.40.

### Apply

In [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic**, choose **Refresh catalog**, select your original Japanese ISO
or the exact English **0.5.40** ISO, and choose **Latest (0.5.42)**. Write a
new output image and keep your source. These instructions apply once the
prepared release is published and its catalog refresh is verified.

Manual patching also works through **Apply xdelta**,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.42-from-original.xdelta` |
| Exact English 0.5.40 | `SRW-Z3-2-PS3-English-0.5.42-from-0.5.40.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.42-from-original.xdelta" "Tengoku-hen-English-0.5.42.iso"
```

Use the patch matching your input version and keep checksum checks enabled.
`BUILD-MANIFEST.json` lists exact identities; folder dumps and repacked images
are not substitutes for these ISO inputs.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.40 ISO: **5,289,541,632 bytes**, SHA-256
  `f80b9be177a4040b92488b745c9594906b2794ffa746787334a0eed974066fe4`.
- Patched 0.5.42 ISO: **5,289,607,168 bytes**, SHA-256
  `1d081d3d00f033ec907fd342bcca0143570aa097d9c0a78bc3206b4ed01639f9`.

Both patches passed complete ISO decode round trips and reproduced the exact
target hash above. Official Retro Trans **0.5.4** validation passed for all
five delivery assets. Downloads are **204.2 MB** from original or **21.3 MB**
from 0.5.40. `SHA256SUMS.txt` verifies the downloads; `VALIDATION.json` records
the successful round trips. Publication and live catalog verification remain
pending.

### What changed since 0.5.40

- **Deployment:** translates seven missed movement-type blocks (45 terrain
  rows). Air, ground, water and underground use the existing compact cells.
  `Left:`, `Sel.` and `MV` clear the remaining count, Team heading and
  movement bracket/value.
- **Terminology:** uses the requested **Psyco Waves** spelling and capitalization
  for both glossary aliases and all eight active dialogue references.
- **War-front reports:** supplies the complete English paragraphs before the
  game splits them into rows. Covers 22 messages at 38 scenario bindings.
  The Northern Europe headline uses two centered lines; the South America
  and Pacific Rim report displays both English rows. All report rows fit.
- **Linked-keyword popups:** includes the separate popup archive correction
  prepared in 0.5.41. All 143 entries and both description variants are
  translated, including Messenger, Meganoid, Avalon and NERV.

The earlier font, Back Log, mission-condition and selection fixes remain.
Current letter shapes and spacing are retained; selected yellow captions use
the original thinner-bordered font. The font archive is identical to 0.5.40.

Checks read back every changed terrain row, all eight compiled terminology
references and all 286 popup descriptions. The real native row-copy code,
installed English lookup and centering helpers are exercised for the news
reports. The final ISO checks all 82 files through both filesystem trees.
`VALIDATION.json` records both complete patch round trips. In-game visual
confirmation of **0.5.42** remains pending.

The full regression run has **338 passing tests** and two optional skips;
the four focused deployment/news/terminology checks also pass without skips.

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
the correction delivers them to the missed popup data source. The terminology
change follows the user's explicit spelling preference.

### Acknowledgements

Thanks to the playtesters reporting missing text and providing screenshots,
and the community references supporting terminology research.

### Source code

The `.xdelta` assets are the game patches. GitHub's automatic source archives
contain project sources and documentation, not an ISO. Source-dependent tools
require locally supplied game data. Build-source commit: `d4e920deacf14f647905e12d3ea85b06715e1033`.

### Contribute

Report issues through the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues)
or **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

---

Patches and release metadata only; supply your own game image.
