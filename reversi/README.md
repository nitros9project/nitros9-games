# Reversi

Joel Matthew Rees's 1991 graphical OS-9/CoCo version of Reversi, imported
from the Microware archive's Reversi.lzh package. The author's source notice
assigns the program and generated object code to the public domain.

## Build and run

Requires the sibling c3 and NitrOS-9 source trees, LWTOOLS, and ToolShed.
Build the c3 host compiler and runtime once:

```sh
make -C ../../nitros9-languages/c3 runtime
make
make disk
make run
```

`make` creates `build/reversi`. `make disk` creates a private bootable
NitrOS-9 Level 2 disk at `build/emulator/reversi.dsk`. `make run` boots it in
MAME as a 512K CoCo 3 and connects the game to `/term`. Game preferences
appear on the terminal; the board opens in its own graphics window.

For another checkout or ROM location:

```sh
make run C3ROOT=/path/to/c3 NITROS9DIR=/path/to/nitros9 \
    MAME_ROM_PATH=/path/to/roms
```

`MAME` selects the emulator executable; `MAME_FLAGS` defaults to
`-window -skip_gameinfo -ramsize 512k`. ROMs default to
`~/.local/share/mame/roms`. `make clean` removes build output and root
listing/map files. This port builds independently of the repository's
aggregate target.

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

`make smoke` runs the scripted MAME check and saves screen captures in
`build/verification`. These captures are for visual inspection; the script
does not assert the game rules. All emulator artifacts stay under `build/`.

## Origin

[Reversi.lzh](https://microware.com/index.php/os-9-archive-new/file/2751-os-9-archive)
contains the C source, original inline assembly, font/piece data, and a
historical executable. Original source notices are retained.
