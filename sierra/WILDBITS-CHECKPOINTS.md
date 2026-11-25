# Wild Bits original-game checkpoint matrix

This file records original-resource runtime checkpoints, not static asset
coverage or native-only unit tests. A title remains incomplete until its
checkpoint invokes the unmodified game logic/resources (or clearly labels a
controlled bootstrap), asserts observable state or output, and checks normal
cleanup. Passing one checkpoint does not imply a complete playthrough.

## Current executable checkpoints

| Title | Automated original-resource checkpoint | What it asserts | Remaining V02 coverage |
| --- | --- | --- | --- |
| King's Quest I | `tests/check_wbgame_mame.py --journey` | Castle-to-lake and return room transitions, exact room descriptions, continued input, planned exit and unchanged free memory. Other options cover original help, hall, king dialog, menus, save/restore/restart, puzzles, encounters, quest chain and ending. | Expand beyond the current route to help, death/capture and representative branches in one documented suite; full adventure progression is V03. |
| King's Quest III | `tests/check_kq3_mame.py` | Original startup/clock, movement, room text, save, changed position, restore, exact static-scene recovery and memory after exit. Optional pair mode covers a second KQ1 terminal. | Add help, menu, inventory, death, representative puzzle and ending checkpoints. |
| King's Quest IV | `tests/check_kq4_mame.py` and `--persistence` | Original credits advance to play; Right moves Rosella from the beach into the river meadow while the scene scrolls, and a second Right press stops her. The `look room` message appears in a centered window with scenery visible around it; Rosella stays at the same position through popup dismissal and Inventory open/close. Escape opens the menu; Inventory opens and dismisses. The optional persistence route saves via the File menu, changes scene, restores, then saves again; room and ego X/Y match the original save, and original `look` logic runs after restore. | Compare additional gameplay fields and failure cases; add item-bearing inventory, death, representative puzzle and ending checkpoints. |
| Leisure Suit Larry | `tests/check_wbgame_mame.py --larry` and `--larry-enter` | Original age quiz, street movement/look, door entry, Lefty's interior, input restoration and memory after exit. | Add menu, inventory, save/restore, death and representative puzzle/ending checkpoints. |

## Remaining bundled titles

The all-title resource audit (`tests/audit_game_scripts.py --all-games`) and
picture/resource regressions do not substitute for original-game runtime
scenarios. Each title below now has an original-resource startup-only MAME
checkpoint through `tests/check_wbgame_mame.py --startup-only --game <title>`.
These establish startup/display and exit cleanup; they do not test subsequent
gameplay actions, so behavior checkpoints are still needed.

| Title | Runtime checkpoint status |
| --- | --- |
| Black Cauldron | Startup-only pass |
| Christmas Carol 1986 | Startup-only pass |
| Gold Rush! | Startup-only pass |
| King's Quest II | Startup-only pass |
| Manhunter: New York | Startup-only pass |
| Manhunter 2: San Francisco | Startup-only pass |
| Police Quest I | Startup-only pass |
| Space Quest 0 | Startup-only pass |
| Space Quest I | Startup-only pass |
| Space Quest II | Startup-only pass |

## Current-revision reruns (2026-10-18)

The KQ1 east/west journey checkpoint passed against the current ABI-14 modules
in MAME; artifacts are in
`/private/tmp/wildbits-v02-kq1-journey-final-20261018`. The KQ3 startup,
movement and save/restore checkpoint also passed; artifacts are in
`/private/tmp/wildbits-v02-kq3-final-20261018`. Larry's quiz, door entry,
Lefty's transition, inside look/dismissal and cleanup passed; artifacts are in
`/private/tmp/wildbits-v02-larry-final-20261018`. These three runs refresh
evidence for those exact scenarios only.

The KQ1 original-resource quest-save scenario was rerun against the same
modules on 2026-10-18. It earned the three treasures through the original room
logic, saved and restored after shield acquisition, completed the ending at
score 61, and recovered the exact shell free-memory report. Its save header and
declared length also matched. Artifacts are in
`/private/tmp/wildbits-v02-kq1-quest-save-rerun-20261018`. This is a controlled
quest progression with prescribed room transfers, not a continuous fresh-start
playthrough.

On 2026-11-06, the updated `check_wbgame_mame.py --quest-chain quest-save`
runner passed end to end from a clean 4 MiB bootable test disk using the
matching emulator firmware. It reached the save, restore and ending prompts,
validated both snapshots' CRCs and gameplay fields, verified the checkpoint-zero
replay stream was replaced and recorded through the ending prompt, and observed
byte-identical 880 KiB free-memory reports before and after. The MAME log and
screenshots are in
`/private/tmp/sierra-quest-save-endtoend-clean2-20261106`. The terminal capture
shows `ERROR #215` after the run; its source is not yet classified, so this
checkpoint does not treat it as harmless. This run closes the fresh end-to-end
runner gap only; it is still a controlled room-transfer scenario rather than
continuous progression from a new game.

The same `quest-save` route passed again on 2026-11-06 after the KQ1 MAME
checkpoint updates. Save/restore/replay/ending assertions and byte-identical
free-memory reports pass again; the terminal capture still shows a lone `.`
followed by `ERROR #215` between game exit and the scripted `mfree` command.
The test requires and verifies the resulting `free-after` file, so the memory
comparison succeeds despite this shell diagnostic. The source of the stray dot
is still unclassified and the failure has not been declared harmless. Artifacts
are under `/private/tmp/wildbits-quest-save-final-rerun-20261106`.

`tests/check_all_title_startup_mame.py` passed for all fourteen titles on
2026-10-18 using the matching ABI-14 modules. It runs the same isolated
original-resource startup/exit test once per title. Each run compares the shell
and game display, requires a nonblank changed screen, sends Ctrl-C, verifies
return to the shell, and compares free memory before and after. The aggregate
artifacts, including one private disk and MAME log per title, are in
`/private/tmp/wildbits-all-title-startup-20261018`.

## Current-module MAME reruns (2026-10-19)

On 2026-11-06, the KQ4 checkpoint was rebuilt and rerun with the current game
modules. The current `l2_wildbitsjr2.dsk` boot image and `grfdrv256` produced a
flat pink MAME display and no opening dialogue. In a private copy of the test
disk, replacing only `OS9Boot` and `CMDS/grfdrv256` with the versions from the
earlier passing MAME run restored the display. The complete KQ4 test then
passed: one Space reached Genesta's opening dialogue; one Return reached
gameplay; Rosella moved through the scrolling river meadow; `look` remained in
the scene popup; and menu/Inventory dismissal restored the scene and Rosella's
position. Artifacts are under
`/private/tmp/wildbits-kq4-compat-rerun-20261106`. The exact firmware-pair
hashes and the failing pair are recorded in `WILDBITS-MAME.md`. This identifies
a MAME firmware-pair compatibility issue; it does not establish hardware parity.
The current L2 disk also lacked `PSGdrv` and `fPSG`. With those process-owned
modules installed, the same KQ4 scenario passed `--audio-trace --audio-wav`:
four intro sound commands generated 1,179 owned PSG writes and a non-silent
48 kHz stereo WAV (intro AC RMS 54.66, peak-to-peak 231). Artifacts are under
`/private/tmp/wildbits-kq4-audio-compatible-20261106`.

After correcting Wild Bits' `obj.in.box`, `center`, and `right` geometry,
`tests/check_kq4_mame.py` passed again against the same compatible boot/graphics
pair and rebuilt `wbgame` (23,752/23,808 bytes). The single-Space intro,
gameplay movement, `look` popup, menu/Inventory and scene restoration all
passed; the popup and Inventory dismissals restored Rosella to X=243.9. The
fresh run is in `/private/tmp/wildbits-kq4-position-fix-20261106`.

`tests/check_all_title_startup_mame.py` passed against the current `wbgame`,
`wbstate` and `wbui` modules for all fourteen titles. Each original-resource
run showed a changed display, returned to the shell after the controlled
interrupt, and matched the before/after free-memory report. Per-title MAME images
and logs are in `/private/tmp/wildbits-all-title-startup-20261019`.

The all-title startup/display/exit checkpoint passed again against the rebuilt
2026-10-29 production modules. All fourteen original-resource runs displayed a
changed game screen, returned to the shell after the controlled interrupt and
matched free memory before and after. Per-title disks, screenshots and logs are
in `/private/tmp/sierra-all-title-startup-20261029`. This refreshes startup
coverage only; V02 still lacks the requested gameplay checkpoints across the
full title matrix.

The KQ1 `quest-save` route also passed against those modules in MAME. It starts
with empty inventory, earns the required items through original room scripts,
saves and restores after the shield, completes the original ending at score 61,
and checks unchanged exit memory. Its artifacts are in
`/private/tmp/wildbits-v02-kq1-quest-save-20261019`. This remains a controlled
root/room-transfer route; V03's uninterrupted fresh-start route remains open.

The current KQ3 original-resource acceptance also passed on 2026-10-19:
clock glyphs, movement, room description, save/change/restore position and
scene pixels, exit, and exact memory recovery. With the documented expanded
emulator kernel, the KQ3/KQ1 pair run additionally verified independent
terminal displays and input, KQ1 inventory, KQ3 continuing after KQ1 exits,
and memory recovery. Artifacts are in
`/private/tmp/wildbits-v02-kq3-current-20261019` and
`/private/tmp/wildbits-v02-v04-kq3-kq1-current-20261019`.

The current Larry `--larry-enter` scenario also passed, including its original
age quiz, door response, transition into Lefty's, inside look/dismissal and
unchanged exit memory. KQ1's save/walk/restore/look route passed with current
modules. The focused `tests/check_wbcredits.py` passes all five picture offsets;
`tests/check_picture_stream.py` passes ten selected large-picture streams,
boundary cases and malformed-command cleanup.

The Larry `--larry-enter` MAME scenario passed again on 2026-11-05 with the
rebuilt modules. It verifies the age question, successful door response,
transition into Lefty's, the complete original inside-look response in a
popup with colored bar pixels visible on both sides, dismissal, interrupt exit
and unchanged free memory. Artifacts are under
`/private/tmp/wildbits-larry-popup-rerun-20261105`. The test was corrected to
recognize the intended scene overlay instead of requiring a black-and-white
full-screen image.

The KQ4 MAME acceptance passed on 2026-11-06 against the just-built modules
and matching Wild Bits MAME/FEU. One Space advances the intro; Right moves
Rosella while the camera scrolls and a second Right stops her; the original
river-meadow `look` text appears in the centered popup with scene colors visible
outside it; menu/Inventory dismissal restores Rosella and the scene. The test
reported screen-X centroids 487.1 before movement, 179.1 during the scrolled
scene, and 239.9 after `look` and Inventory restoration. Popup captures show 11
and 13 distinct scene colors on the left and right, respectively. Artifacts are
under `/private/tmp/wildbits-kq4-current-20261106`. This current-build emulator
checkpoint covers ordinary dialog overlay behavior; it does not test the full
adventure or the separate full-screen `text.screen` path.

The current modules were rerun on 2026-11-07. `check_kq4_mame.py` passed the
one-Space intro, gameplay movement, ordinary `look` popup, menu/Inventory and
scene restoration at `/private/tmp/wildbits-kq4-audio-current-20261107`.
Separate `--direction-trace` coverage confirmed rightward direction 3 selects
view 0 loop 0 of 5 while flag 20 is set and X advances
(`/private/tmp/wildbits-kq4-current-acceptance-20261107`). `--audio-trace`
observed the expected four intro sound commands and 1,175 process-owned PSG
writes. A separate `--audio-wav` run passed the non-silence assertion; its
48-kHz stereo intro window measured AC RMS 53.55 and peak-to-peak 234 at
`/private/tmp/wildbits-kq4-wav-current-20261107`. The audio capture uses MAME's
software mixer and establishes a non-silent emulator signal, not physical
speaker level. These checks confirm the reported intro, facing-animation and
sound paths on the emulator; they do not close the full KQ4 gameplay checklist.

The KQ1 real-driver `--sustained` scenario passed on 2026-10-19: it displayed an
unknown-word response, opened Pause through the original menu, resumed, accepted
a later command, restored the scene, and exited with unchanged free memory.
Artifacts are in
`/private/tmp/wildbits-s06-sustained-kq1-current-rerun-20261019`.

On 2026-11-11, `check_coco_kq4_inventory_mame.py` passed on the CoCo-only MAME
build with the original KQ4 disks. It confirms CoCo's KQ4 Inventory is full
screen black-and-white text, Space restores all 16 scene colors, and ordinary
look popups leave the scene visible outside their bounds and restore it when
dismissed. Captures are in `/private/tmp/wildbits-coco-kq4-compare-20261111`.
The paired Wild Bits captures are in
`/private/tmp/wildbits-kq4-current-parity-20261108`; this comparison checks
these modal paths only, not the full KQ4 adventure.

The current Wild Bits KQ4 modules also passed `check_kq4_mame.py --persistence`
on 2026-11-11. The scripted path verifies the single-Space intro, movement,
look and Inventory presentation, exact scene restoration, save, changed scene,
restore of room and Rosella coordinates, and continuation into original logic.
Artifacts are at `/private/tmp/wildbits-kq4-parity-20261111-r2`.

## Current-module KQ1 quest-save rerun (2026-11-16)

After the menu overlay and actual-menu navigation changes, the original KQ1
controlled quest-save scenario passed again on Wild Bits MAME. It exercises
the original root and room scripts through the treasure chain, carried inventory
and score, room transfers, real save/restore prompts and the ending. The saved
snapshot contains a bounded two-byte replay stream with checkpoint zero, and
the exit free-memory map matches its starting value. Artifacts are in
`/private/tmp/wildbits-kq1-quest-save-current-20261116`.

This is still controlled room-transfer progression; it does not satisfy V03's
uninterrupted fresh-start-to-ending route.

The 14-title original-resource startup/display/exit matrix was refreshed on
2026-11-16 against the menu-updated production modules. All titles changed the
display, returned to the shell after the controlled interrupt, and recovered
the exact free-memory report. Artifacts are in
`/private/tmp/wildbits-all-title-startup-menu-refresh-20261116`. This refreshes
startup and cleanup evidence only; it adds no gameplay checkpoints for the ten
titles that still have startup-only coverage.

To repeat it, build the matching modules and provide the Wild Bits MAME fork,
base disk and firmware paths as described in [WILDBITS-MAME.md](WILDBITS-MAME.md):

```sh
SDL_VIDEODRIVER=dummy python3 tests/check_all_title_startup_mame.py \
  --mame /path/to/mamed --disk /path/to/wildbits.dsk \
  --firmware /path/to/nitros9/recipes/wildbits/feu \
  --output-root /tmp/wildbits-all-title-startup \
  --module-file objs/wbgame --helper-file objs/wbstate \
  --ui-helper-file objs/wbui --os9 /path/to/os9
```

V02 remains open until the required behavior set (help, movement, dialogue,
menus, inventory, save/restore/restart, death, representative puzzles and
ending) has deterministic scenarios for KQ1, KQ3, KQ4 and Larry, and additional
titles have behavior checkpoints or explicitly approved unverified exceptions.
V03 separately requires uninterrupted fresh-start-to-ending progression; these
bounded checkpoints do not satisfy it.

## Additional KQ1 and KQ4 playability reruns (2026-10-19)

Three independent real-driver checks passed against the current module build:

| Scenario | Result | Evidence |
| --- | --- | --- |
| Hall entry after `stop.motion` / `new.room` | Arrow walking resumes; room/picture and exit-memory checks pass. | `/private/tmp/wildbits-v02-kq1-hall-20261019` |
| King speech | Text remains visible for 2,000 frames; a fresh key restores graphics and exit memory. | `/private/tmp/wildbits-v02-kq1-dialog-20261019` |
| Menu restart | Root stack unwinds, position resets, later look/input works, exit memory matches. | `/private/tmp/wildbits-v02-kq1-restart-20261019` |
| Save/restore | Original save dialog, movement, restored position, later look and unchanged exit memory. | `/private/tmp/wildbits-v02-kq1-persistence-current-20261019` |
| Menu and inventory | Original modal interaction/restoration, interrupt exit and unchanged memory. | `/private/tmp/wildbits-v02-kq1-menu-current-20261019` |
| KQ4 opening sequence | Credit dismissal, Right movement, exact original look text, menu navigation, original empty-inventory screen and fresh-key scene restoration. | `/private/tmp/wildbits-s06-kq4-inventory-final-rerun-20261019` |
| Larry bar | Age quiz, successful door response, room transition, inside look/dismissal and unchanged exit memory. | `/private/tmp/wildbits-v02-larry-enter-current-20261019` |

The current-module `--king-dialog` rerun passed on 2026-10-29. Its
`/private/tmp/wildbits-king-dialog-textmode2-20261029/king-speech.png` capture
shows the full-screen black text page after `text.screen`, with the throne
picture replaced. KQ4 Inventory selects bright white before using the same
full-screen text path; CoCo `cmd_status` does the same. A normalized CoCo/native
screen capture comparison remains open under S04. This is distinct from
ordinary KQ4 `print`, whose centered popup and surrounding game scene are
captured at `/private/tmp/kq4-text-popup-check-20261029/kq4-look.png`.

The 2026-11-07 rerun of `--king-dialog` uses the current modules and captures
`/private/tmp/wildbits-kq1-king-popup-20261107/king-speech.png`. This dialog
stays held for 2,000 frames with nine throne-scene colors visible behind the
transparent text overlay; a fresh key restores the scene and free memory
matches before/after. It confirms this synthetic king-dialog path; a normalized
CoCo/native capture for each text-screen mode remains open under S04.

The KQ3 MAME runner was refreshed on 2026-10-29 after its old text-only check
misread the room graphics around a normal `print` popup. The current original
`look room` response is verified inside the centered 21-by-7 white popup; the
test checks the exact message cells, black/white window fill, colored room
pixels outside the window, and room restoration after Space. It passes with
the current production module bytes (which match the copies on the test disk).
Screenshots and MAME log are in
`/private/tmp/kq3-display-popup-20261029`. This covers that KQ3 `print` action;
it does not compare CoCo 3 and Wild Bits captures or cover KQ3's separate
`text.screen` commands.

The original KQ3 MAME route passed again on 2026-11-05 with the rebuilt
modules. It verified the visible clock, arrow movement, original room
description, save/change/restore position and static scene pixels, planned exit,
and unchanged free memory. Artifacts are under
`/private/tmp/wildbits-kq3-resume-20261105`. This remains a bounded gameplay
checkpoint, not a full KQ3 playthrough or direct CoCo/native capture comparison.

## All-title startup matrix refreshed (2026-10-30)

After the current complete build, `tests/check_all_title_startup_mame.py` was
run against all fourteen original game resource sets and the rebuilt
`wbgame`/`wbstate`/`wbui` modules. Every title reached a visibly changed game
screen, returned to the shell after the controlled interrupt, and reported
the same free memory before and after. The run exited 0; per-title disk images,
screenshots and MAME logs are in
`/private/tmp/wildbits-all-title-startup-current-20261030`. This refreshes
startup and cleanup evidence for the current module bytes. It is not gameplay
coverage: V02 still needs the required help, dialogue, menus, inventory,
persistence/restart, death, puzzle and ending scenarios across the named probe
titles and accepted coverage for the rest.

The full 14-title startup/exit matrix passed again on 2026-11-06 against the
current `wbgame`, `wbstate` and `wbui` modules. All fourteen original games
reached a changed game display, returned to the NitrOS-9 shell after controlled
interrupt, and retained the same free memory. The run exited 0; per-title disk
images, screenshots and MAME logs are under
`/private/tmp/wildbits-all-title-startup-current-20261106`. This refreshes
startup and cleanup coverage only; it does not exercise complete gameplay or
the still-open S01-S08 differential gates.

The same 14-title startup/exit matrix passed again on 2026-11-07 using the
Wild Bits-aware `/Users/boisy/Projects/mame/mame` executable and the current
modules. Every title reached a changed original-game display, returned to the
shell after the controlled interrupt and retained its initial free-memory
report. Per-title captures and logs are under
`/private/tmp/wildbits-all-title-startup-rerun-20261107`. This remains startup
and cleanup coverage, not per-title gameplay completion.

The KQ1 `--persistence` MAME scenario passed on 2026-11-06 with the current
modules. The runner selects File: Restore through the actual game menu, checks
that the filename prompt appears, and verifies Graham returns to the saved
screen position after a walk; a subsequent `look room` popup retains the castle
scene around it. Measured shirt centers were 449.5 before save, 625.5 after the
walk, and 449.5 after restore and popup dismissal. Artifacts are under
`/private/tmp/wildbits-kq1-persistence-corrected-20261106`.

The KQ1 `--restart` MAME scenario also passed on 2026-11-06. The original menu
restart unwinds the nested root logic, restores the initial position, accepts
new arrow input, then settles at a stable position before exit with unchanged
free memory. The test reports `RESTART GameRestartCommand`, `VmRestartRoot`
with stack depth zero, and the fresh-root restart flag. Artifacts are under
`/private/tmp/wildbits-kq1-restart-current-verified-20261106`. This covers the
tested root-menu restart and one subsequent movement sequence; other nested
modal restart entry points remain untested.

The original KQ1 `--journey` checkpoint was rerun on 2026-10-30 at
`/private/tmp/wildbits-kq1-journey-current-rerun3-20261030`. It passes the
eastbound castle-to-lake transition, the return to the castle, both original
room-description messages in centered white popups over visible scenery,
continued input, controlled exit and unchanged free memory. The run corrected
the scripted walking duration and replaced two stale full-screen text pixel
expectations with popup/scene checks. This adds an integrated movement/UI route;
it does not close V02's remaining puzzles, death, ending or other-title gameplay.

The KQ1 journey passed again on 2026-11-06 against the current module build and
matching MAME OS/graphics pair. Eastbound castle-to-lake and westbound return
both show the exact original room descriptions, accept continued movement,
exit cleanly and restore free memory. Artifacts are under
`/private/tmp/wildbits-kq1-journey-current-20261106`.

The first `check_wbgame_mame.py --larry-pair` attempt used the default test
kernel and aborted the first game process with error 228 before the second
terminal scenario could run. Re-running with the same expanded-memory test
kernel required by the KQ3/KQ1 pair acceptance passed the simultaneous original
Larry/KQ1 scenario: both games remain visible across terminal switches, KQ1
Inventory accepts input independently, Larry continues after KQ1 exits, and
Larry-only and final free-memory maps are restored. The passing run used the
workspace test kernel `.wildbits-test/expanded-krnp2`; artifacts are in
`/private/tmp/wildbits-v04-larry-pair-expanded-20261029`. The runner now
requires `--expanded-krnp2` for `--larry-pair`, so the insufficient-kernel
configuration is rejected before building or running a test image. This closes
that two-title/two-terminal probe, not V04's broader repeated-start, interrupted
process and injected allocation/driver-failure coverage.

KQ4 was re-probed with the current modules. The title-specific
`tests/check_kq4_mame.py` advances the original credits/opening sequence,
verifies a 500-frame Right-arrow movement with scene scroll, compares the exact
original `look` text, then sends a fresh Space key and checks the restored scene
and Rosella sprite. The earlier probe used Enter; this title-specific test uses
the correct Space dismissal. The 2026-10-29 rerun measures screen X from 487.1
on the beach to 183.1 in the river meadow; camera scrolling means screen X is
not world X. The same current-module run opens the original game menu with
Escape, navigates to
Inventory with Down and selects it with Enter. It checks the menu's Save,
Restore and Inventory rows, the exact empty-inventory prompt, and fresh-key
dismissal back to gameplay, with Rosella present at the same captured screen
coordinate after restoring the scene. Its artifacts are in
`/private/tmp/wildbits-s06-kq4-inventory-final-rerun-20261019`. KQ4 item-bearing
inventory, death, puzzles and ending remain untested; this is a playable
checkpoint, not full KQ4 gameplay coverage.

The same KQ4 MAME checkpoint passed again on 2026-11-02 with the rebuilt
modules. One Space advances the original intro, scripted Right movement changes
Rosella's screen position and the next Right stops her, `look` appears in the
centered 21-by-7 popup with colored scene pixels on both sides, and menu/
Inventory dismissal restores the same scene position. Artifacts are under
`/private/tmp/wildbits-kq4-resume-20261102`. This does not cover a full KQ4
playthrough or direct CoCo/native screenshot normalization.

## Original logic 159 overlap execution (2026-10-29)

The S02 executor check extracts Manhunter I logic 159's original code bytes
from its log directory and volume, then executes the jump into byte 443 and
both outcomes of the overlapping IF at byte 438 through the CoCo and native
owners. The IF true case sets both compared variables; the test checks variable
results and normalized instruction cursors at two code bases.
`python3 tests/check_logic_executor.py` passes all 51 controlled scripts in
both owners. This closes the overlap-specific runtime check only; resource
cache/replay, nested-resource and failure-restoration comparisons remain open.

## KQ4 popup and checkpoint refresh (2026-10-29)

The current production build (`wbgame` 23,807 bytes, `wbui` 8,145 bytes,
`wbstate` 3,193 bytes) passes `tests/check_kq4_mame.py` against original KQ4
resources. The test checks the bundled opening quote (“I am the fairy,
Genesta”) and confirms title artwork remains visible around that dialogue, the
rightward beach-to-river-meadow transition, and the original
river-meadow `look` text. Its screenshot shows the centered 21×7 light text
window with varied game-scene pixels still visible on both sides. The automated
run passes movement, dialogue, menu navigation, Inventory selection/dismissal
and scene restoration. Screenshots, MAME log and movement measurements are in
`/private/tmp/kq4-current-checklist-rerun4-20261029`; an interactive image is in
`/private/tmp/kq4-current-checklist-rerun4-20261029` as `play.sh`.
This confirms the popup presentation path for the KQ4 `look` message. Save and
restore also have an original-resource room/ego-position comparison below;
other saved fields remain unverified. Death, puzzle and ending checkpoints and
the V02 family gate remain open.

A fresh 2026-10-29 run passed after adding the opening-artwork assertion. It
also passed the existing `look` popup and Inventory checks; movement measured
screen X 487.1 before and 179.1 after moving right into the river meadow. The
captured frames and MAME log are in
`/private/tmp/kq4-opening-text-artwork-20261029`. This is a Wild Bits display
regression check, not a normalized CoCo 3 pixel comparison.

The optional `--help-screen` MAME scenario now selects Sierra Help through the
original menu, recognizes three original instruction lines despite artwork
under the text, sends Space, and verifies gameplay returns with Rosella at the
same screen coordinate and scene graphics present. It passed with the current
production modules; details are in
`/private/tmp/kq4-help-asserted-rerun-20261029/help.json` and the adjacent
screenshots. This closes the KQ4 Help scenario only; item-bearing inventory,
death, puzzles, ending and complete V02 coverage remain open.

The optional `tests/check_kq4_mame.py --persistence` route was exercised through
KQ4's File menu. It created a 34,745-byte save whose `WS` v1 header identifies
`KQ4`, changed the scene with Left input, selected Restore, then saved a second
snapshot. The second snapshot's room and ego object-0 X/Y fields match the
original save exactly: room 28, X=65, Y=127. An original-resource `look`
response also ran after restore. The current run is
`/private/tmp/kq4-persistence-state-20261029`, with screenshots,
`persistence.json` and the disk image; the prior selection-only run is
`/private/tmp/kq4-persistence-select-20261029`. This provides KQ4-specific
resumed-position and continued-execution coverage, but does not compare every
saved field or exercise failure/repeated-restore cases, so it is not an S08
pass.

The KQ4 `--persistence` route passed on 2026-11-06 against the current modules.
It created a 34,745-byte KQ4-tagged save, changed the scene, restored it, then
resaved after original logic displayed the river-meadow look popup. The saved
and resaved room/ego X/Y tuple is `(26, 56, 127)`; all saved flags and all
non-animation payload bytes match. The only other object-record changes are
the cel index, cel-resource offset, and cycle countdown for two non-ego objects
whose cycle flags are set; the test allows only these live animation fields
while all other non-variable changes remain errors. A debugger snapshot at the
state-command return matches saved variables 11, 62, 63 and 133 exactly
(`15, 56, 17, 15`); their later differences (`44, 48, 19, 43`) occur while the
original script continues. The restored look popup contains the exact
river-meadow text and retains 11/12 scene colors on its left/right sides.
Artifacts for this apply-boundary run are under
`/private/tmp/wildbits-kq4-apply-verified2-20261106`; the earlier full scenario
is under `/private/tmp/wildbits-kq4-persistence-final-20261106`. This closes
the KQ4 apply-boundary uncertainty only; broader S08 failure and restart cases
remain open.

## KQ3 visual/save-restore rerun (2026-11-16)

The original-resource single-game KQ3 runner passes with the current modules:
clock, movement, readable `look room` dialog over retained picture pixels,
dismissal and static-scene restoration, save/change/restore position, planned
exit and exact free-memory recovery. Captures and MAME log are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq3-current-fullcheck-20261116e`.
This is a bounded checkpoint rather than a complete KQ3 adventure or CoCo pixel
comparison. The KQ3 MAME oracle was corrected to infer glyph polarity from cell
corners (rather than majority fill) and to allow transparent cells to expose
the game palette.

## KQ3/KQ1 repeated-launch terminal stress rerun (2026-11-16)

`check_kq3_mame.py --pair-game kingsquest1 --stress-pair` passes on the current
modules. It checks the independent KQ1 terminal/inventory, first KQ1 exit,
second KQ1 launch and exit, KQ3 timed room transition and follow-up input, then
planned KQ3 exit. The post-second-launch process snapshot has only the KQ3
`wbgame` still running. Free memory is 16 KiB lower while KQ3 remains alive,
and returns exactly to the initial 856 KiB map after KQ3 exits. Artifacts are
in `/Users/boisy/Projects/coco-shelf/.wildbits-test/kq3-kq1-stress-current-20261116f5`.
This expands repeat-launch lifecycle evidence; other failure and stress cases
remain under V04.

## KQ4 Help/audio rerun (2026-11-16)

Current original-resource KQ4 MAME run passes with Help, direction tracing,
PSG tracing and WAV capture enabled. One Space advances the intro; Rosella's
rightward movement reports direction 3/view 0/loop 0 of 5 with AGI flag 20;
look, Help and Inventory dismissals restore the scene, and the game exits with
memory recovered. The log has 2,338 game-owned PSG writes; the 48 kHz stereo
WAV passes the non-silent sample check. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq4-current-fullcheck-20261116`.
This is emulator checkpoint coverage, not full KQ4 progression or hardware
audio acceptance.

## Larry Lefty's entrance rerun (2026-11-16)

The current original-resource Larry MAME run passes the age quiz, `open door`,
the transition into Lefty's and an interior `look`/dismissal, then exits with
unchanged free memory. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/larry-enter-current-fullcheck-20261116`.
This is an opening gameplay checkpoint, not full Larry progression.

The full KQ4 `--persistence` MAME scenario passed again on 2026-11-07 against
the current modules and the compatible Wild Bits test image. One Space advances
the intro; movement, the centered `look` popup, menu/Inventory and scene
restoration pass. The 34,745-byte KQ4 save has a valid header, movement changes
the scene, and Restore resumes the original logic. In the current rerun, the
saved/resaved room-and-ego tuple matches `(26, 69, 127)`; the apply-boundary
variables match the save, saved flags and non-animation payload bytes are
unchanged, and only live cycle fields advance. The restored popup retains
11/12 scene colors at its sides. Artifacts are under
`/private/tmp/wildbits-kq4-persistence-current-20261107`. This refreshes KQ4's
scripted save/restore route; it does not cover full saved-state parity or a
complete adventure playthrough.

After the 2026-10-29 51-script CoCo/native executor expansion and complete
59-command regression rerun, `tests/check_kq4_mame.py` was run again against the
rebuilt `wbgame`, `wbstate` and `wbui`. The original KQ4 intro, movement, river
meadow `look`, menu, Inventory dismissal and scene restoration all passed.
`kq4-look.png` in
`/private/tmp/kq4-popup-white-screen-assertion-20261029` shows the normal `look`
message in the centered popup with game graphics visible on both sides. The
checkpoint now also asserts that the Inventory screen contains only black and
white pixels: it is full-screen because its script selects `status` and
`text.screen`; the CoCo `cmd_status` body uses that same command sequence.
This confirms both native paths for this checkpoint, but does not replace the
still-open normalized CoCo/native pixel comparison in S04. No ordinary-print
full-screen regression was reproduced in this run.

On 2026-10-30, the scenario was tightened to send Right a second time after
the 500-frame walk and assert that Rosella stays stopped through popup and
Inventory dismissal. The run at `/private/tmp/kq4-walk-stop-assertion-20261030`
passed: the captured X position is 239.9 pixels after the stop, after `look`
dismissal and after Inventory dismissal. The centered popup retained 11 and 13
scene colors on either side; Inventory remained an opaque black/white page.
This removes ongoing movement from the display comparison but does not
reproduce a full-white page during an ordinary conversation.

The 2026-10-30 KQ1 `--sustained` real-driver rerun at
`/private/tmp/wildbits-s06-sustained-current-rerun-20261030` also verifies four
ordinary modal pages—two room descriptions, an unknown-word response and the
Pause message—as centered white popups over the colored game scene. The test
now checks the popup boundaries, visible scene on both sides, exact message
text and Pause glyph positions. It passes menu selection, resume, subsequent
input, controlled exit and free-memory recovery. It does not cover all key
repeat or inactive-terminal ownership cases.

The same rebuilt KQ4 checkpoint was rerun with `--audio-trace` and the matched
process-owned `PSGdrv`/`fPSG` modules. Through the post-Space intro capture it
observed four AGI command 99 calls, 1,166 PSG register writes and 220 non-mute
volume writes. The intro-scoped trace artifact is
`/private/tmp/kq4-audio-trace-intro-only-20261029/audio-writes.json`. This
proves the game sends sound events to the PSG driver; the MAME run uses
`-sound none`, so speaker audibility remains unverified.

The current 2026-10-30 KQ4 capture used MAME `-sound auto` and recorded four
command-99 sound requests, 977 owned PSG writes (188 non-mute volume writes),
and a non-silent stereo 48 kHz WAV during the intro window (AC RMS 51.3,
peak-to-peak 231). These are PSG/speaker-mix measurements before MAME's master
volume gain, as confirmed in the local MAME sound path; changing `-volume` does
not alter the WAV capture. The artifacts are in
`/private/tmp/kq4-audio-maxgain-20261030/`. Interactive `play.sh` generation now
explicitly uses `-sound auto -volume 12`, MAME's maximum supported gain, and the
emulator has been relaunched with that setting. The capture proves the game
produces non-silent audio data, but host-speaker audibility still needs the
user's confirmation.

To repeat the KQ4 checkpoint with the current modules and the documented MAME
environment:

```sh
SDL_VIDEODRIVER=dummy python3 tests/check_kq4_mame.py \
  --mame /path/to/mamed --disk /path/to/wildbits.dsk \
  --firmware /path/to/nitros9/recipes/wildbits/feu \
  --module-file objs/wbgame --helper-file objs/wbstate \
  --ui-helper-file objs/wbui --os9 /path/to/os9 \
  --output /tmp/wildbits-kq4-checkpoint
```

Add `--persistence` to that command to exercise KQ4's File-menu Save and
Restore actions, change the scene, compare the restored room and ego X/Y fields
through a second save, and verify that an original `look` response follows
restore. More gameplay fields and failure paths remain for S08.

## KQ4 persistence rerun on complete-check modules (2026-11-16)

`tests/check_kq4_mame.py --persistence` passed against the modules produced by
the 2026-11-16 complete `make -f wildbits.mk check` run. The scenario saved a
34,745-byte KQ4-tagged state through the original File menu, moved Rosella,
restored, and compared room and ego X/Y through a second save. It verifies that
saved flags and non-animation payload bytes are preserved while live animation
fields and variables continue advancing, then confirms the original `look`
command still runs after restore. Artifacts:
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq4-persistence-current-fullcheck-20261116b`.
This is a deterministic KQ4 persistence probe, not complete progression or the
full S08 failure matrix.

## KQ1 menu restart rerun on complete-check modules (2026-11-16)

`tests/check_wbgame_mame.py --game kingsquest1 --restart` passed against the
modules from the current complete check. The original menu restart unwound the
room-logic stack, reset the ego to X=449.5, resumed arrow input, stopped on a
second Right press and exited with unchanged free memory. Captured X positions
were 449.5 before restart, 581.5 before reset, 449.5 after reset and 609.5
after resumed movement. Artifacts:
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-restart-current-fullcheck-20261116`.
This is a restart checkpoint, not continuous progression from a fresh game.

## KQ1 menu save/restore rerun on complete-check modules (2026-11-16)

`tests/check_wbgame_mame.py --game kingsquest1 --persistence` passed against the
modules produced by the full check. The original File menu saved the game,
Right moved the ego from X=449.5 to X=625.5, Restore returned it to X=449.5,
and the restored game accepted the original `look` command. Exit free memory
matched startup. Artifacts:
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-persistence-current-fullcheck-20261116`.

## KQ1 east/west journey rerun on complete-check modules (2026-11-16)

`tests/check_wbgame_mame.py --game kingsquest1 --journey` passed against the
same module build. The east boundary loaded the original lake, `look` returned
the lake description, walking west restored the castle and its exact
description, and controlled exit restored free memory. Both dialog checks
confirm visible scene colors outside the modal. The Wild Bits modal palette is
black/dark blue/white; the initial rerun failed only because the oracle
incorrectly assumed a mostly-white CoCo-style popup. Artifacts:
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-journey-current-fullcheck-20261116c`.

## Current two-terminal process rerun (2026-11-06)

The real-driver `check_wbpic_mame.py --native-game kingsquest1 --interpreter`
scenario passed with two simultaneous `wbgame` processes. It compares the
displayed pixels, switches terminals and verifies both pictures restore,
closes one instance while the other survives, relaunches, then checks the
free-memory map. Artifacts are in
`/private/tmp/wildbits-multiterminal-compatible-20261106`. The first run against
the stock L2 image failed the restored-pixel assertion; the matching OS/graphics
driver image passed. This is controlled picture logic, not a pair of complete
adventures, and leaves modal/audio/save/repeated-failure stress for V04.

The same two-process scenario also passes with `--text-modes` at
`/private/tmp/wildbits-multiterminal-textmode-rerun-20261106`. It switches the
second terminal through text and graphics modes and checks every pixel. The
text-mode oracle now preserves the underlying picture and composites the
opaque text row, matching the CoCo `text.screen` behavior; the earlier oracle
incorrectly expected the entire graphics page to be blank.

With `--persistence`, the two-process run also passes at
`/private/tmp/wildbits-multiterminal-persistence-rerun-20261106`: it saves,
changes and restores the controlled game state on the second terminal, rejects
malformed and truncated snapshots, reuses an existing save name without an
error or scene change, validates the saved file and CRC, then checks survivor,
relaunch and free-memory recovery. The old assertion incorrectly expected an
error dialog for a save name that the implementation replaces by design; it is
now checked as a successful existing-file path.

The original Larry/KQ1 concurrent game pair also passed again on 2026-11-06
with the matching OS disk and expanded-memory kernel. It verifies both original
game scenes across terminal switches, independent KQ1 inventory input, Larry
continuing after KQ1 exits, and exact Larry-only/final free-memory maps. The
runner invocation must pass Larry as `--game` and KQ1 as `--larry-pair`; the
first diagnostic attempt reversed these paths and failed its KQ1-specific
inventory assertion. The successful artifacts are in
`/private/tmp/wildbits-full-game-pair-correct-20261106`.

## Current all-title startup rerun (2026-11-08)

After `make -f wildbits.mk check` rebuilt the current modules, the
`check_all_title_startup_mame.py` matrix passed for all fourteen bundled
titles with the Wild Bits-aware `mame` binary. Each original game reached a
changed display, returned to the shell after the controlled interrupt and
restored the original free-memory report. Artifacts are in
`/private/tmp/wildbits-all-title-current-20261108`. This refreshes startup and
cleanup evidence only; it does not add gameplay checkpoints for the ten titles
without richer routes, and does not complete V02 or V03.

## Current complete build/check rerun (2026-11-16)

`make -f wildbits.mk check` passed against the current worktree. The transcript
is `/tmp/wildbits-full-check-20261116.log`; it records 88 test commands,
including the full native integration and the paired CoCo/native suites, all
443 packed-picture, 11 streamed-picture and 228 KQ1 LZW checks, plus the final
6809 framebuffer/cleanup assertions. A reference-emulator launch timed out on
its first attempt and passed on retry. Current module sizes and hashes are
recorded in the matching section of `WILDBITS-PARITY.md`. This is build and
regression evidence only; V02/V03 gameplay coverage and V06 hardware acceptance
remain open.
