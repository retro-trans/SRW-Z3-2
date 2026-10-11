# English title and credits — 0.5.10

The title now reads **3rd Super Robot Wars Z: Heavenly Prison Chapter**.
The English wordmark follows the adjacent SRW Z3 project's metallic lettering
and silver frame. The subtitle uses its two-line hierarchy, with Tengoku's
red outline. Bottom-right credits read `v0.5.10` and
`github.com/retro-trans`, using Z3's Rodin Bold face, 18-pixel size, outlined
white ink and right alignment.

The title work is part of the matched 0.5.10 testing build. In-game confirmation
remains pending user navigation. The native fiery Z, press-any-button prompt,
UV rectangles, animation records and other title textures are preserved.

## Native bindings

`tools/title_screen.py` guards Tengoku EFFPS3 member 229's original SHA-256,
GTF at 0x7c7d0, texture descriptors and sprite-reference counts. It changes
only these pixel rectangles:

| Texture | Native rectangle | Purpose |
| --- | --- | --- |
| 1 | x0 y0, 861×300 | English wordmark; 428 original sprite references |
| 2 | x0 y0, 536×187 | Whole English subtitle; 832 references |
| 12 | x0/216/440 y0, widths 208/216/208, height192 | Three animated subtitle cells; 410 references each |
| 0, 10 | x912 y640, 340×56 | Build and credit on the stationary title backgrounds |
| 6 | x858 y610, 340×56 | Footer inset for the native background's ten-percent zoom |

The original character quads overlap. The three subtitle cells contain
overlapping windows from one continuous English image, at logical x0, x166
and x332. This prevents the gaps in the physical atlas from cutting the
translated subtitle. Its unused eight-pixel atlas gaps remain byte-identical.
The chapter text is placed 32 source pixels down inside its existing sprite,
giving the wordmark's lower frame space. Animation geometry remains intact.

The build version is passed directly from `tools/game_build.py` into the
EFFPS3 renderer and recorded in `build.json`. The final verifier renders the
expected version again and compares the extracted built member byte-for-byte;
a stale version stamp cannot pass. EFFPS3 is rebuilt once with the preceding
location, episode, Berserk and Library changes plus the new title member.
`tools/refresh_title_build.py` can refresh that archive in the current local
candidate after title-art adjustments. Its default is a dry run. It verifies
every existing output hash, builds and verifies a sibling archive, keeps a
rollback copy and updates only the archive hash and title report. The other
eleven matched files are preserved.

## Artwork provenance and packing

Built-in imagegen created two genuinely transparent RGBA sources, using
Z3's saved wordmark and subtitle as references. The local project copies are:

- `work/ui/textures/assets/title/wordmark-generated.png`
- `work/ui/textures/assets/title/subtitle-generated.png`

The originals remain in the generated-image directory. Packing crops the
transparent bounds and fits the artwork into the original sprite rectangles
without altering its aspect ratio. Source PNG hashes are pinned in the tool;
missing or changed assets cause a failure. Preserve these local files when
moving the build workspace; generated game-art derivatives are ignored by Git.

Wordmark prompt:

> Edit target: the supplied SRW Z3 English wordmark asset. Create a cleaned high quality transparent PNG sprite for the English title screen of the next game. Preserve the exact lettering, gold-white-orange metallic gradients, black plaque, angular silver double outline, and slanted mecha game-logo design. Text verbatim: "3rd SUPER ROBOT WARS". 3 and small rd at far left, SUPER ROBOT WARS on TWO tightly stacked lines to the right just as reference. No Z letter, no subtitle, no other text. Adapt its composition to a wide 864 by 304 sprite rectangle (aspect 2.84:1) with safe transparent padding on all four edges. Lettering should stay readable and look like reference. The image consists only of this wordmark with a genuine transparent background.

Subtitle prompt:

> Use the supplied small translated SRW Z3 subtitle as a STYLE REFERENCE. Generate a new clean transparent PNG subtitle sprite for Super Robot Wars Z3 Tengoku-hen. Text verbatim on TWO lines: "HEAVENLY PRISON" on the first line, "CHAPTER" centered beneath it at approximately 60 percent of the first line cap height. Bold slanted sharp angular condensed italic white lettering, thick deep RED outline and a fine luminous red edge, corresponding to the native Tengoku title red subtitle. Match the reference letter style and arrangement. Top line wider than bottom. Wide composition suitable for a 536 by 187 pixel native sprite; safe transparent padding all edges. This sprite contains ONLY these words and outline, absolutely no logo, no stars, no background plate, no extra text. Actual transparent background.

`work/ui/textures/title/title-0.5.10-frame-preview.png` composes a settled
native frame from the packed textures and original quad coordinates. It is
a texture preview, not an emulator screenshot. The other files in that folder
show the six changed textures for inspection.

## Verification

228 tests: 227 passed and one optional check skipped. New checks cover native
Z/animation preservation, rejection of unrelated changes, continuous subtitle
windows, transparent asset bounds, footer version isolation and background
pixel isolation and footer visibility at every native zoom state. Existing
translation, font and executable-layout checks pass.

`tools/verify_title_screen.py` reads back the final title member, confirms the
build-version match and includes the prior startup and battle checks. Evidence
is saved in `work/ui/title_screen_0.5.10.json`; the reported screenshot is
preserved unchanged under `work/ui/screenshots/`.

Testing image: `work/output/iso/0.5.10/Tengoku-hen-English-0.5.10.iso`.
Size: 5,284,102,144 bytes; SHA-256
`c5dac335998eeb328fb5bf122b81af3d269bb187e8337294f6653e23166f9807`.
Its adjacent JSON records the final image hash and all 82 files verified in
both directory trees. Keep the twelve matched replacement files together.
