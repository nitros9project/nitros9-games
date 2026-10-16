# Sierra instances

See the [Wild Bits / CoCo 3 parity checklist](WILDBITS-PARITY.md) for verified
evidence, remaining work, and the acceptance criteria for completion.

See [the implementation explanation](INSTANCE-DESIGN.md) for the memory
layout, loader, graphics ownership, startup, cleanup, and validation details.

The shared interpreter supports concurrent processes when built with the
ownership-aware NitrOS-9 `co3hires`, CoVDG/CoWin, and GrfDrv changes in the
neighboring source tree. Rebuild the games and bootfile together. An older
screen service fails the startup capability query before Sierra changes its
MMU map or terminal settings.

Give each game a distinct VTIO device, such as `/v1` and `/v2`, with stdin and
stdout attached to the same device. Include those descriptors in your bootfile
or load them before starting the games. Use `-m` to keep a game running while
its terminal is inactive. A second game on an occupied terminal returns
`E$DevBsy`; two separate paths to the same device do not provide two screens.
Each process also needs its own game data directory. Use distinct save
directories or slots when you want independent saved games. Shared floppy
disk changes still affect every process using that drive.

Sierra's options, timer path, MMU snapshots, and cleanup state now live in
process data. The loader copies each complete occupied page of `mnln`, `scrn`,
and `shdw` into private RAM before running it. This also isolates the engine's
relocated tables, patched instructions, resource caches, and save buffers.
Template links are balanced individually; shutdown no longer unloads other
processes' module references. The system map comes from the kernel's DAT,
and descriptor lookup uses the current process ID rather than assuming PID 1
is the kernel.

The private engine pool reserves eight extra 8K blocks (64K) per process,
in addition to the original thirteen game blocks, process data, and screen
allocation. Available contiguous RAM and the `/VI` driver's timer slots bound
the number of instances. The interpreter's byte-sized MMU fields require its
RAM allocation to stay within the first 2MB. Exit through the game's Quit
command to run its screen and timer cleanup.

## Verification

From the parent shelf directory, with its `bin` and Toolshed `os9` on `PATH`:

```sh
make -C nitros9-games/sierra NITROS9DIR="$PWD/nitros9" all
python3 nitros9-games/sierra/tests/check_instances.py
python3 nitros9-games/sierra/tests/check_instances.py --boot
python3 nitros9-games/sierra/tests/make_boot_fixture.py /tmp/sierra-two
python3 nitros9-games/sierra/tests/check_instances.py --boot \
  --disk /tmp/sierra-two/two-instances.dsk --instances 2
```

The CPU/MMU tests use headless XRoar and intercept OS-9 calls. They cover
private page copies, independent writes, reference balancing, allocation
exhaustion, timer registration errors, kernel/process map restoration,
terminal ownership, and screen allocation rollback. Use matching 6809 driver
binaries and symbol maps; a 6309 build in the same recipe directory replaces
those maps, so rebuild the 6809 drivers afterward.

The boot checks use real OS-9 calls and King’s Quest I data. They dismiss the
initial joystick prompt with Ctrl-Break, verify both interpreter loops, then
invoke the normal AGI Quit routine in one process and verify that the other
continues. The fixture is a separate disposable disk; emulator writes are
disabled. These checks do not exercise a complete playthrough or save/restore
through the game UI.

Wild Bits native presentation work and target-side testing are documented in
[WILDBITS-README.md](WILDBITS-README.md). The interactive King’s Quest I port supports
typed commands, movement, inventory, menus, save/restore, owned queued sound and
positioned messages on the tested Wild Bits drivers. Install the matching
`wbgame`, `wbui`, `wbstate` and `wbfont` build together. The matching ABI-8
UI helper supplies text/audio code; the state helper supplies save/restore code.
Build it with `make -C sierra/objs -f wildbits.mk all` from the games repository.
Full AGI compatibility and common-engine consolidation remain unfinished.
