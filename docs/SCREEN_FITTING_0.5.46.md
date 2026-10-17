# Herald terminology and screenshot fitting — 0.5.46

This candidate includes all prepared 0.5.45 corrections. The upgrade patch
must use exact public 0.5.44, because 0.5.45 has not been published.
Publication requires explicit consent for this release.

The 御使い glossary token now expands to singular **Herald**, with existing
plural suffixes retained and group references / singular articles reviewed.
The reported declaration is **Heralds!**. Evangelion Angels, Aquarion Shadow
Angels / 天翅, the pilot Angel and Tenshi remain distinct. Historical drafts
and retranslation snapshots are preserved.

The native no-pilot name routines load UTF-8 fallback dashes from 0x8dc7c8
and 0x8dc7e0, while their normal RPW-name draw path uses CP932. The new
fallback allocations preserve seven/eight original dash cells in CP932.
Only their two TOC pointers change; original UTF-8 strings remain untouched.
The actual consumer at 0x5e3a0 confirms CP932 mode. Executed empty and live
name branches check display arguments, mode and the live RPW name pointers.
No save, pilot assignment, portrait or unit-stat data is changed. In-game
confirmation that this resolves the reported stray letters remains pending.

Conversion captions use **Emerg. Deploy Booster**, **Light Config.** and
**Assault Config.** in both executable and SB2T lookup sources. Descriptions
and the full mech name retain their original meaning. At the conservative
31-pixel quad they measure 353.59, 198.59 and 232.50 pixels respectively,
within the 370-pixel list-name allowance.

Fundraising headings use **Funds** and **/ Funds**. Its remaining-pilot
caption uses **Left:** before the existing count. **Ability Active** measures
163.28 pixels at the indicator's 25-pixel quad, within its 224-pixel allowance.
The remaining-pilot caption is the only widget whose position/centering changes.
Other widget geometry, native values, selected colors and font metrics remain.

The complete build plan asserts unchanged font allocation, both font-page
masks, ordinary lettering profile and advances against prepared 0.5.45.
Source and compiled checks cover the full dialogue corpus, actual Library and
linked-keyword archive copies, native keyword converter consumers, selected
UI lookups and the no-pilot branches. ISO and Retro Trans readback evidence
is recorded separately after those steps finish. Runtime visual QA is pending.

The backlog regression now includes `724:t_1:41`: Heralds increases it from
307 to 309 bytes, crossing the former 308-byte capacity. The native expanded
ring preserves it with all other long entries. The historical 0.5.44 Library
capitalization regression loads that build's recorded source commit, so it
continues to isolate capitalization instead of mixing later Herald edits
into the old fixture. No historical game data or snapshots are rewritten.

Final delivery verification passed: 349 regression tests, one optional skip,
21 installed UI lookups, 12 no-pilot/live-name cases, 572 native keyword
consumer cases, 48 carried D-Command origins and three palace-caption origins.
Readback covers 47 changed stage members, 37 changed Library entries, both
actual keyword-popup variants and all 4,803 widget identities/styles.
Both original and public-0.5.44 Retro Trans patches reconstruct the complete
5,289,607,168-byte ISO with SHA-256
`fc812465c5f6974fda191ae702f29bddd384c7dfa0b4e0d1be2c96210df49036`.
Five delivery assets are sealed in the local readiness record. No GitHub
release has been created. Runtime visual confirmation remains pending.
