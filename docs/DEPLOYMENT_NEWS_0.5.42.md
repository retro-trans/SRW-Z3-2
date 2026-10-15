# Deployment, terminology and war-front reports — 0.5.42

The four screenshots report crowded deployment captions, untranslated terrain
cells, the Psyco Waves spelling, an overwide Northern Europe headline and a
Japanese South America/Pacific Rim report.

## Deployment

`review42_layout` binds six captions to their original FSSA widgets. `Left:`
starts at x340.5 and ends before x409, leaving the native count in place.
`Sel.` ends before x77; `MV` ends before x403. The separate Team heading,
movement brackets, live values and controller state retain their own fields.
Only these yellow captions use the separate original-font alphabet.

The earlier terrain matcher accepted one four-character row. It missed four
ten-row columns, a two-row footer and two padded blocks. The new bindings cover
all seven blocks, 45 terrain rows, using the existing Air/Grd/Wtr/Und cells.
The four-cell pitch, blank padding, row count and state/colour bytes are retained.
This also avoids globally substituting Japanese characters used elsewhere.

## Terminology

The user explicitly requests **Psyco Waves**, including its capitalization.
Both glossary aliases are confirmed overrides. Four lowercase modifiers are
removed; all eight active dialogue references expand to this exact spelling.
The reported Amuro sentence retains its meaning and is wrapped by the existing
dialogue builder. Historical drafts are not active translation inputs.

## War-front reports

The old path performed Japanese-to-English replacement at the glyph drawer.
The native news constructor at 0x184c74 splits its source before that point.
The new plan relocates all 22 report paragraphs and changes the 38 verified
scenario-table pointers that supply them. Only those pointer words change;
scenario IDs, conditions and the original strings remain intact.
The constructor calls selector 0x1dcbfc, which loads this table through
TOC-0x41d8. Final verification executes that selector for all 38 occurrences
before reading each relocated source pointer.

The relocated input uses ASCII UTF-8, with each row under the constructor's
128-byte limit. Native splitting therefore sees the final intended rows.
Each resulting English row has an exact draw key selecting the current letter
shapes and a marker that centers that row by its displayed width. This is a
separate, explicit path from the old Japanese draw keys.

The Northern Europe report becomes:

> Northern Europe Front:
> Federation & Resistance Launch Counteroffensive

The combined report becomes:

> South America Front: Federation Launches Counteroffensive
> Entire Pacific Rim: All-Out Counteroffensive Begins

All rows fit 928 glyph units, equivalent to 1,160 pixels at the conservative
40-pixel news size. Existing condensed glyphs are used for the longest combined
reports. Every word of the existing reviewed English is retained.

## Validation and delivery

Tests cover all repeated terrain cells and their geometry, all report paragraphs
through the real native row-copy instructions, the exact glossary aliases and
all active references, then the compiled scenario pointers, draw lookup and
installed centering helper. The full build includes the 0.5.41 fix for all 143
linked-keyword entries and both description variants.

In-game visual testing remains pending; offline verification is not a claim
that these screens have been observed in RPCS3. Public delivery requires an
original-image patch and an upgrade from public 0.5.40, both validated with
Retro Trans Tools. Creating or publishing a release requires separate consent.
