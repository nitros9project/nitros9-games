# Reversi

Joel Matthew Rees's 1991 graphical OS-9/CoCo version of Reversi, imported
from the Microware archive's Reversi.lzh package. The author's source notice
assigns the program and generated object code to the public domain.

## Build and run

Compilation stays in this repository:

```sh
make -C ../../nitros9-languages/c3 runtime
make
```

`make` produces `build/reversi`. `make clean` removes compilation output.
For a bootable disk or MAME launch, use the sibling NitrOS-9 recipe:

```sh
make -C ../../nitros9/recipes/coco3/games GAME=reversi
make -C ../../nitros9/recipes/coco3/games GAME=reversi run MAME_ROM_PATH=/path/to/roms
make -C ../../nitros9/recipes/coco3/games GAME=reversi check MAME_ROM_PATH=/path/to/roms
```

The recipe builds c3 and the game, packages the OS and assets, and selects
`coco3h` when `CPU=6309`. Images and emulator state live under the NitrOS-9
recipe's `.build/reversi/CPU/TRANSPORT/` directory. Use `LANGUAGES` and
`NITROS9_GAMES_DIR` there to override sibling paths, and `MAME_BINARY` to
select the emulator. See `nitros9/recipes/coco3/games/README.md` for details.

## Controls

Enter a skill level from 0 to 7, choose which colors the computer plays,
and select whether the opening four pieces are diagonal. Press Enter at
the start prompt. Use cursor keys to choose a square and Enter to play.
`C` asks the computer to choose your move; `Q` requests exit with confirmation.
The game also pauses between turns for a key press.

## Port changes

- Replace stack-offset-dependent inline assembly for board addressing,
  coordinate conversion, copying, and random generation with C equivalents.
- Retain the original font and piece images, adjusting comma spacing for lwasm.
- Supply an eight-argument graphics-buffer loader that writes the buffer data,
  using the current c3 calling convention.
- Assemble the supporting graphics primitives from c3, and use the process ID
  for the game's graphics-buffer group.
- Fix keyboard readiness checking to use its path argument.
- Use the C locale so the assembly filter accepts generated high-bit font text.

## Validation

The module builds and links with a good OS-9 CRC. MAME checks exercised
preferences, the opening position, graphics/font buffers, and a
computer-assisted move. Full matches and physical hardware are not tested.

The shared recipe's `check` target verifies startup and captures the screen.
It does not assert the game rules or play a full match.

## Origin

[Reversi.lzh](https://microware.com/index.php/os-9-archive-new/file/2751-os-9-archive)
contains the C source, original inline assembly, font/piece data, and a
historical executable. Original source notices are retained.
