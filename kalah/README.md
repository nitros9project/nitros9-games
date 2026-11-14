# Kalah

Kalah and Dead-Pan strategy games with minimax and alpha-beta search.

Original author: Michael J. Knudsen. Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/kalah`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=kalah
make -C ../../nitros9/recipes/coco3/games GAME=kalah run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=kalah check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/kalah/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

## Play

Choose k for Kalah or p for Pigeons/Dead-Pan, choose computer skill, then select who moves first. Follow the printed prompts.

## Port notes

Compile the supplied movesrc.c alternative instead of the old hand-optimized move.a calling convention. Replace the four integer scanf calls with a decimal input helper, avoiding an unused floating-point dependency in the current runtime.

MAME exercised game selection, skill selection, a human move, and the computer response. Physical hardware has not been tested.

## Origin and distribution

Imported from [Kalah.lzh](https://microware.com/index.php/os-9-archive-new/file/2734-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
