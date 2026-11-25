English translation patches for **Super Robot Taisen Z3: Tengoku-hen**:
**PS3 0.5.51 for RPCS3**, **physical Vita 0.1.4**, and **Vita3K 0.1.4**.

Choose the download for your platform below. Each platform retains its own
build number. This combined release adds the verified PS3 build matching the
Vita translation; the seven original Vita delivery files are unchanged.

### PS3 — RPCS3 0.5.51

Use [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools)
**Apply xdelta**, the matching source ISO and one patch below. Write a new
output ISO, preserve the source and keep checksum verification enabled.
Use this local patch route for the PS3 assets in this combined release.

| Your exact source | Download |
| --- | --- |
| Original Japanese PS3 ISO, BLJS10299 | `SRW-Z3-2-PS3-English-0.5.51-from-original.xdelta` (204.2 MB) |
| Public English 0.5.44 ISO | `SRW-Z3-2-PS3-English-0.5.51-from-0.5.44.xdelta` (21.4 MB) |

- Original Japanese ISO: **4,888,199,168 bytes**, SHA-256
  `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- English 0.5.44 ISO: **5,289,607,168 bytes**, SHA-256
  `80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.
- Output English 0.5.51 ISO: **5,289,738,240 bytes**, SHA-256
  `ece8ec2f3ba945329d13bbf8170703f55b9896622990a04a99437698765fb0f9`.

Both complete-image patch round trips reproduce that output. All 82 ISO
files were verified through both directory trees; the recorded regression
passed 370 tests with two optional skips. The delivered patches and all
three image identities were checked again against the sealed records.
`PS3-BUILD-MANIFEST.json` and `PS3-VALIDATION.json` record PS3 evidence.
`PS3-SHA256SUMS.txt` verifies the PS3 downloads; `SHA256SUMS-ALL.txt` covers
all platform downloads. The original `SHA256SUMS.txt` and `VALIDATION.json`
remain the Vita delivery records.

**Changes since public PS3 0.5.44:**

- Correct Lowen and Schlan, preserve Herald / Heralds and Chaos Caper, and
  remove unwanted separators in translated full pilot names.
- Translate every composed Tengoku stage heading, including
  **Final Episode: World Without End**.
- Translate purchase sentences and align Yes/No positions, weapon requirement
  warnings, conversion-part labels, fundraising and unit-status captions.
- Fit **Sphere Act**, D-Command labels, location captions and power-part names.
- Center all **197** timed narration rows, including the reported DLC narration.
- Translate and align the complete **74-entry** bonus-scenario menu category,
  including summaries, rules, native start/claim/purchase prompts and rewards.
- Retain the established fonts, spacing, glossary and earlier translation.

**RPCS3 only:** physical PS3 support is not claimed for this delivery.
Close RPCS3 and back up your installation. If `dev_hdd0/game/BLJS10299_DATA`
exists, move that game's installation-data folder to a backup outside
`dev_hdd0/game` so updated assets reinstall. Preserve savedata, DLC licenses
and other games. Fresh-boot the new ISO and use an in-game save instead of
an emulator state. Confirm **0.5.51** on the title screen.
See `README-PS3.txt` for complete instructions. Separate PS3 DLC packages are
not included; previously installed English DLC 0.5.49 is compatible.
Live gameplay and a full playthrough remain separate from the native/file checks.

PS3 build-source commit: `f157b772d46a139858f1f2ea61b89e2e07aa2707`.

### Vita and Vita3K — 0.1.4

This is the first public Vita release. It includes the physical Vita
first-battle correction confirmed by the tester, plus a separately verified
Vita3K delivery. The PS3 release remains on its own version sequence.

### Apply

Use [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools)
**0.5.19 or later**, your original Japanese PKG and its matching `work.bin`
or RIF. Keep the patch ZIP intact. In the **Vita** tab, select the matching
destination and ZIP as **Local patch**, then choose a new output.

| Target | Download | Install the generated output |
| --- | --- | --- |
| Physical Vita, rePatch | `SRW-Z3-Tengoku-v0.1.4-Vita-rePatch-patches.zip` (22.3 MB) | Copy the complete `rePatch/PCSG00494` folder to `ux0:/rePatch/PCSG00494` with VitaShell; launch the matching installed game with rePatch enabled. |
| Vita3K | `SRW-Z3-Tengoku-v0.1.4-Vita-PKG-patches.zip` (24.3 MB) | Use Vita3K **File → Install .pkg**, with the same matching license. |

Both downloads start from the original PKG, including upgrades from earlier
English builds. Back up saves and existing overlays, close the game, and
replace the complete older overlay. No separate auth dump is needed.
Confirm **v0.1.4** on the title screen.

The public Retro Trans catalog can discover both targets after refresh.
The local ZIP route also works. Full instructions are in `README-VITA.txt`.

Required original PKG:

- Content ID: `JP0700-PCSG00494_00-SRWZ3OF2DLGPKG00`.
- Size: **2,926,199,744 bytes**.
- SHA-256: `009833f3ecb46da08e50ad9d3cfc9772a2d74499f29960a6645d88235e78e7b0`.

`SHA256SUMS.txt` verifies the Vita downloads; `SHA256SUMS-ALL.txt` covers every platform. `VITA-PKG.json`, `VITA-REPATCH.json`
and `VALIDATION.json` record the exact source, patch and output identities.

### What changed since the last public version

The last public project release was **PS3 0.5.44**. This is a separate Vita
port carrying the prepared **PS3 0.5.51** English translation; local Vita
0.1.0–0.1.3 builds were not public releases.

- Port English dialogue, names, Library and keyword descriptions, menus,
  mission conditions, battle captions and adapted artwork to native Vita
  archives, fonts and ARM text rendering.
- Carry the intervening PS3 name/terminology, menu-fitting, timed-narration
  alignment and DLC-menu text/layout corrections. Vita DLC content is not included.
- Fix the physical Vita first-battle script stop and input lockout. Bind
  original immutable constants directly into 287 stage scripts and the
  shared battle helper, preserving dialogue and game commands. The user
  confirmed the correction works on **2026-11-25**.
- Include the earlier post-intro black-screen correction by preserving
  native compression choices, including directly loaded effect textures.
- Preserve all nine shared-script cache lengths and retain readable native
  error reporting. Ordinary letter shapes and spacing follow the established
  font preference; the added dialogue outline remains removed.

### Compatibility and validation

For the exact Japanese PCSG00494 v01.00 PKG above. The Vita files are unchanged by the PS3 addition. Use the separate PS3 downloads above for RPCS3.

- All **19** component deltas passed full decode round trips.
- The Vita3K 0.1.4 PKG passed isolated native installation and all **141**
  game-file hash checks. Original PKG and license were unchanged.
- The physical rePatch route reconstructed **14** game components plus
  sanitized original permissions from the original PKG and matching license.
  It matches the user-confirmed hardware delivery.
- All **2,582** members in the twelve modified archives preserve native
  storage choices. All nine native shared-script byte lengths are preserved.
- Lua 5.1 checks reproduce the captured missing `LOCAL_FLAG` error, then
  verify the corrected first-stage callback without shared constants. They
  verify **6,481** native values, compile **288** script pairs, and match
  **4,617** modeled event cases; three require unmodeled game behavior.
- Focused regression suite: **33 tests**, 32 passed and one optional skip.

Hardware confirmation covers the reported first battle. The earlier Vita3K
0.1.1 build passed intro, title/menu, battle demonstrations and map testing;
fresh 0.1.4 emulator gameplay is not claimed. A full story playthrough remains
unverified. The device-specific shared-initialization cause is still unconfirmed.

### Coverage and translation process

English story dialogue, pilot/mech/weapon and Library text, captions, UI and
mission text are carried from the shared translation. AI-assisted drafts are
checked against the glossary, edited and revised using playtester feedback.
Canonical names and terminology are retained during the port.

Coverage does not establish complete proofreading or every-screen validation.
Vita DLC was not supplied; Vita DLC, trophy translation and OS metadata are
outside this release. The host event tests use substitutes for native game calls.

### Acknowledgements

Thanks to the hardware and emulator testers for reproductions and screenshots,
and the community references supporting terminology. The local patch route uses
Retro Trans Tools, xdelta3, Vita3K, pkg2zip and psvpfsparser; native regression
checks also use Lua 5.1 and Unicorn.

### Source code and contributions

For Vita, download the two named patch ZIPs above. GitHub's automatic source archives
contain project sources and documentation, not installable games. Source-dependent
tools require locally supplied game data. The `v0.1.4` tag identifies the release
source; exact commit identity is recorded in `VALIDATION.json`.

Report issues with version, device, stage and complete error screenshots through
the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues) or
[Discord](https://discord.gg/MssepShjmB).

Patches and metadata only; no game PKG or license is distributed.

Vita build-source commit: `6c9f44dc459d2917500ddde47b976bf19e4cc055`.
