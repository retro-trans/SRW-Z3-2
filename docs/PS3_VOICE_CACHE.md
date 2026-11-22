# PS3 voices missing and battle captions showing only ellipses

On 2026-11-22, the tester confirmed 0.5.53 reaches the opening and reported
missing battle voices, battle captions containing only ellipses, and working
music/effects. The screenshot alone shows an ellipsis line in the opening;
the broader battle symptom comes from the tester's follow-up. The earlier
trophy-installation screen is no longer the reported blocker. This is not
full gameplay validation.

## What the read-only checks establish

The final 0.5.53 disc contains the correct paired executable and SRVC.BIN.
All four original SOUND archives are byte-identical to the Japanese source.
Every voice-bank header, selection rule and cue table is retained: 368 banks
and 78,302 cue references. No audio sample replacement or voice disabling is
part of the translation or 0.5.53 trophy control.

The executable's native install list maps SRVC.BIN to `/INSCO/DATA0046.DAT`.
The installed copy must agree with the executable's resized bank-offset table.
Using the original Japanese file with the translated table gives invalid
version headers at 359 of 368 bank starts, including 279 of 283 text banks;
109 read windows extend past the old file's end. This demonstrates a concrete
failure mode consistent with the report. The console's cache has not yet been
read, so the mismatch remains a hypothesis until its size/hash is checked.

| Installed DATA0046.DAT | Bytes | SHA-256 |
| --- | ---: | --- |
| Original Japanese copy | 3,499,808 | `8736ee4a52cf931e909b95f3a007ce6ee8d9db258f0ce44b73bd89ce36263ffc` |
| Required by 0.5.52 / 0.5.53 | 4,946,624 | `bf6c6947a393a2ef140bf33a263df05ff6bc626e3ce0033dda574ad93893c48d` |

## Tester check and recoverable refresh

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
- Focused tests: `work/output/scratch/ps3-voice-cache-2026-11-22-tests.log`.

The native game data establishes the install filename. RPCS3's
[game-data implementation](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Emu/Cell/Modules/cellGame.cpp)
also illustrates the separation between installed content and the disc path;
it does not independently confirm this tester's physical-console folder or
cache contents. Hardware audio recovery remains pending.
