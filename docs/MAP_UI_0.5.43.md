# Map UI corrections — 0.5.43

The four reported screenshots are retained under `work/ui/screenshots/`
with the `reported-review43-` prefix. They show the old behavior; they do
not establish visual confirmation of the corrected build.

The end-phase line joins two SB2T fragments around a live native team count.
The generic caption measurement rejects the native count cells and falls back
to fullwidth character counting. A marker on the prefix selects the existing
mixed-text centering helper for the complete assembled line. Both parts of
the message and the live count retain their meaning. The native helper is
executed at 28- and 31-pixel sizes for counts 0, 1, 9, 11, 99, 100 and 999.

The map panel's FSSA widgets 0x8a144/0x8a164/0x8a184 are separate Aboard,
Team and vowel-stroke fragments. `Aboard:` replaces the first; the other
two are blank. The caption ends at source x802.82, before the live count.
All widget geometry, style and selection flags are retained. This yellow
caption uses the existing separate original-font alphabet with its thin
native border. Ordinary lettering and spacing remain unchanged.

Member 5 of AIDDATAPACK has another component table, distinct from its FSSA
terrain widgets and the executable's UTF-8 cells. Rows 91–98 supply movement
types/restrictions and 117–120 supply terrain labels. These entries are
translated before composition using the existing one-cell Air, Grd, Wtr,
Spc, Und and Only glyphs. Four movement flags still occupy four cells;
disabled dashes and native per-field styling stay available.

Dialogue record `598:t_5:36` changes only `An Tenshi` to `A Tenshi`. The
compiled member is compared byte for byte with its certified parent after
that exact substitution; every other stage member stays unchanged.

The source-bound command `aid:6:511` is `Trans-Am`. The incremental build
redirects exactly one dictionary slot to its already allocated translation.
The original pool and all executable code remain unchanged. The installed
lookup is executed for this command and its separate activation question.
Both native caption states are also executed at two sizes, confirming the
translated width stays centered inside the command button.
Future full builds use the same corrected canonical text.

The parent is prepared 0.5.42; the public upgrade route remains 0.5.40.
Original and public-upgrade Retro Trans patches must both reconstruct the
same verified complete ISO before publication. Each new release still
requires explicit user consent; no GitHub release is created by these tools.

The full regression run passed 342 of 344 tests, with two optional checks
skipped. All four focused checks pass without skips. Compiled verification
is recorded in `work/ui/review43_verified_0.5.43.json`; both patch round trips
are recorded separately by the official release SDK.

Both official Retro Trans 0.5.4 complete-image round trips passed. All five
assets are recorded in `work/ui/local_release_0.5.43.json`. The original-image
patch is 204,181,528 bytes and the public 0.5.40 upgrade is 21,351,215 bytes.
Both reconstruct SHA-256
`aef256e93637155bda9a8d3b760c53cb7ae3993bc8ac3e3dd2282b5ee64d2ea9`.
Publication and in-game visual confirmation remain pending.
