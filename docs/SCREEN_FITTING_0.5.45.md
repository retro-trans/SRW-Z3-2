# Screenshot text fitting — 0.5.45

The four reports are bound to their actual draw paths. Public testing remains
on 0.5.44 until a new release is explicitly authorized and published.

- The D-Command list retained Japanese bullet prefixes. Its six preloaded
  rows and six selected help keys now use the existing measurable 32-unit
  invisible padding. No glyph artwork, font advances, colors, widget geometry,
  disabled states or row pitch change. Keep Combo's complete effect uses two
  shorter native help rows, clearing the footer arrows and D Command label.
- `628:t_1:3` keeps the full Wrath Babylon Imperial Palace / Spirit Quanta
  Absorption System location on two centered lines. The existing scene marker
  measures the longest line. Shorter lines receive measured space padding;
  the portrait and right margin remain clear at the checked glyph sizes.
- `Hyperdim. Target Lock` abbreviates the item name consistently in the RPW
  names, its translation slice and the upgrade-message binding. The rendered
  name ends at x1048.25, leaving 71.75 pixels before the conservative count
  boundary x1120. The RPW correction changes only its shared name allocation;
  stats, effect descriptions, pointers and inventory values are preserved.
- The reported timed narration row measured exactly 900 units, passing the
  old width check despite extending from x224 to x1349 at a 40-pixel quad.
  A source-bound 800-unit limit selects the already allocated narrower
  alphabet. All words and punctuation remain; the new right edge is x1176.5.
  Timing bytes and adjacent narration rows are unchanged.
- Both Chaos Caper references are included from the preceding source correction.
  The active glossary and seed both retain the user's confirmed spelling.

The incremental parent is public 0.5.44. Rebuilds first reproduce the parent
script members with the old caption/name and reject unrelated changes.
The executable changes only dictionary values/pointers in reserved text space;
the installed lookup and centering code stays identical. The font archive,
allocation and advance table remain identical to 0.5.44.

`tools/review45_text.py` previews source edits and measured bounds.
`tools/review45_build.py` builds the candidate after its dry run.
`tools/verify_review45.py` reads final archives, runs installed lookup/origin
helpers, compares the fresh full-build UI catalogue, checks all 4,803 widgets,
and records the full ISO verification and screenshots. The release preparer
uses official Retro Trans 0.5.4 with original and exact-public-0.5.44 inputs.

In-game visual confirmation remains pending. No GitHub release or draft is
authorized by the screenshot reports alone.

The candidate image verifies all 82 files through both ISO filesystem trees.
SHA-256: `bc1edfb8c1a38a9190834b5ea0bbc1887cf4c6fa1ca8e404e54fa250d22d8c7e`.

Both official Retro Trans 0.5.4 complete-image patch round trips passed.
All five delivery assets are validated. The original-image patch is
204,175,412 bytes; the public-0.5.44 upgrade is 21,049,982 bytes. Both
reconstruct the same verified image. Publication remains pending explicit
consent for 0.5.45.

The final regression run completed 348 tests: 347 passed, one skipped.
Its Back Log corpus now has 124 rows over the old 128-byte limit, rather than
125: the reported palace caption's former 132-byte row is now 70- and 66-byte
rows. The native ring, row-copy, link and reset checks pass with that updated
inventory. Final delivery readiness is `work/ui/local_release_0.5.45.json`.
