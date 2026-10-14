# Screenshot repairs prepared for 0.5.30

The previous public release is 0.5.28. This candidate carries the completed
0.5.29 Spirit, weapon and native mission-composition repairs, plus five new
reports. The preserved 0.5.29 ISO remains an earlier local candidate.

Skill questions are assembled by the native PPC routine at 0x319038–0x319480.
The prefix, suffixes, level digit table and RPW skill records are source-bound.
The full family includes learning a new skill, a +1 skill, raising a learned
level, an innate-plus-learned level, and overwriting a skill. Both original
Japanese and relocated English name routes have complete draw-time keys.
The oracle executes the native branching/string assembly with bounded getter
and libc adapters. Gameplay skill IDs, PP prices and learning decisions stay
unchanged. Static failure/eligibility messages were already translated.
The meaning review preserves the distinction between purchased +N and intrinsic
Lv B + purchased N. No computed effective level or cap behavior is invented.

Movement masks retain four cells in Air/Ground/Water/Underground order and
preserve all 16 enabled/disabled combinations. Additional exact bindings cover
standalone masks and 0–99 numbered masks, supporting the composed display that
was still Japanese in the reported D-Trader card. The existing native terrain
converter/table repairs remain in place. New English masks use those same
compact terrain cells; disabled cells remain dashes.
The native formatter at 0x329948 emits U+30FC (the Japanese long-vowel mark)
for disabled terrain. It looks like a dash but differs from the U+FF0D minus
in static templates. Both key families are covered (3,131 distinct bindings).
All 16 real native flag combinations also pass composition and converter
readback using the repaired terrain tables; buffer canaries remain intact.

Nine FSSA widgets are changed. D-Trader uses Move, Mob., Acc., Range and Terr.
within its fixed colon column; the unit card uses Move; the owned suffix has
room for the unchanged three-digit count. Battleship selection uses Sel., Ship,
MV and Pil.; Left and Units are spaced around the unchanged remaining count.
The original Latin fill/outline masks, native colors, row pitches and numeric
coordinates are preserved. Source fingerprints and final pointer/coordinate
readback guard each edit. Minimum measured caption gap is greater than 8 pixels.

Earth Sphere is normalized in four dialogue rows and twelve encyclopedia
fields. The proper term was already canonical in the glossary. Generic sphere
references are unchanged. The name-only repair is idempotent and recorded in
an English audit; no Japanese dialogue corpus is exported.

In-game visual confirmation of this exact candidate remains pending. Public
delivery requires original/0.5.28 Retro Trans patches with complete ISO decode
round trips, followed by explicit publication consent for 0.5.30.
