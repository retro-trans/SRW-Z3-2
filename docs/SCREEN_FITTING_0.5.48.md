# 0.5.48: pilot separators, weapon warning and complete stage headings

The pilot-name lookup previously encoded the separator using the translated
font allocation. The game's name composer inserts the original CP932 `8145`
between already translated name parts. Complete keys are now built from the
active RPW name pieces and that native separator. The 810 unique keys support
both native orders and replace only the separator with an ordinary space.
There is no blanket punctuation substitution or save-name rewrite.

The warning uses two overlaid widgets, at source offsets `0x99ac4` and
`0x99ae4`. The full sentence is unchanged. Its lowercase `requirements` is
highlighted at the measured substring origin: 557.25 pixels, inside the full
line's 363–916 pixel bounds at size 28. Both widgets use explicit left origins
instead of independently centering different strings. Their color and vertical
geometry stay unchanged.

The native stage-prefix routine at `0x1dd4f0` chooses regular, prologue and
final prefixes from the stage record. Previous headings assumed regular
episode numbers and missed the four final branches. Verification executes
that routine for all 163 titled Tengoku records in both encoding modes,
then checks each complete heading against the installed translation lookup.
The final heading reads `Final Episode: World Without End`.

The 193 Tengoku stage records reference all 129 title IDs; 30 records have no
title. The broader title catalog contains 682 records and 342 distinct texts,
all with English. The 128 authored title-card translations are complete;
member 88 is already English. Final-stage artwork lives separately in EFF
member 107 and already says `Final Episode` / `World Without End`.

The incremental builder verifies the sealed 0.5.47 parent, reuses existing
English payloads and adds 864 keys in reserved executable space. It preserves
all 19,576 old lookup pointers and payloads, every executable byte outside
the recorded dictionary ranges, fonts, mapping, advances and unrelated
archive members. Only two UI widgets and version artwork otherwise change.
The final readback checks all 4,803 widgets, every new lookup, native heading
prefixes and native caption widths. These are source and executable checks;
live RPCS3 screenshot confirmation remains pending.

Release preparation uses the official Retro Trans 0.5.4 SDK with full-image
round trips from the original Japanese ISO and public 0.5.44. Creating a
GitHub draft or publishing requires explicit consent for 0.5.48.
