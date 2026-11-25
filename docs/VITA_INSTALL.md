# Vita and Vita3K 0.1.4 installation

Download the matching patch ZIP from the [0.1.4 release](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.1.4).
Use [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools) 0.5.19 or later.
Keep the patch ZIP intact. Supply your own original Japanese PKG and matching work.bin or RIF locally.

## Required original

- Game: PCSG00494, Japanese Tengoku-hen, version 01.00.
- Content ID: JP0700-PCSG00494_00-SRWZ3OF2DLGPKG00.
- PKG size: 2,926,199,744 bytes.
- PKG SHA-256: 009833f3ecb46da08e50ad9d3cfc9772a2d74499f29960a6645d88235e78e7b0.

Both deliveries start from this original PKG, including when upgrading an older English build.
Keep originals and back up saves before updating.

## Physical Vita — rePatch

1. In Retro Trans's Vita tab, choose Hardware rePatch.
2. Select the original PKG, matching work.bin or RIF, a new output folder, and
   SRW-Z3-Tengoku-v0.1.4-Vita-rePatch-patches.zip as Local patch.
   Once the public catalog is refreshed, leaving Local patch blank discovers the delivery automatically.
3. Let reconstruction and verification finish. No separate self_auth.bin dump is needed;
   the patch includes sanitized original permissions.
4. Close the game. Back up any existing ux0:/rePatch/PCSG00494 folder outside rePatch, then
   copy the complete generated rePatch/PCSG00494 folder to ux0:/rePatch/PCSG00494 using VitaShell.
   Replace the complete older overlay; do not mix files with other mods. Preserve savedata.
5. Launch the matching installed Japanese game with compatible rePatch enabled.
   Confirm v0.1.4 on the title screen.

The physical tester confirmed the reported first-battle correction works on 2026-11-25.
This is a focused hardware test, not a full story playthrough.

## Vita3K — translated PKG

1. In Retro Trans's Vita tab, choose Vita3K PKG.
2. Select the original PKG, matching work.bin or RIF, a new output PKG name, and
   SRW-Z3-Tengoku-v0.1.4-Vita-PKG-patches.zip as Local patch.
   Automatic also discovers the original PKG after the public catalog refresh.
3. Let local rebuilding and native installation verification finish.
4. Back up your Vita3K save, then use File → Install .pkg to install the generated English PKG,
   supplying the same matching license when requested.
5. Confirm v0.1.4 on the title screen.

The 0.1.4 PKG passed the isolated native installer and all 141 game-file hash checks.
The earlier 0.1.1 build passed the intro, English title/menu, battle demonstrations and map test
in Vita3K; the user confirmed it worked. No fresh 0.1.4 emulator gameplay or complete story
playthrough is claimed.

## Changes and coverage

The port carries the PS3 0.5.51 English dialogue, names, menus, Library, mission text, captions
and adapted artwork. Canonical glossary spellings and font preferences are preserved.
Vita DLC was not supplied and is not included; trophies and OS metadata remain untranslated.

Version 0.1.4 removes a missing-global dependency that stopped physical Vita after the first
battle. Original immutable Vita constants are bound directly in 287 stage scripts and the
shared battle helper. Dialogue and game commands are preserved. All original archive storage
choices and nine fixed shared-script lengths are retained. The earlier post-intro black-screen
correction is included, and readable error reporting remains enabled.

If a problem occurs, report the version, device/emulator, stage and actions, and photograph the
complete error. The device-specific initialization cause is still unconfirmed.
See [port and validation notes](https://github.com/retro-trans/SRW-Z3-2/blob/v0.1.4/docs/VITA_PORT.md).

The release contains patches and metadata. GitHub's automatic source-code ZIP is the project
source, not the patch ZIP. No game PKG or license is distributed.
