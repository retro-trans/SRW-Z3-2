# English 0.5.50 — timed narration alignment

Prepared for public delivery; publication requires explicit consent.

All 197 timed narration lines now center using their actual English glyph
widths, including the DLC scene beginning “Before the overwhelming military
might of the New Earth Empire.” Short lines no longer cling to the old left
edge, and long lines stay within the screen margins. Wording, font choices,
vertical positions, transitions and timing are preserved.

This is a base-game update for BLJS10299 in RPCS3. It carries the prepared
0.5.48 corrections and remains compatible with DLC English 0.5.49. Existing
translated DLC does not need reinstalling for this narration fix.

Retro Trans delivery includes complete-image patches from the original
Japanese ISO and exact public English 0.5.44. Their source checksums are in
BUILD-MANIFEST.json. Use the patch matching your source; the result is the
complete English 0.5.50 image. Keep your original image and saves.

Verification covers 197 final text bindings and 394 native origin cases at
two glyph sizes, unchanged narration records and fonts, all carried assets,
and both ISO filesystem trees. Full regression and patch round-trip evidence
is recorded in `work/ui/local_release_0.5.50.json`. Live visual confirmation
remains pending because the Windows capture helper could not initialize.

See [the technical alignment notes](NARRATION_ALIGNMENT_0.5.50.md) for scope
and preservation checks. The known RPCS3-oriented executable packaging remains;
this is not a PS3 hardware compatibility update.
