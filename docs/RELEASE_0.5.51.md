# English 0.5.51 — DLC menu translation and alignment

Translate the complete bonus-scenario menu text category: 35 scenario
summaries, related purchase/start/claim prompts and the bonus-scenario rules.
Fix the overlapping episode/status and description/reward labels. Keep full
summary wording within the panel and show English titles and reward names
in the native confirmation dialog.

This base-game update carries 0.5.50 and works with DLC English 0.5.49.
Existing translated DLC does not need reinstalling. Fonts, narration timing,
scenario logic, rewards and saves are preserved.

Retro Trans delivery supports the original Japanese ISO and exact public
English 0.5.44. Use the route matching the source checksum in
`BUILD-MANIFEST.json`. Both produce the complete English 0.5.51 image.

The native checks cover every launch/claim combination. Final image,
regression and patch round-trip evidence is recorded in
`work/ui/local_release_0.5.51.json`. Live gameplay confirmation remains
separate. See [the implementation notes](DLC_MENU_0.5.51.md).

Published at the user's explicit request in the
[combined PS3/Vita release](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.1.4)
on 2026-11-25. The known RPCS3-oriented executable packaging remains unchanged.
Use Retro Trans **Apply xdelta** with either PS3 download; see
[installation instructions](PS3_INSTALL_0.5.51.md). The combined release keeps
PS3 0.5.51 and Vita 0.1.4 as distinct build versions.
