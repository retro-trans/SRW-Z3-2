# Public 0.5.18 report corrections prepared for 0.5.23

The five reports cover the Grade 3/Fox Mask unlock, damaged Episode 3 mission
conditions, Sacks, deployment headings/movement flags, and Giltar.

## Mission conditions

The refresh call at `0x18c2ec` invokes the existing name/counter substitution
helper with a 128-byte inline destination (`li r5,128` at `0x18c2dc`). Its
record stride remains 156 bytes. The other script consumer supplies 302 bytes.
Copying long encoded English through those fields can truncate it or exceed
the inline destination. The complete Episode 3 victory text is 134 encoded
bytes before its terminator. The screenshot's beta is not a gameplay term.

`mission_display.py` gives every static condition a unique ten-byte display
key. The native copier carries that key without exceeding its destination;
the existing exact-match drawer hook returns the complete relocated English.
It does not change numeric prefixes, colors, stage IDs or mission logic.
All 262 static conditions use this route. All 25 live name/counter conditions
retain their existing route, including custom-name handling. English wraps
at 1,120 atlas units (980 pixels at the native 28-pixel quad).

The native substitution copier executes for all 262 keys in bounded tests.
Libc memset, strlen, strncmp and strncat calls are modeled; copier instructions
are real. A canary immediately after the 128-byte destination must survive.
Final verification also executes each drawer lookup and reads back all 110
mission stage members, including unchanged condition IDs and nontext bytes.

Source meaning review: five assigned Episode 3 conditions, nine source rows
examined in member 31. No wording corrections were needed. The full SR
requirement is **Defeat all other enemies before shooting down the Tenth Angel.**
The time limit is relative to EVA Unit-01's arrival.

## Deployment

Source-bound captions: `0x9e4a4`, `0xa2024` become Deploy Teams; `0xa2044`
becomes Left:; `0xa31c4` becomes Sel.; `0xa4be4` becomes MV on both rows.
The short yellow captions use original native Latin masks. The remaining
count has a measured 12-pixel gap; numeric widgets and coordinates stay intact.

Seven repeated movement templates at `0xa3644`, `0xa37e4`, `0xa3c24`,
`0xa44c4`, `0xa4c24`, `0xac804`, `0xac864` now use the existing one-cell
Air/Grd/Wtr/Und glyphs. Four cells, all line breaks, native pitch, flag masks
and comparison columns remain intact. Existing native fullwidth spaces are
not allocated as new glyphs; the keyword converter check enforces this.

## Names and unlock report

The user selected Sacks and Giltar. A dry-run-first script updates active
English fields and glossary bindings, preserving historical exports. The
final audit expands glossary tokens across dialogue, Library, executable
text and battle voices; obsolete spellings must be absent.
The audit examined 116,553 rendered English fields: 63,553 dialogue,
48,143 battle voice, 1,322 Library and 3,535 executable fields. It found
83 Sacks and 518 Giltar occurrences, with zero obsolete spellings.

The Grade 3 unlock and Fox Mask announcement were covered by the unpublished
0.5.20 fix (all 23 conditions and 24 item announcements). The final native
report and exact lookup verification are carried into 0.5.23.

## Delivery status

Prepare Retro Trans patches from original and public 0.5.18 inputs. Each
must reconstruct the complete verified ISO and pass official release-tool
validation. Creating or publishing a GitHub release requires explicit user
consent for 0.5.23. In-game visual confirmation of this build remains pending.

Both patch routes now pass full ISO reconstruction and official Retro Trans
0.5.4 protocol validation. The final image is 5,288,230,912 bytes, SHA-256
`3aa832cfc1aec36e33ebeb97f92f04cd712b38f86bdc3dd5d8683e1c4b0d5554`.
All five release assets pass checksums. The 0.5.18 upgrade patch is
26,752,706 bytes; the original-input patch is 203,901,427 bytes.
Evidence: `work/ui/review23_verified_0.5.23.json` and
`work/ui/local_release_0.5.23.json`. Regression: 267 passed, two optional
tests skipped. No GitHub release has been created for 0.5.23.
