# Bayou Bootleggers — CoCo 3 prototype

An original Louisiana-themed belt-scrolling brawler prototype for a **6809
CoCo 3 running NitrOS-9 Level 2**. Nonc Claude's crew stole your shrimp boat.
Fight through Cypress Landing, the Shrimp Shack, and the Captain's Wharf to
take it back. Three dock arenas, three lives, paddle swings, jumping strikes,
enemy wind-ups, lane-based combat, alligator lunges, and a final boss are implemented.

The graphics use original indexed pixel art: six transparent character
poses plus two alligator poses, shaded clothing and shrimp boots, mirrored facing, paddle swings,
jump and hit poses, deckhand/captain palette variants, and detailed bayou
scenes with cypress moss, moonlit water, fishing traps, dock grain, lit
buildings, and Nonc Claude's shrimp trawler. It uses transitions between arenas rather than smooth camera
scrolling. Music, weapons, combos, joystick controls, and a larger campaign
are not implemented. No Texas Shit Kickers code or assets are included.

## Atari 2600 version

The separate [Atari 2600 repository](https://github.com/DrPitre/linzay-downs-2600)
contains the native 4 KB NTSC adaptation, ROM, source, and controls.

## Linzay Downs — Tee-Boy Races

A second mode on the same CoCo 3 disk is a race at **Linzay Downs in
Eunice, Louisiana**.
Type `teeboy` at the NitrOS-9 prompt, or use `tools/launch_race.lua`
as the MAME autoboot script. Tee-Boy is your chestnut horse with
the turquoise saddlecloth and jockey; three rivals race alongside him.
Old Cajun men in straw hats cheer from the rough timber rail. **Cecil
Brown** and **Leroy Pitre** have name plaques and speak first. The crowd
then picks from twelve cheers every two to four seconds, with no immediate
repeats. A clock-seeded generator varies each race; a cached two-line banner
identifies the speaker. The original dialogue now mixes Cajun English ("Mais, look at him go!",
"That's my horse, me!") with Louisiana French ("Lache pas la patate!",
"Il est apres courir!", "Au ras au ras!"). The standard CoCo font omits
French accents. Vocabulary and constructions were checked against
[LSU's Cajun French glossary](https://www.lsu.edu/hss/french/undergraduate_program/cajun_french/cajun_french_english_glossary.php)
and [PBS's Cajun English profile](https://www.pbs.org/speak/seatosea/americanvarieties/cajun/).
The dialogue was written for this game. Cypress trees, churned dirt, a starting post,
and a checkered finish surround the four-lane straight.

Press **Space** at the title. After the countdown, **hold Right** to gallop
and **hold Space with Right** for a sprint burst. Release Space to recover
stamina; easing off Right recovers it faster. The HUD shows your place,
stamina, and metres remaining on the 120-metre course (rounded up to the
next five metres). After finishing, **R** races again and **Q** returns to
the shell. Each race mode has its own command so both programs fit the
CoCo 3's mapped-video address space. The dock brawler remains `bayou`,
with **Nonc Claude** as its villain.

The racing mode has four gallop poses, distinct rival colours, and double
buffering. The current native benchmark improved from about 5 FPS to
11 FPS on a 512K 6809 CoCo 3 in MAME. Compact 32x30 horse art uses 32x32
background patches; a race-only assembly blitter draws palettes translated
once at startup. The full hidden screen stays mapped, and the HUD uses
packed digits instead of per-pixel drawing. Gallop animation advances on
displayed frames, while race logic remains clock-paced. `make build/race-bench`
builds the repeatable 120-frame timing command (see `benchmarks/race.json`). Logic tests cover seeded crowd selections, named introductions, cheer timing,
the countdown, sprint drain/recovery, finish
order, victory, and defeat. Horse rendering tests validate the packed run
masks and compare both alternating screens with clean redraws across the
course. `tools/check_race.lua` drives the native MAME smoke test; allow
`-seconds_to_run 170` and set `BAYOU_SNAPDIR` to capture title, race and
finish screens.

## Play

The supplied `dist/bayou.dsk` is a bootable 40-track double-sided OS-9 floppy
image. Mount it in drive 0 of a **512K CoCo 3**, boot with `DOS`, wait for the
shell prompt, then type `bayou`. The program creates its own 320×200,
16-color graphics window. RGB monitor mode is selected for its palette;
select an RGB monitor in your emulator too.

In MAME, use **emulated keyboard mode** during play. Natural keyboard mode
translates typing into individual presses and prevents reliable held arrows
and simultaneous buttons. `tools/launch.lua` types the boot commands, then
switches to emulated keyboard mode at the title screen. Run it with
`-autoboot_delay 2 -autoboot_script tools/launch.lua`; omit other autoboot
commands when using this script.

| Control | Action |
| --- | --- |
| Space on title | Start |
| Arrow keys | Move left/right and along the dock |
| Space | Jump |
| Hold Control | Repeat paddle swings in facing direction |
| X | Swing paddle (typing alternative) |
| Jump + paddle | Double damage |
| Q | Quit back to the shell |
| R after winning/losing | Restart |

Stay in an enemy's lane to land hits. Face the enemy before swinging.
Hold Control for repeated swings; the cooldown prevents instant hits.
You can move during a swing, with reduced horizontal speed. Paddle hits
interrupt enemy wind-ups and knock enemies back. Yellow enemy health bars
mark raised attacks or hit reactions. Crew members approach on separate
lanes so their silhouettes are easier to read.
Enemies wind up before attacking: step aside or jump to dodge. Clear each
dock, then walk to the right edge. The final boss has twelve health points.

An alligator lurks along the lower edge of every arena, replacing one
crew member within the four-actor rendering budget. Open jaws and a yellow
warning mark signal its attack. It then lunges forward and up onto the
dock, pauses, and retreats. Jump over the bite, sidestep its lane, or face
it and strike with the paddle to interrupt. Alligators award 150 points;
the final arena contains both Nonc Claude and an alligator.

On an existing NitrOS-9 installation with CoWin, `/w`, and `grfdrv`, copy
`dist/bayou` into the execution directory, set its execute permissions,
and install the brawler `.bin` artwork files from `assets/`
into `/dd/BAYOU`:

```
copy bayou /dd/CMDS/bayou
attr /dd/CMDS/bayou e pe
makdir /dd/BAYOU
* Copy assets/dock0.bin, dock1.bin, dock2.bin, title.bin,
* dock0.rle, dock1.rle, and dock2.rle into /dd/BAYOU.
bayou
```

Standard fonts must be loaded (normally done by the system startup).

## Build

Requires CMOC, LWTOOLS, ToolShed's `os9`, a native C compiler for logic tests,
and the `cmoc_os9` source tree. The default library source path is
`$HOME/Projects/cmoc_os9`; override `CMOC_OS9` as needed. The build copies
library sources into its own ignored `build/deps` directory before building
them, so the library source checkout is not modified.

```
make CMOC_OS9=/path/to/cmoc_os9 NITROS9DIR=/path/to/nitros9
make art
make test
make disk NITROS9DIR=/path/to/nitros9
make package
```

The disk recipe uses the neighboring NitrOS-9 source tree by default and
keeps its output and intermediates under `build/disk`. The boot disk
includes NitrOS-9 components, whose existing licenses remain applicable.

`tools/make_art.py` authors all artwork using Python's standard library.
It writes packed four-bit graphics, losslessly compressed background rows,
preview PNGs, and `src/sprites.h`; no external artwork or image libraries
are required. `src/game.c` is portable gameplay logic, `src/render.c`
composites sprites with transparency, mirroring and depth ordering, and
`src/bayou.c` handles the native graphics window, input, and frame pacing.
Sprite streams group opaque and masked runs in both facing directions,
omitting transparent padding. `src/sprite.c` selects its drawing loop once
per run. `src/copy.c` uses fixed-offset word copies for clean actor patches.
Portable rendering and copy routines support host tests.

The native path alternates two graphics screens. Each frame restores the
hidden screen's old clean actor patches, captures new clean patches when
an actor moves, then draws actors in depth order. Stationary actors reuse
their clean patches; identical completed pages need no redraw. Only a
completed screen is selected. Overlapping actors cannot cache or restore
each other's pixels. Both sets of background patches fit within 16K of
writable process memory, including the explicit 1K stack reservation,
leaving three address slots for video. Mappings are released on exit.

Each arena is read from disk once and copied directly into the other
screen's physical RAM. Loading both screens took 4 seconds in the native
emulator benchmark. Compressed backgrounds remain available for host
renderer tests; the native game uses the raw scene assets.

Game logic runs at 15 updates per second using NitrOS-9's 60Hz clock;
rendering can skip intermediate poses instead of slowing movement and
jumping. There is no extra fixed delay after an expensive redraw. The
clock is read through `F$CpyMem` using the CoCo 3 Level 2 direct-page layout.
Double buffering keeps sprite erasure and redrawing off the visible screen.

The alligator build's 512K 6809 CoCo 3 benchmark completed 120 full
redraws in 15 seconds (about 8 FPS), including game updates and drawing,
without deliberate frame delays. The scene contains two crew members and
one alligator. The earlier three-crew double-buffered build took 16 seconds;
the workloads differ. Both are below a 15 FPS rendering target.

Build `make build/profile` to produce the compact `bprof` benchmark command;
it writes `/dd/BAYOU/profile.txt` on the test disk. The benchmark build omits
the normal interactive main loop to preserve the address space needed for
mapped graphics.

## Validation

Host tests cover movement limits, repeat-attack cooldowns, swing footwork, interrupted enemy attacks, crew
spacing, facing/lane checks, jump
damage and dodges, alligator warning/lunge/retreat, bite dodges, paddle
interruptions, wildlife scoring, damage grace periods, lives, room transitions, boss
spawning, victory, and defeat. Renderer tests cover transparency, mirrored
poses, clipping, patch boundaries, palette variants, overlapping actors,
the health display, generated native run masks, and byte-exact reconstruction of all three compressed
scenes. Alternating saved-background screens are compared against clean redraws through
movement, overlapping actors, jumping, blinking, and actor removal.
Native emulator checks on a 512K 6809 CoCo 3
cover booting the disk, opening the title and arena, paddle rendering, and
returning to the shell. Physical hardware testing remains outstanding.

`tools/check_art.lua` drives that native MAME check. Set `BAYOU_SNAPDIR` to
an existing output directory and pass the script using `-autoboot_script`,
with `-autoboot_delay 2 -seconds_to_run 110`. It sets MAME's persistent RGB
monitor configuration and captures title, arena, paddle, and exit screens.

`tools/check_gator.lua` approaches the lower dock edge and captures the
alligator through its warning and lunge, using the same snapshot-directory
setting and MAME options as the regular smoke check.
