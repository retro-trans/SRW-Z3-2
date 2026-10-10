# 0.5.2 release verification

Build source commit: `5e1f5083ce24b714f35a078627a32955bc44d857`.
Release package built with Retro Trans 0.5.4, commit
`8edfb2e1c0d0c74df67107d80803177cc5939079`.

- All 63,553 active dialogue records exactly match the fresh translation rows;
  no missing, duplicate, stale or changed rows.
- 26 focused local tests passed for dialogue rebuilding, VWF, preserved source
  glyphs and texture handling. GitHub source checks passed for the build commit.
- All 82 ISO files verified through both filesystem trees. Stage SDAT
  encryption/decryption round trip and archive/text readbacks passed.
- The official release builder encoded the original-to-0.5.2 patch, decoded
  it to a complete ISO, verified output size and SHA-256, and rechecked both
  original and target input hashes. The official release validator passed.
- Exactly four assets: one xdelta patch, BUILD-MANIFEST.json, VALIDATION.json
  and SHA256SUMS.txt. Only protocol metadata is mirrored in this directory.

Runtime boot, gameplay, condensed-glyph readability and enlarged battle-voice
block limits remain unverified. This is a private RPCS3 playtest prerelease.
Use Retro Trans's manual **Apply xdelta** mode after an authorized GitHub
download. This release is outside the public Automatic catalog.
