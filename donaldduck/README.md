# Donald Duck’s Playground for NitrOS-9 / Wildbits

This is a native 6809 OS-9 binary-adapter port of the preserved two-disk edition.
It retains the original game code and six activity modules and adds a
position-independent Wildbits display, keyboard/joystick, sound, and cleanup
layer. The two original disks’ assets are combined in one data directory.

## Build and run a Jr2 image

Build the adapter with `make`, then create an image from your own Wildbits Jr2
NitrOS-9/FEU base disk:

```sh
python3 tools/make_image.py /path/to/base-jr2.dsk DDP-Wildbits-Jr2.dsk
```
The image boots to a shell in `/s0/ddp`. Type:

```text
DONALD
```

At the title screen, press **Enter**. Use **Up/Down** to choose the difficulty,
then **Space** to accept. Press **Enter** to dismiss the instruction screen.
The original town and activities then use **arrow keys** for movement and
**Space** for the joystick button. A stick on port zero also supplies these
controls. **Q** exits and returns to the shell; release Q before typing there.
Q also works during the airport animation and sound sequences. The title’s
original **F** color-phase adjustment remains available.

Use a Jr2 base disk for the Jr2 emulator; this does not create a K2 boot configuration. For a K2
or an existing installation, install the game files below into your own OS.

## Install in an existing Wildbits system

Requires NitrOS-9 Level 2 and a modern graphics driver providing:

- `SS.AScrn`, `SS.BmBlk`, `SS.FScrn`, `SS.Palet`, `SS.PScrn`, `SS.DScrn`;
- `SS.ClutWrite` ($CF), `SS.LiveKeys` ($C6), `SS.WSig` ($E1);
- `SS.GfxAlloc` ($D4), `SS.GfxFree` ($D5) for one 8 KiB frame-cache block;
- the fixed PSG sound register at $FF92 described in the porting guide.

Copy the seven modules in `build/game/CMDS` into `/s0/CMDS`, with executable
attributes. Copy the `.DAT` files and `PIC` directory from `build/game` into
`/s0/ddp`. Do **not** install the old CoCo SOUND/DDSND drivers. Then:

```text
chd /s0/ddp
DONALD
```

The activity paths are patched to `/s0/CMDS`. Use stdin and stdout on the same
visible Wildbits terminal with bitmap zero available. Run one instance of the
game at a time: the retained Sierra code writes some module data in place.

## Rebuild and test

Requires LWTools (`lwasm`) and Python 3; image tools additionally require
Toolshed `os9`. No Python packages are needed.

```sh
make LWASM=lwasm
make check LWASM=lwasm XROAR=/path/to/xroar
python3 tools/make_image.py /path/to/base-jr2.dsk new-ddp.dsk
```

The local build was made with `lwasm.orig`, avoiding the host’s `lwasm` wrapper.
The adapter uses the ABI constants in `src/defsfile`; no NitrOS-9 checkout is
needed to assemble it. Original bytes, patch assertions, original SHA-256,
module parity, CRC, and the one-block code budget are checked during the build.

The full-machine test accepts your emulator and firmware paths:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tests/check_mame.py \
  --mame /path/to/mame --disk /path/to/base-jr2.dsk \
  --firmware /path/to/directory-with-booter-and-f0.dsk --output /tmp/ddp-test
```

Add `--activity produce` (or `airport`, `railroad`, `playground`, `stores`,
`toystore`) for a diagnostic build that enters that activity directly. These
builds only change the route from the town into the original activity entry;
they are not the shipping module. Add `--record-audio` to capture emulator
sound. To test the supplied release disk, use `--installed` with that disk.

The adapter caches the exact last displayed packed rows and only converts
and copies changed rows. Input polling still presents sprite changes, while
idle polling avoids full-screen conversion. Emulator speed stays at 1×.

## Validation and limits

See `docs/STATUS.md` for results and `docs/PORT.md` for the adapter design.
The port has emulator and CPU validation; it has not been run on physical
Wildbits hardware or through a complete earning/shopping/playground playthrough.

Graphics use a four-color conversion of the original packed CoCo screens,
with blue/orange NTSC-style colors. This is not a full analog artifact-color
simulation. PSG pitches are derived from the original software-DAC delays,
and durations are quantized to the OS’s 60 Hz clock; audio is an approximation.
The original job timers still use wall-clock time, including time spent away
from the terminal. Forced process termination and persistent driver failures
have not been validated. Ordinary Q exit is tested.

The preserved original modules and assets come from the two OS-9 game disks.
Their fingerprints are recorded in `docs/ORIGINAL-SHA256.json`. Original notices
and third-party rights remain applicable. The repository does not include a
bootable OS image; supply your own Wildbits base disk and emulator firmware.

## Interactive emulator launcher

```sh
python3 tools/run_mame.py --mame /path/to/mame \
  --disk DDP-Wildbits-Jr2.dsk \
  --firmware /path/to/directory-with-booter-and-f0.dsk \
  --output /tmp/ddp-play
```

The launcher uses a new private disk copy and opens a dedicated interactive VT
shell before starting DONALD. Running DONALD directly inside an OS-9 startup
script can give it startup-file input instead of keyboard input. MAME UI
controls start disabled and the keyboard uses emulated mode. Default speed is
1× (normal emulator timing). An explicit higher `--speed` also speeds up
music and the game's wall-clock timers. Close an existing emulator before
starting another session. The title appears after the automated boot sequence.
