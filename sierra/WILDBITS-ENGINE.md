# Wild Bits engine structure

## Current source layout

Platform code is grouped into 26 feature/binding assembly files rather than
per-operation fragments. The shared object command component includes
CoCo/native loop/cel table traversal. The resource lifetime audit preserves
CoCo suffix-based view-heap discard and native single-slot slab ownership;
these are distinct backend policies. The native discard failure path now
preserves carry after clearing transient ownership, with failed slots retained
for retry. Sprite visibility now uses the same shared per-cel rule for both
owners; native publishes AGI flag 1 only for ego. Selected-cel positioning is also shared, including right-edge and
height/horizon adjustment. Native platform commands now use an immutable relative dispatch table
from the shared AGI catalog. Both decoders also expand the shared LZW
window-alignment/mask and dictionary-walk core. The game is 23,725 bytes, with 83 resident code bytes free;
process data is 24,460 bytes (116 bytes below its three-page limit).
The per-cel visibility byte reuses the sort key after collection completes.


There is no separate `sierra/wildbits` tree. The game entry point is
`objs/sierra.asm` with `WILDBITS=1`, optional development probe entry points are under
`tests/probes`, platform-specific bodies and private state definitions under
`objs/platform/wildbits-*`, and routines assembled by both ports under
`objs/shared`. The build entry point is `objs/wildbits.mk`; host exporters
and fixtures live in `tests`.

The directory integration preserves every module byte and process-data size.
The native logic owner still differs from CoCo `mnln`: placing that owner’s
components under `platform` identifies their current scope, but does not
complete the common-engine migration. Shared command/condition/object/picture
bodies continue to be used directly by both owners. Remaining native-only
algorithms must be reconciled with the CoCo implementations as that work
continues.

## Game versus development probes

`wbgame` is the runnable game. It assembles the resource loader, decoder,
logic executor, and game loop directly; it does not load any probe modules.
Both production builds now assemble `objs/sierra.asm`. With `-DWILDBITS=1`,
that entry includes `platform/wildbits-runtime.asm`, which defines the native
module header, private storage, and component composition. Otherwise it
assembles the existing CoCo setup module. Selection adds no runtime dispatch.
The Wild Bits executable and internal module name remain `wbgame` so existing
launch commands and emulator harnesses keep working.

The runtime layouts still differ: CoCo starts its separate `mnln` engine,
whereas the native composition owns the full game. A common build entry is
an intermediate step, not proof that the remaining engine behavior is shared.

The other executables are optional diagnostics: `wbasset` exercises expanded
resource loading, `wbdecode` picture decoding, `wbexec` logic execution,
`wbres` raw resource loading, `wbpic` presentation, and `wbrun` the combined
resource/decoder/presentation path. They belong to test tooling rather than
the production game. Their sources live in `tests/probes`; generated binaries,
listings, and maps remain in `objs` for the existing regression harnesses.

From `sierra/objs`, `make -f wildbits.mk all` builds only the game and its font
and checks the game memory budget. `make -f wildbits.mk probes` builds the
optional diagnostics and checks their budgets. `make -f wildbits.mk check`
builds both groups before running the regression suite.

## What `objs/wildbits_engine.asm` does

The existing untracked scaffold sets `WILDBITS` and includes `sierra.asm`,
`mnln.asm`, `scrn.asm`, and `shdw.asm`. It is excluded from the build.
Those are complete CoCo OS-9 module sources, each with its own module header,
trailer, data definitions, and common labels such as `start`, `name`, and `eom`.
They also select backends that deliberately reject an unimplemented Wild Bits
target. An outer `EMOD` cannot convert that collection into one native module.
No native program requires this scaffold; it has been left intact.

## One module can still be the right eventual result

Including several assembly files is a useful way to organize **one program**,
provided they are body/data includes with explicit interfaces and one owning
`MOD`/`EMOD` pair. This is also the structure described by the porting guide.
Source-file boundaries do not require runtime dispatch or extra instructions.

The current King's Quest I binaries total 31,572 bytes:

| Module | Bytes |
| --- | ---: |
| `sierra` | 1,650 |
| `mnln` | 25,442 |
| `scrn` | 1,996 |
| `shdw` | 2,484 |

That makes a single resident native program a reasonable initial target,
subject to the real converted size and process mapping budget. It is not
proof that the finished port fits. The guide's 40,192-byte code budget assumes
an 8 KB private data area and at most two simultaneous one-block service
windows. More physical RAM does not enlarge the process's logical space.

The required conversion is deeper than removing module headers:

- Code references must be position independent; the native code must not
  require the old module load addresses or mutate linked code.
- Each process owns its state. Shared includes use a documented private
  data base rather than absolute CoCo data addresses.
- Cross-module remapping calls become explicit calls between converted
  routines, with register/state contracts. Any remaining banked component
  needs a real loader and bounded mapping lifetime.
- The combined picture/priority buffer, resources and framebuffers stay
  outside the resident state where needed, accessed through OS-managed
  windows. Mapping registers are not an application portability interface.
- Display, input, visibility, timing and sound follow their native platform
  contracts. The existing CoCo assembly remains a working reference.

## Building and proving reusable pieces

`wbgame` is the production native interpreter. Optional executables under
`tests/probes` exercise the same grouped feature bodies directly: `wbpic`
tests presentation, `wbres` raw loading, `wbdecode` decoding, `wbasset` expanded
assets, `wbexec` logic execution, and `wbrun` picture integration. Each owns
one module header and private layout. They neither fork one another nor form
a chain of processes required to play the game.

The current production flow is:

```text
Directory + volume -> checked resource/slab loading -> bounded decompression
Logic cache + mapped byte stream -> common command/condition execution
Commands -> room/object state, motion/cel updates, parser and text/dialog UI
Picture commands -> combined color/priority buffer -> background composition
View metadata + cel runs -> object composition -> terminal-owned bitmap
Cycle loop -> clock/controller input -> logic + motion + presentation
```

`wildbits-memory-resources.asm` supplies loading, asset access and view/room
resources. `wildbits-graphics.asm` supplies mapped picture storage, sprite
composition and presentation. `wildbits-logic.asm`, `wildbits-objects.asm`,
`wildbits-input.asm` and `wildbits-text-ui.asm` own the remaining native
orchestration. Both owners expand common algorithms from `objs/shared`;
the full migration is still incomplete. No complete CoCo module or fixed
CoCo workspace is linked into the native executable.

Normal/follow/wander/move-to motion, animation, parser input, dialogs, menus
and inventory have native implementations and regression coverage. Their
remaining owner-specific orchestration still needs reconciliation. Native
sound currently completes requests with sound disabled and warns once if a
script enables it; there is no owned audio driver. Replay/checkpoint support
does not establish full CoCo save/restore compatibility. Full adventure
completion and sprite-heavy concurrent gameplay are not yet established by
the emulator acceptance tests.

The one-window resource/picture/frame mapping discipline remains necessary.
Private interpreter buffers stay resident while picture, background, assets
and terminal bitmaps use separately owned physical storage. Shared code and
font bytes remain immutable. The grouped assembly dependencies in
`wildbits.mk` now track every feature/binding/shared body for all owners,
including probes, without repeated per-operation prerequisite lists.

## Architecture correction

The picture coordinate, line and pen routines, including their immutable tables, now have
one implementation under `objs/shared/`, included by both `objs/shdw.asm` and
the native decoder. `objs/platform/sections.d` selects either
`coco-graphics.asm` or `wildbits-graphics.asm` at assembly time.
The Wild Bits implementation preserves the registers needed by these shared
algorithms and maps each logical pixel through `PicturePointer`.

Wild Bits mapped-picture allocation/access and terminal presentation now live
in `objs/platform/wildbits-graphics.asm`.
Native game/viewer integration uses the existing `platform/sections.d`
selector. This does not yet make the legacy CoCo interpreter's state ABI usable
on Wild Bits: its loader and other unconverted selectors still reject that
build. The native interpreter is retained during migration, not declared to be
a shared CoCo/Wild Bits interpreter. Remaining work is to reconcile command
interfaces and state access before retiring its duplicate implementations.

The first extraction rebuilt all seven native modules and CoCo `shdw` with
byte-for-byte identical output. CoCo `mnln` also remains byte-for-byte identical
after sharing direction tables. Decoder and native-game CPU regression checks
passed. The selectors add no runtime dispatch. Native
probes remain in this directory; production backend routines belong under
`objs/platform`, and routines shared by both platforms belong under
`objs/shared`.

### Command/state migration

`objs/shared/agi-command-table.asm` is now the single 182-entry command catalog.
Assembly macros expand it into the original CoCo handler/parameter descriptors
or native operand-count bytes. There is no runtime conversion. The CoCo command
table and interpreter binary remain byte-for-byte unchanged.

`objs/shared/object-distance.asm` supplies the distance calculation to both
interpreters. Each owner resolves its own object arguments, binds private
scratch, and stores the result in its own variable table. Native command 69
checks both object indices before calculating distance.

`objs/shared/object-block-test.asm` supplies strict rectangle containment to
both interpreters. The state-addressing choice is made at assembly time.
Native commands 90/91 set/clear a process-private rectangle; movement compares
old and proposed containment, stops a crossing, and honors ignore-blocks.
CPU tests cover blocking, ignoring and clearing, alongside object-distance
self/invisible cases. The expanded suite needs more emulated runtime than the
previous suite, so its emulator limit is now 900 seconds; each synthetic logic
still has an explicit bounded exit.

Actual King's Quest I startup was also exercised with real resources, advancing
mock clock values and Space/Return input. It reached command 99 (`sound`) and
returned the explicit unsupported-service error 208 with complete cleanup.
That run used mocked OS services, not MAME, and is not a gameplay acceptance.
Sound remains the next observed startup blocker. Main interpreter state and
command consolidation remain incomplete.

### Real startup and additional shared motion

The native owner uses the existing sound selector and
`objs/platform/wildbits-audio.asm`. There is no safe multi-instance AGI
playback service in the current driver: `SS.Tone` is blocking, has a global
sound owner and may ignore concurrent requests. The native backend starts with
AGI sound flag 9 off. If a script enables it, the backend reports audio
unavailable once, disables the flag and completes the request. It emits no
hardware writes. Audio support remains unfinished.

Wander direction/countdown and unsigned byte division now come from the same
includes as CoCo. Native random state is private to each game. Native position
predicates also share CoCo's inclusive rectangle comparison, with adapters for
private scratch and boolean returns. The boolean accumulator is preserved.
Native `clear.lines` creates persistent opaque blank cells over inclusive rows;
CPU checks cover both clear colors and persistence after a picture refresh.

CPU checks passed for these changes, including all position predicates, false
AND preservation, wander countdown/direction bounds, audio fallback notification
and completion, and the existing rendering/movement/cleanup cases. CoCo `mnln`
remains byte-for-byte identical to the pre-refactor binary.

Unmodified King's Quest I resources reached room 1 in a bounded CPU run. A
simulated interrupt after two cycle waits returned error 228 and freed all
resources. The captured scene included the castle and sprites. These OS calls
were mocked; the capture is not driver acceptance.

The earlier real-driver diagnostic reached the castle and stopped at command
124 (`status`). The inventory implementation described below removes that
blocker. Full gameplay and concurrent sprite-heavy games remain unverified.

### Inventory state, scratch lifetimes and the font boundary

The Wild Bits inventory backend loads real item names and initial locations,
then keeps mutable locations private to the process. Its status screen rereads
names without resetting those locations. The normal and selecting screens use
the persistent text renderer; selecting uses AGI flag 13 and variable 25.
Tests cover the file bounds, commands, predicates, scrolling logic, selection,
cancellation and restoration. Only encrypted object files up to 2 KB are
currently supported.

The modal screen backs up the character plane and packed color plane in `resourcecommands`. That
8 KB workspace normally holds the LZW dictionary or decoded picture commands.
No asset loading or picture decoding occurs while inventory is modal. The
4 KB fill stack supplies the temporary object-name buffer (first 2 KB) and the
item list (last 256 bytes); names are reloaded because subsequent picture fills
can overwrite them. Item rooms remain in separate persistent storage.

`assetinput`, `picturestage` and `messagebuffer` share one 512-byte private
region. Resource decompression, picture/background copies and message copying
are separate phases. Message consumers must finish copying before presentation
or another asset load. These aliases save memory without introducing window
mapping into hot rendering loops. They are process-local, never shared across
instances. The owner reserves a 512-byte CPU stack area.

Code growth exposed a startup stall on the real driver even while mocked CPU
runs passed. A reduced-size diagnostic passed that point. The build budget now
reserves the kernel's logical block as well as the service window. The native
font is therefore a separate bundled asset exported from the same CoCo font
source, loaded once into private memory. This preserves all 128 glyphs and the
rendering loop while shrinking resident code by roughly 1 KB. Install `wbfont`
in the execution directory with `wbgame`; startup rejects a missing or
incorrect-length font. This is a resource boundary, not a second interpreter.

Real MAME checks cover the inventory title glyphs, dismissal, restored castle,
interrupt exit and unchanged free memory. CPU checks also require every pixel
outside the picture to return to its prior blank state; modal dismissal clears
the full bitmap before redrawing the saved scene and persistent text.

Inventory cursor movement uses a bounded text-cell range to repaint the old
and new rows. Only a visible-page change redraws all cells. The scrolling
check selects item 22 and verifies the bitmap returns to its exact prior blank
state. The input adapter also consumes recognized arrows during program
control rather than exposing them as overlapping ASCII Tab/backspace keys.

The text overlay uses 1,000 character bytes and 1,000 color bytes. Logical
foreground/background values occupy the high/low nibbles. Glyph setup unpacks
them and adds the palette offset; no color unpacking occurs per pixel. Blank
cells are identified by the character plane, independently of color zero.
Inventory normal rows use $0F (black on white), selected rows $F0, and modal
backup/restore copies exactly 2,000 bytes. Controllers similarly use a private
32-byte bitset; controller ID divided by eight selects the byte and its low
three bits select the mask. This retains the full 0–255 script ABI.

At the memory-preparation checkpoint these changes reduced private storage
to 24,328 bytes (three 8 KB blocks) and the module to 15,198 bytes, with a
23,808-byte code budget and 248 spare private bytes. The interactive features
below use this headroom. CPU pixel checks and real-driver MAME inventory
startup/restoration pass with the packed layout; performance parity has not
been measured.

## Interactive native game boundaries

`wildbits-parser-{code,data}.asm` owns the typed line, original dictionary
reader, submitted IDs and saved input spans. `wildbits-text-ui.asm` expands
copied messages; `wildbits-text-ui.asm`, `wildbits-input.asm` and
`wildbits-text-ui.asm` provide modal interaction. The game owner selects these
small components, while `objs/platform/wildbits-logic.asm` only routes commands and tests.
No additional program module or merged CoCo module header is introduced.

Follow and axis-direction bodies are shared includes, with an owner-specific
ego pointer and completion-flag callback. Their CoCo assembly is unchanged.
Reposition is a native placement adapter using existing collision/control
checks and an explicit finite search budget. Game arithmetic reuses Div8 and
process-private random state.

Modal text backups use the first 2,000 bytes of `resourcecommands`. A modal
editor also saves its pending line at offsets 2,000–2,040. The formatter uses
four 512-byte source slots at `fillstack` offsets 0–2,047 and a separate
2,048-byte output area at offsets 2,048–4,095. The decoder is idle during this
phase; menu/inventory and formatter uses of that workspace do not overlap in
time. Entered words and spans are persistent private data, never aliases of
these transient buffers.

Terminal option packets use 32 bytes of CPU stack; only the original echo,
EOF and quit bytes and an ownership flag persist. CTRL-C is retained. Cleanup
restores the changed fields, retries a failed restoration once, and preserves
the earlier failure status. Tests model non-default options and assert their
restoration on every exit.

The current module is 21,235 bytes and its private area 24,572 bytes, leaving
4 bytes before a fourth data block. The code limit remains 23,808 bytes.
Further persistent state needs a deliberate layout change. Timing/performance
parity and complete game-command coverage are not established.


## Native render phases and damage state

The command workspace is reused only after asset/picture decoding or modal
backup restoration has finished. Full background copies and small cel staging
use its whole 8K. Presentation reserves bytes 0..2047 for any live modal/text
editor backup, staging picture input at +2048 and expanded output at +4096.
The maximum 12-row batch fits; ordinary damaged bands contain eight rows.
No operation maps a source slab and framebuffer/picture slab simultaneously.

In native `wbgame` records only, the unused bytes 6..9 hold the last clipped
sprite footprint: x, top, width, height. Zero height means nothing to erase.
Restoration consumes that footprint, and successful plotting remembers the new
one. Both rectangles mark the 21-bit picture-band damage mask. Large footprints
fall back to a full background restore and mark every band. New picture draws
and full bitmap refreshes also mark every band. Damage clears only after a
successful presentation. The CoCo record implementation is unchanged.

`wildbits-text-ui.asm` stages a glyph scanline in the private 320-byte
row-output buffer; palette index zero is a skip marker for absent text cells.
Actual text colors remain indices 1..16. Bounded editor updates retain their
existing range renderer. The full renderer no longer maps pages by character.

Palette/layer setup is cached per process, with foreground notification
invalidating the cache. Real two-terminal tests cover restoration and exits.
The added rendering controls total 17 private bytes and require no extra
physical allocation. Four bytes remain before a fourth data block (one with
optional exit tracing). CPU tests now load the larger module at $A000 rather
than $B000, and reject any fixture overlapping the CoCo I/O page at $FE00.

The scanline text renderer bounds each occupied row to its first and last
nonzero character. Interior zero cells still preserve framebuffer pixels.
Two private bytes retain the inclusive columns across glyph rows. This avoids
generating and copying unused leading/trailing columns without changing the
font, colors, wrapping, or bounded line-editor path.

## Mapped bytecode fetch

`VmFetchByte` checks the sticky asset error and code-end bound before every
read. When the requested offset belongs to the current mapped asset page, it
reconstructs U from the OS-returned map base and the low 13 offset bits. It
does not retain a pointer between calls. An unmapped slab or a different page
uses `AssetPointer`, preserving its mapping and error behavior. Nested calls
and resource switches still unmap through their existing paths.

This removes the general address helper's register save/restore on common
bytecode reads, with no additional private data. The mapped-fetch checkpoint used 6,509 bytes for `wbexec`;
`wbgame` used 20,833 bytes with a 24,572-byte private allocation. The
Makefile explicitly tracks `objs/platform/wildbits-logic.asm` for the game target so edits
cannot accidentally test a stale game binary.

Commands 1–17 now dispatch to shared CoCo/native variable and flag handlers.
Operand collection remains bounded by the native VM before those handlers
run. Flag storage is an explicit owner adapter. The current code budgets are
6,906 bytes (`wbexec`) and 21,235 bytes (`wbgame`), with unchanged private data.

Unsigned comparison/isset predicates now use the same bodies as CoCo. Boolean
return adapters retain native B results and CoCo A results. The condition
catalog provides both owners' operand descriptors/counts; remaining external
predicate implementations are still separate.

### Packed picture resources — 2026-10-06

The asset loader now accepts the picture-only header flag `$80`. This encoding
stores bytes high nibble first, except the color operand after `$F0` or `$F2`,
which occupies one nibble. It uses the existing bounded input and mapped output
callbacks and reuses LZW scratch; the codecs execute sequentially. Expanded
length must match the header, an end marker must be present, and only a final
unused low nibble is permitted as padding. Other resource kinds reject this flag.

All 443 packed pictures in Gold Rush, King's Quest IV, Leisure Suit Larry and
Space Quest 0 match both CoCo's actual `RenderPicStrip` and an independent host
oracle. Tests also cover relocation, short I/O, malformed lengths/truncation,
trailing bytes, wrong resource kinds and allocation/mapping/service failures.
That packed-picture build retained 24,570 private bytes and used 22,466 code bytes.

King's Quest I MAME startup, inventory, restoration, movement and interrupt
cleanup passed at `/tmp/sierra-packed-kq1-movement`. This does not establish
playability of those other titles: Larry's startup separately reaches the
unimplemented `add.to.pic` opcode 122 (`$7A`), as shown by the temporary trace
build at `/tmp/sierra-packed-larry-trace`.

### Static picture cels and input cancellation — 2026-10-06

`add.to.pic` (122) and `add.to.pic.v` (123) now resolve seven operands into a
stack-local 43-byte object record, select the cel through the existing resource
interface, and paint it through the existing sprite renderer. They restore an
existing background before painting, save the resulting static picture, then
recompose animated objects. The initial picture needs no restoration until a
saved background exists. The temporary object has a non-ego identifier so its
visibility cannot overwrite flag 1. No animated object record is borrowed.

Zero priority uses the baseline's default band. Control priorities 0–3 stamp
only the rectangle perimeter, bounded by the cel height and the beginning of
that band; larger legal control values omit the box. The shared clipping rules
handle the right and top boundaries. Malformed priority/control values, offscreen
baselines, invalid loop/cel selection and replay-log overflow return an error.
The canonical view/loop/cel/position/priority tuple is recorded in the existing
bounded replay log, including variable-resolved operands.

`cancel.line` (138) clears pending parser input and redraws an enabled prompt
row, preserving the previous submitted line and unrelated flags. Its redraw
uses the existing parser routine. Tests execute 36 static draws and compare
every visual and priority byte after another sprite is drawn and erased; 36
cancellation calls check complete private-state, row, history, stack and code
guards at two load addresses. All 1,024 command routes and KQ1 MAME acceptance
checks pass. The main game is 22,832 code / 24,570 private bytes.

An isolated diagnostic build gets Larry past the earlier startup failures to
its age-verification question. Persistent question windows and `close.window`
are being verified separately; this is not a full-game acceptance claim.

### Persistent print windows — 2026-10-06

Flag 15 now makes an ordinary `print` return without waiting and is cleared
once consumed, matching CoCo's print-only behavior. The displayed character
and color planes remain active until `close.window` (169), another print, or
`show.pic` closes them. Blocking print and line-input dialogs retain their
existing behavior.

The original 2,000-byte text/color plane is saved inside the process's owned
framebuffer, past its 76,800 visible pixel bytes. Block nine has 5,120 unused
bytes after offset 3,072; the backup needs 2,000. Frame clearing now stops at
the last visible byte. The backup survives decompression and picture staging
that reuse `resourcecommands`. A dialog state value distinguishes this held
window from a blocking modal, without adding private storage or allocations.
Closing releases the current asset/picture mapping before mapping that tail,
restores the plane, and recomposes the scene. Failed map/unmap calls preserve
an error for normal ownership cleanup.

Tests verify continuation with no keyboard input, flag consumption, every
restored character/color byte and pixel, LZW workspace reuse, full redraw,
nested blocking print, repeated close, and errors during both saving and
restoring. Existing gameplay/modal tests and all 1,024 dispatch destinations
pass. The game is 23,009 code / 24,570 private bytes.

### Pictures larger than the private command window — 2026-10-06

The game decoder now uses a logical source offset instead of a pointer into
`resourcecommands`. It refills that existing 8-KiB buffer at source-page
boundaries, releases the output-picture mapping before mapping the owned
resource slab, and releases the source before plotting resumes. The final
chunk copies only the remaining decoded bytes. Source length and end-marker
checks cover the full 65,535-byte resource limit, and the current logic asset
is restored before execution continues after drawing.

Two shared helpers previously reread `X-1` despite using a bounded read
callback. They now use the callback's returned/retained byte: Y-command
recognition uses B, and relative-line steps use `decodevalue`. CoCo's
contiguous-reader instructions are unchanged. The native probe retains the
last byte too, so both native owners use the same bounded-reader contract.
This retains direct plotting calls and adds no private storage or platform
files. The game is 23,072 code / 24,570 private bytes.

Tests verify commands/operands on both sides of 8/16-KiB boundaries, a valid
65,535-byte stream, truncated input, map/unmap failures, and resumption of the
original logic. All 23 actual packed pictures larger than 8 KiB in King's
Quest IV and Space Quest 0 match CoCo's reference pixels. KQ4 picture 5
(10,288 decoded bytes) also passes every-pixel/two-terminal MAME checks at
`/tmp/sierra-stream-large-picture-terminals`; this synthetic interpreter
scenario does not establish full KQ4 adventure playability.

### Object update control — 2026-10-06

The actual Larry intro reached the street-loading logic but stopped on opcode
58 (`stop.update`). Native object commands now implement `stop.update` (58)
and `start.update` (59) by clearing or setting bit `$10` in the existing
43-byte object record. The shared motion scheduler already tests that bit,
so stopping freezes motion and cel progression. The renderer deliberately
continues to collect the visible object: stopping must not erase it.

`force.update` (60) restores the immutable picture background, composes the
current object records and presents the result. It never calls the motion or
animation scheduler. Asset and picture mappings are released before drawing;
normal error propagation and process cleanup remain in charge of failures.
All three commands reject an out-of-range object index. Stop/start also work
in the bytecode probe; force requires the game presentation owner.

These commands extend the existing object component and command catalog,
without new platform files or private storage. CPU tests check frozen/resumed
motion, retained sprite pixels, an identical force-redraw frame and object
record, invalid indices, and all 1,024 dispatch destinations. All 56 CoCo
binaries rebuild byte-identically. The game is 23,152 code / 24,570 private
bytes, within the 23,808-byte code budget.

The MAME harness now has a `--larry` scenario for the original age quiz,
walking outside Lefty's, the exact `look` response, dialog dismissal and
interrupt/free-memory cleanup. `--larry-enter` also verifies opening the door,
entering the bar and its interior description. Both pass with the production
binary on real Wild Bits drivers. These check opening gameplay sequences;
it does not establish completion of Larry or support for save/restore/audio.

### Cel row preparation — 2026-10-06

The native renderer clears only the validated cel width in `spriterow`,
instead of all 160 staging bytes for every row. Plotting, mirroring and
cache copies already stop at that width. Short RLE rows still start with
transparent pixels; data beyond the cel width is never read. The renderer
also computes `160 * Y` once per valid row and adds the column for each
pixel, instead of multiplying again for every opaque pixel.

The row offset reuses `dirtyobject`: background erasure finishes before
cel rendering begins, and its cursor is inactive throughout that draw.
It stores an integer offset, never a mapped pointer. Intercepts do not use
this scratch word. Private storage remains 24,570 bytes and the game is
23,162 code bytes. No platform files or runtime platform dispatch were added.

Both changes pass every castle pixel, transparent/mirrored/clipped/occluded
sprites, large-cel erasure fallback, static-picture drawing and persistent
dialog restoration checks. In the same Larry MAME 400-frame window, measured
movement changes from about nine to ten AGI pixels after narrowing the clear;
hoisting the row multiplication gives the same ten-pixel result. This is a
small measured sample, not a claim that movement performance is solved.

The 50 native check programs pass across the split regression run and stable
gameplay rerun (`/tmp/sierra-update-native-check-summary.json`). The final
row-address change is additionally checked in isolation by the pixel, sprite
erasure, static-picture and persistent-window tests; the production binary
is byte-identical to that tested prototype. All 56 CoCo binaries were verified
unchanged for the object-command work, and these subsequent edits affect
only the native rendering component.

The porting guide's signal-driven clock addresses frame overruns. The current
test OS's `SOL_IRQSvc` does call `F$Send`; the earlier claim that this delivery
was absent was incorrect. Multi-process ownership still needs verification:
the driver schedules one table entry per IRQ, permits repeated line numbers,
and removes entries by line rather than caller PID. Before two games both
register line zero, verify that each receives every frame and that one game
exiting cannot remove the other's registration. The application does not
read hardware timers or kernel globals to compensate.

### Previous-command input recall

Native `echo.line` (137) now follows CoCo's `input_echo`: when input is
accepted and the previous raw command is longer than the current input,
it appends the previous command's remaining suffix. A typed prefix stays
intact. Disabled input and an equal or longer current line are unchanged.
The native editor caps the recalled line at 38 bytes, terminates it, and
rebuilds the prompt row. History, parser flags and adjacent private data
remain untouched. This uses the existing input component and adds no
private storage or platform files.

`check_cancel_line.py` executes both editing commands at two module
addresses, with enabled/disabled input, three prompt rows, differing typed
prefixes and history lengths through 39 bytes. It checks the full private
area, immutable code and stack guards. The dispatch check independently
verifies the command is game-only; the bytecode probe retains its explicit
unsupported-command response.

### Shared raster-clock prerequisite

The stock test driver delivers only one registration per raster interrupt.
Two processes requesting line zero therefore split the frame ticks. A private
MAME probe confirmed this: the paired three-second clients counted 62 and 61
signals; with broadcast delivery they counted 124 and 122. These intervals
start at an arbitrary calendar-second phase, so the raw counts are comparative,
not exact elapsed-time rate measurements.

The isolated NitrOS-9 branch `codex/wildbits-sol-frame-clock` fixes shared-line
delivery and PID-scoped removal. It also fixes mute traversal, masks table
changes against interrupts, handles empty-table operations, and retains
`E$DevOvf` on a ninth registration. A six-second client continued receiving
signals after a three-second peer unregistered: 349 versus 171 signals.
The driver keeps its existing eight-entry interface and static layout.

`tests/check_sol_driver.py --source PATH/TO/SOLdrv.asm` compiles and exercises
that driver on the actual 6809 CPU. Optional `--mame`, `--disk`, `--firmware`
and `--output` arguments install only that module into a private boot image
and run `tests/probes/wbsol.asm`. The MAME check verifies concurrent tick
counts, the surviving owner after peer exit, and identical free-memory maps.
`UPDAT.` opens the clock non-exclusively; adding OS-9's `SHARE.` bit requests
exclusive access and causes a second open to fail with `E$DevBsy`.

The production engine now uses the shared raster service when its capability
check succeeds. `I$GetStt SS.SOLIRQ`, with X initially zero, reports capability
bits in X: bit zero means shared-line broadcast, bit one means PID-scoped
removal, and bit two means a public line-zero frame counter in Y. The current
game requires all three bits. Legacy drivers leave X zero; the engine
closes that optional path and keeps its existing sleep-based pacing.

The current gate registers `S$Wake` (1), rather than a user signal for every
frame. It samples the low byte of the driver's public frame counter through
`I$GetStt SS.SOLIRQ`. The driver advances that 16-bit counter once per line-zero
IRQ, including muted owners; other raster lines do not advance it. Wake
signals can be replaced by keyboard interrupts in NitrOS-9's single pending-
signal slot. The earlier $83 intercept counter could block Ctrl-C: the kernel
rejects another non-wake pending signal, and the keyboard driver does not retry
that send. Real emulator traces showed frame signals arriving without Ctrl-C;
the wake/counter implementation restores successful cleanup in one and two games.

Variable 10's 50-ms delay remains three raster ticks per unit. The gate
subtracts elapsed credit and waits for a wake only when more time is needed.
A long frame therefore does not add the entire delay afterward.
Credit is capped at one extra cycle to avoid an unbounded catch-up burst.
Zero delay still yields. Terminal background handling mutes that process's
clock entries; foreground return unmutes and discards paused credit. The
calendar clock still supplies AGI seconds, and modal Pause rebaselines both
clocks. Exit unregisters line zero before closing the owned path.

At the initial signal-gate checkpoint, the six added private bytes brought
storage to 24,576 bytes, exactly three pages; code was 23,616 of the
23,808-byte limit. Later bounds/text changes below reduce that storage. No platform
files, mapping windows or allocation pages were added; timing belongs to
`platform/wildbits-timing.asm`.

The actual-CPU checks cover fallback and capability policy, delay values
through 255, counter wrap, bounded credit, signal waits, zero-delay yield,
owned registration/cleanup, foreground mute/unmute with register preservation,
modal reset, abort and the actual RTI path with an unrelated interrupted DP/U.
All 4,118 original CoCo/native clock cases also pass. The old-driver gameplay
path retains every reference pixel and passes sprite, input and cleanup tests.
MAME accepts Larry's quiz, street walking, messages and cleanup; KQ1's real
menu Pause and later commands; and concurrent Larry/KQ1 terminal switching,
independent inventory input and exits with free-memory maps restored.

Larry's same 400-frame movement window changes from 9.976 to 11.216 AGI pixels
with the signal gate. This is a modest sample and movement remains slow; the
next performance work needs a profile of logic, sprites and presentation.

A bounded MAME debugger profile of 26 Larry cycles confirms that the remaining
slowdown is mainly graphics. Median phase costs at the configured 12-MHz CPU
are about 30 ms for logic, 138 ms for motion/input (including old-sprite
background restoration), 143 ms for sprite composition, 165 ms for bitmap
presentation, and 59 ms for text. The frame gate and calendar clock take about
0.24 ms in these already-overrunning cycles. These are CPU-cycle differences
between actual production entry points and include intervening OS work;
they are not isolated instruction-only timings. The profile artifacts are
`/tmp/sierra-larry-clock-profile-mapped/profile.log` and `phases.json`.

### Bounded old-sprite restoration spans

Old sprite rectangles are now copied one row span at a time instead of calling
`AssetPointer` or `PicturePointer` for each pixel. A span is bounded by both
the row's remaining width and the mapped page's remaining bytes. At an 8-KiB
boundary the renderer reconstructs the next address through the OS mapping
API. It never retains a foreign pointer across a kernel call. The source is
staged privately before the destination is mapped, preserving the one-window
rule and the immutable background.

Source/destination mapping failures unwind the two-byte span count before
returning the original error. Regression cases deliberately fail after the
first two bytes of a row at offset 8190, on both copy directions. Exact-8K
rectangles, larger fallback rectangles, clips, offscreen sprites, every castle
pixel, static decorations and persistent dialogs also pass with complete
cleanup. The change adds 48 code bytes and no private bytes; the engine is
now 23,664 code / 24,576 private bytes.

Larry's same 400-frame walking sample rises from 11.216 to 13.401 AGI pixels.
The repeatable `check_wbgame_mame.py --larry --profile` option records current
production entry points from its symbol map, validates the mapped module
header/name, and logs bounded phase timestamps. It writes `profile.json` and
`profile-events.json` alongside normal gameplay artifacts. The selected
MAME turbo core's E-clock is 12.5875 MHz (50.35 MHz MC6809 input divided by
four); the earlier nominal-12-MHz figures slightly overestimate milliseconds.

The verified profile at `/tmp/sierra-larry-erase-profile-verified` contains
32 samples: motion/input median falls from 1.651 million to 0.473 million CPU
cycles (approximately 131 to 38 ms at that E-clock). Composition, presentation
and text still dominate at about 140, 157 and 56 ms. Terminal-name validation
accounts for only about 0.9 ms, so removing its two syscalls would not address
the main remaining presentation cost.

### Encoded mapping-cache pages

The picture and resource mapping caches now retain the high three bits of
the logical address (`offset & $E000`). A repeated access compares those bits
directly; the five right shifts needed to calculate a physical 8K block occur
only when that mapping changes. The bytecode-fetch fast path uses the same
encoding. Offsets, error propagation, ephemeral pointers, ownership, and
unmapping behavior remain unchanged.

The native picture/view comparison, split-row and exact-8K sprite tests,
source/destination mapping-failure cleanup, and common executor checks pass.
The original Larry quiz, walking, messages, and free-memory restoration pass
in MAME. The bounded profile measures about 26.5 ms for logic and 137.6 ms
for sprite composition, compared with 27.4 and 139.7 ms before this change.
Walking distance remains 13.4 pixels in the 400-frame sample: this is a small
CPU saving, not a demonstrated improvement in walking speed. Production
code is 23,665 bytes; private storage remains 24,576 bytes.

The MAME `--profile` run also records `profile-sprites.json`: each cel's
position, size, draw/update flags, view, loop, and cel at the actual rendering
entry. Larry's street sample contains five visible objects, including an
8-by-68 animated cel at x=134 and baseline 67, two wider animated cels
around baselines 83–84, a 15-by-40 cel at baseline 131, and Larry near
baseline 156. Their combined vertical coverage explains why nearly all
eight-pixel bands are copied despite relatively narrow changed regions.
This trace is diagnostic; it does not skip stationary objects or change
composition order, transparency, or priority handling.

### Cached-access register preservation

`PicturePointer` and `AssetPointer` preserve D on every call and save X/Y
only on the slower path that invokes mapping services. A cache hit leaves
X/Y untouched without pushing and popping those four bytes. Both mapping
success and failure restore X/Y before returning; the failure path retains
the existing error and releases every owned mapping during exit.

The native picture/view comparisons and exact-8K/split-row sprite tests
pass, including failures while reading and writing restoration spans.
Resource tests pass for relocated modules, exact 16KB input, 65535-byte
LZW output, malformed input, and allocation/map/unmap/I/O failures. The
long resource test requires a 900-second emulated-time allowance; its
earlier 300-second run disconnected when that limit expired.

Larry's real-game profile measures sprite composition at about 135 ms,
and walking covers 14.3 pixels in the same 400-frame sample. Dialogs and
free-memory restoration still pass. This remains slow overall: display
copying takes about 157 ms and text about 56 ms per sampled cycle. The
production module is 23,677 bytes with 24,576 bytes of private storage.

### Narrow damaged-region presentation

The eight-pixel dirty bands now also retain the union of the horizontal
footprints erased and painted since the previous successful presentation.
Bounds round outward to even AGI columns so the existing word copies remain
aligned. Full pictures, first bitmap allocation, and modal restoration
retain the complete 160-column range. Each band's rows are staged privately
with the picture stride removed, converted at the bounded width, and copied
to the matching framebuffer columns. The source mapping is closed before
any destination mapping; cached destination mappings remain owned only
while copying that band. Failed presentations retain their damage.

The two bound bytes replace the resource pointer's redundant saved-offset
field: its original offset is already on the stack and remains there across
the mapping miss path. Private storage remains 24,576 bytes; code is
23,765 bytes. The CoCo backend is unchanged.

Checks cover complete picture/view pixels, explicitly presented moving and
erased sprites, odd widths/columns, columns above 127, split rows, exact-8K
staging, larger-cel fallback, mapping failures, static decorations, persistent
dialog restoration, and the full 65535-byte resource case. The real Larry
run measures presentation at about 117.5 ms instead of 157 ms and movement
at 16.1 instead of 14.3 pixels over 400 frames. Two simultaneous Larry/KQ1
games pass terminal switching, independent inventory input, survivor-after-
peer-exit, and Larry-only/final memory restoration using the documented
emulator-only expanded-memory kernel.

### Per-band bounds, bounded text rendering, and safe clock wakeups

Each dirty band now has its own rounded left/right bounds. A tall, narrow
cel therefore no longer forces unrelated columns to be copied above or
below wider cels. Both erased and newly painted footprints update those
bounds; full redraws cover all 160 columns, and a successful presentation
resets each pair to the empty range. Native presentation no longer reserves
the unused 160-byte `rowinput` buffer. Its 42-byte bounds table replaces
part of that storage, leaving private data below the previous allocation.

Repeated direction input now matches CoCo's event processing: pressing the
same direction again sets direction zero. The actual CPU check verifies
Right, one movement step, Right, then no further movement. The real Larry
harness uses this to stop him before checking dialog restoration. Without
stopping, faster movement legitimately carried him into another room.

Full-screen and bounded text updates use the same scanline renderer. A
bounded update retains its initial column and exclusive ending cell; row
scans and glyph writes stay inside those limits. Its saved limit replaces
two fields used only by the removed pixel-at-a-time glyph routine. This
reduces code duplication and speeds bounded editor/inventory painting.
Complete pixel, persistent-dialog, parser, and 276 cancel/echo-line checks
pass.

The optional wake clock requires the public counter capability added by
NitrOS-9 commit `edaa2283` on `codex/wildbits-sol-frame-clock`. It samples
through the service API, never through kernel globals or direct hardware
registers. Foreground/modal rebasing samples the current counter before
discarding paused credit. Service errors propagate; older drivers use the
existing sleep fallback. The counter has 37 actual driver cases, and the
gate has 25 cases including unsupported capabilities, wrap, bounded credit,
sample errors, abort, ownership cleanup, and unrelated RTI signals. All
4,118 CoCo/native calendar-clock cases also pass.

With all changes combined, the real Larry profile measures picture copying
at about 54.9 ms, compared with 157 ms before horizontal bounds. Walking
covers 20.5 pixels over the same 400 frames, compared with 16.1 using a
single horizontal union. Sprite composition still takes about 134 ms and
full text about 56 ms. Original messages, stop behavior, Ctrl-C, and final
free memory pass. Simultaneous Larry/KQ1 games also pass terminal switching,
independent input, peer exit, survivor operation, and final memory cleanup
using the documented emulator-only expanded kernel.

Production code is 23,679 of 23,808 bytes, and private storage is 24,459 of
24,576 bytes. The existing 26 platform assembly files are retained. These
measurements establish emulator behavior; physical Wild Bits performance
and complete game completion remain separate acceptance work.

### Sprite row clipping

The renderer calculates a cel row's clipped column count and first logical
pixel once, before entering the pixel loop. It retains the original cel
width for decoding, mirroring, and saved-footprint metadata, so clipping
does not silently truncate resource validation or change mirrored pixels.
Offscreen rows still decode through the bounded resource path. The existing
restoration scratch column-count byte is reused after background restoration
has finished; no private bytes or platform files are added.

Pixel comparisons pass for transparent/mirrored/clipped/occluded cels,
offscreen positions, static decorations, movement and erasure. Added
independent priority tests cover long control-nibble columns (0/1/2),
intervening low/high priority pixels, and the picture bottom at priorities
3, 4, and 15. A priority-cache experiment passed those tests but did not
improve the real-game profile, so that implementation was removed.

Real Larry composition measures about 116.3 ms instead of 134 ms, and
movement covers 21.4 pixels over 400 frames. Messages, stopping, Ctrl-C,
and unchanged free memory pass. Code is 23,688 bytes and private storage
remains 24,459 bytes. Picture copying remains about 55 ms and text about
56 ms per sampled cycle.

### Text damage and background-safe framebuffer ownership

Ordinary picture presentation now repaints text only where its picture
bands were damaged. The persistent prompt outside the picture is retained
when its characters and colors are unchanged. `ParserDrawInput` snapshots
that row into the first 80 bytes of idle glyph staging, rebuilds it, and
compares both planes. Changed characters or colors request a full text pass.
This is transient scratch storage, not a second persistent text plane.

`presentationconfigured` bit 0 indicates completed display configuration;
bit 7 requests full text painting. Initial display setup, foreground return,
and clearing the owned bitmap for a modal restoration force a complete
text pass. Direct text updates and bounded editor/inventory updates also
retain their full or bounded rendering behavior. Successful presentation
clears the force bit and band damage; errors retain both. One private byte
selects ordinary damage-limited rendering versus a full/bounded call.

If visibility changes while text has a framebuffer page mapped, foreground
handling now closes that mapping before muting the clock and sleeping.
Unmap failure returns the original error without sleeping or changing clock
ownership; exit can retry its normal cleanup. Actual CPU checks cover both
success and failure with register, stack, and private-memory guards.

The input suite now has 312 actual calls, including unchanged prompt rows
and color-only changes at rows 0, 23, and 24. Complete game pixels and
persistent dialogs pass. Larry passes messages, movement, same-direction
stop, Ctrl-C, and free-memory restoration. Original KQ1 passes repeated
commands, menu Pause, frozen/resumed clocks, and modal restoration. Two
independent Larry/KQ1 games pass terminal switching, separate inventory
input, survivor operation after peer exit, and final memory recovery using
the documented expanded-memory emulator kernel.

The bounded Larry profile now measures text at about 1.7 ms instead of
56 ms during unchanged-input gameplay. Movement covers 26.8 pixels over
the same 400 frames, compared with 21.4 before text damage tracking.
Sprite composition remains about 116 ms and picture copying about 55 ms.
Production code is 23,808 bytes, exactly its conservative limit; private
storage is 24,460 bytes. This requires recovering code space before adding
more interpreter features. No platform assembly files were added.

### Diagnostic exports and sprite mapping fast path

The interactive build excludes the raw picture and variable-stream exporters.
They remain in the diagnostic probes, where they are used to compare decoded
resources with reference output. This removes 199 unreachable code bytes without
changing the probe binaries or the game's private ownership state.

Sprite composition now addresses an opaque pixel directly when its encoded 8 KB
page already matches the owned mapping. The logical offset is still recorded for
priority searches. Page changes use PicturePointer, including its error handling
and register preservation. The fast path keeps no pointer across an OS call and
adds 24 bytes, leaving the game at 23,633 of 23,808 code bytes and 24,460 private
bytes. No platform files were added.

The native CPU test passed all reference picture pixels, sprite clipping,
mirroring, priority searches, map errors and cleanup. The decoder exporter probe
also passed. An original Larry MAME run passed its quiz, walking, exact dialog
glyphs and interrupt cleanup with unchanged free memory. Its 400-frame walking
distance remained 26.8 AGI pixels; median composition fell from 116.2 to 114.0 ms
over 56 and 57 samples respectively. This is a small measured rendering saving,
not an observed increase in that walking-distance measurement.

### Persistent rectangular text clearing

Wild Bits now implements AGI opcode 154, `clear.text.rect(top,left,bottom,right,color)`,
in the existing text component. Bounds are inclusive. Each selected cell becomes
an opaque space: color zero clears black, and a nonzero color clears white in
graphics mode. The argument order and graphics-mode color rule match the
[ScummVM AGI command implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/op_cmd.cpp)
and its [text background conversion](https://github.com/scummvm/scummvm/blob/master/engines/agi/text.cpp).
The cell planes retain the result across picture refreshes. Rectangles outside
25 rows or 40 columns, or with reversed bounds, return OS-9 `E$IllArg` (187)
before changing cells. This follows the native renderer's checked-input policy.
The command uses two stack bytes and adds no private data or platform files.
CoCo retains its existing handler; the diagnostic bytecode probe retains its
explicit unsupported response.

The CPU integration test compares every framebuffer pixel for five valid
rectangles, including full-screen and bottom-right clearing, and four invalid
rectangles with exact error codes and unchanged pixels. Neighboring glyphs
and refresh persistence are checked. All 1,024 dispatch cases passed. The
updated game also passed simultaneous original Larry/KQ1 play, independent
input and inventory, terminal restoration, surviving-peer behavior and final
free-memory restoration in MAME. The build uses 23,739 code bytes and 24,460
private bytes, leaving 69 bytes in its current code budget.

### Code-space preparation for persistence

`clear.lines` now converts its three command-local arguments into a full-width
rectangle and uses the same checked cell-clearing loop as `clear.text.rect`.
The exact-pixel integration suite passed both commands after consolidation.
This removes 48 code bytes without changing private storage, leaving the
interactive game at 23,691 code bytes with 117 bytes available.

`tests/check_cold_module_mame.py` provides a separate diagnostic for the next
code-space decision. It builds an owner padded to the production game's exact
module size and private allocation, and a small position-independent OS-9
subroutine. The owner uses public `F$Load`, copies the validated-size module into
private scratch, unlinks it, and executes the relocated entry. It then allocates,
maps, writes, unmaps and releases one RAM block at the returned `$8000` window.
Both sequences run twice. The MAME check requires the success marker and exactly
identical before/after free-memory reports. It passed with the current
23,691-byte owner and 24,460-byte private area.

Run the diagnostic with the same `--mame`, `--disk`, and `--firmware` paths as
the game tests and a fresh `--output` directory. It creates its assembly sources,
modules, disk and firmware copies inside that output directory; it installs
nothing in the production game. This proves that a small cold routine can leave
the normal mapping window available at this footprint. It does not implement
save/restore, establish a save-file format, or prove that a larger persistence
module fits the available private workspace. Those must be checked separately
before adding the loader to the game.

All 56 CoCo interpreter modules rebuilt byte-identically in isolated output
directories after the shared command-table change and native clearing
consolidation. Existing game-directory binaries were left untouched.

### Single text-cell address calculation

Persistent text writes now compute their cell address once and store the color
1,000 bytes beyond the character. An assembly-time assertion protects the
matching-plane layout. The exact-pixel game suite passed glyph colors, wrapping,
text clearing, rectangles and modal restoration after this change. It removes
17 code bytes without changing private storage: 23,674 code bytes and 24,460
private bytes, with 134 bytes of code space available.

An exact whole-scene sprite-history experiment was tested and removed. Although
its CPU pixel tests and original Larry MAME checks passed, walking scenes changed
on each cycle; median composition rose from 114.0 to 115.3 ms and the walking
distance stayed 26.8 AGI pixels per 400 frames. The current game retains the
measured mapped-pixel optimization and does not allocate sprite-history state.

### Cold-code workspace restriction

The loading probe establishes module and mapping-window behavior, not a general
UI overlay workspace. A tested modal-code experiment was removed after MAME
exposed scratch overlap: `fillstack` also contains four 512-byte formatter source
frames, the 2,048-byte formatter output, inventory-file staging and transient
dictionary groups. A modal routine calling the formatter can overwrite its own
code there. Dialogs remain resident in the verified game. A future persistence
routine may use that space only while those consumers are inactive and must
return before formatting or rendering resumes. The current build requires
`wbgame` and `wbfont`; it has no UI helper-module dependency.

The current resident build passed the original Larry age quiz, opening the
door, transitioning into Lefty's bar, showing and dismissing the interior
description, interrupt cleanup and unchanged free memory in MAME.

### Owned text screens and graphics restoration

`text.screen` (106) now uses the existing terminal-owned bitmap as a 40-by-25
text screen. It fills the persistent character plane with spaces and the color
plane with the selected background; `display` then draws through the same font
and cell renderer used by graphics overlays. The 200 text scanlines occupy the
top of the 240-line bitmap. The remaining 40 scanlines retain the black border.
The combined game picture remains allocated underneath the text screen.

`graphics` (107) closes any active window, clears the text cells, composes the
current objects, and restores the picture. Bit 6 of `presentationconfigured`
requests a full bitmap clear on this transition. The clear consumes that bit
and marks every picture band dirty; bit 7 still requests a full text repaint.
This removes text outside the picture without changing terminal ownership or
writing display registers directly. During text mode, normal game cycles update
logic and input while painting text instead of composing the picture.

`clear.text.rect` and `clear.lines` share the existing rectangle loop. Graphics
mode retains the black/white clearing convention; text mode clears to black.
All of this lives in the existing graphics, text UI and object components; no
new platform assembly files or helper modules are needed. The resident build
uses 23,774 code bytes and 24,460 private bytes, leaving 34 code bytes.

The CPU integration suite checks all text cells and glyph pixels with four
background colors, three-cycle persistence, repeated graphics restoration and
text-mode rectangle clearing. Its simulated-time allowance is 1,800 seconds
for the enlarged suite. The real-driver MAME mode test checks every displayed
pixel on the second terminal, restores the first terminal unchanged, then
checks independent exit, relaunch and identical free-memory maps. All 56 CoCo
modules rebuilt byte-identically after the command-table change.

### Native branch encoding reduction

181 nearby branches and calls in the existing Wild Bits backend now use the
6809 short encodings. They target the same labels and preserve the same register
and condition-code behavior. Two resource branches remain long because their
targets are farther away in the diagnostic owner's layout. All production and
diagnostic owners assemble successfully with range checking. Shared and CoCo
sources are unchanged. This recovers 290 resident code bytes: `wbgame` uses
23,484 code bytes and the same 24,460 private bytes, leaving 324 code bytes.

Validation passed all 1,024 dispatch cases, the full exact-pixel game suite,
resource loading/error/cleanup checks (including 65,535-byte expanded assets),
and the vocabulary/parser suite. The original Larry MAME test passed its quiz,
opening the door, entering Lefty's bar, displaying and dismissing its interior
description, interrupt cleanup and unchanged free memory. No additional
platform files or private buffers were introduced.

### Staged cold-code file I/O

The cold-module diagnostic now accepts `--file-roundtrip`. In this mode the
private scratch area is 4,096 bytes, matching the game's available cold-code
workspace. The owner loads a bounded helper, copies it there, unlinks it and
executes it twice. The helper writes 32 binary bytes through public OS-9 file
services, changes its live destination, reads into a separate stage, validates
the entire stage, and then commits the restored bytes. A second read starting
halfway through the file returns only 16 bytes and is rejected without changing
the restored destination. The helper closes every opened path.

MAME passed both helper invocations, subsequent `$8000` mapping reuse and
identical free-memory reports at the 23,484-byte production code footprint and
24,460-byte private allocation. The harness extracts the resulting file with
binary `os9 copy`; `os9 list` transforms control bytes and cannot validate a
binary save. This is an I/O prerequisite, not a game save format or a completed
implementation of `save.game`/`restore.game`. No new runtime dependency is
installed by this diagnostic.

### Picture and discard replay records

The native replay buffer now distinguishes loading a picture from drawing it.
`draw.pic` reserves type 4 plus the picture identifier before decoding, matching
the CoCo restore stream. Successful picture and view discards reserve type 6
or 7 plus the resource identifier before releasing the cache entry. A redundant
discard of an absent resource emits nothing. `ReplayPush` preserves the cache
entry pointer; recording never stores a physical block number or mapped address.
If the buffer is full, the command returns `E$MemFul` before the destructive
draw or release begins. Normal interpreter cleanup still releases all owned
resources. Existing static-sprite records remain type 5.

The view CPU checks cover immediate and variable arguments, redundant discards,
record order and limits of one, three and four records. Picture checks verify
exact records across three cycles, drawing twice with too little replay space,
and discarded pictures that remain visible until a new draw. Replay setup in
the cycle fixture runs once: `script.size` resets the buffer whenever invoked.
The original Larry MAME room-transition check passed with the added records.
These records prepare reconstruction for save/restore; the two commands remain
unimplemented. The resident build uses 23,506 code bytes and 24,460 private
bytes, with 302 code bytes available.

### Overlay pictures

`overlay.pic` (28) now uses the picture command path with replay type 8. Its
operand remains a variable containing the picture identifier. It resets decoder
color/mask/pen controls while retaining the existing combined visual/priority
pixels. An overlay without an existing picture allocates and clears the normal
blank picture first. Ordinary `draw.pic` still releases and clears its picture.

If animated objects have touched the scene, overlay first restores their saved
background and forgets their previous footprints. The overlay's cache entry is
kept on the stack while that restoration temporarily selects background and
root-logic assets. The decoder then selects the overlay resource again. The
updated background is saved before the next object composition, so moving or
erasing a sprite preserves overlay pixels rather than retaining old sprite
pixels in the background. All mappings follow the existing one-window rules.

CPU checks compare every visible pixel for blank overlays, visual/priority
updates that occlude a sprite, subsequent movement and erasure, exact replay
records and malformed-resource cleanup. The MAME harness supports `--overlay`
with `--interpreter`, optionally combined with `--text-modes`; it installs a
small diagnostic overlay and derives its expected horizontal/vertical pixels
independently of the decoder. No new platform files were added. The build uses
23,563 code bytes and 24,460 private bytes, with 245 code bytes available.

The final full game CPU suite and all 1,024 dispatch cases passed. The combined
`--overlay --text-modes` MAME run passed every displayed pixel on both terminals,
restoration of the overlaid castle after text mode and focus changes, independent
exit, relaunch and identical free-memory maps. All 56 CoCo interpreter modules
rebuilt byte-identically in isolated output directories.


## Cold save and restore

AGI commands 125 and 126 use `objs/wbstate.asm`, an optional subroutine module
built by `wildbits.mk`. This is file persistence code, not another interpreter.
The game loads it only when a save/restore dialog has collected a filename,
checks its private-layout ABI, copies it into the process's 4 KiB `fillstack`,
and unlinks the original module before executing the copy. Normal movement,
logic dispatch and rendering do not load or call this helper.

The entry point receives a mode, filename, private-data base and relative
callback table. The shared `STATE_SCHEMA` in `wildbits-runtime.asm` defines the
persistent field order and the helper's private-layout fingerprint. It contains
variables/flags, strings, object records, inventory rooms and controls, key and
menu definitions, screen controls, motion constraints, random/replay state and
both native text planes. Unloaded inventory controls are normalized to zero.
The callback table lets the helper reuse the existing resource and presentation
owners without absolute module addresses or duplicate engine implementations.

The file starts with an 18-byte big-endian header: two-byte `WS` magic, version
1, picture-present flag, two-byte payload length, CRC-16/CCITT of the payload
(seed $FFFF, polynomial $1021), eight-byte game ID, root logic number, and a
reserved zero byte. The payload has 7,687 bytes of logical fields followed by
32 five-byte cache recipes. Each recipe has resource kind plus one (zero means
empty), ID, two-byte scan offset and a reserved zero. A present picture adds
26,880 bytes in the native combined priority/color format. The largest file is
34,745 bytes. Physical block numbers, open paths and mapped addresses never
appear in the file. This format is specific to the native port.

Save creates a new file and streams the fields, recipes and static background
through public OS-9 file calls. Picture slabs are mapped only long enough to
copy a bounded chunk into the helper's private buffer, then unmapped before
I/O. The helper rewrites the header with its completed checksum and closes the
file. Existing filenames are rejected; a failed save deletes only a new partial
file that this operation created.

Restore has two phases. First it reads into owned staging slabs, checks the
header, identity, exact length, checksum, field bounds and cache recipes, and
rejects trailing data. It retains the validated stage and asks the logic loop
to unwind. At the root, with no nested frame left, it releases the old caches
and images, reloads resources by kind/ID, derives logic bounds from their new
bytes, restores the logical fields and copies the static pixels into a new
owned picture. The staging slabs are released before allocating the permanent
background copy. It then composes objects and text through the normal owner.
The restored root starts at its saved scan offset, with AGI restore flag 12 set
and transient parser/controller state cleared.

`stateentry` aliases `textpointer` only between cold-module loading and root
apply. No formatter, inventory-name loading or picture flood fill may execute
while the copied helper occupies `fillstack`; those operations use the same
workspace. Rendering callbacks used here do not use it. The helper takes no
separate permanent private allocation and does not add a platform source file.

Read/validation failures leave the running game intact. A failure rebuilding
resources after apply begins exits through normal game cleanup rather than
resuming partially replaced state. Public I/O and mapping failures are reported
as file errors during save/prepare; apply failures propagate to the game owner.
This does not establish complete adventure or audio compatibility.


Persistence verification uses `check_wbpic_mame.py --interpreter --persistence`:
it saves variable 40 and every combined-plane pixel, changes the variable,
restores it, checks both terminals, exits/relaunches both owners and compares the
initial/final OS-9 free-memory maps. The extracted file's exact length, game ID
and CRC are checked independently on the host. `check_wbgame.py` also executes
zero, partial, complete and oversized transfer counts with both incoming Z-flag
states, and malformed field/cache recipes with exact mapping cleanup. The
ordinary native game regression suite passed and all 56 CoCo modules remained
byte-identical after these changes.


The extended two-terminal MAME test also overlays and discards a picture source,
then checks save/restore, a valid-CRC snapshot with an invalid key count, a short
snapshot, and an attempted save to the existing filename. All three error paths
restore the identical live scene; the original save still has its expected
length and checksum. Both owners exit and relaunch and the free-memory map is
unchanged. Artifacts: `/tmp/sierra-state-invalid-overlay-complete`.

Unmodified King's Quest I was saved at the castle, walked into the neighboring
room and restored to the castle. Graham's measured shirt center was 449.5 pixels
before save, 21.5 in the next room, and 449.5 after restore and after the next
`look room` interaction. The original-game memory map recovered exactly.
Artifacts: `/tmp/sierra-state-original-kq1-final`. The first test assertion assumed
movement stayed in one room; host verification of the same artifacts uses the
correct room-transition check now present in `check_wbgame_mame.py --persistence`.

The cold helper is 3,045 bytes of its 4,096-byte workspace. The main game is
23,808 bytes and retains 24,460 bytes of private data. No new platform assembly
file was added; the platform feature count remains 26.


The complete original-game persistence harness now passes directly with its
room-transition assertion and explicit post-restore modal response check:
`/tmp/sierra-state-original-kq1-complete`. This confirms the corrected test itself,
not only a host recheck of earlier screenshots. King's Quest I returns to the
saved castle position, accepts `look room`, exits on Ctrl-C and recovers the
initial free-memory map.

Native operand-count storage now uses two four-bit counts per byte, generated
from the same command catalog as CoCo. The lookup selects the nibble using
opcode parity; handler routing and the CoCo table format are unchanged. This
recovers 83 resident bytes without changing private layout or snapshot ABI.
The native game CPU suite and all 1,024 dispatch cases pass; every one of the
182 decoded counts also matches the common catalog in game and probe builds.
The lookup adds a few instructions per command and leaves rendering loops
unchanged. This space is being recovered for the native audio frontend.

The native operand workspace now retains 42 bytes rather than 255. Command
operands fit this buffer. `said` still consumes and validates all up to 254
operand bytes, retaining the first 21 word IDs: the parser has at most 20 input
words, and matching can inspect one following rest-of-line wildcard before
returning. Every later ID is unreachable by the matcher. This preserves long
valid predicates and detects truncated discarded tails. Real-CPU boundary
tests cover 20 matching words, a 21st ordinary/wildcard word, 127-word
predicates with an early or following wildcard, and unchanged adjacent replay
storage. The recovered 213 private bytes are reserved for the audio adapter;
the total private allocation and the full font remain unchanged.

### Owned, queued native sound

The native owner now supplies AGI sound through `platform/wildbits-audio.asm`
and the process-owned `PSGdrv` service. It starts with flag 9 enabled. The driver
must implement version 4 of `SS.PSG` (`$C5`); an absent helper, missing driver,
or older driver disables sound and completes the requested flag
without interrupting the game. A busy device completes only the current request
and leaves sound enabled so a later request can claim the device. Each new
request clears its completion flag before starting asynchronous playback. The PSG remains exclusive to one process; this
is safe ownership across terminals, rather than simultaneous mixing.

The adapter uses the existing sound resource cache. These packaged games have
already been converted to the CoCo stream described in `convutils/cc3snd.c`:
one-byte tone index (0–59), one-byte DAC amplitude (0–63), and a big-endian
16-bit duration. A final `$FF` and two-byte elapsed-time word end the stream.
There is no PC four-track header, and the converted files no longer retain the
other original voices. The adapter validates the record alignment and footer,
reads notes through the bounded native bytecode reader, and sends six-byte
packets with bit 7 of the channel selecting this converted format. The driver
checks tone, amplitude, duration and the reserved byte, converts the note to
its existing five-byte queue record, and uses a 60-entry frequency table derived
from the converter. The converted voice uses channel zero; other channels are
ended explicitly. End packets use the driver's normal `$FFFF` duration form.
No resource cache bytes or saved resource lengths are rewritten. Raw five-byte
AGI packets remain available to other driver clients; this game's adapter is
for the packaged CoCo resources.
No mapped resource pointer crosses file/device I/O. At each game cycle, resource
mappings are cleared before querying queue capacity or submitting notes. Work
is bounded to eight rounds across four channels. The driver advances queued
notes at 60 Hz and reports completion; the interpreter sets the game's flag
when all tracks finish. Disabling sound, issuing `stop.sound`, saving/restoring,
backgrounding the terminal, and exiting close the owned path. Backgrounding
terminates the current request rather than resuming it later. Dialog, inventory and menu waits also refill the queue after visibility
checks. These hooks run after labels and command arguments have been copied
into private UI state, with no picture or resource mapping held. Generic
foreground checks used by rendering do not refill sound or replace the
renderer's resource context. CoCo continues to use its existing audio implementation.

The resident module has eighteen bytes left below its 23,808-byte ceiling.
The kernel's `$FD00` common page and the `$FE00`/`$FF00` I/O area remain reserved.
To fit the adapter, the existing `wbstate` helper exports an immutable audio
code template and a small installer. The game validates the helper's private
layout ABI, including the audio workspace, callback layout and driver protocol,
runs the installer while the helper is linked, then unlinks it
before opening the sound device. Installation copies 450 bytes into a separate
512-byte permanent private workspace and resolves ten engine callbacks into
a 20-byte private table. It never patches the shared module and never aliases
the font, formatter, inventory, flood-fill, or presentation buffers. Device-only GetStat/SetStat helpers execute in that private copy, freeing
resident space for the three modal hooks. Normal
movement does not load the helper; only the first enabled sound request does.
Sound state and pointers are transient and are excluded from saved games.

The argument buffer still retains 42 bytes while validating every operand of
long `said` predicates. Nine cold resource-locator bytes move out of the direct
page to leave room for the fourteen sound-control bytes. Inventory and parser
filename construction use the relocated fields through the private base.
The declared private data remains 24,460 bytes, within the same three 8 KiB
banks. Tests place the user stack above the rounded allocation and parameters,
as OS-9 does, and check that deep logic calls do not overwrite the private code.

Native platform routes now use 182 byte-sized indices and 63 unique relative
handler offsets, generated from the existing shared command catalog. The
lookup zero-extends the opcode before indexing; a signed byte index would break
opcodes 128–181. This saves 48 resident bytes including the decoder. Local
native dictionary branches and a few nearby native calls use short branches;
the assembler rejects an out-of-range displacement. CoCo's instruction bytes
are unchanged.

Verification completed for this integration:

- Native CPU tests delivered exact converted-note/end packets, delayed
  completion into a later cycle, recovered the active logic resource, handled
  missing/older/incompatible services, malformed notes and busy-then-available
  retry, cleared reused completion flags, released ownership, and preserved
  private audio code at sixteen nested calls with a 127-byte directory. A
  fourteen-note fixture exceeded an eight-note queue and completed while a
  Pause dialog remained open, before its dismissal and any next game cycle.
- All 1,024 relocated dispatch cases passed for the game/probe, including all
  256 opcode values, register/stack preservation and immutable shared code.
- The full native gameplay CPU suite passed its picture, sprite, persistent
  text, parser, controller, clock, movement, animation, inventory, validation,
  mapping and cleanup checks.
- All 56 CoCo modules remained byte-identical to the preceding build.
- Original Larry and King's Quest I ran together on separate terminals in
  MAME. Screen restoration, independent inventory input, Larry surviving KQ1
  exit and exact memory recovery passed; 83 owned PSG writes were captured.
  This pair uses the emulator-only expanded-memory kernel.
- Original King's Quest I passed real MAME startup, inventory glyphs, walking,
  save, restored position, a subsequent `look room`, interrupt exit and exact
  free-memory recovery with the compatible version-4 PSG driver installed.

The driver lives on NitrOS-9 branch `codex/sierra-owned-psg`, based on the tested
multi-terminal OS revision, not on the alternate terminal-private ABI. Driver
CPU/public-SCF tests cover queued timing, contention, wrong-owner close,
terminal initialization/bell guards, IRQ rollback/teardown and memory recovery.
Physical hardware, envelope details and complete adventure compatibility still require further work.


### Preserve the CoCo command catalog's explicit no-ops

The shared catalog now routes the seven zero-operand commands whose CoCo
handler is `NoopCmdsRet` to native `VmSuccess`: `init.disk` (127),
`open.dialogue`/`close.dialogue` (163/164), `hold.key` (173), and the catalog's
unused commands 176, 178 and 181. Previously these reached `E$UnkSvc` and
terminated an otherwise valid native script. They now continue without
changing game variables, flags or display state, matching this CoCo port's
behavior. This does not implement a new held-key policy or silently accept
other unsupported commands. The actual close-window command 169 retains its
existing handler.

The native route table grows by one shared success target (two bytes), giving
a 23,790-byte resident engine. The CoCo handler and operand columns are
unchanged; rebuilt King's Quest I `mnln` remains byte-identical. A CPU script
executes all seven commands, continues with variable copying, and verifies
preserved variables/flags plus complete cleanup. The relocated dispatch test
also checks their exact game/probe destinations.


### Positioned messages and a cached text backend — 2026-10-07

`print.at` (151) and `print.at.v` (152) now use the native modal text path instead
of aborting with `E$UnkSvc`. Their arguments are message, row, column and width;
the variable form resolves only the message number through the variable table.
This order follows the maintained [ScummVM AGI command implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/op_cmd.cpp).
Width zero selects 30 columns, following [its text implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/text.cpp).

The native text cursor resets to the supplied left column on a newline or wrap.
Words move to the next row when they do not fit; long words split at the right
limit. Width is clipped to the available screen columns, including arithmetic
overflow, and output clips at the bottom row. Row 25 or greater and column 40 or
greater fail before text is presented. Ordinary `print` and `display` reset their
existing layout independently of the previous positioned message. These are
positioned text within the existing native full-screen modal, not a new bordered
window renderer.

To fit this behavior, the text-storage loop remains in
`platform/wildbits-text-ui.asm` but assembles into the existing `wbstate` helper.
It is immutable: all characters, colors, cursors and limits use the caller's
private U base, and Y supplies the resident presentation callback. The frontend
validates the helper ABI and entry bounds, caches its module and entry pointers,
and retains the link until cleanup. No shared module bytes are patched.

An isolated real-MAME probe confirmed that resources still map at `$6000` while
the helper is linked in the other spare window. The final game uses one service
mapping at a time. The code shares one physical helper block across games, with
one additional DAT code window per process. Movement does not load the helper.
The resident is 23,794 bytes, the helper 3,778 bytes, and declared private memory
remains 24,460 bytes with the full font and permanent audio workspace intact.
No platform assembly files or production modules were added.

`wbstate` is now required for native text output. Install it together with
`wbgame` and `wbfont` from the same build. Private helper ABI version 2 includes
the cached entry/module pointers and text bounds; the loader checks the extended
metadata header and both executable entry bounds. The on-disk save schema remains version 1.
State operations still execute a writable private copy, while linked text code
and the exported audio template remain read-only. A temporary audio-install or
state-operation link is released independently of the retained text reference.

Cleanup unlinks the text helper after stopping sound and before releasing game
resources, retries one failed unlink, and preserves the first exit error.
Text-screen clearing leaves the cached link intact; clearing it there lost the
reference during repeated mode switches, which the regression suite caught.
The sound path is now cleared at process startup, before font loading, so an
early font error cannot try to close an uninitialized path.

Verification covers literal/variable messages, word/newline/long-word wrapping,
default width, clipped right/bottom edges, invalid positions, and a normal print
after a held positioned message. The full gameplay CPU suite and all 1,024
relocated dispatch cases pass. CPU checks also verify an unchanged shared helper
image, no link leaks, early font failure with a dirty sound-path byte, queued
sound, deep logic calls and exact cleanup.

Original KQ1 passes save/restore and subsequent input in real MAME while the
text helper remains linked (`/tmp/sierra-positioned-kq1`). Original Larry and KQ1
also pass independent terminal switching, inventory input, exits and exact
memory recovery (`/tmp/sierra-positioned-pair`, with the documented emulator-only
expanded-memory kernel). The latter captured 80 owned PSG writes. These remain
emulator checks rather than physical-hardware or full-adventure acceptance.


### Timed blocking messages — 2026-10-07

Native `print`, `print.v`, `print.at` and `print.at.v` now honor AGI variable 21:
a nonzero value dismisses the blocking message after that many half-seconds.
The interpreter multiplies it by 30 into a private 16-bit frame budget, so the
maximum value of 255 retains its full 7,650-frame duration. A key can dismiss
it earlier. Blocking dismissal clears variable 21; held messages (flag 15),
input editing and Pause retain their separate behavior. This follows the timer
and nonblocking distinction in the maintained
[ScummVM AGI text implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/text.cpp).

With the public SOL raster counter, the loop subtracts the actual frame delta
between samples, including modulo-256 counter wrap. On a foreground notification
it rebases the dialog sample instead of charging hidden time to the budget.
Without that optional service, it counts the existing one-tick sleep requests;
that fallback can run late under scheduling load. The loop holds no asset or
picture mapping while waiting and continues to refill owned sound queues.

The modal wait and key-reading code remain grouped in
`platform/wildbits-text-ui.asm`, but assemble into the existing immutable
`wbstate` backend. A small resident callback table supplies foreground/audio
processing, line editing, screen restoration and counter sampling. Each process
owns its cached wait entry, budget, sample, mode and visibility epoch. No helper
code or callback address is patched. The text and wait frontends share a loader,
reuse one retained module reference, and validate each entry against the module
header and executable end before jumping. Failure restores the modal call frame
and normal exit releases the reference.

The module metadata now includes a fourth word for the modal entry. Its private-layout hash covers
the added transient fields, so mismatched helpers fail validation. Install
`wbgame` and `wbstate` together. The saved-file schema is still version 1, and
the timer/cache fields do not enter the serialized state. Private allocation is
still 24,460 bytes; the resident is 23,807 of 23,808 bytes and the helper is 4,048
of its 4,096-byte copied-state workspace. Neither memory ceiling was increased,
and the platform source count remains 26.

Verification covers all four timed print commands, early keyboard dismissal,
maximum timeout, held/Pause exclusions, counter wrap and coarse samples,
foreground rebasing, and invalid wait entries including CRC bytes. The full
native gameplay CPU suite and queued-audio regression pass. Original KQ1 passes
save/restore, movement, subsequent input, audio and exact memory recovery in real
MAME (`/tmp/sierra-timed-kq1`). Larry and KQ1 also pass independent inventory
input, terminal switching, one game's exit and final memory recovery together
(`/tmp/sierra-timed-pair`, using the documented emulator-only expanded kernel).
These tests do not establish complete adventure or physical-hardware acceptance.


A generated-message MAME probe subsequently measured all four blocking print
commands against the actual public SOL counter, confirming its path remained
active. Half-second messages measured approximately 0.492–0.494 seconds and a
one-second message 0.995 seconds. The untimed completion message waited for a
key, its glyphs matched the font exactly, and exit recovered the original
free-memory map. The reusable test is `tests/check_wbgame_timers_mame.py`;
its final artifacts are `/tmp/sierra-timed-counter-final`.


### Separate writable state copies from linked cold code — 2026-10-07

The helper's two uses now have separate bounds. Its linked image can occupy the
existing 8 KiB code window. Save/restore copies only the prefix ending at
`StateCopyEnd`, including the state routines and their private working data;
the immutable audio template, text storage, modal wait and text-rectangle code
remain outside that copy. The loader validates that the prefix contains the
metadata header, is no larger than 4,096 bytes, and ends within the module.
The whole module must fit within 8,192 bytes. ABI validation still precedes
entry selection, and each cold entry stays outside the CRC footer.

The prefix length is the fifth metadata word; the sixth holds the immutable
rectangle entry. `StateLoadModule` returns the validated length in Y, so the
copy loop uses that count rather than the module's full size. The layout hash
includes the added cache field and metadata shape. The on-disk save schema and
24,460-byte private allocation remain unchanged. Install matching `wbgame`
and `wbstate` binaries.

`clear.text.rect` now executes through the same retained helper link, with the
resident presentation routine supplied as a callback. `clear.lines` still
normalizes its arguments and uses that rectangle path. Inclusive bounds,
color selection and invalid-coordinate errors are unchanged. The normal
sprite and glyph rendering loops remain resident. The code stays grouped in
`wildbits-text-ui.asm`; no production module or platform file was added.

The resident is 23,741 bytes, recovering 66 bytes from the timed-message build
and leaving 67 below its 23,808-byte ceiling. The linked helper is 4,172 bytes,
but the writable prefix is only 3,054 bytes. It fits the same existing physical
8 KiB block; its copied prefix fits the existing 4 KiB state workspace.

CPU fixtures now place native private banks at `$0000`–`$5FFF`, the helper
window at `$6000`, the resource service window at `$8000`, and resident code
at `$A000`. The preceding artificial `$7000` helper address left only 4 KiB
before the resource window. A harness assertion now rejects overlap between
private banks and linked helper code. This corrects test geometry without
changing target addresses or allocating additional target banks.

The full native gameplay suite verifies rectangle colors/bounds in all text
and graphics modes, timed messages, input, sprite composition and cleanup.
Separate fixtures reject short/oversized prefixes, prefixes beyond the module,
modules beyond the code window, and rectangle entries at zero, the module end
or CRC bytes. Owned-audio regression passes. Original KQ1 save/restore and
subsequent input pass in real MAME (`/tmp/sierra-cold-rect-kq1`).

The simultaneous Larry/KQ1 MAME run also passes with the larger linked helper
(`/tmp/sierra-cold-rect-pair`, using the documented expanded emulator kernel):
independent inventory input, terminal restoration, Larry continuing after KQ1
exits, 80 owned PSG writes, and recovery of both one-game and final memory maps.


### Restart without recursive execution or stale ownership — 2026-10-07

Native `restart.game` now implements the confirmation dialog. ENTER accepts;
ESC or another key cancels and resumes the caller. Flag 16 bypasses the dialog.
The dialog temporarily forces blocking input, then restores flag 15. Accepting
sets pending action 3. Every nested logic call unwinds before the root applies
the restart, so no active caller refers to resources being freed. The root
tail-enters the normal startup loop; repeated restarts do not grow its stack.

The immutable restart routine lives in the existing helper, assembled from
`wildbits-text-ui.asm`. Its resident callback table stops owned audio, closes
the process's clock subscription, releases temporary and cached resources,
and releases picture/background slabs. It retains the terminal bitmap/window,
font and linked helper. It clears game variables, flags, strings, object state,
menus, controllers, logic cache and replay bookkeeping, initializes the UI,
and reloads the original command-line root resource. Fresh initialization sets
flag 6 for the restarted script. Instructions following restart in the old
caller never run after acceptance. Loader failures follow ordinary cleanup.

The helper header's seventh metadata word supplies the restart entry. Entry
bounds exclude the CRC footer; the private-layout ABI hash covers this header,
the new cached pointers and the cache stride. Install matching binaries. The
logical WS version-1 save format is unchanged.

A regression with 16 nested calls, a 127-character resource directory, an
active sound and the confirmation dialog exposed stack overlap with cached
helper pointers. Those pointers now precede the font, below the high stack
area. Cache records use 12 bytes instead of 14: only two unused reserved bytes
per record were removed, preserving all 32 slots and their fields. State capture
uses the same stride. The recovered 64 bytes enlarge the high private padding;
font, audio reservation, resource workspace and declared allocation are unchanged.
The reset range ends before the preserved helper pointers.

The resident is 23,805 of 23,808 bytes; the linked helper is 4,402 bytes and
its writable prefix is 3,056 bytes. Private allocation remains 24,460 bytes.
No production module or platform file was added.

CPU tests cover confirm, cancel, ESC, automatic restart, maximum nesting and
the long-directory case, with active owned audio. They check cleared state,
caller unwinding, preserved font/private audio code, immutable helper bytes,
invalid entries and ownership cleanup. The full game/audio suites and all
1,024 dispatch checks pass. Original KQ1's menu restart passes in MAME: walking
changes Graham's position, restart restores it, a subsequent `look room` works,
and exit restores free memory (`/tmp/sierra-restart-kq1-safe`). Save/restore
passes at `/tmp/sierra-restart-save-safe`; independent Larry/KQ1 terminals pass
at `/tmp/sierra-restart-pair-safe` with the documented expanded emulator kernel.
These checks establish restart behavior, not complete adventure coverage.


### Keep infrequent screen configuration outside the resident — 2026-10-07

The native game now calls the existing immutable helper for cursor character,
text colors, screen rows, status enable/disable and input enable/disable.
`ScreenInitialize` and the pixel/sprite/glyph loops remain resident. The helper
receives the resident message reader as a callback for cursor strings; the
configuration fields remain process-private. Diagnostic modules assemble the
same implementation directly. No duplicate handler body or new module is needed.

The eighth metadata word selects this backend, with an ABI-checked private
cached entry. Bounds now include all eight words. The private allocation and
logical save schema are unchanged. Resident size falls from 23,805 to 23,697
bytes, leaving 111 bytes below its ceiling. The helper is 4,532 bytes and its
writable prefix is 3,058 bytes. Install the matching game and helper.

Targeted CPU tests cover every handler, cursor-message decoding, invalid
colors/rows/messages and zero/oversized/CRC entry rejection. The full native
game suite passes, including maximum-depth restart and long-directory audio
protection. Original KQ1 movement, menu restart, subsequent input, 59 owned PSG
writes and memory cleanup pass in MAME (`/tmp/sierra-screen-cold-kq1`). The
CoCo KQ1 main-line module remains byte-for-byte identical to its baseline.


### Inventory item previews — 2026-10-07

Native `show.obj` and `show.obj.v` now display a view's first cel, centered
horizontally at baseline 167 with priority 15, and wait for dismissal of its
description. The variable form resolves its view number through the AGI
variable table. This follows the CoCo item-display path; the expected view and
description behavior is also visible in [ScummVM's AGI implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/sprite.cpp#L369).

The command executes in the existing immutable helper. Its temporary object
record uses an idle part of the process-private renderer list, so it neither
replaces a game object nor publishes ego-visibility flags. The ordinary view
selector and RLE sprite renderer are resident callbacks. View descriptions are
copied with bounds checks into the private 512-byte message buffer before
restoring the executing logic slab. An absent description is supported; up to
511 characters plus a terminator fit. Out-of-range, unterminated and oversized
descriptions fail with the normal malformed-resource error and cleanup.

The preview forces a blocking, untimed dialog while preserving flag 15 and
variable 21. Blank cells outside its description are transparent during this
dialog, keeping the item visible. The preview does not replace the pristine
background when one already exists. On dismissal it restores that background
fully, then recomposes normal objects and refreshes the display. Full restoration
is necessary because the fast sprite eraser scans game records and cannot see
the temporary preview record. This also prevents ghost pixels when a normal
object subsequently moves. A view loaded only for the preview is discarded;
a preexisting cached view stays owned by the game.

Resident callbacks are a read-only relative-address table. Cold calls preserve
D/X/Y/U arguments and keep their indirect destination in a stack word; no
instruction or shared module data is patched. The helper's ninth metadata word
and new process-private fields are included in ABI validation. The resident is
23,759 bytes, leaving 49 below its ceiling. The linked helper is 5,071 bytes
and its writable prefix is 3,060 bytes. Private allocation remains 24,460 bytes,
and the WS version-1 logical save schema is unchanged. Install matching binaries.
No production module or platform source file was added.

CPU tests verify literal/variable previews, item pixels while the dialog is
active, description text, exact restoration, moving-object restoration,
preexisting cache ownership, preserved print flags, empty/maximum descriptions,
invalid resources and invalid helper entries. The maximum-depth, 127-character
directory case passes with active owned audio and immutable font/private audio
code. The full gameplay and audio suites pass. The CoCo KQ1 main-line module
remains byte-for-byte identical to its baseline.

`tests/check_wbgame_previews_mame.py` checks the generated item and description
against real Wild Bits display drivers: exact pixels/glyphs, keyboard dismissal,
subsequent script execution, controller-driven quit, exact scene restoration
and recovery of the free-memory map (`/tmp/sierra-preview-real-drivers-controlled`).
Original KQ1 save/restore and subsequent input pass at
`/tmp/sierra-preview-original-kq1`, with 59 owned PSG writes. Simultaneous
Larry/KQ1 terminals pass at `/tmp/sierra-preview-pair`, with 80 writes and
recovered one-game/final memory maps using the documented expanded emulator
kernel. These checks do not establish complete story-command coverage.

A separate interrupted run also restores terminal options and the memory map
(`/tmp/sierra-preview-interrupt-clean`). The preview test's `--interrupt` option
reproduces that path, separating modifier/key events and clearing residual
shell input before collecting the memory report.
