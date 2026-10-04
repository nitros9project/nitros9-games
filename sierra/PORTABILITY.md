# Sierra platform separation

## Purpose and current scope

The interpreter is being separated from its CoCo hardware implementation so
that a Wild Bits backend can be added without putting runtime platform checks
in performance-sensitive paths. This is an incremental refactoring, not a
completed Wild Bits port or a position-independent engine conversion.

The first boundary is sound. Resource loading, sound-list management, AGI
commands, completion flags, and the existing elapsed-time bookkeeping remain
in `objs/mnln.asm`. CoCo DAC playback, PIA setup/restoration, private saved PIA
state, and CPU-calibrated frequency and wave-count tables now reside under
`objs/platform/`.

## Assembly-time selection

`mnln.asm` includes `platform/sound-data.asm` at the original sound-data
location and `platform/sound-code.asm` at the original playback-code location.
These selectors include `coco-sound-data.asm` and `coco-sound-code.asm` for the
current CoCo build. They emit no runtime dispatch instructions.

When `WILDBITS` is nonzero, assembly deliberately fails with a missing-backend
message. The existing Wild Bits wrapper is still a scaffold; selecting it must
not silently include CoCo PIA code. Once a Wild Bits implementation exists,
the selectors will include its corresponding data and code files instead.

The shared makefile lists all four includes as dependencies of `mnln`, so
editing a backend or selector causes the affected module to rebuild.

## Current playback contract

The backend supplies `PlaySound` at the existing call site:

- Input: U points to a loaded sound node. The word at offset 3 of that node
  points to the existing converted sound stream. Its memory is already mapped
  by the caller's `SetLogicPage` operation.
- Stream: each note has a note-index byte, an amplitude byte, and a two-byte
  duration. A `$FF` note-index byte ends playback, followed by a two-byte
  elapsed-time value. This describes this interpreter's existing stream;
  it is not a new portable sound-file format.
- Output: D contains the elapsed-time word. Y, the caller's logic-script
  pointer, is preserved. X and U are clobbered, and condition codes are not
  preserved. The current CoCo implementation advances U through the stream.
- Execution: playback is synchronous. The CoCo backend disables IRQ/FIRQ
  during playback and enables them again during restoration, as before.
  It temporarily changes PIA control registers and restores their saved
  settings before returning.
- Storage: the CoCo implementation uses direct-page scratch words `$008E`
  and `$0090`, plus the three saved PIA bytes embedded in its private engine
  copy. These are existing dependencies, not newly introduced storage.

A replacement backend must satisfy the caller-visible contract or update the
shared caller explicitly. In particular, an asynchronous sound driver cannot
simply replace this routine without reconsidering completion flags and
elapsed-time bookkeeping. Existing code adjusts system/game time after the
blocking, interrupt-masked playback; a backend that leaves the system clock
running must adapt that behavior rather than count the duration twice.

The embedded saved PIA bytes remain writable and process-private through the
existing instance-isolation mechanism. Moving them into an include does not
make the module position-independent or eliminate self-modifying storage.
A future packed, shared-code engine must move writable backend state into
process-private data.

## Why this preserves CoCo performance

The extraction leaves every instruction, data byte, addressing width, and
relative location unchanged. Backend selection happens during assembly, not
inside a note loop. The cycle-balancing DAC test and calibrated delay loops
are retained exactly, including the RS-232-safe output handling.

Fresh assemblies before and after this change were compared for `sierra`,
`mnln`, `scrn`, and `shdw` in all fourteen game directories: all 56 modules
were byte-for-byte identical, including their headers and CRCs. A separate
assembly with `WILDBITS=1` was checked to fail with the intended missing-backend
error. These checks establish unchanged generated CoCo code for this step;
they do not establish Wild Bits operation or new hardware behavior.

## Subsequent boundaries

The next substantial boundary is memory mapping. Its interface must describe
which buffer is accessible and for how long, rather than expose CoCo MMU
register numbers as a supposedly portable API. The existing fixed-address
engine and bank-switching assumptions need a deliberate audit.

Graphics should expose strip/span operations and batched buffer access so
that optimized pixel loops remain within each backend. Input should retain
both typed parser commands and movement controls. Timing must preserve game
cadence rather than depend on CPU speed. Terminal switching and cleanup must
track ownership per process, including a policy for the shared sound device.

The Wild Bits implementation should follow the allocation, mapping, graphics,
and terminal-switching interfaces in the
[Wild Bits porting guide](https://github.com/jfed6000/f256_porting).
Every boundary should first retain the working CoCo behavior, with binary
comparison where an extraction is intended to leave generated code unchanged.

## Memory boundary: first extraction

The following routines now live in CoCo backend includes, selected at assembly
time and included at their original locations. The existing labels remain the
entry points, so neither call sites nor dispatch instructions change.

| Selector under `objs/platform/` | Entry points | Current responsibility |
| --- | --- | --- |
| `logic-map.asm` | `SetLogicPage` | Map the two-block resource window used by logic, view, and sound resources. |
| `priority-map.asm` | `MapShdwPage` | Map the priority buffer block into the `$6000` window. |
| `screen-map.asm` | `SetMapBlock` | Map a pair of blocks for screen-module buffer access. |
| `picture-map.asm` | `TwiddleMmu` | Map a pair of blocks for picture-module buffer access. |
| `engine-switch.asm` | `MmuSwitch` | Switch engine module banks, call the selected entry, and restore the caller's banks. |
| `map-snapshot.asm` | `mmuini1`, `mmuini2` | Obtain system and current-process mapping snapshots. |

Each selector includes a matching `coco-*.asm` implementation. A nonzero
`WILDBITS` setting rejects all four engine modules with a missing-memory-backend
error. The makefile explicitly tracks each selector and implementation as a
dependency of its containing module.

### Resource and drawing mappings

`SetLogicPage`, `SetMapBlock`, and `TwiddleMmu` receive a pair of physical block
numbers in A and B. They map adjacent 8 KB windows at `$2000` and `$4000` by
updating both the process's DAT image and hardware registers. The DAT image
is reached by temporarily mapping the process-descriptor block. These are
persistent mappings: the routines do not restore the previous resource window
on return. The existing callers control when to select another pair.

All three routines compare only A against their cached block number and skip
the switch if it matches. Existing code therefore relies on a stable pairing:
changing only B will not remap the second window. This behavior is preserved,
not generalized into a new portable mapping API.

The resource routine uses cache `$000A`, descriptor block `$0042`, and DAT-image
pointer `$0043`. Screen mapping uses the corresponding named equates and cache
`MmuBlkNum`; picture mapping uses `ShdwMmuBlock`. The implementations overwrite
X (resource/screen) or U (picture) when a switch occurs. Registers and condition
codes must not be assumed preserved. On a switch, IRQ/FIRQ are masked during
the DAT/hardware update and enabled afterward; the original incoming interrupt
mask is not restored. The cache-hit path retains the existing compare/return
behavior.

`MapShdwPage` takes no explicit argument. It selects physical block
`[$005F] + 8` into the `$6000` window, using `$0042` and `$0043` to reach the
DAT image. It restores the temporarily borrowed `$2000` hardware slot but
leaves the priority mapping in place. A, B, X, and condition codes are
clobbered. These direct-page fields and fixed window addresses are existing
CoCo layout dependencies.

### Engine switching and snapshots

`MmuSwitch` is special: startup copies the bytes between `MmuSwitch` and
`MmuSwitchEnd` into the private process area beginning at `$0659`. The routine
switches banks around an engine dispatch and returns through the saved caller
address. Moving its source into an include leaves that copy range, its size,
and its placement unchanged. It must not acquire an ordinary subroutine call
to code that would disappear when its own mapping changes.

`mmuini1` fills the system-map portion of `mmubuf`, after first capturing the
current process map through `mmuini2`. It borrows the `$2000` slot while
interrupts are masked and restores that slot and the saved registers.
`mmuini2` uses `F$ID` and `F$GPrDsc` to populate `gprbuf`, then copies the eight
physical block low bytes into `mmubuf+8`. Its process-descriptor offsets and
8-bit block representation are CoCo assumptions. This extraction preserves
the existing register behavior and error handling rather than redesigning it.

### What this does and does not establish

Fresh before/after builds again produced identical bytes for all 56 engine
modules across fourteen titles. Separate `WILDBITS=1` assemblies of each of
the four modules failed with the intended missing-memory-backend diagnostic.
Consequently this extraction adds no CoCo runtime overhead or address changes.

This is a source boundary around the central mapping mechanisms, not a
portable allocator. At this first extraction stage, startup, private-engine copying, and cleanup
still contained inline CoCo mapping operations; the loader extraction below
moves those operations into backends. Fixed-address
buffers, direct-page fields, process-descriptor access, embedded writable
state, and assumptions in the callers also remain. Implementing Wild Bits
requires redesigning these contracts around owned buffers and OS-managed
mapping windows, followed by adapting their callers; substituting different
MMU register addresses is insufficient.

The subsequent loader extraction separates CoCo loader/copy/cleanup operations
and documents their ownership and mapping lifetime. Keep the working CoCo
backend as the reference while determining the packed Wild Bits module's code,
data, and mapping-window budget.


## Loader, private copies, and cleanup

The next extraction moves the remaining executable MMU-register accesses out
of the top-level `sierra.asm`. These includes preserve the existing loader
implementation and its placement; they do not yet provide a new allocation
scheme.

| Selector under `objs/platform/` | Entry points | Responsibility |
| --- | --- | --- |
| `process-map.asm` | `SetupProcMap` | Find the current process's DAT image and alias its first data block into two working windows. |
| `runtime-copy.asm` | `CopySubsToData` | Copy the bank-switch routine and signal handler into private data memory. |
| `engine-load.asm` | `LoadModules` | Set up game-resource block pairs and load the three engine templates into private blocks. |
| `map-restore.asm` | `RestoreMmu` | Restore the original working-window DAT entries and hardware mappings. |
| `address-blocks.asm` | `TwiddleAddr` | Convert a logical address into its slot index and physical block pair using the saved map. |
| `private-load.asm` | `NMLoadModule`, `CopyPrivatePage` | Link/load a template, copy occupied pages into this instance's allocation, then unlink it. |
| `private-allocate.asm` | `SetupVirq` | Install the signal intercept, attach/open `/VI`, allocate private RAM, and register the timer. |
| `private-release.asm` | `CloseVirqPath` | Clear the timer registration, release path-owned RAM, close `/VI`, and detach the device. |

### Allocation and template ownership

`SetupVirq` requests 21 contiguous 8 KB blocks through `/VI`: 13 for game
storage and eight reserved for private engine pages. It rejects physical block
numbers outside the existing 8-bit MMU representation, or a range that would
wrap it. `PrivateNext` marks the next engine destination and `PrivateLimit`
marks the allocation's exclusive end. The path owns the allocation, and its
path/device fields record how far startup progressed for cleanup.

`NMLoadModule` takes X pointing to the module name and U identifying the
runtime remap-table base. It first tries `F$Link`, then `F$Load`. It validates
the occupied logical page range, checks destination capacity, and copies whole
8 KB pages into that instance's allocated blocks. It balances its own template
reference with `F$UnLink` on both the successful-copy and invalid-size paths.
On failure the existing carry/B error convention is retained; partially copied
pages remain part of the same path-owned allocation for shutdown to release.
On success the caller uses the retained logical header address to construct
its relocated dispatch address; it must not dereference an unlinked template.

`CopyPrivatePage` takes X as the source page and A as the destination physical
block. It saves CC, D, X, Y, and U, masks interrupts, borrows only the hardware
`$4000` window, and copies 4096 words. It restores the window to its private-data
alias and restores the saved registers and interrupt mask before returning.
The process DAT image is unchanged during the borrow, and there are no OS
calls while that temporary hardware mapping is active. This distinction from
the persistent resource mappings is essential to preserve.

### Setup, copied code, and restoration

`SetupProcMap` saves the original second and third DAT entries before replacing
them with aliases of the private data block. It records the descriptor's
physical block and DAT-image pointer for subsequent mapping operations.
`ProcMapReady` records completion; `RestoreMmu` skips restoration if setup did
not reach that point. Restoration updates both DAT entries and hardware slots.
These routines retain the original interrupt behavior and process-descriptor
layout assumptions.

`CopySubsToData` copies `MmuSwitch..MmuSwitchEnd` to `sub659` and
`SigIntercept..CloseVirqPath` to `int5EE`. Although the labels now cross include
files, their byte ranges remain exactly the same. No selector emits bytes.
The interrupt handler itself remains in `sierra.asm`; moving the allocation
backend does not change its timing or direct-page setup.

`TwiddleAddr` returns A as the logical 8 KB slot index and U as the physical
block pair from `mmubuf+8`; the adjacent slot wraps modulo eight. D and
condition codes are not preserved. This is a CoCo map-snapshot helper, not a
general owned-buffer lookup API.

`CloseVirqPath` releases only the recorded instance path and device reference.
Its position still serves as the exclusive end marker for the copied signal
handler. `ShutdownFull` retains its existing order: restore the screen, close
and release the VIRQ resources, then restore the original process mappings.
This extraction preserves the existing failure handling; it does not add a
new cleanup policy or change what happens on forced termination.

### Validation and remaining work

All 56 engine binaries were rebuilt and compared with the previously verified
pre-extraction binaries. Every byte matched, including the copied routines,
branch displacements, module headers, and CRCs. A Wild Bits assembly was
checked to fail with the explicit missing-loader-backend diagnostic. The
normal King's Quest I make targets also rebuilt successfully.

The source split now covers the central mappings and loader-side memory
operations. Hardware addresses can still appear in historical comments and
equates. Graphics, input, timer registration, fixed data offsets, and engine
callers retain CoCo-specific assumptions. A Wild Bits implementation must
replace the private-copy/bank-dispatch model with an appropriate packed,
position-independent layout and OS-managed buffer mappings; it must also
preserve per-instance ownership and balanced cleanup. The next useful
extraction is screen setup/presentation/restoration, followed by a deliberate
buffer-layout design rather than a mechanical register substitution.
