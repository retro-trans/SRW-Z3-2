# Timed narration alignment — 0.5.50

The DLC narration page beginning “Before the overwhelming military might of
the New Earth Empire” uses the base game's timed narration records. Its English
lookup worked, but the native caller retained the Japanese left origin at
x224. Long English lines approached or exceeded the right edge, while short
lines remained anchored far to the left.

Every one of the 197 timed narration rows now uses the existing scene-centering
marker. The installed renderer measures each actual ordinary or condensed
glyph advance and sets its origin to `640 − measured_width / 2`. This applies
to all 189 distinct narration keys, including the DLC scenes. The reported
page's five left positions are 99.375, 100, 125, 245 and 368.125 pixels at the
native 40-pixel glyph quad. Every line is centered at x640, within x60–1220.

The fix removes only decorative leading/trailing spaces from the encoded
caption. The complete wording, punctuation, row boundaries, original font
choice, vertical origins, transitions and timing are preserved. All original
narration members remain byte-identical. No font, renderer instructions,
dialogue or DLC payload changes are required. The only game files changed
from 0.5.48 are the executable's narration dictionary entries and title-version
artwork. All 20,251 unrelated dictionary entries retain their pointers and
English payloads.

Verification executes the installed native origin routine for all 197 rows at
28- and 40-pixel glyph sizes (394 cases), checks every final lookup and guards
all carried assets. Five focused tests cover the reported page, complete
narration inventory, unchanged timing and unrelated lookups. Full regression,
ISO readback and complete-image Retro Trans evidence are recorded in
`work/ui/review50_verified_0.5.50.json` and `work/ui/local_release_0.5.50.json`.

The full regression completed with 367 passes and two optional skips across
369 tests. Both official Retro Trans 0.5.4 routes reproduce the complete
verified image, SHA-256
`7d4cba195a9f628e47e3bb8f7c79127e3c79e09380f4e8951f275a05b58d5120`.
RPCS3 now registers that image; the previous registration is backed up under
`work/output/dlc-install/0.5.49-20261106T091902Z/before/`. No saves or DLC
payloads changed during this installation.

This is a base-game correction, compatible with the already installed DLC
0.5.49. Public delivery supports the original Japanese image and exact public
0.5.44. A local test installation was requested; no GitHub release is authorized.
The Windows capture helper failed to initialize, so native execution and file
readback are distinguished from live visual confirmation, which remains pending.
