# Wild Bits MAME acceptance

Use the [Wild Bits MAME fork](https://github.com/rlucente-retro/mame), branch
`wildbits-jr2`, machine `wbjr2`, and `-bios turbo`. Stock/Homebrew MAME does
not provide this machine. The OS image needs the extended drivers from
[NitrOS-9's `wb/multiterm` branch](https://github.com/jfed6000/nitros9/tree/wb/multiterm).
The [porting guide](https://github.com/jfed6000/f256_porting) describes this
emulator and explains why it must not be used to establish hardware timing.

## Prepare an interactive game

The existing acceptance runner can prepare a separate playable image without
running its scripted controls or exiting MAME automatically:

```sh
python3 sierra/tests/check_wbgame_mame.py --prepare-play \
  --mame /path/to/mamed --disk /path/to/wildbits.dsk \
  --firmware /path/to/nitros9/recipes/wildbits/feu \
  --game /path/to/converted/game --output /tmp/sierra-play
/tmp/sierra-play/play.sh
```

Run this from the games repository after `make -C sierra/objs -f wildbits.mk all`.
The output directory must be new. The runner copies the source disk, matching
current `wbgame`, `wbstate`, and `wbfont`, and converted game resources into the
private image. Optional `--sol-driver` and `--expanded-krnp2` have the same meaning
as in acceptance tests. Neither the source disk nor an existing emulator is
changed. The launcher uses normal display, sound and throttling, with the MAME
UI initially disabled so the emulated computer receives keys. It starts the
game after boot; press Space through the introduction, press an arrow to walk
and press the same arrow again to stop,
Escape for the game menu, and Ctrl-C to return to NitrOS-9. Scroll Lock toggles
MAME UI controls. The disk retains saved games between launches.

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

### Two original games and expanded-memory test image — 2026-10-06

The 512-KiB Jr2 kernel leaves only 56 KiB free with Larry running. Launching
original KQ1 on a second terminal reaches the driver's error 32 (`E$MFull`);
Larry remains usable and both failed-launch and final cleanup recover memory.
This is a capacity limit, not successful simultaneous gameplay. Artifacts:
`/tmp/sierra-real-games-pair`.

The current MAME core (`078e0eeb7ea1c7eb3b4445329f109586f1fdd29c`) implements
the upper SRAM windows. The current OS source
(`c45760abeb03c39197ca8e569d5afb621bef8cc7`) contains the expanded block map,
but enables it only for K2. A private emulator-only Jr2 kernel overlay enables
that existing map: RAM blocks `$00-$3F`, `$A0-$BF` and `$D0-$EF` (1 MiB total),
with all intervening flash/I/O/undecoded gaps still marked unavailable. Neither
the application nor the user's OS checkout is modified for this experiment.
It does not establish that an older physical Jr2 core has those windows.

The original Larry/KQ1 two-terminal scenario passes with this overlay. KQ1
opens inventory on its terminal, both game scenes restore after switching,
Larry survives KQ1's independent exit, and the Larry-only and final memory
maps restore exactly. Before/after both games: 848 KiB free. Before/after
KQ1 while Larry remains alive: 568 KiB free. The repeatable scenario is
`check_wbgame_mame.py --larry-pair ../kingsquest1`; the stock 512-KiB image
cannot pass it. The final 23,162-byte production engine passes through the repeatable overlay
path at `/tmp/sierra-real-pair-final`; earlier artifacts are
`/tmp/sierra-real-pair-production`.

`--expanded-krnp2 /path/to/krnp2` replaces only that module inside the harness's
private disk copy. It validates the module name/size, retains the bootfile's
leading FF alignment to 256 bytes, and enforces the recipe's 32,256-byte limit.
The tested replacement is 3,290 bytes, SHA256
`98acf809d94d357cfe1bd8d02383b3dcea03aed7cc2ba6908fc180f810b03549`.

To reproduce the kernel overlay from the OS source revision above, copy
`level2/modules/kernel/krnp2.asm` to a temporary file. Change **only** its two
`IFNE k2` gates for the block-map extension and `NotRAMTbl` to
`IFNE k2+SIERRA_RAMWINDOWS`. Assemble the temporary source with:

```sh
lwasm.orig --6809 --format=os9 --no-warn=ifp1 \
  --pragma=pcaspcr,nosymbolcase,condundefzero,undefextern,dollarnotlocal,noforwardrefmax \
  -I"$NITROS9DIR/defs" -I"$NITROS9DIR/level2/wildbits" \
  -I"$NITROS9DIR/level2/modules/kernel" -I"$NITROS9DIR/level1/modules/kernel" \
  -Dwildbits=1 -Djr2=1 -DSIERRA_RAMWINDOWS=1 \
  -DNOS9VER=0 -DNOS9MAJ=0 -DNOS9MIN=0 \
  -o /tmp/sierra-expanded-krnp2 /tmp/sierra-expanded-krnp2.asm

python3 ../tests/check_wbgame_mame.py \
  --mame /tmp/sierra-wildbits-mame-current/mamed \
  --disk "$NITROS9DIR/recipes/wildbits/l2/l2_wildbitsjr2.dsk" \
  --firmware "$NITROS9DIR/recipes/wildbits/feu" \
  --game ../leisuresuitlarry --larry-pair ../kingsquest1 \
  --expanded-krnp2 /tmp/sierra-expanded-krnp2 \
  --output /tmp/sierra-real-pair-repeat
```

The application remains on the public allocation, mapping and terminal APIs.
The guide's signal-driven pacing approach is described in
[section 12.2](https://github.com/jfed6000/f256_porting#122-keeping-time-when-a-pass-can-overrun-the-sol-clock);
the stock test driver sends SOL signals, but lacks shared-line broadcasting,
PID-scoped removal, and the public counter needed by the current safe frame gate.

The native frame gate can be exercised with `--sol-driver PATH/TO/SOLdrv`.
The harness validates and replaces only that named module in its private
boot image, retaining FF padding and the recipe's size/alignment limit. It
can be combined with `--expanded-krnp2` for the two-original-game test. The
shared-clock prerequisite is on the isolated NitrOS-9 branch
`codex/wildbits-sol-frame-clock`; the user's active OS branch is unchanged.
The current prerequisite is commit `edaa2283`: `I$GetStt SS.SOLIRQ` returns
capability flags 7 in X and a modulo-65536 line-zero counter in Y. The game
registers `S$Wake`, whose pending slot can be replaced by Ctrl-C, and samples
the counter through that public service. Drivers with only capability flags
3 retain the sleep fallback. Current single/two-game acceptance artifacts
are `/tmp/sierra-larry-wake-clock-verified` and `/tmp/sierra-pair-wake-clock`.
Both verify interrupt cleanup and unchanged free-memory maps.

A counter-capable driver can be assembled from the isolated OS worktree:

```sh
lwasm.orig --6809 --format=os9 \
  --pragma=pcaspcr,nosymbolcase,condundefzero -Dwildbits=1 -Djr2=1 \
  -I/tmp/sierra-sol-os-worktree/level2/wildbits \
  -I/tmp/sierra-sol-os-worktree/defs \
  -o /tmp/sierra-sol-counter \
  /tmp/sierra-sol-os-worktree/level1/wildbits/modules/SOLdrv.asm
```

Add `--sol-driver /tmp/sierra-sol-counter` to either game acceptance command.
This patches only its private emulator image; it does not update the user's
active OS checkout or physical machine.


## Native persistence checks

Add `--interpreter --persistence --overlay` to the two-terminal picture harness
with the King's Quest I resource directory. It checks saved variables and every
pixel, validates the extracted file independently, rejects malformed/truncated
snapshots, preserves an existing save, then checks independent exit/relaunch and
exact free-memory recovery. `check_wbgame_mame.py --persistence --game
sierra/kingsquest1` uses the original game's `save game` and `restore game`
commands, walks out of the castle, restores Graham's position and exercises
another command. Install `wbstate` alongside `wbgame` and `wbfont`; both harnesses
now do so in their disposable disk images.

Completed runs are recorded in [WILDBITS-ENGINE.md](WILDBITS-ENGINE.md).
Full-adventure completion remains unverified.

To verify native sound with the process-owned version-4 PSG driver installed
in the test bootfile, add `--audio-trace` to `check_wbgame_mame.py`. The check
requires AGI command 99 and non-muted PSG store instructions while a process
owns the device; it writes the captured bytes to `audio-writes.json`. It uses
the existing disposable disk workflow and leaves the player's emulator alone.


## Owned native sound and modal refill acceptance — 2026-10-06

The production engine is 23,788 bytes with 24,460 bytes of declared private
storage. Its paired `wbstate` helper is 3,550 bytes. Install both from the same
build: the helper ABI includes the audio workspace and callback layout.
The version-4, 1,370-byte PSG driver is preserved on local NitrOS-9 branch
`codex/sierra-owned-psg` at `f99a8196`; its base is the tested Wild Bits terminal
revision `c45760ab`, rather than the active OS checkout's terminal ABI.

The existing game resources contain converted CoCo single-voice notes.
The driver translates these to queued PSG tones; the discarded original
voices and CoCo envelope behavior are not reconstructed. PSG traces verify
non-muted hardware register writes, not speaker output or musical fidelity.

The final engine passed these private MAME runs with the matched PSG bootfile
and verified SOL raster counter:

- King's Quest I startup, inventory, save, walking, restored position,
  subsequent `look room`, interrupt exit and exact memory recovery:
  `/tmp/sierra-modal-audio-kq1-verified` (59 owned PSG writes).
- Original Larry and KQ1 together on separate terminals, independent inventory
  input, restored screens, Larry surviving KQ1 exit and exact memory recovery:
  `/tmp/sierra-modal-audio-pair` (83 owned PSG writes). This uses the documented
  emulator-only expanded-memory kernel.
- Original Larry's door interaction, transition into Lefty's, inside-room look,
  dismissal and cleanup: `/tmp/sierra-final-larry-leftys` (15 owned PSG writes).
- KQ1 movement with audio enabled: 32 AGI pixels in 200 frames, or 3.33 emulated
  seconds; `/tmp/sierra-owned-audio-movement` (427 owned PSG writes). These are
  emulated time measurements, independent of the host's unthrottled speed.

The native CPU audio test separately holds a Pause dialog open longer than an
eight-note queue can cover. Fourteen one-tick notes and all end markers finish
before dismissal, proving that modal waits refill without a next interpreter
cycle. Missing/incompatible helpers, missing/older drivers, busy-then-available
retry, reused completion flags, malformed notes, deep logic calls, ownership
release and immutable private code also pass. The complete gameplay CPU suite
passes after these changes. Physical hardware remains untested.


## Cached text backend and positioned messages — 2026-10-07

The current matched pair is `wbgame` 23,794 bytes and `wbstate` 3,778 bytes,
with 24,460 bytes of declared private data. `wbstate` is required for text output;
its immutable text code retains one DAT window until exit. Install all three
production files (`wbgame`, `wbstate`, `wbfont`) from the same build. The helper
ABI is version 2; the save-file schema remains version 1.

The geometry probe `/tmp/sierra-cold-window-probe` verified resource mapping at
`$6000` while the helper remained linked. The final engine passed original KQ1
save/restore and subsequent input at `/tmp/sierra-positioned-kq1`, and two
original games with independent terminal input, switching and exits at
`/tmp/sierra-positioned-pair` (80 owned PSG writes). Both recovered memory exactly.
The latter uses the expanded-memory test kernel. CPU cases additionally verify
positioned-message wrapping/clipping, immutable helper bytes, link cleanup,
repeated text/graphics switches and early font errors.


The timed-message build also passes original KQ1 save/restore and subsequent
input at `/tmp/sierra-timed-kq1`, capturing 59 owned PSG writes. The independent
Larry/KQ1 terminal test passes at `/tmp/sierra-timed-pair`, capturing 80 writes
with the documented expanded-memory emulator kernel. These runs exercise the
relocated immutable modal wait/key loop against real drivers. Timer arithmetic,
foreground rebasing and invalid entry cleanup have separate CPU fixtures in
`check_wbgame.py`; the original-resource MAME runs are integration checks.


### Real raster timing of modal messages

`tests/check_wbgame_timers_mame.py` generates its own AGI logic and messages,
clones the supplied disk/firmware, and runs a private headless MAME instance.
It does not require game assets. The disk or optional `--boot-file` must contain
the public SOL counter driver. For example:

```sh
python3 tests/check_wbgame_timers_mame.py \
  --mame "$MAME" --disk "$DISK" --firmware "$FEU" \
  --boot-file "$COUNTER_BOOT" --output /tmp/wbgame-timer-check
```

The test records resident wait/restore boundaries in CPU cycles and confirms
that the same non-`$FF` SOL path is active at both boundaries. Under the Jr2 turbo
clock, a half-second print measured 0.49174 seconds; a one-second `print.v`
measured 0.99451 seconds; positioned half-second prints measured 0.49380 and
0.49375 seconds. The final untimed print remains visible until keyboard
input. Exact completion-message glyphs, normal process exit and identical
before/after free-memory maps also pass (`/tmp/sierra-timed-counter-final`).
The slight sub-frame difference follows the phase of the existing raster counter.
The test preserves events, timing, screenshots, command line and disk artifacts.


The split-prefix build passes original KQ1 save/restore at
`/tmp/sierra-cold-rect-kq1` and the independent Larry/KQ1 terminal test at
`/tmp/sierra-cold-rect-pair`. This verifies state copying after the linked helper
exceeds 4 KiB, with the writable prefix still bounded below 4 KiB and the
existing shared code window retained. The pair captures 80 owned PSG writes and
recovers its one-game and final free-memory maps. The full native CPU suite also
checks rectangle colors/bounds and helper immutability with aligned test banks.


### Original KQ1 menu restart

Run `tests/check_wbgame_mame.py` with the usual `--mame`, `--disk`,
`--firmware`, `--game` and fresh `--output` arguments, plus `--restart`.
Use `--sol-driver` for the public counter driver and `--audio-trace` to verify
owned PSG writes. The test walks Graham, selects Restart from the Game menu,
confirms with ENTER, checks root unwinding and restart flag 6, then types
`look room`. Red-shirt positions move from 449.5 to 625.5 and return to 449.5
after restart. Exit recovers the original free-memory map.
`/tmp/sierra-restart-kq1-safe` contains screenshots, debugger trace and
`restart.json`; 59 owned PSG writes were observed.

The same build passes save/restore (`/tmp/sierra-restart-save-safe`) and
independent Larry/KQ1 terminal tests (`/tmp/sierra-restart-pair-safe`, expanded
emulator kernel). CPU tests separately cover cancellation, automatic restart
and the maximum-depth, 127-character-directory stack regression.


### Generated inventory preview on real drivers

`tests/check_wbgame_previews_mame.py` requires no commercial game assets. It
clones the disk/firmware and installs generated logic, picture and view resources.
Run with `--mame`, `--disk`, `--firmware` and a fresh `--output` directory;
`--boot-file` optionally supplies a matching OS9 boot image. `--interrupt` uses
Ctrl-C for cleanup instead of the bound quit controller. The test checks
exact item pixels and description glyphs while visible, dismisses the dialog,
checks subsequent script execution and exact scene restoration, then uses a
bound controller to quit and compares before/after memory maps. Its paced idle
loop avoids using unbounded script execution as an emulator test clock.

The passing run is `/tmp/sierra-preview-real-drivers-controlled`. Original KQ1
save/restore passes at `/tmp/sierra-preview-original-kq1`; independent Larry/KQ1
terminals pass at `/tmp/sierra-preview-pair` with the expanded emulator kernel.

### Generated screen-shake regression

Run `tests/check_wbgame_previews_mame.py` with its usual emulator, disk and
firmware arguments plus `--shake`. Supply `--boot-file` with a compatible
SOL-counter/PSG boot image to exercise public counter timing. The generated
fixture needs no commercial assets. It checks eight alternating phases, shifted
and restored sprite pixels, subsequent script execution and free-memory recovery.
Snapshots use a dedicated snapshot directory, and cold breakpoints follow the
actual helper load address rather than assuming a bank window.

`/tmp/sierra-shake-final-pixels` passes with the public counter active and a
0.723-second repeat. CPU tests additionally compare the entire bitmap, including
the reserved dialog tail, and exercise the sleep fallback.

The same generated UI regression accepts `--version` to check opcode 141's
two-line interpreter information, dismissal, scene restoration and cleanup.
It passes at `/tmp/sierra-version-real-drivers`. `--version` and `--shake`
are mutually exclusive.

The cold-menu helper passes original KQ1 `--restart` at
`/tmp/sierra-cold-menu-restart`, two games with `--larry-pair` at
`/tmp/sierra-cold-menu-pair`, and `--larry-enter` at
`/tmp/sierra-cold-menu-leftys`. The last test verifies the open-door response,
transition into Lefty's, inside look/dismissal and full cleanup, using actual
game resources rather than a generated startup fixture.

The generated UI regression accepts `--joystick` to check real `SS.Joy`
availability, neutral readings, enable/toggle, continued keyboard quit and
free-memory recovery. This MAME revision returns open-bus values at the
unmodeled VIA joystick port; the terminal driver interprets them as neutral.
This test does not claim emulated physical direction/button support. CPU fixtures
provide those samples and verify the game adapter across complete AGI cycles.

For movement comparisons with an earlier binary, `check_wbgame_mame.py` now
accepts `--helper-file` alongside `--module-file`; supply a matching pair.
The pre/post joystick runs at `/tmp/sierra-joystick-movement-before` and
`/tmp/sierra-joystick-movement-after` each measure 32 AGI pixels in 200 frames.
