# 0.5.21 — names, training and Z Crystal columns

The public 0.5.18 screenshots report Heero Yui / Crowe Bluste, fragmented
training tab headings, PP-caption overlaps, undersized training stat badges,
and crystal effects colliding with upgrade costs. This build includes all
unpublished 0.5.19 and 0.5.20 fixes and addresses these four additional reports.
Publication requires explicit consent for 0.5.21.

## Canonical names

The user's spelling overrides the older glossary's wiki-precedence choice.
`review21_names` previews the complete active English JSON inventory before
changing player-facing fields. It corrects two Heero glossary entries, Crowe's
entry, the settled glossary, the executable name, Crowe's proposed Library
name, and three source-bound pilot surname slots. Token-backed dialogue,
Library and battle voice expand from the corrected glossary at build time.
Historical source quotations and prior exports remain evidence of older work.
The unrelated Evangelion character Yui remains unchanged.
All three full-name entries are user-confirmed. The settled choices explicitly
authorize these corrections, so a future glossary seed preserves them rather
than restoring older reference spellings.

`coverage()` checks rendered active dialogue, battle voice, Library prose and
executable text for both old full-name spellings. The complete stage and Library
readback checks verify the rewritten output; the final verifier separately
reads the three relocated pilot surname pieces.

## Training

All four native selection states display single measured captions:
**Raise Stats** and **Learn Skills**. Their centers are 726 and 1007 native
pixels. The trailing Japanese word widgets become empty instead of producing
an English word at a distant fixed coordinate.

**Owned / Cost / Left** retain the source origin and three-row pitch. Their
separate **PP** labels move to x=176; values retain their original positions.
CQB, RNG, SKL, DEF, EVD and HIT use normal 28px glyph quads in both dynamic
CQB/RNG variants and four fixed rows. Air / Grd / Wtr / Spc fit before the
unchanged terrain grades. Font height and raster inset change only where
specified; state flags, colors and row pitch remain native.

## Z Crystal

Both heading variants display **Effect / Cost**. All nine effects, including
the hidden Grade 5 names, use 24px normal glyph quads starting at x=925. The
four-digit cost column is unchanged. Measured clearance is at least 13.75px.
The grouped layout and the all-grades layout receive the same compact names:

| Full name | Compact column label |
| --- | --- |
| Demon Eye of Omniscience | Demon Eye of Lore |
| Undying Iron Chains | Undying Iron Chain |
| Dragon Lying in Wait | Dormant Dragon |
| Gathering Spirit Quanta | Gathering Spirit Q. |
| Greedy Golden Arm | Greedy Gold Arm |
| Road to Peerlessness | Peerlessness Path |
| War God's Inspiration | War God's Rally |
| Divine Wind's Blessing | Divine Wind's Ward |
| Battle God's Hope | Battle God's Hope |

The meaning reviewer examined 9/9 names. “Dormant” retains lying low and
unrealized potential; Q. abbreviates Quanta; Ward retains protective blessing.
Full labels outside the cost column remain available in explanatory text.
No costs, effect logic, grades, unlock conditions or selection state change.

## Verification limits

The layout patch verifies source fingerprints, relocated English readback,
and every unrelated byte. Tests measure clearances with the actual font
advances and reject altered source widgets. Final verification reads the built
FSSA and RPW, executes earlier native UI checks, and verifies both ISO trees.
Release patches must pass complete ISO round trips from original and public
0.5.18 through Retro Trans Tools 0.5.4 before publication.

In-game visual confirmation of this exact build is pending. The malformed
result-screen team label previously reported as “1l,” remains unresolved.
