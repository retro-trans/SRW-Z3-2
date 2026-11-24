# PS3 battle quote and voice diagnostic 0.5.54

This diagnostic investigates the combined report: battle captions show only
ellipses and pilot speech is absent, while music and effects work. Both installed
voice-data files match the verified build. A controlled local execution shows
that an invalid bank can produce the two symptoms together; the console's actual
runtime state remains unknown. This build gathers evidence rather than claiming
an audio repair.

## One tester run

1. Apply the `voice-diagnostic-from-0.5.53.xdelta` patch with Retro Trans Tools
   to the exact 0.5.53 original-trophies CFW test ISO. Keep that source ISO.
   Its SHA-256 is
   `274cd6220c3851f41d11b3dfbf5bed5251157c9fe614f777150017049d6bf3be`.
2. Mount the newly named 0.5.54 diagnostic ISO. The image carries a 0.5.54
   title footer; existing installed title artwork may retain an older number.
   Use the battle caption's `0.5.54` marker to confirm the diagnostic ran.
   Keep the verified installed data; no cache reset is part of this test.
3. Replay one battle attack or the same demonstration that showed the problem.
   Photograph the entire battle-quote box when a diagnostic readout appears.
   The readout starts with `0.5.54` and uses two short lines.
4. If ordinary quotes and speech return, report that result. If the game still
   shows plain ellipses without a readout, photograph that screen and the title
   footer. That can indicate another quote path or an inactive diagnostic;
   it does not by itself prove a particular executable override.

The supplied installation log maps EFFPS3.CPK to INSCO/DATA0030.DAT. Title
artwork caching is therefore a possibility to account for, not a reason to
replace the verified voice files or reset installed data for this diagnostic.

## Reading the photograph

All numeric fields are hexadecimal. The screenshot preview under
`work/ui/0.5.54/voice-diagnostic-sample.png` uses simulated values and the
unchanged game font, not a hardware capture.

| Field | Meaning |
| --- | --- |
| B | Bank id associated with the actual completed read buffer |
| H | Version byte in the bank used by the quote builder; expected `03` |
| N | Line count in that bank after the native parser ran |
| O | Read offset from the runtime bank table |
| S | Requested bank-window length |
| F | Selected entry's fallback flag |
| C | Selected entry's 16-bit voice cue |

For example, `H86 N0000` means the observed bank is not version 3 and has zero
parsed lines. `H03` with nonzero `N` moves the investigation toward entry/rule
selection. `BFFF` means the buffer could not be associated with the bounded
eight-buffer observer cache; it is not proof that the bank file is corrupt.
Missing values are printed as `F` digits. Interpret the whole readout together.

## Scope and validation

Two native hooks are added: the completed SRVC read-pointer store at 0x139084
records the buffer/bank/offset/length association, and the existing fallback
caption load at 0x12e700 formats the readout. The second hook reads the same
side/actor bank slot used by the native entry builder. It reads the actual
post-parser header and selected entry. The cache replaces records for reused
buffers and retains eight distinct buffer identities.

Injected code makes no file, heap or audio calls. It preserves all registers
and machine flags except the original fallback text-pointer result. The
original read-pointer store is replayed. It uses 768 bytes of previously
unallocated lookup headroom and extends the existing RX adapter segment by
1,576 bytes. The data LOAD layout, font files, Unicode converter table, all
voice metadata and sound archives remain unchanged. Ordinary selected quotes,
audio calls and selection data retain their original behavior.

The fallback string occupies 131 UTF-8 bytes plus NUL before native line-break
conversion, within the original 134-byte caption capacity. It reuses the
existing private alphabet; it introduces no new glyphs, spacing or outlines.
Native execution covers 379 read-observer cases, all eight side/actor bindings,
unknown/null buffers, both ordinary/fallback caption paths, register/flag
preservation and four converter-model cases. The focused 25-test CFW/trophy/
native-text/ISO run passes. Physical-console execution remains pending.

The complete original trophy package from 0.5.53 is retained. The only two
logical disc files changed are EBOOT.BIN and EFFPS3.CPK's title-version member.
The ISO readback checks all 82 files through both filesystem trees, and the
Retro Trans delivery must reconstruct the exact target image before sealing.
No emulator registration, installed console data, saves or GitHub release is
modified by preparation.

## Verified delivery

The exact 0.5.53-to-0.5.54 xdelta is
`work/output/releases/0.5.54/artifacts/SRW-Z3-2-PS3-English-0.5.54-voice-diagnostic-from-0.5.53.xdelta`:
139,575,552 bytes, SHA-256
`014afad433f795f9c2fede6ba54e21fc85e107b6394e65b65761285d822c2216`.
Retro Trans Tools' **Apply xdelta** route accepts the source ISO, local patch
and a new output path. The official 0.5.4 delivery builder decoded the complete
patch back to the exact 5,587,206,144-byte target image, SHA-256
`3467f9f0af7e35b86bbe1e215e9b24fde469b5d53582eaa4baff5e5d21b799b3`.
Both input images remained unchanged. The manifest, checksums and successful
round-trip report accompany the patch. Source commit:
`141a35a94729cd31b935e9a76f4631e4e5df7a47`.

Final evidence: `work/ui/cfw_voice_diagnostic_verified_0.5.54.json` and
`work/ui/local_release_0.5.54.json`. Preserve these sealed reports. Hardware
execution remains pending; no new GitHub release has been created.
