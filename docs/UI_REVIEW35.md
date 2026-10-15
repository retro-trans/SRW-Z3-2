# Combined war-front updates — 0.5.35

The supplied East Asia / eastern North America and Midway / southern Europe
screenshots expose a missing draw-time binding. Their English translations
already existed, but the game copies each UTF-8 paragraph into a separate
128-byte row before drawing. A key for the complete message cannot match an
individual row. The 0.5.32 whole-message layout checks did not exercise that
constructor.

`tools/review35_news.py` enumerates the actual 376 scenario-table records and
selects every enabled, nonempty news message: 22 distinct messages. It binds
13 independent rows across six multiline messages, including the final
three-line worldwide report. The existing whole-message and single-message
bindings remain available. Original Japanese lookup keys, scenario records,
route IDs, camera/battle settings and reward counts remain intact.

Each new English row uses the existing scene-centering marker. Unlike the
two-row headline marker, it preserves the native row's vertical position.
The original English wording and existing condensed alphabet are retained;
the longest new row occupies 1,085 of 1,160 allowed pixels at the conservative
40-pixel font. Captured totals remain 18 Terminal Bases and 3 Central Bases.

The regression test reproduces all 13 misses in the prepared 0.5.34 binary.
The fixed version executes the actual constructor at 0x184c74–0x184d0c,
including strchr/strncpy/strcpy row copies, validates the eight-row allocation
canaries, and resolves every resulting paragraph through the native lookup.
Another 26 cases execute the installed centering code at two font sizes,
checking row position, caller registers and complete English payloads.

Reproduction: `python -m tools.review35_news` previews the six translations;
`--apply` records the guarded catalog. `python -m unittest tests.test_review35`
checks the before/after regression. Final built-asset readback uses
`python -m tools.verify_review35 --apply`, including all carried mission,
Library, reward, dialogue and layout checks and the exact 0.5.34 startup/font
archive identity.

Runtime visual confirmation remains pending. The public testing workflow
requires validated Retro Trans delivery; publishing or creating a GitHub
release for 0.5.35 requires explicit consent under AGENTS.md.

## Prepared delivery

Final readback passed for all 22 messages across 38 scenario occurrences,
13 new row keys and 26 centering cases. All earlier native UI, mission,
Library, reward and dialogue checks pass on the final executable. The suite
ran 319 tests: 317 passed and two optional checks were skipped. The shipped
stage wrapper was independently decrypted and its script bytes match 0.5.34.

All 82 ISO files passed both filesystem-tree checks. Both official Retro
Trans 0.5.4 routes (original game and exact public 0.5.28) decoded to the
same 5,289,541,632-byte ISO, SHA-256
`93ad9ea9c3a6c6e720874bf443d6f2990164b0bcb48058d4861b2f0ac3798b25`.
All five protocol assets are recorded in `work/ui/local_release_0.5.35.json`;
complete native evidence is `work/ui/review35_verified_0.5.35.json`. Release
notes are in `docs/RELEASE_0.5.35.md`. Publication remains pending consent.

The three images in `work/ui/news_0.5.35` are inspected native-font layout
previews, not in-game captures. The user's two original screenshots are
preserved as `work/ui/screenshots/reported-review35-*.png`.
