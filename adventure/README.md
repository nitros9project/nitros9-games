# Adventure

Text adventure with the six original data files.

Original author: Crowther/Woods adventure; historical Microware C source package. Original documentation is retained under `docs/`.

## Cross-build

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/adventure`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=adventure
make -C ../../nitros9/recipes/coco3/games GAME=adventure run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=adventure check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/adventure/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

## Play

Answer the instruction prompt, then enter one- or two-word commands. Try look, inventory, north, or help. quit exits; suspend saves.

## Port notes

Preserve the database files byte-for-byte and install them under /dd/GAMES/ADVENT. Use the current c3 compiler/runtime and link in-tree startup objects.

MAME loaded the database and answered look with the starting location description. Database indexing takes time on floppy. Physical hardware has not been tested.

## Origin and distribution

Imported from [Adventure.lzh](https://microware.com/index.php/os-9-archive-new/file/2717-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
