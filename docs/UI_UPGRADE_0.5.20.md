# Public 0.5.18 upgrade reports prepared for 0.5.20

The five screenshots show dynamic item-unlock reports, a dynamic upgrade
confirmation, Japanese trophy notifications, and duplicate award captions.
This change includes the previous unpublished 0.5.19 corrections. The public
upgrade input remains 0.5.18. Creating or publishing 0.5.20 requires explicit
consent for that release.

| Source category | Complete coverage | Implementation |
|---|---:|---|
| Item-unlock condition lines | 23 non-null conditions in the 24-entry native table | Match completed report strings |
| D-Trader item announcements | 24 items | Cover source Japanese and relocated VWF English item-name inputs |
| Selectable Full Upgrade Bonus confirmations | 9 choices | Match complete questions after native UTF-8 conversion |
| Two-color bonus awards | Both Custom Bonus variants and Ace Bonus | Six measured caption edits |
| Trophy UI | 35 name/detail pairs and two title fields in both variants | 144 translated text fields, all 40 container entries verified |

The old draw-time dictionary translated standalone condition/bonus names.
It could not match their completed runtime sentences. The native D-Trader
getter at 0x310328 enumerates 24 source records at 0x855c0c and reads the
condition pointers at 0xa2c118. One entry has no condition because its item is
already unlocked. The report composer at 0x31c798 concatenates quotation marks,
the condition, an achievement suffix, and a second line containing the item
name. The item getter reads the RPW part record's name pointer. Every report is
covered in both original-name and relocated English-name form. No condition
threshold or table ID changes.

The nine selectable upgrade choices come from the native table at 0xa26808.
The table also contains the unset and locked explanatory entries; these are
not selectable bonuses. The confirmation composer at 0x2f4570 combines a
UTF-8 quotation prefix, the selected native label, and its acquisition suffix.
The hook matches the complete converted string, leaving the selected bonus,
menu logic and the independent Are you sure line unchanged.

`tools.upgrade_oracle` executes both original PPC composers with bounded
adapters for string allocation, length, copying and the report sink. The item
adapter supplies the record/name pointer that the native RPW getter returns.
The confirmation oracle supplies the current menu selection in private test
memory and executes the original pointer getter and string assembly. These
are instruction-level checks, not an emulator playthrough. The final verifier
uses actual item names read from the built RPW archive and the final executable.
It checks all 80 lookup keys, all 23 native report compositions and all nine
native confirmation compositions through the produced hook.

The two Custom Bonus headers have a colored subject layered over a complete
black sentence. The English sentence previously duplicated that subject.
The black layer now contains only ` obtained.`; its origin joins the measured
colored `Custom Bonus` subject. The complete line keeps each native center.
The same repair covers the Ace Bonus layout. Native y, font metrics, colors,
icon position and row pitch remain unchanged.

The trophy pack has 40 files: structural configuration, two localized text
documents, two set icons and 35 trophy icons. Translate `TROP.SFM` and
`TROP_00.SFM`, preserving every trophy attribute and all non-text XML fields.
The original configuration and every icon remain byte-identical. Repack the
container with the original file order, identities, flags and alignment, then
recompute and verify its SHA-1. The obsolete SFM signature comment is removed;
this does not sign the modified metadata. Physical PS3/Vita compatibility is
not claimed.

RPCS3 selects a language-specific SFM when present, otherwise `TROP.SFM`;
translating both existing variants covers Japanese selection and the fallback.
Its trophy installation routine preserves existing `TROPUSR.DAT`. These facts
were checked in the primary [trophy module source](https://raw.githubusercontent.com/RPCS3/rpcs3/master/rpcs3/Emu/Cell/Modules/sceNpTrophy.cpp)
and [TRP loader source](https://raw.githubusercontent.com/RPCS3/rpcs3/master/rpcs3/Loader/TRP.cpp).
No emulator process, cache, trophy progress or savedata was modified during
this task.

A read-only proofreading agent examined 104/104 English fields against source.
HP and EN must reach upgrade level 10, rather than gain ten additional levels.
Spirit names are resolved from the bound command glossary across the trophy
category, including Fury and Luck. The source's simultaneous Spirit use is
expressed as concurrent effects; this is a wording interpretation, with no
change to its trigger. Item names retain their existing reviewed RPW values.

In-game visual confirmation of this exact build remains pending. The separately
reported malformed result-screen team name remains unresolved.

The regression suite completed 260 tests: 258 passed and two optional checks
were skipped. All matched build outputs passed readback. Report wording fits
a conservative 1,040-pixel budget at a 31-pixel glyph size; the longest condition
uses `5+` while preserving the simultaneous MAP-weapon requirement.
