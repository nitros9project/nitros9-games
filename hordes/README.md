# Hordes & Holes

Action game in an 80-column text window. Lure the monsters into holes.

Original author: Bruce Terry (1988). Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/hordes`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=hordes
make -C ../../nitros9/recipes/coco3/games GAME=hordes run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=hordes check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/hordes/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

## Play

Choose sound and keyboard/joystick at startup. Use the cursor keys to move.

## Port notes

Replaced the floating-point board-position generator with integer arithmetic, corrected two monster-coordinate assignments and the left-joystick selector, removed an unavailable mouse header, and preserve terminal echo/pause settings.

Game field and monsters displayed in MAME; startup sound/keyboard selections exercised. Physical hardware has not been tested.

## Origin and distribution

Imported from [HordesAndHoles.lzh](https://microware.com/index.php/os-9-archive-new/file/2733-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
