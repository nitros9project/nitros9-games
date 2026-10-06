# Wild Bits MAME acceptance

Use the [Wild Bits MAME fork](https://github.com/rlucente-retro/mame), branch
`wildbits-jr2`, machine `wbjr2`, and `-bios turbo`. Stock/Homebrew MAME does
not provide this machine. The OS image needs the extended drivers from
[NitrOS-9's `wb/multiterm` branch](https://github.com/jfed6000/nitros9/tree/wb/multiterm).
The [porting guide](https://github.com/jfed6000/f256_porting) describes this
emulator and explains why it must not be used to establish hardware timing.

## Build dependencies

Build the emulator using the porting guide's command:

```sh
make SOURCES=src/mame/wildbits/wildbits_jr2.cpp NOWERROR=1 REGENIE=1 -j4
```

Configure SDL for the host. This macOS run used the installed Homebrew SDL3
headers/library with `USE_LIBSDL=1` and an `SDL_INSTALL_ROOT` prefix containing
an `sdl3-config` shim supplying `-I/opt/homebrew/opt/sdl3/include` and
`-L/opt/homebrew/opt/sdl3/lib -lSDL3`. No MAME source was modified.
The default build produced `mamed`; use the actual executable name produced
by your build.

For the 2026-10-06 rebuild, this fork's SDL3 backend still queried
`sdl2-config` in `scripts/src/osd/sdl.lua`. The temporary prefix supplied both
`sdl2-config` and `sdl3-config`, returning
`-I/opt/homebrew/opt/sdl3/include` for `--cflags` and
`-L/opt/homebrew/opt/sdl3/lib -lSDL3` for `--libs`. Installed SDL was 3.4.16.
Do not point this SDL3 build at the Homebrew SDL2 prefix.

The workspace environment also contained a 6809 cross-compiler. Pinning the
host compiler and SDK avoided both selecting that compiler and missing the
macOS C/C++ headers:

```sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools \
SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk \
make SOURCES=src/mame/wildbits/wildbits_jr2.cpp NOWERROR=1 REGENIE=1 \
  USE_LIBSDL=1 SDL_INSTALL_ROOT=/tmp/sierra-wildbits-sdl3 \
  OVERRIDE_CC=/Library/Developer/CommandLineTools/usr/bin/clang \
  OVERRIDE_CXX=/Library/Developer/CommandLineTools/usr/bin/clang++ -j4
```

The prefix is local build configuration; no emulator source changes were
required. The Command Line Tools compiler was Apple clang 21.0.0.

Build the OS tree's `recipes/wildbits/l2` and `recipes/wildbits/feu` recipes
with `PLATFORM=jr2`; the FEU recipe needs both `all` and `f0.dsk` targets.
Set `NITROS9DIR` to that tree and `LANGUAGES` to the sibling language tree.
Build libraries before parallel linking, or use a serial recipe build.
At the OS revision below, the Level 2 recipe references a missing `vs.asm`;
this run supplied the existing workspace's `level1/wildbits/cmds/vs.asm` in
the temporary OS tree. That command is unrelated to `wbpic` or graphics.

The test requires `os9` (ToolShed) on PATH and an already-built `wbpic`.

## Run

From `sierra/objs`:

```sh
python3 ../tests/check_wbpic_mame.py \
  --mame /absolute/path/to/mamed \
  --disk /absolute/path/to/nitros9/recipes/wildbits/l2/l2_wildbitsjr2.dsk \
  --firmware /absolute/path/to/nitros9/recipes/wildbits/feu \
  --output /tmp/wbpic-mame-new-run
```

The output directory must be new. The test copies the disk and firmware,
pads the disk upward to a power of two, installs `wbpic` and two diagnostic
buffers, and replaces startup **only on that copy**. It drives shells on
`/term` and `/vt1`, injects Alt+Left/Right through MAME's keyboard input ports,
and uses a globally retained Lua frame callback. On macOS, SDL may require
access to display services even with `-video none`.

Assertions cover:

- Every captured picture pixel, including the remaining black area, in
  the 640-by-480 output. Each logical AGI pixel becomes four display pixels
  horizontally and two vertically.
- Identical pictures after switching away and back.
- Closing one viewer while the other remains intact.
- Relaunching both viewers with the same bitmap numbers.
- Identical free-memory maps before and after both launch/quit cycles.
- A completion marker written by the shell after both viewers have exited.

Gamma-adjusted colors are calibrated from sixteen distinct color bars; this
checks pixel selection and restoration, not absolute hardware color accuracy.
Logs, Lua commands, memory reports and screenshots remain in the output
directory. No emulator, firmware, disk image or generated game buffer is
committed to the repository.

To use a real exported game picture on `/vt1`, add
`--picture /tmp/kq1-picture-1.bin`. Game assets are optional; the default test
generates both buffers itself.

## Recorded result

Diagnostic-only and King's Quest I picture runs passed on 2026-10-04 with:

- MAME `078e0eeb7ea1c7eb3b4445329f109586f1fdd29c` (the fork's rc20 core model).
- NitrOS-9 `c45760abeb03c39197ca8e569d5afb621bef8cc7`, `wb/multiterm`.
- `wbpic` 870 bytes, CRC `$9781F4`, edition 1.
- Identical memory maps before/after two cycles: 44 free 8 KB blocks, 352 KB.

This establishes emulator behavior for those revisions. It does not establish
hardware speed, switching during the short loading window, hidden cancellation,
forced kill, or behavior under persistent driver failures. Those checks remain
in physical hardware/extended runtime acceptance work. `wbpic` is a combined-buffer viewer. The native game has its own acceptance
runs, including the current result below.

## Native resource-loader check

With the same emulator, disk and firmware prerequisites:

```sh
python3 ../tests/check_wbres_mame.py \
  --mame /absolute/path/to/mamed \
  --disk /absolute/path/to/l2_wildbitsjr2.dsk \
  --firmware /absolute/path/to/nitros9/recipes/wildbits/feu \
  --output /tmp/wbres-mame-new-run
```

This installs `wbres` and a generated 8 KB resource in a copied disk, then
runs the native probe from startup with stdout redirected to a disk file.
The resource uses picture number 255, volume 15, and offset `$23456`, testing
the decimal filename, directory multiplication, full seek offset and maximum
supported command size against real RBF services. The resulting bytes must
exactly match the input, and startup must write its completion marker.

For a real game, add `--game /path/to/kingsquest1 --picture-number 1`.
Only its directory and selected volume are installed on the temporary disk;
no game assets are committed. This run passed for both the diagnostic and
King's Quest I picture 1 using the emulator/OS revisions recorded above.
The latter produced 2,752 command bytes with SHA256
`65f0bfee93044b42eaca6ce11c35d8db108d0af79d1d213e78ebf40167fa8258`.
This verifies native resource loading, not native command decoding.

## Native mapped decoder and fill

Add `--decode` to the resource-loader test command to exercise `wbdecode`.
The default fixture draws a rectangle, fills its inside and outside and
checks a priority-only fill. The test executes the existing CoCo renderer
on XRoar's 6809 CPU and compares every one of the 26,880 native output bytes.
It runs the probe separately on `/term` and `/vt1`, requires both outputs to
match, and compares the free-memory map before and after both runs. This is
sequential terminal-path coverage; the viewer test above covers simultaneous
presentation and terminal switching. Use a fresh output directory each time.

Script input must be redirected explicitly with `</term` or `</vt1`. Without
that redirection, path 0 is the startup file and graphics SetStt requests go
to RBF. The native probe now checks stdin's SCF device type before allocation.
It allocates four program-owned picture blocks, uses one cached mapping window
and releases the mapping and allocation on exit. Output goes through a private
staging buffer after unmapping. No display layers or palettes are modified.

This passed on the emulator/OS revisions recorded above with module size
2,085 bytes, CRC `$A353F8`, and combined output SHA256
`ece06b2520475bce66b073dd594074215b3bea9993957d1153fe3c8a4f4c6cb3`.
The free-memory reports were identical. Artifacts from this run are in
`/tmp/sierra-final-mapped-fill`; they are not committed.

The CPU fixtures generate a tiny idle ROM before debugger attachment and
switch to all-RAM mode before executing either renderer. This contains no
BASIC or game assets. On macOS, headless GDB attachment can still time out;
the exporter retries only startup timeouts, up to four fresh processes, and
reports persistent failure. The final broader CPU regression used an official
XRoar 1.12.1 build configured without SDL, Cocoa, GTK or platform audio, placed
first on PATH. It passed all differential, malformed-input, service-error and
fill-stack boundary checks. The module output and OS-memory checks above
passed independently through the actual Wild Bits MAME drivers.

That fill milestone used a diagnostic fixture. Pen commands and compression
were added in subsequent milestones; the full game interpreter is not running.
Physical hardware and performance validation remain outstanding.

## Integrated native game-resource presentation

Add `--native-game /path/to/kingsquest1` to the viewer test command to exercise
`wbrun` instead of `wbpic`. The test installs plain gradient picture commands
and the selected real game's directory/volume. The native program loads and
decodes both resources itself. The host CoCo renderer is only the pixel oracle.
The test allows extra startup time for native resource decoding and otherwise
checks concurrent terminal presentation, every displayed pixel, restoration,
independent exit, relaunch and the free-memory map as above.

This passed for picture 1 with 3,294-byte `wbrun` and 14,646 bytes requested
private data; artifacts are `/tmp/sierra-native-present-kq1-v2`. The real-OS
`wbdecode --game ... --picture-number 1 --decode` run also matched every CoCo
combined byte on both terminal paths, with unchanged free memory; artifacts
are `/tmp/sierra-native-kq1-pen`. The full game interpreter is still outstanding.


## Expanded resources and mapped bytecode

The existing resource driver harness now also accepts `--asset` and `--execute`:

```sh
python3 ../tests/check_wbres_mame.py \
  --mame /path/to/mamed \
  --disk /path/to/l2_wildbitsjr2.dsk \
  --firmware /path/to/feu \
  --output /tmp/wildbits-logic0 --asset

python3 ../tests/check_wbres_mame.py \
  --mame /path/to/mamed \
  --disk /path/to/l2_wildbitsjr2.dsk \
  --firmware /path/to/feu \
  --output /tmp/wildbits-bytecode --execute
```

`--asset` defaults to local King's Quest I logic 0; `--game` and
`--logic-number` select a different local logic resource. The native program
reads its directory/volume through the real OS, allocates a two-block slab,
expands LZW and exports all 8,950 bytes on both terminal paths. SHA256:
`23d775c6e8fe69ff1dede5186ea86de1d83ed6a76674a62af6513c3c5e0e3677`.
The successful run's artifacts are `/tmp/sierra-native-lzw-logic0`.

`--execute` installs generated diagnostic logic files, not a game. A script
jumps across an 8 KB boundary, loads a second logic, calls it twice through
the cache, and exports its resulting variables/flags. Both terminal runs
match the expected 512 bytes and restore free memory. SHA256:
`5f89714fe7af154e95d837ed83af8fe7853ec6c63a64470bbc284d9104cbbd8f`.
Artifacts are `/tmp/sierra-native-vm-cache`. This verifies the real mapping,
resource ownership and nested-call path; it does not prove gameplay, physical
hardware behavior or performance parity.


## Native game owner: repeated cycles on two terminals

The native `wbgame` diagnostic passed with the same `wbjr2` emulator and
multi-terminal OS revisions above. It executes AGI scripts that load/draw/show
pictures, keep returning through the game cycle, bind ASCII `x` to a controller,
and quit when that controller is seen. Every displayed pixel matches the CoCo
reference. Both terminals survive switches and the other instance's exit;
relaunch succeeds and the free-memory map returns to its starting value.

```sh
python3 ../tests/check_wbpic_mame.py \
  --mame /tmp/sierra-wildbits-mame/mamed \
  --disk /tmp/sierra-wildbits-os/recipes/wildbits/l2/l2_wildbitsjr2.dsk \
  --firmware /tmp/sierra-wildbits-os/recipes/wildbits/feu \
  --native-game ../kingsquest1 --interpreter \
  --output /tmp/sierra-native-game-terminals-final-v1
```

Artifacts from this run are `/tmp/sierra-native-game-terminals-final-v1`.
Both before/after maps contain 344 KB free. The first eager-background build
failed bitmap allocation for the second instance (`E$MFull`, error 32) under
this 512 KB kernel. Lazy background allocation removes the unused duplicate
picture in these sprite-free diagnostics and the repeat then passes. Sprite
composition still needs a separate background; this is not acceptance of two
full games on a 512 KB machine. The guide describes a newer expanded-RAM
kernel/core combination, which remains separate environment validation work.

This result is real-driver integration for the native owner, not proof of
playable King's Quest I. Sprite and text pixel cases currently run in the
actual-6809/mocked-services tests; full game motion, parsing and sound remain.
An optional `-DGAME_TRACE=1` build reports an exit error, last opcode and first
failing presentation stage after cleanup. `--module-file` selects such a build
for MAME tests without replacing the normal executable.


The expanded `wbexec` typed-cache/object diagnostic also passed on `/term`
and `/vt1` with the final 6,194-byte module. It distinguishes same-number logic,
view and sound resources, discards/reloads views, calls cached logic twice and
checks object position/direction/priority. Its 512-byte result hashes to
`3d5134f1ae4380a2d74887b2f8e9fbacddc634300c0f3b03d7e65beca3e01ec3`;
artifacts are `/tmp/sierra-native-vm-objects-final-v1`. Free RAM is unchanged.

## Real-resource inventory checkpoint

The final inventory/font build passed with unmodified King's Quest I files:

```sh
python3 ../tests/check_wbgame_mame.py \
  --mame /tmp/sierra-wildbits-mame/mamed \
  --disk /tmp/sierra-wildbits-os/recipes/wildbits/l2/l2_wildbitsjr2.dsk \
  --firmware /tmp/sierra-wildbits-os/recipes/wildbits/feu \
  --game ../kingsquest1 --module-file /tmp/wbgame-trace-inventory-final \
  --output /tmp/sierra-real-kq1-inventory-ctrl-i-v20
```

That optional trace module is assembled from `sierra.asm` with `-DWILDBITS=1` and
`-DGAME_TRACE=1`. The harness installs the generated `wbfont` in `CMDS` with
read/execute attributes. It checks castle graphics, the inventory title's
pixels against the shared font, dismissal, restored graphics, interrupt exit
and the original 376 KB free-memory map. Ctrl-I supplies the game's ASCII Tab
inventory binding; the ordinary Tab key was not reliably delivered by this
MAME setup. This is not a claim of complete keyboard, parser, audio or gameplay
acceptance. Later trace exits other than controlled abort (228) fail the test.

The font/scratch change also passed the existing two-terminal interpreter
regression in `/tmp/sierra-native-game-inventory-terminals-final-v3`: exact picture pixels,
visibility switching, independent controller exits, relaunch and free-memory
recovery. Those scripts remain picture-only diagnostics, not two full games.

## Packed text/controller memory checkpoint

The 15,198-byte `wbgame` module with 24,328 private bytes passed the same
unmodified King's Quest I inventory harness in
`/tmp/sierra-kq1-packed-text-controllers`, using the normal module rather than
an optional trace build. Castle graphics, shared-font inventory title pixels,
dismissal, restored scene, interrupt exit and unchanged free memory all passed.
The text cell colors are packed nibbles and controller state is a private bitset;
these representations require no new driver or hardware access.

The two-terminal interpreter diagnostic also passed with this layout in
`/tmp/sierra-packed-two-terminals`: every displayed pixel, foreground switching,
restoration, independent exit, relaunch and free-memory recovery. These remain
picture-command diagnostics rather than two complete concurrent games.

## Interactive King's Quest I checkpoint

The native game now accepts typed commands with original game vocabulary and
prints original script messages. Real-driver acceptance includes:

- `look room`: the castle/alligator-moat description, word-wrapped modal window,
  dismissal and restored scene. Artifacts: `/tmp/sierra-kq1-final-typed-room`.
- `nonsense`: the original `I don't understand "nonsense".` response, including
  the `%w1` expansion and restored scene.
  Artifacts: `/tmp/sierra-kq1-unknown-word-v1` (earlier formatter build).
- Escape/Break menu opening and cancellation, with no lost memory.
  Artifacts: `/tmp/sierra-kq1-final-menu-19592` (final 19,592-byte build).

The K keyboard delivers byte 5 for its Break/Escape position. The program now
normalizes that to the game's byte-27 binding, disables the stdin quit/EOF
characters and echo while running, and restores those options after exit.
CTRL-C remains an interrupt. This fixes the observed Escape process abort;
it also explains why disabling the quit character alone did not open a menu.

Reproduce the command and menu checks using the usual harness parameters plus
`--typed-command 'look room'` or `--menu`. The harness accounts for MAME natural
keyboard injection time before taking its response snapshot. Do not treat a
partially injected command as a parser result.

The separate CPU acceptance test:

```sh
PATH=/tmp/sierra-headless-bin:$PATH python3 ../tests/check_wbgame_route.py
```

executes unmodified KQ1 resources, schedules Right/Down/Right input, and requires
room variables `(8,1)`, a rendered new scene and continued movement after the
castle's east exit. This test mocks OS services; it is not a MAME room-transition
claim. A southward diagnostic also progressed through the alligator follow,
reposition and death-message path. Controlled aborts recover all resources.

The final module also repeats the two-terminal picture-command diagnostic in
`/tmp/sierra-kq1-final-two-terminal-regression`. It checks exact scene pixels,
visibility switching, independent exits, relaunch and free-memory recovery.
It still does not establish that two full-resource games fit the 512 KB test OS.

Save/restore, audio, later-game completeness, physical-hardware acceptance and
performance parity remain open. The current evidence establishes interactive
startup, command handling, modal UI, movement and a real-script room transition,
not completion of the entire adventure.

An optional `GAME_TRACE=1` module now appends room, last raw key and menu-entry
count after the existing exit/opcode/stage fields. Normal builds omit these
fields and their recording instructions.


## Credits fix and sustained interaction

The 19,685-byte build passed `--sustained` in
`/tmp/sierra-kq1-sustained-credits-pause-verified`: original castle command, unknown-word
response, actual Escape menu navigation to Pause, exact pause-message font
pixels, resume, another castle command, interrupt exit and unchanged memory.
The castle screenshot was also inspected: startup credits no longer cover it.
The harness rejects the old credit glyph before and after inventory.

`check_wbcredits.py` separately verifies exact picture/text replacement at all
five allowed picture offsets on a real 6809 with mocked OS calls. The native
play suite verifies clock freezing across Pause and resumed clock progression.


## Movement optimization acceptance

Identical timed Right input on the 19,685-byte reference build and the
20,741-byte optimized build measured approximately 1 and 9 AGI pixels,
respectively, over 200 frames (3.33 emulated seconds). The estimate uses the
centre of Graham's visible shirt; animation can shift that centre slightly.
Artifacts: `/tmp/sierra-movement-before` and
`/tmp/sierra-movement-layer-cache` (includes `movement.json`). Use `--movement`
and optionally `--module-file` on `check_wbgame_mame.py` to reproduce it.
This establishes a substantial improvement in the castle scene; it does not
establish a general frame rate or original-interpreter timing parity.

The dirty-band build also passed sustained command/menu/Pause/restore and
free-memory checks in `/tmp/sierra-movement-sustained-final`.
The final palette-cached build repeats terminal-switch, exact-pixel,
independent-exit, relaunch and free-memory checks in
`/tmp/sierra-movement-two-terminals-no-mouse`. These are picture-command diagnostics,
not two simultaneous full-resource adventures.

Separate CPU acceptance covers every reference picture and glyph pixel,
normal and follow/move stepping, clipped/cross-page sprite erasure, the
large-cel fallback, all five picture offsets, bounded editors and modal
backups, Pause clocks and the real KQ1 room 1 to room 8 route. The deterministic
5/6-cycle KQ1 workload used 5,848/6,626 map calls before and 1,423/1,478 after the
dirty-band change: 778 versus 55 for the recurring cycle. Counts include mapped
source and destination slabs. OS calls are mocked for that measurement.

The headless MAME harnesses disable the UI cursor and host mouse provider.
This prevents host pointer movement from adding a hardware cursor to pixel
comparison screenshots; the rendered game and terminal pixels remain checked
without masking.

The subsequent bounded-text build (20,808 code / 24,572 private bytes) passed
the same movement harness at `/tmp/sierra-movement-text-spans`. It still
measured approximately nine pixels in 200 frames; the shorter text span
reduces work but did not improve this coarse movement measurement.

The mapped-fetch build (20,833 bytes) passed the real-driver movement harness
at `/tmp/sierra-movement-fetch-fast`, including inventory restoration and
unchanged free memory. The result remains approximately nine pixels in
200 frames; this test does not establish an additional movement speedup.

The shared-command build (20,966 code / 24,572 private bytes) passed
`--sustained` at `/tmp/sierra-shared-commands-sustained`: original-game
commands, unknown-word response, inventory restoration, menu Pause/resume,
subsequent input, interrupt exit, and unchanged free memory. The preceding
variable-only consolidation also passed `--movement` at
`/tmp/sierra-shared-variables-movement` (approximately nine pixels in
200 frames). That timing result is not a measurement of the later flag build.

The shared-condition build (21,068 code / 24,572 private bytes) passed
`--sustained` at `/tmp/sierra-shared-conditions-sustained`, including original
commands, unknown-word handling, inventory/modal restoration, Pause/resume,
subsequent input, interrupt exit, and unchanged free memory.

The shared-object-flags build (21,174 code / 24,572 private bytes) passed
`--sustained` at `/tmp/sierra-shared-object-flags-sustained`: original commands,
unknown-word handling, inventory/modal restoration, Pause/resume, subsequent
input, interrupt exit and unchanged free memory. The native pixel/motion
regression and cross-platform object-record checks also passed.

The shared-cycle/motion build (21,230 code / 24,572 private bytes) passed
`--sustained` at `/tmp/sierra-shared-cycle-motion-sustained`. The later rate
extraction produces the identical native binary. Native pixel/motion tests
and cross-platform state/rate/completion-flag checks also passed.

The shared-said/case-folding build (21,235 code / 24,572 private bytes) passed
`--sustained` at `/tmp/sierra-shared-said-sustained`, including typed original
commands, unknown-word response, inventory/modal restoration, Pause/resume,
subsequent input, interrupt exit and unchanged free memory. Cross-platform
said/folding and native compressed-vocabulary parser checks also passed.

## Current native game acceptance — 2026-10-06

Rebuilt the same MAME revision `078e0eeb` and multi-terminal OS revision
`c45760ab` in isolated temporary directories. The tested `wbgame` is 22,276
bytes and includes the resource-discard error propagation correction.
The module installed in the movement test disk matches `objs/wbgame` exactly.

- `check_wbgame_mame.py --movement`: real KQ1 startup, inventory glyphs,
  modal interaction/restoration, interrupt exit and unchanged memory passed.
  Movement measured nine AGI pixels over 200 frames (3.33 emulated seconds).
- `check_wbpic_mame.py --native-game ... --interpreter`: every displayed
  pixel, two terminals, picture restoration, independent exit, relaunch and
  free-memory maps passed.

Artifacts are `/tmp/sierra-view-cache-error-movement-verified` and
`/tmp/sierra-view-cache-error-terminals`. The OS Level 2/FEU builds and the
emulator source checkout are temporary; the user's OS tree was unchanged.
These tests verify emulator behavior, not physical hardware speed or full
adventure/save/restore/audio completion.

### Sprite visibility acceptance — 2026-10-06

The subsequent 22,322-byte game adds the shared per-cel ego-hidden rule
(24,571 private bytes). Both acceptance commands above passed again against
this build: nine AGI pixels over 200 frames, startup/inventory/modal/interrupt
cleanup, and two-terminal pixel restoration, independent exit, relaunch and
free-memory checks. Artifacts are
`/tmp/sierra-shared-sprite-visibility-movement` and
`/tmp/sierra-shared-sprite-visibility-terminals`. These emulator checks
complement the synthetic pixel/flag fixtures; they do not establish complete
adventure or physical hardware compatibility.

### Selected-cel clipping acceptance — 2026-10-06

The 22,379-byte native game (24,571 private bytes) shares CoCo's selected-cel
position adjustment and catches right-edge addition carry. Both acceptance
commands passed again: movement remains nine AGI pixels over 200 frames,
with startup/inventory/modal/interrupt cleanup and two-terminal restoration,
independent exit, relaunch and memory checks passing. Artifacts are
`/tmp/sierra-shared-cel-clipping-movement` and
`/tmp/sierra-shared-cel-clipping-terminals`.

The final scratch-reuse layout retains 22,379 code bytes and returns private
size to 24,570 bytes. Both acceptance commands passed with that exact build
as well; artifacts are `/tmp/sierra-shared-cel-clipping-scratch-movement` and
`/tmp/sierra-shared-cel-clipping-scratch-terminals`. Collection's temporary
sort key is reused only after the ordered list has been completed.

### Native indexed dispatch acceptance — 2026-10-06

The native platform comparison chain was replaced with relative entries
from the existing shared AGI catalog. The game is now 22,264 code bytes with
24,570 private bytes. Both acceptance commands passed against this build:
startup, inventory, modal/interrupt cleanup, movement and independent
two-terminal restoration, exit, relaunch and free-memory checks. Artifacts
are `/tmp/sierra-native-table-dispatch-movement` and
`/tmp/sierra-native-table-dispatch-terminals`. Movement still measures nine
AGI pixels over 200 frames; this is not evidence of a walking-speed increase.
The CPU destination test separately checks all opcode routes and preserved
entry state in the game and probe at two load addresses.

### Shared LZW window acceptance — 2026-10-06

The 22,316-byte native game (24,570 private bytes) now uses CoCo's shared
window shift/mask algorithm with bounded native byte acquisition. Both
acceptance commands passed with this build: real compressed-game startup,
inventory/modal/interrupt cleanup, movement, and independent two-terminal
restoration, exit, relaunch and memory checks. Artifacts are
`/tmp/sierra-shared-lzw-window-movement` and
`/tmp/sierra-shared-lzw-window-terminals`. Movement remains nine AGI pixels
over 200 frames; decoder correctness and per-code work are checked separately.

The complete 45-command native check suite also passed, including 228
compressed resources decoded by both actual owners and 528 direct code-window
reads. Extracting the dictionary walk afterward preserved all seven native
modules and all 56 CoCo modules byte for byte, including the exact game used
for these MAME acceptance runs.

### Packed picture loader acceptance — 2026-10-06

The 22,466-byte game (24,570 private bytes) passes the established King's Quest I
startup/inventory/modal/movement/interrupt-cleanup checks. Artifacts are
`/tmp/sierra-packed-kq1-movement`; movement remains nine pixels in 200 frames.
The separate Larry diagnostic run is not an acceptance pass: it stops at
unsupported opcode `$7A` (`add.to.pic`) before entering gameplay. Its trace
is at `/tmp/sierra-packed-larry-trace`. Actual CPU tests independently verify
all 443 packed pictures against CoCo and the host nibble oracle.

The complete 46-command regression suite passed with the packed-picture build,
including all 443 packed resources, both LZW owners, and the existing gameplay,
parser, resource-ownership and presentation checks. Log:
`/tmp/sierra-packed-full-check.log`.

### Static-picture commands acceptance — 2026-10-06

The 22,832-byte game (24,570 private bytes) passes KQ1 startup, inventory,
modal restoration, movement and interrupt cleanup at
`/tmp/sierra-addpic-kq1-movement`. Movement remains nine pixels per 200 frames.
All 56 CoCo modules also rebuild byte-identically to their pre-portability
baseline. Separate CPU fixtures verify every combined color/priority pixel
for static-picture drawing, restoration after animated-object erasure, input
cancellation, invalid arguments, replay overflow and ownership cleanup.

### Persistent-window build acceptance — 2026-10-06

The 23,009-byte game (24,570 private bytes) passes KQ1 startup, inventory,
modal restoration, movement and interrupt cleanup at
`/tmp/sierra-window-kq1-movement`. Two-terminal restoration, independent exit,
relaunch, every displayed reference pixel and free-memory checks also pass at
`/tmp/sierra-window-terminals`. Movement remains nine pixels per 200 frames.
CPU tests additionally exercise held-window restoration and save/restore
mapping failures; this MAME scenario does not itself keep a question window
open during terminal switching.

### Streamed picture input acceptance — 2026-10-06

The 23,072-byte game (24,570 private bytes) passes real KQ1 startup, inventory,
modal restoration, movement and interrupt cleanup at
`/tmp/sierra-stream-kq1-movement`. Movement remains nine pixels per 200 frames.
KQ4 picture 5, a 10,288-byte decoded packed resource, passes every displayed
reference pixel, two-terminal restoration, independent exit/relaunch and
free-memory checks at `/tmp/sierra-stream-large-picture-terminals`. That run
uses synthetic diagnostic game logic around the actual KQ4 picture.

The production game is byte-identical to the tested streaming prototype. All
56 CoCo modules rebuild byte-identically, and native probe rendering,
presentation and persistent-window regression checks pass. CPU tests compare
all 23 actual pictures above 8 KiB against CoCo and cover 65,535-byte input,
page-boundary/truncated commands, source map/unmap errors and ownership cleanup.

### Larry opening gameplay acceptance — 2026-10-06

The production 23,152-byte engine passes two scenarios with the original
Larry resources and real Wild Bits drivers:

- `check_wbgame_mame.py --larry`: age quiz, street scene, rightward walking,
  exact shared-font glyphs in the `look` response, all following message
  dismissals, scene restoration and interrupt/free-memory cleanup. Artifacts:
  `/tmp/sierra-larry-update-production`. Movement is about nine AGI pixels in
  400 frames; this establishes correctness, not a movement speed improvement.
- `check_wbgame_mame.py --larry-enter`: age quiz, approach to the door, the
  successful `open door` response, transition into Lefty's, interior `look`,
  dismissal and interrupt/free-memory cleanup. Artifacts:
  `/tmp/sierra-larry-enter-production`.

Both use the existing MAME/OS checkout and private test images described above.
The `stop.update` failure seen after the quiz is resolved. The harness sends
an explicit carriage return after interrupting: MAME's natural keyboard drops
a later LF following a prior CR, even across separate `post()` calls. Without
that correction, the shell cleanup command could inherit an unfinished line.
The walking measurement excludes the utility pole's white pixels and measures
the character's suit. These are opening gameplay checks; save/restore, audio,
full adventure completion and simultaneous real-game runs remain separate.
