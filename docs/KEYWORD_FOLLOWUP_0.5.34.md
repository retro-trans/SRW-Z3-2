# Keyword follow-up — 2026-10-15

The reported messenger, Avalon and NERV descriptions are already translated
in prepared **0.5.34**. Readback checks both description variants in the native
linked-term table and the separate Library archive. The Avalon text preserves
145,000 hours, approximately 16 years, limited citizenship, the four-week
permit and the three stated freedoms. The messenger text retains the fleet's
courier occupation and backpack gliders; NERV retains the organization,
purpose, headquarters and both commanders.

The complete category passes: 143 keywords, 286 native description pointers,
286 English native payloads and every translated display field in
`MTZKN_KW.CPK`. All 572 native width/draw consumer cases, the substring case
and three ordinary-string fallback cases pass. These checks inspect the
prepared binary rather than only the translation source files. Original
lookup names, series, flags and IDs remain unchanged.

The D-Trader screenshot contains English and repeats the label overlap
addressed in 0.5.30. Actual 0.5.34 archive readback confirms the compact Move,
Range and Terr. captions and separated owned-item suffix, together with the
other related deployment captions. The unknown-item question marks are
intentional locked-item placeholders and remain intact.

No game assets or translations needed changes. Version 0.5.34, its ISO and
both validated Retro Trans patches remain unchanged. This audit records
verification and preserves the four new screenshots. It does not establish
why the supplied captures show Japanese, and in-game confirmation remains
pending. Public delivery still requires explicit consent for 0.5.34 under
AGENTS.md; no release was created or published for this follow-up.

Reproduce with `python -m tools.verify_keyword_followup` (read-only), or add
`--apply` to save evidence and screenshots. Evidence:
`work/ui/keyword_followup_0.5.34.json`.
