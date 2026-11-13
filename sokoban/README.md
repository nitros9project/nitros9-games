# Sokoban

Box-pushing puzzle with 50 levels, saved games, and score tables.

Original author: OS-9 conversion by Tom Napolitano (1989). Original documentation is retained under `docs/`.

## Cross-build

Requires the sibling C-Cubed checkout, a native C compiler, LWTOOLS
(`lwasm`, `lwar`, `lwlink`), and ToolShed `os9` for disks.

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` produces `build/sokoban`. `make disk` builds a private NitrOS-9
Level 2 boot floppy at `build/emulator/sokoban.dsk`. `make run` boots a
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

Enter a player name. Use h/j/k/l to move, u to undo, U to restart the level, s to save and exit, q to quit, and ? for help. Run sokoban -r to restore.

## Port notes

Use the supplied mini-curses implementation, add the CoCo tick-based sleep helper, preserve terminal settings on both input and output paths, reject empty names, and save the complete map rather than its old truncated byte count. Save paths are closed and temporary allocations released.

MAME exercised level loading, one move, save, restart, and restore with the move count and player position retained. Physical hardware has not been tested.

## Origin and distribution

Imported from [Sokoban.lzh](https://microware.com/index.php/os-9-archive-new/file/2761-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.

The disk contains all 50 levels in `SCREENS` and an empty `sok.score` file.
Save/score changes persist on the emulator disk until it is rebuilt or cleaned.
The corrected save-map layout is incompatible with old truncated save files.
