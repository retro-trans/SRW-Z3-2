# Startup warning and copyright pages — 0.5.34

The three reported screens are baked images in TPACKPS3.CPK member 0.
Its five chained 1280 × 720 linear ARGB textures contain the warning, Bandai
Namco logo, CRIWARE logo and two copyright pages. There is no text drawer
string to translate for these images.

Translate the complete warning and the 20 Japanese credit rows; retain the
three original English rows byte for byte. Preserve all 23 credit entries,
their copyright symbols, owners, years, ordering and production relationships.
Keep historical names such as SUNRISE; do not substitute current owners or
add new legal claims. The notice translates the original game's text.

The source-bound catalog records English text and creator-name references in
`work/translation/en/ui/review34_startup.json`. The known source member hash is
`0dc4dcd0d0ecb34d7ea48f09cd84963c571df8a42452c83ffcc50a0401fa5a62`.
Rendering uses the existing PS3 Latin serif and bold fonts. Fit full text by
measured pixel bounds; retain every word. The longest credit uses 26-pixel
type and modest horizontal condensation. Other translated credits use 30 pixels.

Preserve all GTF descriptors and byte spans outside the three translated
textures, all pixels outside their text rectangles, every alpha value, the
warning border and both logo screens. The title footer identifies 0.5.34.
Native-size decoded previews have been visually inspected; they are stored
under `work/ui/startup_notices` and are not in-game screenshots.

The final verifier checks startup pixels from the built archive against the
reviewed render and every unchanged game file and archive member against
0.5.33. It binds those identical bytes to the saved, checksum-verified native
execution evidence for 0.5.33, covering all earlier fixes. Both public-delivery
patches must reproduce the final verified ISO through complete Retro Trans
decode round trips before publication. Public 0.5.28 remains the upgrade base.
Creating or publishing 0.5.34 requires explicit consent; runtime confirmation
is pending.
