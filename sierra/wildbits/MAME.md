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

Build the OS tree's `recipes/wildbits/l2` and `recipes/wildbits/feu` recipes
with `PLATFORM=jr2`; the FEU recipe needs both `all` and `f0.dsk` targets.
Set `NITROS9DIR` to that tree and `LANGUAGES` to the sibling language tree.
Build libraries before parallel linking, or use a serial recipe build.
At the OS revision below, the Level 2 recipe references a missing `vs.asm`;
this run supplied the existing workspace's `level1/wildbits/cmds/vs.asm` in
the temporary OS tree. That command is unrelated to `wbpic` or graphics.

The test requires `os9` (ToolShed) on PATH and an already-built `wbpic`.

## Run

From `sierra/wildbits`:

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
in physical hardware/extended runtime acceptance work. The module is still
a combined-buffer viewer; native game-resource decoding and a playable
interpreter remain future milestones.

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

## Native line decoder

Add `--decode` to the resource-loader test command to exercise `wbdecode`.
The default fixture then contains color/priority, absolute-line, relative-line
and coordinate-clamping commands. The test runs the existing CoCo renderer
as a CPU reference, runs the native decoder under the real Wild Bits OS,
and compares all 26,880 combined bytes. This reference step also requires
XRoar and lwasm on PATH. Use a fresh output directory for each run.

This passed on the same emulator/OS revisions with native module size 1,400
bytes and CRC `$EF5D62`. The combined output hash was
`41b1095683a9252eadcd883f97ffed28467ef96a257f63b4084980d592a3cdd4`.
The fixture is diagnostic, not a complete game picture. `wbdecode` rejects
fill and pen opcodes; its resident probe buffer still needs a mapped backend
before the full interpreter can use it.
