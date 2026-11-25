English translation patch for **Super Robot Taisen Z3: Tengoku-hen** on
**PS Vita and Vita3K** (Japanese **PCSG00494**, version **01.00**).

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

`SHA256SUMS.txt` verifies all downloads. `VITA-PKG.json`, `VITA-REPATCH.json`
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

For the exact Japanese PCSG00494 v01.00 PKG above. This release does not
update PS3 or change its latest-release selection.

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

Download the two named patch ZIPs above. GitHub's automatic source archives
contain project sources and documentation, not installable games. Source-dependent
tools require locally supplied game data. The `v0.1.4` tag identifies the release
source; exact commit identity is recorded in `VALIDATION.json`.

Report issues with version, device, stage and complete error screenshots through
the [issue tracker](https://github.com/retro-trans/SRW-Z3-2/issues) or
[Discord](https://discord.gg/MssepShjmB).

Patches and metadata only; no game PKG or license is distributed.
