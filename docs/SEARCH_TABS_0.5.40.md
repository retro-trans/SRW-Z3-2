# Search tab positioning — 0.5.40

Spirit and Skills used untranslated source strings for native positioning
and received English through the later draw-time lookup. Their selected
and unselected widgets could therefore use Japanese metrics before drawing
English. Abilities already had English stored in both widget states and
was reported to remain correctly positioned.

Four source-bound widgets now store Spirit or Skills before native text
measurement, following the existing Abilities treatment. All coordinates,
font metrics, native center flags, colors and selection fields remain
byte-identical. The selected/unselected font-size cue is preserved; the
center anchors remain 359.5px for Spirit and 639.5px for Skills. Both
Abilities widget records and strings are preserved.

The final readback compares all 4,803 UI text widgets against verified
0.5.39. Only four text pointers/strings change. It preserves all other
widget text and every geometry/style byte. Fonts, executable, stage
dialogue and unrelated archive members retain their certified hashes.
The title stamp is the only other game change.

Focused tests cover English availability in all four states before
centering, the working Abilities control, exact geometry/style isolation,
the preceding side-selector fix, surrounding menus and both font pages.
Twelve cases also execute the installed caption renderer through its real
glyph-drawer entry, covering all six tab widgets in both native modes.
They check the computed center, text, Y coordinate and caller registers;
renderer calls are not mocked.
The ISO and Retro Trans round-trip reports are recorded separately.
In-game visual confirmation remains pending.
