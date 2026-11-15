# Tengoku-hen 0.5.52 — CFW startup test

This is an experimental hardware-test candidate, carrying all English fixes
through 0.5.51. Physical-console boot and gameplay are not yet verified.
The tester reports Evilnat 4.93 with Cobra 8.5 and successful boot of the
unpatched Japanese game on the same setup. The earlier translated image
showed startup error 80010017; its exact checksum was not supplied.

## What changed

The complete 0.5.51 program is enclosed in a CFW disc fake-SELF container,
using the original Tengoku application identity and capabilities. The
embedded ELF, its entry point, program headers, instructions, memory addresses
and translation payloads are byte-identical. No firmware setting is changed.
This is not a Sony retail signature or an unmodified-firmware package.

Only EBOOT.BIN and the title's version artwork differ from 0.5.51. All other
game files, fonts, text, DLC and save data are preserved. This first test
intentionally keeps the three existing nonempty memory LOADs. A successful
wrapper check does not prove that the physical console accepts that layout.

The source disc layout is preserved using the established writer: all replaced
files are referenced from both ISO9660 and Joliet, stale UDF discovery records
are removed, and one plaintext region covers the complete image. Verification
reads all 82 files through both trees. The title ID remains BLJS10299.

## Tester instructions

Expected image: `Tengoku-hen-English-0.5.52-CFW-test.iso`, 5,289,738,240 bytes.
SHA-256: `e3c01ec31f186ddc22e8e53c89c9bf90d0a2352c9dafea83e02b47988ad2ecfd`.

1. Apply the matching Retro Trans patch to your original Japanese ISO or exact
   public English 0.5.44 ISO. Verify the resulting checksum against the release's
   BUILD-MANIFEST.json. Keep the known-working original image.
2. Transfer the full `Tengoku-hen-English-0.5.52-CFW-test.iso` to
   `/dev_hdd0/PS3ISO/` using your existing transfer method. It exceeds FAT32's
   single-file limit. This is an ISO, not a PKG. Do not use a cached
   `.iso.ntfs[PS3ISO]` descriptor as the source image.
3. Use the same manager and mounting settings that boot the Japanese original.
   Mount this exact filename, then launch the mounted disc icon. No firmware,
   plugin, license or DLC installation changes are required for this test.
4. First report whether mounting succeeds and whether the title screen appears.
   Include the exact error code if it fails. If it boots, check English menus,
   early dialogue and one battle. Keep existing progress; use a spare save slot.
5. Report the game manager name/version, actual transferred ISO checksum,
   exact tested filename and results. Firmware details are already recorded as
   Evilnat 4.93 / Cobra 8.5. To stop testing, unmount this candidate and return
   to the known-working image.

If the error changes or startup still fails, keep the exact result. The next
diagnostic would compare a pristine wrapped Japanese executable under the
same packaging; do not assume a particular error number identifies one cause.

## Reproduce and verify

Use the repository's pinned Pillow 12.3.0 environment and validated 0.5.51
build, proof and delivery seal. The original disc SELF is pinned by SHA-256.
The wrapper tool is the locally compiled MIT-licensed
[PSL1GHT fself](https://github.com/ps3dev/PSL1GHT/tree/f649a08fd536a9e27c08c7db2d93a2d7ee4c3bbe/tools/fself)
at commit `f649a08fd536a9e27c08c7db2d93a2d7ee4c3bbe`.
The local build includes the missing `.sceversion` guard documented in the
sibling Jigoku project's `platforms/ps3/CFW_TEST.md`. Its SHA-256 is
`b3bc066b39b69adff7fd59c849b14bb8754c4c306c549aa1ecd791b953799554`.
Pass its location with `--fself` if the default local path differs. Keep the
upstream MIT license with any redistributed wrapper tooling; no wrapper binary
or original game files are committed or included in patch delivery.

Run each command without `--apply`, inspect its preview, then repeat with
`--apply` where shown. Existing binary output directories are never replaced.

```powershell
python -m tools.cfw_package build --fself '<local pinned fself.exe>'
python -m tools.cfw_package build --fself '<local pinned fself.exe>' --apply
python -m unittest tests.test_cfw_self -v
python -m tools.cfw_package iso
python -m tools.cfw_package iso --apply
python -m unittest discover -s tests -v
```

`tools/cfw_self.py` independently checks every SELF program mapping, embedded
header, ELF payload byte, application record, capability record, digest and
section-table reference. Corrupt/truncated containers and invalid LOAD layouts
are rejected. The game program is unchanged, so the sealed 0.5.51 native text
execution evidence remains applicable to its embedded payload. No live emulator
or hardware boot is implied by these file checks.

Evidence is recorded in `work/ui/cfw_verified_0.5.52.json`; complete-image
Retro Trans round trips and regression results are sealed separately in
`work/ui/local_release_0.5.52.json`. Prepared patches target the original
Japanese image and exact public 0.5.44, with no complete ISO redistribution.
Creating or publishing a GitHub release needs explicit consent for 0.5.52.
