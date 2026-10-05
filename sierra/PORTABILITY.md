# Sierra platform separation


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
"next" boundary describe the stage when that section was written. The final
section records the completed boundary inventory and current validation.

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

## Screen setup, presentation, and restoration

The screen lifecycle and CoCo palette operations are now selected through
these backend includes, at their original code/data locations:

| Selector under `objs/platform/` | Entry points/data | Responsibility |
| --- | --- | --- |
| `screen-colors.asm` | `ColorTable` | Startup composite/RGB palettes using CoCo color codes. |
| `monitor-select.asm` | `ConfigureMonitor` | Read the monitor preference, apply `-r`, and store the game's display type without changing the global monitor mode. |
| `screen-setup.asm` | `SetupScreen` | Allocate, record, clear, display, and initialize the instance's screen and palette. |
| `terminal-options.asm` | `DisableKbdInt` | Exchange saved echo/EOF/interrupt/quit options with the input path's options packet. |
| `screen-restore.asm` | `RestoreScreen` | Restore options, reset the palette, select text screen zero, and free the recorded graphics screen. |
| `game-palette-data.asm` | `PaletteData` | Interpreter composite/RGB palettes, separate from the startup table. |
| `game-palette-set.asm` | `cmd_toggle_monitor` | Toggle the game's palette selection and write the sixteen palette commands. |

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
| `render-spans.asm` | `CocoViewPal`, screen clears, rectangle/border fills, picture-strip drawing, and screen-strip copying. |
| `render-view.asm` | `DrawView` and its clipped view/cel drawing loops. |
| `render-glyphs.asm` | `DrawSprites`, the existing software 8-by-8 glyph renderer. |
| `text-packing.asm` | `text_color`, which converts foreground/background indices into repeated-nibble bytes. |

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
| `joystick-input.asm` | `ReadJoystick`/`ReadJoyButton`: standard-input `SS.Joy` sampling, existing result layout and button field, Y preserved. |
| `keyboard-input.asm` | `ReadStdinByte`: availability check followed by one-byte read; A returns the byte or zero on unavailable/error, Y preserved. |
| `timer-intercept.asm` | Signal `$80`, direct-page setup from intercepted U, divide-by-three countdown, and dispatch to the shared clock update. |
| `service-check.asm` | Matching terminal names and CoCo ownership-aware screen-service version check before startup changes state. |
| `presentation.asm` | Existing nibble-swap mode followed by full-picture strip dispatch; preserves the save/UI behavior. |
| `priority-address.asm` | Legacy priority-pointer coordinate conversions (`CalcPriAddr`, `CalcPriCoord`). |
| `picture-storage.asm` | Combined-buffer fill, plotting, line drawing, and flood-fill loops using the legacy fixed window. |
| `picture-orientation.asm` | In-place combined-byte nibble swapping. |
| `object-storage.asm` | Priority/control contact checks, cel composition/mirroring, background save/restore, and related fixed-buffer operations. |
| `sound-elapsed.asm` | CoCo elapsed-time compensation after synchronous interrupt-masked sound, including page restoration. |

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

Native resource loading now exists as `objs/platform/wildbits-resource-code.asm`, exercised
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
bounded stream handling in `objs/platform/wildbits-decoder-code.asm` remain owner adapters;
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
are storage interfaces implemented in `platform/coco-flag-storage.asm` and
`platform/wildbits-flag-storage.asm`. CoCo retains packed flags and the native
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
pointer register. `object-flag-mask.asm` emits the mutation instructions,
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

`objs/shared/object-cycle-state.asm` now emits mode 0/3 continuous cycling
and mode 1/2 endpoint cycling for both owners. It changes the mode byte and
enable/single-loop flags with the same instructions. Completion-flag storage
remains an owner adapter (CoCo packed flags, native bytes).

`object-motion-state.asm` resets the normal motion type and optionally clears
direction for stop-motion. Normal, start and stop commands consume it; ego
direction variables and player/program control state remain owner effects.
`object-rate-state.asm` writes cycle delay, step size and step delay, resetting
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
The menu construction component is `wildbits-menu-build-code.asm`, distinct
from the existing modal `wildbits-menu-code.asm`. Host reference exporters
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

Both owners assemble `objs/shared/object-coordinate-state.asm` for commands
37–40 and 147–148. Position assignments write the current coordinate pair and,
for ordinary position commands, its saved pair. Position queries preserve
last-write behavior when both result operands select the same variable.
Relative reposition interprets each variable as a signed byte, clamps negative
sums to zero, and retains the existing byte wrap for positive sums above 255.
Absolute literal/variable reposition uses the same operand-to-coordinate body.

The `platform/object-coordinate-operands.asm` selector supplies CoCo or Wild
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

Command 33 now uses `objs/shared/object-animation-state.asm`. It preserves
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

`platform/coco-condition-stream.asm` binds streamed reads, trace-aware
`EvalExpr`, descriptor-based operand skipping, and existing branch labels.
Its validation hooks emit no instructions, so the entire CoCo interpreter
remains byte-identical. `platform/wildbits-condition-stream.asm` binds bounded
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

`platform/coco-motion-setup.asm` binds packed flags, fixed input control and the
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

`shared/object-cel-advance.asm` now supplies the cel progression routine to
both owners. It handles continuous forward/reverse cycling, forward/reverse
endpoint modes, one-tick suppression, endpoint completion flags, disabling
cycling and stopping direction at completion. `platform/coco-cel-advance.asm`
binds the existing two scratch bytes, packed flags and `SetCelHelper`;
`platform/wildbits-cel-advance.asm` binds adjacent process-private `vmleft` /
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
`number.of.loops`) now assemble from `objs/shared/object-view-queries.asm`.
The shared bodies read offsets 15, 14, 10, 5, and 11 of the 43-byte object
record, decrementing the cel count only for `last.cel`, then store the result
in the destination variable. Both owners provide record access and variable
storage through `platform/object-view-query-operands.asm`, which selects
`coco-object-view-query-operands.asm` or
`wildbits-object-view-query-operands.asm` at assembly time. No hardware access
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

`platform/game-clock-operands.asm` selects matching CoCo/Wild Bits storage
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
