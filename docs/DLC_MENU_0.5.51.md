# DLC menu text and alignment — 0.5.51

The reported rules notice and scenario summaries were already translated as
whole paragraphs. Their native callers split them into rows before drawing,
so those lookups missed. The launch/claim dialog uses the system's UTF-8 font
and never reaches the game's translation hook.

The source-bound category contains 35 summaries, 29 prompt/fragment records,
nine short menu states and one four-line rules notice. All 74 records were reviewed against their
source. One summary's purpose clause is restored to its original row. No new
terminology was needed. Existing canonical names and glossary choices remain.

The fix adds 63 distinct row lookups, including shared gift descriptions,
and centers the rules notice with the existing scene marker. The menu uses
`Episode`, `Synopsis` and `Rewards` labels with separate measured columns.
The summary body uses a 27-pixel quad and the existing condensed alphabet
only where needed. All complete rows fit a 960-pixel body budget. Vertical
origins, row pitch, colors, normal letter shapes and font files are preserved.

All 29 native prompts use relocated UTF-8 payloads. The nine short menu states
are checked through their installed translation lookups. Short labels and the
blank reward continuation remove obsolete Japanese column padding. Their
allocations retain enough readable padding for the original fixed-size copy
instructions. Format operands and message row counts are preserved.

DLC-only adapters supply all 40 English menu titles (35 scenario/gift entries
and five packs) and 60 English Power Part names
to the native launch/claim constructor. They preserve the source table,
mission identifiers, reward amounts, native formatting and Yes/No behavior.
Unknown inputs retain the original conversion/lookup path. The old executable
gap has only 44 bytes free, so 2,340 bytes of adapters use an otherwise empty
ELF LOAD as a separate read/execute segment. No memory is writable/executable.
The text data LOAD grows by 64 KiB; all old lookup payloads remain intact.

Verification executes all 70 launch/claim combinations, all five pack-title
conversions and their existing description-label lookups, the actual rules-row
copy path, every new final lookup and the existing centering code. It checks
the complete compiled UI plan, all unaffected archive members, carried fonts
and narration. Source and result hashes, geometry and native English output
are recorded in `work/ui/review51_verified_0.5.51.json`. Image and Retro Trans
delivery evidence are recorded in `work/ui/local_release_0.5.51.json`.

This carries 0.5.50 and leaves translated DLC 0.5.49 and saves unchanged.
It remains an RPCS3-oriented build; this is not a PS3 hardware packaging fix.
Live visual confirmation is distinct from native instruction checks. No
GitHub release is authorized without explicit consent for this version.
