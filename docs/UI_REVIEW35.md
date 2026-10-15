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
