English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on PS3
(**BLJS10299**, Japanese retail). This is an **RPCS3 playtest release**.

This update addresses the mission-condition, menu, font and Back Log problems
reported during playtesting, together with missing translations in several
message categories.

### Apply

Start [Retro Trans](https://github.com/retro-trans/retro-trans-tools), open
**Automatic** and select **Refresh catalog**. Select your original Japanese ISO
or the exact English **0.5.28** ISO, choose **Latest (0.5.40)** and write to a
new output file. Keep your source image. Older supported public versions can
use the catalog's upgrade chain.

For manual patching, use Retro Trans's **Apply xdelta** tab,
[DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) or
[xdelta3](https://github.com/jmacd/xdelta):

| Your source image | Patch |
| --- | --- |
| Original Japanese PS3 release, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.40-from-original.xdelta` |
| Exact English 0.5.28 | `SRW-Z3-2-PS3-English-0.5.40-from-0.5.28.xdelta` |

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.40-from-original.xdelta" "Tengoku-hen-English-0.5.40.iso"
```

Match the patch to its listed input. If validation fails, check the input
identity in `BUILD-MANIFEST.json` and leave checksum verification enabled.
Extracted folders, repacked images, other game editions and locally prepared
0.5.29–0.5.39 builds are not inputs for the 0.5.28 upgrade patch.

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.28 ISO: **5,288,361,984 bytes**, SHA-256
  `25cde8ca3973a4ab7196380b8bd75dde582d45e61832a5fb08927a8008bb3a24`.
- Patched 0.5.40 ISO: **5,289,541,632 bytes**, SHA-256
  `f80b9be177a4040b92488b745c9594906b2794ffa746787334a0eed974066fe4`.

`BUILD-MANIFEST.json` lists the input, output and patch identities.
`SHA256SUMS.txt` covers the protocol downloads; `VALIDATION.json` records
successful complete-image patch round trips. Both patches reproduced the
same target ISO. Downloads are **204.4 MB** from original or **24.0 MB** from
0.5.28. Hosted asset digests and both live Automatic catalog routes were
verified; patch building and catalog checks used Retro Trans **0.5.4**.

### What changed since 0.5.28

- **Spirit names and terminology:** uses Break for the command that bypasses
  defensive abilities, Fury for guaranteed critical hits, and Inazuma Kick
  throughout the affected weapon text and references. Corrects Arm Rakers
  capitalization and standardizes Earth Sphere in dialogue and encyclopedia text.
- **Mission conditions:** fixes internal condition IDs appearing instead of
  English text, including numbered and live-name/counter variants. Restores the
  complete Episode 20 and 21 SR requirements and fits six other long SR
  explanations into their panels, retaining quotas, deadlines and exceptions.
- **Missing message categories:** translates skill-learning, level-increase and
  overwrite questions; every movement-terrain combination; all three save
  questions; and the full reward-report category, including AG bonuses,
  upgrade refunds and unlock notices.
- **Location and news captions:** centers all 517 location captions, including
  their Back Log display. Splits eleven long or combined news headlines into
  two centered lines. Connects the separately drawn war-front reports,
  preserving their full wording and captured-base counts.
- **Menu layout:** separates D-Trader labels from their values, battleship
  headings from their columns, Sub Order labels from pilot counters and Back
  Log guides from controller icons. Uses compact Team Setup movement labels.
  Keeps Funds clear of the full eight-digit amount in all three intermission
  footer layouts.
- **Back Log:** expands the entry and row buffers to prevent truncated font
  codes from producing stray kanji. Preserves complete dialogue and fixes the
  Previous Quote guide overlap.
- **Font styles:** removes the added outline from dialogue, narration, names
  and ordinary text while retaining their current letter shapes and spacing.
  Selected yellow labels use a separate alphabet copied from the original
  font, with its thinner border. Original PP and Next-Lv lettering is retained.
- **Selection consistency:** displays Allies / Enemies identically in both
  map-menu states. Centers Spirit and Skills before either Search tab state
  is drawn, matching the existing Abilities treatment.
- **Startup screens:** translates the warning and twenty Japanese copyright
  credit rows across both pages, preserving rights holders, years and the
  existing English credits.

The earlier dialogue, battle-caption, name, Library and UI work is retained.
The version identifies a new build; it does not indicate a translation
completion percentage.

All **82 disc files** passed checks in both filesystem trees. The current
eleven focused checks passed, alongside twelve native tab-positioning cases.
Matching parent-asset hashes retain the earlier twelve selector/UI checks and
full regression result of **324 passes and two optional skips**. Additional
native checks cover condition composition, complete Back Log entries, caption
centering and the separate font styles. These checks do not replace gameplay
confirmation of this exact build.

### RPCS3 compatibility

**RPCS3 only.** This Tengoku build does not claim physical PS3 or Vita support.
The PS3/Vita compatibility statements for Jigoku-hen do not apply to it.

Close RPCS3 and back up your installation before updating. If present, move
only the `dev_hdd0/game/BLJS10299_DATA` installation-cache folder to a backup
outside `dev_hdd0/game`, allowing the game to reinstall matching fonts and
battle text. Preserve savedata and other games. Boot the new image from the
start and load an in-game save; an emulator save state can retain old resources.

Earlier public versions supplied the screenshots behind these repairs. The
new fixes still need live testing, especially selection transitions, Back Log
scrolling, long SR conditions and caption placement. Reports should include
the build number and a screenshot.

### What's included

English story dialogue covering **63,553 records**, including alternate routes,
endings, ace talks and previews, together with battle captions, pilot/mech/weapon
text, glossary and Library entries, and translated menu, skill, Spirit and
mission-condition text.

Coverage checks do not establish that every screen is translated or fully
proofread. The reported malformed result-screen team name remains unresolved.
Provisional wording, name readings and battle-caption layout limits remain
documented in the project reports. No Vita package is included.

### How it was translated

AI-assisted drafts were checked against the project glossary, edited and
revised using playtesting reports. Research and community references inform
names and terminology. Corrections and contextual proofreading are welcome.

### Acknowledgements

Thanks to the playtesters who supplied screenshots, reported missing text and
checked the public builds, and to the community references supporting the
terminology research.

### Source code

Use the matching `.xdelta` release asset to patch your game. GitHub's automatic
source archives contain project sources and documentation, not a patched ISO.
Game dumps, extracted assets and Japanese script dumps are not included;
source-dependent tools require locally supplied game data.

The manifest records build-source commit
`41d15b841f7ef7f592468977b45b60b99c6d47c6`. The release tag also includes later
release documentation. The build used Retro Trans **0.5.4**, commit
`8edfb2e1c0d0c74df67107d80803177cc5939079`.

### Contribute

Send bug reports, proofreading corrections and playtesting feedback through
the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues) or the
project community:

**[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**

---

Only patches and release metadata are distributed. Supply your own game image.
