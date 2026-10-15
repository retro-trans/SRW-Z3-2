# Intermission, Library and scenario chart — 0.5.11

**Historical coverage correction (0.5.41):** the executable dictionary and
Library archive checks recorded here did not cover the linked popup's actual
`MTV_ALL_KEYWORD_DEF.CPK` data. Live inspection of 0.5.40 established that
separate source; see `docs/KEYWORD_POPUPS_0.5.41.md`. The older converter tests
below are valid for the tested consumers but did not verify this popup route.

The five reported screenshots are addressed in the local RPCS3 testing build.
The Z3 Rodin Bold font and advance table are retained. The title version is
updated to v0.5.11 with the existing retro-trans credit. Live layout and
runtime confirmation remain pending user navigation.

## Intermission and Library captions

`tools/intermission_layout.py` binds 79 text widgets to source member and
widget hashes. The main menu uses compact Training, Upgrades, Team Setup
and D-Trader captions. Both ordinary and highlighted states use measured
English widths. Fragmented Team Setup, D-Trader, PS Store and Rengoku Link
captions draw from one complete first widget; their old suffix widgets are
empty. Navigation, selection states and control IDs remain native.

The footer uses Ep, Clear, turns and Ships. Its native turn-number slots
remain in place. Separate score/deployment unit suffixes are suppressed.
The six Library caption states have no quotation marks; their native special
mode 0x01 and text metrics remain unchanged. Their X correction compensates
for the original fullwidth caption offset and the measured English width.
The correction needs confirmation in game.

The plan lives in `work/translation/en/ui/intermission_layout.json`; the final
combined FSSA readback includes this plan with the previous layout repairs.

## Why the linked popup still showed Japanese

The archive Library translations were already complete, including Shikuu.
The linked-term popup uses another table in the executable. It has 143
keyword descriptors grouped by kana, with physical order different from the
stable Library ID. Each descriptor has name, series and two description
pointers, followed by a flag and ID. Translating the archives did not update
those native description pointers.

`tools/library_runtime.py` locates and source-checks every descriptor by its
shape, ID and original text fields. All 286 description pointers now reference
the expanded and wrapped English Library prose. Original lookup names,
series pointers, flags and IDs remain byte-identical.

Native UTF-8 carriers use reserved E100–E15E Unicode cells mapped to the
existing Latin glyphs. Copied wrapped lines still use the original converter.
Complete owned descriptions use a range table at its two callers to select
the matching pre-encoded English pool. Substring positions are converted to
the corresponding CP932 byte offset. This avoids the fixed native UTF-16
stack array and shared output buffer for long prose. All other strings take
the untouched native converter. Code is placed in the executable segment;
the checked range table and scratch word are in writable data.

Final verification executes 572 owned consumer cases, a longest-description
substring, three fallback cases and four native converter cases. It checks
the complete prose bytes and unchanged native output buffer. No description
is shortened or truncated to fit the old buffer.

## Library audit and chart

The final audit covers 143 keyword, 539 pilot and 331 robot entries: 1,013
records, 5,838 rendered display fields and 2,026 description variants. It also
executes the final draw hook for all 500 executable Library display occurrences.
No remaining kana/kanji is present in those rendered display fields. Internal
fields and original lookup keys remain intact.

`tools/chart_art.py` changes EFFPS3 members 234–237 using guarded source hashes.
All four header states read Scenario Chart. The two chapter backgrounds read
Heavenly Prison and Time of Hell, using Z3's native chart lettering approach.
Only the declared header/background lettering rectangles change; animation,
texture descriptors, controls, borders and other pixels remain native.

`tools/operation_layout.py` covers full prologue headings with either no gap,
an ASCII space or a fullwidth space before the quoted title. It also covers
independently drawn quoted stage titles and episode numbers.

## Verification and reproduction

The combined build passes 234 regression tests: 233 passed and one optional
check skipped. Build-time readback checks all translated Library members,
matched archives, the executable, font pages and stage/battle text. The final
evidence tool also rechecks the title and all previous startup/battle layouts.

Use the bundled Python documented in `BUILD_ISO.md`:

```powershell
& $py -m tools.intermission_layout
& $py -m tools.intermission_layout --apply
& $py -m tools.chart_art
& $py -m tools.chart_art --apply
& $py -m tools.game_build
& $py -m tools.game_build --apply
& $py -m tools.iso_write
& $py -m tools.iso_write --apply
& $py -m tools.verify_intermission_library
& $py -m tools.verify_intermission_library --apply
```

Evidence: `work/ui/intermission_library_0.5.11.json`. Original screenshots are
preserved in `work/ui/screenshots/reported-0.5.11-*.png`. Native chart previews
are in `work/ui/textures/scenario_chart/`; they are decoded texture previews,
not in-game captures. The testing ISO is
`work/output/iso/0.5.11/Tengoku-hen-English-0.5.11.iso`. The public release
remains 0.5.2; the ISO is a local testing artifact and is not published.

The ISO contains twelve matched replacement files. All 82 files are verified
through both directory trees. Size: 5,284,167,680 bytes; SHA-256:
`91496c15987e8c24efa5b870041f8b7e2e89b05c224e054587eb94fccc383922`.
The 247-cell font mapping, font archive, RPW, Library archives and battle voice
are byte-identical to 0.5.10. The same stage plaintext is repackaged as SDAT.
