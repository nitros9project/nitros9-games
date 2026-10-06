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
window-alignment/mask and dictionary-walk core. The game is 22,832 bytes;
process data is 24,570 bytes (six bytes below its three-page limit).
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
