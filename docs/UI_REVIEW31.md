# Complete SR conditions — 0.5.31

The two screenshots show missing endings and stray glyphs in Episodes 20/21.
Source review confirms that both stored English translations are accurate:

- Episode 20: defeat all enemies within three turns and let no allied
  battleship take any damage during that time.
- Episode 21: one allied pilot shoots down six or more enemies before map
  clear. No same-turn requirement or MAP-weapon exclusion is specified.

Public 0.5.28 stores each condition as a single short display key and replaces
it with multiple English lines only at drawing time. The prepared 0.5.29/30
repair instead stores one key per English line, so the native assembler counts
and positions those lines. Keep that repair for the reported two-row conditions.

## Actual SR panel limits

The complete panel assembler at `0x1aac08–0x1aaf10` clears `0x407` bytes. It
starts victory rows at offset 1, defeat rows at `0x136`, and SR rows at `0x26b`.
Each row owns two state bytes and a 101-byte text field. Three victory rows,
three defeat rows and four SR rows exactly fill that allocation.

The previous tests guarded an allocation sized to the generated line count.
That missed the fixed four-row SR slot: six static conditions expanded to
five or six rows. Executing the full assembler with a canary immediately after
its actual allocation reproduces all six overruns in the 0.5.30 archive.

Source-reviewed compact wording fits those six in four normal-font rows.
Members 375/554 retain the one-attack requirement, allowed attack modes,
Support Attack combinations, Songs, and guarding/evading exclusions. Both
member 590 variants retain all three conditions in the same turn within three
turns, including ELS invalidation. Member 608 retains all deadlines and quotas.
Member 855 retains its bonus and difficulty explanation; the threshold includes
reaching the stated point total, rather than strictly exceeding it.

The original executable assembler, source phase IDs, selection logic, values
and color-state calculation remain intact. Translation and answer copies are
synchronized through source fingerprints and old English hashes.

## Verification and delivery

`mission_panel.py` executes the complete native integer code, modeling only
libc and the optional SR-status getter. All 101 distinct SR conditions produce
210 cases: both color states, plus default/maximum substitutions for the four
live conditions. Check full rows, inactive victory/defeat sections, state bytes
and the fixed-allocation canary before final drawer lookup. The final verifier
also reads compiled SR literals and runs every actual reported mission phase.

Meaning review examined 2 reported conditions / 9 source table rows, then
6 additional conditions / 29 source table rows. No textual ambiguity remains
in those reviews. Native instruction tests and archive/ISO readback do not
claim in-game visual confirmation.

Carry all 0.5.29/30 repairs into 0.5.31. Prepare original-game and exact public
0.5.28 patches through the official Retro Trans 0.5.4 release API. Both require
complete ISO decode round trips. Release notes describe changes since public
0.5.28. Creating or publishing 0.5.31 requires the user's explicit consent.
