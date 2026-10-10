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
- Published at 2026-10-10 01:08:35 UTC:
  https://github.com/retro-trans/SRW-Z3-2/releases/tag/v0.5.2
  The repository remains private and the release remains a prerelease.
- All four actual GitHub assets were downloaded using the authorized account;
  their sizes, GitHub SHA-256 digests and local hashes match the package. The
  official release validator and release-record reader passed unchanged.
  Only private download transport was supplied by the authenticated download.
- Release tag commit: `458fd31ee0fe9e3d2bca732e6ba54a3698ffd560`. This adds
  release notes and protocol metadata to the recorded game build source commit.
  GitHub source checks passed for both commits.

Runtime boot, gameplay, condensed-glyph readability and enlarged battle-voice
block limits remain unverified. This is an RPCS3 playtest release.

On 2026-10-10 the user requested public repository visibility and then regular
release publication. The prerelease flag is now disabled. The scoped catalog
refresh passed in run 38052611269, committing the unchanged manifest and patch
identities in `f7a396b19ea728374543623edb0ae6cd9389b99e`. Retro Trans's standard
latest-release reader accepts v0.5.2. Use **Refresh catalog** in Automatic mode;
manual **Apply xdelta** remains available. Earlier private/prerelease statements
above record the initial publication state.

The live catalog URL used by Refresh catalog contains v0.5.2. Retro Trans
0.5.4's unchanged recognition function identified the actual original ISO by
size and full hash; its Automatic Latest planner selected 0.5.2 in one patch,
with the published patch SHA-256 matching the verified release manifest.
