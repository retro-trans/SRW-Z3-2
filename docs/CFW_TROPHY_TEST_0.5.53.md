# 0.5.53 CFW trophy-installation control

The tester confirms that 0.5.52 reaches the system screen reading “Installing
trophy data” but remains at 100%. The reported console is Evilnat 4.93 with
Cobra 8.5. The manager may be webMAN; its exact name/version and the wait
duration have not been confirmed. This is progress beyond the earlier launch
error, not successful title-screen or gameplay verification.

## What this test changes

Restore the complete original Japanese `TROPHY.TRP` from the owned game dump.
Only that one logical disc file changes. The wrapped executable, program
headers, translation code, fonts and the other 81 files remain byte-identical
to 0.5.52. No trophy APIs are disabled or bypassed. Trophy names/descriptions
will use the original language; the game translation remains unchanged.

To keep the control to one file, the title artwork deliberately still shows
0.5.52. Identify this diagnostic by its **0.5.53 filename and ISO checksum**.
It is a separate experimental test, not a claim that the hang is fixed.

The translated package changes `TROP.SFM` and `TROP_00.SFM`. Each original
contains a 352-byte comment omitted during XML serialization. Both complete
packages pass their TRP SHA-1 checks; that checksum does not establish SFM
authentication or physical-console acceptance. The control restores every
original byte, including those comments, configuration and icons.

The emulator's [trophy registration implementation](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/Cell/Modules/sceNpTrophy.cpp)
selects a localized SFM and installs it through its own
[TRP reader](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Loader/TRP.cpp).
Those emulator checks cannot establish identical behavior on retail PS3 system
software. The missing-comment finding is a candidate difference, not a proven
cause of the reported hang.

## Tester instructions

Target ISO: 5,293,670,400 bytes; SHA-256
`274cd6220c3851f41d11b3dfbf5bed5251157c9fe614f777150017049d6bf3be`.

1. Keep the current 0.5.52 ISO and known-working Japanese original. In Retro
   Trans Tools, use **Apply xdelta** with the exact 0.5.52 CFW ISO and
   `SRW-Z3-2-PS3-English-0.5.53-original-trophies-from-0.5.52.xdelta`.
   Write a new ISO. The source checksum is in BUILD-MANIFEST.json; this patch
   does not apply directly to the Japanese original or 0.5.44.
2. Transfer the new `Tengoku-hen-English-0.5.53-original-trophies-CFW-test.iso`
   using the same working method, then mount that exact file with the same
   manager/settings. Use the complete ISO, not a cached NTFS descriptor.
3. Report whether the trophy-installation screen closes and whether the title
   screen appears. Include the time spent at 100%, any error code, exact manager
   and version, and whether the PS button still responds while it is stuck.
4. If startup succeeds, check an English menu and early dialogue. The title's
   version label still reading 0.5.52 is expected for this one-file control.

No deletion/reset of installed trophy data, saves, profiles or firmware is part
of this test. If it remains stuck, preserve that result; it does not justify
deleting trophy progress or establish that the executable is at fault.

## Local preparation and evidence

`tools/cfw_trophy_control.py` accepts only the sealed 0.5.52 parent. It restores
the original trophy package, appends it to a new copy of the image, updates both
directory trees and verifies all 82 game files. The source image is preserved.
The original trophy-package SHA-256 is
`0da66f959beb04ef0a1e60bb9838bdf55c7003f4b4342383e812061af7f46e52`.
The translated source package is pinned to
`2521580590639e78a5e8f0d9705a7cd3f8dbc3158d740748bac076b1364e805c`.

Run `python -m tools.cfw_trophy_control`, inspect its dry run, then repeat with
`--apply`. Run the focused CFW, trophy, native-message and ISO tests before
`tools/release_prepare53.py` prepares/seals the official Retro Trans round trip.
The unchanged executable inherits the 0.5.52 native checks and its 379-test
regression evidence; focused new checks are recorded separately, not described
as a fresh full-suite run.

Reports: `work/ui/ps3_trophy_stall_2026-11-22.json`,
`work/ui/cfw_trophy_verified_0.5.53.json` and
`work/ui/local_release_0.5.53.json`. No full ISO, original trophy package,
license material or saved progress is included in public patch delivery.
Creating or publishing a GitHub release still requires explicit consent.
