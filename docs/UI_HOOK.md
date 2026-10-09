# Draw-time UI hook (phase 1)

`tools/ui_hook.py` lets the executable draw English for any string that
reaches the game's string drawer, without changing a byte of the game's own
strings. Phase 1 is exact, whole-string matching only. Centring and measure
fixes (phase 2) and templates for dynamic text (phase 3) are not built. The
design and the evidence behind every address are in
`work/tengoku/research/eboot_hook.md`. Nothing here has been booted yet.

## What it patches

| What | Where | Change |
|---|---|---|
| Join point of the drawer `0x14158` | VA `0x141a0` | `lfs f0,-0x7f1c(r2)` (`c00280e4`) becomes `b 0x93eba0` |
| Lookup stub | VA `0x93eba0..0x93ed14` (file `0x92eba0`) | 93 instructions, 372 bytes, in the zero gap after the VWF stub |
| PH0 `filesz`/`memsz` | program header 0 | `0x92eb94` (after VWF) to `0x92ed14`; 4,844 gap bytes left |
| Table ("EXT") | VA `0xF00000`, file `0xEF0000` | appended to the RW data LOAD (PH1) |

At `0x141a0`, r31 is the cp932 string for both kinds of caller:

- r7 = 1: the caller passed cp932, and `0x14198` copied it to r31.
- r7 = 0: the caller passed UTF-8; `0x14994` converted it with `0x13b38`
  into the text state buffer (`0xa31378 + 0xb8`), set r31 to it and
  branched back to `0x141a0`. That branch at `0x149a4` is the only branch
  into `0x141a0` in all of `.text`.

The glyph loop only reads r31 through `clrldi`/`lbz` and advances it, and the
epilogue restores it from the stack. So replacing r31 changes what is drawn
and nothing else. The game's own strings, which some code also uses as
lookup keys, never change.

## The stub

```
stdu r1,-0x70(r1); save r0, r3..r12, CR
r3 = clrldi(r31); r12 = 0xF00000; miss unless the table magic is 'UIH1'
walk the string as the drawer reads it, FNV-1a over every byte read,
    give up (miss) after 4,096 bytes
empty string -> miss
i = hash & mask; probe slots linearly:
    key_va == 0          -> miss
    hash, length, bytes all equal -> r31 = en_va (hit)
restore r0, r3..r12, CR; pop the frame
lfs f0,-0x7f1c(r2)        (the displaced instruction)
b 0x141a4
```

The stub changes only r31 (and only on a hit) and its own 0x70-byte frame
below the drawer's stack pointer, as the VWF stub does. It uses no CTR, LR,
XER or FPR, so it needs no liveness assumption. The re-check of the report's
liveness claims with Capstone (`python -m tools.ui_hook liveness`) found:

- 494 drawer instructions are reachable from `0x141a0`, with both switch
  tables resolved (escape codes `0x14290`, low-byte classes `0x14610`).
- Every read of r31 after the site is `clrldi`/`addi` in the glyph loop and
  its escape handlers. The only writes are `lwz r31,0xb8(r1)`, on a path
  whose flag is cleared at entry and never set, and the epilogue's `ld`.
- After the site the drawer never stores r31 and never reads the original
  string pointer (r3/r9) again. There is one drawing pass.
- Callees summarised by the argument registers they can read leave only
  r8 and cr2-cr4 live at the site. cr2-cr4 are non-volatile and belong to
  the caller. The r8 result comes from conservative callee summaries:
  unresolved import stubs count as reading every argument. The drawer's
  own code never reads r4-r8. Both are moot, because the stub preserves
  every GPR and the whole CR.

### Drawer string grammar

What the stub hashes and compares is exactly what the glyph loop
(`0x14248`) consumes, so a key always means "this drawn text":

| Byte | Drawer (`0x14248`..) | Stub/`extent()` |
|---|---|---|
| `00` | end | end (not hashed) |
| `0a`, `2e` | line break (jump table `0x14294`) | one byte |
| `2f` | ends drawing (flag at `0xb4(r1)` is always 0) | hashed, then end |
| `30`..`39` | escape + one operand byte (colour, sizes, ...) | two bytes, the operand may be `00` |
| anything else | lead of a two-byte cell | two bytes |

Consequences:

- A colour-closing `1`+`00` inside a string does not end it. UTF-8 sources
  produce exactly this, because the converter stores the operand minus one.
- English must contain only two-byte cells (lead `>= 0x81`), `0a`, and
  escapes that also occur in the key. `check_english` refuses anything else,
  including plain ASCII, a lone trailing byte or an early `2f`. Set
  `'allow_escapes': True` on an entry to add escapes on purpose.

## Table format (EXT at VA 0xF00000)

```
+0x00 header (32 B): 'UIH1', version 1, slot_mask, slots_va,
                     tmpl_count 0, tmpl_va 0, scratch_va 0, scratch_size 0
+0x20 slots[2^k] x 16 B: hash32, key_va, en_va, key_len u16, flags u16 (0)
      keys (each + NUL), then English deduplicated by bytes (each + NUL)
      zero padding to the next 64 KiB step
```

- There are at least 16 slots, a power of two, so the load factor is at
  most 0.5 and every probe sequence reaches an empty slot.
- Linear probing. A hit requires the hash, the length and every byte to be
  equal.
- Identical key and English pairs are merged. The same key with different
  English is refused.

Stress test: all 3,637 distinct display strings of the inventory as keys,
with dummy English. The result:

- 8,192 slots, load 0.444, longest probe 10, no 32-bit hash collisions
- 532,079 bytes used, so EXT is 576 KiB
- output file 16,268,336 bytes
- build and verification took about 2.5 s

## Layout B: the fold into PH1

Every number below is re-derived from the input. `measure()` refuses an input
whose layout differs in any way from the measured one (file size, all 8
program headers apart from PH0's grown size, `e_shoff`, 32 sections, the
non-loaded tail starting exactly at the end of PH1's file data).

| Item | Input (VWF build) | Output |
|---|---|---|
| PH1 `filesz` / `memsz` | `0xf12f4` / `0x5b9b18` (`.bss` ends at VA `0xef9b18`) | both `0x5c0000 + N` |
| EXT | none | file `0xEF0000` = VA `0xF00000`, N bytes (64 KiB steps) |
| File between `0xa212f4` and `0xEF0000` | (tail) | zero (`.bss`, then a gap) |
| Non-loaded tail (sections 29, 30, 31) and section table | `0xa212f4`, `e_shoff 0xa24720` | moved by `delta = 0xEF0000 + N + 4 - 0xa212f4`, so `offset % 16` is kept |
| Section headers | | only the offsets of non-ALLOC sections change |
| PH2-4 (empty placeholders), PH5 TLS, PH6/7 | | untouched |
| File size | 10,637,088 | 15,744,048 with the 2 canaries (N = 64 KiB) |

Notes:

- PH1's offset and VA do not move, so every `.data` file offset is
  unchanged, including the SRVC block table at file `0x9db0a0`.
- The table is RW but not executable. Code stays in PH0.
- Jigoku's proven fold also re-pointed the empty placeholders' offsets to its
  new tail. Here they are left at `0xa212f4`, as instructed. A zero-size LOAD
  is ignored by RPCS3. If a hardware SELF wrapper ever objects, that is the
  one-line difference to try.

## Keys for UTF-8 sources: `utf8_key`

`utf8_key(utf8_bytes)` returns the bytes that `0x13b38` writes into the text
state buffer. It uses the ELF's own table at `0x82db00` (128 ASCII entries,
then 65,536 entries indexed by UTF-16 code). The function's code bytes are
pinned by SHA-256 and the table's TOC slot is checked.

| UTF-16 unit | Output |
|---|---|
| `000a` | `0a` |
| `0031` (`1`) | `31`, then (low byte of the next unit) - 1; both units are consumed |
| high byte `0d` | nothing; this unit and the next are skipped |
| below `0080` | 2 bytes from the ASCII sub-table (fullwidth: `A` gives `8260`) |
| anything else | 2 bytes from the big table (unmapped gives `81a1`, the black square) |

Refused because the result depends on memory past the input: strings
containing NUL, non-BMP characters (the game's character count and the
UTF-16 length disagree), and a `1` as the last character.

The converter calls two functions that are modelled in Python:

- `UTF8stoUTF16s`, cellL10n import NID `0xf7681b9a`, stub `0x77ad40`.
- `mbstowcs(NULL, s, 0x800)` at `0x687034`. This is libc code that reads
  TLS locale state. The centring wrapper at `0x149bc` uses the same call to
  count UTF-8 characters.

Everything else, including the libc `strlen` at `0x68a2ac`, runs as real
machine code in `tools/ppc_exec.py`, a small pure-Python PPC64 interpreter.
It refuses any instruction it does not implement.

The oracle runs every string twice:

- **Model A:** characters are counted as code points, no terminator is
  written, and the stack and output are pre-filled with junk.
- **Model B:** characters are counted as bytes, a terminator is written, and
  memory is zeroed.

A string passes only if both runs produce byte-identical output that equals
the emulation, with nothing written past it.

**Result** (`python -m tools.ui_hook validate-converter`):

- All **4,467** UTF-8 records in `eboot_strings.json` were checked.
- **4,466** were identical under both models. There were 0 mismatches and
  8,806,670 instructions were executed.
- 1 was skipped: a debug string ending in `1`.
- Paths covered:
  - 57 strings with `1` escapes
  - 765 with line breaks
  - 330 with other ASCII
  - 9 with Latin-1
  - 17 containing unmapped characters
- The high-byte-`0d` path does not occur in the inventory. The tests cover it
  with synthetic strings.

## Verification inside `hook()`

All gates raise on failure:

1. **Byte isolation.** Restore the branch word, the stub range, the PH0 and
   PH1 size fields and `e_shoff`, and the input must be reproduced exactly
   up to the end of PH1's data. Also:
   - the fill is all zero
   - the EXT bytes are the table
   - the moved tail, with its section table restored, equals the original tail
   - every section header equals the original apart from the expected offset
     change, and alignment is kept
   - every section payload is unchanged apart from the branch word
   - PH0, PH2-7 and PH1 hold exactly the expected values
   - there is no W+X LOAD and no overlap.
2. **Table readback.** An independent Python lookup over the produced file
   finds every key's English. A plain scan of the slot array gives the same
   English address. Prefixes, extensions and other non-keys do not resolve.
3. **Stub.** Every word is decoded by `ppc_exec`. There are no calls, no
   SPR writes, no stores except through r1, and all branches stay in the stub
   except the final `b 0x141a4`, which follows the replayed `lfs`. When
   Capstone is installed it must decode all 93 words and agree on the last
   two. It is optional; Python 3.12 builds run without it.

   The real stub then runs in `ppc_exec` against the produced image:
   - up to 512 keys (all keys if fewer; tests run all), with r31 carrying
     junk in its high 32 bits
   - the misses: empty, over 4,096 bytes, prefixes, extensions

   Every run must:
   - return to `0x141a4` with r31 set to the slot's English, or unchanged
     on a miss
   - leave all other GPRs, CR, LR, CTR and XER(CA) unchanged
   - set f0 to the TOC constant (-1.0) and leave the other FPRs unchanged
   - write no memory outside its frame.
4. **SRVC table.** `srvc.read_table` on the output, with the SRVC size the
   input's table ends at, must return the same table at the same file
   offset. `apply()` requires this gate. Tests on a synthetic ELF skip it
   explicitly.

## Integration with `game_build` (not yet wired)

`apply(executable, entries)` is `hook(..., require_srvc=True)`.

The SRVC rewrite and the hook touch disjoint bytes. The SRVC table is at
file `0x9db0a0` and does not move; `srvc_check.verify` compares the two
executables it is given, so it works on a hooked pair. The two steps
therefore commute: `test_order_with_srvc_table_rewrite_does_not_matter`
builds both orders and gets identical bytes.

Call it right after the VWF patch in `plan()`:

```python
    elf, source_report = decrypt(verified_source(settings, EBOOT).read_bytes())
    executable, exec_report = patch(elf, widths)
    exec_report.update(source_report)
    exec_report['vwf_output_sha256'] = exec_report['output_sha256']
    from tools import ui_hook
    executable, exec_report['ui_hook'] = ui_hook.apply(executable, hook_entries)
    exec_report['output_sha256'] = sha256(executable)
```

Then three changes elsewhere:

- In the voice block, replace
  `exec_report['vwf_output_sha256'] = exec_report['output_sha256']` with
  `exec_report.setdefault('vwf_output_sha256', exec_report['output_sha256'])`.
  This keeps the label honest, because it now runs after the hook.
- `hook_entries` must come from translation data such as
  `work/translation/en/ui/eboot.json`:
  - `key` is the ELF bytes for cp932 sources and `ui_hook.utf8_key(raw)` for
    UTF-8 sources.
  - `english` comes from an encoder that writes every Latin character as its
    allocated VWF cell (`library_build.encode(text, mapping)` or
    `ui_build.encode(..., 'vwf')`), keeps Japanese as cp932, and passes
    escape bytes through.
- The hook English letters must be added to `tokens` before `allocate()`, or
  the cells will not exist.

## Canary and runtime test plan

`python -m tools.ui_hook canary --out work/output/scratch/ui_hook_canary`
writes `ui_hook_canary.json` and changes nothing else. It holds two entries
with fullwidth cp932 English, which is in the game's own font and needs no
VWF mapping. It also holds a dry-run report of `hook()` on the VWF baseline,
with all gates passed. `load_entries(path)` turns the file back into
`hook()` input.

| Id | Key | Shows | Evidence |
|---|---|---|---|
| `canary:cp932:pilot-training-melee-help` | cp932 at `0xa08962`: the Melee stat help of the Pilot Training screen (3 lines) | `ＳＪＩＳ　ＨＯＯＫ　ＯＫ` | The identical cp932 string is a key in Jigoku `ui_hook.json`, a hook on the cp932 drawer entry. Jigoku also held it as cp932 in its ELF. Whether the cursor starts on that row is not verified. |
| `canary:utf8:keyhelp-back` | UTF-8 at `0x88b668`, the key-help "Back" label; key `96df82e9` | `ＵＴＦ８ＯＫ` | It is in the `AID_UIT_KeyHelp` label family. It is UTF-8 only in both games, so a swap can only come through the r7 = 0 converter path. It is shown on the key-help bar of most menus. |

Neither string is statically proven to be drawn by `0x14158` on a given
screen. A fallback with a static proof is available: the name-entry help
lines at `0x88c698..0x88c8c8` are loaded from the TOC and passed with
`li r7,0` to the centred wrapper `0x149bc`, which branches to `0x14158`.
They show on the New Game name-entry screen, depending on the cursor.

The runtime test plan, RPCS3 first:

1. Build with the canary entries and boot. Check the log for loader, `vm`
   and PPU-recompiler errors. PH1's memory size grows by about 90 KB with
   the canaries, and by about 600 KB with a full table.
2. Load a save and open a menu with the key-help bar. "Back" should read
   `ＵＴＦ８ＯＫ`. This confirms the r7 = 0 path and the converter emulation.
3. Open Pilot Training (intermission), put the cursor on Melee, and the help
   box should read `ＳＪＩＳ　ＨＯＯＫ　ＯＫ`. This confirms the r7 = 1 path.
4. Play one dialogue scene and one battle to check for regressions. Compare
   frame rate on text-heavy screens with a no-hook build.
5. If neither canary swaps, the hook site is wrong. If only one swaps,
   suspect composition or a different renderer before the hook.

## Risks and open items

- **Not runtime-tested.** The stub, the fold and the canaries have not been
  booted on RPCS3 or hardware.
- **Centring and measuring still use the Japanese.** The centred wrapper
  `0x149bc` and measure `0x13d5c` see the Japanese, so swapped English is
  placed for the Japanese width until phase 2.
- **Strings outside the drawer.** OS dialogs, textures and strings drawn by
  other renderers are not covered.
- **Converter assumptions.** The emulation depends on two modelled calls.
  Both plausible models agree on all 4,466 strings, but the true libc and
  cellL10n behaviour is assumed, not observed.
- **Unmapped characters.** Keys containing the black square cannot tell
  unmapped characters apart. Review such keys.
- **Global content matching.** One Japanese string gets one English wherever
  it is drawn, so short generic keys are dangerous. Dynamic strings
  (`%s`/`%d` results, composed titles) will not match until phase 3.
- **Cost.** The stub runs on every draw call: about 16 instructions per byte
  of the string plus about 45. A 50-byte label costs about 850
  instructions; the longest inventory string (2,170 bytes) costs about
  36,000.
- **File size.** EBOOT.BIN grows from 10.6 MB to 15.7-16.3 MB, mostly zeros.
  ISO, deploy and Retro Trans Tools patch steps must accept it. xdelta
  compresses the zeros.
- **Hardware.** There is no SELF wrapper or hardware test for Tengoku.
  Jigoku's fold boots on a CFW PS3, but its placeholders were re-pointed and
  these are not.

## Reproduction

```powershell
$py = "<bundled python>"   # 3.12, no Capstone: builds and tests
& $py -m unittest tests.test_ui_hook -v
& $py -m tools.ui_hook validate-converter
& $py -m tools.ui_hook canary --out work/output/scratch/ui_hook_canary
python -m tools.ui_hook liveness          # Python 3.8 with Capstone
python -m unittest tests.test_ui_hook     # also passes with Capstone (adds the listing gate)
```

The tests in `tests/test_ui_hook.py` cover:

- a synthetic ELF with the exact measured layout, so they run without game
  files
- the real prepared ELF when it is present
- the grammar, the FNV vectors and a real 32-bit hash collision, home-slot
  clustering, prefixes, escape operands, `2f` and near-cap keys
- machine-code execution of hits and misses
- tamper detection and refusal of 7 layout or guard changes
- `utf8_key` samples and an oracle sample with special paths
- the canaries, all gates and the order of the SRVC rewrite.
