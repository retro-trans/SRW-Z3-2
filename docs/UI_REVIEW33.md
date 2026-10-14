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
