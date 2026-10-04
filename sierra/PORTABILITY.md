# Sierra platform separation

## Purpose and current scope

The interpreter is being separated from its CoCo hardware implementation so
that a Wild Bits backend can be added without putting runtime platform checks
in performance-sensitive paths. This is an incremental refactoring, not a
completed Wild Bits port or a position-independent engine conversion.

The first boundary is sound. Resource loading, sound-list management, AGI
commands, completion flags, and the existing elapsed-time bookkeeping remain
in `objs/mnln.asm`. CoCo DAC playback, PIA setup/restoration, private saved PIA
state, and CPU-calibrated frequency and wave-count tables now reside under
`objs/platform/`.

## Assembly-time selection

`mnln.asm` includes `platform/sound-data.asm` at the original sound-data
location and `platform/sound-code.asm` at the original playback-code location.
These selectors include `coco-sound-data.asm` and `coco-sound-code.asm` for the
current CoCo build. They emit no runtime dispatch instructions.

When `WILDBITS` is nonzero, assembly deliberately fails with a missing-backend
message. The existing Wild Bits wrapper is still a scaffold; selecting it must
not silently include CoCo PIA code. Once a Wild Bits implementation exists,
the selectors will include its corresponding data and code files instead.

The shared makefile lists all four includes as dependencies of `mnln`, so
editing a backend or selector causes the affected module to rebuild.

## Current playback contract

The backend supplies `PlaySound` at the existing call site:

- Input: U points to a loaded sound node. The word at offset 3 of that node
  points to the existing converted sound stream. Its memory is already mapped
  by the caller's `SetLogicPage` operation.
- Stream: each note has a note-index byte, an amplitude byte, and a two-byte
  duration. A `$FF` note-index byte ends playback, followed by a two-byte
  elapsed-time value. This describes this interpreter's existing stream;
  it is not a new portable sound-file format.
- Output: D contains the elapsed-time word. Y, the caller's logic-script
  pointer, is preserved. X and U are clobbered, and condition codes are not
  preserved. The current CoCo implementation advances U through the stream.
- Execution: playback is synchronous. The CoCo backend disables IRQ/FIRQ
  during playback and enables them again during restoration, as before.
  It temporarily changes PIA control registers and restores their saved
  settings before returning.
- Storage: the CoCo implementation uses direct-page scratch words `$008E`
  and `$0090`, plus the three saved PIA bytes embedded in its private engine
  copy. These are existing dependencies, not newly introduced storage.

A replacement backend must satisfy the caller-visible contract or update the
shared caller explicitly. In particular, an asynchronous sound driver cannot
simply replace this routine without reconsidering completion flags and
elapsed-time bookkeeping. Existing code adjusts system/game time after the
blocking, interrupt-masked playback; a backend that leaves the system clock
running must adapt that behavior rather than count the duration twice.

The embedded saved PIA bytes remain writable and process-private through the
existing instance-isolation mechanism. Moving them into an include does not
make the module position-independent or eliminate self-modifying storage.
A future packed, shared-code engine must move writable backend state into
process-private data.

## Why this preserves CoCo performance

The extraction leaves every instruction, data byte, addressing width, and
relative location unchanged. Backend selection happens during assembly, not
inside a note loop. The cycle-balancing DAC test and calibrated delay loops
are retained exactly, including the RS-232-safe output handling.

Fresh assemblies before and after this change were compared for `sierra`,
`mnln`, `scrn`, and `shdw` in all fourteen game directories: all 56 modules
were byte-for-byte identical, including their headers and CRCs. A separate
assembly with `WILDBITS=1` was checked to fail with the intended missing-backend
error. These checks establish unchanged generated CoCo code for this step;
they do not establish Wild Bits operation or new hardware behavior.

## Subsequent boundaries

The next substantial boundary is memory mapping. Its interface must describe
which buffer is accessible and for how long, rather than expose CoCo MMU
register numbers as a supposedly portable API. The existing fixed-address
engine and bank-switching assumptions need a deliberate audit.

Graphics should expose strip/span operations and batched buffer access so
that optimized pixel loops remain within each backend. Input should retain
both typed parser commands and movement controls. Timing must preserve game
cadence rather than depend on CPU speed. Terminal switching and cleanup must
track ownership per process, including a policy for the shared sound device.

The Wild Bits implementation should follow the allocation, mapping, graphics,
and terminal-switching interfaces in the
[Wild Bits porting guide](https://github.com/jfed6000/f256_porting).
Every boundary should first retain the working CoCo behavior, with binary
comparison where an extraction is intended to leave generated code unchanged.
