# Tengoku-hen DLC English 0.5.49

Prepared for public delivery; publication requires the user's consent.

This is a separate DLC patch set for the English PS3 game in RPCS3. It works
with the verified font and text hooks in base-game versions 0.5.44 and 0.5.48.
It does not replace or update the base-game ISO. Gameplay and PS3 hardware
compatibility have not been verified. It does not fix the reported CFW launch
failure; the base English game still uses an RPCS3-oriented executable.

## Coverage

All 32 supplied packages are covered: 24 bonus missions and eight reward packs.
The supplied IDs are DLC2301–DLC2331 and DLC2334. DLC2332 and DLC2333 were not
present in the supplied folder.

- 4,666 dialogue and narration records, including alternate event branches.
- All 32 scenario/package titles, 16 distinct mission-condition strings and
  146 distinct team-name strings.
- English system installation titles through optional PARAM.SFO patches.
- Original runtime placeholders, linked terms, mission logic and asset IDs
  remain intact. Shared game-logo branding and background artwork are retained.

The glossary is expanded before measuring and encoding. Existing canonical
spellings are preserved. Newly proposed names include Ohio-ya, Dawn Gale
Brigade, Primordial Calamity, Crystal Superbeast and Hard Luck Alliance; these
are documented proposals, not claims of official English terminology.

Ordinary dialogue uses the existing font. One unusually long AG speech uses
the already shipped 85% alphabet to retain all six sets of three in the joke.
No font artwork or character allocation changes are required.

## Apply the patches

1. Install your original DLC and its legitimate license in RPCS3. Keep a backup
   of the original installed files and close the emulator before replacing them.
2. Find the installed content folder:
   `dev_hdd0/game/NPJB00692/USRDIR/DLC/`.
   This is separate from the disc game's BLJS10299 folder.
3. In Retro Trans Tools, use **Apply xdelta** with an original `DLC23xx.EDAT`
   and the matching `SRW-Z3-2-DLC23xx-English-0.5.49.xdelta`. After catalog
   publication, **Automatic** can identify each original EDAT by its checksum.
4. Save the result separately, give it its exact original filename
   (`DLC2301.EDAT`, for example), then replace that file in the installed DLC
   folder. Repeat for the DLC you have installed. You do not need all 32.
5. Optional: translate the installed content's system title by patching
   `dev_hdd0/game/NPJB00692/PARAM.SFO`. Use the **System-Title** patch that matches
   its original checksum. Automatic identification will select the matching
   source after publication. All 32 original variants lead to the same English
   title because this installation folder is shared. Restore the exact filename
   `PARAM.SFO` and replace only that file. Reinstalling another original DLC may
   overwrite this optional system title.
6. Start the English base game and check the DLC menu and scenarios. Keep your
   original files so you can restore them when reporting a problem.

Apply EDAT patches to installed EDAT files, not ZIPs, PKGs or the game ISO.
The patch names identify the required DLC; matching checksums are in
BUILD-MANIFEST.json. Do not force a patch onto a mismatched source.

The original content IDs and license type are retained. Your original license
is still required. The patch set contains no RAPs, licenses, complete DLC
files, retail PKGs or game images. Modified EDATs cannot retain Sony's retail
signatures, so this is not a claim of signed retail or console compatibility.

## Validation

The final files were decrypted and every archive member read back. Dialogue,
titles, quoted strings and script bytes outside approved text spans were
checked against the source-bound translation plan. Source ZIP hashes remain
unchanged. All 32 original and translated EDATs pass header, block and metadata
authentication checks with the locally supplied license material.

The official Retro Trans 0.5.4 release SDK built and round-trip verified all
64 routes: 32 EDAT patches and 32 optional system-title patches. Offline catalog
checks confirmed that each original identifies uniquely and selects its correct
one-step route. The full regression suite ran 366 tests: 364 passed and two
optional checks were skipped. Asset hashes and delivery evidence are recorded
in `work/ui/local_dlc_release_0.5.49.json`.

These checks do not substitute for playing the scenarios. Please report the
DLC ID, event or screenshot, English base-game version and emulator version
for any visual or translation issue.

## Rebuild and review

English authoring is in `work/translation/en/dlc/` and `dlc_ui.json`. Glossary
research is in `work/glossary/research/dlc_terms.json`. Original scripts,
licenses and context briefs stay in the ignored `work/tengoku_dlc/` folder.

The source extractor uses the configured local make_npdata tool. The licensed
EDAT codec uses Python's cryptography package and the public format documented
in [RPCS3's EDAT reader](https://github.com/RPCS3/rpcs3/blob/master/rpcs3/Crypto/unedat.cpp).
It retains the original NPD identity and does not convert licenses.

Historical font regression checks require Pillow 12.3.0, pinned in
`tools/requirements-font.txt`. Pillow 13 changes some coverage pixels even
with the identical font file. The DLC build reuses the sealed font bytes;
it never rerasterizes them. Use an isolated dependency folder or environment
for these checks rather than changing the user's installed packages.

Run each command without `--apply` first and inspect its preview:

```text
python -m tools.dlc
python -m tools.dlc_text
python -m tools.dlc_build
python -m tools.dlc_verify
python -m tools.dlc_release config
python -m tools.dlc_release seal
```

Extraction, builds and delivery bundles use new output directories and refuse
to overwrite an existing candidate. A glossary change requires rebuilding and
reading back the affected text before sealing delivery.
