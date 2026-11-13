# Kalah

Kalah and Dead-Pan strategy games with minimax and alpha-beta search.

Original author: Michael J. Knudsen. Original documentation is retained under `docs/`.

## Cross-build

Requires the sibling C-Cubed checkout, a native C compiler, LWTOOLS
(`lwasm`, `lwar`, `lwlink`), and ToolShed `os9` for disks.

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` produces `build/kalah`. `make disk` builds a private NitrOS-9
Level 2 boot floppy at `build/emulator/kalah.dsk`. `make run` boots a
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

Choose k for Kalah or p for Pigeons/Dead-Pan, choose computer skill, then select who moves first. Follow the printed prompts.

## Port notes

Compile the supplied movesrc.c alternative instead of the old hand-optimized move.a calling convention. Replace the four integer scanf calls with a decimal input helper, avoiding an unused floating-point dependency in the current runtime.

MAME exercised game selection, skill selection, a human move, and the computer response. Physical hardware has not been tested.

## Origin and distribution

Imported from [Kalah.lzh](https://microware.com/index.php/os-9-archive-new/file/2734-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
