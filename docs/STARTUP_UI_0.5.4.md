# Startup screenshot fixes — 0.5.4

Five user screenshots exposed issues in the 0.5.3 testing build. Originals are
saved under `work/ui/screenshots/0.5.3-*.png`; they show actual game output.
No emulator navigation or cache changes were performed by the agent.

| Screenshot | Change | Bound source |
| --- | --- | --- |
| Link overflow / No | Five lines of full explanation; selected No anchor adjusted to its English background | Member 0 widgets 0x93404, 0x93964, 0x939a4, 0x993c4, 0x99444 |
| Naming overlap | Caption `Squad:`, moved 16 native pixels left | Member 0 widget 0x91844 |
| Opening page 1 | Reviewed translation of all four lines | Member 19 offsets 0x14c–0x236 |
| Opening page 2 | Reviewed translation of all six lines | Member 19 offsets 0x5de–0x764 |
| Default MC name | `$n` now displays Hibiki for the default saved name | Getter 0x1faae0 |

The viewport is 1280×720. Link text uses 28px glyphs and a 38px line pitch;
the conservative width cap is 1180 atlas units (1032.5 native pixels). The
five wrapped lines retain exactly the original English word sequence.
`tools.startup_layout` previews edits before `--apply`, producing the source
hashes and coordinates in `work/ui/startup_layout.json`.

The grey Yes/No string uses narrow English advances. The selected No is
centred/positioned using the original Japanese by the native wrapper before
the dictionary swap. Its anchor therefore moves by the difference between
the native Japanese prefix and the rendered English prefix. Both selected
No variants retain their original source pointer, flags, colors and text;
the FSSA patch changes only their guarded x coordinates. General text
measurement remains unchanged and other centred labels still require QA.

The opening resides in fixed 78-byte records in AIDDATAPACK member 19,
rather than the stage dialogue archive. `tools.opening_narration` verifies
the complete pristine member fingerprint and exposes 28 exact keys. English
uses the existing draw-time dictionary, with no edits to narration records,
timing, page boundaries or background references. All six opening pages are
translated. The widest row is 894 units at a 32px glyph size; the budget is
900. Meaning and deliberate sentence fragments are documented in
`work/ui/opening_review.json`. Source Japanese remains in ignored local data.

The three name getters at 0x1faae0/0x1faae8/0x1faaf0 feed only the display
substitution builder at 0x1fb2b8. A fingerprint gate pins that consumer.
The new leaf stubs compare the complete default CP932 name including NUL,
return relocated VWF English on a match, and return the original pointer
for custom/empty/null values. They never store to editable or saved buffers.
CR, LR and nonvolatile registers survive. `$F` retains its saved order and
native middle-dot separator. A nickname over 20 bytes uses `K.` for the
default surname in `$F` only, to protect its 40-byte payload plus NUL;
standalone `$l` still shows Kamishiro. Custom surnames are unchanged.

Instruction tests cover exact defaults, prefixes, suffixes, empty/null names,
both full-name orders, long nicknames, source drift and patch byte isolation.
These tests do not constitute a live emulator test. In-game QA still needs
both Yes/No states, the naming field, the opening, normal dialogue and backlog.

Build with `python -m tools.game_build` for the dry run, then `--apply` for
matched files under `work/output/builds/0.5.4`. Build the local testing image
with `python -m tools.iso_write`, then `--apply`. Public v0.5.2 assets remain
unchanged; a subsequent public release must follow the existing Retro Trans
manifest/patch workflow. The 23 previously unresolved generated UI bindings
are outside these startup fixes and remain recorded in the build report.

Verified output: `work/output/iso/0.5.4/Tengoku-hen-English-0.5.4.iso`,
5,284,036,608 bytes. SHA-256:
`a019288059acf6f64cb8e1ecf67bdacea39d95397816f24eabaf0333c97df29e`.
Both directory trees verified all 82 files. The regression suite ran 197
tests (196 passes, one skip); final-executable probes executed all 28 opening
keys and 29 default/custom name cases. `tools.verify_startup_ui --apply`
saves hashes, screenshots and verification reports to
`work/ui/startup_0.5.4.json`. The decoded stage CPK has the identical SHA-256
as 0.5.3, although its encrypted SDAT envelope changes during packaging.
