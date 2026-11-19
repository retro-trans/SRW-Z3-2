# Vita 0.1.0 testing

The prepared Vita3K build uses the original Japanese PCSG00494 version 01.00
package. Its title screen displays **v0.1.0**. The patch package is approximately
25 MiB; each user supplies the original game and matching license locally.

1. In Retro Trans 0.5.19 or later, select the local
   `SRW-Z3-Tengoku-v0.1.0-Vita-PKG-patches.zip` delivery.
2. Select your original PCSG00494 PKG and its matching work.bin or RIF. Choose
   a new output name for the English PKG and let verification finish.
3. Back up your Vita3K save. In Vita3K, use **File → Install .pkg** to install
   the English PKG, supplying the same matching license when requested.
4. Check the title-screen version, then test a new game or your backed-up
   Vita save. Report the screen, stage and exact text when something fails.

The maintainer's local package is
`work/output/vita/packages/0.1.0/Tengoku-hen-English-0.1.0-Vita3K.pkg`.
Retro Trans rebuilt it through the same patch ZIP and Vita3K's isolated native
installer checked all 141 game-file hashes. This does not establish gameplay
compatibility. The user's normal emulator installation and saves were not used.

Prioritize opening narration, dialogue and names, objectives, command menus,
unit/pilot stats, battle captions, Library links, and save/load confirmations.
The shared English uses the established glossary and font choices.

This initial candidate ports the in-game text/artwork. Native platform trophy
and OS metadata have not been translated in this candidate. The Vita trophy
source is byte-identical to the PS3 source, but physical-overlay support for
that archive still needs checking. Vita DLC packages were not supplied; this
build does not claim Vita DLC translation or compatibility.

Physical Vita needs a separate rePatch overlay and an original PCSG00494
version 01.00 console self_auth.bin dump. That input is still pending. The
Vita3K PKG is not the physical-Vita delivery. See [the port notes](VITA_PORT.md)
for the upstream dump documentation and authentication handling.

No GitHub release or draft has been created. Public delivery requires the
user's explicit approval for this release; the local ZIP can be validated
before publication through Retro Trans's local-patch route.
