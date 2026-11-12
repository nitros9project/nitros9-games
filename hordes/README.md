# Hordes & Holes

Action game in an 80-column text window. Lure the monsters into holes.

Original author: Bruce Terry (1988). Original documentation is retained under `docs/`.

## Cross-build

Requires the sibling C-Cubed checkout, a native C compiler, LWTOOLS
(`lwasm`, `lwar`, `lwlink`), and ToolShed `os9` for disks.

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` produces `build/hordes`. `make disk` builds a private NitrOS-9
Level 2 boot floppy at `build/emulator/hordes.dsk`. `make run` boots a
512K CoCo 3 in MAME and starts the game with `/term` connected to its input.
Boot modules, libraries, system fonts, and disk artifacts stay under `build/`.
`make clean` removes the build directory and root `.list`/`.map` files.

Override sibling/tool paths as needed:

```sh
make run C3ROOT=/path/to/c3 NITROS9DIR=/path/to/nitros9 \
    MAME_ROM_PATH=/path/to/roms
```

`MAME` selects the executable. `MAME_FLAGS` defaults to
`-window -skip_gameinfo -ramsize 512k`. ROMs default to
`~/.local/share/mame/roms`. The NitrOS-9 checkout supplies the boot sources;
its CoCo 3 recipe builds in this port's `build/emulator` directory.
The game can also be copied into an existing OS-9 execution directory;
set its execute attributes with `os9 attr -e -pe` after copying to an image.

## Play

Choose sound and keyboard/joystick at startup. Use the cursor keys to move.

## Port notes

Replaced the floating-point board-position generator with integer arithmetic, corrected two monster-coordinate assignments and the left-joystick selector, removed an unavailable mouse header, and preserve terminal echo/pause settings.

Game field and monsters displayed in MAME; startup sound/keyboard selections exercised. Physical hardware has not been tested.

## Origin and distribution

Imported from [HordesAndHoles.lzh](https://microware.com/index.php/os-9-archive-new/file/2733-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
