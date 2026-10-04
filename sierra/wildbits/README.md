# Wild Bits Sierra port: first presentation milestone

`wbpic` is a native, position-independent 6809/NitrOS-9 Level 2 program that
presents the Sierra engine's combined picture-buffer format. It is the first
executable port artifact, not yet a playable interpreter. The existing
`objs/wildbits_engine.asm` remains an unfinished scaffold and is not built.

## Target and interfaces

The target is **independent games on separate terminals**. Each viewer owns
its bitmap and private process data, uses standard output for graphics and
standard input for keyboard/visibility notifications, and requires both paths
to identify the same terminal. An already-defined bitmap zero is an error;
the viewer does not adopt, overwrite, or free that bitmap.

A current Wild Bits terminal/graphics driver must provide:

- `SS.AScrn`, `SS.FScrn`, `SS.Palet`, `SS.PScrn`/layer selection,
  `SS.DScrn`/master-control selection, and `SS.DevNm`.
- `SS.BmBlk` (`$E4`): GetStat with Y=bitmap zero returns its first block in X.
- `SS.ClutWrite` (`$CF`): SetStat with X=BGRA entries, Y=CLUT/first entry,
  U=count. The viewer supplies seventeen entries in CLUT zero.
- `SS.WSig` (`$E1`): SetStat on standard input with X=`$8182` registers
  background/foreground signals; X=0 deregisters them.
- Per-terminal bitmap, layer, and CLUT preservation on terminal switching.

These conventions follow the [Wild Bits porting guide](https://github.com/jfed6000/f256_porting)
and the published [Joust graphics](https://github.com/jfed6000/JoustF256/blob/main/src/gfx.a)
and [platform backend](https://github.com/jfed6000/JoustF256/blob/main/src/platform.a).
The viewer requires visibility registration to succeed; it does not silently
continue with a driver lacking multi-terminal notification support. Start it
from the visible terminal. Actual initial-visibility notification and graphics
restoration must be verified on the installed driver/core.

## Build and run

From this directory, with lwasm on PATH:

```sh
make NITROS9DIR=/path/to/nitros9
make fixture
```

Copy the resulting OS-9 module `wbpic` to the target's executable directory
and `test-picture.bin` to a data directory using the usual OS-9 file-transfer
and executable-attribute procedure. On the target:

```text
wbpic test-picture.bin
```

Any input byte exits. CTRL-C/BREAK signals are intercepted as cancellation;
non-interceptable kill remains subject to normal OS-9 process cleanup.

The input is exactly **26,880 raw bytes**, row-major, 160 by 168:

- Low nibble: logical color index 0..15.
- High nibble: priority/control data; presentation leaves it unchanged.
- No module header, picture-resource compression, or file-format header.

The generated fixture is diagnostic color bars with varying priority, not an
AGI game resource or a picture decoded from a game. An engine-buffer export
must be in the normal low-color/high-priority orientation. The viewer does
not load `picDir`/`vol.*` or implement AGI picture commands yet.

## Presentation and memory

Each logical pixel is duplicated horizontally into a 320-by-240, one-byte
bitmap. The first 168 rows contain the picture; the remaining rows are opaque
black. Logical colors become indices 1..16, reserving transparent index zero.
The palette uses the conventional sixteen-color RGB values in BGRA order.

The module requests one 8 KB private data area, including row staging and
stack. It retains only **one 8 KB service mapping** at a time. Bitmap storage
is allocated by the graphics driver; no direct MMU or VICKY register access
occurs. Mapping always uses the address returned by `F$MapBlk`, and `F$ClrBlk`
receives that original base. Spans split at an 8 KB boundary even when a
320-byte row crosses it. The module-size budget target uses the conservative
40,192-byte budget intended for the eventual two-window interpreter.

The signal handler writes only private flags through intercepted U and does
not assume the interrupted DP. Hidden instances wait using `F$Sleep` before
continuing block/row work or presentation. Visibility registration is released
during cleanup. Background cleanup still uses the terminal driver: its
per-terminal shadowing contract is essential to avoid altering the visible
terminal. The CPU tests cannot establish that driver behavior.

The viewer balances the opened input file, bitmap ownership, and mapping
lifetime on the tested success/error paths. It restores text mode on its own
terminal and frees only its allocated bitmap. It is a viewer lifecycle, not
yet a generalized restoration of arbitrary previous graphics applications.
Persistent driver cleanup failures and forced kill have not been validated on
hardware; these remain runtime validation work.

## Checks and hardware acceptance

```sh
make check
```

This requires XRoar with its GDB interface. The test executes the actual
assembled 6809 module with mocked OS-9/graphics calls. It checks:

- Every output pixel and the untouched black region, with varied priority bits.
- Short input reads and spans crossing mapping boundaries.
- Different code/data locations and OS-returned mapping-window addresses.
- Truncated/oversized input, allocation refusal, mapping failure, and a
  transient unmap failure followed by cleanup.
- Terminal name matching, background waiting, registration release, and
  refusal to free an existing bitmap.

This is CPU/service-contract testing, **not a Wild Bits emulator or hardware
run**. For multi-terminal acceptance, launch the viewer on two separate
terminals, switch between them during loading and while displayed, verify each
palette/picture returns correctly, quit one, and verify the other remains
intact. Repeat both launches and check free RAM and bitmap availability.
Also test mismatch/redirection, missing services, signal cancellation while
hidden, and the actual keyboard behavior on the target.

The next port milestone is connecting the existing picture/resource decoder
to this native buffer/presentation path, then running one silent game before
adding sound and full concurrent-instance acceptance.
