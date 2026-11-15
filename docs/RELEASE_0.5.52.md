# English 0.5.52 — experimental CFW startup test

Carry the complete 0.5.51 English translation inside a disc fake-SELF wrapper,
retaining the original Tengoku application identity and capabilities. This
addresses the known plain-ELF packaging limitation in the earlier RPCS3 image.
It is a hardware-test candidate, not a confirmed fix for startup error 80010017.

The embedded program is byte-identical to 0.5.51. Only its outer executable
container and title-version artwork change. Text, fonts, other disc files,
translated DLC 0.5.49 and saves remain unchanged.

Two Retro Trans routes are prepared: original Japanese ISO to 0.5.52 and exact
public English 0.5.44 to 0.5.52. Use the source checksum in BUILD-MANIFEST.json.
Patches contain neither a full game image nor license material.

For the tester on Evilnat 4.93 / Cobra 8.5, follow
[the hardware test instructions](CFW_TEST_0.5.52.md). Report mount success,
title-screen success and any error separately, including the manager/version
and transferred ISO checksum. Do not change firmware for this test.

Physical PS3 compatibility and live gameplay remain unverified. Local checks
cover the full executable payload, container metadata, all disc files in both
directory trees and complete-image patch reconstruction. Final results are
recorded in `work/ui/local_release_0.5.52.json`.

Prepared locally. A GitHub release or draft requires explicit consent.
