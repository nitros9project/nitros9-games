# Wild Bits Sierra port

`wbpic` is a native, position-independent 6809/NitrOS-9 Level 2 program that
presents the Sierra engine's combined picture-buffer format. It is the first
executable port artifact, not yet a playable interpreter. The existing
`objs/wildbits_engine.asm` remains an unfinished scaffold and is not built.
See [ENGINE.md](ENGINE.md) for why including four complete CoCo modules is
insufficient, and how one native program can be organized from reusable includes.

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

From this directory, with lwasm on PATH:

```sh
make NITROS9DIR=/path/to/nitros9
make fixture
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
make check
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

`make check` is CPU/service-contract testing. The separate MAME check below
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
See [MAME.md](MAME.md) for setup, the repeatable test command, exact revisions,
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

The loader lives in `resource-code.asm`, with private fields declared by
`resource-data.asm`; the probe owns the sole module header. `LoadPicture`
takes X=game directory, Y=picture number, U=private data base and matching DP.
It returns X=command buffer and Y=length, or carry/B indicating an error.
Its mutable fields, path strings and command bytes are process-private.
There are no hardware accesses, fixed load addresses or writable code.

The probe is 728 bytes with 8,907 bytes of requested private data, including
the full 8 KB command buffer and stack. The OS rounds this data allocation to
two 8 KB blocks. This is a test arrangement: the eventual interpreter should
put large resources behind bounded mapping windows to retain its 8 KB state
budget. It must not simply add this resident buffer to the packed engine.

`make check` runs actual 6809 tests for relocation, short reads/writes,
directory/header failures, large offsets and boundary sizes. The separate
real-driver MAME test is described in [MAME.md](MAME.md). Native MAME reads
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

`../objs/platform/wildbits-picture-memory.asm` allocates four consecutive physical blocks through
`SS.GfxAlloc` and maps one block at a time through `F$MapBlk`. The current page
is cached. `PicturePointer` accepts a logical byte offset and returns a pointer
valid only until another mapping call; clients never retain it across pages.
The line and plot routines use this boundary, including lines crossing an
8 KB page. All four blocks are initialized; only the 26,880 picture bytes
are exported. A private 512-byte staging buffer lets output unmap before
`I$Write`, including partial writes.

`decoder-fill.asm` uses scanline flood fill with a private 4,096-byte stack
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
free-memory map. See [MAME.md](MAME.md) for reproduction.

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
integration test. `presentation-data.asm`, `presentation-buffers.asm`,
`../objs/platform/wildbits-presentation-helpers.asm`, `../objs/platform/wildbits-presentation-palette.asm` and `presentation.d`
are shared with `wbpic`. Splitting these includes left `wbpic` byte-for-byte
unchanged. `../objs/platform/wildbits-presentation.asm` copies source spans into private row staging,
unmaps them, then maps the framebuffer. Source and destination never require
two simultaneous service windows. The integrated module is 3,294 bytes and
requests 14,646 bytes of private data.

The MAME integration test passed with simultaneous gradient and King’s Quest I
castle instances on `/term` and `/vt1`: every displayed pixel, terminal
restoration, independent quit, relaunch and an unchanged free-memory map.
It uses host rendering only to calculate the expected test pixels; the native
program reads the game files itself. See [MAME.md](MAME.md).

`decoder-pen.asm` retains the original CoCo circle tables, edge clamping and
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
python3 export_picture.py ../kingsquest1 1 /tmp/kq1-picture-1.bin \
  --assembler /path/to/lwasm --defs /path/to/nitros9/defs
python3 ../tests/check_wbpic.py --picture /tmp/kq1-picture-1.bin
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
the probe CLI currently selects logic. Nibble-packed pictures remain unsupported.
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
`logic-code.asm` follows the existing CoCo operand-count table; argument
staging and instruction/branch bounds prevent malformed scripts from reading
messages as instructions. Script positions remain offsets across mapping
changes. Messages use bounded relative offsets; plain logic strings are
XOR-decoded with the original key, while compressed logic strings are plain.

`logic-cache.asm` retains up to 32 owned typed resource slabs. Sixteen private call
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
See [MAME.md](MAME.md) for the commands and hashes.

Current probe modules: `wbasset` is 1,815 bytes with 9,989 private bytes;
`wbexec` is 6,194 bytes with 17,069 private bytes. The latter now needs three
private 8 KB blocks and one mapping window, leaving 23,808 code bytes.

## Native game owner

`wbgame.asm` has one OS-9 module header and includes the same small loader,
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
survive picture refreshes. `display`/`display.v` support literal messages, colors and wrapping;
format directives currently return an explicit unsupported error.

`wbgame` currently uses 15,198 code bytes and 24,328 private bytes. Three private
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

This is **not a playable game yet**. Follow motion, vocabulary
parsing, formatted messages/dialogs, menu interaction, sound playback and
remaining game commands still need integration. Native blocking-rectangle
commands now use the same containment routine as CoCo, with private native
state; blocking, ignoring and clearing passed CPU tests. Menu construction and replay
records are bounded state components, not completed menu UI or save/restore.
The original `objs/wildbits_engine.asm` remains untouched and unbuilt.

The native-owner MAME diagnostic passed on the existing 512 KB Jr2 test OS:
repeated logic cycles, every castle/diagnostic pixel, two terminals, switching,
independent controller-key exits, relaunch and unchanged free RAM. Its scripts
exercise implemented picture commands; they are not the full King's Quest I
logic. See [MAME.md](MAME.md). Two sprite-heavy games need additional memory;
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

The shared-source/backend migration is described in [ENGINE.md](ENGINE.md#architecture-correction).

The Wild Bits owner currently starts with AGI sound flag 9 off because the
existing global blocking `SS.Tone` service cannot safely play independent AGI
sound streams. `wildbits-sound-code.asm` implements sound-off completion and
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
acceptance. See [MAME.md](MAME.md).

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
parser code. Parsing itself is still pending; this is memory preparation.
