# Scene captions, Sub Order, news, saves and movement — 0.5.32

All earlier prepared repairs carry forward. Public 0.5.28 is the delivery
baseline. Creating or publishing 0.5.32 requires explicit consent.

## Location captions and news

517 decorated location records have a blank speaker and one nonempty caption.
Their Japanese padding assumes full-width words. At encoding time, remove that
padding, use spaced slashes between location components, keep all original
blank rows, and prepend a display-only marker. The drawer removes the marker
and centers the complete caption at x=640 using its actual live font quad and
glyph advances. Preserve every word and record identity. The widest reviewed
caption is 1,298 units, or 1,135.75 pixels at the 28-pixel scene font.

Eleven long or combined news records use two centered rows. The reported
headline becomes “Central Asia Front:” then “Assault on Imperial Capital Wrath
Babylon Fails.” Preserve original combined-news paragraphs. Four combined
headlines use the existing 0.85 condensed alphabet to fit both complete lines.
Each row fits a conservative 1,160-pixel budget at a 40-pixel quad. Pad shorter
rows to the same center and lift the first baseline by half the native pitch.
The separate three-row worldwide-result record retains its existing layout.

The maximum-line-width helper is restricted to marked content. Keep the
existing general width helper, selection anchors and save markers. Preserve
all scratch GPRs, CR, LR and temporary floating registers. Share the marker
handler to fit the original checked executable gap; no segment permissions
or executable addresses are changed.

## Sub Order and guides

Use Undeployed / Capacity / L: (left) around the fixed counters. The actual
Sub Order numeric elements are at 0xb647c, 0xb6488 and 0xb6494, with anchors
x=305, 206 and 327. Suppress the independent pilot-word fragments. Keep every
numeric element, style, count and row pitch unchanged. Shorten Fill Slots and
Switch Mode. Fit both Back Log guide variants with a measured blank interval
for the R1 icon; preserve line/quote navigation and the fast modifier.

The Team Setup movement caption changes to MV in both footer rows and moves
nine pixels left, clearing its separately drawn brackets. Its movement number,
slash and terrain cells retain their coordinates. All 16 masks, both disabled
dash variants and numbered forms carry from the 0.5.30 repair.

## Save questions

The exact second-line draw key already matches Continue playing in the earlier
build. Cover the native route earlier as well: three display-only TOC pointers
select relocated UTF-8 carriers for both complete English paragraphs. The
existing private Unicode converter maps those letters to the allocated Latin
glyphs. Original strings, save operations, question kind and choices survive.

Execute the native constructor 0x168a1c through its paragraph splitting and
128-byte row copies, stopping only at UI registration 0x9af68. All six lines
fit those buffers. Execute the real converter in both supported locale models.
Check the saved-register boundary after the four native row buffers.

## Verification

Four focused checks cover all 539 scene/news origin executions, caller state,
complete headline wording, fixed icon/numeric slots, and all save paragraphs.
Final verification reads all 517 caption occurrences, eleven headline payloads,
eleven changed widgets and all three relocated save pointers from the actual
archives/executable, then runs the carried checks and ISO verification.
Instruction and archive checks do not claim in-game visual confirmation.
