# Public 0.5.18 screenshot fixes prepared for 0.5.24

The user supplied three screens: Clear Report bonuses, the Mech / Weapon
Upgrades list, and the map's deployment preparation menu. These changes
carry all unpublished 0.5.19–0.5.23 fixes. Publication needs explicit consent.

## Clear Report

The PP award is three native 81-byte strings, copied/formatted by the
0x185e08 branch. Use “President skill bonus:”, “Each deployed pilot received”,
and the live amount followed by “PP.” This retains the distributive meaning
without repeating “each”. The existing proportional centering helper
measures the final strings, including the unchanged native number glyphs.

The Z-Chip and funds rows use the original 0x1858a8 composer and 0x15d108
number conversion routine. Bind all six fragment consumers to relocated
English payloads. Use “Bonus received:”, “Z Chips: ” and “Funds: ”; replace
the closing bracket with an empty suffix. Change the two callers' padding
argument from six cells to zero. Award values, calculation, number conversion,
and other composer callers remain intact. Source hashes and individual TOC
loads guard the change. Large signed-positive amounts remain under 81 bytes.

## Upgrade list

Both native list/footer variants use the original Latin fill and outline
masks for “Accuracy”, “Wpn”, “Mech Upgrades”, and “Weapon Lv”. Move the footer
caption eight pixels left and the cyan RANK caption to x=940. Preserve the
numeric amount and bar. Shorten the right header so it ends inside the screen.

## Deployment menu

Use “Select Team”, “Prep Menu”, “Objectives”, “Map Deploy”, and “Quick Save”.
Keep the bullet icons and 48-pixel row pitch. Shorten the status labels to
“SR Pts” and “Teams”, and suppress the redundant suffix after the live team
count. The number widgets stay in their original positions. All measured
labels have at least six pixels before the next field or panel edge.

`BASE_RULES.md` requires agent meaning review. `review24_wording` checked all
five meaning groups; the wording retains per-pilot PP and separate resource
awards. Scripted checks validate source bindings, font masks, row geometry,
command lookups, native number composition, canaries, and final archive/ISO
readback. In-game visual confirmation of this build remains pending.
