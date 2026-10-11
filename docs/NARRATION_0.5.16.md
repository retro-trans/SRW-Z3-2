# Full-screen narration coverage — 0.5.16

The earlier build connected 35 individually listed narration records. It missed
whole files, including the Sidereal invasion, occupation and Leyline cards in
the four reported screenshots. This build enumerates the complete narration
record format instead of adding another small list of offsets.

The source archive contains 34 narration members: 19–24 and 26–53. Their
headers define a two-byte big-endian record count and one-byte caption
capacity. Each record starts at `20 + index * (capacity + 30)`. The archive-wide
scan recognizes signature `262b263c` and requires exact member length,
terminated CP932 captions and matching member fingerprints. Member 25 has a
different `2424242a` signature and is the staff credit roll, outside this
narration audit.

All 197 nonempty narration records now have reviewed English. They contain
189 unique captions: 35 existing translations and 154 new translations. The
review includes adjacent rows and the later story introductions. Duplicate
captions use one shared translation. Full Japanese briefs remain in the
ignored local `work/tengoku/narration_briefs` directory; tracked translations
and evidence contain English, identities and fingerprints.

English retains one timed line per source record. Complete meaning is drafted
before fitting. Lines use the regular alphabet where it fits and the existing
85% condensed alphabet otherwise, with a 900-unit maximum. Blank timing rows,
page order, native state and every original narration member remain unchanged.
Dictionary bindings select relocated English at draw time.

Canonical names follow the existing glossary. Supplementary names and research
are recorded in `work/glossary/narration_terms.json`. The deliberate Heavenly
Prison wordplay matches the English title. The title footer now shows v0.5.16,
and the build retains the Retro Trans Tools-compatible pipeline and all earlier
fixes.

`tools.verify_narration` executes all 197 source-to-English bindings in the
final executable, checks line widths and original member bytes, and exercises
the four reported captions through the native centered drawer in both styles
at 28 and 40 pixels. Its cumulative evidence includes earlier UI, font,
Library, archive and ISO checks. Live emulator appearance still needs testing.

Regression: 246 tests run, 245 passed and one optional check skipped. The
testing image is `work/output/iso/0.5.16/Tengoku-hen-English-0.5.16.iso`.
Final executable checks passed for all 197 narration bindings and all 16
reported-caption centering cases. Evidence is saved to
`work/ui/narration_verified_0.5.16.json`; the authored review is
`work/ui/narration_review_0.5.16.json`.
All 82 files passed readback through both ISO directory trees. Image size:
5,284,167,680 bytes. SHA-256:
`e38ea9bc3bc45f16f0373eda67aaec55dc4f83ef2a00fd55bfc6542ce9bde5fd`.

```powershell
$env:PYTHONIOENCODING = 'utf-8'
& $py -m tools.narration_catalog
& $py -m tools.narration_catalog --apply
& $py -m tools.narration_translation
& $py -m tools.narration_translation --apply
& $py -m tools.title_screen --version 0.5.16
& $py -m tools.title_screen --version 0.5.16 --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -u -m unittest discover -s tests *> work/output/scratch/startup-0.5.16-tests.log
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_narration
& $py -m tools.verify_narration --apply
```
