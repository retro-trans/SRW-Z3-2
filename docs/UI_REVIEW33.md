# Reward reports, Arm Rakers and Back Log — 0.5.33

Carry all 0.5.29–0.5.32 repairs forward from public 0.5.28. Creating or publishing
0.5.33 requires explicit consent for this version.

The SC_GIFT_EXEC_B binding at 0xa1e8a8 selects descriptor 0x964f38 / entry
0x19d26c. It invokes the reward processor at 0x18bc18. Its message branch at
0x18c09c splits CP932 notices at LF, copies each into an independent 128-byte
report row and sets the report flag. The existing whole-message translation
keys therefore miss multiline notices after this split.

Pair each original Japanese paragraph with its existing reviewed English
paragraph. Include all 22 player-facing notices / 97 occurrences and their
36 distinct whole/line keys. Preserve both AG heading indentation variants
and all eight bonus amounts (50, 100, 200, 1000, 1500, 2000, 3000, 3500).
Developer-only diagnostics retain their earlier coverage. Stage literals,
reward values and conditional logic remain byte-identical.

Use the existing display-only centering marker and installed origin helper.
Its English width measurement centers each report at x=640 without changing
the font, baseline or native copies. No additional native code is required.
Execute all 22 real paragraph-copy branches, look up their actual output rows,
check full English and amounts, and exercise all 36 final centered payloads
with caller-state checks. Whole-message lookups also pass independently.

The glossary already says Arm Raker. Remove the sole active lowercase token
override in Takuya's row 419:t_1:178; preserve its other words and row identity.
Read back the complete encoded Arm Rakers row from the final stage archive.

Both Back Log guide variants carry the 0.5.32 measured Previous Quote / R1 gap
repair. Preserve the controller icons, next/previous navigation and fast
modifier. Record all three new reported screenshots along with the carried
source screenshots. Native execution and archive checks do not establish
in-game visual confirmation.

## Final candidate verification

313 regression checks ran: 311 passed and two optional checks were skipped.
Final archive/native execution covers all 22 report messages, 97 source
occurrences, 36 whole/line keys and the corrected Arm Rakers row. The carried
checks cover all 517 scene captions, eleven news profiles, 539 scene/news
origins, eleven layout widgets, native save copies/converters, all 101 distinct
SR conditions and 210 panels, Spirit terms, movement masks and defeat quotes.

All 82 disc files pass both directory trees. Both official Retro Trans 0.5.4
patch routes, original Japanese game and exact public 0.5.28, pass complete
ISO decode round trips to the same 5,289,279,488-byte image:
`6994227fe27fd4e28a96d1ba89965469b1f7aeffffdbe71b808e91200e955683`.
The five delivery assets, checksums, native evidence and pending-consent state
are recorded in `work/ui/local_release_0.5.33.json` and
`work/ui/review33_verified_0.5.33.json`. No GitHub release was created.
