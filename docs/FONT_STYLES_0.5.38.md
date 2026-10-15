# Independent font styles — 0.5.38

The user confirmed that dialogue and narration should retain the current
lettering and lose only its added outline. The earlier global font encoder
dilated every generated mask by two texels, so the border also appeared on
white dialogue, names and numbers.

Ordinary Rodin glyphs now repeat their existing fill mask in the G8B8
coverage plane. They keep their exact ink, antialiasing, baseline and
advance; there is no outer border. Clearing the coverage plane instead
would make the letters invisible and is deliberately avoided.

Selected yellow labels use the separate `@native-label:` alphabet. Its
41 glyphs copy both planes from original font page 1; only blank horizontal
margins are removed. No stroke is generated or thickened. The new layout
routes Team, Mech and Kills in 19 unit-list headings to that alphabet.
Existing explicitly selected native labels retain the same glyphs. Native
PP / Next-Lv source glyphs and their widgets remain untouched.

The incremental builder checks all 301 codepoints and advances against
verified 0.5.37. It proves that all ordinary fill pixels are identical,
all native-label pixels are identical, all other atlas cells are identical,
and all 4,803 UI text widgets keep their geometry, colors and states.
Only the selected headings change their encoded font selection. The
executable and stage archive remain byte-identical, preserving the backlog
storage fix and every translated entry.

`work/ui/fonts/0.5.38-font-comparison.png` compares actual atlas masks. It
is a generated comparison, not an emulator screenshot. Final archive/ISO
readback and Retro Trans round trips are recorded separately; in-game
visual confirmation remains pending.
