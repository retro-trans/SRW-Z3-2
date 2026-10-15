# Complete Back Log text — 0.5.37

The reported line is dialogue record `557:t_011:15`, source fingerprint
`373f95c8d8`. The translation and font cells are correct. Its CRLF-normalized
entry has 323 bytes; the native dialogue-event backlog writer copies only
308 bytes and appends a terminator. That cut falls inside an allocated font
cell, explaining the malformed text even though normal dialogue is intact.
The original native writer reproduces the invalid terminal cell. The new
writer preserves every byte, including the complete final sentence.

The shared inline layout is enlarged by 768 bytes. Text capacity increases
from 309 bytes including the terminator to 1,077. Entry stride increases from
344 to 1,112 bytes, and the 20-entry allocation grows from 7,524 to 22,884
bytes. Both constructors, reset-all/reset-one helpers, entry writer and ring
compaction use the same layout. All six keyword-link identities, descriptor
pointers, event identities, flags and the 20-entry count retain their values.

The backlog also clips each separately drawn row at 128 bytes. Its row buffer
now accepts the complete 255-byte descriptor range. The window's stack frame
grows by 128 bytes, with every affected saved-register/local offset adjusted.
The buffer starts at offset 0xb0 and its maximum terminator is at 0x1af;
the next live local is at 0x1c0. The original copy branches remain in place.

`tools/backlog_storage.py` binds all six consumer spans to the pinned original
executable and changes exactly 114 instruction constants. Applying it to the
verified 0.5.36 executable leaves every other executable byte intact. The
complete builder and the incremental 0.5.37 builder use this same patch.

The complete active corpus contains 63,553 dialogue entries. The compiled
byte audit finds 204 entries over the old storage limit and 125 rows over the
old copy limit. The longest encoded entry is 413 bytes and the longest row
is 156 bytes. Native substitutions retain their existing handling. No
dialogue is shortened, rewritten or rewrapped for this fix.

Instruction-level checks run both real allocation constructors, insert all
204 long entries plus Leonard's report, and execute 185 ring shifts for each
constructor. They compare every retained text and its six keyword IDs after
each insertion, check duplicate suppression, reset every entry, and guard the
allocation with a canary. Row checks run all 125 longer rows plus boundary
lengths 1, 127, 128, 129, 254 and 255, preserving adjacent stack canaries.
The actual window prologue/early return also restores all saved registers and
the original stack pointer. Tests separately reproduce both old limits.

Final verification also reads Leonard's exact packaged Lua block, checks the
encrypted stage wrapper and decoded stage hashes against their certified
parent, and verifies unchanged files/archive members. This is native-code
execution and artifact readback; in-game visual confirmation remains pending.

Dry runs: `python -m tools.backlog_storage`, `python -m tools.review37_build`,
and `python -m tools.verify_review37 --preview`. Final evidence and the supplied
screenshot are recorded by `python -m tools.verify_review37 --apply`.
Public delivery uses both official Retro Trans routes from the original game
and public 0.5.28. Creating or publishing a GitHub release requires explicit
consent for 0.5.37 under AGENTS.md.

## Final checks

The full current regression run contains 322 tests: 320 passed and two
optional Capstone checks skipped. Final native readback passes both
constructors, 370 ring shifts, every affected long entry and row, the original
failure reproduction, link metadata, duplicate suppression and resets.
The packaged Leonard dialogue exactly matches the complete dialogue fixture.

All 82 ISO files passed both filesystem-tree checks. The resulting
5,289,541,632-byte image has SHA-256
`345da8e95b2d974e9622ae1921aab0a1086a4fd566d4db078f490a2797f12892`.
Final evidence is `work/ui/review37_verified_0.5.37.json`.

Both official Retro Trans 0.5.4 patch routes, from the original game and exact
public 0.5.28, passed complete ISO decode round trips to that same hash. The
five delivery files and their checksums are recorded in
`work/ui/local_release_0.5.37.json`. Release notes in `docs/RELEASE_0.5.37.md`
use **What changed since last version** and compare with public 0.5.28.
The source commit is `74a3857d1cff319ef54459be26bdba25365be5a1`.
No GitHub release or draft was created or published.
