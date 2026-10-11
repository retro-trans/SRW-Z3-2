# Map and Spirit menu layouts — 0.5.7

This local testing build addresses the five user screenshots. It keeps the
SRW Z3 Rodin Bold profile and previous link, dialogue and startup repairs.
In-game confirmation remains pending user navigation.

The ordinary centered drawer previously corrected only UTF-8 captions after
the font-mode branch. The new guarded interception at Tengoku VA 0x14a24
measures translated CP932 and UTF-8 captions before that branch, using the
live font quad and matched advances. Native/unknown strings retain the original
normal or alternate font path. CP932 Yes/No labels retain their existing
selector measurements and anchors. Instruction tests cover both font modes,
native fallbacks, short/empty strings and preserved register/CR/LR state.

The map menu contains two multiline FSSA text widgets. Each line needs its
own spacing because the drawer resets its pen on a newline. The two widgets
remain left anchored at x=1030, with their original 31-pixel font and line pitch.
Measured invisible prefixes center Search, Objectives, Battle Report, System,
Unit List and Quick Save at x=1140 within half a font advance unit. Blank
lines and selection flags remain unchanged. Three transparent cells with
advances 1, 2 and 4 supplement the existing 9-unit space; they add no visible
art and do not change the normal font raster profile.

| Binding in pristine member 0 | Change |
| --- | --- |
| 0xab904 / 0xab924 | Center six visible map-menu lines independently |
| 0x96e24–0x96f04 | Settings 1 / Settings 2, all eight tab-state widgets |
| 0x96f64 / 0x97144 | Shorter Abilities tab in both Spirit-screen states |
| 0x98564 | Teams Defeated / Total Kills / Units Lost |
| 0x98544 | Move live team counter 64 native pixels left; allow three digits |
| 0xb7fb8 | Move the separate right-aligned team number by the same amount |
| 0x1dd178 | Translate assembled prologue heading before the widget draws it |

The source-bound translation/layout plan is
`work/translation/en/ui/menu_layout.json`. Only checked text pointers and x
coordinates change in these widgets; colors, line pitch, selection state,
native counters and statistics remain intact. Full FSSA readback proves that
unrelated bytes and the original string pool are preserved.

The team number is a separate 12-byte type-15 element, bound to numeric
style 45. Its original endpoint is x=503 (plus the style's -0.5 pixel offset),
beside the suffix at x=503.5. Both coordinates move 64 pixels left, keeping
their one-pixel gap. The adjacent numeric elements are the kills and losses
at y=552 and y=600; their positions and values are unchanged. Readback and
tests cover the reported zero and totals through three digits. The native
six-digit cap is preserved; larger totals still need a separate layout check.

The existing two exact prologue-heading keys are retained. The new guarded
formatter-return binding translates the generated heading before its consumer
at 0x30f700 passes it to the widget drawer. The native path
0x2d8bf8 → 0x5fc64 → 0x5fad4 → 0x5fa64 passes the text pointer onward
as r8 to 0x5e2a0 without copying it into a fixed-size buffer. The native
64-byte formatter buffer is unchanged; English remains in relocated storage.

Testing output: `work/output/iso/0.5.7/Tengoku-hen-English-0.5.7.iso`.
Final layout evidence and the five original screenshots are recorded in
`work/ui/link_layout_0.5.7.json`; font/opening/name checks are in
`work/ui/startup_0.5.7.json`. Public release assets and emulator state are not
changed. The other mission descriptions retain the separate byte-limit audit
recorded in the 0.5.6 layout document.

Final validation: 213 regression tests, 212 passed and one optional check
skipped; 16 installed helpers, 36 caption centers, six map-menu line centers,
159 text-widget edits and one numeric-element coordinate. Both font pages
match all 214 allocated glyphs and their advances. All 82 ISO files match
through both directory trees; final SHA-256:
`70b32536eac05b854eb4ae1212a7a5d96d9de5be7906df234ef46c7a29224c64`.
