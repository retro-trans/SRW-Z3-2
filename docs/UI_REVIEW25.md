# Public 0.5.18 screenshot fixes prepared for 0.5.25

The seven reports cover a room caption, Ameria, two D-Trader unlock reports,
Team Setup, Mao's dialogue font, and Episode 11's SR condition. This build
carries the unpublished 0.5.19–0.5.24 fixes. Publication requires consent.

The Gargantia room caption has seven source occurrences with fingerprint
36755227d4. Use the full fleet token, add visible spaces and a slash between
the fleet and room labels, and center the final expanded line by measured
font advances. Keep both original blank rows and the same three-line block.
All unrelated captions retain their existing layout.

Ameria replaces Amerria in active glossary and location art. Dialogue tokens
resolve through that glossary; historical drafts retain their old evidence.
Record the user's choice in AGENTS.md and the dialogue style guide.

Both Team Setup states keep the title's native size and color. Move Next
and its live counter 19 pixels right; shorten its caption to Next:. Preserve
the two-digit field contents and the rest of the grid. The title's measured
gap is 13.75 pixels. Existing terrain edits from 0.5.15/0.5.23 cover both
bottom rows and the independent partner movement row.

Mao's explanation at 81:t_1:64 used a special alphabet squeezed horizontally
to 85%, making it visibly narrower than Ledo's ordinary text. The reviewed
wording fits three normal-font rows at 948, 940 and 912 units, within the
960-unit limit. Remove only this record's condensed profile. Preserve the
keyword link and the uncertainty of the Japanese explanation.

Both reported unlock screens are already covered by 0.5.20: obtaining a
Repair Kit, Propellant Tank and Cartridge unlocks Rescue Unit; attacking
from 12 or more spaces away unlocks Hyperdimensional Target Lock. Those
native report compositions are verified again in the final build.

Episode 11's condition is static text. The 0.5.23 display-key route prevents
the original 128-byte temporary buffer from truncating its English. The
complete condition names Lal'C, Nono, Tycho and Nicola and forbids any NPC
kill. Check its native copy and final lookup without changing the gameplay.

BASE_RULES.md requires agent meaning review. review25_wording examined 47
dialogue source rows and six related mission conditions. It approved the
caption and shortened Mao wording; the mission meaning remains unchanged.
In-game visual confirmation of this exact build remains pending.
