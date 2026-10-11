# 0.5.22: labels, tutorial rows and parts movement

The five reports are from public 0.5.18. This build carries the unpublished
0.5.19–0.5.21 fixes. Publishing any GitHub release still requires explicit
consent for this version.

`review22_layout` binds each changed FSSA widget to the original text and
32-byte widget hashes. English captions move or shorten around independent
values. Live numbers, names, arrows, ranks, colors and row pitch stay intact.
Selected confirmation words are left-aligned with the neutral Yes / No row;
only their native count-centering bit is cleared.

The yellow captions use proportional copies of the original page-1 Latin
letters. `native_labels` trims horizontal blank margins but preserves every
fill and outline texel and vertical position. Both output font pages receive
these masks. No synthetic stroke thickening is used for these captions. The
neutral and colored emblem footer captions use identical encoded letters.

`tutorial_layout` limits the 23 combat/team selector titles to 320 pixels and
fixed tutorial rows to 980 pixels, at a 28-pixel glyph quad. Long rows use the
existing condensed alphabet; two exceptionally long rows have reviewed shorter
wording. No rows are added or merged. Color controls retain their positions.
The proofreader checked 15 assigned items against 146 source rows; the other
selector meanings remain unchanged.

`parts_movement` patches three four-byte UTF-8 cells read by the actual parts
formatter, rather than relying on the separate unit-status movement tables.
The source ELF hash, TOC binding, formatter instructions and exact cell bytes
are guarded. Existing private Unicode conversion supplies readable compact
Air / Grd / Wtr cells. All eight flag combinations are exercised through the
real converter, preserving unavailable dashes and unchanged numeric fields.

Final verification checks installed label bytes, origins, native masks on both
font pages, exact tutorial lookups, both emblem caption paths, movement cells,
prior fixes and the final ISO. In-game confirmation of this build remains
pending; source and instruction checks do not substitute for emulator visuals.
