# Concurrent Sierra instances: implementation notes

## Why isolation is necessary

OS-9 can share a module marked `ReEnt` between processes. That attribute
allows sharing; it does not make writes to the module private. The original
interpreter stored setup variables alongside executable code and patched
engine instructions and dispatch tables in linked modules. Two processes
could overwrite each other's options, relocation state, buffers, and cleanup
information.

The implementation keeps Sierra's setup code shared, moves its mutable state
into process data, and gives each process private physical copies of `mnln`,
`scrn`, and `shdw`. Screen ownership is enforced by the companion NitrOS-9
graphics changes. Both repositories must be built and installed together.

## Private setup state

In `objs/sierra.asm`, the variables formerly declared with `fcb`, `fdb`, or
`fzb` in the executable module are now `rmb` declarations in its data area.
For example, the old store:

```asm
sta       >MultitaskFlag,pcr
```

addressed a byte relative to the shared module. The new store:

```asm
sta       >MultitaskFlag
```

addresses this process's data block under Sierra's existing memory layout.
Two games use the same logical address but map it to different physical RAM.

| Fields | Responsibility |
| --- | --- |
| `MultitaskFlag`, `RgbRequested` | Per-process command-line choices |
| `OwnProcessId` | Identity used to locate the process descriptor |
| `SierraMmuBlk2`, `SierraMmuBlk3` | Original mappings restored at exit |
| `EchoSave`, `EofSave`, `IntSave`, `QuitSave` | Saved terminal options |
| `ViPathNum`, `ViDevAddr` | This process's timer/RAM device references |
| `PrivateNext`, `PrivateLimit` | Private engine allocation bounds |
| `ProcMapReady`, `OptionsChanged` | Which cleanup operations are necessary |
| `mmubuf` | Private system and process mapping snapshots |

## Heap layout and temporary storage

The permanent setup state occupies 36 bytes. The engine heap therefore moves
from `$0776` to `$079A`. `objs/instance.d` defines `SierraHeapBase` for both
Sierra and MnLn. Sierra calculates `InstanceHeapBase` from its declarations
and emits an assembly error if the calculated address differs from the shared
constant. This prevents a layout change from silently overlapping engine data.

MnLn's memory-information calculations now subtract `SierraHeapBase` rather
than the old hardcoded address. These are the only engine logic changes in
`objs/mnln.asm`; isolation of its writable code comes from the private copies.

`gprbuf` is a 512-byte startup scratch buffer at the beginning of the future
heap. Its `equ` declaration names an address without reserving permanent
storage. No descriptor snapshots occur after engine entry. Following the final
snapshot, `MainInit` clears all 512 bytes so the engine receives the same
initial zero-filled heap it expects. The scratch buffer therefore does not
permanently consume another 512 bytes of common data space.

## Startup and failure handling

Startup now performs these operations in order:

1. Clear and initialize private data, preserving the command-line pointer.
2. Parse `-m` and `-r` into private state.
3. Check terminal identity and graphics-service compatibility.
4. Prepare this process's MMU aliases and copy its runtime helper routines.
5. Allocate `/VI` RAM and register the timer.
6. Copy the engine templates into private pages.
7. Allocate and configure the terminal's application screen.
8. Clear descriptor scratch storage and enter MnLn.

Initialization precedes option parsing because those options now reside in
the data area being cleared. On setup failure, `InitEntry` saves the original
error in `B`, runs `ShutdownFull`, restores `B`, and exits. Cleanup calls may
change registers, so saving the error preserves the actual cause of failure.
The ownership fields and flags let this path handle partial initialization.

## Kernel and process MMU maps

The CoCo 3 MMU divides the 64K logical address space into eight 8K slots.
Each slot selects a physical RAM block. Sierra switches mappings to access
its data, its process descriptor, engine code, and graphics memory.

The old `mmuini1` treated PID 1's descriptor as the kernel map. PID 1 belongs
to SysGo. The new routine obtains the kernel DAT through `D.SysDAT`: it masks
interrupts, briefly maps system block zero into the `$2000` window, reads the
mapping entries, and restores the window. It first captures its own map so
the borrowed slot can be restored correctly.

`mmuini2` uses `F$ID` and `F$GPrDsc` to capture the current process's map into
private buffers. `SetupProcMap` also records the current PID and uses
`D.PrcDBT` to locate its descriptor. It saves the original mappings before
making `$2000` and `$4000` aliases of its data block. `ProcMapReady` records
that these aliases were installed. `RestoreMmu` checks and clears that flag
before restoring them, preventing duplicate restoration.

## Private engine pages

Moving Sierra's variables alone would leave the writable engine modules
shared. `NMLoadModule` instead treats a linked module as a source template:

```text
                     Shared engine template
                       /               \
                  copy pages        copy pages
                     /                   \
            Game A's physical RAM   Game B's physical RAM
```

For each module, the loader:

1. Calls `F$Link`, or `F$Load` if linking fails.
2. Determines the occupied 8K source pages from the header and module size.
3. Checks the source range and remaining private capacity.
4. Copies each complete page into this process's allocation.
5. Stores the private block numbers in its runtime remap table.
6. Calls `F$UnLink` to release its acquired template reference.

The existing `MmuSwitch` machinery maps these private blocks when dispatching
between modules. Copying whole pages preserves the legacy engine's internal
layout and isolates patched instructions, relocated command tables, resource
caches, and save buffers without rewriting every engine store.

`CopyPrivatePage` maps the destination temporarily at `$4000` and copies
4,096 words, or 8,192 bytes. IRQ and FIRQ are masked during the copy. It makes
no OS-9 calls while the temporary hardware mapping is installed and restores
the original mapping before returning. The process DAT image remains unchanged
during this temporary copy window.

## RAM allocation and timers

The `/VI` allocation grows from 13 to 21 contiguous 8K blocks:

| Purpose | Blocks | RAM |
| --- | ---: | ---: |
| Original game allocation | 13 | 104K |
| Reserved private engine pool | 8 | 64K |
| Total `/VI` allocation | 21 | 168K |

Process data and graphics screens are additional allocations. `PrivateNext`
starts after the original thirteen blocks; `PrivateLimit` is the exclusive
end of the allocation. The loader checks capacity before each page copy.
Range checks reject allocations that the interpreter's byte-sized physical
block fields cannot represent. This restricts that allocation to the first
2MB and rejects byte wraparound.

`SetupVirq` explicitly reloads `A` from `ViPathNum` before timer registration,
because allocation arithmetic has changed `A`. Its error path preserves the
registration failure in `B`. Cleanup clears this path's timer, releases its
RAM, closes the path, detaches the device reference, and clears saved ownership
fields. Available contiguous RAM and the `/VI` driver's timer slots bound the
number of simultaneous instances.

## Screen ownership and capability query

The companion changes in NitrOS-9's `co3hires.asm` record an owner PID in the
previously unused device-static byte at `$2A`. `cocovtio.d` names it
`HRS.Owner`/`V.HRSOwner`; subsequent fields retain their offsets.

An unowned device permits allocation. Successful allocation and mapping claim
ownership. The owning process can manipulate its application screens; another
process receives `E$DevBsy`. Releasing the last application screen clears the
owner. If physical allocation succeeds but mapping fails, the allocation is
released before returning the mapping error.

Each game therefore requires a distinct VTIO device, such as `/v1` and `/v2`.
Two paths to `/v1` still address the same device and screen state.

`CheckInstanceServices` compares stdin and stdout device names and requires
them to identify the same terminal. It then issues `I$GetStt` with `SS.AScrn`.
The updated CoVDG and CoWin handlers forward a non-allocating request using
`X=$FFFF` to the screen service. The updated service returns interface version
2. Sierra requires version 2 or later before changing mappings or terminal
settings. An older service therefore cannot silently run the new interpreter
without ownership protection. Sierra and Co3HiRes module editions are also
raised to 2; the runtime compatibility check uses the capability response.

## Palette and monitor handling

Previously Sierra changed the global monitor setting and restored a saved
value at exit. One process's restoration could override another process's
configuration. Now `-r` records a private request. `ConfigureMonitor` reads
the monitor setting and chooses this game's palette without changing the
global setting.

CoVDG and GrfDrv now apply application-screen palettes as raw GIME color
values. Sierra has already selected the RGB or composite color table, so a
second monitor-dependent conversion would be incorrect. Ordinary screen
palette handling retains its monitor-dependent conversion. CoWin's changed
short branch to a long branch accommodates the added capability-query code.

## Independent shutdown

The old `UnloadMod` loop repeatedly called `F$UnLoad` until it failed. That
could consume references acquired by another process. The loop is removed.
The new loader balances each template reference after copying, so shutdown
only releases resources belonging to this instance:

1. Restore terminal options if they were changed.
2. Return to the text screen and free the application screen.
3. Clear the timer and release `/VI` RAM and references.
4. Restore the original MMU aliases.

Successful cleanup clears the corresponding state fields. Palette-write
failure no longer prevents later screen-release attempts. Normal AGI Quit
executes this cleanup; forced-termination cleanup is not established by these
tests.

## Build and documentation changes

`sierra-game.mak` adds the shared source directory to the include path and
makes Sierra and MnLn depend on `instance.d`. A heap-layout change therefore
rebuilds both. `objs/ReadMe` corrects the obsolete claim that these sources
were unused. All fourteen standard Sierra builds use them. `wildbits_engine.asm`
was not modified by this implementation.

See [README.md](README.md) for running requirements and verification commands.
Use `-m` when a game should continue while its terminal is inactive. Each
process needs the appropriate game data directory. Use distinct save
directories or slots for independent saved games; sharing a filename still
shares the saved file. Physical floppy disk changes affect every process
using that drive.

## Validation and its limits

All fourteen game builds and both 6809 and 6309 graphics-driver builds passed.
The targeted headless XRoar CPU/MMU tests intercept OS-9 calls and cover:

- Private page copies, independent writes, and unchanged templates.
- Reference balancing and private-pool exhaustion.
- Timer registration and error preservation.
- Kernel/process map snapshots, descriptor lookup, and MMU restoration.
- Screen ownership, non-allocating queries, and allocation rollback.

The live OS-9 fixture launches two King's Quest I processes on separate
terminals. It supplies Ctrl-Break at the initial joystick prompts and verifies
that both processes reach their interpreter loops with separate data and
engine pages. It then invokes normal AGI Quit in one process, checks that its
resource fields are cleared, and verifies that the other process continues.
The fixture uses a disposable disk with emulator disk writes disabled.

This establishes concurrent initialization and independent normal exit. It
does not establish complete-playthrough coverage, save/restore UI coverage,
or cleanup after forced termination. Runtime validation was on the 6809
fixture; the 6309 drivers were build-checked.
