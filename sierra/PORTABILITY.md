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
