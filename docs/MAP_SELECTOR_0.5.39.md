# Consistent map selector — 0.5.39

The two choices used separate source fragments: Allies / plus a singular
Enemy in one state, and a singular Ally plus / Enemies in the other. The
fragments also used different sizes and origins, so the slash and words
shifted when the selection changed.

Four source-bound FSSA widgets now use the same pair, `Allies / ` and
`Enemies`. Both pairs have identical 26px geometry and fixed origins;
native colors and selection flags remain intact. The measured 204.75px
label fits the 220px command button with 7.625px per side. Global Ally and
Enemy terms used elsewhere are not pluralized.

The incremental build carries the verified 0.5.38 executable, font styles,
dialogue and all unrelated assets. Final readback compares all 4,803 text
widgets: only the four selector records change text and approved geometry.
Twelve focused checks cover state equality, one separator, fit, native
colors/flags, font masks and surrounding menu layouts. Earlier full
regression evidence is carried by matching asset hashes.

The title version stamp is the only other game change. Screenshots supplied
by the user are preserved as reported-state evidence; in-game visual
confirmation of the new build remains pending.
