# Wild Bits engine structure

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

The current native executables are probes for implemented interfaces. They
are not separate processes intended to form the eventual game interpreter.

`wbpic.asm` owns one OS-9 module and exercises combined-buffer presentation.
`wbres.asm` owns another small test module and includes `resource-data.asm`
and `resource-code.asm`. `wbdecode.asm` now includes those same resource routines
directly, together with converted command, line, fill and mapped-storage bodies. It does not fork
`wbres` or reimplement its loader. `resource-cli.asm` supplies shared probe
argument/output handling. Each executable still has exactly one module header.

The current flow is:

```text
Native resource step: picDir + vol.N -> LoadPicture -> AGI command bytes
Presentation step:   combined color/priority buffer -> wbpic -> terminal bitmap
Native decoder:     F0-FA command bytes -> owned physical buffer, one mapped window
Native assets:       log/view/sound resources -> bounded LZW -> owned mapped slabs
Native logic:        mapped byte fetch -> arithmetic/conditions -> cached/nested calls
Native game owner:  picture/view composition + literal text + repeated logic/input cycles
Still to convert:   motion/cel updates, word parsing, dialogs, sound, remaining commands
```

The host renderer supplies the reference while the native decoder is converted.
The decoder has private state, bounded reads and immutable relative dispatch.
Mapped picture storage and bounded scanline fill now replace fixed CoCo buffer
and stack addresses. The private command buffer and fill stack still consume
two process blocks; integration must budget interpreter state alongside them.
Pen conversion and direct presentation now work together in `wbrun`.
Compressed logic/view storage now exists in the shared asset components.
The old fixed-address `shdw` body cannot simply be linked into the new module.

`wbrun.asm` now owns one module and includes the resource loader, decoder and
shared presentation routines directly. It does not fork the probes. The same
small presentation includes are used by the existing viewer, whose binary is
unchanged. This proves the single-program source structure before bringing in
the main interpreter; it does not claim that displaying a resource is gameplay.


The interpreter follows the same include structure. `wbexec.asm` owns its
module header and private data, includes `lzw-*`, `asset-*`, `logic-*` and
`message-*` routine bodies, and calls them directly. It never starts `wbasset`
as a subprocess. The eventual main game owner can use these same components
alongside the picture/presentation includes. `logic-platform.asm` is currently
the command integration boundary, with explicit errors for unported behavior.
The original CoCo `mnln.asm` remains the source/semantic reference; no complete
CoCo module or fixed-address workspace is incorporated into the native owner.


`wbgame.asm` is now the integration owner. The `object-*`, `view-*`, `room-*`,
`menu-*`, `input-*`, `screen-*`, `string-*` and `replay-*` bodies keep small AGI
command groups separate. `game-picture-*` connects script picture commands to
the existing decoder. `game-background-*` owns an immutable decoded background;
`game-render-*` stages bounded view rows and composes visible objects;
`game-text-*` maintains private persistent text cells and draws the shared font;
`game-cycle-*` owns scheduling, clock, controller polling and immediate quit.
Each component calls OS services through the same one-window discipline.
The `game-motion-*` bodies add object stepping and cel updates without merging
the sources into a second engine. There is still no complete gameplay claim:
follow/wander motion, parsing, dialogs and sound remain explicit work, and unsupported commands do not become silent no-ops.

Startup and cycle flags follow the existing AGI semantics, checked against
[ScummVM's AGI cycle implementation](https://github.com/scummvm/scummvm/blob/master/engines/agi/cycle.cpp).
The 6809 command adaptations remain based on this repository's CoCo engine.
The native renderer retains priority/control distinctions while changing the
storage and mapping interface; shared module code and font bytes are immutable.

## Architecture correction

The picture coordinate, line and pen routines, including their immutable tables, now have
one implementation under `objs/shared/`, included by both `objs/shdw.asm` and
the native decoder. `objs/platform/picture-storage.asm` selects either
`coco-picture-storage.asm` or `wildbits-picture-storage.asm` at assembly time.
The Wild Bits implementation preserves the registers needed by these shared
algorithms and maps each logical pixel through `PicturePointer`.

Wild Bits mapped-picture allocation/access and terminal presentation now live
in `objs/platform/wildbits-picture-memory.asm` and `wildbits-presentation*.asm`.
Native game/viewer integration uses the existing `platform/presentation.asm`
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
`objs/platform/wildbits-sound-code.asm`. There is no safe multi-instance AGI
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
reader, submitted IDs and saved input spans. `wildbits-format-code.asm` expands
copied messages; `wildbits-dialog-code.asm`, `wildbits-line-input-code.asm` and
`wildbits-menu-code.asm` provide modal interaction. The game owner selects these
small components, while `logic-platform.asm` only routes commands and tests.
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

The current module is 20,741 bytes and its private area 24,570 bytes, leaving
6 bytes before a fourth data block. The code limit remains 23,808 bytes.
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

`wildbits-render-text.asm` stages a glyph scanline in the private 320-byte
row-output buffer; palette index zero is a skip marker for absent text cells.
Actual text colors remain indices 1..16. Bounded editor updates retain their
existing range renderer. The full renderer no longer maps pages by character.

Palette/layer setup is cached per process, with foreground notification
invalidating the cache. Real two-terminal tests cover restoration and exits.
The added rendering controls total 15 private bytes and require no extra
physical allocation. Six bytes remain before a fourth data block (three with
optional exit tracing). CPU tests now load the larger module at $A000 rather
than $B000, and reject any fixture overlapping the CoCo I/O page at $FE00.
