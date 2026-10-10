# 0.5.2 — Fresh English dialogue retranslation (RPCS3 playtest)

English patch for **Super Robot Taisen Z3: Tengoku-hen**, Japanese PS3 edition
**BLJS10299**. This is the first release in the SRW-Z3-2 repository.

## Apply

Download the release assets. In [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools),
use **Apply xdelta**, select your matching original Japanese ISO and
`SRW-Z3-2-PS3-English-0.5.2-from-original.xdelta`, and choose a new output ISO. This playtest prerelease is not enrolled in
the public Automatic catalog. Retro Trans 0.5.4 was used for release validation.

Alternatively:

```text
xdelta3 -d -s "original-japanese.iso" "SRW-Z3-2-PS3-English-0.5.2-from-original.xdelta" "Tengoku-hen-English-0.5.2.iso"
```

This patch accepts only the exact original input below. Other versions,
folder dumps, repacked ISOs and Vita packages are not interchangeable. Keep
checksums enabled and preserve your original image.

- Original Japanese ISO: **4,888,199,168 bytes**,
  SHA-256 `803df496be059d43a6045bd06e31a7def0d96f721ef8147e0d6efff81d125b99`.
- Patched 0.5.2 ISO: **5,282,922,496 bytes**,
  SHA-256 `3351402913f80937bcf373acd4bdb26fcf1c04ac0dba03be4cedfffca51aca2b`.

`BUILD-MANIFEST.json` records complete input, output and patch identities.
`SHA256SUMS.txt` verifies downloads; `VALIDATION.json` records the full-image
decode round trip. Only patches and protocol metadata are distributed.

## Included

- Fresh English dialogue: **63,553 records**, including main story, alternate
  routes, endings, ace talks, guidance and previews.
- Five long records use a separate 85% horizontal VWF alphabet. All wording
  and eleven full Sphere names are retained. Font cells, advances and encoded
  text are matched; each rendered speech block fits the three-line budget.
- Existing UI, Spirit, mission-condition, name-table, team-name, artwork and
  encyclopedia translations, plus **48,143 battle-voice strings**.
- Six shared route-choice filenames are merged by ID; the build rejects
  incomplete or duplicate dialogue coverage.

## RPCS3 compatibility and limitations

**RPCS3 only.** This build uses a plain ELF executable; physical PS3 and Vita
support are not claimed. This is a playtest prerelease. Boot, gameplay and
live readability of this exact build remain unverified. Coverage checks do
not prove every screen or wording is final; provisional names and difficult
interpretations remain recorded in the project reports.

Close RPCS3 before updating. Back up your installation and move only the old
`dev_hdd0/game/BLJS10299_DATA` installation-cache folder to a backup outside
`dev_hdd0/game`, allowing the new build to reinstall matching fonts and battle
text. **Preserve savedata and other games.** Fresh-boot the image and load an
in-game save; emulator save states can retain older code/resources.

The paired SRVC and EBOOT pass independent readback. Four voice blocks exceed
the original largest block; runtime block limits and battle-text layout still
need playtesting. Some estimated battle-caption lengths remain flagged.

Build sources: `5e1f5083ce24b714f35a078627a32955bc44d857`. Release tool: Retro Trans **0.5.4**,
commit `8edfb2e1c0d0c74df67107d80803177cc5939079`. All 82 disc files are verified through both filesystem
trees; the stage SDAT passes encrypt/decrypt round trip. Report issues with
the build number and a screenshot.
