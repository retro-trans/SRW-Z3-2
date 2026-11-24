# PS3 voices missing and battle captions showing only ellipses

On 2026-11-22, the tester confirmed 0.5.53 reaches the opening and reported
missing battle voices, battle captions containing only ellipses, and working
music/effects. The screenshot alone shows an ellipsis line in the opening;
the broader battle symptom comes from the tester's follow-up. The earlier
trophy-installation screen is no longer the reported blocker. This is not
full gameplay validation.

The supplied `incoming/DATA0046.DAT` is **4,946,624 bytes** and byte-for-byte
identical to the verified English build, including its SHA-256 below.
**Do not refresh or move this correct cache.** The executable actually selected
on the console remains unconfirmed.
The user subsequently reported no EBOOT.BIN under the requested installed-game
USRDIR, only INSCO and UPDATE.LOG. That location does not support the update
override hypothesis. The supplied `incoming/UPDATE.LOG` has 38 source/destination
records; all match the native install table. Its header and trailing fields have
unverified semantics. It does not establish the active executable or validate
installed audio payloads. Leave the console files unchanged.

The log maps `/app_home/DATA/SOUND/TALKZ3TENPS3.CPK` to
`/INSCO/DATA0133.DAT`. The expected audio archive is 872,459,864 bytes, SHA-256
`beaa7c4a4458d07699ed1e1376d64fdb7419530c4beb5d4483e8383cb10eb8ec`.
UPDATE.LOG itself is 10,344 bytes, SHA-256
`0e0fe4542e2d8a33176407647ed762bc11cc63153666cdd4029b0fde0e7751c9`.

On 2026-11-23, the user confirmed installed DATA0133.DAT is exactly
**872,459,864 bytes**, matching the expected voice archive length. On
2026-11-24 the user supplied its SHA-256; normalized to lowercase, it exactly
matches the verified original voice archive above. This is a user-reported
console hash, not a file read directly from the console by this tool.
No further audio upload, replacement or reinstall is justified by these checks.
After the user
pointed out that the local disc EBOOT was already available and checked, defer
collecting a duplicate from the tester. The local executable is verified;
the console's actual mounted-image identity is still a separate unknown.
After both voice-file identities matched, a mounted EBOOT hash-only comparison
was requested. The user replied that it cannot be checked currently; leave it
pending rather than treating the local EBOOT as proof of the console's copy.

## What the read-only checks establish

The final 0.5.53 disc contains the correct paired executable and SRVC.BIN.
All four original SOUND archives are byte-identical to the Japanese source.
Every voice-bank header, selection rule and cue table is retained: 368 banks
and 78,302 cue references. No audio sample replacement or voice disabling is
part of the translation or 0.5.53 trophy control.

Instruction-level execution of the packaged PPC start-read chain and parser
now verifies all 368 bank read ranges and parsed array/pool pointers. Every
valid input bank remains unchanged. The largest read window is 76,048 bytes;
only one bank exceeds 64 KiB. This check mocks the streaming boundary at
0x22a84: it does not verify PS3 allocation, file I/O, bank selection or audio
playback, and it does not establish the hardware failure's cause.

The executable's native install list maps SRVC.BIN to `/INSCO/DATA0046.DAT`.
The installed copy must agree with the executable's resized bank-offset table.
Using the original Japanese file with the translated table gives invalid
version headers at 359 of 368 bank starts, including 279 of 283 text banks;
109 read windows extend past the old file's end. This demonstrates a concrete
failure mode consistent with the report, but the supplied file rules out this
old-cache explanation for that copy. The running executable still needs checking.

The reverse mismatch also matters: the original executable table used with the
correct-sized translated data gives 363/368 invalid bank headers, including
280/283 text banks. Therefore a matching file size cannot rule out an
executable/data mismatch. An installed update executable is one possibility to
check, not a confirmed finding on this console.

| Installed DATA0046.DAT | Bytes | SHA-256 |
| --- | ---: | --- |
| Original Japanese copy | 3,499,808 | `8736ee4a52cf931e909b95f3a007ce6ee8d9db258f0ce44b73bd89ce36263ffc` |
| Required by 0.5.52 / 0.5.53 | 4,946,624 | `bf6c6947a393a2ef140bf33a263df05ff6bc626e3ce0033dda574ad93893c48d` |

## Current tester checks

Current next checks, after the byte-identical cache result:

- Treat missing speech and all-ellipsis battle captions as one combined report.
  Voice Volume is not an established explanation for both. The next useful
  runtime evidence is the selected bank id, table offset/read length, read
  status, loaded header, parsed line count and prepared fallback flag/cue.
- Installed DATA0133.DAT now has both the expected reported length and SHA-256.
  Preserve it and the byte-identical DATA0046.DAT; no further audio-file upload
  or reinstall is part of the current investigation.
- The user reports `/dev_hdd0/game/BLJS10299/USRDIR/EBOOT.BIN` does not exist,
  with only INSCO and UPDATE.LOG in that directory. Preserve that result;
  do not change a different directory looking for an override.
- The expected mounted-disc EBOOT.BIN is 19,337,892 bytes, SHA-256
  `93e0ad06074f485c27fcc2c9689134bf897f9dabdad56c14acd41a69c27af3d9`.
  A differing container hash needs inspection; it does not alone prove a
  different program because a manager could have altered only its wrapper.
- A mounted-disc EBOOT SHA-256 can resolve remote executable identity. The user
  cannot obtain it currently; this check remains pending. If a future hash
  differs, inspect its program/table before drawing conclusions from the wrapper.
- Historical unpatched-game battle speech remains unconfirmed. Do not switch
  to an original executable against translated installed data as a control;
  that creates a known mismatch. Settings are secondary context, not a substitute
  for investigating the coupled caption/voice failure.

## Native control reproducing both symptoms

On 2026-11-24, the user reiterated that every battle quote is also an ellipsis.
The previous reply overemphasized Voice Volume; the primary target is the
shared bank/quote-selection path. `tools/cfw_voice_selection_audit.py` executes
the packaged PPC read chain, parser, entry builder and playback selector in
interpreter memory. These control code ranges are byte-identical to the original.

For bank 3, the paired English table reads offset 13,600, length 13,024. The
native parser obtains 214 lines; the controlled rule selection produces entry
flag zero, the expected translated quote and one voice-play call (cue 41,167).
Replacing only the table in interpreter memory with the original offsets makes
the same code read offset 9,920, length 9,312 from the same English file. Its
loaded header starts `86e186f286e181ae`, not version 3. The native parser clears
the line count, and the entry builder prepares a flagged fallback entry using
the control's seeded default template (cue zero, fallback flag one). That
template state is a controlled input, not a captured value from the tester.

The relevant original code path is:

- 0x139118..0x139148: an invalid version clears the bank counts.
- 0x12ebb4..0x12ec60: zero lines select the default entry; 0x12ecb8 copies
  its fallback flag.
- 0x12e58c..0x12e594: a nonzero entry flag selects 0x12e6f0, bypassing
  the voice-play call at 0x12e7c4.
- 0x12e700: load the built-in UTF-8 ellipsis caption (source VA 0x84ecc0)
  and copy it through the native caption routine. The control verifies exactly
  that caption and zero voice-play calls.

This demonstrates a concrete shared failure mode, not the tester's root cause.
The audio engine, streaming completion, C string helpers, speaker lookup and
upstream rule choice are modeled boundaries. The console's actual loaded bank
header and prepared flag remain unknown. Both installed voice files match; do
not infer corruption or change the correct files from this local negative control.

RPCS3's [disc boot/update selection](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/System.cpp)
checks for a title-specific installed update EBOOT. This supports checking for
an override; it is not proof of the file or launch behavior on this tester's
console. It does not supersede the reported absence of that installed EBOOT.

## Historical procedure for a confirmed stale cache only

This procedure does not apply to the correct supplied DATA0046.DAT. Use it only
if a different installed copy is independently confirmed to be stale.

1. Close the game. Locate its installed game-data cache. The observed Tengoku
   path in RPCS3 is `/dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0046.DAT`;
   confirm the actual folder/file on the console before changing anything.
2. Check that file's size. If it is 3,499,808 bytes, it is the original-size
   data and cannot match this executable. The required size is 4,946,624 bytes;
   compare the hash above if possible because size alone cannot prove identity.
3. If the old cache is confirmed, preserve a complete backup of **only the
   Tengoku installed-data folder `BLJS10299_DATA`**, then move that folder to
   a backup location outside `/dev_hdd0/game/`. Start the 0.5.53 ISO again and
   let the game recreate its installed data. Keep the backup until recovery
   is confirmed. This is a cache refresh, not another ISO patch.
4. Check the new DATA0046.DAT size/hash, then replay one battle attack. Report
   whether both speech and captions return. If the file already matches, or
   the stated folder does not exist, report that instead of changing a
   different folder; the next investigation must use that evidence.

Preserve savedata, trophy progress, DLC under NPJB00692, the disc image and
other games. No deletion/reset of those is part of this procedure. No remote
console or local emulator cache was changed during this investigation.

## Evidence

Run `python -m tools.cfw_voice_cache_audit` for a dry, read-only audit. Repeat
with `--apply` only to save its English JSON report; it never writes game or
installed-cache files. All 16 SRVC parser/rebuilder checks also pass.

- Report: `work/ui/ps3_voice_report_2026-11-22.json`.
- Audio hashes, cue preservation and old-cache simulation:
  `work/ui/ps3_voice_audit_2026-11-22.json`.
- Actual PPC start-read/parser execution for all 368 banks is included in the
  same audit under `native_bank_readback`.
- Paired and mismatched native caption/voice controls are included under
  `native_coupled_quote_voice_controls`.
- Focused tests: `work/output/scratch/ps3-voice-cache-2026-11-22-tests.log`.

The native game data establishes the install filename. RPCS3's
[game-data implementation](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/Cell/Modules/cellGame.cpp)
also illustrates the separation between installed content and the disc path;
it does not independently confirm this tester's physical-console folder or
cache contents. Hardware audio recovery remains pending.
