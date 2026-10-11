# Tengoku UI comparison with current Jigoku sources

The 0.5.2 build has substantial UI gaps. Its executable text dictionary is
mostly translated, but it does not inventory the other UI text sources or
handle runtime formatting. A complete dialogue translation is not complete
UI coverage.

Evidence: [coverage_2026-10-10.json](../work/ui/coverage_2026-10-10.json).
Reproduce with `python -m tools.ui_coverage` (read-only preview). `--apply`
saves a new report; an existing report is refused. Local game sources and
the 0.5.2 build are required. No translation or game file is modified.

The reference is the current `../SRW Z3` canonical `localization/messages/`
and `localization/locales/en/`, plus its implementation sources. The earlier
imported reference pack alone was insufficient: it has 27 translation files
and was based on older work. This audit consulted **82 current groups / 3,633
reference messages**, including later UI fixes. Each consulted source/locale
file is fingerprinted. Jigoku has unbuilt local changes; these are reference
candidates, not assertions about its published release. Its recorded HEAD is
`f2a95187d92f97c3f03c2c7418dc96a5285980aa`.

## Verified gaps in the released data

| Source / family | Distinct strings without an exact hook key | Evidence |
| --- | ---: | --- |
| AIDDATAPACK member 0: menu/layout strings matched to Jigoku UI sources | **463** | 570 distinct whole NUL-delimited source strings matched; only 107 have hook keys. Built member is byte-identical to Japanese source. |
| AIDDATAPACK member 5: SB2T text table | **97** | All 166 offsets validated against its TDXT pool; 125 distinct Japanese strings, 28 hook keys. Built member is unchanged. |
| AIDDATAPACK member 6: UB2T text table | **479** | All 596 offsets validated; 530 distinct Japanese strings, 51 hook keys after the game's UTF-8 conversion. Built member is unchanged. |
| RPW pilot-skill descriptions, sk-pri columns 4–5 | **151** | 164 nonempty description cells; every description remains byte-identical and none has a hook key. |
| RPW power-part descriptions, boost-p columns 3–8 | **391** | 474 nonempty cells / 392 distinct strings; all unchanged, only one has a hook key. |
| Executable formatted messages / joined fragments | **40** | English exists, but `eboot_text.hook_entries()` explicitly skips them. |
| Executable Sphere explanation | **1** | The encoded English is 4,943 bytes; the exact-hook extent cap is 4,096, so this duplicate display path is refused. |
| System-dialog candidates | **99 distinct / 104 occurrences** | Excluded from the executable dictionary; OS save/install/network paths need a separate implementation. |

These counts belong to separate source inventories. Do not add them as a
unique remaining-screen total: strings and rendering paths can overlap,
and some consumers still need verification. Presence of a hook key is only
static coverage, not proof of runtime visibility or fit. The overall remaining
UI total is **unknown**.

Member 0's 463 is a reference-matched subset, not its complete UI inventory.
The historical count of 48,049 Japanese-looking runs is a heuristic scan and
must not be used as a count of real UI messages.

## What the missing labels cover

Member 0 includes source matches for deployment instructions and confirmation,
intermission menus, pilot training, mech lists, weapon information, naming and
search, D-Trader, combat records, Tag Command rewards, save commands and key help.
Examples of current Jigoku candidate wording are “All units, deploy!”, “Deploy
with these teams?”, “[Pilot List]”, “[Power Parts]”, “SP Cost”, “Uses”, “Buy”,
“Sell”, and “Right Stick”. Match target context before adopting wording.

Useful member-0 subsets below overlap with each other and with the general
dictionary; each is a count of distinct matched target strings missing keys:

| Current Jigoku reference group | Missing |
| --- | ---: |
| ui_hook: broad UI labels | 223 |
| ui_aiddata: direct UI labels | 83 |
| ui.intermission_layout | 22 |
| ui.naming_search_layout | 19 |
| ui.trader_ui | 16 |
| ui.command_layout | 12 |
| ui.deployment_layout | 9 |
| ui.deployment_menu_text | 8 |
| ui.tag_reward_layout | 8 |
| ui.search_list_headers | 4 |

The additional tables contain further weapon/ability/menu labels and settings,
tutorial and help text, including Tengoku-only content. All nine LUACPK members
were lexed: 15 Japanese literals remain as source-discovery candidates, four
with exact current reference matches. Their roles and generated values are
unverified; this is not a count of 15 visible untranslated labels. AIDDATAPACK
member 4 remains an unresolved binary layout/text source.

## Implementation order

1. **Expand the hook's inputs beyond EBOOT.** Give AIDDATAPACK and RPW
   occurrences stable target identities, fingerprints, encoding and context.
   Build the same matched VWF dictionary from those inputs. Jigoku explicitly
   supplies keys that are absent from its executable; Tengoku currently does
   not. Keep source strings used as internal keys intact.
2. **Translate the menus used most often.** Start with intermission, pilot
   training, status/weapon screens, parts, deployment, search and D-Trader.
   Cover the duplicate SB2T/UB2T paths. Port alignment and compact labels using
   Tengoku's actual widget records, not Jigoku offsets. Check selected,
   disabled, empty and longest-value states.
3. **Translate skill and part descriptions through display substitution.**
   Current Jigoku provides exact-source English candidates for 118 of 151
   skill strings and 203 of 392 part strings. The rest require target-specific
   review. Preserve full effects, thresholds, ranges, main/sub-unit rules and
   consumable/DLC variants. Use Tengoku's Spirit terminology. Some Jigoku prose
   deliberately follows wiki corrections rather than its original game text;
   do not import those numeric/mechanical claims without checking Tengoku.
   Do not repoint these RPW description columns: the Jigoku investigation
   found boot corruption, and its later implementation uses draw-time hooks.
4. **Handle generated text explicitly.** Preserve printf argument order and
   implement complete joined/count variants for purchase/sale prompts, rewards,
   scenario requirements, reports, terrain/movement fields and weapon
   requirements. An exact Japanese format string is not the final drawn text.
5. **Review tutorials and settings in UB2T**, then resolve the long Sphere
   duplicate and OS dialogs. Use full wording with measured wrapping rather
   than omitting effects or blindly applying old limits.
6. **Audit remaining native sprites and geometry.** The 65-cell Tengoku atlas
   catalogue uses 26 reused, 35 newly rendered and four intentionally kept
   cells. Older artwork previews show substantial translated art already;
   Japanese glyphs or unused atlas content alone do not prove a missing label.
   Compare later Jigoku repairs for training, Team/Sub Order, DEF/search tabs,
   equipped-parts help and deployment status against actual target consumers.

Relevant Jigoku implementations include `tools/eboot.py` (keys from multiple
sources, prefixes, joined strings and count ranges), `aiddata.py`,
`build_skill_descriptions.py`, `build_parts_descriptions.py`, `trader_ui.py`,
`training_help_layout.py`, `search_list_headers.py`, `team_order_labels.py`,
`upgrade_list_labels.py`, `weapon_requirements.py`, and
`weapon_requirement_runtime.py`. Read them as patterns; their addresses,
font slots, rectangles and gameplay assumptions are not portable bindings.

## Existing coverage and validation boundary

0.5.2 already contains 3,494 executable hook keys, 129 Spirit occurrences,
11,472 RPW name cells, 287 mission-condition strings, 296 team-name strings,
128 episode title cards and the existing battle/title/library artwork. Those
counts describe implemented source coverage, not closed UI families.

The audit verified the hashes of the selected EBOOT, RPW and AIDDATAPACK
outputs, independently read the actual built hook slot array, compared every
audited RPW description cell with pristine data, compared UI members with their
originals, and validated both UI string-table pointer arrays. Runtime fit and
visibility remain unverified. Some older docs describe earlier pending art
which the build now includes; the build evidence takes precedence.

157 current reference messages lack extracted Japanese sources and therefore
cannot be matched automatically. Generated variants, member-4 structures,
Tengoku-only messages and every screen/state still need their own inventories.
This audit changes tooling and documentation only; it does not rebuild,
deploy, navigate the emulator or alter the published 0.5.2 patch.
