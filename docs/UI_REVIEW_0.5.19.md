# Public 0.5.18 screenshot corrections prepared for 0.5.19

Publication requires explicit consent for this release. Local preparation does
not create a GitHub release, including a draft.

| Report | Change | Preserved fields |
|---|---|---|
| Link question | Clears / Chart / Game Clear; shorter suffix and aligned choices Link network data / Link & Start | Separate counts, chart state and clear state |
| Link Bonus PP | Shorter explanatory header, Chart Complete / Replay, compact multiplication suffix | Replay count, multiplier, individual PP and total |
| Japanese protagonist name in defeat condition | Translate default values at the mission substitution table, independently of dialogue getters | Custom names, name order, script lookup keys, saved bytes |
| Library Full Name overlap | Shorten the shared label to Name | Complete official name value |
| SR Point / bonus funds overlap | Separate colored SR Point and black earned text; put Bonus funds to the left of the existing yellow amount | Native amount, colors, font metrics and row pitch |
| World-map domination caption | New Earth Empire Control, bounded to the caption portion of the swizzled atlas | Percentage digits, decimal point, percent sign, bar and animation records |

`tools.review19_layout` produces 34 source-fingerprinted widget edits. The six
Clears/Chart layouts include alternate link states and the later link menu.
Each label keeps the native live-value fields. Reward sentence layers now use
measured left origins; the number is rendered once by its original widget.

The prior 19 exact mission-name matches did not cover the independent runtime
substitution route. Its consumer at 0x15cee8 builds four name key/value pairs
for the text replacement call at 0x15d0c8. Guarded store wrappers translate
default nickname, first name, surname and complete name values. Custom values
pass through. The native name buffers and lookup keys are unchanged. Existing
RPW/Library translations and the three dialogue getters cover the other
identified protagonist display paths; canonical Japanese identifiers remain
available to game logic.

`tools.domination_art` changes member 239, texture 1, rectangle
(0,64,200,32). The caption stays inside the original text region. The next
texture row supplies digit art. All pixels outside the caption rectangle,
including the decimal/percent art and entire digit row, compare identical.
Every effect-script byte and all ten final reveal keyframes remain identical.

One read-only proofreading agent reviewed 12 wording units under BASE_RULES.
It recommended Link & Start and Chart Complete, and confirmed Name is suitable
when the full value remains visible. No additional Japanese prose was exported.

Validation: `tests.test_review19` executes the installed mission store wrappers,
checks custom values and guarded source rejection, measures label clearance,
and compares the untouched HUD digit/animation regions. The full suite ran 254
tests successfully, with two optional skips. `tools.verify_review19` reads the
final archives and executable, repeats the mission store execution checks and
includes all prior cumulative checks against the final ISO manifest.

Final readback passed all 34 captions and 15 mission-name execution cases,
including eight custom/empty values passed unchanged. Evidence and the six
public 0.5.18 report screenshots are saved in
`work/ui/review19_verified_0.5.19.json` and `work/ui/screenshots/`.
The matched ISO is 5,284,429,824 bytes; both directory trees verified all 82
files. SHA-256:
`dde16f0bf9abb363265b765c8dd1a8803809a7cb9272b8b94cf3d51a0a91b65f`.

Live appearance in RPCS3 remains unconfirmed until the user tests the approved
public release. The earlier malformed result team-name report (`1l,`) remains
unresolved; this change does not claim to repair it.
