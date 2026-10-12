# Public 0.5.18 screenshot review: Library, Zuul, team width and map save

Prepared version: 0.5.27. Publication requires consent for this version.
In-game visual confirmation remains pending; all earlier prepared fixes carry.

1. The Library Full Name overlap is the same shared FSSA label at original
   widget 0x9cd64 covered in 0.5.19. Its prepared text is Name. Preserve its
   font, alignment, origin and row pitch, and the separate complete mech name.
   Check that exact final widget again instead of altering the name value.

2. The user selects Zuul / Emperor Zuul over prior Xul and Zul. Apply a word
   boundary name pass across the active glossary, Library, executable, RPW,
   team labels and battle voice fields. Preserve Geara Zulu and Rozen Zulu,
   source quotations and historical exports. Confirm active expanded English
   contains no old spelling. AGENTS.md and the dialogue style guide protect
   this spelling during future proofreading; updated glossary entries record
   explicit user approval over the earlier researched romanization.

3. Sheryl's 194:t_1:82, source SHA a87061d96e, reassures fellow prisoner Ranka
   that Alto and their team will rescue them. Read-only meaning review examined
   19 source and 19 English neighboring records, 194:t_1:74–92. Keep the wording,
   deliberate ellipsis, controls and row identity. The renderer had budgeted
   $c as two literal characters, although it becomes the six native full-width
   cells of the team name. The default source is UTF-8 at file offset 0x8cc1c0.
   Reserve 192 units, including with condensed Latin profiles. Both validator
   and builder use the same measurement. All 800 records using $c fit their
   independent three-row budgets; the preview changes wrapping in 444 records.
   This reserves the default name's width; longer custom team names have not
   been verified. No saved name or native name field is rewritten.

4. The complete save question at UTF-8 VA 0x892748 already has the reviewed
   English Save complete / Continue playing. The screenshot indicates that
   the game draws its second paragraph independently; the whole-message lookup
   misses that fragment. Cover both whole messages and individual lines for
   all three map save dialogs at 0x892668, 0x8926d8 and 0x892748. Five distinct
   lines cover six occurrences. Validate their source bytes and exact converter
   keys, preserving save operations and Yes / No behavior. This does not alter
   the separate OS save-data dialogs.

Evidence: work/ui/review27_name_audit.json, review27_dialogue_audit.json,
work/translation/en/ui/review27_messages.json and final build readback.
