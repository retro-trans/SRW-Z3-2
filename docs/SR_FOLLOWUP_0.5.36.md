# Episode 41 SR overflow follow-up

The reported public-build text exceeds the four-row SR panel. The prepared
0.5.36 candidate already carries the shorter source-reviewed wording from
review 31:

    Shoot down either Angel in one attack (Attack/Maximum
    Break/Counter).
    Support Attacks may join it. Songs count as attacks.
    Guarding or evading an Angel's attack does not count as an attack.

This preserves either Angel, one attack, the three attack modes, permission
for Support Attacks, songs counting as attacks, and the guarding/evading
exception. The longest line measures 1,054 font units against the existing
1,056-unit budget; all four rows fit.

`tools.verify_sr_followup` reads the final executable and compiled stage member
554, verifies their build hashes together with the shipped encrypted stage
wrapper, and checks unchanged condition IDs. It runs the original panel
assembler for the applicable phase in both color states, with its existing
output canary, then resolves each complete row through the final drawer.
Both cases pass. Victory/defeat behavior and live-name substitution are
outside this focused check; their prior certification is unchanged.

Evidence: `work/ui/sr_followup_0.5.36.json`. Reported image:
`work/ui/screenshots/reported-sr-followup-episode41.png`.

No game assets or delivery patches were changed; no new version is needed.
0.5.36 remains prepared with both validated Retro Trans routes. Publication
awaits explicit consent. In-game visual confirmation remains pending.
