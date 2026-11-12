# Adventure

Text adventure with the six original data files.

Original author: Crowther/Woods adventure; historical Microware C source package. Original documentation is retained under `docs/`.

## Cross-build

Requires the sibling C-Cubed checkout, a native C compiler, LWTOOLS
(`lwasm`, `lwar`, `lwlink`), and ToolShed `os9` for disks.

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` produces `build/adventure`. `make disk` builds a private NitrOS-9
Level 2 boot floppy at `build/emulator/adventure.dsk`. `make run` boots a
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

Answer the instruction prompt, then enter one- or two-word commands. Try look, inventory, north, or help. quit exits; suspend saves.

## Port notes

Preserve the database files byte-for-byte and install them under /dd/GAMES/ADVENT. Use the current c3 compiler/runtime and link in-tree startup objects.

MAME loaded the database and answered look with the starting location description. Database indexing takes time on floppy. Physical hardware has not been tested.

## Origin and distribution

Imported from [Adventure.lzh](https://microware.com/index.php/os-9-archive-new/file/2717-os-9-archive)
in the Microware OS-9 archive. Source notices and original documentation
are retained. No new license is asserted over the imported material.
