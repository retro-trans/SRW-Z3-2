# Actual linked-keyword popup archive — 0.5.41

Public 0.5.40 still displays Japanese keyword descriptions, including
Messenger and Meganoid. Earlier audits verified English in the executable's
dictionary and `MTZKN_KW.CPK`; neither check covered the data source used by
this popup. The earlier claim that those audits proved all popup entries
were translated was incorrect.

## Confirmed source

RPCS3 was running BLJS10299 with the 0.5.40 executable instructions and patched
dictionary pointers. Installed Library files DATA0011/12/13 matched the
released English archives exactly. This was not a simple stale Library file.

Read-only diagnostic and memory inspection located the loaded popup table.
All **143 records**, their **572 fields** and the complete string pool match
the original `COMMONDATA/MTDATA/MTV_ALL_KEYWORD_DEF.CPK`. The evidence is
`work/ui/keyword_popup_live_0.5.40.json`. No game memory, saves, emulator
settings or installed files were modified. The diagnostic protocol follows
[RPCS3's PINE implementation](https://github.com/RPCS3/rpcs3/blob/master/3rdparty/pine/pine_server.h).

## Correction

`tools/keyword_popup.py` checks the original archive hash and parses member 0:
MTFL/kwrb contains an lkke table and an XOR-0x7a CP932 jstr pool. Each of the
143 rows has four offset/length pairs, flags and its stable keyword ID.
Every original field is matched to its Library source by ID before editing.

Both description variants now reference complete, wrapped English encoded
with the existing font mapping. The pool is expanded without a fixed text
budget. Lookup names, series, row order, IDs and flags are unchanged; the
original pool and provenance trailer remain intact. Only description
offset/length pairs and five containing-size fields change. The source pool
ends without a NUL, so a terminator is added before the new allocations.

The member grows from 94,964 to 329,196 bytes; the longest English description
is 4,962 encoded bytes. The rebuilt archive is compressed and independently
reopened. Full builds and ISO delivery now explicitly replace this additional
archive. The incremental build retains every 0.5.40 game asset except the
title-version stamp and adds the corrected popup archive.

## Verification

Five focused archive/loader tests reproduce the omission in public 0.5.40,
read back every English description through its actual native record,
check line widths, pool termination and preserved lookup data, reject invalid
bounds/IDs, and reopen the compressed CPK. Sixteen focused checks pass when
combined with the earlier Library, font and selection tests.

`tools/verify_review41.py` verifies all final assets and the deployed popup
archive in the final ISO inventory. Matching asset hashes retain earlier
regression evidence. The live audit proves the old bug and the correct
source; it does **not** establish live visual verification of the new build.
The new image still needs a fresh boot and popup/navigation testing.

This is a new build with immutable new Retro Trans patches. Public 0.5.40
assets are not replaced. Publication of 0.5.41 needs the user's explicit
consent after local patch validation.
