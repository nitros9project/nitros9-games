# Sokoban

Box-pushing puzzle with 50 levels, saved games, and score tables.

Original author: OS-9 conversion by Tom Napolitano (1989). Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/sokoban`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=sokoban
make -C ../../nitros9/recipes/coco3/games GAME=sokoban run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=sokoban check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/sokoban/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

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
