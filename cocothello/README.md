# CoCothello 1.2

Graphical Othello game with a computer opponent and mouse/joystick interface.

Original author: Zack C. Sessions / ColorSystems (1989). Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/cocothello`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=cocothello
make -C ../../nitros9/recipes/coco3/games GAME=cocothello run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=cocothello check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/cocothello/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

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
