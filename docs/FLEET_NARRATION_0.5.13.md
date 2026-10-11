# Enemy-fleet narration — 0.5.13

The reported two-row narration was absent from the English catalogue. It now reads:

- Breaching absolute defense lines on all fronts, the enemy fleet
- descended toward Earth.

The continuation matches the original sentence boundary. The first row uses
the existing condensed Z3 Rodin alphabet at 835 advance units; the second uses
the normal alphabet at 394 units. Both fit the conservative 900-unit caption
budget. No line is merged or split, and the source rows and timing stay intact.

Meaning review examined both requested rows, the following two-row page and
the preceding three-row military report: seven context rows for a two-row
translation slice. The final wording preserves the breakthrough on all fronts,
the enemy fleet subject and descent toward Earth. It does not imply landing.
No unresolved referent or meaning uncertainty remains.

`tools/fleet_narration.py` guards AIDDATAPACK member 27 with its full SHA-256,
`8e046c881365f6fb4436d7bb2a4f64a8af18c41b03b69dd6deb0234f63c62c52`, and
binds rows at `0x1a4` and `0x1f4`. The English catalogue is
`work/translation/en/ui/expanded/fleet.json`. The draw-time dictionary supplies
English without changing the source's fixed records. The cumulative verifier
executes both final entries, checks their encoded text and width, verifies the
unchanged source member, and retains all previous font, title, Library and UI checks.

The title footer shows v0.5.13 with the existing retro-trans credit. This is a
local testing build; public release 0.5.2 is unchanged. In-game confirmation
remains pending user navigation.

Regression: 238 tests run, 237 passed and one optional check skipped. The
matched font retains 249 cells; no new glyph allocation is required.

The testing image is `work/output/iso/0.5.13/Tengoku-hen-English-0.5.13.iso`,
5,284,167,680 bytes. All 82 files passed readback through both ISO directory
trees. SHA-256: `030050b0a79abfd6319982dee999f0fd567a9889db4efad5d8c09047bfbe935a`.
Final caption execution and cumulative verification are recorded in
`work/ui/briefing_levelup_0.5.13.json`; the reported screenshot is saved under
`work/ui/screenshots/reported-0.5.13-fleet-narration.png`.

```powershell
& $py -m tools.fleet_narration
& $py -m tools.fleet_narration --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -m unittest discover -s tests
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_briefing_levelup --version 0.5.13
& $py -m tools.verify_briefing_levelup --version 0.5.13 --apply
```
