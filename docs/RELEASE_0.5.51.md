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

Prepared locally; creating or publishing a release requires explicit consent.
The known RPCS3-oriented executable packaging remains unchanged.
