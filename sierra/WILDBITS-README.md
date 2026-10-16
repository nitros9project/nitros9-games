# Wild Bits Sierra port

See the [Wild Bits / CoCo 3 parity checklist](WILDBITS-PARITY.md) for verified
evidence, remaining work, and the acceptance criteria for completion.

`wbgame` is the native 6809/NitrOS-9 game owner. King's Quest I now accepts
typed commands, displays responses, moves the player between rooms, and opens
inventory and menus. Its platform code and state are grouped by feature in
`objs/platform/wildbits-*.asm`; common motion, object, formatter and decoder
algorithms live in `objs/shared`. See
[the platform layout](objs/platform/README.md) for the feature map. The older `objs/wildbits_engine.asm` scaffold is not built.

Build with `make -C sierra/objs -f wildbits.mk all` from the games repository. Install
`wbgame`, `wbfont`, and the matching `wbui` and `wbstate` auxiliary helpers in the OS-9
execution directory, with read/execute access. The current private helper ABI
is version 10; install all three executable modules together when upgrading.
Keep the original game resources together in a readable directory, then run:

```text
wbgame /s0/game 0
```

Press an arrow to move and press the same arrow again to stop. Type a command and press ENTER. `look room` requests
the castle description. CTRL-I opens inventory on the tested Wild Bits keyboard;
Escape/Break opens the menu. ENTER selects; Escape/Break cancels. CTRL-C exits.
The terminal's echo, EOF and quit settings are restored on exit.

The game's Save and Restore commands ask for a filename (for example,
`/s0/my-save`). Save creates a new file; choose a new name for each save rather
than overwriting an existing file. Restore checks the complete file before
replacing game resources. Files belong to this native port and must match the
current game's ID. The `wbstate` helper supplies save/restore code, copied into the caller's private workspace for each state operation. The `wbui` helper supplies
immutable text/UI code and the private audio adapter. It is required for text
output. Its first text request retains a shared code mapping until exit; normal
movement does not reload it. Install both helpers from the same build as `wbgame`. A pictured snapshot needs
five temporary 8 KiB blocks during validation, so available OS-9 memory matters
when several games are running. A read/validation error leaves the game running;
a resource reconstruction failure exits through cleanup.

This is an **interactive early build**, not a complete AGI compatibility claim.
Owned queued audio is available with version 4 of `PSGdrv`; the standard
older driver falls back to silent completion. Install the matching driver and
`fPSG` descriptor in OS9Boot. Later-game commands, complete sound compatibility
and further timing improvements remain.
Do not infer that the entire adventure can be completed from the tested route.
See [MAME.md](WILDBITS-MAME.md) for exact driver tests and [ENGINE.md](WILDBITS-ENGINE.md) for
ownership, buffer aliases and shared-source boundaries.

## Target and interfaces

The target is **independent games on separate terminals**. Each viewer owns
its bitmap and private process data, uses standard output for graphics and
standard input for keyboard/visibility notifications, and requires both paths
to identify the same terminal. An already-defined bitmap zero is an error;
the viewer does not adopt, overwrite, or free that bitmap.

A current Wild Bits terminal/graphics driver must provide:

- `SS.AScrn`, `SS.FScrn`, `SS.Palet`, `SS.PScrn`/layer selection,
  `SS.DScrn`/master-control selection, and `SS.DevNm`.
- `SS.BmBlk` (`$E4`): GetStat with Y=bitmap zero returns its first block in X.
- `SS.ClutWrite` (`$CF`): SetStat with X=BGRA entries, Y=CLUT/first entry,
  U=count. The viewer supplies seventeen entries in CLUT zero.
- `SS.WSig` (`$E1`): SetStat on standard input with X=`$8182` registers
  background/foreground signals; X=0 deregisters them.
- Per-terminal bitmap, layer, and CLUT preservation on terminal switching.

These conventions follow the [Wild Bits porting guide](https://github.com/jfed6000/f256_porting)
and the published [Joust graphics](https://github.com/jfed6000/JoustF256/blob/main/src/gfx.a)
and [platform backend](https://github.com/jfed6000/JoustF256/blob/main/src/platform.a).
The viewer requires visibility registration to succeed; it does not silently
continue with a driver lacking multi-terminal notification support. Start it
from the visible terminal. Initial visibility and graphics restoration still
need validation on physical hardware; MAME checks below cover the specified
emulator/driver versions.

## Build and run

From the games repository directory, with lwasm on PATH:

```sh
make -C sierra/objs -f wildbits.mk NITROS9DIR=/path/to/nitros9
make -C sierra/objs -f wildbits.mk fixture
```

Copy the resulting OS-9 module `wbpic` to the target's executable directory
and `test-picture.bin` to a data directory using the usual OS-9 file-transfer
and executable-attribute procedure. On the target:

```text
wbpic test-picture.bin
```

Any input byte exits. CTRL-C/BREAK signals are intercepted as cancellation;
non-interceptable kill remains subject to normal OS-9 process cleanup.

The input is exactly **26,880 raw bytes**, row-major, 160 by 168:

- Low nibble: logical color index 0..15.
- High nibble: priority/control data; presentation leaves it unchanged.
- No module header, picture-resource compression, or file-format header.

The generated fixture is diagnostic color bars with varying priority, not an
AGI game resource or a picture decoded from a game. An engine-buffer export
must be in the normal low-color/high-priority orientation. The viewer does
not load `picDir`/`vol.*` or implement AGI picture commands yet.

## Presentation and memory

Each logical pixel is duplicated horizontally into a 320-by-240, one-byte
bitmap. The first 168 rows contain the picture; the remaining rows are opaque
black. Logical colors become indices 1..16, reserving transparent index zero.
The palette uses the conventional sixteen-color RGB values in BGRA order.

The module requests one 8 KB private data area, including row staging and
stack. It retains only **one 8 KB service mapping** at a time. Bitmap storage
is allocated by the graphics driver; no direct MMU or VICKY register access
occurs. Mapping always uses the address returned by `F$MapBlk`, and `F$ClrBlk`
receives that original base. Spans split at an 8 KB boundary even when a
320-byte row crosses it. The module-size budget target uses the conservative
40,192-byte budget intended for the eventual two-window interpreter.

The signal handler writes only private flags through intercepted U and does
not assume the interrupted DP. Hidden instances wait using `F$Sleep` before
continuing block/row work or presentation. Visibility registration is released
during cleanup. Background cleanup still uses the terminal driver: its
per-terminal shadowing contract is essential to avoid altering the visible
terminal. The CPU tests cannot establish that driver behavior; the MAME test
below exercises the actual driver during ordinary switching and foreground exit.

The viewer balances the opened input file, bitmap ownership, and mapping
lifetime on the tested success/error paths. It restores text mode on its own
terminal and frees only its allocated bitmap. It is a viewer lifecycle, not
yet a generalized restoration of arbitrary previous graphics applications.
Persistent driver cleanup failures and forced kill have not been validated on
hardware; these remain runtime validation work.

## Checks and hardware acceptance

```sh
make -C sierra/objs -f wildbits.mk check
```

This requires XRoar with its GDB interface. The test executes the actual
assembled 6809 module with mocked OS-9/graphics calls. It checks:

- Every output pixel and the untouched black region, with varied priority bits.
- Short input reads and spans crossing mapping boundaries.
- Different code/data locations and OS-returned mapping-window addresses.
- Truncated/oversized input, allocation refusal, mapping failure, and a
  transient unmap failure followed by cleanup.
- Terminal name matching, background waiting, registration release, and
  refusal to free an existing bitmap.

`make -C sierra/objs -f wildbits.mk check` is CPU/service-contract testing. The separate MAME check below
uses the real Wild Bits OS and drivers. For physical hardware acceptance,
launch the viewer on two separate
terminals, switch between them during loading and while displayed, verify each
palette/picture returns correctly, quit one, and verify the other remains
intact. Repeat both launches and check free RAM and bitmap availability.
Also test mismatch/redirection, missing services, signal cancellation while
hidden, and the actual keyboard behavior on the target.

## Wild Bits MAME checks

The real-driver `wbjr2` MAME test passed with two viewers on `/term` and `/vt1`:
every displayed pixel, restoration after switching, independent exit,
relaunch, and an unchanged free-memory map after two launch/quit cycles.
Both diagnostic buffers and the King's Quest I reference were exercised.
See [MAME.md](WILDBITS-MAME.md) for setup, the repeatable test command, exact revisions,
and remaining hardware acceptance work.

## Native resource loader

`make` now also builds `wbres`, a small native resource-loading probe. On
Wild Bits, with an existing game directory containing `picDir` and `vol.N`:

```text
wbres /s0/kingsquest1 1 >/s0/picture-1.cmd
```

Its binary output is **AGI picture commands**, not the combined pixels accepted
by `wbpic`. It reads a three-byte directory entry, constructs the decimal
volume filename (including `vol.10` through `vol.15`), seeks to the 20-bit
resource offset through `I$Seek`, checks the seven-byte CoCo resource header,
and reads exactly the stored resource size. It validates the volume number,
nonzero size, an 8 KB command limit, equal decoded/stored lengths, and final
`$FF` marker before emitting anything. Packed and LZW resources are explicitly
rejected. Short reads/writes retain progress; failures close opened inputs.
The shell may create an empty redirected output file when validation fails.

The loader lives in `objs/platform/wildbits-memory-resources.asm`, with private fields declared by
`objs/platform/wildbits-memory-resources.asm`; the probe owns the sole module header. `LoadPicture`
takes X=game directory, Y=picture number, U=private data base and matching DP.
It returns X=command buffer and Y=length, or carry/B indicating an error.
Its mutable fields, path strings and command bytes are process-private.
There are no hardware accesses, fixed load addresses or writable code.

The probe is 728 bytes with 8,907 bytes of requested private data, including
the full 8 KB command buffer and stack. The OS rounds this data allocation to
two 8 KB blocks. This is a test arrangement: the eventual interpreter should
put large resources behind bounded mapping windows to retain its 8 KB state
budget. It must not simply add this resident buffer to the packed engine.

`make -C sierra/objs -f wildbits.mk check` runs actual 6809 tests for relocation, short reads/writes,
directory/header failures, large offsets and boundary sizes. The separate
real-driver MAME test is described in [MAME.md](WILDBITS-MAME.md). Native MAME reads
matched both an 8 KB diagnostic resource from `vol.15` at `$23456` and all
2,752 bytes of King's Quest I picture 1 at `vol.1` offset `$E24A`.

## Native mapped picture decoder

`wbdecode` includes the same native resource loader as `wbres`, then decodes
picture commands into a 26,880-byte color/priority buffer. From an interactive
Wild Bits terminal:

```text
wbdecode /s0/diagnostic-game 1 >/s0/combined.bin
wbpic /s0/combined.bin
```

When invoking it from a shell script, give it terminal input explicitly:
`wbdecode /s0/diagnostic-game 1 </term >/s0/combined.bin`. Use the appropriate
`/vtN` for another terminal. The program uses its own stdin path for graphics
allocation and checks that it is an SCF device before allocation. A startup
script's disk-file stdin is rejected: RBF SetStt codes are not graphics calls.
It does not define a bitmap or change a terminal's palette or display layers.

Commands `$F0` through `$FA` and the `$FF` terminator are supported: color and
priority controls, corner/absolute/relative lines, flood fill, and solid/splatter circle/rectangle pens. Unknown commands
are rejected before buffer output begins.
Incomplete coordinates, invalid colors and bytes after the terminator also
fail. King’s Quest I picture 1 now decodes natively with the exact CoCo reference
buffer. This is still a decoder probe, not a playable interpreter.

`objs/platform/wildbits-graphics.asm` allocates four consecutive physical blocks through
`SS.GfxAlloc` and maps one block at a time through `F$MapBlk`. The current page
is cached. `PicturePointer` accepts a logical byte offset and returns a pointer
valid only until another mapping call; clients never retain it across pages.
The line and plot routines use this boundary, including lines crossing an
8 KB page. All four blocks are initialized; only the 26,880 picture bytes
are exported. A private 512-byte staging buffer lets output unmap before
`I$Write`, including partial writes.

`objs/platform/wildbits-graphics.asm` uses scanline flood fill with a private 4,096-byte stack
of 2,048 coordinate seeds. It paints a horizontal span and queues neighboring
runs. Exhaustion returns `E$MemFul` instead of overwriting another buffer.
It matches white color when color drawing is enabled, otherwise default
priority 4 when only priority drawing is enabled, preserving CoCo semantics.
The CPU stack stays in normal private process storage.

The module is 2,507 bytes and requests 14,076 bytes of process data (two 8 KB
blocks), plus four owned picture blocks. Reserving one mapping window and
the kernel block leaves a conservative 32,000-byte code budget. The command buffer
and bounded fill stack remain private resident data; this is still a probe
layout, not the completed interpreter's memory budget. Dispatch offsets and
code are immutable. No application hardware-register access is used.

Normal success and error exits unmap and explicitly free the picture blocks.
Abort/interrupt signals request a controlled error exit; cleanup retries once
on failure and preserves the original error. The driver does not reclaim
program-owned slabs automatically. Forced termination or persistent cleanup
failure can therefore leave an allocation behind; an eventual interpreter
needs to account for that ownership limit. Output errors can leave a partial
file, so only use a successful decode as viewer input.

Differential CPU checks cover the complete CoCo reference buffer, two native
code/data locations, different window addresses, malformed input, service
errors, immutable code and the fill-stack boundary. The MAME diagnostic runs
on `/term` and `/vt1`, compares both outputs and requires an unchanged
free-memory map. See [MAME.md](WILDBITS-MAME.md) for reproduction.

Pen commands, direct native presentation, compressed-resource storage and the
interpreter core now exist. Game command integration remains. Performance optimization
of mapped spans and fill remains to be measured; correctness does not prove
performance parity with the original CoCo routines.

## Integrated native resource presentation

`wbrun` loads, decodes and displays a picture from a game directory in one
native process, without an exported combined file or a host renderer:

```text
wbrun /s0/kingsquest1 1
```

Input and output must be the same Wild Bits terminal; any key exits this
integration test. `objs/platform/wildbits-graphics.asm`, `objs/platform/wildbits-graphics.asm`,
`objs/platform/wildbits-graphics.asm`, `objs/platform/wildbits-graphics.asm` and `presentation.d`
are shared with `wbpic`. Splitting these includes left `wbpic` byte-for-byte
unchanged. `objs/platform/wildbits-graphics.asm` copies source spans into private row staging,
unmaps them, then maps the framebuffer. Source and destination never require
two simultaneous service windows. The integrated module is 3,294 bytes and
requests 14,646 bytes of private data.

The MAME integration test passed with simultaneous gradient and King’s Quest I
castle instances on `/term` and `/vt1`: every displayed pixel, terminal
restoration, independent quit, relaunch and an unchanged free-memory map.
It uses host rendering only to calculate the expected test pixels; the native
program reads the game files itself. See [MAME.md](WILDBITS-MAME.md).

`objs/platform/wildbits-graphics.asm` retains the original CoCo circle tables, edge clamping and
splatter sequence. CPU tests cover every pen size and style at edges and
mapping boundaries, relocated code/data, and malformed input. Native MAME
picture 1 output matched SHA256
`d1ddfc805018b2c8f4e5fac32b6ce17489154499479fca8ec41194c306b0a757` on both
terminal paths, with no allocation leak.

This is not yet gameplay: the logic interpreter, object animation and game
input still need integration. King’s Quest I logic 0 is compressed (5,941
stored bytes, 8,950 expanded bytes), so the existing plain 8 KB loader cannot
run it. Native decompression and mapped resource storage are prerequisites.

## Real game picture reference bridge

A host-side bridge can now locate a plain picture resource in `picDir` and
`vol.N`, execute the existing `shdw` renderer on XRoar's actual 6809 CPU,
and export the combined buffer. It preserves the working renderer rather
than introducing a second picture algorithm. For example, from this directory:

```sh
python3 sierra/tests/export_picture.py sierra/kingsquest1 1 /tmp/kq1-picture-1.bin \
  --assembler /path/to/lwasm --defs /path/to/nitros9/defs
python3 sierra/tests/check_wbpic.py --picture /tmp/kq1-picture-1.bin
```

Transfer the exported file and run `wbpic` on the target as with the diagnostic
fixture. King's Quest I picture 1 is the castle scene; its plain resource is
2,752 bytes at `vol.1` offset `$E24A`. The reference combined buffer has SHA256
`d1ddfc805018b2c8f4e5fac32b6ce17489154499479fca8ec41194c306b0a757`.

The exporter assembles a private copy of the shared renderer in a temporary
directory, uses its existing fixed-address layout only inside the CoCo CPU
reference fixture, and returns the normal low-color/high-priority bytes.
It does not change the Wild Bits module's position-independent layout or
perform host-side memory mapping on the target. No game assets or generated
buffers are committed to the repository.

Resource extraction validates the directory entry, volume header, stored
length, and end marker. This first bridge supports plain resources up to one
8 KB command window. Nibble-packed and LZW resources fail explicitly; they
are not silently treated as plain bytes. Native resource loading and F0-FA mapped command decoding now exist.
Compression and interpreter integration remain unimplemented.
The viewer still takes a raw combined buffer, not a game directory.

Validation includes visual inspection of the castle reference and execution
of the native viewer against every pixel of that real buffer under mocked
services, alongside its diagnostic/error/terminal tests. This proves the
reference-to-presentation pipeline at the CPU level. The separate MAME run
also verified every displayed pixel of this buffer through the real Wild Bits
driver on `/vt1`, including restoration after terminal switching. A playable
game and physical hardware validation remain future milestones. The bridge
establishes a concrete reference for comparing the eventual native decoder.

## Expanded resources and native logic execution

`wbasset` loads a logic resource from `logDir`/`vol.N`, expands it if necessary,
and writes the exact expanded bytes. Run from a terminal or redirect terminal
stdin explicitly in a script:

```text
wbasset /s0/kingsquest1 0 </term >/s0/logic0.bin
```

The reusable loader supports logic, picture, view and sound directory kinds;
the probe CLI currently selects logic. The loader also expands nibble-packed pictures
using the picture resource kind; the plain `wbres` probe remains deliberately limited.
Plain resources and expanded LZW resources occupy owned physical slabs of one
to eight blocks, rather than a fixed 8 KB output buffer. The LZW dictionary and
string stack reuse the private 8 KB command-workspace buffer. Both disk input
and output use private 512-byte staging with the mapping removed before I/O.

The decoder preserves the CoCo algorithm's least-significant-bit-first stream,
clear/end codes, and 9–11-bit dictionary widths. It additionally bounds the
input stream, dictionary references, temporary string stack and exact output
length. It uses callbacks for byte input/output, so compression code contains
no terminal, filesystem or hardware assumptions. Dictionary/code tables never
change in shared module memory; only private workspace changes.

`wbexec` includes that loader plus the converted bytecode core, mapped fetch,
logic cache, nested-call handling and message reader. On successful execution
it exports 256 variables followed by 256 byte-valued flags for regression
checks. It is a probe, **not yet a playable interpreter**. Unsupported game
commands/tests return an error instead of silently being skipped.

The core implements commands 1–17, relative jumps, return, comparisons,
variable/flag tests and AND/OR/NOT expressions. Platform commands currently
include typed resource loading/discard, cached/nested logic calls, scan-start
management, `set.game.id`, bounded object/view state, menus, strings, screen
configuration, keyboard bindings, replay records and room transitions.
`objs/platform/wildbits-logic.asm` follows the existing CoCo operand-count table; argument
staging and instruction/branch bounds prevent malformed scripts from reading
messages as instructions. Script positions remain offsets across mapping
changes. Messages use bounded relative offsets; plain logic strings are
XOR-decoded with the original key, while compressed logic strings are plain.

`objs/platform/wildbits-logic.asm` retains up to 32 owned typed resource slabs. Sixteen private call
frames save the caller's cache slot, instruction offset, code end and remaining
instruction budget. Loading a callee unmaps the caller first; return restores
its descriptor. Exit frees temporary allocations and all cache-owned slabs,
including failed loads and errors inside nested calls. Cache/call overflow
fails explicitly. Forced termination and persistent cleanup failures retain
the same program-owned allocation limitation described above.

Actual 6809 tests match all 228 compressed King's Quest I logic/view/sound
resources against an independent dictionary implementation. They also cover
relocation, exact 16 KB plain and 65,535-byte expanded output, partial I/O, malformed LZW, service failures,
encrypted/malformed messages, nested/cached calls and recursion bounds.
MAME verified real logic 0's 8,950 expanded bytes and a diagnostic cross-page
script with cached/nested calls on `/term` and `/vt1`, with unchanged free memory.
See [MAME.md](WILDBITS-MAME.md) for the commands and hashes.

Current probe modules: `wbasset` is 1,815 bytes with 9,989 private bytes;
`wbexec` is 6,194 bytes with 17,069 private bytes. The latter now needs three
private 8 KB blocks and one mapping window, leaving 23,808 code bytes.

## Native game owner

`sierra.asm` with `WILDBITS=1` has one OS-9 module header and includes the same small loader,
logic, decoder and presentation components directly. It also includes separate
`game-background-*`, `game-render-*`, `game-cycle-*` and `game-text-*` components.
It does not concatenate complete CoCo modules or run the probes as subprocesses.

The implemented path is:

```text
logic -> load.pic/draw.pic -> immutable background + composition buffer
      -> view metadata/RLE rows -> priority-sorted sprite composition
      -> show.pic -> terminal bitmap + persistent text cells
      -> wait/poll keyboard/update clock -> run root logic again
```

A composition slab owns four physical blocks. A separate four-block background
slab is allocated lazily when the first visible sprite needs it. Picture-only
scenes retain no duplicate background, saving 32 KB per process. Sprite
RLE rows stage in private memory; the view is unmapped before picture pixels
are accessed. Transparent pixels, mirrored cels, clipping and priority/control
occlusion are handled without retaining pointers across mapping changes.
Draw/erase rebuild visible objects over the saved background. This version
refreshes complete pictures; dirty-region optimization and hardware timing
measurements remain work, so no performance parity is claimed.

The game cycle resumes root logic at its saved scan start, while room changes
unwind nested calls before discarding room resources. Nonblocking `SS.Ready`
and one-byte reads route ASCII `set.key` bindings to controllers. `F$Time`
updates the AGI clock, including second rollover. Foreground/background signals
pause work, and foreground return resets the time baseline to avoid counting
hidden time. Immediate `quit(1)` releases owned resources.

Text uses the existing immutable 128-character, 8-by-8 font, extracted into
`objs/font-data.asm`; the CoCo screen module remains byte-for-byte identical.
Private 40-by-25 character cells and packed foreground/background colors
survive picture refreshes. `display`/`display.v` support colors, wrapping and
bounded `%v`, `%s`, `%w` and recursive `%m` message expansion. `print`/`print.v`
show a modal response and restore the scene after dismissal.

`wbgame` currently uses 23,584 code bytes and 24,460 private bytes. Three private
blocks, the kernel block and one mapping window leave a conservative
23,808-byte code budget.
Physical memory also holds resource caches, two picture slabs and the terminal
bitmap. These are distinct from the logical-address budget.

`check_wbgame.py` executes native instructions and checks every castle pixel,
transparent/mirrored/clipped/occluded/erased sprites, glyph colors and wrapping
across framebuffer pages, persistence after `show.pic`, repeated logic cycles,
keyboard controllers, clock rollover, normal and move-to stepping,
end-of-loop animation, directional keys, and ownership cleanup. These CPU tests
mock OS services; real-driver MAME acceptance is reported separately.

Vocabulary parsing, typed input, formatted responses, follow motion and menu
interaction are now integrated. Save/restore, owned audio and restart are implemented and tested;
later-game command coverage is incomplete. Native blocking rectangles use the
same containment routine as CoCo. Follow motion and its axis-direction helper
also use shared CoCo routines; the CoCo binary remains byte-for-byte identical.
Menu construction and selection work. Save/restore uses the validated WS
version-1 format described in the engine notes.
The original `objs/wildbits_engine.asm` remains untouched and unbuilt.

The native-owner MAME diagnostic passed on the existing 512 KB Jr2 test OS:
repeated logic cycles, every castle/diagnostic pixel, two terminals, switching,
independent controller-key exits, relaunch and unchanged free RAM. Its scripts
exercise implemented picture commands; they are not the full King's Quest I
logic. See [MAME.md](WILDBITS-MAME.md). Two sprite-heavy games need additional memory;
the guide's current RAM-capable kernel/core must be verified before claiming
that configuration. An allocation failure is reported and cleaned up.

The native `game-motion-*` components now step visible animated objects between
logic cycles, choose directional loops, advance cels, and complete move-to and
end-of-loop operations. Positions are checked against horizon/edge limits,
picture control pixels and other object baselines. Those checks use the saved
background rather than the priority values written by sprite composition.
Normal stepping, exact move-to completion with restored step size, and animation
completion passed CPU tests, as did impassable picture controls and
land-only/water-only restrictions. Object collisions and edge cases still need
dedicated coverage. Direction keys use `SS.KySns` after reading a character, so an ordinary
Backspace does not become a left arrow. Function-key bindings recognize the
four codes exposed by the current driver. This input path has CPU-test coverage;
real-driver gameplay acceptance is still pending. Arrow autorepeat currently
keeps the selected direction; stop/toggle behavior needs game-level verification.

The shared-source/backend migration is described in [ENGINE.md](WILDBITS-ENGINE.md#architecture-correction).

The Wild Bits owner currently starts with AGI sound flag 9 off because the
existing global blocking `SS.Tone` service cannot safely play independent AGI
sound streams. `wildbits-audio.asm` implements sound-off completion and
stop commands without touching audio hardware. If a script re-enables flag 9, the backend reports audio unavailable once,
clears flag 9 and completes the request in sound-off mode. This is sound-disabled operation, not
audio playback support.

## Inventory and native font installation

Install **both** `wbgame` and the generated `wbfont` in the target execution
directory. Give `wbfont` read/execute attributes, including public attributes
when other users run games. The engine opens it with `READ.+EXEC.` and requires
exactly 1,024 bytes. `make` exports those bytes directly from the canonical
`objs/font-data.asm`. The CoCo font is unchanged; native glyph rendering reads
a per-process copy loaded once at startup. Missing, short or oversized fonts
fail with closed paths and owned-resource cleanup.

The inventory backend is in `objs/platform/wildbits-inventory-{code,data}.asm`.
It implements `get`, `get.v`, `drop`, `put`, `put.v`, `get.room.v`, `has`,
`obj.in.room`, and `status`. The item table comes from the game's encrypted
`object` file using its Avis Durgan key. Files above 2,048 bytes are explicitly
rejected. The header must describe at most 256 complete three-byte entries;
name pointers must follow the entry table and terminate within the file.
Item locations are mutable private state: room 255 means carried, room zero
means removed. `put` resolves its room variable; `put.v` also resolves the item
variable. Names are reread for each status screen without resetting item rooms.

`status` shows up to 21 item names per page. With flag 13 enabled, up/down moves
the selection, ENTER stores the selected item in variable 25, and ESC cancels; cancellation stores 255. CTRL-C interrupts the game. Without flag 13, a key dismisses the
screen. Foreground checks and ready polling leave no mapping live while waiting.
The modal screen saves the 2,000 persistent text bytes and restores them after
exit. It clears the complete owned bitmap before redrawing the picture, sprites
and text, including pixels outside the 168-row picture region.

CPU checks cover item transfers and predicates, selection/cancellation,
modified rooms surviving status reload, full-frame restoration, malformed
objects/fonts and cleanup. The real-resource MAME diagnostic now checks the
inventory title against the shared font pixel by pixel, dismisses inventory,
requires the castle scene to return, interrupts the process and compares free
memory. This is inventory/startup acceptance, not parser, audio or full-game
acceptance. See [MAME.md](WILDBITS-MAME.md).

Selection changes redraw only the old and new highlight rows. A page change
redraws the list. The CPU suite tests selecting item 22, beyond the 21 visible
rows. Recognized arrows are consumed while player control is disabled, so a
Right arrow cannot accidentally trigger the game's ASCII Tab controller.
The real-driver test sends Ctrl-I for that Tab binding; ordinary physical Tab
delivery in this MAME setup remains a separate keyboard-driver/UI check.

Text colors now occupy one byte per cell: the high nibble holds the logical
foreground and the low nibble holds the logical background (each 0–15).
The renderer converts these to palette indices once per glyph; its pixel loop
is unchanged. Inventory highlights and text backups use the same packed format.
Keyboard controllers use one private bit each, retaining all 256 controller
IDs in 32 bytes. Tests exercise all eight adjacent bits at IDs 248–255 and
require each event to expire after one cycle. Together these changes save
1,224 private bytes and one 8 KB logical data block, leaving room for vocabulary
parser code. The interactive parser described below uses that space.

## Interactive gameplay checkpoint

The parser reads original `words.tok` files using bounded 512-byte partial
reads. It honors the first indexed entry (including padding after the 52-byte
header), reconstructs prefix-compressed words, recognizes the trailing zero,
and chooses the longest matching phrase. It normalizes case and the same two
punctuation classes as CoCo, ignores dictionary group zero, and records unknown
word indexes in AGI variable 9. Input is limited to 38 typed characters (up to
39 through `parse`), with at most 20 word IDs. Submitted text and word spans
remain private across subsequent logic/resource loads. `said` supports word
wildcards 1/9999 and flag 4 prevents a second acceptance of the same sentence.

The game drains at most 40 buffered keys per cycle, stopping after sentence
submission. Controller bindings take precedence over text entry. Normal AGI
startup now enables player control; explicit program-control commands still
suppress arrow movement. On the tested K keyboard Escape/Break delivers byte
5, normalized to 27 for bindings and modal cancellation. The program disables
stdin echo, EOF and quit characters while running, preserves CTRL-C interrupts,
and restores the three changed options on normal, error and interrupt exits.

`get.string`, `get.num` and `word.to.string` work with bounded private editors
and string slots. A modal editor saves any pending ordinary input line and
restores it afterward. Numeric results follow byte-variable arithmetic.
The formatter supports `%vN`, `%sN`, `%wN`, `%mN`, `%gN` and `%oN`, with
recursive string/message expansion, byte-wrapped indices and numeric widths.
Like CoCo, unknown two-byte escapes (including `%%`) disappear, missing numeric
operands default to zero, and out-of-range words/messages expand to empty.
Expansion is bounded to 2,047 output bytes and four copied frames; corrupt or
missing resources remain errors. Message zero safely expands to empty. Final
recursion/malformed-input policy acceptance remains open in WILDBITS-PARITY.md.
Modal responses wrap whole words and retain a two-column margin.

The native menu is a paged list of `title: item` entries. Arrow keys navigate,
ENTER sends the item's controller, disabled entries cannot activate, and
Escape/Break cancels. Modal windows save both text planes and wait without
foreign mappings. Immediate and confirmed quit are supported.

Commands `random`, `mul.n/v`, `div.n/v`, `follow.ego` and all three reposition
forms are integrated. Reposition uses bounded left/down/right/up placement
search with screen, horizon, object-collision and picture-control checks.
Division by zero returns 255 like CoCo; random bounds use CoCo byte wrapping,
including reversed ranges. Exhausted placement searches fail explicitly.

`check_wbparser.py` verifies typed/multiword matching, ignored words,
normalization, editing and unknown indexes. `check_wbplay.py` verifies following,
placement, math, modal/menu selection, formatted glyph pixels, bounded editors
and rejection/cleanup paths. The longer `check_wbgame_route.py` executes the
unmodified KQ1 scripts with Right/Down/Right inputs, requiring a room 1 to room 8
transition, a rendered new scene and continued movement. Its OS calls are
mocked. MAME separately verifies `look room`, unknown-word formatting, real
menu/inventory handling and cleanup. Full-game completion and two simultaneous
full-resource games remain unverified.


## Credits replacement and Pause

`draw.pic` removes saved text cells within its configured 21-row picture
area after the new picture successfully decodes. Previously the startup's
“Designed and written by” credits remained in the text overlay and were drawn
again on every castle refresh. `show.pic` still preserves text written after
that draw; status/prompt text outside the picture area remains intact.
`check_wbcredits.py` compares every pixel for all five picture positions,
including repeated `show.pic` and retained outside text.

The original game's Pause menu action now opens a modal pause window, restores
the scene on a keypress and resets the clock sampling baseline. Time spent
paused does not advance AGI game seconds; subsequent normal seconds do.
Pause itself requires no new private storage. The credits/Pause checkpoint
used 24,555 private bytes; the rendering changes below add 17 bytes.

The MAME harness's `--sustained` mode submits `look room`, submits an unknown
word, selects Pause through the original game menu, resumes and submits
`look room` again before verifying interrupt exit and unchanged free memory.
This covers a longer interactive session; it does not establish full adventure
completion, save/restore or sound support.


## Movement performance

The original interactive build restored the full background twice per cycle,
transferred the full picture row by row and rendered text by character. A
character crossing a framebuffer page repeatedly mapped those same pages.
Small sprites also alternated view and picture mappings for every cel row.
Those operations made normal movement visibly slow.

The native backends now:

- Copy a full background in 8K word-sized chunks when a full copy is needed.
- Remember each sprite's clipped previous footprint and erase just that area.
  Cels larger than the 8K staging workspace retain the full-copy fallback.
- Stage a complete small cel before plotting it, keeping the picture mapping
  while painting consecutive rows. Transparency, mirroring and priority stay
  unchanged.
- Mark both erased and newly drawn eight-pixel picture bands. Present only
  those bands; new pictures and modal restoration force a full repaint.
- Render text by scanline over the first through last occupied columns,
  leaving pixels for empty text cells untouched.
- Configure the palette/layer once, then invalidate that cached setup when the
  process receives its foreground signal so terminal switching remains safe.

The timed KQ1 castle test measured approximately **9 AGI pixels instead of 1**
for the same 200-frame (3.33-second) Right input. This is a short, scene-specific
movement measurement, not a general FPS or performance-parity claim. The
preceding dirty-band build reduced recurring map calls from 778 to 55 in a
separate deterministic CPU workload; the subsequent palette cache removes
additional setup calls.

Run the real-driver harness with `--movement` to produce `movement.json` and
before/after screenshots. `--module-file` can select an earlier build for
comparison. `check_wbsprite_damage.py` verifies moved/erased sprites, page
boundaries, clipping, offscreen positions and the large-cel fallback.
The native pixel/motion, modal/editor, credits and real-game room-route tests
also passed. Save/restore, sound and full adventure completeness remain open.

The current audio implementation and verification are described under
[Owned, queued native sound](WILDBITS-ENGINE.md#owned-queued-native-sound). Older
sound-disabled entries below record earlier implementation stages.


Timed blocking messages now honor AGI variable 21 (half-second units), with early
keyboard dismissal and automatic clearing after dismissal. Held messages and
Pause retain their separate behavior. The optional public SOL counter supplies
frame timing and rebases after terminal switching; the sleep-count fallback can
run late under scheduling load. Both text storage and modal waiting execute
through the matching immutable `wbstate` helper. Install it with `wbgame` from
the same build. The current resident is 23,584 bytes, the linked helper is 6,941 bytes, and
its writable state prefix is 3,080 bytes. Private allocation remains 24,460 bytes. See [the engine notes](WILDBITS-ENGINE.md#timed-blocking-messages--2026-10-07)
for the implementation and acceptance checks.


Inventory `show.obj`/`show.obj.v` previews now display the item and its bounded
description, wait for dismissal, then restore the scene and continue the
script. Existing cached views remain loaded. Implementation and verification
are in [the engine notes](WILDBITS-ENGINE.md#inventory-item-previews--2026-10-07).

Native `shake.screen` is supported through the existing graphics backend. It
restores the original picture, keeps sound serviced, and uses the public raster
counter when available. See [the implementation and validation notes](WILDBITS-ENGINE.md#native-screen-shake--2026-10-07).

The interpreter `version` command now opens a blocking identification dialog
and returns to its script after dismissal, preserving print flags and timers.
It shares the existing text helper and introduces no additional module.

Menu display/navigation uses the same immutable helper while ordinary movement
and rendering remain resident. Menus also work before the first picture creates
a screen. See [the backend notes](WILDBITS-ENGINE.md#menu-display-in-the-existing-cold-helper--2026-10-07).

Joystick initialization now toggles terminal-owned digital stick 0 through
`SS.Joy`. Movement and Enter/Escape button edges work in normal game cycles;
use the keyboard for modal dialogs. Missing joystick service keeps keyboard play
available. Current MAME verifies neutral readings but does not model physical
stick input; directional/button tests use the CPU fixture. See
[the input and performance notes](WILDBITS-ENGINE.md#terminal-joystick-input--2026-10-07).


Video Mode now switches each instance between the standard AGI colors and the
original CoCo Sierra RGB colors. See [the implementation and validation notes](WILDBITS-ENGINE.md#per-terminal-video-mode--2026-10-07).
To launch a private playable MAME image without automated test input, follow
[the interactive preparation instructions](WILDBITS-MAME.md#prepare-an-interactive-game).


Item previews now remain visible when opened from text mode and restore the
opaque text screen after dismissal. [The regression notes](WILDBITS-ENGINE.md#text-mode-item-previews-and-room-travel--2026-10-07)
explain that fix and the original KQ1 castle/lake round-trip check.


Entering the castle hall now restores arrow control after the door script stops
Graham. Room transitions also release the previous movement block. See
[the hall-control regression](WILDBITS-ENGINE.md#castle-hall-arrow-controls--2026-10-07).


The game's priority diagnostic (`show.pri`, opcode 29) displays the priority
plane until a fresh Enter or Escape, then restores the color scene. Ordinary
keys do not dismiss it. Each terminal owns its mode, including across foreground
switches. See the parity checklist for comparison and failure-path evidence.


Opcode 133 object status now shares CoCo's command/formatter source.
See [ABI-9 ownership, modal behavior and verification](WILDBITS-ENGINE.md#shared-object-status-diagnostic-abi-9).


Opcode 135 now reports native module/private sizes and owned page categories.
See [the ABI-10 memory mapping and callback contract](WILDBITS-ENGINE.md#native-memory-diagnostic-and-callback-layout-contract-abi-10).
