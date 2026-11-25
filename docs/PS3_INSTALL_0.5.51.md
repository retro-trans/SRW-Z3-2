# PS3 0.5.51 — RPCS3 installation

The [combined release](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.1.4)
includes PS3 **0.5.51** and Vita/Vita3K **0.1.4**. Each platform keeps its own
build version. This PS3 delivery is for **RPCS3**, Japanese **BLJS10299**.
Physical PS3 compatibility is not claimed for this build.

## Choose the matching PS3 patch

| Your exact input ISO | Download |
| --- | --- |
| Original Japanese BLJS10299 | `SRW-Z3-2-PS3-English-0.5.51-from-original.xdelta` (204.2 MB) |
| Public English 0.5.44 | `SRW-Z3-2-PS3-English-0.5.51-from-0.5.44.xdelta` (21.4 MB) |

Download one patch. In
[Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), open
**Apply xdelta**, choose the matching source ISO and downloaded patch, and
write a new output ISO. Keep checksum verification enabled and preserve your
source. Use this local patch route for PS3 downloads hosted in this combined
release; the release's Automatic Vita entries are separate.

The Vita ZIPs do not patch a PS3 ISO. GitHub's automatic source-code ZIP is
project source, not a game patch.

## Exact image identities

- Original Japanese ISO: **4,888,199,168 bytes**;
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**;
  SHA-256 `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Output English 0.5.51 ISO: **5,289,738,240 bytes**;
  SHA-256 `ece8ec2f3ba945329d13bbf8170703f55b9896622990a04a99437698765fb0f9`.

Folder dumps or repacked ISOs are not substitutes for these inputs.
`PS3-BUILD-MANIFEST.json` records patch identities; `PS3-VALIDATION.json`
records both successful full-image decode round trips. Verify the PS3
downloads with `PS3-SHA256SUMS.txt`, or all platform downloads with
`SHA256SUMS-ALL.txt`. The original `SHA256SUMS.txt` covers the Vita delivery.

## Launch in RPCS3

1. Close RPCS3 and back up your installation and saves.
2. If `dev_hdd0/game/BLJS10299_DATA` exists, move that game's installation-data
   folder to a backup outside `dev_hdd0/game`. The game will reinstall the
   updated assets, including the keyword-popup archive. Preserve savedata,
   DLC licenses and other games. Never remove saved games as installation data.
3. Start RPCS3 with the generated 0.5.51 ISO. Fresh-boot the game and load an
   in-game save; do not resume an emulator state containing old assets.
4. Check **0.5.51** on the title screen. Report the version, stage, actions
   and screenshot if a problem occurs.

The base-game build includes the name, menu and stage-title fixes after
0.5.44, centers all 197 timed narration rows, and translates and aligns the
74-entry bonus-scenario menu category. It preserves the established font
preferences and glossary. Separate PS3 DLC packages are not included in this
addition; previously installed English DLC 0.5.49 is compatible.

The sealed image verifies all 82 files through both ISO directory trees.
The recorded regression ran 372 tests: 370 passed, two optional skips.
Both patch round trips produced the exact output hash above. Live gameplay
and a full story playthrough are separate from these file/native checks.
This is the unchanged verified RPCS3 build, without the later experimental
CFW wrapper or hardware voice diagnostics.

Build-source commit: `f157b772d46a139858f1f2ea61b89e2e07aa2707`.
Patches and metadata only; supply your own game image.
