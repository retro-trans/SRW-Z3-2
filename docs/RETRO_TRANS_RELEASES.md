# Retro Trans release preparation

Every new Tengoku release must work with
[Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools), following
the approach documented by [SRW-Z3](https://github.com/retro-trans/SRW-Z3/blob/master/docs/RETRO_TRANS_RELEASES.md).

This repository is public as of 2026-10-10, at the user's request. Release
0.5.2 is a regular GitHub release in Retro Trans's public Automatic catalog.
It remains a playtest build. Repository administration does not create a game build.

For a separately requested release:

1. Resolve the known dialogue overflow, promote reviewed translation inputs,
   build and test the intended output. Record the actual source commit,
   platform, input/output sizes and SHA-256 hashes.
2. Use the existing `0.x.y` build sequence and update the changelog. Do not reset
   the sequence or assign a release version for repository administration.
3. Check the current Retro Trans release contract and record the tool version.
   Prepare its required manifest, patches, checksums and validation report.
   Use Tengoku BLJS10299 identities, never Jigoku BLJS10256 identities.
4. Validate full patch decode round trips against the intended output and run
   the release validator. Confirm the package format is supported.
5. Keep game images, extracted files, fonts and private source material out of
   hosted assets. Automatic discovery requires a public repository and a
   published release without GitHub's prerelease flag. Refresh the scoped
   Retro Trans catalog and verify recognition and the patch route. Keep
   runtime limitations in the notes. Never add credentials to a public catalog.

No release artifacts or compatibility certification are created by this setup.
