# CoCothello 1.2

Graphical Othello game with a computer opponent and mouse/joystick interface.

Original author: Zack C. Sessions / ColorSystems (1989). Original documentation is retained under `docs/`.

## Cross-build

Requires the sibling C-Cubed checkout, a native C compiler, LWTOOLS
(`lwasm`, `lwar`, `lwlink`), and ToolShed `os9` for disks.

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` produces `build/cocothello`. `make disk` builds a private NitrOS-9
Level 2 boot floppy at `build/emulator/cocothello.dsk`. `make run` boots a
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

The boot script chooses RGB/fast mode. Click the title screen, select the strategy options, and click board squares. Keyboard mouse and joystick controls depend on the NitrOS-9 input driver.

## Port notes

Add missing global/constants, create the documented standalone type-6 graphics window, replace the floating-point parity helper with integer parity, and provide current-ABI mouse/window/get-put wrappers. Graphics primitives are assembled from c3 sources.

MAME verified the title, mouse click handling, board rendering, and strategy-selection interface. Full games have not been played through. Physical hardware has not been tested.

## Origin and distribution

Imported from [CoCothello.lzh](https://microware.com/index.php/os-9-archive-new/file/2726-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.

The original documentation permits free distribution with copyright notices
intact and prohibits selling or profiting from the software; it is not public
domain. See the complete original notice in `docs/`.
