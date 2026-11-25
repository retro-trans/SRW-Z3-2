# Tengoku-hen Vita port — 0.1.4

**2026-11-25 release status:** the user confirmed that the physical Vita
0.1.4 first-battle correction works and authorized publication for both Vita
and Vita3K. The 0.1.4 Vita3K PKG passed isolated native installation and all
141 file hashes; fresh 0.1.4 emulator gameplay is not claimed. Neither result
establishes a full story playthrough. The release uses the exact sealed game
components from the successful hardware delivery.

The 0.1.3 physical diagnostic identified
`EventCheck_ActionEnd`, stage line 174, doing arithmetic on missing
`LOCAL_FLAG`. The native definition is zero. Version 0.1.4 binds immutable
native constants into 287 stage scripts and the shared battle helper, using
the 6,481 verified original values. The exact missing-global failure is
reproduced and corrected in Lua 5.1, with 4,617 modeled event-check cases
matching the intact original. Why shared initialization differs on that
device is still unconfirmed. The first-battle retest now succeeds on hardware.
The separate 0.1.4 Vita3K package includes the same correction.

The native shared loader copies fixed byte counts for nine Lua files. The
modified common helper keeps its original 9,993-byte extent with 541 trailing
spaces, so cached lengths remain correct without changing EBOOT's data table.
Script strings/comments, original numeric/string types and archive storage
modes are preserved. The unpublished unpadded candidate was rejected and
retained privately for analysis. Hardware delivery uses fourteen game files
plus the original sanitized auth. Error reporting remains active.

The 0.1.2 hardware photo exposed a diagnostic rendering bug: literal ASCII
`1` changes text color in the native converter. Version 0.1.3 escaped that
digit, and the following hardware photo captured the underlying Lua error. See
[installation and diagnostic instructions](VITA_INSTALL.md). The original
port/build evidence below is historical; current test scope is stated above.

The requested targets are physical Vita and Vita3K. This port has its own
0.1.0 version and does not change the PS3 0.5.51/0.5.52 outputs or installation.
Its English source is the sealed PS3 0.5.51 translation, including the requested
glossary spellings. No additional meaning edits are inferred during porting.

## Original source

The user supplied `SRW Z3 Tengoku.pkg` (2,926,199,744 bytes), PCSG00494
version 01.00, SHA-256
`009833f3ecb46da08e50ad9d3cfc9772a2d74499f29960a6645d88235e78e7b0`.
The matching work.bin stays local. Neither license values nor raw console
authentication data may appear in logs, commits or patch packages.

`tools/vita_source.py` performs identity checks, extraction and native PFS
decryption. It verifies all 141 game files and 28 CPK archives. Original inputs
are unchanged. Dependencies are reused read-only from the sibling project's
audited public-tool workset. Details and hashes are in ignored `work/vita/`.
The PFS sources are Vita3K/psvpfsparser; package extraction uses mmozeiko/pkg2zip.
The SELF format reference is pinned locally to SHA-256
`aa70c0dcfc912ead27abb2040cba0d9c2f3b543ecf7c5baa7c56c4459270a7d3`.

## Native port

- Every one of 63,559 parsed source dialogue identities matches PS3; the
  63,553 active translated records transfer into 437 source-bound Lua members.
  Platform-specific Vita commands remain intact. There are also 9,628 quoted
  names and mission strings transferred by source/context identity.
- Five text archives have matching decoded native members and carry the
  sealed English names, Library text and keyword definitions.
- All 368 battle voice blocks match the original PS3 source exactly. The
  native ARM data segment contains one unique complete offset table; that
  table is rewritten for the translated SRVC. Selection/cue data is unchanged.
- Nine guarded Thumb hooks implement exact text lookup, proportional advance,
  callback origins and caption centering. They preserve live LR, including
  the keyword callback's row value. Two relative SCE relocations bind appended
  data. No PS3 instructions or Jigoku executable addresses are transplanted.
- The actual patched instructions pass 44,638 Unicorn execution checks,
  including all 35,095 dictionary entries, 4,480 width slots, embedded-NUL
  operands and independent text/data load shifts. This is not gameplay proof.
- The native ASSF canvas is 1280×720, scaled to the 960×544 framebuffer. The
  caption origin therefore remains logical X=640. Native widget pixel-center
  adjustments are preserved when applying 604 text/layout widget changes,
  four element changes and 14 native string-table changes.
- The P8 font uses 301 originally blank cells. Original pixels and used
  palette entries are preserved. Ordinary English uses a new white alpha ramp
  with at most one alpha level of quantization error, keeping the existing
  shapes/spacing without adding an outline. Separate native-label glyphs keep
  their thinner border.
- GXT artwork is decoded and requantized to native palettes. Changes are
  confined to pixel masks and source-checked animation operands. Stage cards,
  episode headings, map captions, title artwork, battle banners, startup
  notices and credits are included. The startup warning is laid out directly
  within its original Vita frame; whole text areas are repainted to avoid
  leftover Japanese edges after resolution conversion.

## Build and validation

Retro Trans 0.5.20 (local source commit
`c07105f40201274e4f8e3d76120bea1fec4ab04a`) rebuilt the original package through
the 18-component patch ZIP. Vita3K's isolated native installer verified all 141
target files. The local PKG is 2,940,151,216 bytes, SHA-256
`f529bfd591baa80784a0afb70b83c8e7a9950f4faf47eadba5f699ace5a7bc86`.
The patch ZIP is 26,172,180 bytes, SHA-256
`b356f9d13769f2478225925497374da8692feb4d132d50535c9be545bc11c786`.
Both original package and license remained unchanged.

The broad regression run executed 388 tests: 386 passed, one skipped and one
historical PS3 font comparison failed under bundled Pillow 13.0.0. The same
failure reproduces without importing Vita code: 14 alpha pixels in `(` differ
from the frozen fonts. Frozen 0.5.37, 0.5.38 and 0.5.51 fills are identical and
their standalone font files match their sealed archives. That test passes with
the existing pinned Pillow 12.3.0. `tools/vita_regression.py` loads that version
before PIL; all 20 related font/native checks passed with it. `--full` reruns
the entire suite. No historical font or PS3 build was changed to accommodate
a library update.

All tools default to a dry run; review output before adding `--apply`.
Run with the pinned local Python and dependencies described in `tools/vita/`.
The sequence is source intake → ELF baseline → source comparison → stage/font
plans → native UI/art plans → ARM build/execution checks → component build →
Retro Trans patch packaging and isolated PKG integration.

`tools/vita_build.py` verifies every source hash, all member plans and the
matching ARM execution proof. It rebuilds each native CPK and independently
checks replacement contents and every untouched member. Outputs go under
`work/output/vita/builds/0.1.0/`; public-delivery candidates go under
`work/output/vita/releases/0.1.0/`.

`tools/vita_release.py` makes per-file xdelta patches and decodes every one
back to its declared target hash. The Vita3K profile uses Retro Trans's
`retro-trans-vita-pkg-v1` schema. Users supply their original PCSG00494 package
and license locally. The custom rebuilt PKG is a Vita3K target, not a package
to install on physical hardware. No original game files or licenses belong in
the GitHub release assets.

## Physical Vita permissions from work.bin

The user's follow-up requested using the supplied work.bin. The earlier
console-dump requirement was too strict: the original encrypted SELF already
contains the required permissions in its decrypted optional-header table.
`tools/vita_auth.py` uses the original PCSG00494 SELF and matching work.bin to
extract them locally. No separate console dump is needed for this delivery.

The format and copy semantics are verified against
[reF00D's loader implementation](https://github.com/dots-tb/reF00D/blob/f3271bcd010950193cfb6e0331cae89bdb5e96e9/src/ref00d_kprx_auth.c#L383-L410)
and its
[metadata types](https://github.com/dots-tb/reF00D/blob/f3271bcd010950193cfb6e0331cae89bdb5e96e9/src/ref00d_kprx_auth.h).
Optional type 1 supplies 32 capability bytes and type 3 supplies 32 attribute
bytes. Type 2 is a separate seed header and is never exported. Header extents,
sizes, chain flags, uniqueness and signature boundary are checked strictly.
The original SELF's public authority ID supplies the first eight auth bytes.

Only the authority/capability/attribute fields are written to the sanitized
144-byte rePatch auth file; padding and all secret/license regions remain
zero. The result has SHA-256
`a28ed743f23a027ad39bd058848445ffe04c3ef3c3306d9351049b43142af20a`.
As an independent check, extraction from the existing Jigoku source exactly
matches its separately prepared rePatch profile. That comparison is an oracle;
no Jigoku permissions are used to construct the Tengoku output. The Tengoku
executable's original boot-parameter header is also preserved byte for byte.

Run `tools/vita_auth.py`, then `--apply`, followed by
`tools/vita_release.py --auth work/vita/derived_auth/self_auth.bin` and its
`--apply` invocation. This adds a separate `retro-trans-vita-repatch-v1` ZIP
without changing the existing Vita3K package or game components. It omits the
five original modules supplied by the installed game. The profile includes
the sanitized permissions, so end users supply just their original PKG and
matching work.bin to Retro Trans.

`tools/vita_hardware_check.py` exercises that actual PKG/work.bin route, checks
all 13 reconstructed components plus auth, and makes a private copy-ready ZIP.
This route PASSED, including hashes streamed from the copy-ready ZIP. The
Retro Trans hardware patch ZIP is 24,206,554 bytes. Original inputs and user
devices were unchanged. Thirteen focused auth/native tests passed, and the
metadata decoder still reproduces the exact previously verified plain SELF.
No physical console gameplay verification is claimed.

No installation into the user's actual Vita3K setup or physical Vita has been
performed. No GitHub release or draft is authorized. Once validation is complete,
request explicit consent for the concrete release, with the target-specific
limitations stated. Live gameplay and Vita DLC compatibility remain untested;
the supplied package is the base game, not a set of Vita DLC packages.

## Vita 0.1.1: post-movie black screen

The physical-Vita tester reported that the original Japanese game works and
the English overlay stops after the intro. An isolated Vita3K 4377
(`685b80a6`) installation with local firmware reproduced the English 0.1.0
failure. The original Japanese control passed the movie and reached character
setup. Replacing only the executable or restoring the original AID UI archive
did not resolve the translated build's failure.

Vita3K's native thread inspector showed PC `0x81324458`, LR `0x810042ef`,
and the main thread repeatedly sleeping in the game's synchronous file-load
error path. Its request named `app0:/data/anime/effvita.cpk`, with member
`0xe5` (229). This member was originally stored uncompressed; 0.1.0 had
compressed its translated payload. Keeping the same English payload raw let
loading advance to the equivalent failure on member `0xe8` (232). Keeping
both raw passed the full movie, English title/menu and battle demonstrations.
Manual keyboard input opened the title menu. Automated taps were unreliable,
so this does not establish a complete interactive story playthrough.

Decoded-file equality was therefore an insufficient validation criterion.
`tools/vita_storage.py` now selects compression from the native source and
independently rejects any changed compression mode. The 0.1.1 build checks
all 2,573 members in eleven modified CPKs. It restores the two effect assets
and preserves the storage choices of 43 small Library records as well. The
Thumb executable, font glyphs, spacing and dialogue payloads are unchanged;
the title artwork identifies the new version. A regression explicitly shows
that a decoded-payload-correct archive can still fail the native storage check.
The focused CPK/native run completed 30 tests: 29 passed, one optional check
skipped.

The final component build is under `work/output/vita/builds/0.1.1/`.
The exact final installation passed all 141 file hashes, reached the map in
Vita3K and was confirmed working by the user on 2026-11-20. The reconstructed
Vita3K PKG passed native installation verification. The separate original-PKG
and work.bin route reconstructed all 13 physical overlay components and the
sanitized auth file; the copy-ready ZIP's payload hashes were checked too.
Retro Trans patch ZIPs, reconstructed package checks, hardware-overlay checks
and runtime observations are recorded separately in the versioned output and
`work/ui/vita/0.1.1/` review evidence. Physical-console retesting remains
required. No GitHub release or draft is authorized for this version.
