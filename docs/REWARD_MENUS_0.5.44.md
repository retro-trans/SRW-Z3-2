# Reward and deployment menus — 0.5.44

The three user screenshots are retained as `reported-review44-*.png` under
`work/ui/screenshots/`. They show the reported behavior; corrected-build visual
confirmation remains pending.

The room heading uses the shared Colony Laser glossary entry. It previously
expanded to lowercase `colony laser`. The corrected entry uses **Colony Laser**
throughout active text, including all thirteen dialogue references and ten
affected Library records. The three changed stage members are 598, 604 and 605.
Their previous rendered versions must match the certified parent exactly
before replacements are accepted. Library checks allow only capitalization
and the resulting line wrapping; meaning, record IDs and other fields remain.

The Sub Order result sentence and reward are separate FSSA elements. The
translated sentence was centered across the fixed numeric field. The three
reward modes now use `EXP each:`, `PP each:` or `Kills each:` at x476.5, with
the native right-aligned number endpoint at x780. Their original values,
styles, color state and animations stay intact. Thirty-three executions of
the installed digit-count/alignment code cover eleven values per mode,
including the reported 750 EXP and every digit boundary through eight digits.
The smallest conservative gap is 9.25 pixels.

The deployment command prefixes are retained `・` characters. Replace those
prefixes with 32 units of invisible padding: three ordinary spaces plus the
existing four- and one-unit blank glyphs. Both font pages have zero fill and
border planes in those cells. Their combined advance matches the old prefix.
The two Select Team states and the multi-row command list retain indentation.
The global font is unchanged.

A native fullwidth blank initially looked suitable, but the caption helper
rejects native 32-unit cells and falls back to character counting. Execution
reproduced different origins for the native key and preloaded English. The
measurable padding avoids that fallback. Twenty native renderer cases cover
all five labels, both input paths and both font states; their origins agree.
The first local candidate is retained under scratch as diagnostic evidence.

`Mech/Wpn Upg` replaces the overlong upgrade caption in both the canonical
lookup and the preloaded submenu block. At its existing 28-pixel size it
ends at x508.63, before the button edge x518. All six submenu rows preserve
their original pitch and style. Fourteen installed lookup cases cover nine
updated outputs, including the selected/dynamic forms.

The parent is certified prepared 0.5.43. The public patch route remains from
0.5.40 and includes the accumulated 0.5.41–0.5.43 corrections. Both Retro Trans
routes must reconstruct the same verified complete image before publication.
No GitHub release or draft is created without consent for this version.

All four focused checks pass, including the twenty caption-origin cases.
The final full regression run passes 346 tests with two optional skips.
Compiled readback verifies all thirteen dialogue references, ten Library
records, fourteen lookups, thirty-three reward cases and the earlier phase/
Trans-Am checks. Both ISO filesystem trees verify all 82 files. Image SHA-256:
`80d6b7f92ae584ecd78994bc1ab7c83abef0d3a302ee826d2b770cd61101c9dd`.

Both official Retro Trans 0.5.4 complete-image round trips passed and all
five assets are validated. The original-image patch is 204,181,888 bytes;
the public 0.5.40 upgrade is 21,351,721 bytes. Readiness is recorded in
`work/ui/local_release_0.5.44.json`. The user explicitly authorized publication
on 2026-10-16. [v0.5.44](https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.44)
is published as latest stable. The scoped Retro Trans catalog refresh succeeded;
both Automatic Latest patch routes are verified. Public delivery evidence is
recorded in `work/ui/public_release_0.5.44.json`. In-game visual testing remains
pending.
