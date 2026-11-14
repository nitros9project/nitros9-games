# Pyramid Solitaire 1.4

Graphical Pyramid Solitaire with its card artwork built into the source.

Original author: Zack C. Sessions / ColorSystems (1989). Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/solitaire`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=solitaire
make -C ../../nitros9/recipes/coco3/games GAME=solitaire run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=solitaire check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/solitaire/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

## Play

Choose RGB or composite with the mouse, click the title screen, and use the card/deck/menu controls.

## Port notes

Add missing global/constants, create the documented standalone type-6 graphics window, and provide current-ABI mouse/window/get-put wrappers. Graphics primitives are assembled from c3 sources.

MAME verified monitor selection, the title click, card-image generation, and the dealt pyramid. Full games have not been played through. Physical hardware has not been tested.

## Origin and distribution

Imported from [Solitaire.lzh](https://microware.com/index.php/os-9-archive-new/file/2762-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.

The original documentation permits free distribution with copyright notices
intact and prohibits selling or profiting from the software; it is not public
domain. See the complete original notice in `docs/`.
