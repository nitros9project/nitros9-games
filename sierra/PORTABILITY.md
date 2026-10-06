# Sierra platform separation


## Current consolidation status

Both production runtimes now assemble common logic execution, dictionary lookup,
direction-vector stepping, screen/horizon clamping, terrain classification and
constraints, complete object collision scanning, and candidate-position
transactions. Platform bindings retain
storage, mapping and intentionally different legacy policies. The broader
migration is unfinished: per-cycle orchestration, destination triggering, resource/view
acquisition, rendering and remaining presentation/formatter behavior still need
consolidation. Historical sections below describe their stage when written;
the latest sections record the ongoing shared-engine work.

## CoCo portability groundwork status

The source-separation phase is complete: assembly-time CoCo backends now own
hardware I/O, platform service checks, memory mapping and private loading,
screen lifecycle/palettes, input sampling, timer interception, presentation,
and storage-dependent picture/object loops. Shared engine logic, parsing,
resource/file handling, logical clock updates, and font/table data remain
outside those implementations where appropriate.

This is a replaceable CoCo backend with documented legacy contracts. It is
not yet a platform-neutral, position-independent interpreter. The fixed-address
ABI and banked call sites deliberately remain intact to preserve behavior.
Converting that ABI, selecting a packed memory budget, implementing owned-buffer
mappings, and adding an actual Wild Bits backend are port implementation work
and are intentionally excluded from this phase.

The sections below document the successive extractions; statements about the
"next" boundary describe the stage when that section was written. The later
sections record subsequent shared-engine consolidation and its validation.

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

`mnln.asm` includes `platform/sections.d` at the original sound-data
location and `platform/sections.d` at the original playback-code location.
These selectors include `coco-audio.asm` and `coco-audio.asm` for the
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
| `sections.d` | `SetLogicPage` | Map the two-block resource window used by logic, view, and sound resources. |
| `sections.d` | `MapShdwPage` | Map the priority buffer block into the `$6000` window. |
| `sections.d` | `SetMapBlock` | Map a pair of blocks for screen-module buffer access. |
| `sections.d` | `TwiddleMmu` | Map a pair of blocks for picture-module buffer access. |
| `sections.d` | `MmuSwitch` | Switch engine module banks, call the selected entry, and restore the caller's banks. |
| `sections.d` | `mmuini1`, `mmuini2` | Obtain system and current-process mapping snapshots. |

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
| `sections.d` | `SetupProcMap` | Find the current process's DAT image and alias its first data block into two working windows. |
| `sections.d` | `CopySubsToData` | Copy the bank-switch routine and signal handler into private data memory. |
| `sections.d` | `LoadModules` | Set up game-resource block pairs and load the three engine templates into private blocks. |
| `sections.d` | `RestoreMmu` | Restore the original working-window DAT entries and hardware mappings. |
| `sections.d` | `TwiddleAddr` | Convert a logical address into its slot index and physical block pair using the saved map. |
| `sections.d` | `NMLoadModule`, `CopyPrivatePage` | Link/load a template, copy occupied pages into this instance's allocation, then unlink it. |
| `sections.d` | `SetupVirq` | Install the signal intercept, attach/open `/VI`, allocate private RAM, and register the timer. |
| `sections.d` | `CloseVirqPath` | Clear the timer registration, release path-owned RAM, close `/VI`, and detach the device. |

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

## Screen setup, presentation, and restoration

The screen lifecycle and CoCo palette operations are now selected through
these backend includes, at their original code/data locations:

| Selector under `objs/platform/` | Entry points/data | Responsibility |
| --- | --- | --- |
| `sections.d` | `ColorTable` | Startup composite/RGB palettes using CoCo color codes. |
| `sections.d` | `ConfigureMonitor` | Read the monitor preference, apply `-r`, and store the game's display type without changing the global monitor mode. |
| `sections.d` | `SetupScreen` | Allocate, record, clear, display, and initialize the instance's screen and palette. |
| `sections.d` | `DisableKbdInt` | Exchange saved echo/EOF/interrupt/quit options with the input path's options packet. |
| `sections.d` | `RestoreScreen` | Restore options, reset the palette, select text screen zero, and free the recorded graphics screen. |
| `sections.d` | `PaletteData` | Interpreter composite/RGB palettes, separate from the startup table. |
| `sections.d` | `cmd_toggle_monitor` | Toggle the game's palette selection and write the sixteen palette commands. |

### Screen ownership and layout

`SetupScreen` uses standard output and CoCo `SS.AScrn` screen type 4
(320 by 192, sixteen colors). It records the returned screen number in
`HiResScrnNum` immediately after allocation, so later initialization failures
still leave ownership information for shutdown. It preserves the returned
mapping address across monitor selection, snapshots the process map, and
uses `TwiddleAddr` to record the physical screen block pairs.

The implementation then clears the fixed logical range `$6000..$D7FF`
(30,720 packed-pixel bytes), displays the allocated screen with `SS.DScrn`,
and writes sixteen four-byte `ESC $31 register color` palette sequences.
Each byte of pixel data represents two sixteen-color pixels. This is an
existing CoCo address/layout contract, not an arbitrary mapped-framebuffer
interface. A Wild Bits backend cannot reuse the clearing range, packed-pixel
format, palette codes, or screen-call arguments unchanged.

The startup routine returns carry/B errors from the existing OS operations
and balances its local stack frame. It sets `OptionsChanged` only after
terminal-option changes succeed. Other registers are not a preserved API;
callers rely on the existing routine's behavior.

`RestoreScreen` skips work when no graphics screen is recorded. Otherwise it
exchanges terminal options back when needed, writes the default-palette
sequence, selects text screen zero, and requests `SS.FScrn` for the recorded
screen number. It clears that number only when the free operation succeeds.
The extraction preserves the original cleanup error handling, including its
handling of earlier restoration errors; it does not make new guarantees
about recovery from failing driver calls.

### Terminal options and game palette commands

`DisableKbdInt` is an exchange operation, not a one-way setter: the saved
bytes start at zero during setup, and a later call swaps the original values
back. It reads and writes `SS.OPT` on standard input, with a 32-byte temporary
packet. Screen setup and cleanup both call this helper, so it is selected
alongside the screen backend even though the packet operation belongs to SCF.

`cmd_toggle_monitor` changes the game-local display-type byte and writes the
selected palette to standard output. It does not change the global monitor
setting. Both startup and game palette tables remain in their original
locations, and the command's instruction sequence and existing error path
are retained. This refactor does not repair unrelated palette-write failure
behavior or introduce a new palette abstraction.

The shared `cmd_text_screen`, `cmd_graphics`, and `SetGraphicsMode` routines
remain in `mnln.asm`. Their current actions include game flags, renderer
dispatch, and status/input redraws rather than direct OS screen selection.
Likewise, `text_color` still creates packed foreground/background bytes for
the existing renderer. These are dependencies for the forthcoming renderer
interface and should not be confused with the OS screen lifecycle extracted
here.

### Verification and next boundary

All four engine modules were rebuilt for all fourteen games and compared with
the previously verified binaries: all 56 were byte-for-byte identical. The
normal King's Quest I make targets were also rebuilt. Both affected modules
were checked to reject `WILDBITS=1` with the missing-screen-backend diagnostic.
The shared makefile tracks every new selector and implementation explicitly.

There is no runtime platform dispatch or new per-pixel call in this change.
The next boundary is the renderer's packed-pixel and fixed-window contract:
strip/span drawing, text-color packing, palette-index interpretation, and
framebuffer mapping lifetime. Preserve AGI picture/priority semantics while
allowing each backend to keep its optimized drawing loops.

## Packed-pixel renderer boundary

The renderer is now selected at assembly time through four additional includes:

| Selector | Implementation boundary |
| --- | --- |
| `sections.d` | `CocoViewPal`, screen clears, rectangle/border fills, picture-strip drawing, and screen-strip copying. |
| `sections.d` | `DrawView` and its clipped view/cel drawing loops. |
| `sections.d` | `DrawSprites`, the existing software 8-by-8 glyph renderer. |
| `sections.d` | `text_color`, which converts foreground/background indices into repeated-nibble bytes. |

Each selects its `coco-*.asm` counterpart; Wild Bits assembly reports a missing
renderer backend. No per-pixel dispatch or new subroutine call is introduced.
The ten-entry `scrn` dispatch table remains unchanged. `UpdateViewList` remains
shared because it traverses game objects and updates their coordinate/flag
bookkeeping around calls to `DrawView`. `BitmapFont` also remains shared: its
one-bit glyph data is independent of the destination framebuffer format.

### Existing rendering contract

This is an extraction of the current drawing interface, not a new portable
pixel API. Entry points retain their stack arguments, direct-page scratch,
register behavior, and mapping dependencies. The comments within each backend
retain the individual routines' existing argument descriptions.

The CoCo renderer assumes a fixed framebuffer beginning at `$6000`, a
160-byte physical row stride for a 320-pixel display, and two four-bit color
indices per destination byte. `CocoViewPal` expands each sixteen-color index
into a repeated-nibble byte (`$00`, `$11`, ... `$FF`). The software loops retain
their current clipping, transparent-pixel handling, and byte merging.
`DrawView` uses `SetMapBlock` to select resource block pairs; those mappings
persist until another operation selects a different pair. Rendering and
mapping therefore remain coordinated through the existing fixed windows.

`text_color` receives the foreground index in A and background index in B.
It masks both to four bits, duplicates each nibble, and stores the resulting
bytes at `$024C` and `$024D`. A and B contain those packed bytes on return;
condition codes are not preserved. A Wild Bits renderer using one byte per
pixel must change this representation together with every consumer of those
fields. Merely replacing this routine would leave existing fills and text
paths interpreting the fields incorrectly.

`DrawSprites` is a font-glyph renderer, not a hardware sprite API. A Wild Bits
backend can initially draw the same shared font into its bitmap. Likewise,
AGI view objects need not become hardware sprites to preserve the game's
priority and composition behavior.

The picture decoder and priority-buffer algorithms in `shdw.asm` remain
shared for this phase, including their current fixed addresses and CoCo
mapping dependency. They are not yet a position-independent, arbitrary-buffer
implementation. The engine's text/graphics commands and renderer call sites
also retain their banked dispatch convention.

### Verification and remaining design work

All 56 engine modules were rebuilt and compared with the previous verified
screen-extraction binaries; every byte matched. The normal King's Quest I
make targets rebuilt the affected modules. Separate Wild Bits assemblies of
`mnln` and `scrn` failed with the intended missing-renderer diagnostic. The
makefile tracks the new selectors and implementations.

The next substantive design step is to specify owned picture, priority, and
framebuffer buffers with explicit dimensions, formats, and mapping lifetimes.
Audit the callers and scratch fields against that design before implementing
Wild Bits routines. The current includes make the optimized CoCo implementation
replaceable at build time; they do not by themselves make its fixed-address
calling convention portable.

## Buffer layout and mapping-lifetime design

`objs/buffer-layout.d` now names the shared 160-by-168 AGI picture dimensions.
Its CoCo selection includes `platform/coco-buffer-layout.d`, which names the
existing screen width/height, packed-pixel stride, framebuffer range, mapping
block size, and private-copy window. Selected clear, copy, and drawing operands
use these equates instead of literal numbers. The constants emit no bytes;
all 56 rebuilt modules still match the previous renderer binaries exactly.
Other literals remain where their meaning requires further caller analysis.
Changing these constants alone cannot change the engine's fixed-address ABI.

### Proposed portable model

The following is the intended replacement contract, not an implemented buffer
ABI. Introduce it together with the affected callers rather than mixing new
handles and old absolute pointers in the same operation.

| Buffer role | Logical meaning | Storage responsibility |
| --- | --- | --- |
| Picture | 160-by-168 AGI color indices | Private to the game; independent of physical screen packing. |
| Priority/control | Priority and control information used by game logic | Private to the game; preserve decoder and collision semantics exactly. |
| Framebuffer | Presented image, text, and composed views | Owned by the terminal/game through the platform graphics service. |
| Resource | Loaded logic, view, picture, or sound bytes | Private allocation or a deliberately immutable shared resource, with an explicit lifetime. |
| Scratch | Temporary decode, drawing, and staging bytes | Private to the process; never shared implicitly through module code. |

These roles need not imply separate allocations on CoCo. Its existing picture
representation and banked layout can remain behind its backend. For an initial
Wild Bits implementation, one byte per logical picture pixel and a separate
priority/control representation are reasonable candidates; the latter must
be chosen after auditing the existing combined values and masks. Do not
convert AGI priority/control values into display palette indices.

The Wild Bits presentation candidate is a 320-by-240, one-byte-per-pixel
framebuffer with a 320-byte stride (76,800 bytes). A 160-by-168 one-byte picture
would occupy 26,880 bytes; a separate one-byte priority/control plane would
occupy the same amount. These are planning sizes, not an allocation implemented
here. Account separately for text placement, staging buffers, resource blocks,
private engine data, and graphics allocation alignment.

### Buffer identity and ownership

A future process-private buffer record should describe its role, dimensions,
stride, format, byte length, allocation owner, and backing allocation/block
list. It should identify storage independently of whichever logical address
happens to map it. Do not store a borrowed mapped address as a permanent resource
pointer or serialize it into a saved game. Save/restore must reconstruct such
references from game state and owned-resource identity.

An allocation is published to callers only after successful setup. Every
failure path releases the allocations created so far. A buffer's release
operation uses its recorded allocator/owner; a framebuffer obtained through
a graphics service is released through that service. This preserves the
per-instance ownership discipline already established for the CoCo backend.

### Mapping lifetime

For a backend that uses OS-managed windows, a mapping operation should receive
buffer identity plus a byte offset and requested access length. It should
return the actual mapped address and contiguous accessible length; a caller
must split work at that boundary. The returned address must come from the OS
mapping operation, not an assumed fixed window address.

A mapped pointer is valid only until that window is unmapped or reused. Its
scope should be one strip/span or a documented batch of operations. Nested
resource and framebuffer access needs distinct windows or explicit staging:
remapping a resource while retaining a pointer into the same window is invalid.
Map once outside the inner pixel loop, draw the accessible span, then advance
the buffer offset and remap as necessary. The mapping service must keep its
allocation pinned while a mapping is active and balance mapping cleanup on
errors and normal completion.

For Wild Bits, reserve the planned two service windows explicitly in the
module/data budget. One candidate is a resource/picture window and a framebuffer
window; priority accesses that compete for the former need short-lived maps
or private staging. Avoid designing an inner loop that requires three
simultaneous mapped buffers without first proving the logical address budget.
The legacy CoCo backend's interrupt-masked hardware borrow remains a separate
implementation technique with its existing restrictions.

### Rendering contract and migration order

Shared code should pass logical coordinates, color indices, source offsets,
and clipping information. The backend performs pixel packing and chooses
optimized span/glyph/view operations. Text foreground/background remain
logical indices at this boundary; the existing repeated-nibble state must
be adapted with all of its readers, not changed piecemeal. Keep font data and
AGI picture/priority rules independent of display storage.

Before adopting the new ABI, audit picture/priority reads and writes in
`shdw.asm`, resource pointers and text-color consumers in `mnln.asm`, and
screen/resource mapping use in the rendering backends. Then implement a
small owned-buffer mapping and span-drawing path, verify its allocation/error
cleanup, and use it for the first Wild Bits picture-display milestone. Leave
the working CoCo backend available as the behavioral reference throughout.

This phase supplies named current geometry and the design contract. It does
not implement Wild Bits allocation, convert the engine to position-independent
code, or claim that old save files remain compatible with a future layout.

## Picture/priority access audit: findings

The first source audit establishes a useful distinction: the current AGI
picture/priority buffer is **one combined byte per logical pixel**, whereas
the presented CoCo framebuffer packs **two display pixels per byte**. They
have the same 160-byte row stride for different reasons and must not be
interchanged. `AgiCombinedBytes` now names the 26,880-byte combined storage
size; the CoCo layout names its existing `$6040..$C93F` range, with exclusive
end `$C940`. `shdw.asm` uses those equates without changing generated code.

### Access inventory

| Code | Observed storage dependency | Migration implication |
| --- | --- | --- |
| `RenderPic`, `EnablePicDraw`, `EnablePriDraw` | Initial fill `$4F`; color in the low nibble and priority in the high nibble during command drawing. | Preserve combined-byte meaning before changing display packing. |
| `SbuffPlot`, `SbuffXLine`, `SbuffYLine` | Compute addresses from fixed base and 160-byte rows; update bytes as `(old OR DrawMask) AND DrawColor`. | A buffer interface must preserve selective color/priority updates. |
| `SbuffPicFill` | Flood-fill reads, masks, and writes combined bytes using direct pointers and shared scratch. | Moving to mapped chunks needs explicit treatment of traversal and scratch lifetimes. |
| `PicCmdLoop` | Maps a resource pair, then reads the picture-command stream through `GivenPicDataPtr`. | Preserve the input pointer's lifetime while drawing into the output buffer. |
| `PicBufUpdateRemap` | Swaps both nibbles of every byte in place. | Buffer orientation is mutable state; identify its callers before removing or relocating this operation. |
| `ObjChkControl` | Reads high-nibble priority/control values along an object's baseline. | Logic must access combined priority information, not presentation pixels. |
| `ObjBlit`, `ObjAddPicPri` | Combine cel data and picture/priority data using fixed pointers and masks. | View resource access and destination access must coexist or use staging. |
| `BlitSave`, `BlitRestore` | Copy complete combined bytes for rectangles into/from buffers referenced by blit records. | Saved backgrounds must retain priority as well as color. |
| `PicRenderSetup`, picture decoding in `mnln` | Maps the shadow block and maintains decoder state and output pointers in scratch fields. | The vector-command decoder is not the only producer to audit. |
| `CalcPriAddr`, its callers | Construct priority addresses from row offsets and a banked pointer representation. | Returning an old fixed pointer cannot serve as a future buffer identity. |

These observations come from the instructions, not just the disassembly's
comments. In particular, `PicBufUpdateRemap` really does change the buffer in
place. A follow-up call-chain audit must establish the orientation expected
at each boundary; this inventory does not assume that every consumer always
sees the command-drawing orientation.

### Text-state audit

Global `$024C`/`$024D` accesses include the packed text-color pair, color-stack
save/restore, and temporary changes around text drawing. Some matching numeric
operands are **stack-relative** (`$024C,s` or `$024D,s`) in save/restore UI code
and refer to unrelated local data. Do not change them with a textual address
replacement. The `$024D` alias/comments also vary between routines; trace the
actual packing routine and consumers when assigning portable field names.

### Revised first-port recommendation

Keep a single combined picture/priority buffer for the initial Wild Bits port.
Separating its nibbles into independent planes is optional future work and
would require changing fill, collision, background save/restore, and blitting
at the same time. Retaining the combined format uses 26,880 bytes and preserves
more of the working algorithms. Convert the appropriate color nibble into
Wild Bits display palette indices only at the presentation boundary, once the
orientation at that boundary is proven.

A combined logical buffer and the candidate 320-by-240 framebuffer together
need 103,680 bytes before alignment, resource storage, and scratch. This is a
planning total, not proof that the existing fixed-address engine can map them
simultaneously. The logical address budget and mapping schedule still govern
implementation.

### Implementation gate

Before introducing mapped-buffer calls into these algorithms:

1. Trace the nibble-swap dispatch and each producer/consumer's orientation.
2. Classify each retained pointer as an owned allocation offset or a borrowed
   mapped pointer, including pointers embedded in view and blit records.
3. Design the mapping schedule for picture input, combined destination,
   view/cel input, and saved-background storage. Two windows do not permit
   arbitrary simultaneous access to all of them.
4. Measure the code/data budget and select a staging strategy that keeps
   mapping calls outside inner drawing loops.

The audit changes no game behavior. All 56 modules are compared against the
previous verified binaries; this establishes equivalence of the named-size
changes, not correctness of a new portable buffer API or Wild Bits runtime.

## Nibble-swap call chain and pointer lifetimes

`gfx_picbuff_update` in `mnln.asm` tests `GfxPicBufRotate` (`$0550`). When
nonzero it writes dispatch offset zero to `$0021`, obtains the shadow remap
table through `$0028`, and calls the copied dispatcher at `$0701`. Shadow
entry zero is `PicBufUpdateRemap`: it swaps the nibbles in every combined
picture byte **in place**, without copying the buffer. Then the update routine
always dispatches screen entry zero (`DrawStrip`) through `$0019`/`$0026`.
`DrawStrip` selects the low nibble and translates it through `CocoViewPal`.

Thus presentation normally uses the low-nibble color, while a swap makes the
other nibble available to that same renderer. The original "shadow copy"
comment at this call site was misleading and has been corrected. The code
now uses the existing `GfxPicBufRotate` name instead of its literal address.

`CmdSaveGame` increments that byte, calls `gfx_picbuff_update`, runs
`BooleanPoll`, calls the update routine again, and clears the byte. Two swaps
restore the original bytes because swapping is an involution. Other update
call sites also exist in `mnln`; any invoked while the flag is nonzero also
perform a swap. Consequently a future presentation routine must model this
explicitly rather than assume the flag means "dirty" or "copy required".
The observed outer pair is not proof that every UI/error/nested path is safe
under a replacement implementation. Trace those paths before eliminating the
mutation or changing the UI's displayed content.

### Pointer classes established by the audit

| Pointer/reference | Current validity | Portable replacement requirement |
| --- | --- | --- |
| `GivenPicDataPtr` | Input command stream in the resource mapping selected by `PicCmdLoop`. | Retain resource identity plus offset; keep its mapping alive while commands read it. |
| `gfx_picbuff + y*160 + x` | Combined destination in the legacy engine's fixed/banked address layout. | Logical combined-buffer offset; obtain a mapped address only for the accessible span. |
| Object `$08` block pair and `$10` cel pointer | `ObjBlit` maps the pair before dereferencing the cel pointer. | Keep the backing resource identity associated with the cel offset; a pointer alone is insufficient. |
| Blit record `$0C` pair and `$0A` saved-background pointer | `BlitSave`/`BlitRestore` select the pair and copy complete combined bytes. | Associate background identity/offset with its mapping and preserve both nibbles. |
| `ScratchA8`, `ScratchAD`, X/U traversal pointers | Temporaries inside fill/blit operations that may traverse rows. | Never retain them across reuse of their mapping window. |
| Screen renderer source X and destination Y | Source may be remapped in `DrawStrip`; destination remains in the current screen layout. | Separate source/destination mapping lifetimes and split spans at both boundaries. |

The field meanings above are taken from these routines' actual loads. They
are not a universal description of every structure using the same numeric
offset. CoCo routines obtain simultaneous access through their existing
banked engine layout; source extraction has not removed that dependency.

### First portable implementation boundary

Start with presentation of a combined buffer to a framebuffer: input should
be buffer identity, source offset/rectangle, and an explicit choice of color
or priority nibble; output is a framebuffer span. A Wild Bits implementation
can select the nibble during conversion without mutating the source, provided
the current save/UI behavior is reproduced deliberately. Keep CoCo's existing
implementation as the reference until that equivalence is checked.

Presentation is a narrower first implementation than converting flood-fill
or sprite save/restore: those operations need additional live storage and
traversal state. This audit establishes their dependencies but does not yet
implement their mapped-buffer replacements. The comment/symbol changes leave
all 56 generated engine binaries byte-for-byte identical.


## Remaining platform boundaries and completion checks

The final extraction adds these selectors and matching CoCo implementations:

| Selector | Boundary and retained contract |
| --- | --- |
| `sections.d` | `ReadJoystick`/`ReadJoyButton`: standard-input `SS.Joy` sampling, existing result layout and button field, Y preserved. |
| `sections.d` | `ReadStdinByte`: availability check followed by one-byte read; A returns the byte or zero on unavailable/error, Y preserved. |
| `sections.d` | Signal `$80`, direct-page setup from intercepted U, divide-by-three countdown, and dispatch to the shared clock update. |
| `sections.d` | Matching terminal names and CoCo ownership-aware screen-service version check before startup changes state. |
| `sections.d` | Existing nibble-swap mode followed by full-picture strip dispatch; preserves the save/UI behavior. |
| `sections.d` | Legacy priority-pointer coordinate conversions (`CalcPriAddr`, `CalcPriCoord`). |
| `sections.d` | Combined-buffer fill, plotting, line drawing, and flood-fill loops using the legacy fixed window. |
| `sections.d` | In-place combined-byte nibble swapping. |
| `sections.d` | Priority/control contact checks, cel composition/mirroring, background save/restore, and related fixed-buffer operations. |
| `sections.d` | CoCo elapsed-time compensation after synchronous interrupt-masked sound, including page restoration. |

Some of these algorithms are logically reusable, but their current
implementations directly depend on storage addresses, masks, or mapping
lifetimes. Keeping them in the backend prevents treating that implementation
as already portable. A later port may reuse or move their logical portions
once it supplies the new buffer contract. CoCo rendering loops and dispatch
addresses remain unchanged.

### Input and timing responsibilities

Event queues, key translation, joystick debounce/direction decisions, and AGI
parser handling remain shared. The backend samples the device using the
existing representation. The CoCo joystick routines retain their current
error handling rather than introducing a new success/failure convention.
A replacement must normalize results for their callers or adapt those callers
explicitly. Keyboard sampling must continue to support typed command input,
not only held movement keys.

The signal interceptor remains inside the same copied byte range, now through
an include. `SigHandlerCore` remains shared and advances the game timer and
logical clock; its tick accumulation expects twenty logical ticks per second.
The CoCo intercept reduces the existing VIRQ stream by three. A replacement
must reproduce that cadence from its own timer source, not carry over the
countdown independently of the source frequency. No OS calls were added to
the handler, and its copied relative branches retain their original bytes.

`CheckInstanceServices` belongs to the backend because its `SS.AScrn` version
query is the CoCo ownership API, not a portable graphics-capability query.
Generic OS-9 file/device operations remain shared; a matching service number
alone is not evidence that a platform implements the same graphics semantics.

Sound completion flags remain in the shared command handler. The elapsed-time
compensation block is now platform-selected because CoCo DAC playback stops
timer interrupts. It retains its existing system-time correction and game
clock correction. A future interrupt-friendly audio backend must supply an
appropriate replacement rather than increment clocks that already advanced.

### Save/UI behavior and ownership

The CoCo presentation implementation retains every existing swap and dispatch,
so no save/UI behavior changes in this phase. The audit identified the outer
swap pair and additional update callers; it did not prove a replacement
presentation scheme for all nested UI and error paths. That proof is required
when implementing a new scheme, not inferred from this extraction.

Cel mirroring and writable dispatch tables still depend on the existing
private copies/resources. Module code cannot become globally shared merely
because its source is under `platform/`. Keep those mutations private until
a subsequent layout conversion relocates writable state explicitly.

### Reproducible verification

Run the committed comparison from the repository with an installed assembler
and the NitrOS-9 definition directory:

```sh
python3 sierra/tests/check_platform_equivalence.py \
  --baseline 83e5fb4 --assembler /path/to/lwasm --defs /path/to/nitros9/defs
```

The checker obtains the baseline sources through `git archive` without changing
the checkout, assembles each of four modules using each game's definitions,
and compares complete module bytes. It builds in a temporary directory and
leaves the game binaries alone. The baseline revision is explicit so later
intentional behavior changes can choose their own reference. This verifies
generated-code equivalence; it is not a substitute for runtime testing when
new behavior is introduced.

At completion, all 56 modules across fourteen games match pre-refactor commit
`83e5fb4` byte-for-byte. Normal make builds were checked for every game's four
engine targets. Wild Bits selections are checked to fail explicitly rather
than emit CoCo code. There is no implemented Wild Bits layout, framebuffer,
audio, or input backend, and none is claimed by this groundwork.


The compilation/include paths and explicit backend dependencies now live in
`sierra-engine.mak`. Both the standard `sierra-game.mak` and Black Cauldron's
standalone makefile include it; Black Cauldron retains its existing disk recipe.
This prevents a backend edit from being missed by that title and supplies the
same source include path to every game. The comparison checker also verifies
that all four module sources reject the unimplemented Wild Bits selection.


## Wild Bits implementation has started

The follow-on `tests/probes/wbpic.asm` is the first native presentation module.
It implements the proposed combined-buffer-to-framebuffer path using OS-managed
mapping, separate process data, and a terminal-owned bitmap. It accepts an
uncompressed combined-buffer export rather than existing game resource files.
The unfinished packed-engine wrapper is still excluded from the build.

The target is separate instances on separate terminals. The viewer checks
input/output terminal identity, refuses an existing bitmap zero, requires
background/foreground notifications, and keeps signal state private. Its
signal handler addresses fields through intercepted U rather than DP.
Native CPU checks cover distinct module/data addresses, different map-return
addresses, span boundaries, short reads, malformed files, cleanup failures,
terminal identity, and visibility flags. A separate `wbjr2` MAME test now runs
the actual OS/graphics driver: it verifies every displayed pixel, two-terminal
picture restoration, independent exit, relaunch, and an unchanged free-memory
map after two launch/quit cycles. The diagnostic pair and King's Quest I
reference both passed. Physical hardware validation remains outstanding. See
[WILDBITS-README.md](WILDBITS-README.md) for exact build/run instructions and
the acceptance checklist. The CoCo binaries continue to match `83e5fb4`.


A host reference bridge now extracts a plain on-disk picture resource and runs
the existing 6809 picture renderer to produce `wbpic` input. This establishes
a real-game reference for the native presentation tests; it does not implement
native resource decoding. King's Quest I picture 1 was rendered and visually
inspected as the castle scene. See the Wild Bits README for reproduction,
supported resource encoding, and the reference hash.

Native resource loading now exists as `objs/platform/wildbits-memory-resources.asm`, exercised
by the position-independent `wbres` probe. Real `wbjr2` MAME RBF reads matched
the host reference for King's Quest I picture 1 and an 8 KB resource at a
20-bit offset in volume 15. Native command decoding is described below.
See [WILDBITS-ENGINE.md](WILDBITS-ENGINE.md) for the planned module structure:
one native program may include converted routine bodies, but the old complete
module sources cannot simply be included into an outer module. The untracked
packed scaffold remains untouched and excluded from the build.

The native decoder now handles F0-FA through private state, bounded reads and
immutable dispatch. Its combined picture occupies four owned physical blocks,
accessed through one cached OS mapping window; scanline fill uses a bounded
private seed stack. Export unmaps before disk writes. MAME checks use actual
terminal stdin: a shell script's RBF stdin must never receive graphics codes.
The module checks SCF input before allocation. Two terminal-path runs must
produce identical diagnostic buffers and restore the free-memory map.
Solid/splatter pen conversion now passes differential CPU checks for all
sizes/styles. `wbrun` integrates native resource loading, decoding and
presentation through small shared includes; concurrent MAME instances passed
all pixel, switching, exit/relaunch and memory checks with the real castle
resource. Native LZW, mapped expanded resources and the bytecode core now
exist as small shared includes. CPU checks cover all 228 compressed KQ1 assets,
logic conditions/arithmetic and cached/nested calls. MAME checks cover logic 0
and cross-page bytecode on both terminal paths with unchanged free memory.
Object/view motion, text/input, game commands and the main game cycle remain;
this is not yet playable. Performance parity has not been established. No existing CoCo engine source was changed.


### Native game integration checkpoint

The Wild Bits owner now follows the CoCo approach of small included bodies,
with one module header and private process state. Object/view metadata, room
transitions, menus, strings, keyboard bindings and replay bookkeeping live in
separate command components. Picture loading, background ownership, sprite
composition, literal text and scheduling each have their own `game-*` bodies.
The shared bitmap font is now `objs/font-data.asm`; assembling the CoCo `scrn`
module before/after extraction produces identical bytes.

CPU tests cover the native picture/view/text path, repeated logic cycles and
controller input. Real Wild Bits MAME checks cover two picture-command game
instances, visibility switching, independent exits/relaunch and free-memory
recovery. This is not full game acceptance: motion, vocabulary parsing, dialogs,
sound and remaining commands still need integration. See
[WILDBITS-README.md](WILDBITS-README.md) and [WILDBITS-MAME.md](WILDBITS-MAME.md)
for module budgets, exact test scope and the older test kernel's RAM limit.

## Shared-engine consolidation

The CoCo and Wild Bits owners now assemble the same F0-FA picture-command
catalog, F0-F3 color/mask bodies, and F4-F7 corner/line command bodies from
`objs/shared/picture-command-table.asm`, `picture-colors.asm`, and
`picture-commands.asm`. These join the already shared coordinate, raster-line,
and pen-geometry routines. The bounded-reader selection happens at assembly
time; CoCo retains its direct stream reads and Wild Bits retains its error
checks. No runtime platform dispatch was added.

At this checkpoint, CoCo `shdw` and Wild Bits `wbgame` are both byte-for-byte
identical to their pre-consolidation builds. Both build graphs track the new
includes. The decoder regression compares every pixel with the CoCo renderer
at two relocated code/data addresses and exercises malformed input and
mapping failures. Its emulated timeout is now 900 seconds so error-injection
fixtures complete after the full picture comparisons.

This does not complete the shared-engine migration. The native startup and
bounded stream handling in `objs/platform/wildbits-graphics.asm` remain owner adapters;
flood-fill workspace, resource loading, logic execution, object state, and
parser integration still require reconciliation. The former `wildbits` directory has been removed: module owners now live
in `objs`, native adapters in `objs/platform`, and host utilities in `tests`.
Logic execution and state-layout reconciliation are still unfinished. A file qualifies as shared only when
both platform owners assemble it.

### Shared variable and flag command execution

Commands 1–11 now come from `objs/shared/variable-commands.asm` in both
`mnln.asm` and the native logic owner. The shared bodies implement saturating
increment/decrement, modulo-byte assignment/addition/subtraction, variable
operands, and left/right indirect assignment. Each owner expands
`VARIABLE_TABLE` into its existing variable-table address. The CoCo owner
reads operands from its script Y; the native owner has already bounded and
copied operands into private memory and points Y there. Shared handlers
consume bytes identically; no mapped pointer is retained.

Commands 12–17 now come from `objs/shared/flag-commands.asm`. The indirect
variants use `FLAG_VARIABLE_TABLE`; `SetFlag`, `ClearFlag`, and `ToggleFlag`
are storage interfaces implemented in `platform/coco-logic.asm` and
`platform/wildbits-logic.asm`. CoCo retains packed flags and the native
owner retains canonical byte flags. This avoids prematurely changing every
flag reader throughout either engine while removing duplicate command rules.

The native arithmetic opcode chain is replaced by an immutable, table-relative
dispatch to these common command bodies. Both CoCo macros emit the original
instructions, and the resulting CoCo `mnln` is byte-identical to the baseline.
The native game now uses 20,966 code bytes and still 24,572 private bytes; the
probe interpreter uses 6,642 code bytes. No new process data is required.

The native control/arithmetic tests cover relocation, saturating edges,
wrapping, indirect assignment through index 255, flag operations, AND/OR/NOT,
argument/branch bounds, and immutable code. The mapped interpreter tests
cover physical page crossings, cached/nested calls, and ownership cleanup.
Whole-game pixel and real-driver sustained-play checks validate integration.
The full engine migration remains incomplete beyond these command groups.

### Shared condition predicates and catalog

Tests 1–8 (equal/less/greater, immediate/variable, and direct/indirect isset)
now use `objs/shared/condition-tests.asm` in both owners. The unsigned branch
semantics are the CoCo implementation. `TEST_VARIABLE_TABLE`, `TestFlag`, and
`CONDITION_TRUE`/`CONDITION_FALSE` adapt storage and boolean return conventions
without changing the algorithm: CoCo returns A, native returns B.

`objs/shared/agi-test-table.asm` is the common catalog of all 19 condition
entries and operand descriptors. CoCo expands handler words and descriptors;
native expands operand counts. Dynamic `said` operands remain handled by the
native bounded operand reader. The remaining external predicates still have
owner implementations and are not yet consolidated by sharing this catalog.

CoCo's old numeric table addresses are now handler labels. Comparing its
module to the previous baseline proves the only differences are the reserved
entry-zero target (old $0F6E, actual RetTrue $0F6A) and the three CRC bytes.
The other 18 addresses and every instruction remain unchanged. Labels prevent
future extraction or code-size changes from silently invalidating the table.

`tests/check_coco_conditions.py` assembles the real CoCo module, checks all
19 table entries, runs `FixupEvalTbl`, and executes `EvalExpr` at bases $8000
and $9000 on a 6809. It covers unsigned 0/255 and 127/128 comparisons, both
operand modes, packed flags across byte boundaries, and indirect flag index
255. The native control and full-game tests cover the native return adapter.
The native game is now 21,068 code bytes with unchanged 24,572-byte private
data; the probe interpreter is 6,744 bytes.

### Shared object flag rules

Fourteen object commands now use `objs/shared/object-flag-rules.asm`: fix/
release loop, release priority, ignore/observe horizon, water/land/anything,
ignore/observe objects, stop/start cycling, and ignore/observe blocks. The
catalog defines opcode, field offset, AND/OR masks, and the legacy CoCo
pointer register. `object-commands.asm` emits the mutation instructions,
omitting identity AND/OR operations. Both owners use the same catalog and
body, rather than merely keeping similar constants in separate files.

CoCo selects each catalog entry at its existing handler location. Its original
object lookup and register convention remain intact, and comparison against
the previous module proves the entire binary is unchanged. Native resolves a
bounded record separately and dispatches through immutable table-relative
handler offsets; existing loop/cycling command entry points call those same
handlers. Native success/error conventions are unchanged. No process-private
state or runtime platform dispatch was added.

`tests/check_object_flags.py` executes both real engine binaries for every
rule, object indices 0 and 63, and four bit patterns. It checks the whole
64-record array and guards, preservation of unrelated bits, and native
invalid-index/unsupported-command errors against independent expectations.
Native code is 21,174 bytes (`wbgame`) or 6,850 bytes (`wbexec`), with unchanged
private data. Object positioning, animation progression, motion integration,
resource handling and parser integration still need further consolidation.

The CoCo reference-picture utility now waits 100 ms for queued power-on reset
before debugger memory setup, matching the other CPU harnesses, and uses a
900-second emulated limit. Its former 10-ms/120-second setup disconnected
during the real-picture reference phase on repeated regression runs.

### Shared cycle, motion and rate state

`objs/shared/object-commands.asm` now emits mode 0/3 continuous cycling
and mode 1/2 endpoint cycling for both owners. It changes the mode byte and
enable/single-loop flags with the same instructions. Completion-flag storage
remains an owner adapter (CoCo packed flags, native bytes).

`object-commands.asm` resets the normal motion type and optionally clears
direction for stop-motion. Normal, start and stop commands consume it; ego
direction variables and player/program control state remain owner effects.
`object-commands.asm` writes cycle delay, step size and step delay, resetting
the corresponding countdown where required. Owner-selected accumulator and
record registers preserve each calling convention. No private state or
runtime platform selection is added.

The CoCo interpreter remains byte-for-byte unchanged. Native code is now
21,230 bytes (`wbgame`) or 6,906 bytes (`wbexec`), with the same private data.
The rate extraction itself changes neither binary: the native artifact tested
in `/tmp/sierra-shared-cycle-motion-sustained` matches the final build exactly.

`check_object_flags.py` now also executes these transitions in both real
engine binaries. It verifies whole-array guards, continuous/reverse/endpoint
modes, completion flag 255, ego versus other-object control effects, and
rate/countdown edge values 0/1/127/255 resolved through variable index 255.
Native pixel/motion/animation and real-driver sustained-play checks passed.
Animation progression, coordinate stepping, resource ownership and parser
integration are still separate and require further consolidation.

### Shared said matching and case folding

`objs/shared/said-match.asm` is now the actual matching loop assembled by
both CoCo `TestSaid` and native `ParserSaid`. Script word IDs are read little
endian; parsed dictionary IDs are compared big endian. ID 1 consumes any one
word and ID 9999 accepts the remaining input, advancing over remaining script
operands as in CoCo. Ordinary matches require both lists to end together.
The owners gate input/already-accepted flags and store the acceptance result.
Their existing packed-bit/byte flags and A/B boolean conventions remain intact.

The loop uses owner-provided adjacent remaining-count scratch. CoCo retains
$72/$73; native reuses `vmleft`/`vmright`, which are dead comparison scratch
during this external test. No process-private data is added. The native VM
continues bounding and copying said operands before calling the matcher.

`ascii-lower.asm` supplies both `ToLower` and `ParserLower` with ASCII-only
folding. B/X/Y/U remain unchanged; condition flags are unspecified. The CoCo
module remains byte-for-byte identical. Native game code is now 21,235 bytes
with unchanged 24,572 private bytes; the non-game interpreter is unchanged.

`tests/check_said.py` executes both real engine adapters, including exact and
length/mismatch cases, both wildcards (including ignored trailing operands),
16-bit ID byte order, no-input/already-accepted gates, cursor guards, repeated
acceptance, and exhaustive folding of all 256 byte values. The original typed
parser test covers compressed vocabulary phrases, ignored/unknown words,
editing and path/slab cleanup. Its emulator shutdown now has a bounded kill
fallback when the debugger is already closed and termination stalls.
Dictionary loading/decoding, sentence normalization, input editing and full
parser integration still need further consolidation.

### Removal of the separate Wild Bits source directory

The `sierra/wildbits` directory is removed. Build the Wild Bits game with
`make -C sierra/objs -f wildbits.mk all` from the games repository. Module
entry points are `objs/sierra.asm` with `WILDBITS=1` and the optional diagnostic `tests/probes/wb*.asm` owners;
platform-specific bodies and storage definitions use `objs/platform/wildbits-*`.
The menu construction component is `wildbits-text-ui.asm`, distinct
from the existing modal `wildbits-text-ui.asm`. Host reference exporters
and fixture generators live beside their consumers in `tests`. Port and
emulator documentation is now `WILDBITS-README.md`, `WILDBITS-ENGINE.md` and
`WILDBITS-MAME.md`. Test drivers read assembled products from `objs`. Build the diagnostic executables
with the separate `probes` target; `check` builds both groups.

A forced rebuild produced byte-identical copies of all seven native modules
and the font. The move adds no instructions, state or runtime dispatch.
This removes the separate source/build tree but does not turn native-only
logic into shared behavior: the remaining logic interpreter, resource and
state-layout differences still need reconciliation. Components in `shared`
continue to qualify as shared only when both platform owners assemble them.

Validation for this layout change: all seven native modules and `wbfont`
were byte-identical after a forced rebuild; CoCo `mnln` matched the existing
consolidation baseline. The updated native MAME sustained test passed typed
commands, unknown-word output, inventory, Pause/resume, subsequent input,
interrupt exit and unchanged free memory. CPU tests cover shared commands,
conditions, object state, parsing, rendering, compression, resource ownership
and decoder/reference pixel equality. The host fixture and reference exporter
were also exercised from the new build entry point. Emulator tests now bound
shutdown and use the established idle-ROM startup helper for the viewer.

### Shared sentence and string normalization

Both owners now assemble `objs/shared/tokenize-string.asm`, `find-byte.asm`
and `parser-punctuation.asm`. The tokenizer removes leading delimiters,
collapses adjacent delimiters to one space, discards apostrophes/backticks/
hyphens/double quotes, and removes trailing delimiters. Delimiters and dropped
characters come from one shared pair of immutable byte sets. The algorithm
supports a separate output buffer or in-place normalization without letting
the output cursor overtake unread input.

CoCo supplies its existing PCR output buffer and empty folding/finish macros,
so the entire rebuilt `mnln` binary remains identical. Wild Bits supplies its
private input/output buffer, ASCII folding, and an output-length adapter. Its
previous separate normalization loop and punctuation tables are removed.
No private state or per-frame work was added; native normalization executes
when a sentence is submitted.

`objs/shared/compare-strings.asm` also supplies the existing CoCo `MatchWord`
and `NormWord` algorithms to Wild Bits. This enables native condition 15,
which previously returned an unsupported-service error. Both owners ignore
exactly the comparison punctuation set and compare ASCII case-insensitively;
that set intentionally differs from the sentence delimiter/drop sets. Native
adapters validate both indices against the 12 private 40-byte slots, restore
U, and return the interpreter's B boolean with carry clear. String input must
be NUL-terminated within its slot, as ensured by the native string producers.
Normalization scratch is on the stack, not new process-private allocation.

The native game is 21,409 code bytes out of its 23,808-byte mapping budget,
with unchanged 24,572-byte private data. Tests execute both actual owners at
two code/data locations, check all 255 non-NUL byte classes, buffer guards,
empty/max-length cases, case folding and distinct punctuation semantics.
The condition test also runs loaded message strings through actual native
bytecode argument decoding and IF branches, and rejects indices 12/255.

Validation: both new 6809 regression tests passed; the existing typed-command
parser test passed; the final native MAME sustained acceptance passed original
commands, unknown-word output, inventory, Pause/resume, subsequent input, exit
and unchanged free memory. Artifacts are in `/tmp/sierra-shared-text-mame`.
CoCo `mnln` and all six diagnostic modules remain byte-identical to the
pre-extraction builds. This consolidates text normalization; the remaining
logic execution, resource and object-update differences are still unfinished.

### Shared object coordinate and animation commands

Both owners assemble `objs/shared/object-commands.asm` for commands
37–40 and 147–148. Position assignments write the current coordinate pair and,
for ordinary position commands, its saved pair. Position queries preserve
last-write behavior when both result operands select the same variable.
Relative reposition interprets each variable as a signed byte, clamps negative
sums to zero, and retains the existing byte wrap for positive sums above 255.
Absolute literal/variable reposition uses the same operand-to-coordinate body.

The `platform/sections.d` selector supplies CoCo or Wild
Bits macros for reading their literal/variable operands,
resolving result variables, and saving/adding signed deltas on the stack.
CoCo retains its existing stack locals and streamed operands; Wild Bits retains
its decoded argument array and balanced push/pop delta storage. The shared
macros expand directly into instructions, without runtime platform dispatch.
Placement validation remains an owner boundary: CoCo calls `FindObjPos`;
Wild Bits enters `RepositionPlace` and its bounded collision/terrain search.
The new coordinate regression stops at those real boundaries so it tests the
common arithmetic without implying that the placement algorithms are shared.
Existing gameplay tests cover completed native searches separately.

Command 33 now uses `objs/shared/object-commands.asm`. It preserves
an already animated record; otherwise it sets the initial flags and clears
motion type, cycling mode and direction. CoCo’s entire rebuilt `mnln` remains
byte-identical. Native initialization uses the same zero/store body in place
of three memory clear instructions. Native `wbgame` is 21,415 bytes and
`wbexec` 6,908 bytes; both private-data sizes are unchanged. Reposition and
initialization ownership, error checks and render invalidation remain in the
platform adapters.

The new real-6809 test checks the first and last records, variable indices
0/255, aliased outputs, repeated animation, signed clamp/wrap edges, both
absolute operand forms, stack balance, whole-array guards, native invalid
object indices and immutable code. The broader logic/resource/object-update
reconciliation remains unfinished.

The native execution probe now declares `WILDBITS=1` explicitly, matching
the game owner, so the new assembly-time selector cannot choose CoCo operand
bindings for that probe. The coordinate regression also executes the probe's
position/query/animation handlers to verify that selection, rather than
relying on its normal startup path, which stops before those commands.

Validation: the complete native placement/play and composition regressions
passed, as did the bytecode execution probe. The MAME movement acceptance
measured approximately 9 AGI pixels in 3.33 emulated seconds, matching the
previous benchmark; inventory, modal restoration, exit and unchanged free
memory also passed. Artifacts are in `/tmp/sierra-shared-coordinates-mame`.
CoCo `mnln` and the five unaffected diagnostic modules remain byte-identical.

### Shared short-circuit condition execution

CoCo and Wild Bits now assemble `objs/shared/condition-flow.asm` for the
condition control algorithm. It evaluates AND chains, OR groups and NOT
prefixes in the same order, and consumes the operands of skipped predicates
without calling them. This replaces Wild Bits’ separate eager evaluator.
The difference matters for predicates with side effects: a skipped `said`
match must not mark a submitted sentence as accepted, and a skipped keyboard
predicate must not consume an event.

For example, when the first arm of an OR group is true, a matching `said` in
the remaining arm is now skipped. A subsequent `said` can accept that same
sentence once. The regression failed with an isolated module verified
byte-identical to the previous native binary: `LOOK` had an acceptance count
of zero. The common traversal passes that regression.

`platform/coco-logic-bindings.asm` binds streamed reads, trace-aware
`EvalExpr`, descriptor-based operand skipping, and existing branch labels.
Its validation hooks emit no instructions, so the entire CoCo interpreter
remains byte-identical. `platform/wildbits-logic.asm` binds bounded
mapped reads, decoded operand counts, native callbacks, checked branch offsets
and balanced error exits. It validates OR/NOT controls while skipping, without
invoking skipped predicates. Native errors release the two local bytes before
returning. Four obsolete eager-evaluation bytes are removed from native
private state; condition state now uses the common two-byte stack frame.

The cross-owner test executes both actual control paths at two code locations
with instrumented predicate callbacks. It checks all 16 truth combinations
of mixed AND/OR/NOT groups, exact callback order, said/key skipping, control
bytes inside operands, branch destinations, stack balance and immutable code.
The parser regression separately exercises actual native `said` acceptance.
The native bytecode test checks malformed controls in both evaluated and
short-circuited paths. The remaining main command loop, cache/resource storage
and object-update reconciliation are still unfinished.

The final guarded native build uses 21,557 / 23,808 code bytes and 24,568
private-data bytes (`wbgame`), or 7,050 code / 16,841 private-data bytes
(`wbexec`). The four-byte private-state reduction does not change the number
of OS-9 data blocks allocated. The CoCo build remains byte-identical.

Validation: the full CPU suite passed with the reduced private-state layout.
The final bounded skip-control hooks passed the malformed-input and cross-owner
callback-order tests; the final game/probe builds also passed parser acceptance
and cached/nested execution regressions. MAME sustained gameplay passed typed
commands, unknown-word output, inventory, Pause/resume, subsequent input, exit
and unchanged free memory. The final movement benchmark remained approximately
9 AGI pixels in 3.33 emulated seconds. The two-terminal MAME acceptance passed
every displayed pixel, terminal switches, picture restoration, independent
exit, relaunch and the free-memory map. Final artifacts are in
`/tmp/sierra-final-condition-flow-mame`,
`/tmp/sierra-final-condition-flow-movement`, and
`/tmp/sierra-final-condition-flow-two-terminals`.

### Shared complete logic executor

The obsolete `sierra/wildbits` directory has been removed. Native modules build
from `objs`, platform bindings live in `objs/platform`, and algorithms assembled
by both platforms live in `objs/shared`. This layout does not yet imply that
all command implementations have been reconciled.

Both engines now include `shared/logic-executor.asm` for the complete execution
loop, including return, jump, condition and command decisions. The stream
adapters retain the CoCo page/contiguous-reader conventions and Wild Bits
bounded offset reader, command operand staging, instruction budget and error
statuses. Compile-time macros emit each owner's instructions directly. The
CoCo `mnln` binary is unchanged, preserving its internal offsets and execution
cost. Wild Bits false-condition and unconditional jumps now share one bounds
check instead of maintaining duplicate implementations.

The executor owns a two-byte stack frame for each logic invocation, including
nested calls. Its common return releases that frame on both normal and native
error exits. Helpers still return status to their immediate caller; they must
not unwind the executor frame themselves.

The resulting build uses 21,534 code / 24,568 private-data bytes for `wbgame`
and 7,027 code / 16,841 private-data bytes for `wbexec`. The change removes 23
native code bytes and adds no private data. The direct executor regression runs
both actual owners at two load addresses, compares variable and flag results,
and checks branch behavior, stack balance and code immutability. Native logic,
parser, cached/nested execution and game-rendering regressions also pass.

Real Wild Bits MAME validation of this build also passed sustained commands,
inventory and modal restoration, Pause/resume, interrupt exit and free-memory
checks. Two-terminal tests passed picture restoration, independent exits and
relaunch. Movement remained approximately 9 AGI pixels in 3.33 emulated
seconds. Artifacts are in `/tmp/sierra-shared-executor-mame`,
`/tmp/sierra-shared-executor-terminals` and
`/tmp/sierra-shared-executor-movement`. These checks do not establish complete
gameplay or audio support.

### Shared random command

`shared/random-command.asm` now supplies AGI command 130 to both owners. It
reads the minimum and maximum, computes the inclusive byte-width, selects a
remainder using the existing shared `Div8`, adds the minimum, and stores the
result in the destination variable. A wrapped width of zero represents the
full 0–255 range and bypasses division. This preserves the existing modulo
selection rather than changing the game's random distribution.

The CoCo `InitRandSeed` and native private LFSR remain owner implementations;
sharing range selection does not require identical random sequences. The
native wrapper validates minimum <= maximum before obtaining a random byte.
Both wrappers bind the variable table at assembly time. The CoCo handler keeps
its original bytes and script-cursor advancement; native status return and
private storage remain intact. The native game shrinks a further 15 bytes to
21,519 code bytes, with its 24,568-byte private allocation unchanged.

`tests/check_random_command.py` substitutes only the random-byte provider and
executes each actual handler, including `Div8`. At two load addresses it checks
all 256 input bytes across six ranges, destination variables 0 and 255, full
range and singleton edges, guards, stack balance and code immutability. The
native reversed-range case must fail without changing a variable or calling
the generator. `check_wbplay.py` separately exercises the real generator through
loaded logic and the normal command dispatcher.

The exhaustive comparative test and gameplay regression passed. Sustained
original-game commands, inventory/modal restoration, Pause/resume, interrupt
exit and free-memory checks passed in Wild Bits MAME; artifacts are in
`/tmp/sierra-shared-random-mame`. This does not establish full gameplay or audio
support.

### Shared motion command setup

`shared/object-motion-setup.asm` now supplies the state transitions used by
`follow.ego`, `wander`, `move.obj` and `move.obj.v` in both owners. The existing
CoCo command entry points and native command wrappers expand the same macros
against their object pointer registers; no runtime platform selection is added.

Follow setup records mode 2, chooses the greater of the current step size and
requested follow distance, saves the literal completion flag, clears that flag,
sets the initial $FF follow marker and requests a position update. Wander setup
records mode 1, requests the update and transfers ego input ownership where
applicable. The native adapter retains its existing wander-counter reset;
CoCo retains its existing counter. The reset is an explicit owner policy.

Move setup saves the previous step size before applying a nonzero override,
stores and clears its literal completion flag, requests an update, transfers
ego input ownership, then calls the owner's initial-direction routine. The
variable form dereferences the coordinate and speed operands while retaining
a literal completion-flag index. Native object/coordinate validation still
runs before any record mutation. Target reads, initial direction and subsequent
position/collision updates remain owner routines and need further reconciliation.

`platform/coco-objects-bindings.asm` binds packed flags, fixed input control and the
existing CoCo operand/callback conventions. The native adapter binds private
byte flags and input control, preserves the object pointer while clearing a
flag, selects staged literal/variable speed, and prepares the existing native
direction callback context. Shared includes emit the original CoCo bytes: the
whole `mnln` module remains byte-identical. The native module uses 21,526 code
bytes (seven more than the preceding random-command checkpoint), with private
data unchanged at 24,568 bytes; it remains within the 23,808-byte code limit.

The whole-record regression now checks follow/wander transitions on objects
0 and 63, step/distance edges 0/1/255, completion flags 0/255, neighboring flags,
variable preservation, ego control and native invalid-object rejection.
`tests/check_motion_setup.py` executes both real move handlers at two code
addresses and verifies literal/variable operands, speed preservation/override,
flags, record/argument/stack guards, and native callback context. It substitutes
only the direction callback so setup can be compared independently. The game
regressions execute actual direction, following and motion updates.

These comparative checks and `check_wbgame.py` / `check_wbplay.py` passed on the
final build. Real Wild Bits MAME startup, inventory/modal restoration, movement,
interrupt exit and free-memory checks also passed, with movement unchanged at
approximately 9 AGI pixels in 3.33 emulated seconds. Artifacts are in
`/tmp/sierra-shared-motion-setup-movement`. This checkpoint does not establish
full gameplay, audio support or completion of the remaining source migration.

### Shared inventory rules

`shared/inventory-commands.asm` now supplies all six inventory commands
(`get`, `get.v`, `drop`, `put`, `put.v`, `get.room.v`) and both inventory
predicates (`has`, `obj.in.room`) to CoCo and Wild Bits. Carried objects use
room $FF; dropped objects use room $00. Both put forms read their destination
room from a variable. The variable forms resolve the item through a variable,
while `get.room.v` resolves the item before writing the destination variable,
so aliasing the item and destination variable remains valid. Both predicates
use literal item numbers; `obj.in.room` resolves its expected room variable.

The CoCo adapter binds its three-byte object-file entries, packed resource
layout, original item-pointer helpers and A-valued condition returns. The
native adapter binds its separate private room-byte table, cached bounded
item lookup and B/carry status conventions. Native command dispatch now uses
an immutable relative table for opcodes 92–97; pointer helpers reject item
indices outside the loaded count before any store. Inventory file loading,
name validation/decryption and the modal inventory screen stay in their owner
implementations. Sharing rules does not require changing those storage/I/O
boundaries.

The CoCo module remains byte-identical, including predicate cursor advancement
and command helper branch distances. The native game uses 21,613 code bytes,
87 more than the preceding motion-setup checkpoint, and unchanged 24,568-byte
private data; both stay within the existing limits. No runtime platform
selector, extra private state or mapped resource pointer is introduced.

`tests/check_inventory_commands.py` runs both actual owners at two load
addresses. It covers every command and predicate, items/variable indexes 0 and
255, carried/dropped/ordinary room values, variable-indirect items and rooms,
aliased room queries, CoCo name-byte preservation, native whole-private-state
preservation, argument/cursor/stack guards and native bounds errors. The native
cached loader remains active; the test supplies a validated loaded table.
`check_wbgame.py` separately exercises actual object-file loading, transfers,
queries, predicates, modal selection and scrolling through the interpreter.

The comparative suite and loaded-file gameplay regression passed. The final
build also passed sustained original-game input, inventory/modal restoration,
Pause/resume, interrupt exit and free-memory checks in real Wild Bits MAME.
Two-terminal tests passed pixel restoration, independent exit and relaunch.
Artifacts are in `/tmp/sierra-shared-inventory-rules-mame` and
`/tmp/sierra-shared-inventory-rules-terminals`. These checks do not establish
full gameplay, audio support or completion of the remaining engine migration.

### Shared string-copy and decimal helpers

`shared/bounded-string-copy.asm` supplies the same NUL/limit loop to CoCo
`MemCopyNull` and native `set.string`. CoCo retains its 16-bit stack-local
count and destination return convention; native retains its byte counter and
Y destination. The helper copies up to a positive character limit and then
appends NUL, so truncation requires limit+1 destination bytes. The extraction
alone produced byte-identical CoCo `mnln`, native `wbgame` and native `wbexec`
binaries. No extra instructions or data were added to the copying loop.

The caller regression then exposed an existing CoCo overflow: `set.string`
and `word.to.string` allowed 40 characters in a 40-byte slot, and the copy
helper wrote the trailing NUL at byte 40. This overwrote the next slot, or
variable 0 after the last slot. Both callers now pass 39, reserving the final
byte for NUL as native `set.string` already does. The first real-command
regression failed on a 40-character source before the fix and passed afterward.
The CoCo module differs from its preceding binary at exactly these two count
immediates plus the module CRC; its instruction layout and size are unchanged.
Inputs up to 39 characters retain their resulting string; shorter-than-39
copy paths retain their instruction behavior. Long inputs now remain inside
the selected slot.

`shared/decimal-byte.asm` supplies CoCo `AtoI` and the native modal number
editor. It skips leading ASCII spaces, accumulates unsigned decimal modulo
256, stops at the first nondigit, returns A and preserves U/Y. Two stack-local
bytes hold the accumulator/digit; no global/private scratch is required. The
native editor still filters its input, restores the pending game input and
writes the selected variable. Native `wbgame` adds 32 code bytes to 21,645,
with private data unchanged at 24,568; `wbexec` remains byte-identical at 7,027
code / 16,841 private bytes.

`check_text_helpers.py` executes the actual routines at two code addresses,
checking copy limits 1/2/39/40/127/255 and CoCo 256/257, every nonzero source
byte, termination/truncation, registers, cursors, guards and balanced stacks.
Decimal cases cover values 0–255, overflow, leading spaces, invalid prefixes
and every nondigit byte class. `check_string_slots.py` executes actual CoCo
`set.string`/`word.to.string` and native `set.string`, supplying only the
message-source boundary. It verifies slots 0/11, long and boundary inputs,
adjacent strings/variables, immutable sources/code and native invalid slots.
The game regression also exercises the actual modal editor with blank input,
256/999 overflow, ignored letters and cancellation, writing variable 255.

All comparative helpers, slot-boundary, normalization and extended modal-input
checks passed, as did cached/nested execution. All 14 configured CoCo `mnln`
builds pass. The final native binary matches the MAME-tested artifact in
`/tmp/sierra-shared-text-helpers-mame`, where sustained original-game commands,
inventory/modal restoration, Pause/resume, interrupt exit and unchanged free
memory passed. These checks do not establish full gameplay/audio support or
completion of the remaining source migration.

### Shared cel advancement

`shared/object-animation.asm` now supplies the cel progression routine to
both owners. It handles continuous forward/reverse cycling, forward/reverse
endpoint modes, one-tick suppression, endpoint completion flags, disabling
cycling and stopping direction at completion. `platform/coco-memory-resources-bindings.asm`
binds the existing two scratch bytes, packed flags and `SetCelHelper`;
`platform/wildbits-memory-resources-bindings.asm` binds adjacent process-private `vmleft` /
`vmright` scratch, byte flags and the existing native view-selection callback.
No private allocation is added. Native mode validation and callback B/carry
status are preserved explicitly.

The initial extraction retained the exact CoCo binary. Extending the logical
transition test to unsigned high cel indexes then reproduced a CoCo defect:
reverse mode with cel 254 in a 255-cel loop passed 254 to its callback instead
of 253. The old DECB/BPL sequence treated the decremented byte as signed. Both
owners now use SUBB #1/BCC for the previous index and load the last index only
on unsigned underflow. That one rule supports high indexes without a separate
owner algorithm. The CoCo change adds one byte, retains the instruction count
on the normal reverse step, and leaves relocation to the existing assembler
labels/tables. The full shared-executor regression verifies actual CoCo table
initialization and command/test dispatch at two code bases after the shift.

The native game uses 21,672 code bytes (27 more than the preceding text-helper
checkpoint), with unchanged 24,568-byte private data. Its cycle-rate countdown
and automatic loop selection remain in the owner update wrapper; the common
routine starts at cel advancement. Resource loading, mapped view metadata and
rendering remain view/backend responsibilities.

`check_cel_advance.py` executes the actual common routine in both owners at two
load addresses, substituting only the view-selection callback. It covers all
four modes, first/middle/last cels, counts 1/2/4/128/255, one-tick suppression,
objects 0/63, completion flags 0/255, whole-record/flag preservation, callback
context, stack guards and immutable code. Native invalid-mode and callback-error
cases verify balanced returns and retained B/carry status. The high-count test
proves the logical index transition; it does not establish full CoCo loading
of a 255-cel view. `check_wbgame.py` separately runs actual native view selection,
cel metadata refresh, animation, move-to completion and rendered pixels.

These tests passed, as did all 14 configured CoCo builds. Wild Bits MAME
movement remained approximately 9 AGI pixels in 3.33 emulated seconds, with
startup, inventory/modal restoration, interrupt exit and free-memory checks
passing. Two-terminal tests passed pixel restoration, independent exits and
relaunch. Artifacts are in `/tmp/sierra-shared-cel-advance-movement` and
`/tmp/sierra-shared-cel-advance-terminals`. This checkpoint does not establish
full gameplay/audio support or completion of the remaining engine migration.

### Shared multiply/divide commands

AGI commands 165–168 (`multn`, `multv`, `divn`, `divv`) now assemble from
`objs/shared/math-commands.asm` in both engines. `VARIABLE_TABLE` supplies
the variable-table address, and `MATH_DIVIDE` calls the existing common
`Div8` helper. Multiplication stores the low byte; division stores the
unsigned quotient. The variable forms read the source before writing the
destination, including when both indices designate the same variable.

CoCo retains the original command bodies and short divide calls, producing
identical `mnln` bytes. Wild Bits selects one of those bodies from its decoded
arguments and rejects a zero divisor before entering it. That validation is
an owner policy: this extraction does not change CoCo's existing behavior for
zero divisors. Both successful bodies consume exactly two operand bytes.
The native adapter returns its existing success/error convention separately
from the arithmetic result in the destination variable.

`tests/check_math_commands.py` executes both real owners at two load addresses.
Its 2,478 calls cover every byte dividend, boundary products and quotients,
variable indices 0/255, source/destination aliasing, native zero-divisor
rejection, operand/table/stack guards, and immutable module code. All 14 CoCo
engine builds remain byte-for-byte unchanged. The Wild Bits game now occupies
21,750 of its 23,808 available code bytes, with unchanged 24,568-byte private
storage. This command extraction does not complete the remaining common
startup, resource, rendering, parser, or game-cycle work.

The same native arithmetic build passed the private Wild Bits MAME movement
check and the two-terminal interpreter check. The latter verified every
presented pixel, visibility switching, restored pictures, independent exits,
relaunch, and the free-memory map. Artifacts are under
`/tmp/sierra-shared-math-movement` and `/tmp/sierra-shared-math-terminals`.
These checks do not claim complete gameplay or audio support.

### Shared object view-state queries

AGI commands 49–53 (`last.cel`, `current.cel`, `current.loop`, `current.view`,
`number.of.loops`) now assemble from `objs/shared/object-commands.asm`.
The shared bodies read offsets 15, 14, 10, 5, and 11 of the 43-byte object
record, decrementing the cel count only for `last.cel`, then store the result
in the destination variable. Both owners provide record access and variable
storage through `platform/sections.d`, which selects
`coco-objects-bindings.asm` or
`wildbits-objects-bindings.asm` at assembly time. No hardware access
is added to the common component.

CoCo resolves the script's object operand into U and retains its original
empty-loop behavior. Its generated query bytes are unchanged. Wild Bits
retains `ObjectAddress` validation before entering the common bodies and
rejects an empty loop for `last.cel` before storing a result. Its adapter
supplies the already-resolved record in X, decoded operands, and private
variable storage. The shared bodies consume both operands on success; the
native return convention remains zero B with clear carry, or an explicit
error with set carry.

`tests/check_view_queries.py` exercises these actual owners at two load
addresses, including every byte field value, object/variable boundaries,
zero-count and invalid-object policies, whole-record and native private-state
preservation, argument/stack guards, and immutable code. All 14 CoCo engine
binaries remain unchanged. The current native game is 21,807 of 23,808 code
bytes, with unchanged 24,568-byte private storage.

The complete regression run started for the common-entry checkpoint finished
successfully, including resource loading, decoder equivalence, parser, sprite
damage, dialog/play commands, relocation, mapping boundaries and cleanup.
The separately added arithmetic regression also passed. Those results do not
replace the focused verification of each subsequent common component.

The native view-query build passed sustained original-game commands and
unknown-word handling, menu Pause/resume, graphics restoration and subsequent
input in Wild Bits MAME. The independent two-terminal run passed every
displayed pixel, visibility switching, independent exits, relaunch and the
free-memory map. Artifacts are in `/tmp/sierra-shared-view-query-mame` and
`/tmp/sierra-shared-view-query-terminals`. Full gameplay/audio coverage is
still outside these tests.

The focused view-query regression completed successfully: 5,140 actual
command calls across both owners and two load addresses. Every byte value
was exercised in every queried field, including CoCo's wrapped zero-count
result and the native empty-loop error. Every native call checked the whole
private area for changes outside the result variable and documented record
pointer scratch field. Invalid native object indices left all private state
unchanged. The CPU run and both MAME runs therefore validate this extraction;
they do not prove the remaining engine migration complete.

### Shared game-clock rollover

`objs/shared/game-clock-tick.asm` advances four consecutive byte fields:
seconds, minutes, hours, and days. Both ports use the same increment and
60/60/24 rollover rules, including the original byte wrapping at 255. The
common macro takes the owner's continuation label; it does not read an OS
clock, sleep, change mappings, or decide whether time is paused.

`platform/sections.d` selects matching CoCo/Wild Bits storage
bindings. CoCo supplies its signal-handler `TimeOfDay` address and emits the
original timer bytes unchanged. Its 32-bit timer, pause test, tick counters,
and 20-tick second accumulator remain in the existing owner. Wild Bits
supplies private AGI variables 11–14. Its `F$Time` call, sampled-second delta,
minute wrap, initial sample, modal reset, invalid-second check, and OS-error
handling remain in the native cycle owner. The common body uses X and D as
scratch while preserving U; native clock callers consume its B/carry status
and establish their own subsequent record/context pointers.

`tests/check_game_clock.py` executes the actual CoCo signal-handler core and
native `GameReadClock`, substituting only delivery of the native OS time
sample. All 4,118 calls passed across two load addresses per owner. Coverage
includes every byte value in each clock field, rollover through days, CoCo
32-bit timer carry, pause/subsecond behavior, native single/multiple-second
and minute-wrap deltas, initial/modal-reset samples, unchanged seconds,
invalid OS seconds and OS failure. Full private-state comparisons at boundary
values, surrounding guards, stack/context checks, and immutable module code
also passed. All 14 CoCo setup binaries remain byte-for-byte unchanged. The
native game is 17 bytes smaller: 21,790 of 23,808 code bytes, with unchanged
24,568-byte private storage.

The same clock build passed sustained original-game commands, unknown-word
handling, menu Pause/resume and subsequent input in private Wild Bits MAME.
The two-terminal interpreter run verified all displayed pixels, visibility
switching, restored pictures, independent exits, relaunch and free-memory
recovery. Artifacts are `/tmp/sierra-shared-clock-mame` and
`/tmp/sierra-shared-clock-terminals`; these are bounded runtime checks rather
than complete gameplay/audio acceptance.

### Shared decimal substitution-index scanner

The formatters now use `objs/shared/decimal-index.asm` for decimal indices
following substitutions such as `%v123`. It peeks at the next byte, consumes
only decimal digits, accumulates `value * 10 + digit`, and leaves X at the
first nondigit. It does not skip spaces or interpret the substitution itself.

`platform/sections.d` selects the owner policy. The CoCo
binding preserves modulo-256 arithmetic and the original return flags,
producing identical `mnln` bytes. The native binding keeps the complete
multiply/add result until the overflow check, rejects a value above 255,
and records each accepted value and digit count in existing formatter
scratch fields. A failing digit is consumed but not committed to those
fields. The native formatter still rejects missing indices and unwinds its
source frame on error; this extraction preserves the original byte-sized
digit-count wrapping too. No additional private storage is allocated.

`tests/check_decimal_index.py` passed 3,580 real scanner/formatter calls at
two load addresses per owner. It covers every byte result, every nondigit
terminator, CoCo wrapping versus native overflow rejection, exact source
cursors, leading zeroes, digit-count edges, native variable expansion and
escape errors, frame cleanup, whole-state edge comparisons, source/buffer/
stack guards, and immutable code. The existing `check_wbplay.py` also passed
formatted variables, strings, words, nested messages, dialog restoration,
rejection bounds, and ownership cleanup. All 14 CoCo engine binaries remain
unchanged. The native game is 21,797 of 23,808 code bytes, with unchanged
24,568-byte private storage.

The scanner is a shared component of the formatter, not the complete
formatter. CoCo's word wrapping, global/object message substitutions and
padding, and the native bounded source-frame/output organization still need
reconciliation behind common formatting interfaces.

The same native scanner build passed sustained original-game input and menu
Pause/resume in private Wild Bits MAME. The two-terminal interpreter run
passed every displayed pixel, visibility switching, restored pictures,
independent exits, relaunch and free-memory recovery. Artifacts are
`/tmp/sierra-shared-format-index-mame` and
`/tmp/sierra-shared-format-index-terminals`; complete gameplay/audio support
is not asserted by those bounded checks.

### Shared unsigned decimal conversion for message expansion

`objs/shared/unsigned-decimal.asm` now implements the complete digit-generation
loop used by CoCo `UIntToDecStr` and native `%v` expansion. It divides by ten,
writes remainder digits backward from the caller's buffer end, and repeats
until the quotient is zero. The result is a NUL-terminated string without
leading zeroes, including the single digit `0` for zero input.

`platform/sections.d` selects storage and divider bindings.
CoCo retains its original private engine conversion buffer and 16-bit
`UIntDivide` call, producing unchanged engine bytes and supporting values
through 65535. The native caller supplies a four-byte stack buffer for its
byte-valued AGI variables. Its adapter binds the existing 8-bit divider to
the common quotient/remainder register convention. The caller keeps its
source cursor and private context on the stack and releases all eight local
bytes on both success and output-limit failure. Copied messages, source
frames, decoded arguments and persistent strings are not reused as numeric
scratch storage; no extra private data is allocated.

`tests/check_decimal_output.py` passed 1,560 actual converter/formatter calls
at two load addresses per owner. It covers every byte value, CoCo wide values
through 65535, exact digits and NUL placement, surrounding buffer guards,
register/stack conventions, native copied-message preservation, and a numeric
write failure after string expansion fills the 2047-byte output limit. That
failure verifies stack and source-frame unwinding while the numeric buffer is
live. Whole private-state checks at numeric boundaries and instruction
immutability also passed; CoCo's existing writable conversion buffer is
explicitly excluded from its instruction comparison.

The existing scanner and play regressions also passed: 3,580 scanner/formatter
calls and formatted variables/strings/words/nested messages, rejection bounds,
modal restoration and ownership cleanup. All 14 CoCo engine binaries remain
unchanged. The native game is six bytes smaller than the prior checkpoint:
21,791 of 23,808 code bytes, with unchanged 24,568-byte private storage. Full
format expansion and wrapping remain part of the unfinished engine migration.

The same native conversion build passed the private Wild Bits MAME movement
check (approximately nine AGI pixels in 3.33 emulated seconds) and the
independent two-terminal interpreter check. The latter verified all displayed
pixels, visibility switching, restored pictures, independent exits, relaunch,
and the free-memory map. Artifacts are
`/tmp/sierra-shared-decimal-output-movement` and
`/tmp/sierra-shared-decimal-output-terminals`. These bounded checks preserve
the established movement/terminal behavior; they do not prove complete
formatter, gameplay, or audio coverage.

### Shared formatter character traversal

`shared/formatter.asm` now owns the character loop for both formatters:
end-of-string detection, percent dispatch, ordinary-character output, and
continuation. Assembly-time interfaces in `platform/*-sections.d`
provide source consumption, completion/directive branches, output storage and
line-buffer operands. CoCo peeks before dispatch and consumes during copying;
Wild Bits consumes when reading and calls its existing bounded `FormatPut`.
The CoCo line-tracking trait retains literal-next handling, newline counts,
space wrap points and per-line character counts in the shared loop. These
choices compile directly into the existing instruction sequences.

Verification rebuilt all fourteen CoCo main engines and the native `wbgame`;
every resulting module was byte-identical to its pre-extraction counterpart.
This establishes unchanged executable behavior, code size and instruction
cost for this extraction. Substitution providers, recursive source frames and
wrapping/output helpers still require further consolidation; this does not
claim a complete shared formatter or engine.

### Shared formatter directive selection

`shared/formatter.asm` selects word (`w`), string (`s`), message
(`m`) and variable (`v`) substitutions for both owners. An assembly-time
capability also includes CoCo's global-message (`g`) and object-name (`o`)
branches. Platform macros supply the directive register and existing branch
targets/widths; substitution handlers and their source/storage contracts
remain unchanged. CoCo still skips unknown directives; Wild Bits still
rejects unsupported directives with `E$UnkSvc` after operand validation.
Neither owner gains a runtime table lookup or indirect dispatch.

All fourteen CoCo engine modules rebuilt byte-identically. Wild Bits remains
21,791 code bytes and 24,568 private-data bytes. Its comparison order now
matches the common catalog (word/string/message/variable), changing the number
of comparisons for some substitutions but introducing no new allocations.
The extended index/formatter test passed 4,080 actual calls at two load
addresses, including every unsupported non-NUL directive byte and frame/stack
cleanup. Gameplay regression covered all supported substitutions, nested
messages and malformed expansion. Real MAME sustained commands, unknown-word
response, menu pause/resume, inventory/dialog restoration, interrupt exit and
unchanged free memory also passed. The two-terminal MAME test passed exact
picture restoration, independent exit/relaunch and unchanged free memory.
Full formatting source acquisition,
substitution handlers and recursion remain separate work.

### Shared string-slot provider and NUL traversal

`shared/formatter.asm` resolves a string index into a 40-byte slot
for both formatters. Platform bindings prepare/validate the index, address
the appropriate private string table, and choose expansion. CoCo retains
its existing decimal parser, table at `$0251` and recursive `FormatStr`
expansion. Wild Bits retains the twelve-slot bound, process-relative
`vmstrings` table and literal bounded output. In particular, a percent sign
inside a string slot still has the owner's existing meaning; this extraction
does not silently reconcile that semantic difference.

`shared/nul-string-copy.asm` supplies one traversal macro for CoCo's `StrCopy`
and three native formatter loops: frame copying, literal string-slot output
and numeric output. Its compile-time terminator trait places completion
before writing for checked emitters, and after writing for direct copies.
The latter copies the NUL and leaves the destination one byte beyond it;
the former preserves the existing output terminator managed by `FormatPut`.
Checked emitters provide completion/error branches, retaining their exact
branch widths and numeric stack-frame cleanup. Each expansion reads once,
advances its original source register and preserves the original stop policy.
No call, private buffer or runtime branch was added by the abstraction.

Verification rebuilt all fourteen CoCo engines and native `wbgame`. Every
module is byte-identical to the preceding verified directive-selection
revision, including native source-frame copying and the CoCo string helper.
The preceding CPU formatter/gameplay and MAME sustained/two-terminal results
therefore exercise the identical machine code. Source acquisition, word and
message providers, recursive frame policy and owner-specific expansion
semantics still need further consolidation.

### Shared recursive substitution call and resume

`shared/formatter.asm` invokes recursive formatting after binding
the owner's argument ABI and releases those arguments afterward.
`shared/formatter.asm` applies the result, checks failure when the
owner has an error return, and resumes the outer scan. CoCo's generic
substitution continuation and native message expansion both use this sequence;
CoCo's global-message path also uses the shared invocation before performing
its existing logic-page restoration.

The CoCo adapter supplies the output pointer and source pointer as four
stack bytes, calls `FormatStr`, releases those four bytes and records the
returned output pointer. The native adapter restores U to the private process
context, calls `FormatPart`, and restores the outer X cursor already saved by
the message provider. `FormatExpansionReturn` is also the native reader-error
exit: failed acquisition skips recursion but still pops X and returns the
error through the existing `FormatPartError` path. The result adapter's PULS
X preserves carry, so that error is not overwritten during restoration.
CoCo retains its unchecked recursive convention and existing null-message
skip behavior; the native recursion depth and frame storage remain unchanged.

Both production owners rebuilt byte-identically, as did all fourteen CoCo
engine variants. Consequently the previous CPU nested-message/error checks
and MAME command/dialog/two-terminal checks cover the identical instructions.
There is no new runtime dispatch, code growth or stack allocation. This shares
recursive invocation/result continuation, not message-table acquisition,
source-frame allocation or the full formatter. Those layers and word/message
providers still need consolidation.

### Shared AGI buffer decryption and key

`shared/xor-decrypt.asm` is now the actual in-place XOR implementation for
both CoCo and native object-file loading. The native loader computes the
exclusive end of its already-bounded private object buffer and calls that
same routine instead of maintaining a second counted loop. The helper uses
X as the advancing data pointer, stores the end pointer in two stack bytes,
and cycles an immutable key pointer at its NUL sentinel. It leaves Y/DP
unchanged; the native caller explicitly restores Y to zero, retaining the
old counted-loop result before object validation. The native caller reloads
its process context afterward. Buffer length/table/name validation and
error handling remain unchanged.

`shared/agi-xor-key.asm` supplies the single immutable `Avis Durgan` key and
sentinel for each assembled owner. The native message reader aliases that
same key instead of containing another copy. Message strings still use the
existing checked streaming reader and per-message modulo/key index; this
change does not replace its bounds or decryption phase logic. The key is
included by the message component so the bytecode-only probe, which has no
inventory loader, also builds independently.

All fourteen CoCo engines remain byte-identical. Native game code is five
bytes smaller (21,786 bytes); private data remains 24,568 bytes. The native
decryptor removes per-byte stack-based key-end comparisons. It temporarily
adds the call return address and one two-byte local end pointer, released
before validation; no process-owned storage or writable code is introduced.
The direct CPU test passed 2,108 real helper calls across both owners and
two load addresses, covering lengths 0–256, key-wrap boundaries, 511/512,
1023/1024 and 2047/2048-byte buffers, symmetric encryption/decryption,
empty/reversed spans, guards, stack/register contracts and immutable code/key.
The native engine regression passed real encrypted object files, inventory
transfers/predicates/selection/scrolling, malformed/truncated/oversized object
rejection and complete cleanup. Gameplay regression also passed nested
messages and all supported formatting providers. Real Wild Bits MAME passed
sustained commands, inventory/modal restoration, pause/resume, interrupt exit
and unchanged free memory.

The corresponding two-terminal MAME run also passed every displayed pixel,
restoration, independent exit/relaunch and unchanged free-memory maps.

### Shared blocked-motion state, bulk unanimation and step deltas

`shared/object-commands.asm` owns the object-control mutations used after
blocking checks: clear the crossing bit when allowed, or set it and stop the
object's direction after a crossing. The owner supplies ego identification
and the address of ego's direction variable through
`platform/*-sections.d`. CoCo identifies ego by its first
record pointer; native motion identifies it by record ID zero in private
context. Only a stopped ego clears variable six. The prior block rectangle
classification, ignore/disabled policy and collision sequencing remain at
their existing callers.

`shared/object-commands.asm` owns the complete record traversal for
`unanimate.all`: preserve all control bits except animated/visible, advance
by 43 bytes and continue until the owner boundary is reached. CoCo supplies
an exclusive end pointer and keeps the preceding draw-range cleanup; native
supplies a positive record count, currently 64. The native count interface
requires a nonempty range, as its original loop did; CoCo's end-pointer loop
also accepts an empty range. All other record fields remain untouched.
`shared/object-step-deltas.asm` now provides the actual nine signed X/Y
movement deltas for both engines, under their existing label aliases. Each
owner keeps its arithmetic width and boundary policy.

All fourteen CoCo engines and native `wbgame` rebuilt byte-identically to
the verified shared-XOR revision. Production size, state and instruction cost
therefore remain unchanged. Native probes also build. The focused CPU test
passed 3,086 calls through the real owner routines at two load addresses:
every control byte, allowed/stopped transitions, ego/non-ego direction policy,
unrelated record fields, empty/single/two/64-record bounds, all direction-table
entries, guards, stack/cursor preservation and immutable code. This shares
those motion-state operations and data; stepping arithmetic, terrain/collision
validation and complete per-cycle object orchestration remain separate work.

### Shared object priority/direction setters and field queries

`shared/object-commands.asm` now owns fixed-priority updates and direction
assignment for both owners. Platform operand adapters preserve the original
register/read ordering: CoCo sets the fixed-priority bit before fetching its
literal/variable priority; native validates a preloaded B value, stores it,
then sets that bit. Native still rejects priorities above fifteen and directions
above eight before mutation; CoCo retains its existing unrestricted byte
assignments. Native direction assignment mirrors ego's direction into variable
six, while CoCo keeps its original command policy. Object addressing and
native invalid-index checks remain in their existing entry adapters.

`shared/object-commands.asm` provides the record-to-variable query used
by `get.priority`, `get.dir` and the five existing view queries. The latter
remain a small handler catalog in `object-commands.asm`. All seven queries
now resolve the object/operand, load the field, apply any last-cel adjustment,
address the destination variable, store and return using one implementation.
Native scalar queries no longer use a separate stack-based result-store
helper. Their X/Y scratch results now follow the common query path; the native
executor retains stream/state in private fields and does not rely on those
scratch registers. The existing native view-selection/query component remains
byte-identical (466 bytes), as confirmed against the preceding module.

CoCo code size is unchanged in all fourteen variants. Binary differences are
confined to the two scalar-query instruction sequences and module CRC (17
changed bytes in each build); setters and all other code remain identical.
The reordered CoCo queries retain the same operations and instruction costs.
Native `wbgame` is 21,795 bytes, nine bytes larger, with unchanged 24,568-byte
private data. The focused CPU test passed 7,188 real command calls across both
owners and two load addresses: every priority/direction value and control byte,
first/last objects and variables, native range/index rejection, ego behavior
and variable-six aliasing, unrelated fields/state, guards, stack and immutable
code. Full native engine regression passed rendering, movement/collision,
inventory, malformed resources and cleanup. Real MAME movement remained nine
AGI pixels in 3.33 emulated seconds with startup, inventory/modal restoration,
interrupt exit and unchanged free memory. Two-terminal MAME passed every
picture pixel, restoration, independent exit/relaunch and free-memory maps.
This shares these commands; full placement, view acquisition, collision and
per-cycle orchestration remain further consolidation work.

### Shared placement-search spiral

`shared/object-placement-step.asm` now owns the left/down/right/up spiral
used after a placement candidate is rejected. One leg implementation advances
the coordinate, decrements the remaining count, changes direction, increases
the next run length when needed and resumes candidate validation. It is
expanded four times at assembly time, preserving CoCo's original unrolled
instruction schedule. `platform/*-sections.d` supplies
frame offsets, continuation branches and exhaustion policy.

CoCo's frame contains the object pointer, run length, direction and remaining
count. Native's frame contains direction, run length, remaining count and a
16-bit search budget. Both keep their existing five-byte frame; U points to
the record. Coordinates and counts retain byte wrapping. CoCo retains its
zero-length counter behavior (a subsequent zero countdown gives 256 steps)
and unbounded legacy search. Native retains budget and run-length exhaustion,
restoring the saved coordinates and releasing the frame on either failure.
Candidate bounds, horizon, object collision and terrain/MMU validation remain
in the respective providers. The shared step's direction contract is 0..3,
as established by initialization and every subsequent transition.

All fourteen CoCo production modules rebuilt byte-identically, preserving
instruction costs as well as behavior and size. Native code is 21,846 bytes,
51 bytes larger; process data and stack-frame size are unchanged. Native
continuations and the terrain-error/budget-exit branches use long encodings
where the unrolled body exceeds short-branch range. This introduces no runtime
platform dispatch or allocations. The observed MAME movement remains nine
AGI pixels in 3.33 emulated seconds; that is not a physical-hardware placement
search timing claim.

The focused CPU regression passed 18,434 steps across both owners and two
load addresses. It covers all four directions and every byte coordinate,
run length and remaining count, verifies native run/budget exhaustion and
position restoration, and checks frame/record guards, stack/cursors and
immutable code. CoCo outcomes are also compared with its frozen original
step in `tests/probes/coco-placement-step.asm`; that fixture is test-only and
requires no Git history, so source archives/shallow checkouts work. Gameplay
regression passed signed/absolute reposition and blocked-placement search.
MAME passed real startup, movement, inventory/modal restoration, interrupt
exit and unchanged free memory. The shared executor's actual CoCo dispatch/
relocation regression also passed during this extraction. Full placement
validation and collision acquisition remain further consolidation work.

The final two-terminal MAME run also passed every displayed pixel,
restoration, independent exit/relaunch and unchanged free-memory maps.

### Shared placement geometry validation

`shared/object-bounds.asm` now supplies the actual geometry check used by
CoCo `CheckObjBounds` and native reposition candidate validation. It rejects
right-edge byte overflow and edges beyond 160, baselines beyond row 167,
objects whose height extends above row zero, and baselines at/above the
horizon unless the ignore-horizon bit is set. Platform bindings supply the
horizon comparison and flags scratch register. An explicit zero-width trait
retains native rejection and CoCo's existing allowance; it also preserves the
original load/add instruction ordering. Height zero retains each owner's
existing behavior rather than acquiring a new restriction.

CoCo keeps A as a Boolean result accumulator and uses B for flags; native
uses A for flags and branches directly to its existing accepted/rejected
candidate paths. Neither binding performs hardware access or retains a
mapped resource pointer. These are record/state operations; collision and
terrain/MMU acceptance remain in the original providers.

The focused regression passed 7,500 calls through the real owners at two
load addresses, sweeping every coordinate, size, horizon and control byte
and combinations around screen edges, overflow, height and horizon equality.
It verifies both zero-width policies, all ignore-horizon flag patterns,
unchanged object/private state, guards, stack/registers and immutable code.
All fourteen CoCo engines and native `wbgame` rebuilt byte-identically to the
verified shared-spiral revision, preserving behavior, code/private-data size
and instruction cost. Native probes also build. The preceding placement,
gameplay and MAME movement/two-terminal checks therefore cover the identical
production instructions. Full collision/terrain validation and placement
orchestration remain further consolidation work.

### Shared collision eligibility

`shared/object-collision-filter.asm` now supplies actor ignore-objects checks
and candidate activity/ignore/self filtering for both collision routines.
It requires both animated/visible bits (`$41`), excludes ignored candidates,
and binds self identity through `platform/*-sections.d`.
CoCo preserves its ID comparison after flag checks and B scratch register;
native preserves pointer comparison before flag checks and A scratch register.
The actor's result accumulator and early-ignore behavior remain unchanged.
Candidate iteration, geometric edge rules and baseline-crossing histories
remain separate; this does not claim a shared complete collision algorithm.

The focused regression passed 3,084 calls through the real collision routines
at two load addresses, covering every actor/candidate ignore byte and candidate
control byte, self exclusion and the preserved duplicate-ID/pointer distinction,
record/private-state preservation, scan bounds, guards/stack and immutable code.
All fourteen CoCo engines and native `wbgame` rebuilt byte-identically to the
preceding verified revision. Native probes also build. This extraction changes
source ownership only, preserving size and instruction cost; previous gameplay
and MAME acceptance results cover the identical production instructions.

### Shared dictionary lookup

Both `mnln` and the native game now assemble `shared/dictionary-lookup.asm`.
The former native `ParserCompare`/`ParserCandidate` matching implementation is
removed. A common six-byte stack frame holds the ID, best phrase boundary,
matched-prefix length and comparison byte. Cursor operations are selected at
assembly time; the common algorithm has no hardware or file-service access.

CoCo cursor reads remain direct mapped reads, with the original instruction
sequence. Its case-folding, single-letter defaults and in-place word boundary
termination remain CoCo policies. Wild Bits calls the same lookup with normalized
input and leaves that input intact. Its adapter converts the returned boundary
into the existing private phrase length and word ID; sentence/unknown-word
state still belongs to the native parser.

The native file provider retains full prefix/length/character/ID validation,
including EOF/trailing-zero rules, before using the shared matcher. It locates
the first encoded group with the input's first character, including dictionaries
with zeroed letter indexes. Cached cursor reads preserve X/Y/U and use the
existing 512-byte buffer. Real I/O errors unwind the common frame before reaching
the existing resource cleanup path. No slab is mapped during file I/O. The old
decoded-ID scratch now holds the selected entry offset; only the two-byte cache
base is added to private data.

All fourteen CoCo title modules rebuilt byte-identically. Native game/probe
builds pass: `wbgame` is 22,261 / 23,808 code bytes with 24,570 private bytes,
415 code bytes and two private bytes above the preceding revision. This is a
maintenance consolidation, not a speed improvement: native validation is retained
and the shared matcher adds cursor work. Focused tests cover both production
owners at two addresses, full native parsing/said, dictionaries beyond the
buffer size, malformed files, immutable code/private state and stack/guards.

Wild Bits MAME movement remained approximately nine AGI pixels per 3.33
emulated seconds. Two-terminal pixel restoration, independent exit, relaunch
and free-memory checks passed. The tested module matches the final build.
Artifacts are under `/tmp/sierra-shared-dictionary-movement` and
`/tmp/sierra-shared-dictionary-terminals`. The final-module typed-command check also passed in
`/tmp/sierra-shared-dictionary-command-recheck`. An earlier run with the identical
module did not reach any scheduled screenshots or its exit marker; its cause
has not been established. The fresh repeat, movement and two-terminal runs
passed, alongside the CPU parser regression. These checks do not constitute
a full adventure playthrough or physical-hardware timing measurement.

### One native dictionary validation pass per submitted line

The streaming adapter now validates vocabulary once when the first token of a
line is searched. It records the first encoded offset for each byte-valued group
in a temporary 512-byte table at `fillstack+2048`. Subsequent phrases use these
offsets with the same shared lookup kernel and buffered cursor provider. This
removes the repeated full-file validation scans introduced during integration.
The `parserseen` flag is reset on every `ParserParse`, so offsets never survive
into a new submission or depend on scratch content from a previous game cycle.

The table uses idle formatter-output storage. Parser acquisition first unmaps
asset and picture buffers; its lookup/validation path does not call formatting,
fill decoding, or inventory presentation. The object-name load area ends at
`fillstack+2048`, and the inventory selection list starts at `fillstack+3840`, so
the group table does not overwrite either. Formatting or fill decoding may reuse
this scratch after parsing finishes. Each process owns its own storage.

There is no added private allocation: the native game uses 24,570 private bytes
and 22,294 code bytes. The native CPU parser regression checks partial-read
refills, multi-phrase input, two separate submissions, malformed files and cleanup.
It counts real intercepted dictionary reads and bounds them by one sequential
validation scan plus cursor/header overhead per submitted line. This verifies
reduced repeated file work; it is not a physical-hardware timing measurement.

The final native module also passed the sustained Wild Bits MAME scenario:
repeated original-game commands, unknown-word response, inventory interaction,
real menu Pause/resume, a subsequent command, interrupt exit and unchanged free
memory. Artifacts: `/tmp/sierra-shared-dictionary-onepass-play`. CoCo sources and
the common matching kernel are unchanged by this native adapter optimization.

### Common native move-to direction classification

The separate `MotionMoveDirection` eight-way calculation is removed. Native
per-cycle stepping now calls `shared/object-move-direction.asm` through its
existing `CalcMoveDir` entry. Threshold one classifies each byte-coordinate
difference as negative, zero or positive, preserving native exact-target
selection. The subsequent `MotionTargetClamp` still applies the real step and
prevents overshooting. CoCo stepping and native command setup retain their
existing actual-step threshold policy.

The native wrapper saves/restores X, passes current/target coordinates and the
threshold on the stack, stores the returned direction in object field `$21`,
and preserves U/Y and process data. It adds up to nineteen transient stack bytes
below the entry stack pointer, within the existing runtime stack reserve. This
is not a zero-overhead substitution: it replaces inline classification with a
call to the common algorithm. CoCo's production instructions are unchanged.
The native module shrinks 28 bytes to 22,266, with private size still 24,570.

The focused regression passed 9,280 calls through actual CoCo/native entries
at two code addresses each. It covers every current/target coordinate byte,
unsigned/signed-boundary edge combinations, all nine results (including stopped),
record/context preservation, private state, stack guards and immutable code.

The full native game regression also passed, including repeated move-to cycles,
exact target completion, composition, inventory and cleanup. The gameplay helper
suite passed. Wild Bits MAME ordinary movement remained approximately nine AGI
pixels per 3.33 emulated seconds, with startup/inventory/modal restoration and
unchanged free memory; artifacts are under
`/tmp/sierra-shared-native-direction-movement`. That ordinary movement measurement
does not benchmark the additional call cost of move-to mode. Native game and all
probes build successfully.

### Shared direction-vector coordinate stepping

`shared/object-motion.asm` now computes candidate coordinates in both
`UpdateAllMotion` and `GameUpdateObjects`: zero direction components leave the
axis alone; negative/positive components subtract/add the word-sized step. It
consumes the existing common X/Y direction tables. The owner bindings expose
candidate X/Y and step operands plus direction lookup; CoCo uses its private
stack frame and X table cursor, while native uses private context X and table
cursor Y. No new state or runtime dispatch is allocated.

The store-joining trait preserves CoCo's separate minus-path store and native's
joined stores. All fourteen rebuilt CoCo title modules and native `wbgame` are
byte-identical to the preceding revision, preserving instruction cost, sizes,
register behavior and stack use. Native probes also build. The preceding full
native game regression and MAME checks cover the identical production binary;
no additional emulator run is claimed for this source-only extraction. This
shares vector stepping, not the complete movement pipeline: initialization,
clamping/horizon policy, collision/terrain checks and position commit remain
further consolidation work.

### Shared movement coordinate clamping

`shared/object-motion.asm` replaces the two owner implementations of
left/right/top/bottom and horizon clamping. It reuses the candidate X/Y and step
storage interfaces established for vector stepping. Separate clamp bindings
supply width/height reads, boundary-code storage, horizon operands and native
error branches. The engine still operates in AGI's 160-by-168 logical picture
coordinates; no hardware or OS service is accessed by the shared component.

Four explicit traits preserve existing policies: dimension checks, candidate-
first comparison scheduling, early exits after vertical clamping, and byte-sized
horizon arithmetic. CoCo keeps its signed width arithmetic, early top/bottom
exits and horizon equality behavior. Native keeps its existing width/height
validation points, unsigned right comparison, continued vertical checks and
word-sized horizon-plus-one calculation. Thus this consolidates source ownership
without silently making one owner's behavior match the other's. Legacy entry
labels are retained as aliases for debugging and focused callers.

Native `wbgame` and all fourteen rebuilt CoCo title modules compare byte-identical
to the preceding revision, proving unchanged instructions, timing cost, storage,
register behavior and stack use for this extraction. Native probes also build.
The previously verified full native game and MAME results cover the identical
production binary; no fresh emulator run is claimed. Native remains 22,266 code
bytes and 24,570 private bytes. Target clamping, terrain/object collision,
placement orchestration and final position commit remain further migration work.

### Shared baseline terrain classification and constraints

`shared/object-terrain-scan.asm` now classifies baseline pixels for both the CoCo
`ObjChkControl` path and native `MotionTerrain`. Priority zero blocks, priority
one requires ignore-control, priority two signals, and priority three is water.
`shared/object-terrain-constraints.asm` applies the common water-only and land-only
status bits after scanning. The two owner copies of these rules are removed.

`platform/*-sections.d` supplies pixel reads, width progression,
control/status operands, metadata writes and rejected exits. CoCo reads mapped
packed pixels directly and compares upper-nibble constants; native uses its
picture-pointer provider and decoded priority values. The scan therefore adds
no conversions to the CoCo pixel path. CoCo retains its raw signal value and
water clearing before conditional-control rejection. Native retains its trigger
count and clears water after accepting a conditional-control pixel. The explicit
water-first trait preserves the differing metadata on rejected moves.

Mapping and priority setup, CoCo's priority-15 bypass, native unmapping/error
cleanup and ego flag publication remain owner responsibilities. Those lifecycle
steps are not claimed as consolidated. This extraction reorders branches and is
not byte-identical. KQ1 `shdw` grows from 2,484 to 2,486 bytes; native `wbgame`
grows eight bytes to 22,274 / 23,808, with private size unchanged at 24,570.
There is no runtime dispatch or added state. No CoCo hardware timing benchmark
was performed; native ordinary movement retains its measured MAME rate.

The focused CPU regression passed 3,328 production-owner scan/constraint calls
at two code addresses each. It covers every priority, every control/status byte,
mixed water/trigger/blocked baselines, owner metadata policies, record/private
state, stack guards and immutable code. Only native pixel mapping is substituted;
classification and constraints execute real assembled instructions. The native
full-game regression passed, including water/land/control blocking, composition,
move-to completion, inventory and cleanup. All fourteen CoCo `shdw` title builds
and native probes pass. MAME movement remained approximately nine AGI pixels in
3.33 emulated seconds; two-terminal pixel restoration, independent exit/relaunch
and free-memory checks also passed. Artifacts: `/tmp/sierra-shared-terrain-movement`
and `/tmp/sierra-shared-terrain-terminals`.

### Common complete object collision scan

`shared/object-collision-scan.asm` replaces the bodies of `CheckObjCollision`
and `MotionObjectCollision`. It owns scan sequencing, the existing common
eligibility filters, two-sided horizontal overlap, baseline rules and Boolean
result selection. Their legacy entry/loop/result labels remain aliases.
`platform/*-sections.d` binds candidate/table iteration,
registers, native history storage and A-versus-B return convention. CoCo still
uses its end pointer; native still counts exactly 64 records and retains its
existing early-ignore counter behavior.

Policies remain explicit: CoCo uses byte sums and inclusive touching edges;
native retains the original word comparison sequence and excludes touching
edges. The first native candidate comparison preserves its prior high-byte
handling, while the second clears it. CoCo compares previous record baselines;
native uses its private pre-step actor baseline against the candidate's current
baseline. This extraction centralizes those rules without changing them.

Native `wbgame` and all fourteen rebuilt CoCo `mnln` modules are byte-identical
to the preceding revision, preserving instruction cost, stack/register behavior
and storage. Native probes build. The focused collision regression executes the
legacy entries, with activity/ignore/self filtering, owner identity semantics,
scan limits and guarded records/private state. Previous full-game/MAME checks
cover the identical native binary; no new emulator acceptance run is claimed.
Position commit and per-cycle orchestration remain further migration work.

### Common candidate-position transaction and boundary publication

`shared/object-motion.asm` now supplies candidate writes, collision
result branching, rejected-coordinate restoration, accepted-state transition
and ego/other-object boundary publication for both movement paths. The owner
routine bodies are replaced with one include and legacy entry aliases.
`platform/*-sections.d` binds stack/private coordinate fields,
collision calls/result registers, status and variable writes, terrain lifecycle,
recovery and destination-stage continuations.

The static terrain-prechecked policy preserves ordering. CoCo writes the
candidate, checks object collision, then calls its banked terrain service. It
restores rejected coordinates, clears the boundary code and calls `FindObjPos`
before continuing. Native enters after its terrain check, tests the committed
candidate for collision, restores rejected coordinates and branches to
`MotionBlocked`. Its accepted-state blocked-bit clearing remains before boundary
publication. CoCo's no-boundary path still skips directly to its flag update;
native still proceeds to exact-destination checking. No existing policy is
silently made to match the other owner.

Final native `wbgame` and all fourteen rebuilt CoCo `mnln` modules compare
byte-identically to the preceding revision. Native probes also build. This
proves unchanged instruction cost, register/stack behavior, service call sites
and storage for the extraction. The previously verified native full-game and
MAME results cover the identical binary; no new emulator run is claimed.
Native remains 22,274 code bytes and 24,570 private bytes. Arrival handling,
per-cycle orchestration and the broader resource/rendering migration remain
unfinished.

### Shared target direction and arrival transition

`shared/object-motion.asm` replaces the CoCo `SetObjMotion`/`ObjMoveReached`
and native `MotionMoveDirection`/`MotionArrived` bodies. It owns argument setup
for the common direction classifier, direction storage, the optional zero-result
completion call, saved-step restoration, completion flag/state sequencing and
ego-only completion handling. Legacy entries remain aliases.

Owner operands retain the actual-step CoCo threshold versus native threshold
one, private X context preservation, A/B result handling, packed/byte flag writes
and ego control storage. CoCo sets its completion flag before clearing motion
type and does not add a new record-direction clear. Native clears record direction
and motion before flag publication. Their existing ego-variable/control changes
remain in the same order. Exact-position and boundary-based completion triggers
at the callers are unchanged; those differing orchestration policies are not
claimed as merged.

Native and all fourteen rebuilt CoCo `mnln` modules compare byte-identically to
the preceding revision. Native probes build. The previously verified direction,
full-game move-to completion and MAME checks therefore cover the identical
production instructions; no new emulator acceptance run is claimed. Code,
private allocation, stack use and instruction cost are unchanged. Per-cycle
orchestration, resource/view acquisition, rendering and remaining presentation
behavior still require consolidation.

### Shared per-object animation update

Direction-driven loop selection and cycle countdown now live in
`objs/shared/object-animation.asm`, used by CoCo `mnln.asm` and the
Wild Bits motion owner. Platform bindings retain view acquisition, error
returns, reverse-enable storage and iteration versus subroutine continuation.
The existing loop eligibility and timer reload order differences are explicit
assembly-time policies. All 14 CoCo main-loop modules and the native game are
byte-identical after rebuilding; native remains 22,274 code bytes and 24,570
private-data bytes. Existing emulator evidence therefore applies to identical
production bytes; no new runtime or speed improvement is claimed here.
Outer update traversal, motion scheduling and rendering remain to consolidate.

### Shared motion scheduling and dispatch

Both owners now include `objs/shared/object-motion.asm` for the
active-object gate and all four motion-mode dispatch paths. The platform
interface supplies step scheduling, follow context restoration, unknown-mode
handling and move-to entry names. This preserves CoCo's separate direction
pass and Wild Bits' per-object animation/countdown pass; combining the outer
loops would otherwise change when objects observe each other's state.
All 14 CoCo `mnln` modules, native Wild Bits and the probes build. Production
main-loop/game bytes match the preceding revision exactly, with no additional
code, private data or runtime dispatch. Existing emulator verification covers
those identical bytes; this change adds shared ownership, not new gameplay.

### Consolidated component files

Replaced 41 formatter/motion/animation fragments with 12 files: one shared
component, one platform selector/interface and one binding file per platform
for each feature. Named assembly-time expansion macros preserve the existing
code placement without wrappers or additional runtime dispatch. Removed the
old fragments and updated assembly includes, dependencies and documentation.
All 14 CoCo main-loop modules and native Wild Bits remain byte-identical;
native/probe builds pass. This is a source-layout change with no additional
runtime storage. Other independently maintained components remain separate.

### Platform feature consolidation

Reduced `objs/platform` from 208 to 34 assembly files. Related code and private
state now occupy feature files for memory/resources, graphics, input, text/UI,
audio, timing, logic and objects. Macro-only interfaces are grouped into
feature binding files, loaded once per assembly. Removed redundant selector
files; their compile-time backend branches remain at owner expansion sites.

`platform/sections.d` names the code/data layout sections. Owners select each
section at its original location, so private offsets, module layout, branch
encodings and runtime instructions are preserved. Conditional chains select
one section even when it includes another feature section. Macro-bearing
native implementations remain separate where they already form substantial
components; assembler macro definitions cannot be safely placed in skipped
layout sections. See `objs/platform/README.md` for the current feature map.

Rebuilt four CoCo modules for every one of the 14 titles and compared all 56
modules byte for byte with the pre-consolidation files. Native `wbgame` is also
byte-identical; all native probes build. No new emulator run is claimed for
this source-layout change. Runtime behavior and performance are unchanged.

### Completed platform grouping and object command component

Moved the eight remaining native implementation bodies into their feature
files after extracting local macro definitions into the existing feature
binding files. This resolves the assembler conditional-section limitation
without retaining per-operation implementation files. Timing bindings now
reside in the timing feature files. Platform assembly count is 26, down from
208 before consolidation; `wildbits-runtime.asm` remains the module owner.

Eleven shared object command/state/query fragments now form
`shared/object-commands.asm`, loaded once with a caller-side definition guard.
The view query handler body has a named expansion macro so its original
placement is retained. The component defines no new state or runtime wrapper.
Native/probe builds pass, native game bytes are unchanged, and all 56 CoCo
engine modules match the pre-consolidation versions. Resource/view loading
behavior and rendering remain owner-specific work; this stage consolidates
source organization and does not claim new shared resource algorithms.

### Shared view table traversal

Loop/cel table traversal now expands from the existing object component in
both CoCo metadata helpers and native `ViewSelect`. Owner bindings preserve
CoCo mapped little-endian reads with byte-index arithmetic and native bounded
16-bit logical offsets. Native I/O error unwinding, table bounds, and cel
relative offset checks remain intact. This adds no source files or runtime
calls: all 14 CoCo main-loop modules and native game bytes remain identical;
all probes build. Cache allocation, loading, ownership and discard behavior
remain separate because CoCo maintains a linked view list and native uses
32 typed cache slots with slab ownership.

### Resource lifetime audit and discard error correction

The two caches have different allocation contracts. CoCo's view nodes occupy
an ordered, stack-like heap: discard rewinds the data-block pointer to the
selected node and the asset pointer to its mapped allocation boundary, then
ends the predecessor link. Consequently the selected view and later views
are removed as a suffix. Native has 32 typed cache slots, each with explicit
slab ownership: discard removes only the matching kind/id and restores the
executing logic's asset context after success. An absent native resource is
already discarded. These policies must remain separate behind any future
shared cache orchestration; changing CoCo unlinking alone would retain links
into reclaimed allocations.

`check_resource_lifetime.py` executes actual owner discard routines at two
load addresses. It checks CoCo first/middle/last suffix rewinds and page
restoration, native typed matching, absent discard, failed release retention
and successful retry, cache ownership, stack guards and allowed module-data
writes. Only replay/render/mapping boundaries and native asset service calls
are mocked. It does not execute the mapped CoCo allocator or OS slab service.

The test exposed a native error-path defect: `VmDiscardFailed` cleared
`assetowned` to retain ownership solely in the cache slot, but 6809 `CLR` also
clears carry. Added `ORCC #1` before returning so callers see the release error
in B with carry set. The cache slot remains owned and can be retried. This
adds two code bytes (native game 22,276; private data unchanged at 24,570).
The direct CPU regression passes 18 calls, including failure then retry;
CoCo executable code is unchanged by the correction.

The native interpreter integration suite also passes after the carry fix:
picture/view composition, transparent/mirrored/clipped/occluded/erased sprites,
text and repeated cycles, controllers, clock rollover, motion completion,
end-of-loop animation, parser input, inventory and cleanup. Fresh MAME acceptance was completed after rebuilding the fork and temporary
boot image; the installed stock emulator does not provide `wbjr2`.

Fresh MAME checks on 2026-10-06 passed with the corrected 22,276-byte game:
movement (nine AGI pixels over 200 frames), real-resource startup, inventory,
modal restoration, interrupt exit and unchanged memory; then every-pixel
restoration on two terminals, independent exit, relaunch and free-memory maps.
Artifacts are `/tmp/sierra-view-cache-error-movement-verified` and
`/tmp/sierra-view-cache-error-terminals`. The emulator/OS revisions match the
previous acceptance (`078e0eeb` / `c45760ab`); host SDL/SDK configuration was
rebuilt as documented in `WILDBITS-MAME.md`. This does not establish physical
hardware timing or complete adventure/audio compatibility.

### Shared sprite visibility and native ego-hidden correction

CoCo's cel renderer records whether it wrote any pixel and publishes the
result as AGI flag 1 for ego. Native rendering previously left that flag
unchanged. Both now expand the same visibility macros in the existing shared
object command component, with owner bindings for storage and flag layout.
Native marks actual composed-buffer writes in its ordinary priority and
control-pixel paths; transparent and occluded pixels leave the draw hidden.
It publishes only after a completed ego cel, never for a non-ego. An errored
render takes the existing cleanup path without publishing its partial result.
The rule preserves CoCo's per-cel semantics; it does not rescan the completed
scene for overlap from objects drawn later.

All 14 CoCo sprite modules are byte-identical. Native integration tests check
pixels and flag 1 for visible, background-hidden, fully transparent and
mirrored/clipped cels, with a visible non-ego unable to overwrite hidden ego
state. Native now uses 22,322 code bytes and 24,571 private bytes. Fresh MAME
movement and two-terminal acceptance passed with this build on 2026-10-06;
artifacts are `/tmp/sierra-shared-sprite-visibility-movement` and
`/tmp/sierra-shared-sprite-visibility-terminals`.

### Shared selected-cel position reconciliation

CoCo adjusts an object's position when a selected cel extends past the right
edge or above the picture. It sets object clip-state bit `$04`; the height
adjustment also respects the ignore-horizon flag. Native selection previously
updated dimensions without this reconciliation. `OBJECT_CEL_CLIP` in the
existing shared object component now supplies that rule to both owners.
Native runs it after successful metadata validation for view, loop or cel
selection and catches carry from X+width; CoCo's original byte-add behavior
and instruction stream remain unchanged. The horizon adjustment is performed
when the height forces a Y adjustment, preserving CoCo's rule. This does not
replace the separate motion/position bounds checks.

`check_cel_clipping.py` directly executes the production routines at two load
addresses, with 5,920 cases across all coordinate/horizon/flag bytes and legal
cel dimensions. It verifies right-add overflow policy, clip-bit preservation,
unrelated object fields, private state, code and stack/register guards. All
14 CoCo main-loop modules remain byte-identical. Native adds 57 code bytes and
no additional private storage. The visibility scratch now aliases the dead
sprite insertion key during rendering, restoring the preceding private size
(22,379 code; 24,570 private). Fresh movement and
two-terminal MAME acceptance passed with this build; artifacts are
`/tmp/sierra-shared-cel-clipping-movement` and
`/tmp/sierra-shared-cel-clipping-terminals` before scratch reuse. The final
layout also passed both checks, with artifacts at
`/tmp/sierra-shared-cel-clipping-scratch-movement` and
`/tmp/sierra-shared-cel-clipping-scratch-terminals`.
