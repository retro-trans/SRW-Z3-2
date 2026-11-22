# 0.5.53 — original-trophies CFW control

The hardware tester confirms 0.5.52 but reports a persistent 100% trophy
installation screen. This diagnostic restores the complete original disc
trophy package. It tests one candidate difference; it is not a confirmed fix.

Apply the xdelta to the **exact 0.5.52 CFW ISO**, creating a new output image.
It does not apply directly to the Japanese original or 0.5.44. Check both source
and target identities in BUILD-MANIFEST.json.

Only `TROPHY.TRP` changes. The wrapped executable and other 81 game files
remain byte-identical. Trophy text returns to its original language. The title
artwork deliberately still says 0.5.52; identify the control by its **0.5.53
filename/checksum**. No installed trophy progress, saves or firmware are reset.

All 21 focused checks pass, and all 82 disc files verify through both directory
trees. The unchanged program inherits the prior 0.5.52 regression evidence.
Official Retro Trans round-trip results are recorded in
`work/ui/local_release_0.5.53.json` when sealed. Hardware retesting remains
pending. See [the tester instructions](CFW_TROPHY_TEST_0.5.53.md).

Prepared locally; no GitHub release or draft is authorized.
