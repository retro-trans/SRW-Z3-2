# Large Funds values and Central Asia headline — 0.5.36

All three intermission footer variants share the translated `Funds.` label
beside the native right-aligned amount. The old x coordinate, 391.5, leaves
too little room once the amount reaches eight digits. The game caps current
Funds at 99,999,999 in the native getter at 0x37540.

`review36_funds` moves only the x coordinates of widgets 0x9af44, 0x9b124 and
0x9b304 to 346.5. The existing translated wording, 28-pixel font, colors,
numeric endpoint, number style, values and other footer fields stay intact.
The conservative budget includes eight 17-pixel advances, a complete
32-pixel digit quad and two extra outline pixels. Its left boundary is 450;
the label ends at 441, leaving nine pixels. The preceding SR counter's
endpoint is 334, leaving another 12.5 pixels before the label.

Twelve cases execute the unchanged cap getter, native decimal digit counter
and right-alignment arithmetic. They include zero, each digit boundary,
13,028,032, the maximum, 100,000,000 and the largest signed 32-bit input.
The oversized inputs clamp to 99,999,999; no numeric formatting or gameplay
logic is patched.

The reported Central Asia headline already has a two-line profile in the
prepared 0.5.35 executable:

    Central Asia Front:
    Resistance Groups Launch Coordinated Disruption Ops

0.5.36 retains that exact executable. Final verification resolves the actual
headline lookup and executes its centering at both tested font sizes. The
complete second line fits within the reviewed screen width.

The incremental builder requires the canonical complete UI planner to differ
from verified 0.5.35 at exactly three x coordinates. It preserves the entire
string pool, all other widget fields and the archive's other stored members.
Only the version's title stamp is rebuilt elsewhere. All other game files,
including the executable, font archive and encrypted stage wrapper, retain
the certified parent hashes. This carries the full prior native and
regression evidence without claiming those checks were rerun.

Dry run: `python -m tools.review36_funds` and `python -m tools.review36_build`.
Apply only after inspecting the plans. Final evidence uses
`python -m tools.verify_review36 --apply`. In-game visual confirmation remains
pending; public delivery requires validated Retro Trans patches and explicit
consent before creating or publishing a GitHub release for 0.5.36.
