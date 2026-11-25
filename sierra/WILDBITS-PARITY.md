# Wild Bits / CoCo 3 parity acceptance checklist

Baseline: commit `da0bdc7`, 2026-10-15. This checklist defines completion of the
migration; it is not a percentage-complete estimate. CoCo 3's current engine is
the behavioral reference. Platform-specific memory, display, audio and file
representations may differ when their observable game behavior is equivalent.
PC AGI features that CoCo itself ignores are not additional implementation goals.

Check an item only after recording its test, reference and native revisions,
result, and any permitted platform difference here or in a linked report.
A dispatch destination or successful build alone does not close a behavior item.
Existing evidence below is scoped to the tests actually run. An unchecked item
may already work; it lacks the evidence required to close the parity gate.

## Verified starting point

- [x] **B01 — Build baseline.** All 63 owners build; all 56 CoCo images are
  byte-identical to the preceding verified revision. Native game/helper match
  the tested matrix.
- [x] **B02 — Native regression baseline.** Complete `check_wbgame.py` passes,
  including controlled original KQ1 quest chains, restart, persistence,
  recycled private memory, text, rendering and ownership cleanup.
- [x] **B03 — Original-game driver acceptance.** KQ3/KQ1 MAME scenarios pass:
  movement, dialogs, clock, save/change/restore, terminal independence and exact
  memory recovery. This is not an entire adventure completion.
- [x] **B04 — Latest focused regressions.** Priority tables/boundaries and fixed
  sprite depth, 52 static painting cases, 1,024 dispatch cases, 4,094
  index/formatter calls (including 548 direct formatter comparisons, seven
  recursion-depth cases, three malformed-message cases and a 2,211-byte
  output-bound comparison),
  object/global formatting, audio, and custom-priority two-terminal/cold-restore
  MAME acceptance pass.

Evidence and reproduction paths: [engine validation](WILDBITS-ENGINE.md#custom-priority-bands-and-fixed-priority-depth-2026-10-15)
and [MAME guide](WILDBITS-MAME.md). These checked baseline items do not close the
unchecked equivalence gates below.

## 1. Close the command coverage inventory

At the recorded baseline the catalog contained 182 commands: 171 had native
routes, including eight success-only routes; eleven were explicitly unsupported.
The C08–C11 correction gave 175 routed commands and seven unsupported
commands. C01–C03, C06 and C07 raise that to 180 routed commands and two unsupported routes. Four added success-only routes reproduce actual CoCo stubs, rather
than suppressing unimplemented CoCo behavior. Commands 0..17 execute
in the VM before platform dispatch and are included in both totals. These numbers
measure routing, not behavioral equivalence.

The catalog's CoCo symbol names are sometimes misleading: opcode 29 is labeled
`show pri` but calls `CmdSaveGame`; 144 and 175 both call `cmd_shake_screen`.
Compare the actual bodies and caller contracts, not symbol names alone.

| ID | Command route | CoCo reference | Acceptance required |
| --- | --- | --- | --- |
| C01 | 29: show-priority/debug UI | `CmdSaveGame` | Establish its actual visible behavior; match display/dismissal and restoration, without invoking native save accidentally. |
| C02 | 133: object status | `CmdObjStatusV` | Selected object's fields, variable argument, dismissal and unchanged game state match the reference. |
| C03 | 135: memory information | `CmdShowMemInfo` | Provide equivalent diagnostic information using native memory categories; document differences and restore the scene/input. |
| C04 | 149: trace on | `cmd_trace_on` | Reference enable/step/input behavior matches; normal execution resumes and no trace state leaks between instances. |
| C05 | 150: trace configuration | `cmd_trace_info` | Three operands, trace selection/display and invalid bounds match the reference; test with C04. |
| C06 | 170: automatic save naming | `cmd_set_simple` | Copy the selected string into the automatic name; document native path mapping and verify subsequent save/restore, repeated selection, clearing, bounds and cancellation. |
| C07 | 177: menu visibility | `cmd_show_menu` | Flag changes produce equivalent menu visibility and input behavior; test toggling, room change and restore. |
| C08 | 144: log | `cmd_shake_screen` stub | Consume one literal operand, return successfully like CoCo, preserve state and execute the next command. |
| C09 | 175: discard sound | Same CoCo stub | Consume one variable operand using the correct decoding contract; match CoCo's no-op, preserve active sound/state and continue. |
| C10 | 179: hide mouse | `cmd_hide_mouse` stub | Consume all four catalog operands, match CoCo's ignored operation, and leave the next instruction aligned. |
| C11 | 180: allow menu | `cmd_set_upper_left` stub | Consume both variable operands, match CoCo's ignored operation, and leave state/instruction alignment intact. |

- [x] **C01 — Priority diagnostic:** Actual CoCo/native conversion and control
  comparisons, loaded logic and real-driver MAME acceptance pass (evidence below).
- [x] **C02 — Object status:** Shared command/strings/word formatter; direct
  reference comparisons and loaded-script/MAME modal and restoration checks pass.
- [x] **C03 — Memory information:** Documented native category mapping, actual
  module headers/owned pages, guarded calculations and two-terminal modal/scene
  restoration checks pass.
- [x] **C04 — Trace enable and stepping:** The loaded native VM test enters
  trace mode, displays the selected event, advances on a step, resumes the
  following assignment and returns normally; it also verifies instance-owned
  trace-page cleanup. The real-driver MAME fixture passes with the active
  overlay advancing through KQ1 logic events. Reproduce with
  `tests/check_wbgame_mame.py --trace`; final captures are under
  `/private/tmp/wildbits-trace-final-rerun-20261017`.
- [x] **C05 — Trace configuration:** Loaded command tests cover operands
  `(0,1,8)`, `(255,255,255)`, and `(0,0,0)`, verifying raw configuration,
  minimum row clamping, wrapped byte arithmetic bounded by the 40x25 display,
  and continued script execution. `tests/check_trace.py` compares all 256
  event values against the CoCo reference contract. This shares the C04 loaded
  interpreter and provider tests; details are in
  [engine validation](WILDBITS-ENGINE.md#native-trace-backend-integration-abi-14-accepted).
- [x] **C06 — Automatic save naming:** Shared string-index copy, explicit native
  path mapping, bounds/clearing/lifetime, repeated selection, actual save/restore
  and existing-file replacement, cancellation and independent terminals pass.
- [x] **C07 — Menu visibility:** Literal values, request-time flag-14 permission,
  event-time visibility, deferred ordering, duplicate requests, controller
  delivery, default/module lifetime, room/restore behavior, two terminals and
  exact scene/memory recovery are verified.
- [x] **C08–C11:** Close each CoCo-stub compatibility case above individually.
- [x] **C12 — Existing success-only routes:** Verify all of 127, 155, 163, 164,
  173, 176, 178 and 181 against their actual CoCo bodies. Record argument
  consumption, successful return and preserved state for each. In particular,
  155's fixed-origin behavior is a permitted platform difference only after its
  observable effect is explicitly documented.
- [x] **C13 — Complete command manifest:** The generated manifest accounts for
  all 182 commands and 19 predicates with CoCo/native implementations, shared
  component/backend boundaries, route and semantic tests, and results. Every
  unsupported or intentionally different result links to its decision. The
  remaining seven open command-equivalence rows (111, 125, 126, 128, 129, 134,
  162) retain their focused evidence and explicit unresolved conditions; those
  are tracked under S06/S08 rather than missing from the inventory. Do not
  implement omitted PC behavior that CoCo does not implement merely to improve
  a count.

The static all-title audit and its self-test were rerun on 2026-10-29 into
`../.wildbits-test/audit-20261029-current-rerun`. It parsed all 1,470 bundled logics and
300,305 instructions across 14 titles, found no unsupported opcodes, and classified
all 19 predicates. It still reports 216 CoCo-ignored operations,
18 malformed/unknown formatter directives, 101 dynamic destinations and three
overlapping bytecode bytes in Manhunter I logic 159. The overlap is localized:
a jump at byte 245 targets byte 443, which is also the first byte of the
condition's skip operand at byte 438. The auditor records both decodings; the
executor test covers the corresponding alternate entry path. This resolves the
static parser ambiguity, but not a runtime comparison of this original resource.
The audit confirms inventory coverage only; C13 and semantic gates remain open
until the listed implementations and runtime regressions are tied together. The
native production build also passes at this
revision (`wbgame` 23,785/23,808 code bytes; `wbui` 8,089/8,192; `wbstate`
3,193/8,192).

The checked-in [C13 command manifest](WILDBITS-COMMAND-COVERAGE.json) links
every command and predicate to CoCo and native implementation source files,
names the shared-core/platform-backend boundary, and records the all-opcode
dispatch or predicate test result. It also gives each row a behavior policy
and decision link; the twelve CoCo no-op/stub routes link to their explicit
preservation decision below. Its self-test requires nonempty source and
decision links for all 182 commands and 19 predicates, and asserts there are
no unsupported command routes. This
closes the source/route accounting portion of C13, not semantic equivalence:
`check_native_dispatch.py` verifies routing, argument-table bytes and preserved
machine state, while behavior remains open wherever a focused differential
result is not recorded. Its S04 and S05
candidate-regression lists now include `check_wbgame_mame.py` and
`check_kq4_mame.py` for original-game screen-mode, popup and text behavior; these
are pointers to behavioral evidence, not blanket closure of those command
families. `tests/audit_game_scripts.py --self-test` and the 14-title
`--all-games` audit were rerun on 2026-10-29 and pass (182 commands, 19
predicates; 1,470 logics, 300,305 instructions, zero unsupported opcodes).
The current report is in `../.wildbits-test/audit-20261029-current-rerun/coverage.json`;
it confirms that Manhunter I logic 159 remains the only overlap-bearing
resource; the original overlapping jump/IF entry paths are now compared by
both real executors. On 2026-10-30, the 14-title audit was rerun against the
current worktree and passed to `../.wildbits-test/audit-20261030-parity/`:
1,470 logics, 300,305 instructions, no unsupported opcodes, 216 explicitly
ignored CoCo operations, 18 formatter findings, 101 dynamic destinations, and
three overlapping instruction bytes in Manhunter I logic 159. The audit
self-test now also asserts that dispatch-only S-gate rows remain `open`, and
that only predicates with a focused comparison have a completed equivalence
result. Complete Manhunter runtime and puzzle equivalence remain open.

On 2026-10-31, the C13 manifest self-test and all-title audit passed again in
`../.wildbits-test/audit-20261031-manifest-final/`. The manifest has 182 command and
19 predicate rows; every row links both a CoCo reference source and a native
source, identifies its acceptance gate and candidate regression tests, and
links its behavior decision. All twelve intentional `VmSuccess` rows link to
the CoCo-stub decision. There are no unsupported command routes.
The audit parsed 1,470 logics and 300,305 instructions across all fourteen
bundled titles, with zero unsupported opcodes. It classifies 216 ignored CoCo
operations, 18 formatter findings, 101 dynamic destinations, and the three
overlapping instruction bytes in Manhunter I logic 159. The inventory is now
complete, but it does not mark dispatch as behavioral equivalence: the 19
accepted C01-C12 command rows and 18 predicate rows have closed equivalence
results; the remaining 163 command rows and predicate 13 remain open under
their semantic acceptance gates. The generator self-test now enforces
that distinction.

#### C13 and predicate manifest refresh (2026-11-06)

The current manifest was regenerated after adding direct evidence for
predicate 13 (`have.key`). Its self-test and all-title audit pass across 14
titles, 1,470 logics and 300,305 instructions, with zero unsupported opcodes.
All 19 predicate rows now have a focused acceptance result. Of 182 command
rows, 112 have command-level evidence and 70 remain open across S02–S08; C13
remains open until those command behaviors are covered or their platform
differences are explicitly accepted. The refreshed data is checked in as
[`WILDBITS-COMMAND-COVERAGE.json`](WILDBITS-COMMAND-COVERAGE.json).
Reproduce with
`python3 tests/audit_game_scripts.py --self-test` and
`python3 tests/audit_game_scripts.py --all-games --output-dir ../.wildbits-test/audit-20261031-manifest-final`.

#### C13 command-evidence refresh (2026-11-06)

After rerunning `check_inventory_commands.py`, the manifest now ties opcodes
92–97 (`get`, `get.v`, `drop`, `put`, `put.v`, `get.room.v`) to their actual
CoCo/native state comparisons and boundary results. The generator self-test
requires the S06 inventory and cancel/echo rows to retain their specific test
and result text, while leaving other S06 commands open. The current generated
manifest now also records opcode 105 (`clear.lines`) from the paired CoCo text
request and Wild Bits framebuffer regression, and opcodes 131/132 from the
actual program/player-control handler comparison. It records 139 of 182
commands with command-level evidence and 43 open; all 19 predicate rows have
focused results. S06 has 18 open command rows, and C13 remains open. Reproduce with
`python3 tests/audit_game_scripts.py --self-test` and the all-title audit.

The first restricted attempt to run `check_decimal_index.py` failed when the
6809 harness tried to bind its localhost debugger socket. With local loopback
available, the focused test passed on 2026-10-19, including the added original
Space Quest II message-table case, 548 formatter comparisons and 4,094 calls.

### S01 focused VM and predicate evidence, refreshed 2026-10-30

At repository revision `6829106` plus the current working-tree test sources,
the following actual-6809 CoCo/native comparisons pass: `check_coco_conditions.py`
(all 19 predicate-table entries relocate; unsigned comparison and packed-flag
boundaries at two code bases), `check_condition_flow.py` (all 16 mixed
AND/OR/NOT combinations, short-circuit callback order and branch/cursor/stack
guards), `check_math_commands.py` (4,544 calls including all byte dividends,
zero divisors, boundary products/quotients, variable indexes and aliasing),
`check_random_command.py` (all 256 controlled generator bytes over eleven
inclusive/wrapping ranges, destination indexes 0/255 and range edges),
`check_said.py` (ASCII folding, both wildcard forms, endian IDs, length and
input-gate boundaries), and `check_logic_executor.py` (51 scripts at two code
bases, including indirect-variable reads/writes through v0 and v255, both
Manhunter I logic-159 decodings, arithmetic/flags, conditions, branches,
command tables, operand advancement and frame guards).
The executor test also runs the same four-script nested-call graph through the
actual CoCo command dispatcher at both code bases: root `call 1`, child
`call.v 3`, then root `call.v 2`. It checks the same post-return variables,
caller continuation, script bounds, stack and executable-code guards used by
the native loaded-resource fixture in `check_wbgame.py`; the CoCo fixture
preloads its four slots to isolate interpreter semantics from its OS resource
loader. The native integration additionally verifies call depths `0,1,0` and
normal root quit. The executor test also calls the actual CoCo and native
`set.scan.start` / `reset.scan.start` handlers at both load bases: CoCo absolute
pointers normalize to the same native offsets, reset returns to each logic's
start, and updating the second logic slot leaves the first slot unchanged. All
six tests pass, including the refreshed 51-script executor fixture.
`check_wbgame.py` now also loads four controlled logic resources through the
native loader and runs a literal `call`, a child `call.v`, and a root `call.v`.
The test checks child-written variables after each caller resumes, observes the
call depths `0,1,0`, and verifies the root reaches quit with depth zero. The
focused test and Python compile/diff checks pass on the current workspace.
The 2026-10-30 executor comparison covers truncated `assignn`, `addn`, `subn`,
`assignv`, `addv` and `subv` instructions at both code bases. For the first
three, CoCo consumes the following controlled byte `42` as the missing
literal; v0 becomes 42, 42 and 214. For the variable forms, it consumes that
byte as v42 and v0 remains zero. All six reach the next `return`. Wild Bits
stops at `vmend` with EOF, leaves v0 zero, and preserves its stack, code and
script boundary. The test treats the 6809 carry bit as arithmetic state, not
as an error signal. This documents a real safety difference on malformed
bytecode, not equivalent error behavior. S01 remains open for acceptance of
that difference and broader malformed-script, error-cleanup and
branch/resource-bound comparisons; indirect-variable script integration,
nested calls and scan-marker handler equivalence have paired CoCo/native
evidence. `check_logic_executor.py` passes this expanded six-command matrix.

The 59-command target also ran on 2026-10-30 after the first malformed-command
expansion (`assignn`, `addn`, `subn`) and reached its final `check_wbpic.py`
pixel/resource check, which passed. Module sizes were `wbgame` 23,785/23,808,
`wbui` 8,089/8,192 and `wbstate` 3,193/8,192 bytes. The three additional
variable-command cases were then verified by a fresh standalone
`check_logic_executor.py` run; the complete target was not repeated after this
test-only extension. Neither 2026-10-30 run has a retained full console log.

### S02 resource-format, replay and cache evidence, refreshed 2026-10-30

At source revision `6829106` plus the current working-tree sources, five
focused actual-6809 regressions were rerun on 2026-10-30 and passed:
`check_lzw.py` compares 228 compressed KQ1 logic/view/sound resources against
the shared oracle and exercises 528 direct reads across bit alignments and code
widths, including malformed native streams and exact input consumption;
`check_resource_format.py` performs 9,184 directory/header decoding calls,
covering every directory byte, size-byte boundaries, endianness, guards and
context preservation; and `check_resource_lifetime.py` exercises 18 discard
calls at two load bases, including CoCo suffix rewind and native typed-slot
release/absent/release-failure behavior. `check_replay_differential.py` compares
CoCo script-operation records and checkpoint rollback with Wild Bits resource
replay records at two code bases; both preserve the same sequence after a
discarded tail is overwritten. `check_logic_executor.py` executes the original
Manhunter I logic 159 overlap paths in both owners and compares state/cursors.
`check_replay_differential.py` was rerun from `objs/` after the full target on
2026-10-30; it again passed the matching record sequence, checkpoint restore,
discarded-tail overwrite, allocation guards and stack guards at two code bases.
It is now part of the standard `wildbits.mk check` target, so this record-level
replay comparison is no longer a manual-only regression.
The same executor test now also compares a four-resource nested logic call on
CoCo and Wild Bits at two code bases, including variable results, root cursor,
active resource, call depth, stack, cache bytes and guards after each caller
resumes. Native asset-pointer mapping is supplied by the harness; this isolates
the actual native cache lookup and nested VM execution, but does not exercise
the disk loader. The native-only `check_wbasset.py` loader regression was also
rerun: actual 6809 code reads and expands original KQ1 logic 0, reads an exact
16-KiB plain asset and a synthetic 65,535-byte LZW stream, and cleans up partial
I/O, malformed stream, allocation/map/unmap/read/write failures. This
establishes substantial native loader behavior. On 2026-11-05,
`check_coco_volume_load.py` added the paired original-volume check: it uses the
same KQ1 `logDir` entry and `vol.*` bytes, runs actual CoCo `FindVol` and LZW
code plus Wild Bits `wbasset`, and compares the full 8,950-byte logic 0 result
at two code bases. It then truncates that same volume inside the packed LZW
payload: CoCo reaches its production I/O error prompt and returns a null
resource when the harness selects quit, while Wild Bits rejects the resource
instead of returning a completed payload. This covers the successful original
load and one paired truncated-stream failure; disk discovery and broader paired
read/map failure behavior remain open. A controlled plain-record fixture stores
those same expanded original logic bytes without compression; both direct-read
paths return the same 8,950 bytes. A second paired failure injects an OS-9
`I$Read` error on the payload read after the valid header: CoCo takes its normal
error prompt and returns a null resource, while Wild Bits propagates the error,
returns no output, and releases its partial slab. These checks cover one
specific read-service failure, not all read/map failures. The expanded
`check_coco_volume_load.py` passed on 2026-11-06, as did the affected
`check_wbres.py` and `check_wbasset.py` loader regressions; the 62-command
integrated run above predates these harness-only additions. Cache lifecycle and
replay restore are covered by the following evidence.
`check_view_cache_reload.py` now runs original KQ1 view 0 through the loaded
Wild Bits VM with `load.view`, `discard.view`, `load.view`, and `quit`; it sees
exactly two loader calls and confirms the reloaded cache record retains the
same resource lengths and type. In the same test, CoCo's real `view_load` and
`DiscardViewHelper` routines perform cache-hit, unlink, and reload against the
same original expanded view bytes; only CoCo's page/file service boundary is
controlled. The separate CoCo LZW/volume test covers real disk reads. These
checks now establish cache hits, discard/reload, and bounded cache-slot reuse.
The expanded paired case holds eight distinct views, discards view 0 from the
middle of the CoCo list, and loads view 8. Wild Bits reuses the same cache slot;
CoCo retains the other list entries and appends the new view. This test exposed
that `DiscardViewHelper` previously zeroed the predecessor link and lost every
later view; it now links the predecessor to the discarded node's successor.
`check_resource_lifetime.py` now checks successor links for removal at the head,
middle and tail of the list. The paired loader and eight-view lifecycle checks
pass with that fix. Eight simultaneous views are verified. A 32-view fill
attempt hit process `E$MemFul`, so the test proves slot reuse after discard but
does not fill all 32 metadata slots. The paired volume-loader check covers
original LZW and controlled plain-read paths, truncated LZW input and one
injected OS-9 `I$Read` error after a valid header. Paired allocation and mapping
failures and other read-error positions still need coverage.
Runtime replay restore is covered by the focused differential and KQ1 MAME
quest-save scenario below. S02 remains open for the remaining failure cases,
nested-resource boundaries and full-resource execution.
On 2026-11-06, the MAME `quest-save` run reached both save and restore prompts.
The saved snapshot passed its header/CRC checks and contains replay limit 255,
one two-byte `(load view, 143)` record, and checkpoint zero. A state trace then
showed the restored game reaching room 53, stage 5, with the expected score and
quest progress. The fixture was waiting for its final room flag, so the MAME
driver now supplies that controlled ending condition only after the restored
run reaches that room. The game then wrote the ending snapshot and returned to
the shell; free memory was byte-identical before and after at 368 KiB. The
ending snapshot's replay prefix matched the live restored replay log. Because
the checkpoint is zero, that replay prefix correctly replaces the earlier
saved `(load view, 143)` record. The standalone validation passed both snapshot
CRCs, checked the restored replay prefix and confirmed that checkpoint rewind
replaced the discarded tail. At that point the updated runner and complete
check target had not yet been rerun; the fresh results below supersede that
status. S02 remains open for broader paired failure cases, nested-resource
boundaries and full-resource execution, the other open semantic gates, and
physical-hardware verification.
The view lifecycle, paired loader, and replay-record comparison are wired into
`wildbits.mk`. On 2026-11-06, the complete `make -f wildbits.mk check` target
passed all 62 Python commands after the CoCo list-unlink fix, including the
head/middle/tail resource-lifetime checks, paired eight-view CoCo/Wild Bits
cache reuse, original-volume/truncation comparisons, replay-record differential,
complete `check_wbgame.py` integration, packed pictures and final `check_wbpic.py`
pixel checks. Build and module-budget checks passed: `wbgame` 23,750/23,808 bytes,
`wbui` 8,089/8,192 and `wbstate` 3,193/8,192. This closes that software
regression run, not the full parity goal: S02 broader failure cases and
full-resource execution, the other open semantic gates, and physical-hardware
verification remain open.
The updated `tests/check_wbgame_mame.py --quest-chain quest-save` runner also
passed end to end in MAME on 2026-11-06 from a clean 4 MiB bootable test disk
and the matching emulator firmware. It reached the original save, restore and
ending prompts; validated both snapshot CRCs and gameplay fields; verified the
checkpoint-zero replay tail was replaced and re-recorded at the ending prompt;
and compared byte-identical 880 KiB free-memory maps before and after. The
complete command and log are recorded in `WILDBITS-CHECKPOINTS.md`. The captured
post-exit terminal contains `ERROR #215`; the runner currently does not
classify that message, so it remains a follow-up to investigate rather than
being called harmless. This closes the previously missing fresh runner
invocation for this scenario only. Broader paired failure cases, full-resource
execution, other semantic gates and physical-hardware verification remain open.

### S03 object and motion primitive evidence, 2026-10-19

Nine actual-6809 CoCo/native comparisons pass: `check_object_flags.py`,
`check_object_scalar_commands.py` (7,188 calls), `check_object_bounds.py`
(7,500 cases), `check_object_terrain.py` (3,328 scans), `check_motion_setup.py`,
`check_move_direction.py` (9,280 calls), `check_object_collision_filter.py`
(3,100 calls), `check_object_coordinates.py`, and `check_cel_advance.py`.
Together they cover object flag/field preservation, first/last records, screen
and horizon bounds, terrain/control masks, move setup and completion, direction
selection, collision ignores and self-filtering, coordinate aliases and deltas,
cel loop modes, wrap edges, callback context and stack/record guards. All nine
pass at two code addresses where the harness supports relocation. The terrain
pixel mapping is mocked. S03 remains open for integrated scenes with overlapping
moving actors, follow/wander over time, blocking interactions and room-edge
transitions; primitive command agreement alone does not establish those flows.

On 2026-10-30, the current original-resource KQ1 journey run
`/private/tmp/wildbits-kq1-journey-current-rerun3-20261030` passed the east
castle-to-lake transition, the return transition, exact lake/castle descriptions,
continued command input and exit-memory recovery. It exposed two obsolete
full-screen text expectations in the MAME test; the original game displays both
descriptions in centered white popups over the scene. The scripted walks now
hold long enough to reach each room edge, and the test checks popup text and
scene pixels outside the popup. This is an integrated original-game movement
checkpoint; overlapping actors, follow/wander interactions and other room-edge
cases remain open for S03.

On 2026-10-31, the collision-filter comparison added two active, opposing
movement records. It starts them one pixel apart, then moves each one pixel to
edge contact and compares CoCo/native collision results at both code bases.
This exposed a real native boundary mismatch: the wide Wild Bits comparison
treated equal interval edges as non-colliding, while CoCo's byte comparison
counts edge contact. The wide comparison now skips only on a strict greater
result. `check_object_collision_filter.py` passes all 3,100 paired calls,
including record/control preservation, collision-scan order, stack and bounds.
This covers the post-step overlap decision; simultaneous full-cycle movement,
follow/wander sequences, blocking interactions and room-edge behavior remain
open, so S03 stays unchecked.

The 2026-10-31 `check_wbplay.py` run drives two observed, active objects
toward one another through repeated cycles of the loaded `wbgame` module. The
first actor advances from X=10 to X=19; the second advances from X=30 to X=21.
Both remain on Y=60, and neither commits the next step because the shared
edge-contact collision rule sees the other actor's committed position. The
same scene is then run for ten ticks through CoCo's actual `UpdateAllMotion`
routine from `mnln.asm`; its only test substitution is a local stub for the
CoCo MMU/terrain placement service that reports this controlled scene as
walkable. CoCo and Wild Bits end at exactly the same two positions. This closes
the paired two-mover motion/collision case, not the entire event loop. Follow/
wander sequences, blocking interactions, room-edge behavior and broader
multi-actor scenes remain open; S03 stays unchecked.

Focused object checks were refreshed on 2026-11-07. `check_object_coordinates.py`
and `check_object_flags.py` pass their command families; `check_object_distance.py`
passes 24 actual CoCo/native calls; `check_object_position_predicates.py` passes
3,200 calls; and `check_object_update_control.py` passes 8,192 stop/start calls
over all initial flag bytes and four object slots. These checks cover primitive
state and operand behavior only. Full-cycle movement, follow/wander sequences,
blocking interactions and room-edge behavior remain open under S03.

### S04 picture and sprite evidence, 2026-10-19

Seven graphics checks pass: `check_picture_stream.py` verifies streamed picture
handling and malformed-input cleanup; `check_fill_selection.py` compares 9,136
fill selections; `check_add_to_picture.py` checks 52 immediate/variable static
cel draws and priority/occlusion behavior; `check_cel_clipping.py` compares
5,920 clipping cases; `check_priority_bands.py` compares all 168 CoCo tables,
4,565 native custom priorities/band heights and transitions; and
`check_wbsprite_damage.py` exercises movement/erase restoration and span failures.
Most importantly, `check_packed_pictures.py` compares all 443 bundled original
packed pictures against CoCo and an independent oracle, rejecting bounded
malformed inputs. All pass. S04 remains open for complete scene-level
pixel/palette normalization, text/graphics mode switches and restoration after
all modal UI and failure paths.
The log’s broader A04 result and this focused rerun together cover the updated
test source.

#### S04 stream, fill and pixel refresh (2026-11-06)

The current worktree passes `check_picture_stream.py` on ten streamed original
and boundary pictures, including exact 8/16-KiB limits, a 65,535-byte length,
resumed logic, malformed operands and cleanup. `check_fill_selection.py` passes
9,136 actual CoCo/native selections at two addresses, and `check_wbpic.py`
passes its 6809 pixel, short-read, mapping-boundary and ownership checks. These
focused cases pass; scene-wide palette normalization and all UI/failure
restoration paths remain open under S04.

The `check_add_to_picture.py` rerun enters CoCo's actual `cmd_add_to_pic` and
`cmd_add_to_pic_v` handlers for 104 immediate/variable cases and checks the
normalized six-byte request at `AddToPicImpl`, operand advance and caller
stack. CoCo packs priority in the low nibble and control in the high nibble.
Its paired Wild Bits scenarios cover 52 rendered static-cel cases, including
default/custom/hidden priority, control-box bands, occlusion, clipping and
persistence. The same test now also runs CoCo's actual `ObjBlit` and
`ObjAddPicPri` routines against paired cel/background pixels.

On 2026-11-07, `check_add_to_picture.py` passed again: 52 native rendered cases
and 104 actual CoCo literal/variable command calls at the normalized draw
request boundary. It also passes 53 pixel comparisons through actual CoCo
`ObjBlit`/`ObjAddPicPri`: one paired renderer case for each of the 52 native
scenarios plus a repeat at a second CoCo code base. The matrix covers transparent
runs, automatic/fixed and hidden priorities, custom priority bases, control-box
edges, priority occlusion, and top/right clipping. Its renderer fixture makes
the cel directly addressable and stubs only `TwiddleMmu`; it does not establish
the complete OS dispatcher/MMU path. A follow-up rerun now also sends those 104 commands through
the actual `AddToPicImpl`, `view_find`, `SetViewForObj`, `SetLoopHelper`,
`SetCelHelper`, `FindObjPos`, `CheckObjBounds` and `CheckObjCollision`. It
resolves a real loaded-view list node, loop and cel pointer, checks dimensions
and object fields, then bounds-checks placement and scans a deliberately empty
object list. The `$0701` callback counts three dispatches per command (one
placement and two draw calls); its preseeded placement-success flag controls
the actual `FindObjPos` continuation. Operand/caller stacks, packed priority
and control, service counts and logic-page call count are checked. A second
pass sends 36 of those immediate/variable invocations through the same real
`AddToPicImpl` and view/placement path, then tail-dispatches the visual `$0F`
selector to CoCo `ObjAddPicPri`/`ObjBlit`. Those 36 complete frames match the
paired Wild Bits oracle. The harness counter lives outside picture memory; it
also guards against counter/frame overlap. In both integration passes,
`PushScript`, `ClearBothRanges`, `SwapObjRanges` and `SetLogicPage` are instrumented
return stubs, and the selector-aware `$0701` shim supplies placement success,
skips the empty priority-range list, and directly calls the renderer. The
picture data is directly addressable and `TwiddleMmu` is stubbed. Thus opcode
122/123 rendering is now compared through the command-to-pixel path for the
tested matrix, while production MMU bank switching, nonempty range operations,
custom-base AddToPicImpl cases, and the broader scene-level S04 presentation
paths remain open. The regenerated C13 manifest now records scoped behavioral
evidence for all 13 S04 commands (156 of 182 total commands and all 19
predicates); it keeps the overall S04 family open for those remaining scene,
MMU and failure-path requirements.
`check_packed_pictures.py` also passed all 443 bundled
original pictures against both CoCo and the independent oracle, rejecting its
malformed-input cases. The renderer comparison executes CoCo `ObjBlit` and
`ObjAddPicPri` against the Wild Bits pixels for all 52 static-cel cases:
transparent runs, automatic and fixed priorities, default and custom priority
bases, control boxes, occlusion and clipped coordinates. All pixels match; a
53rd matched case reruns at a second CoCo code base. The custom table fixture
uses the formula independently compared against all 168 actual CoCo
`SetPriBase` tables by `check_priority_bands.py`. The direct renderer harness
stubs only `TwiddleMmu` because it keeps the cel directly addressable. The
36-case integrated `AddToPicImpl`/renderer run also substitutes the OS MMU and
range/page services as described above; it closes opcode 122/123 for this
static command-to-pixel matrix, but not production bank switching, nonempty
range lists, custom-base integration or the broader scene-level presentation
gate. On the same
date, `check_cel_clipping.py` passed 5,920 actual CoCo/native cases
at two code bases, and `check_priority_bands.py` passed all 168 CoCo tables and
4,565 native custom-priority/band-height cases, including transitions, default
rows, fixed priority and invalid-base handling. The scene-level S04 gate stays
open for the documented rendered add-to-picture and broader presentation paths.

The 2026-11-06 MAME `--text-modes` rerun also switches the second live game
terminal into text mode and back. Its pixel oracle now overlays the opaque text
row on the saved graphics picture and requires exact restoration afterward.
The first attempt exposed an outdated oracle that expected a blank graphics
page; the corrected test and current modules pass at
`/private/tmp/wildbits-multiterminal-textmode-rerun-20261106`.

The full-suite `check_wbsprite_damage.py` run exposed an assertion requiring a
narrow paint span even for a fully off-screen sprite at (255,255). The test now
applies that optimization assertion only to on-screen fixtures; the movement,
erase, clipping, off-screen, staging, large-cel and mapping-error test passes
independently.

On 2026-10-29, the `--king-dialog` MAME fixture passed the 2,000-frame speech
hold, fresh-key dismissal, graphics restoration and memory recovery, but its
full-screen assertion encoded a Wild Bits regression as expected behavior. The
CoCo reference handler switches text mode without clearing the graphics page;
KQ1 logic 53's speech must therefore overlay the throne picture. On 2026-10-30
`GameTextScreen` was corrected to preserve the picture and existing text cells,
and switch `vmgraphics` off until `graphics` restores it. The revised native
pixel fixture compares the original KQ1 scene plus its text glyphs; the fresh
MAME rerun at `/private/tmp/wildbits-textscreen-overlay-rerun-20261030` passes
the 2,000-frame hold, retained throne-scene colors, fresh-key dismissal and
memory recovery. The king fixture remains synthetic after it enters the speech
sequence, so full original `talk king` execution is still unverified.

On 2026-11-07, the same `--king-dialog` scenario passed again against the
current built modules at `/private/tmp/wildbits-king-dialog-current-20261107`:
the dialogue remains stable over the throne-room picture for 2,000 frames,
fresh input restores the exact scene and the game recovers memory on exit. This
confirms the overlay fix is still present in the current build; it does not
replace the open direct CoCo/native dialogue capture or exercise the complete
original `talk king` script.

KQ4 Inventory is a distinct opaque page: Wild Bits `InventoryStatus` explicitly
fills its text plane with white cells, while CoCo `cmd_status` switches to text
mode and draws the same full-page inventory. A fresh KQ4 MAME rerun after the
complete 59-check target passed both display assertions: ordinary `look`
remains in a centered 21-by-7 `print` popup with scene pixels outside, while
Inventory is an opaque black/white page. The Inventory assertion was added to
`tests/check_kq4_mame.py`; both passed in
`/private/tmp/kq4-popup-white-screen-assertion-20261029`. A further
current-module rerun at
`/private/tmp/kq4-opening-text-artwork-20261029` also verifies that KQ4's opening
Genesta dialogue leaves title artwork visible around it. The KQ1 king speech
fixture described below exercises the separate `text.screen` path. A current
KQ3 MAME rerun on 2026-10-29 now
captures the original `look room` response as a centered white popup over the
colored room, with scene pixels outside the 21-by-7 bounds and the room restored
after Space. `tests/check_kq3_mame.py` now checks the popup contents, boundaries,
visible surrounding scene and restoration. The run passed with current
`wbgame`/`wbui`/`wbstate` in
`/private/tmp/kq3-display-current-rerun-20261029`; it replaces a stale text-only
assertion that failed to account for graphics behind the popup. This confirms
the current native `print` path for that KQ3 action, but is not a normalized
CoCo 3 capture. The subsequent `text.screen` fix covers the separate mode that
was clearing graphics; the user's exact title/action remains unidentified.
The complete KQ3 movement/save/restore MAME checkpoint passed again on
2026-11-05 with the rebuilt modules. It verified the visible clock, movement,
original room text, save/change/restore position and static scene pixels,
planned exit and unchanged free memory. Its artifacts are under
`/private/tmp/wildbits-kq3-resume-20261105`; it does not establish full-game or
direct CoCo/native capture parity.
On 2026-11-05, the real-driver Larry bar route also passed with the rebuilt
modules. It checks the original quiz and door response, the room transition,
the full `look` response inside a popup, colored bar pixels outside the popup,
dismissal and memory recovery. The MAME test's old full-frame black/white
expectation was replaced with these scene-aware assertions; artifacts are in
`/private/tmp/wildbits-larry-popup-rerun-20261105`.
S04 and S06 remain open for direct CoCo/native dialogue comparison and broader
modal coverage.

On 2026-10-31, `tests/check_kq4_mame.py` passed against the freshly rebuilt
modules and the Wild Bits Jr2 MAME image. One Space plus one Return reaches the
gameplay scene; scripted Right-arrow movement changes Rosella's screen X from
487.1 to 179.1 as the camera scrolls; the look popup retains the colored scene
around it and restores the original position after dismissal; and the
menu/Inventory sequence restores the same scene position. Captures and the
private disk image are under
`/private/tmp/wildbits-kq4-current-parity-20261031`. This confirms these
original-resource display/input paths in MAME; it is not a direct CoCo capture
comparison or full KQ4 completion.

The same original-resource KQ4 MAME checkpoint passed again on 2026-11-02
against the rebuilt modules. It verified one-Space intro advance, the scripted
Right movement and stop, the centered `look` popup with colored room pixels on
both sides, menu/Inventory open and close, and Rosella's restored screen
position. Artifacts are under
`/private/tmp/wildbits-kq4-resume-20261102`. This remains a bounded playability
checkpoint rather than a complete CoCo/native capture comparison or full
adventure run.

The native `tests/check_wbgame.py` full-frame checks cover foreground color 14,
rectangle clears over a displayed message, and text/graphics mode transitions.
The `text.screen` test compares the retained picture and overlay cells and
checks that text mode clears `vmgraphics`. The complete 59-command standard
target passed after this change on 2026-10-31; see its retained log below. A
focused current actual-6809 fixture and the MAME king-dialog scenario also
pass. S04 remains open for direct normalized CoCo/native capture comparisons of
text colors and graphics restoration.

On 2026-11-22, the KQ1 text-screen path was tightened to match the user's
requested window treatment: a broad white text area, a black tile border, and
bounded wrapping that keeps display text off the frame. The frame is reapplied
before each text presentation so successive display messages cannot leave
holes. `tests/check_wbgame_mame.py --king-dialog` passed against the original
KQ1 king speech: the panel remains stable for 2,000 frames, a fresh key restores
the throne picture, and the process recovers its memory. The same check passes
its pixel assertions for black/white panel contents and the black frame.
`--journey` also passed after the change, including lake/castle descriptions,
room transitions, and continued play after dismissing ordinary `print` text.
The MAME capture uses the original KQ1 logic and a scripted `talk king` input;
it does not represent a complete manual playthrough or a direct CoCo pixel
comparison.

The current rebuilt modules were rerun through `tests/check_kq4_mame.py` on
2026-10-29; the test passed its opening dialogue, gameplay, movement, centered
`look` popup, Inventory and restoration assertions. This run follows the latest
capacity edits and ABI correction; it reports `wbgame` 23,785/23,808 bytes,
`wbui` 8,089/8,192, and `wbstate` 3,193/8,192. The capture at
`/private/tmp/kq4-display-current-rerun-20261029/kq4-look.png` retains the
river-meadow picture around the dialogue. The separate
`/private/tmp/kq4-display-current-rerun-20261029/kq4-inventory.png` is a full white
text page. CoCo `cmd_status` sets black on bright white, selects text mode, and
draws Inventory across the page. Wild Bits `InventoryStatus` explicitly fills
its private text plane with white cells. Thus the full-page Inventory is
expected on both platforms; it is not evidence that ordinary `print` text hides
the Wild Bits scene. Direct normalized CoCo/native dialogue captures remain
open under S04.

After the user's report of a white screen obscuring game graphics, the KQ4
`look` and Inventory scenarios were rerun. `look` retained the colored
river/meadow outside its centered popup; Inventory showed the separate full-page
page. A 2026-10-31 acceptance rerun again passed the popup test: the measured
center window had two colors and was 87.3% light, with 11 colors visible on the
left and 13 on the right; its capture is
`/private/tmp/wildbits-kq4-popup-recheck-20261031/kq4-look.png`. The KQ1
`--king-dialog` scenario also passed on the current build at
`/private/tmp/wildbits-king-overlay-current-20261031`: the throne scene remains
visible around its text-screen content, a fresh key restores the scene, and
exit recovers memory. That fixture still injects the speech sequence after the
real `talk king` input, so it does not verify the complete original dialogue
script. Neither run reproduces a full-screen white replacement for ordinary
`look` or the tested king text mode. A subsequent audit found the shared
cause: Wild Bits `GameTextScreen` was clearing all 25 text rows, while CoCo's
`cmd_text_screen` only selects text-overlay mode. KQ1 logic 53 and KQ4 logic 99
use that command while graphics are visible. The handler now preserves the
picture and existing cells and sets `vmgraphics` to text mode. The current MAME
king-dialog capture and a focused actual-6809 pixel comparison pass with scene
pixels retained. The exact action that produced the user's reported full-white
screen remains unidentified, and a normalized CoCo/native capture remains open.
A direct CoCo 3 MAME
capture was obtained on 2026-10-30 using the original KQ4 disk and CoCo 3
MAME. `/private/tmp/coco-kq4-parity-20261030/co-ref-look-beach.png` shows a
bordered white dialogue box over the beach picture; the scene remains visible
around it. After Space,
`co-ref-look-beach-restored.png` shows the picture still present.
This confirms the CoCo overlay/restoration behavior, but it is not a normalized
pixel comparison with the Wild Bits `look` capture: the two runs reached
different original dialogue text and scene states. The first CoCo Inventory
capture reached the game's “Please insert disk 2, side 1” prompt. I corrected
the capture sequence to mount disk 2, dismiss the prompt, and reissue
`inventory`. The resulting
`/private/tmp/coco-kq4-parity-20261030/co-inventory-confirmed.png` is an opaque
black-on-white text screen (120,912 white and 32,048 black pixels); after a
Space,
`co-inventory-dismissed.png` restores the beach scene (16 colors). The current
Wild Bits KQ4 run likewise shows an opaque two-color Inventory page and restores
the picture after a fresh key. Inventory/status therefore accounts for a
full-white screen on both platforms; it is not the centered `print` popup.
This CoCo behavior is now reproducible with
`tests/check_coco_kq4_inventory_mame.py`; the 2026-10-30 run passed and saved
captures/results under `/private/tmp/coco-kq4-inventory-acceptance-20261030`.
That check requires CoCo 3 MAME ROMs and both original 80-track KQ4 disks. The
check now also issues `look room` after the disk-2 swap and asserts a white
center popup (75.0% white, 17.9% black in the measured window) plus scene colors
outside it (4 colors on the left, 12 on the right). The 2026-10-30 rerun passed;
its artifacts are under `/private/tmp/coco-kq4-ui-parity-20261030`. The matching
Wild Bits scenario at `/private/tmp/kq4-persistence-verified-20261030` shows
the same overlay behavior and separately verifies the full-page Inventory.
The CoCo assertion closes the display-mode ambiguity for these KQ4 actions;
the exact text/scene differs between the runs, so a state-matched pixel
comparison remains open.

The CoCo reference capture was reproduced again on 2026-11-05 using stock
MAME 0.289 and the original KQ4 disks. `tests/check_coco_kq4_inventory_mame.py`
passes with the same results: 120,912 white and 32,048 black Inventory pixels,
16 colors after dismissal, and the `look room` popup retains scene pixels on
both sides (4 colors left, 12 right). The Wild Bits-only MAME build does not
include the CoCo 3 machine; the reference run used stock MAME and a temporary
ROM directory assembled from the workspace's CoCo ROM files. Artifacts are
under `/private/tmp/coco-kq4-inventory-parity-stockmame-20261105/run`. This
reconfirms the distinct fullscreen Inventory and centered `print` popup
contracts; the state-matched normalized pixel comparison remains open. The CoCo
capture was rerun on 2026-11-07 with the current stock MAME 0.289 binary and the
same original disk pair; it again measured 120,912 white/32,048 black Inventory
pixels, 16 colors after dismissal, and 4/12 scene colors beside the `look room`
popup. Artifacts are under
`/private/tmp/coco-kq4-popup-parity-current-20261107`.
Wild Bits reference run is
`/private/tmp/kq4-look-room-parity-20261030-final`: its Inventory capture also
contains only black and white pixels and a fresh key restores a 13-color scene.
The two MAME captures use different display resolutions and are not a
normalized pixel comparison. The matched-state display comparison remains open
under S04. A later CoCo run swapped disk 2 in MAME,
continued through the opening, and captured the original river-meadow response
at `/private/tmp/coco-kq4-parity-20261030/co-look-after-disk-swap.png`. This
also shows the `look` text in a small white popup while the meadow scene remains
visible. Its room-description text differs from the Wild Bits checkpoint, so
the evidence confirms overlay presentation, not exact message or normalized
pixel parity. The direct CoCo restoration capture above is from the beach-state
run; the matched river-meadow dismissal remains unverified.
An attempted matched 500-frame Right hold followed by `look` produced the CoCo
prompt “What's a look?” in
`/private/tmp/coco-kq4-parity-20261030/co-look-after-disk-swap-moved.png`,
while the no-movement capture showed a room description. This does not match
the Wild Bits river-meadow response and leaves the input/game-state sequence
unresolved; it is not evidence for changing popup rendering.
The CoCo 3 `look room` command does display the room description in a popup in
`co-look-room-after-disk-swap.png`. I changed the KQ4 Wild Bits MAME scenario
to issue `look room` (rather than bare `look`) for its original-resource
comparison. The full opening, 500-frame movement, popup, menu, Inventory and
restoration scenario passes against the current modules with exit status 0;
artifacts are in `/private/tmp/kq4-look-room-parity-20261030-final`.
The follow-up Wild Bits rerun also passed automated popup-region checks;
artifacts are in `/private/tmp/kq4-look-room-acceptance-final-20261030`.
The measured center window contains 2 colors and is 88.4% light, while the
visible scene outside it has 6 colors on the left and 8 on the right. Space
restores the scene after the description. Thus, KQ4 `look room` matches the
CoCo behavior at the display-mode level; a normalized, same-state pixel
comparison remains open under S04.
To rule out a resource-version mismatch, I extracted all volumes from the
three original CoCo KQ4 disks and byte-compared them with the Wild Bits source
files: `vol.0` through `vol.6`, `vol.9` through `vol.11` all match. The CoCo
disk's `logDir`, `picDir`, `viewDir`, `sndDir`, `object`, and `words.tok` also
match byte for byte. The CoCo and Wild Bits `look room` captures nevertheless
show different artwork and text. The runs have not yet been proven to reach
the same room/state, so this comparison does not establish a rendering or
logic defect; S04 remains open pending a state-matched capture.

On 2026-10-30, the KQ4 MAME scenario was rerun against the freshly rebuilt
modules using `tests/check_kq4_mame.py` and passed: the original intro advances
with one Space, Rosella moves, `look` shows the centered popup over the scene,
Inventory shows a full white page, and a key restores the scene. Captures and
the exact MAME command are in
`/private/tmp/kq4-parity-current-20261030`. This confirms the current build's
two separate display paths. It does not identify which action produced the
user's reported white page, nor does it substitute for a matched-state CoCo 3
pixel comparison.

The same focused KQ4 MAME scenario was rerun against the current module files on
2026-10-30 with `tests/check_kq4_mame.py`, using the rebuilt disk and Wild Bits
firmware. It exited 0 and passed single-Space intro advance, gameplay,
movement, centered `look` popup, menu, Inventory and scene restoration. Its
captures are in `/private/tmp/kq4-text-report-followup-20261030`; notably,
`kq4-look.png` shows dialogue over the game scene, `kq4-inventory.png` shows
the separate full white Inventory page, and `kq4-inventory-restored.png`
shows scene restoration after dismissal. Movement JSON records the final
position checks. This reproduces both display modes on the current build; it
does not cover every dialog command or replace the open matched-state CoCo 3
pixel comparison in S04/S06.

Following the user's report of text replacing the graphics, the same automated
current-module MAME run was repeated on 2026-10-30 at
`/private/tmp/kq4-screen-report-rerun-20261030`. It passed its full scenario.
The fresh `kq4-look.png` capture visibly retains the river/meadow outside the
center popup; `kq4-inventory.png` is the separate white Inventory page, and
`kq4-inventory-restored.png` shows the graphics after dismissal. Static
reachability in the original KQ4 resources locates `text.screen` in logics 99
and 102, and `status` in root logic 0; ordinary NPC/room messages use `print`.
The prior white-screen report prompted a source audit, which found and fixed
the incorrect full-plane clear in the shared `text.screen` handler. KQ1 logic
53 and KQ4 logic 99 use that command while graphics are visible. The current
KQ1 king MAME fixture confirms that the handler preserves the throne picture.
The user's exact title/action remains unidentified; the full native target and
a state-matched CoCo/native capture are still outstanding.

After the shared `text.screen` correction, the rebuilt `wbgame` was rerun
through both original-resource MAME checks on 2026-10-30. The KQ1 king-dialog
fixture passed retained throne pixels, the 2,000-frame hold, fresh-key graphics
restoration and exit-memory recovery at
`/private/tmp/wildbits-textscreen-overlay-rerun-20261030`. The KQ4 acceptance
scenario passed its opening Genesta text with title artwork still visible,
movement, centered `look` popup, menu/Inventory and restoration at
`/private/tmp/kq4-textmode-fix-rerun-20261030`. `make -f wildbits.mk budget`
reports `wbgame` 23,778/23,808 bytes, `wbui` 8,089/8,192 and `wbstate`
3,193/8,192. A focused actual-6809 fixture also verified exact 320x240 pixels:
the KQ1 picture remains under occupied text cells, `graphics` clears those
cells, and the mode flag transitions 1→0→1. The complete native target and the
normalized CoCo/native capture comparison remain open.

The KQ4 scenario was tightened on 2026-10-30 to press Right a second time
after the 500-frame walk, because that is the game's stop-toggle. The fresh
run at `/private/tmp/kq4-walk-stop-assertion-20261030` passed: Rosella's
position after stop, after dismissing the centered `look` popup, and after
dismissing Inventory is 239.9 pixels in all three captures. The popup has two
colors with 87.3% light pixels in its measured bounds, while the scene outside
it retains 11 and 13 colors on the left and right. Inventory remains a
black/white full-page text page and a fresh key restores the scene. This
rules out continued camera movement as the cause of the popup comparison drift;
it still does not reproduce an unexpected full-page white screen during an
ordinary conversation.

The KQ3 original-game MAME scenario was also rerun against these current
modules on 2026-10-30 at
`/private/tmp/kq3-current-parity-followup-20261030`; it passed the visible
clock, movement, `look room` popup, save/change/restore pixels and position,
planned exit and unchanged-memory checks. This gives a second current-build
confirmation that ordinary room-description text leaves the Wild Bits scene
visible, but does not exercise every NPC interaction or identify the user's
reported full-page trigger.

`tests/check_wbpic.py` was also rerun on 2026-10-30 and passed its actual-6809
pixel, short-read, mapping-boundary, relocation/error-cleanup, ownership-refusal
and private-visibility-signal checks. This verifies the Wild Bits picture
backend's covered cases alongside the MAME overlay scenario; it is not a
CoCo-vs-Wild Bits normalized picture comparison, so S04 stays open.

The 2026-10-30 full target also passed `check_monitor_profiles` and
`check_monitor_instances` in `check_wbgame.py`. The profile check derives all 16
CoCo RGB entries from the CoCo GIME color codes, compares the generated BGRA
table byte-for-byte, checks the default-to-RGB-to-default toggle, pre-screen
selection, palette-write failure cleanup and unchanged picture indices. The
instance check toggles two separate private maps and verifies each process's
palette choice and shared code/font/stack remain intact. This closes the
palette-conversion and process-isolation subcases; actual CoCo-vs-Wild Bits
scene pixels remain open pending a state-matched capture with the CoCo monitor
mode recorded.

The paired screenshot investigation also identified palette mode as a required
normalization input. CoCo initializes the screen palette from the monitor type
and selects its composite/RGB table using `$0553` (`objs/platform/coco-screen-setup.asm`;
`coco-graphics.asm`). Wild Bits selects its default AGI palette or its CoCo RGB
mapping using the per-process `monitorprofile` (`objs/platform/wildbits-graphics.asm`).
The archived CoCo MAME screenshots do not record `$0553`, so their color
appearance cannot yet be compared to the current Wild Bits profile. The next
paired capture must record the CoCo monitor byte and Wild Bits profile along
with room, picture, ego coordinates and popup state, then normalize resolution
and palette before scoring pixels. This is a capture-protocol requirement, not
evidence of a palette defect.

#### S05 cursor-character checkpoint (2026-11-06)

The actual CoCo `cmd_set_cursor_char` handler was run at two code bases with a
seeded logic message table. It resolves the selected message and stores its
first byte as the cursor character, consumes exactly one operand and returns
with a balanced stack. The loaded Wild Bits screen-backend regression checks
the same valid-message result and invalid-message cleanup. This closes opcode
108 for the exercised cases.

Reproduce with `python3 tests/check_cursor_char.py` and
`python3 tests/check_wbgame.py`.

### S05 text-attribute checkpoint (2026-11-06)

The actual CoCo `cmd_set_text_attribute` handler was run with valid foreground
and background colors at two code bases. It packs each nibble into the CoCo
text-color byte and consumes exactly two operands. The loaded Wild Bits
screen-backend regression executes opcode 109 and checks the same two color
fields, plus its out-of-range rejection. This closes opcode 109 for the tested
valid pair and invalid boundary.

Reproduce with `python3 tests/check_text_attribute.py` and
`python3 tests/check_wbgame.py`.

### S05 string-slot and word-to-string checkpoint (2026-11-06)

`set.string` writes to its zero-based destination slot. `word.to.string` takes
the destination slot first and the one-based parsed-word index second. Wild Bits had read those operands in reverse and did not bound the
copy to the destination slot. The handler now follows the CoCo operand order,
rejects invalid slots and word indexes, copies no more than 39 bytes and writes
a terminator within the 40-byte string slot. `check_string_slots.py` calls both
real handlers at two code bases and checks slots 0 and 11, parsed-word index
handling, empty and boundary cases through 80 bytes, adjacent-slot and variable
preservation, and caller-stack guards. This closes opcodes 114 (`set.string`) and 116 (`word.to.string`) for those
tested bounds; malformed parser state outside its 40-byte input
buffer is not represented as a valid game input.

The integrated `check_wbplay.py` fixture was corrected to use the CoCo operand
order: it writes parsed word 2 into string slot 1 before displaying `%s1`. Its
former `(2,1)` operands encoded the reversed native behavior and made the
integration oracle disagree with the actual CoCo handler. The corrected
loaded-game path passes and confirms the expected `tree` glyphs.

Reproduce with `python3 tests/check_string_slots.py`.

### S05 tokenizer and formatter evidence, 2026-10-19

Six parser/text regressions pass: `check_tokenizer.py` covers all 255 non-NUL
byte values in three positions and delimiter/drop/trim boundaries;
`check_dictionary_lookup.py` checks mapped/streamed lookup, longest phrases,
case folding, ignored words and partial boundaries; `check_string_compare.py`
compares all byte classes and punctuation/length/slot edges through real IF
dispatch; `check_string_slots.py` covers set.string/word.to.string and slot
guards; `check_text_helpers.py` checks bounded copies, decimal input/output and
all byte classes; and `check_decimal_index.py` performs 4,094 calls plus 548
direct formatter comparisons, seven recursion chains, a 2,211-byte output edge,
and original Space Quest II missing/corrupt/truncated-message cases. The test
builds its 16 malformed/unknown escape samples from the 18 all-title findings
(duplicates included) and compares each against the actual CoCo formatter; the
two missing-operand cases also have original-resource boundary tests. Thus the
static anomaly inventory is now tied to runtime comparisons. The test
documents a material remaining difference: Wild Bits rejects formatter depth
above four active frames and caps output at 2,048 bytes, while CoCo follows its
unbounded paths into the caller's memory/resource. S05 remains open until the
depth/output policy is made an explicit accepted platform difference or brought
into parity, and the remaining original message cases and error cleanup are
resolved.

#### S05 string predicate checkpoint (2026-11-06)

`check_string_compare.py` compares CoCo `TestStrings` with the native opcode 15
test dispatcher across all 255 non-NUL byte classes, punctuation policies,
empty/prefix/full-length strings, first and last string slots, invalid native
indexes, and actual loaded IF branches. Both owners agree, and argument/slot
guards plus code relocation are checked. This accepts predicate 15; formatter
and malformed-resource behavior remain open under S05.

#### S05 said predicate checkpoint (2026-11-06)

`check_said.py` compares the actual CoCo `TestSaid` body with the native opcode
14 `InputTest` route through `ParserSaid`. It covers exact and partial matches,
both wildcard forms, little/big-endian word IDs, mismatched/empty/overlong input,
all 256 byte-folding values, disabled-input and already-accepted flags, operand
cursor/guards and one-time acceptance. Both engines match across the test cases.
The separate S05 malformed-resource, formatter-depth/output policy and original
message cases remain open.

#### S05 tokenizer/parser refresh (2026-11-06)

The current worktree reruns `check_wbparser.py` and `check_tokenizer.py`
successfully. The parser covers typed commands, phrase-stream refills, ignored
words, backspace, unknown indexes, wildcard matching, one acceptance per line
and slab cleanup. The tokenizer compares both real owners over all 255
non-NUL bytes in three positions, delimiter/drop/trim rules, empty and maximum
strings, relocation and guard bytes. This refreshes those input cases; S05
remains open for the documented formatter-depth/output policy and unresolved
original-resource messages and malformed-resource cleanup.

The same parser primitives passed again on 2026-11-07: `check_wbparser.py`,
`check_said.py`, `check_tokenizer.py` and `check_text_helpers.py`. The refresh
rechecked tokenization over all 255 non-NUL byte values, shared `said` behavior,
typed/prefix-compressed dictionary parsing, bounded string copies and decimal
conversion at two code bases. It adds regression confidence for these helper
paths but does not settle formatter recursion/output differences or all original
message and malformed-resource cases.

### S06 input, inventory and modal evidence, 2026-10-19

Six focused checks pass, with different scopes: `check_cancel_line.py` exercises
316 Wild Bits cancel/echo helper cases (it does not run a CoCo comparison);
`check_inventory_commands.py` runs all six inventory handlers against both
owners at two load addresses; `check_persistent_window.py` checks native
nonblocking print and character/color/pixel restoration after workspace reuse
and nested modals; `check_game_clock.py` covers 2,048 cycle-flag boundaries, 26
frame-clock cases and 4,118 clock calls; `check_wbparser.py` exercises native
typed commands, refills, backspace and single acceptance; and `check_wbplay.py`
covers loaded fixtures for pause/resume freezing, modal restoration,
input/parser and resource ownership, including original KQ1/Larry/SQ messages.
All pass, but only the explicitly paired command cases count as CoCo/native
equivalence evidence. S06 remains open for the full held/repeated/fresh-key
matrix, stale-key dismissal,
inactive-terminal ownership and room-transition interactions; those require
the real event loop and title checkpoints rather than primitive unit coverage.
The real-driver KQ1 `--sustained` MAME scenario passed on the current modules:
unknown-word response, Pause selected through the actual menu, resume, subsequent
command, scene restoration, interrupt exit and unchanged free memory. Captures
are in `/private/tmp/wildbits-s06-sustained-kq1-current-rerun-20261019`.

#### S06 inventory command-state checkpoint (2026-11-06)

#### S04 text-screen and graphics-mode checkpoint (2026-11-06)

`check_text_graphics_mode.py` runs the actual CoCo `text.screen` and `graphics`
handlers at two code bases. It verifies their mode-page selections, CoCo's text
mode flag, preservation of an 8-KiB picture-memory fixture, display-service
returns and caller-stack guards. The Wild Bits logic matrix in
`check_wbgame.py` checks the corresponding opcodes against exact 320x240
frames: text-screen mode preserves the game picture under changed text cells,
and graphics mode clears those cells while restoring the picture. This closes
opcodes 106/107 for these mode and picture-retention behaviors; other text
colors and full normalized MAME capture comparisons remain open.

#### S04 monitor-toggle checkpoint (2026-11-06)

`check_monitor_command.py` executes the actual CoCo `cmd_toggle_monitor` at two
initial monitor states and captures all 32 `I$Write` palette payloads. Each
write has the expected `ESC`, palette command, color index and value; the
monitor byte toggles in both directions, and code, script pointer and stack
remain intact. The Wild Bits monitor-profile scenarios in `check_wbgame.py`
compare the generated CoCo RGB palette, toggle back to the AGI palette, and
verify picture-index and font preservation plus error cleanup. This closes
opcode 140 for palette selection and profile-local behavior; physical monitor
appearance remains part of the emulator/hardware visual gate.

Reproduce with `python3 tests/check_monitor_command.py` and
`python3 tests/check_wbgame.py`.

#### S04 opcode 110 CoCo-stub checkpoint (2026-11-06)

The public `cmd_shake_screen` body in `mnln.asm` consumes one literal operand
and returns without changing the displayed image. Wild Bits had added a real
frame-buffer shake, which was a behavioral difference despite the common
symbol name. Opcode 110 now uses the ordinary `VmSuccess` route, and its
packed UI-class entry is disabled. `check_logic_executor.py` calls the actual
CoCo target directly to confirm operand consumption, and runs the native
command table with an operand byte that resembles a return opcode before a
following assignment. It checks variable/flag state, stack and code guards at
two code bases. `check_native_dispatch.py` confirms all 256 routes.
The S04 manifest accepts opcode 110 on this command-level evidence. The large
frame-buffer implementation and its four private scratch bytes are removed;
the helper directory keeps a one-instruction compatibility stub at that slot.

#### S04 custom priority-base command checkpoint (2026-11-07)

`check_priority_bands.py` now calls the actual CoCo `SetPriBaseStub` entry,
which installs the table pointer and enters the reference `SetPriBase` routine;
it compares all 168 legal base values and all 168 resulting row priorities.
The native half exercises `AuxPrioritySet` for every legal value, rejects
168..255 without changing the saved base/scale, and checks 4,565 rows and band
heights around every transition. Its loaded overlapping-sprite scenario verifies
that a custom base affects actual draw ordering as expected. This accepts
opcode 174 at the command and visible-priority levels. CoCo's monitor-specific
MMU output remains covered by its existing presentation boundary.

Reproduce with `python3 tests/check_text_graphics_mode.py` and
`python3 tests/check_wbgame.py`.

#### S04 clear-text rectangle checkpoint (2026-11-06)

`check_text_rect.py` compares the actual CoCo `cmd_clear_text_rect` writes with
Wild Bits executing the real `clear.text.rect` script. For the covered ranges,
cell contents, text attributes, row-23 clipping, empty rows beyond the screen,
column-40 spill behavior, operand advancement, cursor/color preservation and
following script execution match. The test separately bounds a CoCo inverted-
row case that does not return; that legacy edge is not represented as equivalent.

Reproduce with `python3 tests/check_text_rect.py`.

#### S06 clear-lines checkpoint (2026-11-06)

The direct CoCo probe added to `check_text_rect.py` invokes the real
`cmd_clear_lines` handler with both color operands. It observes spaces written
to every column in the inclusive requested rows, verifies the color byte maps
to the expected black/white text attribute, and confirms the command consumes
three operands while restoring cursor, current text attribute and stack. The
Wild Bits side is exercised by `check_wbgame.py` on the loaded game: both
boolean colors clear the requested framebuffer band, the scene is preserved
elsewhere, and the resulting pixels persist through the next logic cycle. The
platforms use their native text and graphics representations, but the tested
clear range, color choice and persistence match. This closes opcode 105 for
those tested ranges and colors; other status/input screen commands remain open.

Reproduce with `python3 tests/check_text_rect.py` and
`python3 tests/check_wbgame.py`.

#### S06 input acceptance checkpoint (2026-11-06)

The CoCo direct test invokes `cmd_prevent_input` and `cmd_accept_input` with
their display-service boundary trapped, checking the actual input-acceptance
flag and balanced caller stack across both initial flag values and two module
addresses. The native `check_wbgame.py` screen-backend scenarios execute the
actual `prevent.input` and `accept.input` command bytes and verify the same
private state transitions, including off followed by on. This establishes
input acceptance state; the platforms retain their own rendering of the input
row and cursor.

Reproduce with `python3 tests/check_screen_input.py` and
`python3 tests/check_wbgame.py`.

#### S06 set-key checkpoint (2026-11-07)

`check_set_key.py` invokes actual CoCo `CmdSetKey` and `RemapKeyEvent`, then
Wild Bits `SetKeyCommand` and `GameKeyBinding`. Both owners append repeated
key bindings, select the first matching mapping when the event arrives, and
silently ignore a 51st binding after the fixed 50-entry table is full. The
initial paired test exposed that Wild Bits replaced a duplicate entry and
returned an allocation error at capacity; `SetKeyCommand` now matches CoCo's
append/first-match/full-table behavior. Storage, event/controller result,
operand handling, code immutability and guards pass at two code addresses.

Reproduce with `python3 tests/check_set_key.py` and
`python3 tests/check_wbgame.py`.

#### S06 status-line checkpoint (2026-11-06)

`check_status_line_commands.py` invokes the actual CoCo status-line on/off
handlers at two code bases. It verifies the enable flag, the immediate
`StatusLineWrite` request, and the disable request's selected row and column
before `ClearTextLine`; each call returns with a balanced stack. The loaded
Wild Bits status-line scenarios in `check_wbgame.py` check the visible score
and sound fields, row selection, disabling, and live cycle updates. Together
these cover the command state and tested screen effects; other screen modes and
complete room-by-room parity remain open.

Reproduce with `python3 tests/check_status_line_commands.py` and
`python3 tests/check_wbgame.py`.

The C13 generator records opcodes 112 (`status.line.on`) and 113
(`status.line.off`) against their paired evidence, opcode 136 (`pause`) in
the S07 checkpoint, and opcode 140 (`toggle.monitor`) in the S04 checkpoint.
The earlier 2026-11-06 manifest snapshot recorded 145 of 182 commands with
command-level results, 37 open command rows, and focused results for all 19
predicates. At that checkpoint S04 had two open rows; S06 had 16 open rows,
including `set.key`; and S07 had three open command rows. Later counts are
recorded below.
Reproduce the manifest update with `python3 tests/audit_game_scripts.py
--self-test` and `--all-games`.

#### S06 `set.key` follow-up (2026-11-06)

The actual CoCo `CmdSetKey` stores a two-byte normalized key identifier and
variable number. The Wild Bits input backend stores a three-byte character,
scan and variable tuple, which its keyboard event path matches directly. The
KQ4 all-title audit locates 29 `set.key` commands in logic 101; 27 have a zero
second operand, and two bind character 1 with nonzero second operands 1 and 3.
This confirms the nonzero scan/mask case is used by an original title, but does
not establish how CoCo key normalization maps to the Wild Bits terminal
driver's key-sense bytes. Opcode 121 therefore stays open until an injected
KQ4 key event proves those bindings trigger the same variables on both
platforms. No table-format change is accepted from the handler-only probe.

#### S06 player-control checkpoint (2026-11-06)

The direct comparison in `check_player_control.py` runs the actual CoCo and
Wild Bits handlers for `program.control` and `player.control`. Both restore the
expected input-control flag. The CoCo handler also resets the ego's motion type
to normal on `player.control`; Wild Bits previously only restored its control
flag, leaving an active scripted motion type in the ego record. The native
handler now resets that same field. The test verifies motion and direction
fields, each private-memory guard, and caller stack for both commands. This
closes the two command rows for those state effects; movement completion and
whole-room input behavior remain covered by the separate S03/S06 runtime gates.

Reproduce with `python3 tests/check_player_control.py`.
The rebuilt module also passed the KQ4 MAME movement direction trace and full
intro/movement/look/menu/Inventory restoration scenario documented in
[`WILDBITS-MAME.md`](WILDBITS-MAME.md#2026-11-06-follow-up).

The current rerun of `check_inventory_commands.py` passes all six CoCo and
Wild Bits command handlers: `get`, `get.v`, `drop`, `put`, `put.v` and
`get.room.v`. Across two code bases per owner, the matrix covers item and
variable indexes 0/255 and room values 0/37/128/255, variable-indirect item and
room selection, `get.room.v` aliasing, caller cursor/stack guards, immutable
CoCo inventory names, and preservation of the full native private state. It
also verifies that invalid native item indexes return an error without
mutating private state. These six command rows now carry command-level evidence
in the C13 manifest; this accepts the tested inventory state transitions, not
the inventory screen, menu navigation or broader S06 event-loop behavior.

#### S06 cancel and echo command checkpoint (2026-11-06)

`check_cancel_line.py` now compares the actual CoCo `cmd_cancel_line` and
`cmd_echo_line` bodies with Wild Bits `GameCancelLine` and `GameEchoLine` at two
code bases. Both sides match with input enabled or disabled, for cancel-to-empty
and for merging the previously typed prefix with the remaining history suffix
at lengths through 38 bytes. The CoCo character-output MMU service is stubbed at
its call boundary; its input and command routines execute. The whole input
helper regression passes 392 native and paired command cases. C13 now records
these two command rows as accepted for the tested input-buffer state effects;
prompt rendering, event-queue timing and held/repeated key behavior remain open
under S06.

#### S06 inventory predicate checkpoint (2026-11-06)

The direct CoCo/native calls in `check_inventory_commands.py` compare predicates
9 (`has`) and 10 (`obj.in.room`) at two code bases and two native private bases.
The matrix covers item and variable indexes 0 and 255, room values 0, 37, 128
and 255, expected-room boundaries, exact operand advancement, unchanged
inventory/variables, whole native private-state preservation, stack guards and
native rejection after reducing the loaded inventory count. Both predicates
match in every accepted call. This accepts the possession and room predicates;
the string predicate and broader S06 event-loop behavior remain open.

#### S06 controller predicate checkpoint (2026-11-06)

`check_controller_predicate.py` calls the actual CoCo `TestController` and
native `InputTest` handlers for predicate 12. Its 1,536 calls cover all 256
controller values with false, canonical true and noncanonical nonzero states.
The CoCo side seeds the key-state byte at the 6809 signed accumulator-indexed
address used by `TestController` and `EventLoopKey`; the native side sets the
corresponding private bit. Results match, with operand, cursor, stack, guard and
code checks. This accepts the predicate lookup behavior. Controller event
delivery, per-cycle clearing and inactive-terminal ownership remain part of
the open S06 runtime gate.

#### S06 have.key predicate checkpoint (2026-11-06)

`check_have_key_predicate.py` calls the real CoCo `TestHaveKey` and native
`InputHaveKeyTest` handlers. The CoCo test verifies the pending-key fast path
and six fresh-key return values, including storage in v19 and a normalized
true result. The native handler's pending-key result is checked directly;
`check_wbgame.py` separately exercises its cleared-v19 modal wait, fresh key,
and graphics/input restoration. The focused test passes. This closes predicate
13's handler result; S06 event queue ownership, repeat/clearing rules and
inactive-terminal behavior remain open.

On 2026-10-30 this real-driver scenario exposed stale assertions that incorrectly
required all four ordinary messages to replace the full screen with only black
and white pixels, and checked the Pause glyph at the top-left text origin. The
captures show the intended centered white popup over the colored castle scene.
The assertions now check popup bounds/colors, visible scene pixels on both sides,
the exact response phrases, and Pause glyphs at the default print-window text
origin. The fresh run passed at
`/private/tmp/wildbits-s06-sustained-current-rerun-20261030`: `look room`, an
unknown-word response, Pause selection/resume and a repeated `look room`; all
four popup captures retain the scene. It also verifies later scene recovery,
interrupt exit and unchanged free memory. This corrects the regression oracle
and confirms these ordinary modal paths; stale-key, held/repeated-key and
inactive-terminal input ownership remain open.

The full native game integration suite passed again in the 2026-10-31 standard
target. It covers timed and held print dialogs, fresh-key text-screen
dismissal, original KQ1 help/death/pickup/encounter/ending routes,
room-transition input and sound cleanup, menu/Inventory behavior, and a
text/graphics pixel matrix with `text.screen`, `graphics`, `clear.lines`,
`clear.text.rect`, and picture discard. These Wild Bits checks pass; paired
CoCo event-sequence and inactive-terminal ownership gaps remain open.
The same rebuilt modules passed the real-driver KQ4 MAME run on 2026-10-31:
one-Space intro, movement/camera scroll, centered look popup, menu/Inventory
and scene restoration. The standard regression log is
`/private/tmp/wildbits-two-mover-parity-20261031.log`; all 59 commands pass,
including the new controlled two-mover cycle fixture.
The same KQ4 scenario passed on 2026-11-06 against the modules rebuilt by the
current full check. It verifies one-Space intro advance, camera-scrolling
movement and stop, the original centered `look` popup with 11/13 distinct scene
colors visible at its sides, menu/Inventory dismissal and exact Rosella scene
restoration. Captures and `movement.json` are under
`/private/tmp/wildbits-kq4-current-20261106`. This confirms that ordinary
dialogue does not blank the scene on the current build; the distinct full-screen
`text.screen` behavior and direct normalized CoCo/native capture comparison
remain separate S04 work.

An additional no-repeat-key KQ4 intro trace started the game, sent one Space,
then captured every five seconds through frame 16,800. It shows the throne-room
narration `He flings the battered hat towards his children and his wife, Queen
Valanice, proudly looks on.` at frame 8,100; the scene remains at frame 8,400
with that timed line cleared, and the next hat-animation caption appears by
frame 8,700. Later captures show the original story progressing to Rosella on
the shore without further key input. Captures are under
`/private/tmp/wildbits-kq4-intro-observe-20261106`. This establishes a five-
second sampled hold and automatic progression on Wild Bits; it does not decide
whether CoCo's corresponding original logic uses the same timer. The local MAME
binary only contains the `wbjr2` target, so a CoCo 3 reference capture is still
needed before closing this S06 timing discrepancy.

On 2026-11-02, the rebuilt modules also passed KQ1's original hall-entry
MAME checkpoint: after scripted `stop.motion`/`new.room`, arrow input moved the
ego from screen X=310.5 to X=243.5, and exit restored free memory. Artifacts
are under `/private/tmp/wildbits-kq1-hall-resume-20261102`. This verifies the
reported input-resumption path in MAME, not the full S06 input matrix.

### S07 clock and audio evidence, refreshed 2026-10-29

`check_game_clock.py` (recorded under S06 above) passes 2,048 cycle-flag cases,
26 frame-clock cases and 4,118 clock calls, including pause/reset/error policy.
`check_native_audio.py` passes converted CoCo note/end packets, bounded resource
reads and queue refill during a long modal wait, plus missing/stale helpers,
driver versions, busy/unavailable devices, malformed notes, deep logic calls,
audio completion and ownership cleanup. It now loads original KQ4 resources 2,
100, 101 and 102 from `sndDir`/`vol.*`, decodes their 386 four-byte CoCo note
events, runs each through the actual Wild Bits adapter, and compares every
emitted tone, amplitude, big-endian duration, order and channel-end packet.
`tests/check_kq4_mame.py --audio-trace` independently asserts that the original
KQ4 intro issues those same four sound IDs in that order with completion flags
220, 154, 154 and 154. This ties the resource-level event comparison to the
intro sequence rather than a synthetic-only sound fixture. The optional
`tests/check_kq4_mame.py --audio-trace` run also advances the original KQ4 intro,
observes the four command 99 calls and process-owned PSG register writes
through the post-Space intro capture, with the matched PSGdrv/fPSG modules. The
audio-enabled rerun on 2026-10-30 used
`--audio-trace --audio-wav`; the latter now enables MAME's automatic sound
mixer instead of leaving `-sound none` active. Its stereo 48-kHz WAV contains
varying samples in the post-boot KQ4 intro window (30–281.7 seconds): centered
RMS 51.7 and peak-to-peak 231. The latest run recorded 1,111 owned PSG writes.
Captures and metrics are under
`/private/tmp/kq4-audio-sequence-verified-20261030`; it also records all four
command IDs and completion flags. A prior audio run had 1,157 writes, so the
write count varies with asynchronous scheduling and is not used as the parity
criterion. The WAV check removes the DC offset before deciding whether the
intro has a varying signal, so a constant nonzero silence baseline cannot
pass. Inspection of the local MAME sound path shows `-wavwrite` captures the
speaker mix before MAME's master-volume gain; therefore the WAV verifies
non-silent PSG output but cannot prove that host speakers are audible. A fresh
`--audio-trace --audio-wav` run with MAME `-volume 12` is in
`/private/tmp/kq4-audio-maxgain-20261030`; the WAV remains pre-master, while the
interactive `play.sh` now explicitly enables sound at +12 dB. The note-data
sequence itself matches for these four original resources. S07 remains open
for user-confirmed speaker output, full-scene timing, speed-setting and
modal/device-change comparisons; identical hardware waveforms are not expected
across platforms.

#### S07 clock/audio current rerun (2026-11-06)

The current worktree passes `check_game_clock.py` and `check_native_audio.py`.
The clock run covers 2,048 cycle-flag values, 26 frame-clock cases and 4,118
CoCo/native calls. The audio run matches all 386 note events from original KQ4
sounds 2, 100, 101 and 102, and passes queue refill, busy/unavailable driver,
malformed note, nested-call and ownership checks. This verifies the emitted
sound events and clock logic in the harness; S07 still lacks user-confirmed
speaker output, matched CoCo/Wild Bits timing workloads and agreed performance
thresholds.

#### S07 pause command checkpoint (2026-11-06)

`check_pause_command.py` runs the actual CoCo `cmd_pause` at two code bases. It
checks that queued events are cleared, the clock is paused before the pause
message is shown, and the clock is resumed after the modal returns. The loaded
Wild Bits `check_wbgame.py` scenarios verify that pause blocks until dismissal
and that the game clock does not count the modal wait. This closes opcode 136
for those state and clock effects; device-change and full gameplay timing
comparisons remain open under S07/V04.

Reproduce with `python3 tests/check_pause_command.py`,
`python3 tests/check_game_clock.py` and `python3 tests/check_wbgame.py`.

#### S07 stopsound command checkpoint (2026-11-07)

The actual CoCo command table maps opcode 100 to `NoopCmdsRet`, with zero
operands. Wild Bits had treated the script command as a request to close its
audio helper, which diverged from the CoCo behavior. Opcode 100 now returns
success without stopping active playback. Internal game-exit and clock cleanup
still call the private stop routine directly, so this command fix does not
weaken resource cleanup. `check_logic_executor.py` runs opcode 100 through both
production dispatchers before a following assignment and checks that the next
command executes. `check_native_audio.py` starts a two-note sound, runs opcode
100 while it is playing, and verifies the same complete note/end packet stream
and completion flag as uninterrupted playback. This closes the command-level
row for opcode 100; broader S07 timing, host audio and device-change gates stay
open.

Reproduce with `python3 tests/check_logic_executor.py` and
`python3 tests/check_native_audio.py`.

#### S07 load sound command checkpoint (2026-11-07)

`check_native_audio.py` now executes the actual CoCo `cmd_load_sound` twice
against the same volume record. It verifies both operands are consumed, the
loaded sound node retains the payload pointer and bytes, and the duplicate
request performs no additional volume reads. The Wild Bits fixture runs opcode
98 twice before playback, inspects the native typed cache at the sound command
boundary, and verifies there is one kind-3 entry for that sound. The volume
read count shows the logic record and sound record are each read once, despite
the duplicate load request; playback produces the same note packets. This
closes the command-level behavior for opcode 98. Opcode 99 playback and the
broader S07 timing, host audio and device-change gates remain open.

Reproduce with `python3 tests/check_native_audio.py`.

#### S07 sound command checkpoint (2026-11-07)

The same audio regression now executes the actual CoCo `cmd_sound` and its
blocking `PlaySound` routine at two code bases using a short resident note
stream. It checks completion flag 200, both operand advances and caller-stack
restoration. The Wild Bits loaded-script case for opcode 99 checks the complete
note and end packet stream and that its completion flag is set after playback;
the KQ4 resource checks compare 386 original note events for tone, amplitude,
duration and order. The test harness now recognizes literal OS-9 `F$Time`
service `$16`, which the assembler may omit from the owner map. This closes
opcode 99's sound-resource and command-completion behavior. Platform waveform,
full-scene timing, performance thresholds, host speaker confirmation and
device-change behavior remain open under S07/V04.

Reproduce with `python3 tests/check_native_audio.py`.

### S08 save, restore and restart evidence, 2026-10-19

The full 59-command `make -f wildbits.mk check` target passes on the current
workspace (`sierra/objs` working directory, local emulator loopback enabled).
Its loaded-game coverage includes restart confirmation/cancellation and unwind,
automatic/manual filename selection and persistence after restart, 64 actual
CoCo/native replacement and create-error cases, cold snapshot validation,
partial reads and malformed state rejection, plus continued logic after restore.
Current original-resource MAME checkpoints independently pass KQ1 save/walk/
restore/look, the KQ1 controlled quest-save ending, and KQ3 save/change/restore
with exact position/scene recovery and memory cleanup (see
`WILDBITS-CHECKPOINTS.md`). The 2026-10-30 KQ4 File-menu scenario creates a
valid KQ4-tagged save, changes the scene, restores it, resaves, and continues
into the original `look` logic. The second-save comparison checks invariant
header fields, all saved flags, and every serialized payload byte outside the
256-byte AGI variable array. Those fields match exactly, and the room/ego X/Y
remain `(28, 65, 127)`. Four variables differ between the two save points:
v11, v62, v63 and v133. The current capture does not isolate whether those
changes were caused by logic running after restore or by a restore mismatch;
the 2026-11-06 apply-boundary checkpoint below later resolves that uncertainty.
A live-memory probe at video-frame callbacks was discarded: those callbacks
ran while the CPU's direct-page register was zero, outside the game process, so
the sample did not describe restored game state. The verified scenario was
rerun after removing that invalid probe; captures and the valid `KQ4` save are
under `/private/tmp/kq4-persistence-verified-20261030`. The same run confirms
that KQ4 `look` displays a centered white popup with the scene visible around
it, while Inventory uses an opaque full-page white text display matching the
CoCo 3 reference. S08 remains open
for a full corruption/wrong-game/short-write/
full-disk matrix through the complete user-facing save command, and restart
from every nested/modal execution state; the remaining failure cases are not
all compared against CoCo-observable resumed behavior.

The current KQ4 `--persistence` MAME route passed on 2026-11-06 after the full
integrated rebuild. It saved a 34,745-byte KQ4 state, changed scenes, restored,
and continued through the original river-meadow look dialogue. Room and ego
X/Y matched at `(26, 56, 127)`; all saved flags and non-animation payload bytes
matched. Two active non-ego cycling objects advanced only their cel index,
cel-resource offset, and cycle countdown while the restored game kept running;
the checker allows those named live fields and rejects every other non-variable
payload difference. Variables 11, 62, 63, and 133 changed after restore during
continued original logic. A debugger checkpoint at the state-command return
captured variables 11, 62, 63 and 133 as `(15, 56, 17, 15)`, exactly matching
the saved file. A later checkpoint after resumed logic changed them to
`(44, 48, 19, 43)`, confirming the differences are from continued script
execution rather than a restore mismatch. The restore popup also retained
scene colors on both sides. The apply-boundary rerun is under
`/private/tmp/wildbits-kq4-apply-verified2-20261106`; the broader scenario is
under `/private/tmp/wildbits-kq4-persistence-final-20261106`. This closes the
KQ4 variable apply-boundary question, but not S08: corruption, wrong-game,
short-write/full-disk and nested/modal restart cases remain uncovered against
their CoCo-observable outcomes.

The same KQ4 `--persistence` route passed again with the current build on
2026-11-07. It wrote a 34,745-byte KQ4-tagged file, changed 173,192 displayed
pixels before restore, then restored room/ego coordinates exactly to
`(26, 69, 127)` and continued into the original `look` logic. Saved flags and
non-animation payload bytes matched. The four changing variables matched at
the restore-apply boundary; subsequent changes occurred during resumed script
execution. The post-restore popup retained 11/12 scene colors on its left/right
margins. Artifacts are in
`/private/tmp/wildbits-kq4-persistence-current-20261107`. This rerun does not
close the remaining S08 failure and nested/modal restart matrix.

Two original KQ1 persistence/lifecycle scenarios passed against the same
current modules on 2026-11-06. `--persistence` now selects File: Restore through
the real menu (rather than typing an unsupported `restore game` parser command),
checks the filename prompt, walks Graham, restores the saved position and runs
`look room` with its centered popup over the retained castle scene. The measured
shirt centers were 449.5 before save, 625.5 after walking and 449.5 after
restore. `--restart` verifies menu restart unwinds the root stack, resets the
position, accepts new arrow input and reaches a stable stop before process exit.
Artifacts are under `/private/tmp/wildbits-kq1-persistence-corrected-20261106`
and `/private/tmp/wildbits-kq1-restart-current-verified-20261106`. These close
the KQ1 normal restore and root-menu restart checkpoints only; nested/modal
restart and the invalid/corrupt save matrix remain open under S08.

#### S08 save and restore filename cancellation (2026-11-08)

The two-terminal MAME persistence harness sends Escape after the save and restore
filename editors open, without scheduling a filename for either canceled
prompt. It verifies the scene remains identical through both cancellations and
that canceled save creates no `cancelled` file. The existing `GameLineCancel`
path clears the parser line and length; no change to the save callback was
needed. Save/restore, overwrite, invalid-field-count, wrong-game, bad-CRC,
truncated-state, unsupported-version, declared-length-mismatch and trailing-byte
cases continue afterward and pass. The run used the compatible Wild Bits Jr2
image and current MAME fork; artifacts are in
`/private/tmp/wildbits-state-headers-20261108-r3`. Reproduce with
`python3 tests/check_wbpic_mame.py --native-game kingsquest1 --interpreter
--persistence` and the compatible MAME/disk paths in `WILDBITS-MAME.md`.
An earlier `make -f wildbits.mk check` run completed successfully. After
restoring the save callback's carry propagation, the focused
`check_wbstate_transfer.py`, full `check_wbgame.py` and MAME persistence runs
also pass with the final UI module.
`wbgame` is 23,801/23,808 resident code bytes. Command 125 remains open for
the CoCo-observable save-failure comparison and remaining S08 state matrix.

The new `--full-disk` MAME mode fills the disposable OS-9 disk until only 6 KB
remain, attempts a 34,745-byte save, and checks the visible `Error` modal over
the unchanged scene. Dismissing the modal restores the exact pre-save pixels;
the failed file is absent, and the game returns to the shell. This passes with
the actual Wild Bits drivers in `/private/tmp/wildbits-full-disk-20261108-r4`.
`check_wbstate_transfer.py` separately verifies `E$Full` propagation and
incomplete-file cleanup. These close the native full-disk save and dismissal
cases only; equivalent CoCo failure behavior, other write failures and the
remaining S08 state matrix are still open.

#### S08 `set.game.id` command checkpoint (2026-11-07)

`tests/check_game_id.py` invokes CoCo `cmd_set_game_id` and runs the real loaded
Wild Bits opcode 143 against equivalent logic messages. Seven values cover an
empty message, short identifiers, exactly seven characters, truncation beyond
seven characters, and high-bit bytes. Both produce the same NUL-terminated
eight-byte identifier; the CoCo side also checks the operand cursor, stack
guard and immutable module at two code addresses. This closes the command's
message-copy semantics only. Save-file ownership, wrong-game restore rejection
and the broader S08 persistence/failure matrix remain open.

Evidence for C01: `check_priority_view.py` executes the actual CoCo control
body and nibble swap, compares all combined byte values, and verifies visible
native priority pixels, fresh Enter/Escape dismissal, ignored ordinary keys,
repeated cached calls, preserved gameplay/combined buffers, first-picture setup
and show/restore/unmap failures. `check_priority_mame.py` verifies physical
Escape (native byte 5), Enter, repeated views, two terminals, foreground
retention, unchanged save bytes, no remaining game process and exact memory
recovery after cleanup. Install matching ABI-7 modules. Reference/platform
mapping, negative tests, budgets and artifact paths are recorded in
[engine validation](WILDBITS-ENGINE.md#priority-diagnostic-arithmetic-edges-and-common-text-plane-copy).
S06's other modal/menu/input combinations remain open.

### C08-C12 CoCo stub decisions

For opcodes 127, 155, 163, 164, 173, 176, 178 and 181, preserve the actual
CoCo `NoopCmdsRet` behavior. Opcodes 144 and 175 preserve CoCo's
`cmd_shake_screen` stub; 179 and 180 preserve their respective CoCo stubs.
Native `VmSuccess` is therefore intentional only for these twelve entries.
Each still consumes the operands specified by its catalog and continues at the
next instruction. Do not add PC AGI behavior that the CoCo engine omits.

Evidence for C08–C12: `check_logic_executor.py` executes 51 controlled scripts
in both actual interpreters at two load addresses (204 executions). Tests use
return/branch/condition-looking operands, execute a following assignment, and
compare the entire variable and flag sets plus stack, cursor guards and immutable
initialized code. The new cases fail on the old native unsupported routes and
pass after the correction (`/tmp/sierra-parity-stub-baseline.log`,
`/tmp/sierra-parity-stubs.log`). Opcode 155's two ignored operands also match the
actual CoCo body; no additional platform exception is needed for that stub.
The latest cases execute bytes decoded from original Manhunter I logic 159:
the exact condition bytes `FF 02 5F 20 FF 08 00` and alternate entry
`FE C3 00` / `08 00 84`. The resource-derived jump, true branch and false
branch produce matching variables and normalized cursors in both real
interpreters at two code bases. This closes the overlap-specific runtime check.
The replay log/checkpoint comparison is a separate scoped result; actual
resource-loader replay, nested resource use and load/map/read failure
restoration remain open under S02.
Native audio
regressions verify that opcode 175 during active playback retains the exact
converted note/end packet sequence, completion flags and balanced ownership
(`/tmp/sierra-parity-audio-fixed.log`). Broader audio/driver equivalence remains
under S07/V04.

Reference sources: [command catalog](objs/shared/agi-command-table.asm),
[CoCo engine](objs/mnln.asm), [dispatch contract](tests/check_native_dispatch.py).
The four stub routes above are four compatibility gaps, not four missing game
features. Debug features remain part of strict CoCo parity even if normal play
rarely reaches them.

## 2. Verify semantics behind existing routes

For each gate, execute identical controlled scripts/resources on actual assembled
CoCo and Wild Bits code. Compare logical state and normalized output at defined
checkpoints. Compare errors, instruction advancement and cleanup as well as
successful output. Platform services may be simulated for focused CPU tests;
retain separate real-driver acceptance.

- [ ] **S01 — VM and predicates:** Arithmetic/wrap/division, indirection, flags,
  branch/said bounds, literal/variable operands, nested calls, scan starts,
  random range behavior and malformed scripts. Control random inputs rather
  than requiring different platform generators to produce identical sequences.
- [ ] **S02 — Resources and replay:** Plain/LZW loading, cache replacement,
  discard/reload, replay checkpoints, nested resource use, truncation/read/map
  failures and restoration of caller context. Manhunter I logic 159's bytecode
  overlap is classified above; execute this original resource through both
  engines before claiming its resource semantics verified.
- [ ] **S03 — Objects and motion:** Baselines/loops/cels, animation, follow,
  wander, move-to, blocking/terrain/horizon, collisions, fixed/automatic priority,
  visibility flags, stop/start/update and room-edge transitions. Test overlapping
  moving objects, not just isolated sprites.
- [ ] **S04 — Pictures and presentation:** Drawing/erase/redraw, fill and pen
  geometry, mirrored/clipped cels, static additions, priority/control masks,
  custom bands, palette changes, text/graphics switching and scene restoration.
  Normalize palette indices and platform resolution before pixel comparison.
- [ ] **S05 — Parser and formatter:** Tokenization, synonyms/unknown words,
  controllers and strings; all supported substitutions and nested combinations.
  Resolve the remaining original-resource message cases, zero/missing message
  policy, recursion/output bounds and malformed-resource behavior against CoCo.
  Match return/error and caller context, not merely visible happy-path text.
- [ ] **S06 — Input and modal UI:** Held/repeated/fresh keys, arrows after room
  transitions, king conversation, menus, inventory, input prompts, pause and
  dialogs. Compare timer expiration and dismissal rules; stale input must not
  dismiss newly displayed text. Include inactive-terminal input ownership.
- [ ] **S07 — Clock and audio:** Speed settings, step/cycle timing, pause/modal
  behavior, end flags, sound enable/disable/stop, queue refill, busy/unavailable
  devices and scene changes. Compare logical note/event sequences; hardware
  waveforms need a documented platform mapping, not identical samples.
- [ ] **S08 — Persistence and restart:** Preserve every gameplay-visible field,
  resource recipe, text/menu/input state, custom priority, and continued script
  behavior. Cover fresh/warm restore, repeated save/restore, cancellation,
  corruption, wrong game, short writes, full disk and restart from nested/modal
  execution. Native/CoCo save files need not be byte-compatible; document that
  boundary and compare resumed state/behavior instead.

Existing focused tests cover portions of every family. Closing a family requires
an explicit comparison report identifying covered boundaries and remaining
exceptions; a native-only regression cannot by itself prove CoCo equivalence.

#### S01 unsigned comparison and packed-flag predicates (2026-11-06)

`tests/check_coco_conditions.py` now calls the actual CoCo and Wild Bits
handlers for predicate opcodes 1–8. Its 1,728 calls cover equality, unsigned
less-than/greater-than with literal and variable operands, variables 0 and 255,
and `isset`/`isset.v` for every flag number 0–255. Each call checks the Boolean
result, exact operand cursor, unchanged variable/flag tables, balanced stack,
guards and code bytes. All calls pass at the two loaded code bases. This accepts
predicates 1–8. Results for the other predicate families are recorded under
their own gates; the remaining S01 command and malformed-script cases remain
open.

#### S01 arithmetic, random and executor refresh (2026-11-06)

The current worktree passes `check_math_commands.py` (4,544 actual CoCo/native
calls), `check_random_command.py` (all 256 controlled generator bytes over
eleven ranges), `check_condition_flow.py` (all 16 mixed AND/OR/NOT combinations),
and `check_logic_executor.py` (54 controlled scripts through both owners at two
code bases). The executor covers indirect variables, nested calls, scan
markers, branches, original Manhunter I logic-159 alternate entries, bounded
truncation behavior and return/frame guards. `check_have_key_predicate.py`
adds fresh-key, zero-event and `$FF` no-key retry cases; the full
`check_wbgame.py` integration matrix passes the native modal wait and game
routes. These runs strengthen the semantic evidence but do not close S01:
malformed-script behavior and remaining bytecode/error-boundary differences
still need explicit policy and coverage.

These command-level checks passed again on 2026-11-07. The refresh reran the
4,544 math calls, the controlled random ranges, 1,728 actual condition
comparisons, all 19 relocated predicate-table entries, all 16 short-circuit
condition combinations, and dispatch at both load addresses (364 UI selections
and 1,024 native platform dispatches). This confirms those focused boundaries
on the current worktree; the malformed-script and remaining S01 gaps listed
above stay open.

### S01 paired VM checkpoint, refreshed 2026-10-30

Six actual-6809 comparisons were rerun from the current source on 2026-10-30:
`check_coco_conditions.py` verifies all 19 relocated CoCo predicate-table
addresses and shared unsigned/packed-flag conditions at two bases;
`check_condition_flow.py` compares all 16 mixed AND/OR/NOT combinations,
short-circuit callback order, branch targets, cursor and stack state;
`check_math_commands.py` compares 4,544 calls, including every byte dividend,
boundary products/quotients, zero divisors, variable indexes 0/255 and
aliasing; `check_random_command.py` substitutes all 256 source bytes across
eleven inclusive, singleton and wrapping ranges at two module bases;
`check_said.py` covers ASCII folding, endian IDs, both wildcards, mismatch and
length edges, input gating and cursor guards; and `check_logic_executor.py`
runs 54 controlled scripts through both real owners at two load bases, covering
indirect variables, nested calls, scan markers, flags, branches, mixed
conditions, original Manhunter I logic 159 overlap entries, return guards and
truncated literal/variable commands. All six pass.

#### Increment and decrement paired executor case (2026-11-06)

`check_logic_executor.py` now assigns `v0=7`, executes increment, copies the
result to `v250`, executes decrement, and copies that result to `v251`. CoCo
and Wild Bits both produce `(v0,v250,v251)=(7,8,7)` at both code bases, while
the harness also verifies complete variable/flag state, cursor guards, stack
balance and immutable initialized code. The focused test passes with 54 scripts.
This closes the manifest's opcode 1/2 paired-case evidence; remaining arithmetic
routes and the broader S01 malformed-script/command matrix remain open.

#### Immediate and variable arithmetic executor case (2026-11-06)

`check_logic_executor.py` also runs a paired script exercising opcodes 3–8:
assign immediate, add immediate, assign from another variable, add from another
variable, subtract immediate and subtract another variable. It records each
intermediate result, including byte wraparound, and compares all 256 variables
and flags through the full executor at two code bases. CoCo and Wild Bits match
the checkpoints `(v0,v250,v251,v252,v253)=(249,4,11,252,249)`. This accepts
these paired boundary values only; exhaustive arithmetic vectors remain open.

#### Multiply and divide handler boundaries (2026-11-06)

The already maintained `check_math_commands.py` test invokes the actual CoCo and
Wild Bits handlers for opcodes 165–168 at two code bases. It checks every byte
dividend against byte multiplication or unsigned division, edge products and
quotients, zero divisors (result 255), variable indexes 0 and 255, aliasing,
stack/operand/table guards and unchanged code. Both owners match the expected
results in 4,544 calls. This accepts only opcodes 165–168; malformed scripts
and the rest of S01 remain open.

#### Random handler range boundaries (2026-11-06)

`check_random_command.py` calls the actual CoCo and Wild Bits random handlers
with all 256 possible generator bytes across eleven inclusive, singleton and
wrapping ranges, at two code bases. It verifies the resulting variable, operand
cursor, stack and guards. The test substitutes the generator byte at the real
seed routine boundary, so it verifies range mapping but not seed initialization
or long-term sequence quality. This accepts opcode 130's tested range behavior
only; those other random semantics and the rest of S01 remain open.

#### Indirect variable command case (2026-11-06)

The complete-script case in `check_logic_executor.py` exercises opcodes 9–11
through both real command dispatchers: indirect assignment from a variable,
reading through a variable-held index, and indirect assignment from a literal.
It points index variables at both edge slots, 0 and 255, and reads the values
back through later commands. Both owners match the expected complete variable
state and flags at two code bases, with cursor, stack, guard and code immutability
checks. This accepts only those indexed cases; other indirect semantics and the
rest of S01 remain open.

#### Flag command executor case (2026-11-06)

The paired full-executor script exercises opcodes 12–17: literal set, reset and
toggle, then their variable-selected forms. It chooses distinct flag numbers so
each operation's state remains visible, including reset of a flag first set by
the script. CoCo and Wild Bits match the complete flag and variable state at two
code bases, with cursor, stack, guard and immutability checks. This accepts the
listed set/reset/toggle transitions only; edge flag IDs and the broader S01
matrix remain open.

#### Scan marker handler case (2026-11-06)

`check_logic_executor.py` invokes the real CoCo set/reset scan-start handlers
and Wild Bits per-logic cache handlers for opcodes 145–146. It sets and restores
the marker in two distinct logic slots, then verifies that the other slot's
marker stays unchanged. The handlers match at two code bases and preserve stack
balance. This establishes marker operations and slot isolation only; full
command-stream scan behavior remains open.

S01 remains open for malformed-script acceptance. For six truncated commands,
the paired executor test records CoCo consuming bytes after its declared logic
end (including the controlled following value) while Wild Bits rejects the
same bounded fetch with EOF and leaves the destination unchanged. This is a
verified safety difference rather than matching behavior. The current policy
is to retain Wild Bits' bounded EOF behavior: the legacy CoCo logic slot has no
declared script-end field, so imposing this check there would require changing
its loader/slot ABI rather than merely sharing a fetch routine. Treat this as a
documented compatibility exception, not proof of equivalence. The tests also do
not exhaust every invalid branch/said/resource bound in a full loaded-resource
run. The passing focused tests establish their listed boundaries only; they do
not close S01 by themselves.

#### Script terminator executor case (2026-11-06)

Opcode zero is the executor's script terminator, not a dispatched gameplay
command. `check_logic_executor.py` runs a zero-terminated script through both
real owners and checks the matching return, normalized cursor, stack, complete
variables/flags and code bounds at two code bases. The test accepts this return
case only; malformed terminators and the rest of S01 remain open.

### S02 original overlapping-resource checkpoint, refreshed 2026-10-30

`check_logic_executor.py` reads Manhunter I logic 159 from the bundled `logDir`
and `vol.*`, expands the actual LZW payload, checks its declared 464-byte logic
body and the original jump/IF bytes, then runs the relevant original entry
paths through both real executors at two code bases. The test controls only the
variables and the terminator after each selected path so execution stops after
the overlap operation; it does not rewrite the overlapping instructions.
Current test output includes the jump-to-`subv` path and both IF outcomes, with
matching variable state and normalized cursors. This verifies the original
overlap decoding through both dispatchers, not the complete 464-byte resource
or its disk-load lifecycle. The paired view lifecycle test now verifies cache
slot reuse and CoCo linked-list preservation with eight resident views. The
KQ1 quest-save MAME run below exercises replay through runtime restore. S02
therefore remains open for full original resource execution, nested-resource
boundaries, and paired resource allocation/map/read failures beyond the tested
truncated LZW stream.

#### Paired original-volume loader check, refreshed 2026-11-06

`python3 tests/check_coco_volume_load.py` passed against the current source. It
assembles CoCo `mnln.asm` and runs actual 6809 `FindVol` beside native `wbasset`
for original King's Quest I logic 0: both load and expand the bundled 5,941-byte
LZW payload to the same 8,950 bytes at two code bases each. The paired check
also feeds each loader a synthetic uncompressed volume record containing those
same expanded bytes and verifies direct-read output. A volume truncated 64
bytes into the compressed payload reaches CoCo's user-facing read-error path
and returns a null resource; Wild Bits rejects it without returning payload.
An injected OS-9 read-service error on the second volume read likewise makes
CoCo prompt and return null while native `wbasset` returns an error and cleans
up its partial owned allocation. The harness enforces native ownership cleanup
on exit. This covers one actual original resource and specific loader error
paths; it does not test a complete logic execution, nested load/replacement,
or paired allocation/map/unmap failures, so S02 stays open.

#### Integrated regression run, 2026-11-06

`make -f wildbits.mk check` completed successfully from `objs/`. It rebuilt the
native modules (`wbgame` 23,750/23,808 bytes, `wbui` 8,089/8,192,
`wbstate` 3,193/8,192) and ran the full configured CPU/reference suite through
the final `check_wbpic.py` actual-pixel and ownership check. This includes the
paired loader result above, the 51-script real-owner executor, replay/resource
checks, original KQ1/KQ3 scenarios and 443 packed-picture comparisons.
`check_wbexec.py` also runs a standalone interpreter probe over original KQ1
logic and deliberately stops at opcode 24 (`load.pic`), because that probe has
no game graphics backend. The game module routes this command to
`GameLoadPicture`; the probe's explicit unsupported-platform result is not
evidence that `wbgame` startup stops there. The integrated target is regression
evidence for the implemented and exercised behavior, not completion of S01–S08
or the whole-game parity checklist.

#### S02 resource lifecycle and replay refresh (refreshed 2026-11-07)

The current worktree also passes `check_resource_lifetime.py` (30 actual
discard calls), `check_resource_format.py` (9,184 actual directory/header
decodes), `check_view_cache_reload.py` (eight resident views, discard/reuse and
reload), and `check_replay_differential.py` (matching CoCo/native replay records
and checkpoint restoration after overwriting the discarded tail). These
refresh the listed boundaries; paired full-resource execution and all loader
failure combinations remain open under S02.

On 2026-11-07, `check_resource_lifetime.py`, `check_view_cache_reload.py` and
`check_wbres.py` passed again. The first checks head/middle/tail unlinking and
native typed-cache release at two code bases; the second compares public
literal/variable view load/discard, eight-view retention, reload and view/loop/cel
selection; the third covers native 6809 reads, relocated code/data, 20-bit seeks,
volume boundaries, short reads/writes, malformed resources and cleanup. These
results refresh resource ownership and cache behavior, but do not close paired
full-resource execution or every disk/map failure combination.

#### S02 public view resource commands (2026-11-06)

`check_view_cache_reload.py` now drives CoCo's public literal and variable
`load.view`/`discard.view` entries, and Wild Bits bytecode opcodes 30, 31, 32
and 153. Both load the original view resource, fill the resident set,
discard/reload view 0, and reuse a released slot for view 8. The test verifies
CoCo's linked-list state, Wild Bits cache reuse, decoded resource path, operand
advancement and guards, then compares view/loop/cel selection. This accepts
only those four command forms; logic loading/calling and broader
resource-failure cases remain open under S02.

#### S02 replay checkpoint commands (2026-11-06)

`check_replay_differential.py` also covers CoCo `cmd.push.script` and
`cmd.pop.script` against Wild Bits' `ReplaySaveCheckpoint` and `ReplayRestore`
implementations. At two code addresses, both engines save and restore the
replay write boundary, discard the same tail record, overwrite it with the
next record, and produce identical bytes when replayed. Buffer/count guards
and stack balance are checked. The same test compares `cmd.script.size` with
`ReplayInitialize` for limits 0, 1, 3 and 255, verifying reset counters,
checkpoint, write boundary, preserved buffer and CoCo operand consumption.
This accepts opcodes 142, 171 and 172; logic load/call transitions remain open
under S02.

#### S02 nested logic call commands (2026-11-06)

`check_logic_executor.py` runs a controlled four-logic graph through the actual
CoCo and Wild Bits command tables. It exercises literal `call` (opcode 22),
variable `call.v` (opcode 23), nested variable calls, and caller instructions
after each return. The CoCo side starts with the preloaded logic slots; the
Wild Bits side resolves the same child resources through its native resource
pointer service. Both sides produce identical child-variable effects and
caller continuations, return at the expected root cursor, restore call depth,
preserve stack sentinels and stay within script guards at two code bases. This
accepts call and call.v semantics. `load.logics` and `load.logics.v` (20/21)
remain open because the current cross-engine fixture does not yet compare their
public loader-state effects.

#### S02 room transition and logic-load boundaries (2026-11-06)

The room transition APIs have different timing contracts: CoCo's
`cmd_new_room`/`cmd_new_room_v` run `NewRoomSetup` during the command, while
Wild Bits records a request and applies it after the current logic stack
unwinds. `check_room_entry.py` verifies the shared entry-coordinate and room
variable publication helpers across both owners (all request bytes and entry
boundaries), but does not invoke either public command or prove whole-room
equivalence. The later `check_room_commands.py` checkpoint compares the public
commands through room-entry setup, including a zero room number, but still
stubs actual resource I/O and destination logic. Opcodes 18/19 stay open until
destination execution, room-zero logic, post-transition continuation and
cleanup are compared. A separate nested-script case now proves Wild Bits
unwinds its pre-transition call stack when a room request is pending. The
manifest records this timing difference so a successful route or partial
helper test cannot be mistaken for parity.

The same distinction applies to `load.logics`/`load.logics.v` (20/21): their
routes exist, but the paired executor fixture tests resource loading through
`call` and `call.v`, not the public preloading commands. A focused test still
needs to compare duplicate loads, fresh resource reads, resource failure and
replay effects before the complete command behavior can be accepted.

#### S02 public room-command timing probe (2026-11-07)

`check_room_commands.py` calls the public literal and variable room-change
handlers in both production owners at two code addresses. The room number is
decoded correctly in all eight cases. CoCo immediately enters `NewRoomSetup`
from the command; Wild Bits sets the same `vmnewroom` value and pending flag,
then applies the transition after the active logic stack unwinds. The test
also runs both actual 64-object room-reset loops with identical initialized
records. All 2,752 object bytes match after reset, including animation flags,
motion/cycle state, cel/rate values and preserved bits; stack and surrounding
guards remain intact. It checks the command stack, operand source, request
bytes, private-state guard and code immutability. This confirms the timing
difference described above and proves the shared object-reset portion matches;
it does not compare completed resource teardown/setup, room-zero execution,
destination logic, or caller continuation. Opcodes 18/19 remain open until
those observable post-transition states are compared.

Reproduce with `python3 tests/check_room_commands.py`.

#### S02 completed room-entry setup comparison (2026-11-07)

The same test now advances both public commands through the room-entry setup
instead of stopping at the request boundary. For ordinary and zero literal and
variable room numbers, it runs all four border entries and compares the
resulting room variables, every byte of the 64 object records, ego placement,
input/control flags, horizon, replay reset, pending-request state and saved root
instruction offset. On Wild Bits it starts with the root logic in cache slot
zero and a populated non-root slot; the real transition loop releases that slot, clears
its used byte, leaves the root slot intact, unmaps the active asset and invokes
the destination-logic loader once with the requested room number. The CoCo
resource and presentation services and the Wild Bits resource release/unmap
and logic-load boundaries are counted successful stubs so the test can compare
the state machine without depending on disk contents. Stack, code, private
state and object guards also pass.

This closes the paired room-entry reset/setup comparison. A paired synthetic
runtime fixture now runs the same destination and root scripts on both owners.
CoCo's room-logic loader boundary installs the room in its real logic table;
Wild Bits' room loader boundary installs it in the private resource cache. The
real CoCo `ExecLogicScript` and Wild Bits `VmRunRoot` then perform the cache/list
lookup, run destination logic that writes v249=`$77`, resume the root script
which writes v250=`$66`, and return with the same two bytes. Wild Bits also
completes its cycle exit. A second paired case requests room zero: both actual
executors run resident logic zero and produce the same two variable writes.
This verifies destination execution, room-zero execution through the resident
root resource, and post-transition root behavior with controlled scripts. It
does not prove real disk resource loading or real failed-volume error handling;
those cases remain required before S02 opcodes 18/19 can be accepted. Reproduce with
`python3 tests/check_room_commands.py`.

The current-worktree rerun on 2026-11-07 passes the paired room-command cases:
completed setup across ordinary/zero requests and four borders, nested safe
point unwind, nonzero destination/root script effects, room-zero resident-root
execution, and the public literal/variable handlers. The injected native
destination-load failure now starts at the real root VM safe point, executes
the public `new.room` command, reaches production `ApplyRoomChange`, and
propagates `E$PNNF` through `VmNativeReturn`; pending request and stack/private/
code guards are verified. The CoCo volume I/O test additionally runs the real
`OpenVolFile` caller: after a seek failure and an Enter result it calls
`SetLogicPage`, retries `FindVol`, and returns the second resource to its
caller. The second resource success is controlled at the `FindVol` boundary.
The focused test passes, while matching the full CoCo retry/dialog behavior in
Wild Bits remains open.

The missing-room checks now compare the user-visible text directly as well as
checking each backend path: CoCo's real `FetchLogic` formats the error and sends
it to `message_box`, while Wild Bits' real `ResourceLocate` reaches the `wbui`
formatter and its print-text callback. Both produce exactly `Logics #58 not
found.`. The native load path also closes `logDir`, releases the failed asset,
retains the pending room request and root cache entry, and returns `E$PNNF`.
This does not close the transition failure comparison: CoCo's quit path and
Wild Bits' modal dismissal/caller continuation are still exercised separately,
and paired read/seek/close error semantics remain open. Reproduce the paired
message assertion with `python3 tests/check_room_commands.py`.

#### S02 room-load failure through each production caller (2026-11-07)

`check_room_commands.py` now starts the native failure case at `VmRunRoot`,
executes the actual root bytecode `new.room 58`, applies the queued transition,
injects `E$PNNF` only at the destination `VmLoadLogic` boundary, and continues
through the real `VmNativeReturn` cleanup. Wild Bits returns `E$PNNF` with carry
set to its caller, retains the pending room request, and releases the old room
cache entry; all stack, private-state and code guards pass.

The CoCo volume-I/O probe also runs the actual `OpenVolFile` caller around
`FindVol`. For an injected volume seek error, the real `ErrorDialog` Enter
result returns null from `FindVol`; `OpenVolFile` then calls `SetLogicPage`,
retries `FindVol`, reads the second attempt's actual seven-byte volume header
and eight-byte resource payload, and returns that resource to its caller. Only
the file-service results and bytes are controlled. The separate seek/read
probe checks CTRL-BREAK's MMU quit request. Both focused test paths pass.

These results confirmed an observable error-policy difference: CoCo offers
retry/quit and its room loader retries after Enter, while Wild Bits previously
returned the load error without a corresponding system-error dialog. A native
room-load event now uses the existing `wbui` callback path: non-missing I/O
errors display an Enter-retry/Escape-quit prompt, Enter retries the destination
logic resource, Escape sets the game quit state, and `E$PNNF` keeps the existing
missing-logic message and error return. The game checks the quit state before
running another logic cycle. `check_room_commands.py` now invokes the actual
`wbui` event handler, captures the prompt text, and verifies Enter, a failed
retry followed by another prompt, and Escape cleanup. Its ShowCallbacks loader
returns scripted success/error results, so it verifies the UI and retry control
flow. The volume failure fixture also fails the first production volume
seek or read once, selects Enter at the room-error boundary, and executes a
second real `VmLoadResource` through `ResourceLocate`, `LoadAsset`, and the OS-9
open/seek/read hooks. Both cases read the second volume attempt successfully,
populate the destination cache entry, clear the pending transition, close all
paths and preserve stack/private/code guards. The asset-pointer mapping and OS-9
allocation result are controlled by the fixture. `make -f wildbits.mk
wbgame wbui budget` passes with `wbgame` at 23,803/23,808 and `wbui` at
7,565/8,192 bytes; `python3 tests/check_room_commands.py` passes. Both owners
now complete an actual second volume read after an Enter retry, though the
native room-error UI and file-loader retry are exercised in composable fixtures
rather than one terminal-level run. At this point only the narrow second-read
gap is closed; the full S02 room/resource matrix remains open.

Reproduce with `python3 tests/check_room_commands.py`.

#### S02 room-command transition and failure checkpoint (2026-11-07)

The paired `check_room_commands.py` scenarios now cover the observable contract
for public opcodes 18 (`new.room`) and 19 (`new.room.v`): ordinary and zero room
requests, four entry borders, room setup state, safe-point unwinding, destination
logic, root continuation, room-zero execution, missing-resource failure, and
volume seek/read failures. After an injected first-attempt volume seek or read
failure, both owners perform a successful second read through their production
loaders. The Wild Bits UI handler separately verifies the real retry prompt,
Enter retry, repeated prompt after another failure, and Escape quit cleanup.

CoCo applies the room synchronously inside the command, while Wild Bits queues
it until the current logic stack unwinds. The error keys and final actions also
have platform-specific mappings (CoCo Enter/CTRL-BREAK; Wild Bits Enter/Escape).
The fixtures compare resulting room, script, caller, and cleanup effects; they
do not claim identical presentation timing or one integrated terminal UI run.
The command manifest accepts these two opcodes at command-evidence level with
those differences recorded. The S02 family remains open for other resource,
replay, cache, and malformed-input cases in its checklist.

The focused build and `python3 tests/check_room_commands.py` pass in this
worktree. Reproduce with `python3 tests/check_room_commands.py`.

#### S02 Wild Bits room-directory I/O cleanup checkpoint (2026-11-07)

`check_room_commands.py` now injects OS-9 `E$EOF` at the production
`ResourceLocate` seek, exact-read, and close calls while `ApplyRoomChange`
loads a destination logic. Seek/read errors propagate with the original error
code, preserve the pending room request and root cache entry, balance the
stack, and close the directory handle. A partial exact-read case returns one
byte successfully, fails the next read, and verifies the retained partial
progress is discarded safely while cleanup still closes the handle. The close
case starts from a valid directory entry, fails its first close, and verifies
the production error
path retries the close successfully before returning the original error.
All four injected cases preserve private-state and code guards. These cover
Wild Bits' directory-file cleanup; the later volume-file comparison is recorded
below. Reproduce with `python3 tests/check_room_commands.py`.

#### S02 room-volume seek/read error and retry comparison (2026-11-07)

`check_room_commands.py` now calls CoCo's actual `FindVol`, `SeekFile`, and
`ReadFile` code with an open volume handle. It injects OS-9 `E$EOF` at the
volume seek and seven-byte header read, lets the real `OsErrorHandler` store
the error, and exercises both real `ErrorDialog` return choices. Enter/try
again returns a null resource pointer to the caller with `$009F` equal to
`E$EOF`; CTRL-BREAK sets the quit function code and reaches the real MMU exit
entry. Both preserve the open CoCo volume handle and the caller's stack marker.
The paired Wild Bits cases run production `ApplyRoomChange`, `VmLoadLogic`,
`LoadAsset`, and `ResourceLocate`; they inject `E$EOF` at the volume-file
seek/read and close the failed volume path. The Escape-selection fixture
verifies game-quit state, cleared pending room request, root cache, stack,
private-state and code guards. The retry variants fail the first volume seek
or read, select Enter at the room-error callback boundary, and run a second
production `VmLoadResource` through the actual directory lookup, volume seek,
header read and payload read. Both retries succeed, publish the destination
cache entry and close the volume/directory paths. The asset pointer and OS-9
allocation result are controlled.

This establishes the loader-level error outcomes, both retry branches, and
CoCo's nonreturning exit request. The CoCo and Wild Bits system-error dialog
tests still compose the real error handlers, loader calls and key choices in
separate fixtures; an interactive full-game comparison of prompt layout,
second-read outcome and post-transition state remains open. S02 opcodes 18/19
are not closed.
Reproduce with `python3 tests/check_room_commands.py`.

The integrated native `check_room_controls` and `check_room_input_sound`
scenarios in `check_wbgame.py` complement that paired synthetic fixture: they
start the real `wbgame` owner with virtual `/game/logDir`, `/game/vol.0`, and
`/game/sndDir` files, transition from root logic to destination logic through
the production resource loader, and execute the destination script. They cover
literal and variable room changes, stopped/program control, destination control
retake, cancellation of pending parser input, sound stop/completion, and the
next fresh key. The file contents are controlled test resources, not original
game media, and this integration test is Wild Bits-only. It confirms the
production native loading/execution path but does not replace the paired CoCo
comparison or cover room-zero execution and injected transition-load failures.

`check_room_commands.py` injects `E$PNNF` at the destination `VmLoadLogic`
boundary after the old room cache and room-owned services have been torn down.
The actual Wild Bits `ApplyRoomChange` returns that error with carry set,
releases the old non-root cache slot, retains the pending room request, and
preserves stack, private-state, and code guards. The focused fixture passed on
the current worktree on 2026-11-07. `check_coco_missing_logic_path` now follows
the actual absent-directory-entry path through `FetchLogic` and
`ResNotFoundErr`; it runs the real formatter and verifies the exact message
`Logics #58 not found.` at `message_box`, then observes the quit request at the
MMU handler. The message-box drawing and quit service themselves are controlled
boundaries. This replaces the removed, unrealistic injection of a returned
`E$PNNF` at `LoadLogicNum`.

The same test now compares Wild Bits' real missing-resource path. It executes
the production `ApplyRoomChange`, `VmLoadLogic`, `LoadAsset`, and
`ResourceLocate` code with OS-9 file calls and unrelated presentation services
controlled. For room 58 with a `$FFFFFF` `logDir` entry, Wild Bits seeks to the
correct three-byte entry, closes the directory file, releases the old room
cache entry, invokes the `GameUiCommand` cold-provider boundary for the normal
`wbui` diagnostic, and returns `E$PNNF` with carry set. The pending request,
old room cache entry, stack, private-state guard, and code remain intact. The
room-resource regression intercepts that UI boundary and verifies the request.
A separate actual-6809 call into the production `wbui` handler runs its real
formatter and verifies the exact `Logics #58 not found.` string at the
ShowCallbacks print-text slot, with stack, private-state and code guards intact.
`check_wbplay.py` also exercises a real missing nested-logic load through the
cold UI provider, supplies Enter to dismiss the resulting dialog, and verifies
the original error and restored VM caller state. The final print callback is
controlled in the exact-text case, and rendered room-58 dialog pixels are not
compared against CoCo yet; broader resource-failure cases also remain. S02
opcodes 18/19 stay open. The absent-entry fast path uses `$FF` as the impossible
volume marker, avoiding a redundant offset-word compare. The production
rebuild passes at `wbgame` 23,808/23,808 bytes and `wbui` 7,358/8,192 bytes.
Reproduce with `python3 tests/check_room_commands.py` and
`python3 tests/check_wbplay.py`.

The nested safe-point case executes a root script that calls a child script
containing `new.room`, with variable writes after the command in both scripts.
Both writes remain unexecuted; the child call unwinds, depth/current-logic state
returns to the root, and the root cursor remains at the post-call boundary. The
existing paired command check verifies that CoCo's synchronous setup returns
with its execution cursor zeroed. The paired synthetic destination fixture then
checks each owner's root script and caller continuation after room setup.

As a native integration checkpoint, `check_wbgame.py` now executes literal
`load.logics` and variable `load.logics.v` in its four-logic quest fixture,
then calls the preloaded children and verifies that only the two preloads and
the remaining uncached child take the cache-miss path (`1, 3, 2`). Child
effects and caller continuation remain correct. This checks the actual
Wild Bits interpreter and loader, but does not change the two rows' `open`
status until the same public commands are compared with CoCo.

#### S02 resident `load.logics` cache-hit comparison (2026-11-07)

`tests/check_load_logic_cache_hit.py` directly calls the actual CoCo
`cmd_load_logics`/`cmd_load_logics_v` handlers and Wild Bits
`VmCommandLoadLogic`/`VmCommandLoadLogicVariable`. The fixture places the
requested logic in each engine's resident table/cache, then checks literal and
variable selection, operand advancement, active caller asset context and
instruction position, replay records, unchanged resident links/records, stack
and guard bytes, and immutable code at two load addresses. The test exposed
that CoCo records every public request while Wild Bits previously recorded
only cache misses. The native command wrappers now add a replay record only
when the resident hit left the replay write position unchanged, so cache misses
do not create duplicate records. Both forms produce identical replay bytes.
All four handler paths pass. The same test also executes a real native
`load.logics` cache miss followed by a hit; replay contains exactly one record
per request, with no duplicate on the miss. The complete
`python3 tests/check_wbgame.py` CPU regression passes with the source change,
alongside the original KQ1 quest, modal, room-transition, rendering and cleanup
scenarios. Fresh resource-read comparison against the CoCo loader,
duplicate-list behavior and error cleanup remain open under S02.

The current-worktree rerun on 2026-11-07 also passes
`python3 tests/check_load_logic_cache_hit.py`: both owners' public resident-hit
handlers match replay entries, and native miss-then-hit execution records each
request exactly once. It does not exercise fresh public loads or error cleanup.

The all-title audit also emits `coverage.json`, a complete 182-command and
19-predicate inventory with effective routes, acceptance gates and candidate
regression families. C13 remains open: test suggestions and routed status are
not individual semantic comparison results.

### Predicate zero: command versus condition

Predicate zero is reconciled:
CoCo's `RetTrue` table entry is a constant-true condition, while command zero
remains the separate script-return operation. `check_logic_executor.py` runs
that predicate through the actual CoCo and native executors at two load bases,
including NOT/AND/OR traversal and the following command; `check_coco_conditions.py`
verifies the relocated CoCo table entry. Trace routes C04/C05 and the stub routes
C08–C12 also have explicit results. C13 remains open until every other command
and predicate has a meaningful semantic comparison, with each unsupported or
different result tied to its decision. Resource hashes identify audited
versions without treating a game-directory name as sufficient provenance.

#### S04 picture load, draw and show checkpoint (2026-11-06)

`check_picture_stream.py` executes the actual Wild Bits `load.pic`, `draw.pic`
and `show.pic` opcodes as one logic script. The resulting full frame matches
the CoCo `shdw.RenderPic` output for 23 original large packed pictures from
King's Quest IV and Space Quest 0. Ten synthetic streams place picture
commands and operands across 8/16-KiB boundaries, including offset 65527; the
test also checks malformed streams, injected map/unmap errors, and execution
of the next logic command. This records successful picture load/draw/show
behavior for these resources and boundaries. It does not close the other S04
commands or picture behaviors outside this corpus.

The same test now runs a two-picture `load.pic`/`draw.pic`/`load.pic`/
`overlay.pic`/`show.pic` script. It renders each source stream through the
actual CoCo `shdw.RenderPic`, composes the reference using non-default overlay
pixels, and compares all 26,880 visual/priority bytes with the Wild Bits
combined-picture buffer. It also checks the full displayed frame and a
following logic flag. The synthetic overlay matches, so opcode 28 is accepted
for this overlay composition behavior; complex priority masks, original-game
overlay scenes and failure restoration remain open.

#### S04 discard picture single-node unlink checkpoint (2026-11-06)

`check_resource_lifetime.py` executes the public CoCo `discard.pic` command and
the Wild Bits `GameDiscardPicture` handler for first, middle and last entries
in a three-picture list/cache at two code load addresses. This exposed a CoCo
unlink error: the predecessor link was cleared, dropping all later pictures
when a middle entry was discarded. `DiscardPicImpl` now copies the discarded
node's successor into its predecessor link. The regression verifies that the
remaining CoCo chain is intact and that Wild Bits releases only the selected
typed-cache slot, preserving its neighbors, guard bytes and caller stack.
Platform memory-release services are stubbed at the test boundary. This
accepts S04 opcode 27 (`discard.pic`) for the tested list/cache behavior; it
does not claim picture rendering or out-of-memory paths are covered here.

The existing `check_add_to_picture.py` regression also passed on this worktree:
52 actual immediate/variable static-cel draws cover automatic/custom/hidden
priorities, control-box band heights, occlusion, clipping and retained
background pixels. This is native rendering evidence for opcodes 122/123; the
rows remain open until the same cases are paired with actual CoCo behavior.

`check_text_rect.py` now executes CoCo's public `cmd_clear_text_rect` and the
Wild Bits logic command for color values 0, 1, 7 and 15. Both produce spaces
over rows 3–4, columns 5–7, with white foreground and the requested background
nibble; cursor/color state and script continuation are preserved. This
revealed that Wild Bits had collapsed every nonzero background to white. The
renderer now stores `$F0 | color` in graphics mode, and its pixel oracle expects
the corresponding palette index. Text-plane color and pixels are verified for
these valid rectangles. The full `check_wbgame.py` emulator suite also passes
`clear.lines` for both boolean colors and preserves the screen through its
following logic cycle. `GameClearLines` tags its private scratch color before
calling the shared rectangle helper, because the cold UI call changes the
current opcode; the helper therefore keeps `clear.lines`' black/white rule
separate from `clear.text.rect`'s 0–15 background rule. CoCo clipping versus
Wild Bits invalid-rectangle errors remain open under opcode 154. A direct CoCo
boundary probe confirms that a rectangle spanning rows 23–24 writes row 23
only, a requested bottom row of 255 still clips to row 23, and starts at rows
24 or 25 are successful no-ops. Wild Bits now follows those rules. The focused
CoCo/native test covers both clipping limits and no-op starts; the full game
regression checks these cases as well. The CoCo probe confirms a column-40
rectangle is passed to its text service without clipping (`row=3,column=40`).
The CoCo GRF driver computes text addresses as row stride plus `column * 2`
(`level2/cmds/grfdrv.asm`, `L1E9D`), so column 40 aliases column 0 of the next
row. Wild Bits now reproduces this linear spill for widths that fit the CoCo
rectangle's 42-byte local buffer, and `check_text_rect.py` compares both the
CoCo service request and resulting native cell coordinates. Wider and inverted
horizontal ranges remain rejected by Wild Bits; CoCo's 8-bit width arithmetic
can overrun its local stack buffer there. A bounded CoCo run of vertically
inverted bounds also issued eight row writes without returning; the test stops
at the service boundary before any display write or unbounded execution. Wild
Bits rejects inverted bounds with `E$IllArg`. These malformed-range cases remain
open under S04 pending an explicit behavior policy. A fresh direct run of
`python3 tests/check_text_rect.py` on 2026-11-06 passed all ten ordinary,
clipping and column-spill comparisons and reproduced the bounded eight-write
CoCo inverted-row probe. This confirms the same known edge behavior; it does
not close opcode 154 while malformed-range policy remains unresolved. The full
emulator regression includes the column-40 cases.

## 3. Finish the architecture and capacity work

- [x] **A01 — Reclaim code capacity:** Establish space for C01–C07 before adding
  resident instructions. Baseline limits: game 23,807/23,808 bytes; helper
  8,190/8,192; writable prefix 3,191/4,096; private data 24,465/24,576.
  Short branches, arithmetic delegation and common copies made C01 fit. The
  current rebuilt modules use game 23,785/23,808, UI helper 8,089/8,192, state
  helper 3,193/8,192, copied prefix 3,190/4,096 and private data 24,450/24,576.
  Nearby line-plot and UI-wrapper calls now use short subroutine branches,
  saving two resident bytes and one UI-helper byte. Screen-shake transfers and
  trace-overlay character/newline calls saved five more helper bytes; the
  memory-info and trace-display near calls saved two additional helper bytes.
  Trace activation, initialization, allocation and mapping now use three more
  short calls, for 11 UI-helper bytes recovered from the 8,148-byte baseline.
  The assembler rejected the attempted short branch to the more distant terrain
  helper, which remains a long call. These changes leave three resident code
  bytes, 55 UI-helper bytes, 4,999 state-helper bytes and 126 private-data
  bytes. The private reduction comes from right-sizing
  the 443-byte audio adapter's 512-byte workspace to 448 bytes.
  The latest in-range branch/call shortening pass recovered another 21 game
  bytes and 50 UI bytes from the prior measured build. An attempted shortening
  of the copied audio entry was rejected by its fixed three-byte entry ABI and
  reverted; the production build then passed. Current map/list analysis finds
  no further safe short transfers in `wbgame`; three candidates remain in the
  UI provider, and none increase resident capacity. The complete standard
  target passed all 59 commands on this build with exit status 0; its retained
  log is `.wildbits-test/continuation-20261029/full-check.log`. CoCo sources
  are untouched.
  The earlier intermediate build left three resident bytes; the current
  rebuilt modules leave 23 resident bytes and 103 UI-helper bytes. All seven
  C01–C07 implementations now fit within the unchanged address-space limits,
  their focused checks are recorded above, and the current complete 59-command
  target passes its budget, stack-guard and ABI checks in
  `/private/tmp/wildbits-parity-current-20261030.log`. This closes A01's stated
  capacity requirement for C01–C07. Future edits must continue to pass the
  same fixed limits and guards; remaining semantic coverage is tracked under
  C13 and S01–S08, not as an unbounded expansion of A01.
- [x] **A02 — Complete duplication inventory:** Reviewed the paired feature
  backends and the owner includes against the shared component catalog. The
  inventory and the disposition of each remaining parallel implementation are
  recorded below. No remaining common gameplay algorithm was found to exist
  only as two separately maintained bodies; the remaining paired code is
  either included from `objs/shared` or has an explicit representation/service
  boundary. Reopen this item if a future review finds an unclassified duplicate.
  This review does not claim that every behavior has differential test coverage;
  those gates remain S01–S08 and V02–V05.
- [x] **A03 — Document interfaces:** Assembly-time selection, shared-body
  calling assumptions, scratch/private-state ownership, native error cleanup,
  codec transfer rules, mapped-resource lifetime, helper ownership, and
  per-terminal input/clock/sound behavior are documented in
  [`objs/platform/README.md`](objs/platform/README.md#interface-and-ownership-contracts),
  with the concrete register/stack bindings beside each feature and ABI-specific
  provider contracts linked there. Shared assembly adds no runtime dispatch;
  hardware and OS calls stay in their platform backends. CoCo's four modules
  and native `wbgame`/`wbui`/`wbstate` keep their distinct packaging.
- [x] **A04 — Run the complete standard target:** All 59 current check commands
  pass on one revision, with reproducible logs; any debugger/test infrastructure
  failure is fixed or explicitly isolated and rerun. The older segmented
  baseline is useful evidence but does not satisfy this gate. The current
  workspace revision passed all 59 commands uninterrupted with exit status 0
  on 2026-10-17; the full output is `../../.wildbits-test/wildbits-check-final-20261017.log`.
  An earlier run hit a transient `check_wbres.py` debugger timeout; the isolated
  resource-loader rerun passed, followed by this complete clean run. Revision `78893f7`
  now passes the former 57-command target uninterrupted; the promoted
  priority/arithmetic/copy revision `a9a889a` passes all 58 commands. The
  ABI-8 capacity run now passes all 58 checks with exit status 0; the latest
  ABI-13 revision `33c079d` with the corrected host-time watchdog passes
  all 58 check commands uninterrupted with exit status 0. The final revision's
  full target also passed on 2026-10-17 (retained log above). Rerun after any
  later product change. The newer
  catalog revision `f1a52a3` passes all 59 checks uninterrupted with exit status
  0, including the trace reference and expanded UI routing checks. The ABI-12
  run stopped with a debugger disconnect; a guest-time cutoff was then
  reproduced. The original ABI-13 partial run was superseded after that
  fixture defect was identified. The ABI-11 run stopped on a debugger
  disconnect in static painting; its isolated rerun passes. The ABI-10 run
  stopped on a missing prebuilt CoCo fixture; the test now compiles that
  reference itself. The ABI-9 partial run was superseded and is not a pass.

  The current workspace was rebuilt and `make -f wildbits.mk check` completed
  on 2026-10-19 with local loopback access for the emulator harness. All 59
  checks completed and reported PASS; the retained 878-line log is
  `../.wildbits-test/wildbits-check-full-20261019.log`. Coverage includes
  1,024 native dispatch cases,
  4,544 math comparisons, 5,140 view queries, 548 CoCo/native formatter
  comparisons (including 16 original-resource escapes), 4,094 index/formatter
  calls, original KQ1 game regressions, both original Space Quest missing-
  operand message cases, 443 packed picture comparisons, and streamed-picture/
  error-cleanup cases. The log contains no failed target or assertion. This
  supersedes the earlier run whose output-capture path was invalid. A04's
  standard CPU/build gate is now satisfied for this workspace revision; the
  physical Wild Bits gate remains open below. After that logged run, the
  formatter test was extended to make slot zero empty for the original `%s`
  missing-operand case and to exercise the original Space Quest II message
  table through both formatters; `tests/check_decimal_index.py` was rerun and
  passed all 548 differential comparisons, the original-resource case and
  4,094 calls. It now also verifies the formatter's 2,047-byte output bound,
  corrupt/truncated message sections and an unterminated original message
  against the CoCo reference, with native cleanup guards checked on each error.
  The expanded formatter target passed again on 2026-10-19. The complete
  `make -f wildbits.mk check` target was then rerun from `objs/`; all 59 check
  commands completed successfully, including this expanded formatter target.
  The earlier retained logs document preceding revisions; the final
  latest 50-case executor revision's complete 885-line output is retained at
  `../.wildbits-test/wildbits-check-manhunter-overlap-20261019.log` (all 59
  commands, exit status 0). This includes the exact Manhunter I dual-decode
  cases and the three trace short-call substitutions; UI helper capacity is
  8,137 bytes. A fresh `make -f wildbits.mk check` on 2026-10-29 rebuilt the
  current working tree based on `6829106df38a1919ee655c838396ac333a709115`
  and completed all 59 check commands with exit status 0. It rebuilt `wbgame`
  at 23,807/23,808 bytes, `wbui` at 8,145/8,192, and `wbstate` at 3,193/8,192
  (writable prefix 3,190/4,096; private data 24,450/24,576). The run included
  the updated formatter/error cases, nested-call fixture, original KQ1 game
  flows, native text/graphics pixel checks, all 443 packed-picture comparisons,
  stream/resource cleanup and final `wbpic` pixel/error checks. This refreshes
  the current-tree pass evidence; the retained full logs above remain from the
  2026-10-19 source revision. A04's standard CPU/build gate is satisfied for
  the tested current tree; physical hardware acceptance remains open. After
  adding the 51st executor script for indirect variable access, the entire
  standard target was run again from `objs/` and completed all 59 test commands
  with exit status 0. Its complete log is
  [wildbits-check-indirect-20261029.log](tests/reports/wildbits-check-indirect-20261029.log);
  the log records the final module sizes above and the passing v0/v255 indirect
  read/write comparison. This is the latest full-target evidence for the
current working tree. After the subsequent capacity edits and restoration of
the audio adapter's fixed three-byte entry slot, `make -f wildbits.mk check`
was rerun from `objs/` on 2026-10-29. All 59 commands passed with exit status
0; the complete captured output is
[`sierra/.wildbits-test/continuation-20261029/full-check.log`](.wildbits-test/continuation-20261029/full-check.log).
The rebuilt sizes are `wbgame` 23,785/23,808, `wbui` 8,089/8,192 and `wbstate`
3,193/8,192 bytes (writable prefix 3,190/4,096; private data 24,450/24,576).
The current binaries also pass the original KQ3 and KQ4 MAME scenarios; the
KQ4 run verifies its centered `look` popup, Inventory text page and restoration.
The full target ran on 2026-10-30 after adding the remaining malformed
`assignv`, `addv`, and `subv` cases. `make -f wildbits.mk check` completed with
exit status 0; the output reached the final `check_wbpic.py` PASS. Rebuilt
module sizes were `wbgame` 23,785/23,808, `wbui` 8,089/8,192, and `wbstate`
3,193/8,192 bytes (writable prefix 3,190/4,096; private data 24,450/24,576).
The current KQ4 MAME rerun also passed its intro, movement, centered popup,
Inventory and restoration assertions; its artifacts are described under S04.
The full console log is not retained for this run, so this records observed
terminal output and exit status rather than a reproducible archived log.
The complete standard target was rerun once more on 2026-10-30 after the
current shared-source and UI changes. It rebuilt the production modules and
completed all 59 check commands with exit status 0; the retained output is
`/private/tmp/wildbits-full-check-20261030.log`. The log contains all 59 test
invocations and no traceback or failed assertion. It includes the expanded
formatter and malformed-executor comparisons, loaded-game integration, all 443
packed-picture comparisons, and final actual-6809 framebuffer/error-cleanup
checks. Final sizes are `wbgame` 23,785/23,808, `wbui` 8,089/8,192, and
`wbstate` 3,193/8,192 bytes (writable prefix 3,190/4,096; private data
24,450/24,576). This is the current A04 build/regression evidence; it does not
close the remaining semantic/gameplay or physical-hardware gates.
The target was independently rerun once more on 2026-10-30 after strengthening
the command-manifest self-test. `make -f wildbits.mk check` again completed all
59 commands with exit status 0; the full log is
`/private/tmp/wildbits-parity-current-20261030.log`. It rebuilt the same module
sizes and passed the final `wbpic` check. The all-title static manifest was
also regenerated from the current worktree at
`../.wildbits-test/audit-20261030-parity/`; this inventory still does not
replace the open per-command semantic evidence listed for C13.
After expanding `check_native_audio.py` to decode and compare all note events
in the original KQ4 CoCo intro sounds 2, 100, 101 and 102, the complete target
was run again from `objs/`. All 59 commands passed with exit status 0; the
complete 891-line log is `/private/tmp/wildbits-audio-parity-full-check-20261030.log`.
The audio test compared 386 original note events, including tone, amplitude,
duration, order and end packets. Module sizes remain `wbgame` 23,785/23,808,
`wbui` 8,089/8,192 and `wbstate` 3,193/8,192 bytes. This refreshes A04 for
the current tested source tree; semantic/gameplay and physical-hardware gates
remain open.

The full standard target was rerun from `objs/` on 2026-10-31 after fixing
three test-harness defects exposed by the preceding complete game run: SOL
clock and PSG status `I$GetStt` calls were falling through to generic file-size
handling, and the text-mode test compared a captured byte string with an
integer. All 59 check commands passed with exit status 0. The complete log is
`/private/tmp/wildbits-parity-harness-fixes-20261030.log`; its command count is
59, and its final `check_wbpic.py` output is PASS. Rebuilt sizes were `wbgame`
23,778/23,808 bytes, `wbui` 8,089/8,192, and `wbstate` 3,193/8,192 (writable
prefix 3,190/4,096; private data 24,450/24,576). This refreshes the standard
build/regression gate, not the open semantic parity or hardware gates.

On 2026-10-30, after the KQ4 picture-stream, persistent-window and related
source changes, `make -f wildbits.mk check` completed all 59 commands with exit
status 0. The complete 891-line log is
`/private/tmp/wildbits-parity-check-current-20261030-2.log`. It includes the
current KQ1/KQ3, logic-executor, audio-resource, formatter, picture, stream,
resource-loader, fill-selection and final actual-6809 pixel/error-cleanup
checks. Module sizes are `wbgame` 23,785/23,808, `wbui` 8,089/8,192 and
`wbstate` 3,193/8,192 bytes. This refreshes A04 only; C13, S01–S08 and the
remaining V02–V06 acceptance work are still open.

On 2026-10-31, the full standard target was rerun after adding the two-active-
mover collision edge case and correcting the follow-motion test to permit the
shared eight-way direction routine's one-pixel diagonal step. All 59 check
commands passed with exit status 0. The log is
`/private/tmp/wildbits-collision-edge-parity-20261031-rerun.log`. This includes
the 3,100-call CoCo/native collision comparison, 443 packed-picture comparisons,
the native game integration and original KQ3 startup checks, and the final
picture/decode checks. Module sizes are `wbgame` 23,778/23,808 bytes, `wbui`
8,089/8,192 and `wbstate` 3,193/8,192. S03 remains open for complete-cycle
multi-actor movement, follow/wander sequences, blocking interactions and room
edge behavior. Passing the standard target refreshes A04; it does not close the
remaining semantic parity or physical-hardware gates.

The 2026-10-31 standard target was rerun after adding a loaded-game two-mover
cycle scenario and a paired CoCo `UpdateAllMotion` reference. It passed all 59
checks with exit status 0; the retained log is
`/private/tmp/wildbits-coco-two-mover-parity-20261031.log`. CoCo and Wild Bits
both move the actors from X=10/30 to X=19/21 and stop at edge contact. The
original KQ4 real-driver MAME acceptance also passed against the same rebuilt
modules, with artifacts at
`/private/tmp/wildbits-kq4-current-parity-20261031`. These results extend A04,
S03 paired motion evidence, and S04/S06 original-game acceptance; remaining
listed parity gates are still open.

The paired follow case in `tests/check_wbplay.py` seeds the same two object
records into the actual CoCo motion routines and the loaded Wild Bits game cycle.
The follower uses `ignore.objs` so ordinary follow completion is measured without
entering either backend's object-collision recovery. The test clears CoCo flag
memory, replays the pending first cycle, and checks that both engines stop the
follower and set completion flag 255; final coordinates are compared with a
one-pixel tolerance for their differently scheduled motion updates. The focused
`python3 tests/check_wbplay.py` run passed on 2026-10-31. This verifies ordinary
follow completion; the blocked-follow case is described below. Wander over time,
room transitions and other S03 cases remain open.

That follow comparison exposed a blocked-step divergence: Wild Bits had been
setting and clearing `$25` bit `$40` as temporary collision state. CoCo leaves
that byte unchanged; bit `$40` is the AGI random-animation property also read by
shared follow/wander logic. Removed the Wild Bits mutation and added a paired
blocked-follow case. Both engines now stay at the same last walkable position,
retain the follow motion state, leave random-animation clear, and leave
completion flag 255 unset. The completed-follow case, blocked-follow case,
two-mover case and 3,100-call collision filter test pass against the rebuilt
`wbgame` (23,750 bytes). `check_object_terrain.py` (3,328 comparisons),
`check_motion_setup.py`, and the loaded-game `check_wbgame.py` all pass on this
revision. The post-fix `make -f wildbits.mk check` then completed all 59 check
commands on 2026-11-01; the retained 904-line log is
`/private/tmp/wildbits-parity-follow-fix-20261031.log`. It records 170 passing
assertion summaries, no failed checks, and final picture/decode acceptance.
Modules are `wbgame` 23,750/23,808 bytes, `wbui` 8,089/8,192 and `wbstate`
3,193/8,192. This closes only these two follow cases within S03; long-run
wander, terrain interactions and room-edge transitions remain open.

The focused motion test now also invokes the actual CoCo and Wild Bits
`ObjAnimStep` routines with the random-byte service replaced by the same fixed
value. Both owners select direction 7, set the minimum valid delay to 7, count
down to zero without rerolling when random animation is disabled, and select a
new direction when the delay expires. It then compares 16 more random-animation
ticks with the fixed random byte; both owners select direction 7 and keep their
delays within 6–7. The test checks ego-direction publication, stack balance and
the Wild Bits private-state guard. This isolates wander's state transitions
from the platforms' intentionally different random generators; it does not
establish scene-level wander movement or terrain-response parity.
`python3 tests/check_wbplay.py` passed first with the three transition checks
inside the complete target run, then with the expanded 19-tick comparison on
2026-11-02.

On 2026-11-05, `check_wbplay.py` added a paired `move.obj` completion case. The
loaded Wild Bits event loop moves object 1 from `(10,60)` to `(20,60)`; the same
captured records run through CoCo's actual `DispatchMotion` and
`UpdateAllMotion` routines. Both owners reach the target, stop with matching
direction/motion state, and set flag 200. The CoCo placement service is stubbed
to accept this fixture's empty, walkable scene. The focused test passes; the
full target was then run against this test revision. It reached
`check_cancel_line.py` after the motion, parser, rendering, resource and
all-picture checks, but the debugger transport timed out while waiting for a
CPU response. The isolated `check_cancel_line.py` rerun passed all 316 cases;
every remaining target after it also passed sequentially, through
`check_wbpic.py`. The full make invocation therefore did not exit cleanly in
one uninterrupted run, but its only reported failure was a transport timeout,
not a failed assertion. Full-run log:
`/private/tmp/wildbits-check-resume-20261105.log`. The target rebuilt
`wbgame` at 23,750/23,808 bytes (`wbui` 8,089/8,192; `wbstate` 3,193/8,192).
The retry set was `check_cancel_line.py`, `check_persistent_window.py`,
`check_picture_stream.py`, `check_lzw.py`, `test_picture_resource.py`,
`check_wbres.py`, `check_fill_selection.py`, `check_wbdecode.py` and
`check_wbpic.py`; all passed. `check_wbplay.py` also passed inside the initial
target after adding move-to and 19-tick wander coverage. `git diff --check` and
Python compilation of the edited test sources pass. This is fresh regression
evidence, not closure of the semantic or game-acceptance gates below.

The complete `make -f wildbits.mk check` target was rerun from `objs/` on
2026-11-02 with this test included. All 59 test commands completed; the 894-line
log is `/private/tmp/wildbits-parity-wander-20261102.log`, and its final
`check_wbpic.py` target passed. The run rebuilt `wbgame` at 23,750/23,808 bytes,
`wbui` at 8,089/8,192, and `wbstate` at 3,193/8,192. This refreshes the
automated build/regression evidence only; C13, S01–S08 and V02–V06 remain open.
The 19-tick wander and paired `move.obj` additions were also included in the
2026-11-05 target attempt; their focused and in-target checks passed. The
remaining semantic and acceptance gates are still open.

#### S03 object flag and cycle command checkpoint (2026-11-06)

Three focused actual-6809 comparisons now provide command-level C13 evidence.
`check_object_flags.py` covers opcodes 45, 46, 56, 61, 62, 64–68, 70–80,
83–85, 88–91, including cycle state/rate, motion stop/start, follow/wander setup,
and the global block/unblock rectangle at three coordinate boundaries.
`check_object_scalar_commands.py` covers priority and direction
opcodes 54, 55, 57, 86 and 87, plus `set.horizon` opcode 63, over 7,208
calls. The horizon comparison checks legal values 0, 1, 166 and 167 at both
load bases for both owners; the native handler also rejects 168 and 255 without
changing the stored horizon. `check_motion_setup.py` covers
the literal and variable `move.obj` setup routes, opcodes 81 and 82. Each
compares the real CoCo and Wild Bits handlers and checks relevant object,
variable, flag, stack and guard state. All three passed on 2026-11-06.

#### S03 object distance command checkpoint (2026-11-06)

`check_object_distance.py` executes opcode 69 through both actual command
handlers at two load bases. Its 24 calls cover visible and invisible objects,
reversed coordinates, first/last object records, exact and overflowing
saturation cases, and zero distance. The test checks output variable 255,
unchanged object records, stack/record guards and native instance bounds. This
accepts the shared Manhattan-distance calculation and its visible-object policy;
distance behavior during live movement and collision updates remains open. The
test is now part of `make -f wildbits.mk check`; the full target completed on
2026-11-06, including its final picture-decoder probes.

These results accept only the listed command-level states. They do not prove
multi-cycle wander, move completion under varied terrain, blocking geometry,
room-edge transitions or full loaded-game interaction; S03 remains open.

#### S03 object-position predicate checkpoint (2026-11-06)

`check_object_position_predicates.py` compares the actual CoCo and native
handlers for predicates 11, 16, 17 and 18 in 3,200 calls. The matrix covers
first/last object records, coordinate and width wrap, zero/odd/even widths,
inclusive rectangle edges, and rectangles spanning the byte-coordinate range.
It checks the returned Boolean, operand cursor, object records, guards, stack
and immutable code. The first run exposed a native defect: opcode 16 used the
center rule, while opcode 18 used the full box span. The handler now matches
CoCo's box, center and right-edge calculations, and all matrix cases pass.
This accepts those four position predicates; room transitions and the broader
S03 movement/rendering cases remain open. The rebuilt 23,752-byte `wbgame` also
passed the KQ4 single-Space intro, movement, popup, menu/Inventory and scene
restoration MAME checkpoint with the documented compatible driver pair; captures
are in `/private/tmp/wildbits-kq4-position-fix-20261106`.

#### S03 motion integration refresh (2026-11-06)

`check_wbplay.py` passes the original CoCo motion routines against the loaded
Wild Bits cycle: `move.obj` reaches the same target and completion flag, 19
controlled wander ticks match including the published ego direction, and ten
CoCo motion ticks match a two-mover Wild Bits collision at the same edge. The
run also covers follow/block outcomes, stop/start/force update, pause/resume
clock behavior, modal restoration and lazy plain/LZW resource loads. This
extends motion evidence; broader terrain, room-edge and full-scene collision
coverage remain open under S03.

#### S03 coordinate and animation command checkpoint (2026-11-06)

`check_object_coordinates.py` passes against both actual owners at two load
bases for opcodes 33, 37–40, 147 and 148. It compares position and get-position,
animate-object behavior, signed delta reposition and absolute reposition
fields; exercises aliased output variables and first/last object records; and
checks native invalid indexes, stack/record guards and unchanged code. This is
command-level coverage; loaded view lifecycle, erase/redraw and room-edge
behavior remain open.

#### S03 view-query command checkpoint (2026-11-06)

`check_view_queries.py` passes 5,140 actual CoCo/native calls for opcodes 49–53:
last cel, current cel, current loop, current view and number of loops. It tests
every byte value, first/last object records, native empty-loop and invalid-index
errors, two load bases, full record/private-state preservation and guards. This
accepts the queried values and stated error boundaries; view selection, cel
redraw and resource-lifecycle interactions remain open.

#### S03 view loop and cel selector checkpoint (2026-11-06)

`check_view_cache_reload.py` now drives opcodes 41, 42, 43, 44, 47 and 48
against original view data. It selects view 0 and loop 1/cel 0 with literal
operands, then selects view 8 and loop 0/cel 1 through variables. The test
captures the native object state between each selector and compares the view
number, loop/cel counts and dimensions with CoCo after each matching operation.
It also checks that both views remain correctly cached and that selector calls
hit the intended resource. The actual resource and cache path pass; rendering,
invalid selector policies and view-list cleanup during active scenes remain
open.

#### S03 KQ4 reverse-loop direction checkpoint (2026-11-06)

Original KQ4 view 0 has five loops, and logic 101 sets AGI flag 20 before
Rosella's rightward movement. CoCo's animation policy permits views with more
than four loops and selects the reverse-direction loop table when flag 20 is
set. The native binding previously rejected this loop count, so direction 3
selected loop 1 and Rosella's sprite appeared to walk backward while her X
position advanced. `wildbits-memory-resources-bindings.asm` now uses the CoCo
loop-count policy and reads native `vmflags[20]` for the same reverse-table
decision. The optional `--direction-trace` path in `check_kq4_mame.py` ran the
original KQ4 logic and movement in MAME against rebuilt `wbgame`; it confirmed
direction 3, view 0, loop 0 of 5, flag 20 set, and advancing X (120 through 152).
The focused trace passes. This closes that concrete direction-animation case;
other animation-cycle combinations and full KQ4 progression remain open under
S03/S04.

The standard non-debugger `check_kq4_mame.py` run also passes through the
single-Space intro, beach-to-woodland rightward movement, look dialogue,
Escape/menu, Inventory, and scene restoration. Screenshot measurements show
the expected camera scroll and preserve scene colors on both sides of the
centered look window. The test oracle now recognizes the original fruit
narration at the one-Space checkpoint and measures the small opaque popup
against its surrounding scene, instead of requiring most of the larger
measurement region to be white. This accepts the tested intro/input/dialogue
path, not a complete KQ4 playthrough.

#### KQ4 modal display comparison (2026-11-06)

To investigate the report that Wild Bits replaces the game picture with a white
screen, I ran the CoCo 3 KQ4 modal capture against a separately built MAME
`coco3` target, using the original disk pair and CoCo ROMs. The test passes:
ordinary `look` text appears in a centered black/white popup while scene pixels
remain visible on both sides; Inventory is intentionally a full black-on-white
text page, and a fresh Space restores the scene. CoCo captures and metrics are
under `/private/tmp/coco-kq4-popup-20261106`.

I then reran the corresponding original KQ4 scenario on Wild Bits MAME using
the unchanged `mame` Wild Bits binary. It passes the single-Space intro,
movement, centered `look` popup, menu/Inventory and restoration checks. The
look capture contains varied scene colors on both sides of the popup; Inventory
is a full text page and restores the gameplay scene with Space. Results are
under `/private/tmp/wildbits-kq4-coherence-rerun-20261106`. Thus the measured
ordinary popup and Inventory behaviors match the CoCo reference. This does not
yet compare the king's specific conversation line-by-line; that interaction
still needs a controlled room/dialogue checkpoint under S05/S06.

#### KQ4 throne-room narration dwell comparison (2026-11-06)

To investigate the report that the King's text vanishes as soon as it finishes,
I captured the original KQ4 throne-room beat at one-second intervals with no
further keys after the initial Space. The exact caption `He flings the battered
hat towards his children and his wife, Queen Valanice, proudly looks on.` is
visible in the CoCo 3 capture at frame 19920 and gone by frame 20040. In the
Wild Bits capture it is visible at frame 7800 and gone by frame 7920. Both
therefore advance this caption automatically, without a dismissal key, after
roughly the same one-to-two-second interval. This specific intro behavior is
not a Wild Bits-only early-dismissal regression. It does not prove the timing
of every throne-room line or an interactive conversation; the screenshots are
in `/private/tmp/coco-kq4-throne-dwell-20261106` and
`/private/tmp/wildbits-kq4-throne-dwell-20261106`.

The same standard scenario with `--audio-trace --audio-wav` passed with MAME's
audio mixer enabled. It observed 1,112 process-owned PSG register writes and
captured stereo 48 kHz PCM with intro-window AC RMS 52.8 and peak-to-peak 231
(`audio-summary.json` and `audio-writes.json` under
`/private/tmp/wildbits-kq4-audio-20261106`). This proves a changing MAME audio
signal reaches the mixer; it does not establish the user's speaker/output
volume or physical-board loudness.

The complete `make -C objs -f wildbits.mk check LWASM=lwasm.orig` run also
passed after the test-oracle fixes, including loaded `wbgame`, all 443 packed
picture comparisons, the 228-resource LZW check and the sprite-damage failure
paths. All production and probe size limits passed; `wbgame` linked at
23,800/23,808 code bytes.

#### S03 unanimate-all command checkpoint (2026-11-06)

`check_object_block_state.py` now invokes opcode 34 through both public command
entries and verifies all 64 object records. Both engines clear the animated and
visible bits while preserving every other byte, with stack and record guards.
For CoCo, the test replaces only the leading `ClearBothRanges` call with NOPs;
that MMU range-cleanup service remains outside this command-body comparison.
This verifies bulk state mutation only; view-list cleanup and the full render
cycle remain open.

#### S03 stop start update command checkpoint (2026-11-06)

`check_object_update_control.py` passes 8,192 actual CoCo/native command calls
for opcodes 58 (`stop.update`) and 59 (`start.update`). It covers all 256
starting flag bytes, four object slots including the first and last, repeated
already-stopped/already-started states, and two code load addresses. Whole
object records, operands, stack and private-state guards are checked. The CoCo
helper's MMU draw-range maintenance calls are replaced with NOPs in this
focused probe; the actual command handlers and flag-transition helpers remain
assembled and executed. This accepts the update-bit transitions only. Draw,
erase remain open.

#### S03 force update command checkpoint (2026-11-06)

`check_force_update.py` passes 16 direct calls through both actual opcode-60
handlers at two code addresses. It checks first/middle/last object indexes,
preserved object and private state, operand/stack guards, and CoCo's
`ClearBothRanges`/`SwapObjRanges`/`UpdateObjSegments` sequence against Wild
Bits' unmap/recompose/present sequence. CoCo range services are intercepted at
their call boundaries; Wild Bits composition and presentation are likewise
intercepted here. The game-cycle frame-capture case in `check_wbplay.py`
supplies the rendered-result check: force update leaves the stopped sprite and
its pixels unchanged and does not advance motion or cels. This accepts opcode
60's refresh behavior.

#### S03 draw and erase command checkpoint (2026-11-06)

`check_object_visibility.py` passes 384 actual CoCo/native public command calls
for opcodes 35 (`draw`) and 36 (`erase`) across two object slots and two code
addresses. The cases cover already-drawn/undrawn idempotence, stopped-but-
visible objects, the single-advance flag and preservation of every other
record byte. CoCo range, cel-position and MMU rendering services are stubbed
at the helper boundary for this state comparison; `check_wbgame.py` separately
checks sprite pixels, clipping, transparency, occlusion and erasure in the
native game cycle. The comparison exposed that native `draw` restarted an
already-drawn stopped object and failed to clear CoCo's single-advance flag.
`GameObjectVisibility` now matches CoCo's no-op and flag behavior. Broader
platform rendering and room-transition behavior remain under S04/S03.

### A02 backend disposition

The inventory covers every paired feature source in `objs/platform/` and the
shared bodies documented in [`objs/shared/README.md`](objs/shared/README.md).
Shared code is assembled in place through compile-time bindings, so this review
does not require identical module layout or runtime platform dispatch.

| Feature | One shared source of behavior | Remaining paired implementation and reason |
| --- | --- | --- |
| VM and logic | `logic-executor.asm`, `condition-flow.asm`, `condition-tests.asm`, `agi-command-table.asm`, `agi-test-table.asm`, and command-family files | `coco-logic.asm` owns the contiguous CoCo stream/table ABI; `wildbits-logic.asm` owns bounded resource access, native cache records, process-private flags and OS-9 error returns. These are storage/execution adapters for the same executor. |
| Objects and motion | `object-commands.asm`, `object-motion.asm`, `object-animation.asm`, terrain, bounds, placement, collision, follow/wander and delta components | `coco-objects.asm` and `wildbits-objects.asm` bind different object records, MMU versus native address spaces, terrain services, collision identity, horizon representation and error/edge policies. The policy differences are explicit in `*-objects-bindings.asm`; no second unbound movement/animation algorithm remains. |
| Pictures and view rendering | Picture command catalog, coordinates, line/pen geometry, color rules, and common view/cel command semantics | `coco-graphics.asm` and `wildbits-graphics.asm` implement different pixel stores, mapping windows, palette/display APIs and presentation planes. Those operations touch platform memory/display hardware and cannot share an address-level routine. Shared geometric and command decisions are in `objs/shared/`. |
| Resources and codecs | `resource-codecs.asm`, `xor-decrypt.asm`, `agi-xor-key.asm`, directory/header decoding and shared logic/view command rules | CoCo loading maps fixed MMU blocks and uses its resource directories; Wild Bits loading owns OS-9 paths, bounded reads, physical slabs, cache replacement and release. Resource ownership and failure cleanup differ by OS; the codec/format rules are shared. |
| Text, parser and modal UI | Formatter, numeric/string conversion, tokenization, dictionary lookup, said matching, inventory semantics and string comparisons | The CoCo text plane, cursor/editor and module calls differ from Wild Bits terminal input, process-owned dialog state and helper-provider UI. Key acquisition and drawing remain backend services; common parsing/formatting rules are shared. |
| Input and timing | Logical cycle reset/rollover and common movement/input command policies | CoCo timer intercept and keyboard matrix versus Wild Bits process clock, terminal key status and joystick driver are hardware/driver interfaces, not duplicate game rules. |
| Sound | AGI sound state and command sequencing where represented in common VM behavior | CoCo direct sound hardware versus Wild Bits owned PSG-driver path have different device and process ownership contracts. Register writes stay in each backend. |
| Startup, memory and save lifecycle | Shared save-state semantics and common command-level state selection where applicable | CoCo's four cooperating modules and MMU allocator differ fundamentally from the native process-owned modules, module-link lifecycle, OS-9 allocation and provider ABIs. This is packaging/OS ownership, not duplicated gameplay logic. |

The source review found no additional common algorithm suitable for safe
extraction without changing a platform contract. Shared files can still be
refined as equivalence defects are discovered; A02 records the completed
duplication audit, while A03 records the separate interface-contract task.

## 4. Acceptance across games, terminals and hardware

- [x] **V01 — Audit every bundled title:** Run script/message audits for all 14
  bundled titles; resolve parse failures and classify every unsupported/no-op
  site and unresolved dynamic destination. An audit must never imply runtime
  completion merely because it reports no missing routes.
- [ ] **V02 — Automate game checkpoints:** Commit deterministic scenarios for
  original resource versions covering startup, help, movement/room changes,
  dialogue, menus, inventory, save/restore/restart, death, representative puzzles
  and ending. At minimum cover KQ1, KQ3, KQ4 and Larry as distinct compatibility
  probes, then account for every other bundled title in the acceptance matrix.
  Use controlled bootstraps/state injection where necessary and label them;
  do not make the user manually finish fourteen adventures. The current per-title
  evidence and remaining scenario gaps are tracked in
  [WILDBITS-CHECKPOINTS.md](WILDBITS-CHECKPOINTS.md); all fourteen titles now
  pass a startup/display/cleanup checkpoint, and KQ1, KQ3 and Larry have richer
  gameplay probes. KQ4 now advances through its credits, moves Rosella, returns
  the original river-meadow look text after the camera-scroll transition,
  restores graphics after a fresh Space key, opens the
  menu, and selects Inventory to verify the exact empty-inventory prompt and
  return to play. Required gameplay checkpoint coverage remains incomplete,
  especially broader saved-state coverage, puzzles, death/ending and the ten
  additional titles, so this gate remains open. Its optional
  `--persistence` MAME probe now saves a KQ4-tagged state through the original
  File menu, changes the scene, restores, and proves the saved room and ego X/Y
  match through a second snapshot before continuing original logic; details are
  in `WILDBITS-CHECKPOINTS.md`.
  Current-module reruns also pass KQ1 hall arrow recovery, the king speech's
  2,000-frame text hold/fresh-key dismissal, menu restart, save/walk/restore,
  and Larry's quiz/bar/inside-look route, with continued input and memory
  recovery. The Larry/KQ1 two-terminal MAME probe passes when booted with the
  expanded-memory test kernel also required by the KQ3/KQ1 pair test: both
  original games remain visible across switches, KQ1 Inventory receives
  independent input, Larry continues after KQ1 exits, and the memory map is
  restored. The default test kernel aborts the first process with error 228;
  the runner now rejects that invalid setup unless `--expanded-krnp2` is
  supplied. This closes one pair scenario, not V04's broader repeated-start,
  interruption and injected-failure matrix. Details and artifacts are recorded
  in `WILDBITS-CHECKPOINTS.md`.
  On 2026-11-06, `check_wbpic_mame.py --native-game kingsquest1 --interpreter`
  also passed with two simultaneous `wbgame` instances: every displayed pixel
  matched, both pictures restored across terminal switches, the peer survived
  independent exit, relaunch succeeded, and the free-memory map returned to
  baseline. Artifacts are in
  `/private/tmp/wildbits-multiterminal-compatible-20261106`. The stock L2 disk
  image failed the restore-pixel assertion; rerunning with the documented
  compatible OS/graphics-driver pair passed. This adds a fresh concurrent
  process/display check, but it uses controlled picture logic rather than two
  complete games and does not close V04's modal/audio/save/failure stress.
  A same-day `--text-modes` rerun also passed every pixel while switching the
  second terminal between graphics and text. Its oracle keeps the existing
  picture and draws the opaque text row over it, matching `text.screen`; the
  previous oracle had incorrectly expected a blank graphics page. Artifacts:
  `/private/tmp/wildbits-multiterminal-textmode-rerun-20261106`.
  A concurrent `--persistence` rerun now also saves, changes and restores the
  second process state, rejects malformed/truncated snapshots, reuses an
  existing save name without an error or scene disturbance, validates the file
  and CRC, then verifies peer survival, relaunch and memory recovery. The
  runner previously expected an error for this successful replacement path;
  the corrected assertion and rerun pass at
  `/private/tmp/wildbits-multiterminal-persistence-rerun-20261106`. V04 still
  needs repeated start/interrupt and injected driver/allocation-failure stress.
  The actual original Larry/KQ1 concurrent pair passed again with the matching
  OS disk and expanded-memory kernel: both scenes survive terminal switches,
  KQ1 Inventory receives its own input, Larry continues after KQ1 exits, and
  Larry-only/final memory maps match. Its current artifacts are in
  `/private/tmp/wildbits-full-game-pair-correct-20261106`. This closes another
  real-game two-terminal scenario; repeated starts and failure injection remain.
  On 2026-10-29, the refreshed KQ4 MAME checkpoint passed using the current
  production modules; it additionally verifies the original river-meadow `look`
  dialogue inside the centered 21x7 popup with varied game-scene pixels still
  visible outside it. The distinct File-menu persistence probe also compares
  saved room and ego X/Y after restore, as described under S08. The KQ4 Help
  screen is now checked by an optional menu scenario, which recognizes the
  original instructions and verifies Space returns to Rosella's scene. Other
  saved fields, item-bearing inventory, death, puzzles, ending, the other-title
  behavior matrix and V02 as a whole remain open.
  The all-title startup-only matrix passed again against the rebuilt modules on
  2026-10-29; all fourteen original-resource games changed the screen, returned
  to the shell after interruption and restored the exact free-memory report.
  Artifacts are under `/private/tmp/sierra-all-title-startup-20261029`.
  It passed again on 2026-11-06 against the current modules; artifacts are in
  `/private/tmp/wildbits-all-title-startup-current-20261106`. On that same
  module build, KQ1's actual-menu save/walk/restore and menu-restart scenarios
  passed: the restored ego returns to X=449.5 after moving to X=625.5, and the
  restart path unwinds to depth zero, resets the ego, accepts new arrow input
  and exits with recovered memory. See `WILDBITS-CHECKPOINTS.md`. This adds
  focused KQ1 coverage; it does not close V02's full title/gameplay matrix.
  The 14-title startup/display/exit matrix passed once more on 2026-11-07 with
  the current modules and Wild Bits-aware MAME binary; all original titles
  reached a changed display, returned to the shell and recovered their starting
  free-memory report. Artifacts are under
  `/private/tmp/wildbits-all-title-startup-rerun-20261107`. This refreshes
  startup/cleanup only; the per-title gameplay matrix remains open.
  After the 2026-10-30 complete build, the same matrix passed again against the
  current module files for all fourteen titles. Each reached a changed original
  game display, returned to the shell after the controlled interrupt, and
  recovered its initial free-memory report. Per-title artifacts are in
  `/private/tmp/wildbits-all-title-startup-current-20261030`. This refreshes
  startup/cleanup only; gameplay coverage remains open in V02.
  KQ1's actual eastbound castle-to-lake and westbound return journey also passed
  on 2026-11-06 with exact original room descriptions, continued input, clean
  exit and unchanged free memory; artifacts are in
  `/private/tmp/wildbits-kq1-journey-current-20261106`. V02 remains open for
  broader title gameplay, puzzles, death and ending coverage.
  The complete native `python3 tests/check_wbgame.py` suite passed again on
  2026-11-07 against the current modules. This includes original KQ1 help,
  death, pickup and puzzle sequences, three coronation/quest-chain variants,
  fiddle/dragon/giant encounters, timed and held messages, literal and variable
  object previews, menus, input, screen backends, save/restart and ownership
  cleanup. The same run executed four actual CoCo `show.obj`/`show.obj.v`
  handler cases at two code bases, through the MMU draw/erase calls with the
  renderer stubbed. It establishes a broad native regression baseline and
  command-to-renderer behavior, but not rasterized CoCo pixels or the missing
  per-title MAME gameplay matrix;
  V02 and the rendered CoCo preview comparison remain open.
- [ ] **V03 — Continuous progression:** Add an uninterrupted automated KQ1 route
  from a fresh start to ending, exercising resource changes and accumulated
  state. Extend progression scenarios to each supported title or record an
  explicit unverified exception. Injected quest checkpoints alone do not pass
  this gate.
- [ ] **V04 — Terminal stress and failure cleanup:** Repeatedly start/switch/exit
  two different games; exercise modal UI, audio, save/restore, occupied-terminal
  rejection, interruption and allocation/driver failures. Surviving instances
  keep input/display/audio/state and final memory/module/path ownership balances.
  On 2026-11-08, the original Larry/KQ1 MAME pair was extended to exit and
  relaunch KQ1 twice in Larry's presence. The second KQ1 opening frame matches
  the first launch, Larry's scene remains intact across the second exit, both
  KQ1 exits return to the exact Larry-only memory map, and the final Larry exit
  restores the initial free-memory map: it is 848 KiB before the pair and
  after both games exit, and 560 KiB while Larry alone is resident after each
  KQ1 exit. The run passes with the compatible Wild Bits image and expanded
  `krnp2`; captures are in
  `/private/tmp/wildbits-larry-kq1-repeat-20261108-r8`. This adds repeated
  launch/exit coverage for one game in a two-title pair. V04 remains open for
  the other game's repeat cycle, modal/audio/save stress, occupied-terminal
  rejection, and allocation/driver failure cleanup.
- [ ] **V05 — Performance:** Measure comparable movement/cycle, room-load,
  redraw, modal and sound workloads with specified emulator CPU/driver settings.
  Compare default and custom-priority paths and inactive terminals. Agree on
  acceptable differences before closing; bounded arithmetic and working motion
  are not measurements of parity or zero performance overhead.
- **Current Wild Bits baseline, 2026-11-06:** The complete original Larry
  `--larry --profile` MAME scenario passes with current production modules and
  records 43 cycles at 12.5875 MHz E-clock; the 400-frame walk covers 20.52 AGI
  pixels. Median logic-to-cycle, object update, composition, picture
  presentation, and text/post-cycle intervals are 27.371, 37.240, 113.912,
  55.006 and 74.268 ms respectively; the clock gate is 0.412 ms. Exact settings,
  module hashes and capture path are in
  [the current profile record](WILDBITS-ENGINE.md#current-wild-bits-performance-profile-rerun-2026-11-06).
  This is a fresh Wild Bits baseline only. A matched CoCo 3 run, custom-priority
  path, room-load/modal/sound workloads, and inactive-terminal comparison are
  still missing, as are agreed acceptance thresholds. V05 remains open.
- [ ] **V06 — Physical Wild Bits:** Record hardware/FPGA/NitrOS-9/driver versions
  and repeat movement, dialogs, audio, terminal switching, persistence and exit
  acceptance on the user's multiple-terminal target. Emulator success alone
  does not close this hardware gate.

## Execution order and completion rule

1. C13 and S01–S08: finish command-level semantic evidence and differential
   behavior comparisons.
2. V02–V05: add continuous progression, terminal stress and matched performance
   evidence.
3. Keep A01's fixed code/data budgets, stack guards and ABI checks passing as
   parity fixes land; A02–A04 are verified.
4. V06 remains the physical-hardware acceptance gate.

Maintain this file after each verified change. For grouped command rows, record
individual results before checking the group. Newly discovered defects belong
under the relevant existing gate with a reproducer; add a gate only when it
represents a distinct missing requirement.

**Parity is complete when every open gate is closed, or a specific difference is
explicitly accepted and documented by the user.** Do not convert unsupported
commands to success-only routes, reduce test scope, or redefine parity to mark
this checklist complete. Until then report closed gates and concrete blockers,
not a completion percentage or an unsupported delivery date.


## Formatter parity status

The earlier formatter gap report is stale for the current source: recursive
string-slot expansion, unknown two-byte escape handling, modulo-256 indices,
missing numeric operands and decimal-width wrapping are implemented in the
Wild Bits formatter. On 2026-10-19, `tests/check_decimal_index.py` passed 548
actual CoCo/native formatter comparisons and 4,094 index/formatter calls. The
formatter comparisons include 16 unknown-escape spellings extracted from
the audited original message resources, without copying game prose into test
output.
The test added a terminal-percent case after first reproducing a mismatch: CoCo
returns successfully with empty output, while Wild Bits previously returned
`E$BMode`. The native formatter now returns through its normal successful
completion path. `check_wbplay.py` now loads the actual Space Quest II logic 82
`%m` message and Space Quest I logic 0 `%s` message, then compares each rendered
frame to its literal-text control. The two original missing-operand sites now
have loaded native behavior coverage. The direct CoCo/native formatter matrix
also reruns missing-operand `%s` with both owners' slot zero explicitly empty,
matching the Space Quest I case; all 548 comparisons and 4,094 index/formatter
calls pass. An additional direct call runs the original Space Quest II logic 82
message table and `%m` text through both formatter implementations. With the
CoCo lookup target at the message-section boundary initialized to zero, both
render the same literal suffix. With `Adjacent\0` at that same address, CoCo
prepends `Adjacent`; Wild Bits still renders only the suffix because its
missing index produces a bounded empty expansion. CoCo also retains carry set
after its missing-index report while Wild Bits returns success. This confirms
CoCo reads beyond the resource boundary; accepting the safe native behavior
and return-status difference remains a policy decision. The suite also covers
nested local/global expansion, object names, plain/LZW logic-zero loads and
caller restoration. It corrupts an offset in the original message table too:
CoCo formats `Adjacent!` from beyond the declared section, while Wild Bits
returns `E$BMode` and restores its stack, formatter depth, resource bytes and
guards. A declared section length that ends before the offset table is also
rejected safely by Wild Bits, while CoCo follows the retained offset and
formats the original first message. A 2,211-byte, newline-delimited output is
fully emitted by CoCo; Wild Bits returns `E$BMode` at the 2,048th byte after
writing the exact 2,047-byte prefix and NUL, with stack/depth/guards intact. An
unterminated first message bounded exactly before its missing NUL is rejected
by Wild Bits with depth, stack, private memory and resource guards restored;
CoCo scans through a controlled adjacent byte to its NUL and renders the text.

S05 remains open. The current original-resource audit still reports 18
unusual format sites in six titles; 16 unknown-escape spellings now have direct
CoCo/native differential coverage. Both original messages have loaded native
literal-control coverage; the Space Quest I missing-operand `%s` also compares
through both direct formatters with empty slot zero. The original Space Quest II
`%m` table has direct CoCo/native comparisons, but its CoCo carry status and
access beyond the message section remain different/unsafe. The
message-zero policy, explicit acceptance of the 2,047-byte output limit
relative to CoCo, the unterminated-string policy and other malformed-resource
cleanup paths still need resolution.
The original Space Quest II `%m` table has direct CoCo/native comparisons with
both zero and nonzero adjacent bytes. CoCo's zero-index lookup consumes
`Adjacent` beyond the resource boundary and leaves carry set; Wild Bits returns
a bounded empty expansion with carry clear. Out-of-range offsets and a declared
section ending before the offset table are covered. The 2,047-byte output cap
differs from CoCo's unbounded formatter. Unterminated strings also differ:
CoCo reads past the declared message section until its controlled adjacent
NUL, while Wild Bits rejects at the bound with intact cleanup. Both policies
and other malformed-resource behavior still need explicit acceptance or
further reference coverage.
Do not use the earlier isolated candidate logs as evidence for the current
implementation.

On 2026-10-19, `tests/check_decimal_index.py` added seven real CoCo/native
recursive string-slot chains, from no nested substitution through six nested
substitutions. CoCo renders all seven as `leaf`. Wild Bits renders chains with
one top-level plus two recursive `%s` substitutions (four active formatter
frames), then returns `E$BMode` for deeper chains. The depth counter returns
to zero and the stack, frame guards and linked code remain intact on success
and error paths.
This verifies the native recursion bound and cleanup; the semantic difference
from CoCo's unbounded recursion still needs explicit acceptance before S05 can
close.

C07/S06 must account for the menu representation: CoCo uses its menu-bar and
selection machinery, while the existing native backend presents a paged list.
Existing selection/cleanup tests do not by themselves establish identical
visibility rules or navigation behavior.

## Hardware availability

The user confirmed emulator-only testing on 2026-10-15. V06 remains open; this
is not an accepted waiver of physical-hardware parity. Continue all independent
software/emulator work and report that gate separately when it is the remaining
external dependency.


## Bundled-title audit inventory (2026-10-15)

All 14 resource sets parse in report mode. V01 is closed as a static inventory: every
ignored/unsupported command site is classified, dynamic targets remain explicitly
unresolved, and overlaps are reported with byte offsets. This does not establish
playability or close runtime destination coverage under S02/V02/V03. Reproduce:

```sh
python3 sierra/tests/audit_game_scripts.py --self-test --all-games \
  --output-dir /tmp/sierra-parity-audits
```

Full per-logic JSON is retained under
`.wildbits-test/parity-classified-audit-20261015` with validation log
`/tmp/sierra-parity-classified-audit.log`. Each report includes every logic's dynamic
calls/rooms and the unresolved sites in the directly reachable root graph.

| Title | Logics | Instructions | Unsupported sites | Ignored CoCo-stub sites | Formatter findings | Dynamic sites from direct root graph | Overlapping bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| blackcauldron | 85 | 10560 | 6 | 0 | 0 | 6 | 0 |
| christmas86 | 26 | 2837 | 5 | 0 | 0 | 2 | 0 |
| goldrush | 184 | 49898 | 6 | 0 | 1 | 4 | 0 |
| kingsquest1 | 90 | 11413 | 3 | 4 | 0 | 2 | 0 |
| kingsquest2 | 133 | 11676 | 4 | 4 | 1 | 8 | 0 |
| kingsquest3 | 132 | 20564 | 0 | 88 | 0 | 17 | 0 |
| kingsquest4 | 178 | 33465 | 6 | 12 | 0 | 5 | 0 |
| leisuresuitlarry | 52 | 12128 | 4 | 0 | 0 | 5 | 0 |
| manhunter1 | 66 | 30945 | 0 | 16 | 0 | 13 | 3 |
| manhunter2 | 96 | 36507 | 0 | 61 | 0 | 14 | 0 |
| policequest1 | 122 | 26106 | 6 | 15 | 3 | 15 | 0 |
| spacequest0 | 82 | 17961 | 5 | 10 | 9 | 5 | 0 |
| spacequest1 | 106 | 16401 | 4 | 4 | 2 | 2 | 0 |
| spacequest2 | 118 | 19844 | 6 | 2 | 2 | 3 | 0 |

The unsupported sites in this inventory use only opcodes 29, 133, 135 and 150
(11, 21, 15 and 8 sites respectively). The other three unsupported routes remain
strict-parity requirements even though this static scan finds no reachable use.
Zero missing sites for KQ3 or Manhunter is not a gameplay equivalence claim.

Manhunter I logic 159 contains a jump at byte 245 to byte 443, inside a conditional
instruction beginning at 438. Bytes 443..445 have two instruction interpretations.
The auditor previously rejected any overlap. Report mode now retains both
bounded decodings and reports the three overlapping bytes explicitly; strict
`analyze` mode still rejects overlap. Invalid/truncated predicates and out-of-range
branches remain errors in both modes. The actual original resource is decoded
and executed through both CoCo and native logic executors for the jump,
conditional true and conditional false entries. The test changes only a
post-path terminator, then checks variables and normalized instruction cursors
at two code bases. This verifies both interpretations rather than assuming the
resource is malformed or silently ignoring the finding. It does not prove
Manhunter's complete control flow or puzzles.

The current formatter inventory contains 18 findings across six titles:
unknown two-byte escapes (including punctuation) and two missing operands.
Their byte locations and classifications are in the per-title audit reports.
The direct CoCo/native matrix now covers the corresponding escape and numeric
operand policies, but S05 still requires resource-context comparison for the
original sites and decisions for zero-message, recursion and failure bounds.


### Additional focused evidence, refreshed 2026-10-19

The formatter/predicate comparison results and the bounded reference-transport
retry policy are recorded in
[engine validation](WILDBITS-ENGINE.md#formatter-and-constant-true-predicate-parity).
548 direct formatter comparisons (including 16 original-resource escape
samples), 4,094 index/formatter cases and 192 executor executions pass. S01 and
S05 remain open: these results cover specific boundaries,
not their complete acceptance scope. Message index zero is safely normalized to
empty; recursion and malformed-resource policies still require final decisions.

The user confirmed emulator-only availability. V06 physical-hardware acceptance
remains unchecked and has not been waived. Independent software work continues.


### Capacity-provider evidence, 2026-10-15

The ABI-8 UI/persistence split, byte budgets, loader safety checks and matching
64-owner/MAME evidence are recorded in
[engine validation](WILDBITS-ENGINE.md#separate-ui-and-persistence-providers-abi-8).
It creates 3,108 UI bytes of headroom; A01 remained open for the complete
remaining feature set at that 2026-10-15 checkpoint. A01 was closed after
C01–C07 were implemented within the fixed budgets; see the current gate result
above. The preceding ABI-7 complete 58-command target passed.
The matching ABI-8 complete target is running, so A04 remains open.


### Object-status evidence, 2026-10-15

C02 is verified by the shared CoCo/native command and formatter, 400 direct
comparisons, 84 numeric and eight guarded failure cases, loaded-script modal
and maximum-nesting tests, and two-terminal real-driver MAME acceptance.
See [the complete interface and evidence record](WILDBITS-ENGINE.md#shared-object-status-diagnostic-abi-9).
Current package ABI is 9; current UI size is 5,897 bytes. C03–C07 and the
matching complete-regression gate remain open.


### Native memory evidence, 2026-10-15

C03 is verified using explicit native memory categories, 32 guarded direct
reports, four failure cases, loaded-script/deep-nesting tests and all five
real-driver MAME phases. The callback extension preserves priority-wait layout
with assembly-time checks. See [the mapping and complete evidence](WILDBITS-ENGINE.md#native-memory-diagnostic-and-callback-layout-contract-abi-10).
Current package ABI is 10; UI size is 6,219 bytes and resident size is 23,805.
C04–C07, the latest complete-regression target and physical acceptance remain open.

The frozen ABI-8 capacity revision `63679fa` has also completed all 58 standard
checks with exit status 0 (`/tmp/sierra-capacity-complete-check-20261015.log`).
This is baseline evidence; A04 still requires the latest revision to finish.


### Menu visibility evidence, 2026-10-15

C07 passes 2,570 actual reference/native calls, loaded scripts, deepest nesting
and path tests, and all six real-driver MAME phases including visibility and
restored-game-state snapshots. See [the complete lifetime/input contract](WILDBITS-ENGINE.md#menu-visibility-and-input-permission-abi-11).
Current ABI is 11, UI size 6,265 and private extent 24,470 bytes. The latest
complete 58-command run remains pending. The packed-picture test now compiles
its own CoCo reference and passes all 443 pictures from a clean workbench.


### Reopened menu ordering gap, 2026-10-15

The earlier setter/lifetime/MAME cases pass, but do not prove full C07 input
ordering. An actual-executor counterexample now establishes the remaining gap:
CoCo executes `menu_input`, then hide-menu and a following assignment, before
its next event loop clears the hidden request without selecting anything.
Native displays the menu before that hide/assignment and publishes a selection.
Evidence: `/tmp/sierra-menu-queue-counterexample.log` and the controlled runner
`/tmp/sierra-menu-queue-counterexample.py`. C07 is reopened; S06 remains open.
The next migration must share the request policy and queue native menu display
at the corresponding cycle boundary, preserving controller/input ownership.


## Deferred-menu correction (ABI 12)

The ordering counterexample above is fixed and preserved as an actual CoCo
executor/event-loop regression. C07 is reclosed with request-time flag-14 checks,
event-time visibility, late hiding/showing, permission revocation, duplicate
request coalescing, controller delivery, default/module lifetime, room/restore,
two terminals and memory recovery verified. S06's broader interactions stay open.
Rare UI commands now share a private loader/cache; a mixed-command test caught
and fixed a framebuffer/resource mapping ownership error. The final 64-owner
matrix leaves all 56 CoCo binaries unchanged. See the
[ABI-12 implementation and verification record](WILDBITS-ENGINE.md#deferred-menu-requests-and-shared-ui-entry-abi-12).

The ABI-11 complete run stopped on a debugger disconnect in static painting;
its isolated 52-case rerun passes. The first ABI-12 full run failed a stale
independent dispatch-test expectation. The corrected frozen run and later
complete revisions are recorded under A04 above. Trace C04/C05 and save-name
C06 are now closed; C13 and the remaining unchecked gates stay open.


## Automatic save naming and overwrite correction (ABI 13)

C06 is verified. The actual CoCo command takes a string index, despite its
misleading slot-index comment; the command rule and bounded copy are shared.
Native maps the selected name to its filename/path interface, with an explicit
12-string bound and 31-character-plus-NUL buffer. Empty names restore manual
input. The setting persists independently of source strings and logical saves.

344 actual command comparisons, loaded/deep staging, actual restart/save-write
scope, 64 create/delete/error comparisons and all eight real-driver MAME phases
pass. The new cold alias-restore/subsequent-save test found and fixed a real
existing-file creation bug: native now follows CoCo delete-before-create.
All 64 builds pass, with 56 CoCo/five probe images unchanged, and all 14 title
audits pass. Only 149/150 remain unsupported. The matching full target is still
running; A04 and broader S08 coverage remain open. See the
[ABI-13 contracts and evidence](WILDBITS-ENGINE.md#shared-automatic-save-naming-and-replacement-abi-13).


## CPU deadline correction

The recurring debugger EOF was reproduced as a normal XRoar exit at its
emulated-time cutoff. start_cpu now uses a real-time watchdog, retaining emulator diagnostics and
all response/call/loop bounds. The paused-target watchdog check and three
consecutive gameplay batches pass. No product code or ABI changes.
The ABI-12 failed run and superseded initial ABI-13 run are not complete passes.
The corrected frozen revision `33c079d` completed all 58 check commands with
exit status 0. This verifies the current baseline; A04 remains open for the
final product revision after the remaining feature gates. See
[the cause and verification record](WILDBITS-ENGINE.md#cpu-fixture-deadlines-and-disconnect-evidence).


## Available verification target

The user confirmed that testing is emulator-only for now. Continue CPU and
MAME verification independently; V06 remains unverified because no physical
Wild Bits board is available. This is a testing constraint, not a waiver or
a claim of hardware parity.


## Trace reference and native acceptance (2026-10-17)

The shared trace scheduling/configuration rules now preserve every CoCo image
byte for byte. `check_trace.py` verifies actual relocated CoCo controls, dispatch,
input transitions and formatted transcripts, including cached name lookup.
All 64 owner images matched the verified ABI-13 baseline at the reference
contract stage. The ABI-14 native backend has since passed C04/C05; see the
[trace reference evidence](WILDBITS-ENGINE.md#trace-reference-contract-and-shared-scheduling).


## Packed catalog groundwork

Shared paired-nibble emission preserves the native VM decoding bytes and all
CoCo images while reducing `wbui` by 77 bytes. All 364 actual UI selections,
1,024 VM routes, targeted loaded-provider/cache/shake/preview/save-name checks,
and 128 before/after builds pass. The trace commands are now enabled and pass
the loaded VM/provider and real-driver MAME checks. All eight matching MAME phases pass. The complete 59-check
target passes all 59 commands uninterrupted on frozen `f1a52a3` with exit
status 0 on the final trace revision as recorded above. See the
[catalog contract and evidence](WILDBITS-ENGINE.md#shared-packed-catalog-emission).

## Historical integrated check and audit (2026-11-06)

Every command in `objs/wildbits.mk`'s `check` target passed on the current
worktree. The target first stopped at an obsolete `check_wbplay.py` fixture
that used reversed `word.to.string` operands; after correcting that fixture,
`check_wbplay.py` and every remaining target command passed in sequence. The
refreshed all-title audit and its self-test also pass: 14 titles, 1,470 logics,
300,305 instructions and zero unsupported opcodes. Current module budgets are
`wbgame` 23,808/23,808 bytes, `wbui` 8,116/8,192 and `wbstate` 3,193/8,192.
This confirms the current software regression set; it does not close the 39
open command rows, gameplay/runtime gates, or emulator-only hardware gate. The
refreshed report was in `../.wildbits-test/audit-20261106-full-check-rerun`.

## Current parity and MAME verification (2026-11-07)

The Wild Bits-only opcode-110 screen-shake implementation was removed because
the CoCo handler is a no-op. Its former UI helper slot now contains a single
`rts`, and four private bytes were reclaimed. `wbgame`, `wbui` and `wbstate`
rebuild at 23,806/23,808, 7,035/8,192 and 3,193/8,192 bytes respectively.
The interpreter, full 1,024-route dispatch, CoCo/native logic, audio, resource,
UI/state, and loaded-game regression sets pass. The initial `make check` run
stopped at the now-corrected `check_ui_command_cache` expectation; the corrected
`check_wbgame.py` and every remaining Makefile check were then run separately
and passed. This documents coverage without claiming one uninterrupted Make
invocation.

The MAME `--movement` acceptance run passed using the persistent Wild Bits
environment (`mame` commit `078e0eeb`, OS `f99a8196`, expanded kernel and
SOLdrv), rebuilt modules, and original KQ1 resources. It measured about 21.5
AGI pixels over 200 frames and passed startup, inventory/modal restoration,
interrupt cleanup and free-memory checks. Artifacts are in
`../.wildbits-test/kq1-movement-opcode110-20261107-expanded`.

The refreshed all-title audit covers 14 games, 1,470 logics and 300,305
instructions with zero unsupported opcodes. After the add-to-picture,
`set.key`, resident `load.logics` cache-hit/replay, `set.game.id`, `stop.sound`,
`load.sound`, `sound`, and menu construction comparisons, the manifest records
168 of 182 commands with scoped evidence, 14 open command rows
and results for all 19 predicates; all 13 S04
command rows have focused evidence, while the broader S04 family and physical
hardware gate remain open. The updated report, including the sound and menu
command results, is `../.wildbits-test/audit-20261107-menu-build`. The all-title audit is inventory
evidence, not runtime gameplay equivalence.
The resident logic-load, key-binding and game-ID focused scripts are now part
of `objs/wildbits.mk`'s `check` target; all three passed individually after the
production modules were rebuilt.

#### S05 literal and variable print checkpoint (2026-11-07)

`check_text_command_entry.py` calls the actual CoCo `cmd_print`, `cmd_print_v`,
`cmd_print_at`, `cmd_print_at_v`, `cmd_display` and `cmd_display_v` handlers at
two code bases. It checks literal versus variable message selection, the exact
string pointer passed to `message_box`, positioned row/column/height, reset of
those overrides, display text and row/column passed to `PrintFmtStrToScr`,
operand consumption, return flow and stack guards. The loaded-game tests
exercise both native print forms, including positioned cell output, wrapping,
clipping, invalid coordinates, timeout and dismissal. They also compare exact
literal and variable display glyph pixels, including a row boundary and
persistence through `show.pic`. The KQ4 MAME scenario checks the original
game's centered popup, retained scenery and scene restoration after dismissal.
The audit manifest records these six commands with this scoped evidence.
Reproduce with
`python3 tests/check_text_command_entry.py`, `python3 tests/check_wbgame.py`,
and the KQ4 MAME popup scenario documented in [WILDBITS-MAME.md](WILDBITS-MAME.md).

At this print-only checkpoint, the refreshed manifest self-test and all-title
audit passed with 151 of 182 commands covered; one S05 command and 31 commands
overall remained open. It did not reduce the two open S04 rendered add-to-picture
comparisons.

The KQ4 MAME scenario was rerun against the current `wbgame`, `wbui`,
`wbstate` and `wbfont` artifacts in `/private/tmp/wildbits-kq4-print-checkpoint-20261107`.
It passed single-Space intro progression, gameplay, movement, the centered
`look` popup, menu/Inventory and scene restoration. The popup region had three
colors, and the scene retained 11 and 13 colors on its left and right sides;
the post-dismissal Rosella centroid matched the Inventory-restored centroid.
This is a real original-game visual check for popup behavior, not a CoCo
emulator pixel-for-pixel comparison.

The same current-module KQ4 run was repeated with `--persistence` on the
Wild Bits-aware `/Users/boisy/Projects/mame/mame` binary (the adjacent `mamed`
binary is CoCo-only). The KQ4-tagged save, scene change, restore, continued
original logic, restored popup and memory cleanup passed. The saved and
resaved room/ego values match; the state-apply snapshot restores the saved
variables, while only live animation fields advance afterward. This refreshes
one original-game persistence route and does not close V02's per-title matrix
or S08's broader field/failure requirements. Artifacts are under
`/private/tmp/wildbits-kq4-parity-mame-20261107`.

#### S05 parse command checkpoint (2026-11-07)

`check_parse_command.py` calls the actual CoCo `cmd_parse` with a 40-byte
string slot and an indexed `words.tok` fixture. It verifies the word-ID and
noun-pointer tables, found-word flags, parsed count, single-operand advance,
stack balance, and invalid slot 12 behavior. The native streaming parser is
covered by `check_wbparser.py`; loaded KQ1 scenarios in `check_wbgame.py`
exercise the original `get.string`/`parse`/`said` route with real game scripts,
including the fiddle encounter. The refreshed command inventory now has
152/182 rows with scoped command evidence (30 open), and no S05 opcode row is
open. This closes the parse command row only; broader S05 formatter, malformed
resource, and edge-case comparisons remain open. Reproduce with
`python3 tests/check_parse_command.py`, `python3 tests/check_wbparser.py`, and
`python3 tests/check_wbgame.py`.

#### S06 get.string checkpoint (2026-11-07)

`check_get_string.py` calls the CoCo `cmd_get_string` entry and checks its
five operands, target-slot clearing, cursor row/column handling, bounded length
passed to `EditString`, operand cursor and stack. For Wild Bits it runs the
actual `get.string` opcode through a rendered prompt and keyboard editor. Enter,
backspace, length limiting and Escape are checked against the destination slot;
the command line suspended before the modal prompt is restored afterward. The
coverage manifest now records 153/182 commands with scoped evidence (29 open),
with 15 open in S06. Reproduce with `python3 tests/check_get_string.py`.

#### S06 config.screen investigation (2026-11-07)

`check_screen_config.py` calls the actual CoCo command and Wild Bits
`ScreenConfigure` handler for seven legal boundary layouts. It checks operand
consumption, CoCo's derived right edge and line stride, its stored input/status
rows, and Wild Bits' layout writes. It now also executes CoCo's real
`MsgBoxColCalc` at both code bases for offsets 0 through 4 and checks the
resulting left column. The legal first operand is used in several places on
CoCo: it sets the pixel-buffer stride (`offset * 8 * 160`), shifts dialog
columns, adjusts menu-window height, and sets the trace-window top. Wild Bits
uses `vmpicturetop` for the corresponding eight-row vertical picture/trace
offset, and packs the dialog text-column offset into spare bits of its
status-enabled byte. Wild Bits' modal-preview check verifies all five text and
picture positions; `check_trace.py` verifies trace top at `offset + 2`. This
supports equivalence for those legal uses, but CoCo/Wild Bits menu geometry
still needs a paired display comparison. The second and third arguments
control input and status rows on both sides. Real KQ1/KQ3/KQ4 scripts use
`[1,22,0]`, `[1,22,0]`, and `[1,23,0]` respectively.

The probe also captures an unresolved malformed-input difference. CoCo accepts
out-of-range byte values and writes them to its fields; Wild Bits rejects
picture-top values above 4 and input/status rows above 24 without partially
publishing any setting. The production scripts use legal values, but malformed
input policy and menu geometry keep opcode 111 open. The test output explicitly
reports the invalid-range policy difference; matching stored bytes alone is
not a closure claim. Reproduce with
`python3 tests/check_screen_config.py`.

#### S06 `config.screen` horizontal text-offset implementation (2026-11-07)

Wild Bits now retains the CoCo first operand's horizontal message offset in the
unused high bits of its per-instance status-enabled byte. Status-line logic
uses only its low enable bit, and the status row remains valid in saved states.
The text helper applies the offset to active dialog cells and their backing
rectangle, while leaving unconfigured dialogs and the parser input row
unchanged. This keeps the offset private to each process and adds no bytes to
the size-capped `wbgame`.

`check_screen_config.py` passes 38 direct CoCo/Wild Bits command calls,
including guard bytes, unchanged operands, input/status rows, the packed offset,
and invalid-range policy. It switches between two private maps with different
offsets and confirms status on/off preserves each instance's value. The full
`check_wbgame.py` run passes its configured screen object-preview case, which
checks the shifted box and text plus exact
scene restoration, as well as the broader menu/status/modal/frame regressions.
The build remains `wbgame` 23,801/23,808 bytes and `wbui` 7,651/8,192 bytes.

Opcode 111 remains open: CoCo accepts malformed bytes that Wild Bits rejects,
and CoCo's first operand also participates in graphics/trace geometry while
Wild Bits retains its existing picture-top use. The first persistence rerun
also showed that storing the offset in the status-row byte made valid save
files fail validation; the final representation uses status-enabled's spare
bits, and the corrected save/restore rerun passes. Remaining layout semantics
need their own comparison before the checklist row can close. Reproduce with
`python3 tests/check_screen_config.py` and `python3 tests/check_wbgame.py`.

#### S06 `get.num` checkpoint (2026-11-07)

`check_get_number.py` invokes CoCo `CmdObjStatus` through its real command
entry, intercepts the prompt editor with known typed text, then continues
through CoCo's `AtoI` and variable write. It runs native opcode 118 through the
modal keyboard path as well. Both store the same values for blank input, `0`,
`255`, `256`, and `999` (including byte wrap for values above 255), and clear
modal input state with balanced stacks. This closes the command-level `get.num`
result cases; full editor-key and prompt-render parity remain in S06. Reproduce
with `python3 tests/check_get_number.py`. Regenerating the command manifest after
this checkpoint records 170 of 182 commands with scoped evidence; 12 remain
open (six in S06, four in S08, and two in S02). The remaining S06 command rows
are `config.screen`, `show.obj`, `init.joy`, `menu.input`, `show.obj.v`, and
`close.window`.

#### S06 `init.joy` behavior probe (2026-11-07)

`check_init_joy.py` runs the actual CoCo command at two load addresses. With
joystick support enabled, CoCo shows its prompt and waits for a button release;
Escape cancels enabling. When disabling, it skips the prompt. The test checks
the enabled/last-direction state, callback order, event-clear call, stack and
code path. The real Wild Bits Jr2 MAME probe
`check_wbgame_previews_mame.py --joystick` passes with the compatible boot and
graphics-driver pair documented above: the OS joystick service enables,
neutral samples poll, toggling off allows the caller to continue, and process
memory returns to baseline. Wild Bits does not show CoCo's prompt; it uses the
terminal driver's `SS.Joy` service and reports unavailable service instead.
This platform-specific initialization policy is accepted at command level in
the checkpoint below; identical prompt presentation is not claimed.
Artifacts: `/private/tmp/sierra-joystick-mame-compatible-20261107`.
Reproduce the CoCo command probe with `python3 tests/check_init_joy.py` and the
driver probe using the command recorded in that artifact's `command.json`.

#### S06 `init.joy` platform interface checkpoint (2026-11-07)

Opcode 139 has command-level coverage for both platform interfaces. CoCo's
actual `cmd_init_joy` prompts when enabling, accepts a button, cancels enable
on Escape, skips the prompt when disabling, clears events, and balances the
stack at two load addresses. The Wild Bits Jr2 MAME run exercises the real
`SS.Joy` driver path: enable succeeds, neutral samples poll, disabling lets the
caller continue, and process memory returns to baseline. Wild Bits reports an
unavailable joystick service instead of presenting CoCo's prompt when the
driver is absent. This is the accepted platform decision for initialization;
it does not claim matching prompt visuals or key legends.

The command manifest records opcode 139 as accepted with this policy. The S06
family remains open: `config.screen` still needs paired menu-geometry and
invalid-range policy evidence, and `show.obj` still needs full MMU integration.
Reproduce the CoCo probe with
`python3 tests/check_init_joy.py`; reproduce the Wild Bits probe with the
command stored in `/private/tmp/sierra-joystick-mame-compatible-20261107/command.json`.
After regenerating the manifest, 175 of 182 command rows have scoped evidence;
seven remain open: three S06 rows (`config.screen`, `show.obj`, and
`show.obj.v`) and four S08 rows (save, restore, restart, and quit behavior).
S02 command rows are all accepted, while the broader S02 family checklist
still requires its resource/replay matrix.

#### S06 `close.window` probe update (2026-11-07)

`check_persistent_window.py` runs CoCo's actual `cmd_close_window` with the
window-open flag set and clear, checking the erase callback, rectangle values,
MMU page, flag, stack and code guards at two code bases. It also runs actual
Wild Bits opcode 169 repeatedly after nonblocking print, modal dialogs, full
redraw and LZW workspace reuse; both the character/color plane and rendered
pixels return to their previous contents, and repeated close is harmless. The
CoCo erase callback is still stubbed, so these runs do not compare its rendered
output with Wild Bits. Opcode 169 therefore remains open pending that visible
comparison. Reproduce with `python3 tests/check_persistent_window.py`.

#### S06 submitted-menu construction lock (2026-11-07)

The CoCo `cmd_set_menu` and `cmd_set_menu_item` handlers check
`MenuSubmitted` and return before allocating or linking another entry. The
Wild Bits handlers previously continued to mutate their fixed menu arrays
after `submit.menu`. They now return through the shared successful-build exit
when `menuready` is set. The loaded-game regression runs actual opcodes 156,
157 and 158, then attempts another title and item before requesting input; at
the input boundary the submitted state remains one title and one item and the
script resumes normally. `MenuCommand` was placed beside the handlers to keep
the resident module within its 23,808-byte limit; `wbgame` now builds at
23,808/23,808 bytes. The complete `tests/check_wbgame.py` run passed after this
change, including the new `check_cold_menus` scenario, loaded original KQ1
quest chains and the existing rendering, input, UI, resource and cleanup
regressions. Reproduce with `make -f wildbits.mk all` and
`python3 tests/check_wbgame.py`.

This closes the specific post-submit mutation regression. At this checkpoint,
normal menu construction and item enable/disable had not yet been compared
directly with CoCo; later checkpoints record those results. Menu
selection/cancellation, paging and resource-failure behavior remain open where
the later tests do not cover them.

The audit manifest remains at 153/182 commands with command-level evidence;
this focused regression does not claim full equivalence for opcodes 156 or
157. After the change, `audit_game_scripts.py --self-test` and the all-title
scan passed for 14 titles, 1,470 logics and 300,305 instructions with zero
unsupported opcodes. The report is in
`../.wildbits-test/audit-20261107-menu-lock`.

#### S06 menu construction checkpoint (2026-11-07)

`check_menu_build_reference` executes the real CoCo `cmd_set_menu`,
`cmd_set_menu_item`, and `cmd_submit_menu` handlers at two code bases. Only
`GetMsgPtr` and `AllocDataBlock` are bounded test services; the CoCo handlers
build their actual circular title/item lists. A loaded Wild Bits logic runs
opcodes 156, 157 and 158 with the same five labels and three action codes. The
test normalizes both owners' records and checks the same two title groups,
ordered actions, labels and enabled states. Wild Bits then accepts Enter on the
first action and resumes the following script. This closes the basic
construction and submission state for opcodes 156, 157 and 158. The actual
CoCo menu renderer, full navigation/cancellation comparison, paging and
allocation/resource failure cases remain open under S06/V04.

The complete `python3 tests/check_wbgame.py` regression passed with this
comparison in its normal run path, including original KQ1 encounters, loaded
menu selection/cancellation/paging, visibility and cleanup cases.

#### S06 menu navigation and cancellation checkpoint (2026-11-07)

The CoCo `DrawMenuBar` event loop is run with only drawing and event services
stubbed. Its Up event from the first item selects the title's tail and Enter
publishes action 22; Down from that tail returns to the head and Enter publishes
action 21. A separate Right event advances to the next nonempty title and
selects its final item, publishing action 23. The loaded CoCo event-loop
fixture verifies these paths at two code bases and confirms Escape returns
without publishing an action. Wild Bits previously
treated K2's right-arrow byte (TAB, `$09`) as flat next-item
navigation and selected action 22. `GameMenuRight` now follows the item's
owner title, scans title groups with a bounded count, skips empty groups and
selects the next nonempty title's tail item, wrapping at the end. The loaded
Wild Bits script confirms Enter selects action 21 and TAB+Enter selects action
23, then resumes the following script.

K2's left-arrow key is reported as backspace (`$08`). `GameMenuLeft` follows
the selected item's owner title and selects that title's second item. Both
horizontal handlers now add the six-byte item offset after multiplying the
selected index; without this, selections beyond item zero read item zero's
owner. Loaded scripts cover left, right, Enter, and separately delivered left
on a one-item title (which stays on its only item).

The CoCo handler's Up event follows the previous-item link within the current
title. Wild Bits now applies that rule and a loaded K2 input case verifies Up
from the first item selects the title's last item. The actual CoCo event-loop
fixture also verifies Up then Down returns to the title's head. Wild Bits Down
previously advanced to the next flat item; it now resolves the selected item's
title and returns to that title's first item, matching CoCo. The disabled-first
item case now uses Up to wrap to the title tail, the CoCo route. The full
`python3 tests/check_wbgame.py` regression passes with the matching behavior.
Reproduce the focused cases through `check_menu_build_reference` and
`check_cold_menus` in that suite. Cancellation parity and menu drawing/allocation
failure comparisons also remain open under S06/V04. The self-test and refreshed
all-title audit pass at `../.wildbits-test/audit-20261107-menu-navigation`:
14 titles, 1,470 logics, 300,305 instructions, and zero unsupported opcodes.
This static audit does not close the remaining runtime menu/input cases.

#### S06 original-game dialog overlay rerun (2026-11-07)

The current modules pass both the original KQ1 king-dialog MAME probe and the
KQ4 movement/look/menu probe on Wild Bits Jr2. During KQ1's 2,000-frame held
king speech, the picture remains behind the text overlay (nine retained scene
colors); a fresh key dismisses the text and restores the scene, and free memory
matches before/after. In KQ4, the look window is centered over the river-meadow
scene: the captured popup has three colors while the uncovered scene retains
11 colors on the left and 13 on the right, and the image restores after
Inventory. These runs verify those specific dialog paths and do not close the
held/repeated/fresh-key matrix or CoCo popup-geometry comparison. Captures are
in `/private/tmp/wildbits-kq1-king-popup-20261107` and
`/private/tmp/wildbits-kq4-s06-popup-20261107`.

Reproduce with `tests/check_wbgame_mame.py --king-dialog` for KQ1 and
`tests/check_kq4_mame.py` for KQ4 using the documented Wild Bits Jr2 image,
firmware and OS/9 paths in `WILDBITS-MAME.md`.

#### S06 modal text color correction (2026-11-07)

The user reported that popup text made the Wild Bits picture appear to turn
white. `GamePrintText` had assigned black as the foreground and white as the
background, opposite both the renderer's packed-cell format (foreground in the
high nibble, background in the low nibble) and CoCo's `text_color(0,15)` white
on black setting. It now assigns foreground 15 and background 0, so character
background pixels no longer paint white over the scene. `check_wbgame.py`
checks those live colors at `GamePrintPositionReady` while executing original
KQ1 death-support messages for three score branches; the messages still
dismiss, resume the nested caller and clean up resources. The targeted actual
6809 regression passes. The full Wild Bits Jr2 MAME KQ4 scenario also passes:
one Space advances the intro, the fruit narration remains legible over the
logo artwork, the look popup is white on black with the scene retained, Rosella
moves, and the menu reaches Inventory and restores gameplay. Its title-group
navigation now uses two Right presses, matching the accepted CoCo behavior;
Down returns to the selected title's head and cannot traverse to Inventory.
The screenshots and command are in
`/private/tmp/wildbits-kq4-popup-color-menu-final-20261107`. This closes the
reported popup color defect on the emulator, not the full S06 modal/UI gate.

Reproduce with `make -f wildbits.mk wbgame` from `sierra/objs`, followed by
`check_original_death_messages` in `tests/check_wbgame.py`.
Reproduce the visual flow with `tests/check_kq4_mame.py` and the matching MAME,
disk and firmware paths in `WILDBITS-MAME.md`.

#### S06 interpreter information (2026-11-07)

The CoCo `CmdShowAgiInfo` handler passes `StrAgiVersion` to `message_box`:
`Adventure Game Interpreter`, followed by `Version 2.072`. Wild Bits had
replaced that version line with a Wild Bits attribution. `InterpreterInfo` now
matches the CoCo text. The actual CoCo handler is checked at two code bases for
its message pointer/string and return stack; loaded Wild Bits opcode 141 checks
the displayed text, dismissal, caller resume, held/timed-print state and a
16-call nested path. `check_interpreter_information` passes. This closes the
S06 opcode 141 command row; other S06 UI commands and full screen behavior
remain open. The checked-in command manifest now records this result; it has
154/182 commands with command-level evidence and 28 open rows. The regenerated
all-title audit passed for 14 games, 1,470 logics and 300,305 instructions
with zero unsupported opcodes at
`../.wildbits-test/audit-20261107-interpreter-info`.

#### S06 `show.obj` command-boundary comparison (2026-11-07)

The loaded Wild Bits preview test now includes literal view 4 and variable
view 13, both using the same `A fine treasure.` description. It checks the
preview pixels, popup text, full-scene restoration, held/timed print state and
resource cleanup. A paired CoCo check executes `cmd_show_obj` and
`cmd_show_obj_v` at two code bases against expanded KQ1 view 4 in the actual
view list. It runs `view_find`, `SetViewForObj`, `SetLoopHelper`, and
`SetCelHelper`, reaches `message_box`, consumes operands and restores the redraw
flag and stack. With reference heap space initialized, each handler also runs
through `AllocViewEntry` and issues the real MMU sequence at `$0701`. The MMU
renderer in that command-boundary test is stubbed. Real-resource raster evidence
is recorded in the 2026-11-08 checkpoint below; full hardware-renderer lifecycle
parity remains open.

#### S06 enable and disable menu items checkpoint (2026-11-07)

The menu reference comparison now runs the actual CoCo `cmd_enable_item` and
`cmd_disable_item` handlers beside Wild Bits `MenuCommand` at two code bases.
The fixtures contain duplicate action codes across two circular CoCo menu
lists and three equivalent Wild Bits entries. They verify ordered enable/disable
changes, duplicate matching, an absent action code, operand advancement, stack
guards, record guards and immutable code. The loaded-game menu test adds a
disable-then-enable path and confirms the re-enabled first item is selectable.
This closes opcodes 159 and 160 for item state and selection behavior;
construction, paging, cancellation and complete menu rendering remain open
under S06. The `close.window` CoCo erase-output limitation is documented in
the handler probe above; opcode 169 remains open.

Reproduce with `python3 tests/check_wbgame.py`.

#### S06 original KQ4 Inventory status checkpoint (2026-11-07)

The original KQ4 menu Inventory action was exercised in the CoCo 3 and Wild
Bits Jr2 MAME runs. On CoCo, the captured status page contains only black and
white pixels (120,912 white and 32,048 black); a fresh Space restores a
16-color game scene. On Wild Bits, the original menu action displays the exact
`You are carrying:`, `nothing`, and `Press a key to return to the game` lines
on an opaque black/white page; a fresh key restores the scene and Rosella's
position. Together these runs close opcode 124's original-game status-screen
and dismissal behavior. They are separately asserted captures, not a direct
pixel-for-pixel comparison: the CoCo capture uses its native 640x239 display,
while Wild Bits text is decoded at its 640x480 mode. This does not close the
broader modal input matrix under S06.

Reproduce the CoCo reference with `tests/check_coco_kq4_inventory_mame.py`
and the Wild Bits run with `tests/check_kq4_mame.py`. Current artifacts are at
`/private/tmp/coco-kq4-popup-parity-current-20261107` and
`/private/tmp/wildbits-kq4-s06-popup-20261107`.

#### S06 `close.window` handler probe (2026-11-07)

`check_persistent_window.py` now also calls the actual CoCo
`cmd_close_window` at two load addresses with the window flag both clear and
set. It checks the no-window fast path, the erase callback page and routine,
the rectangle words on the stack, window-flag clearing, caller stack and
immutable code. Its Wild Bits scenarios independently confirm full-frame
restoration after dismissal, harmless repeated close, and cleanup after
resource failures. The CoCo erase callback is stubbed to an RTS in this probe,
so it does not compare rendered CoCo pixels against the Wild Bits frame. Opcode
169 remains open pending that rendered CoCo reference; this test narrows the
remaining question to the erase output rather than command dispatch or its
callback contract.

Reproduce with `python3 tests/check_persistent_window.py`.

#### S06 close window rendered restoration checkpoint (2026-11-07)

The CoCo handler probe above stubs the low-memory erase callback, but the
original KQ4 MAME path now exercises a real `look` popup and dismissal. The
popup region is predominantly white and black while color artwork remains
visible around it; after Space, the same 16-color palette is visible and the
popup area is no longer a white dialog. Wild Bits' original-game modal tests
separately verify that fresh-key dismissal restores the rendered scene. This
closes opcode 169's visible dismissal/restoration behavior for these tested
paths; it does not claim pixel-for-pixel equivalence across the two graphics
systems or close the broader S06 modal matrix.

Reproduce the CoCo capture with `tests/check_coco_kq4_inventory_mame.py` and the
Wild Bits capture with `tests/check_kq4_mame.py`. The CoCo output is under
`/private/tmp/coco-kq4-close-window-20261107`; Wild Bits evidence is under
`/private/tmp/wildbits-kq4-s06-popup-20261107`.

#### S06 menu input request checkpoint (2026-11-07)

Opcode 161 (`menu.input`) now has command-level event-loop evidence. The actual
CoCo dispatcher confirms that the script continues through later commands
before the next menu event loop consumes the request. The loaded Wild Bits
path checks permission at request time, defers display until the script
finishes, and covers visible/hidden settings, room retention, item selection,
cancellation and caller continuation. Its two-title fixture compares the
actual CoCo and Wild Bits menu lists and navigation; Up wraps to the selected
title's last item, Down selects its first item, and left/right cross title
groups consistently. The cold-menu paging test confirms repeated Down stays on
the title's first item, matching the CoCo handler. This closes opcode 161's
scoped request, selection and cancellation behavior. Complete menu drawing,
modal behavior beyond the exercised cases, and S06 family parity remain open.

Reproduce with `python3 tests/check_wbgame.py`.

#### C13 manifest and all-title audit refresh (2026-11-07)

After adding the original KQ4 Inventory status-screen evidence for opcode 124,
the C13 manifest self-test and all-title audit pass in
`../.wildbits-test/audit-20261107-inventory-status`. The manifest has 182
command rows: 169 have scoped command-level evidence and 13 remain open (two
S02, seven S06, and four S08). All 19 predicate rows have focused evidence.
The audit parses 1,470 logics and 300,305 instructions across fourteen titles
with zero unsupported opcodes. This refresh does not close S01–S08 as families,
or V02–V06; command evidence and the static resource audit remain narrower
than complete runtime parity.

Reproduce with `python3 tests/audit_game_scripts.py --self-test` and
`python3 tests/audit_game_scripts.py --all-games --output-dir
../.wildbits-test/audit-20261107-inventory-status`.

#### C13 manifest and all-title audit refresh (2026-11-07, get.num)

After adding actual CoCo/native `get.num` result evidence, the manifest
self-test and fourteen-title audit pass in
`/private/tmp/sierra-audit-s06-verified-20261107`. The manifest records 170 of
182 commands with scoped evidence and 12 open (two S02, six S06, four S08);
all 19 predicates have focused evidence. The audit parses 1,470 logics and
300,305 instructions, with zero unsupported opcodes. The open command list
remains in `WILDBITS-COMMAND-COVERAGE.json`; this audit does not close S01–S08
or V02–V06 as families.

#### C13 manifest and all-title audit refresh (2026-11-07, menu and window)

After adding scoped CoCo/native evidence for opcodes 161 (`menu.input`) and 169
(`close.window`), the manifest self-test and fourteen-title audit pass in
`/private/tmp/sierra-audit-s06-close-window-20261107`. The manifest now records
172 of 182 commands with scoped evidence and 10 open (two S02, four S06 and
four S08); all 19 predicates have focused results. The audit covers 1,470
logics and 300,305 instructions with zero unsupported opcodes. This does not
close the S06 family or the remaining runtime parity gates.

Reproduce with `python3 tests/audit_game_scripts.py --self-test` and
`python3 tests/audit_game_scripts.py --all-games --output-dir
/private/tmp/sierra-audit-s06-close-window-20261107`.

#### Wild Bits native regression refresh (2026-11-07)

The `wildbits.mk check` run rebuilt the production owners and probes, then
passed the dispatch, VM, cache, audio, predicate, movement, resource, text/UI,
room-command, and integrated `check_wbgame.py` regressions. It stopped at a
`check_wbplay.py` menu fixture whose key sequence pressed Down back to the
disabled head item before Enter. The CoCo reference confirms Down returns to
that head item; the fixture now uses Up to wrap to the enabled tail item. The
same focused test also supplies Enter to dismiss the newly displayed missing-
logic dialog. `check_wbplay.py` then passed by itself, as did every remaining
target command: `check_wbexec`, `check_logic`, `check_wbasset`, paired volume
loading, 443 original packed pictures, priority and picture-stream checks, LZW,
resource bounds, and `check_wbpic.py`. Thus every command in the check target
passed across the run and its focused continuation; the full make target was
not rerun from its first command after correcting that fixture. Final rebuilt
sizes are `wbgame` 23,808/23,808 code bytes, `wbui` 7,358/8,192 and `wbasset`
1,968/32,000. This regression result does not close the remaining command or
runtime parity gates.

#### S08 quit-command comparison (2026-11-07)

`check_quit_command.py` invokes the real CoCo `cmd_quit` and Wild Bits
`GameQuitCommand` handlers at two code addresses. Enter selects quit, Escape
continues play, and the immediate operand exits without displaying a prompt on
both owners. The test checks the CoCo exit dispatch, consumed CoCo operand,
Wild Bits private `gamequit` state, caller stacks, guards and code immutability.
The native prompt now starts with the CoCo wording `Press ENTER to quit.` and
identifies Escape as the keep-playing key, which is the terminal equivalent of
CoCo's CTRL-BREAK. This is a deliberate platform-key mapping, not yet user
accepted; opcode 134 remains open until that mapping is accepted and full-game
exit cleanup is paired.

Reproduce with `python3 tests/check_quit_command.py`.

#### S08 CoCo restart cancellation checkpoint (2026-11-07)

`check_wbgame.py` invokes the actual CoCo `cmd_restart_game` handler at two
code addresses and stops at its real `message_box` call. The cancel case
checks the prompt text and returns the negative result through the real caller
stack, verifying that game flags, volume handles, menu module state, autosave
name, stack guards and code remain intact. The confirmed case continues
through the actual CoCo restart logic while replacing only heap/object/volume
and menu services with counted stubs. It verifies line cancellation, restart
service order, room-change flag, preserved score-display bits, cleared timer
and stack guards. This establishes both CoCo prompt branches for opcode 128;
it does not yet compare equivalent Wild Bits prompt outcomes and confirmed
restart state or cover nested/modal restart. Opcode 128 and the broader S08
persistence matrix remain open. Reproduce through
`check_coco_restart_cancel` in `tests/check_wbgame.py` (also called by the
integrated `check_wbgame.py` run).

#### S08 Wild Bits restart matrix refresh (2026-11-07)

The focused `check_restarts` run in `tests/check_wbgame.py` passed six real
loaded-game cases: confirm, ordinary cancellation, Escape cancellation,
automatic restart, manual restart at maximum logic depth, and maximum-depth
restart with a 127-byte directory path. Confirmed/automatic cases verify the
new root state, cleared caller data and key/string/object state; cancellation
cases verify the old caller's variables, flags, key queue and strings remain
live. A cold-module hook catches the real `AuxRestartCall` and reads the prompt
pointer at runtime for each manual case. A second hook captures the actual
40-column text plane at `AuxPrintWait`; the composed dialog text is
`ENTER restarts; ESC cancels.`. The CoCo check reads its different prompt at
the real `message_box` boundary. Wild Bits now sets a restart-specific modal
input mode: Enter confirms, physical Escape (`$05`) or AGI Escape (`$1B`)
cancels, and ordinary keys are ignored. The cancellation fixture sends `x`
before Escape and verifies the old gameplay state remains live; the confirm
fixture sends Enter and verifies restart. This matches CoCo's Enter/CTRL-BREAK
decision using Wild Bits' terminal Escape key. Every Wild Bits case checks
active sound exercise and private-font integrity. The same test checks invalid
restart-helper module headers and entry bounds. The actual KQ1 rock-death
scenario also passes with restart requested after the death-message/countdown
flow; it verifies player control remains withheld until restart and that the
death variables/flags clear afterward. Maximum-depth cases exercise restart
from nested callers. The normalized cancel/confirm outcomes now agree across
the two owners; their platform-specific prompt layouts and key legends remain
different. Opcode 128 and S08 remain open pending nested/modal field parity and
the broader persistence failure matrix.
Reproduce the focused matrix by calling
`check_restarts(d)` with the initialized CPU from `check_wbgame.py`.

#### Integrated game-owner regression rerun (2026-11-07)

`python3 tests/check_wbgame.py` passes end to end on the current build,
including the original KQ1 quest/death routes, timed and positioned text,
object previews, menus, input/palette/screen backends, restart and persistence,
picture/text composition, inventory, and ownership cleanup. The rerun also
exercises the CoCo restart comparison from the integrated entry point. Two
test-harness issues uncovered while restoring this coverage were corrected:
the packed white-on-black cell-color expectation is `$F0`, and the integrated
CoCo restart call now compiles and supplies its actual reference module and
symbol map. The targeted positioned-message matrix and the CoCo restart
comparison both pass independently as well. This refreshes regression
evidence; it does not close C13 or S01–S08 as full semantic families.

#### Full Wild Bits native regression target rerun (2026-11-07)

`make -f wildbits.mk check` completed with exit status 0 on the current
production engine and test suite. It passed the build-size checks, command and
predicate dispatch, VM and resource regressions, CoCo/native command
comparisons, the integrated `check_wbgame.py` and emulator-backed `check_wbplay.py`
scenarios, all 443 packed-picture comparisons, large-picture streaming, LZW,
priority, text-window persistence, and pixel/resource cleanup checks. The
expanded room-transition suite passed again independently after the full run;
it now also checks both CoCo volume-error dialog choices (Enter returns a null
resource; CTRL-BREAK requests the MMU exit). The full target was run before
that small test-only extension, so the combined latest verification is the
successful full target plus the successful focused room-transition rerun.
Neither run closes the still-open S01–S08 semantic families or V02–V06
acceptance gates.

#### KQ4 original-resource MAME rerun (2026-11-07)

Using `/Users/boisy/Projects/mame/mame` (the `wbjr2` build), the current
production modules passed `tests/check_kq4_mame.py` against the original KQ4
resources. The full no-persistence run passed one-Space intro progression,
gameplay entry, movement, look popup, Escape menu, Inventory and restored scene;
the popup retained the picture on both sides. With `--audio-trace`, the same
run observed original sound commands `(99,2,220)`, `(99,100,154)`,
`(99,101,154)`, `(99,102,154)` and 1,223 PSG writes owned by the game process.
The independent `--direction-trace` run sampled Rosella advancing in X with
direction 3, view 0, loop 0 of 5 while flag 20 was set. Captures and logs are
in `/tmp/sierra-kq4-full-audio-current-20261107` and
`/tmp/sierra-kq4-parity-current-20261107-rerun`.

The `--persistence --audio-trace` run also passes. It saves a 34,745-byte KQ4
state, changes the scene, restores, and reaches the original post-restore look
response. The restored variables at the state-apply return match the saved
file; the room and Rosella's X/Y position match exactly; all saved flags and
non-animation payload bytes match in a second save. The two changed animation
fields are live cel countdowns; four variables change later as the original
logic continues after restore. The trace records 1,175 owned PSG writes.
Reproduce from `tests/check_kq4_mame.py --persistence --audio-trace`; captures
are in `/tmp/sierra-kq4-persistence-verified-20261107`.

Two fixture defects were fixed to make this evidence valid: audio tracing now
clears only its own MAME breakpoints, preserving the later state checkpoint;
and the script uses the Wild Bits menu's Right/Up/Enter navigation, including
the disabled separator rows, rather than selecting the About item. The prompt
check now distinguishes the actual `File:` prompt from the menu. These focused
KQ4 results verify this title's exercised persistence path; they do not close
the broader S08 failure, cancellation, and multi-instance matrix.

The `config.screen` offset implementation was then checked against the same
original KQ4 resources. The no-persistence run passes with the popup at its
configured column, scene pixels visible at both margins, movement, menu,
Inventory, and restoration. The persistence plus audio-trace run also passes:
the 34,745-byte KQ4 save restores room/X/Y exactly, original look logic resumes,
the second save preserves all saved flags and non-animation payload, and 724
PSG writes are owned by the game process. The first offset-storage attempt
failed the saved-screen row validator because it packed bits into the row;
the final build stores offset in the high bits of `vmstatusenabled` and tests
only its low enable bit. Artifacts are in
`/private/tmp/wildbits-kq4-offset-rerun-20261107b` and
`/private/tmp/wildbits-kq4-offset-persistence-fixed-20261107`.

#### Full Wild Bits regression rerun after screen-offset and probe-boundary changes (2026-11-08)

`make -f wildbits.mk check` completed with exit status 0 on the current tree.
This fresh run rebuilt the production modules and probes, then passed the full
native regression target: all command/predicate and CoCo/native differential
suites, `check_wbgame.py`, `check_wbplay.py`, 443 packed-picture pixel
comparisons, 11 large streamed pictures, 228 LZW resources, priority and
text-window paths, and picture/resource cleanup. The configured screen-offset
case passed in both the direct configuration probe and rendered object-preview
integration. The run also confirmed the `wbexec` probe assembles within its
budget after game-only quit and room-error UI calls were guarded by
`GAME_PRESENTATION`; the standalone probe now propagates the room-load error
without a presentation dependency.

The command manifest still has seven open rows: opcodes 111 (`config.screen`),
129/162 (`show.obj`/`show.obj.v`), 125/126 (save/restore), 128 (restart), and
134 (quit). The new full regression is evidence for exercised paths, not a
closure of those unresolved command semantics or S01–S08 as families. The
physical V06 gate also remains open because testing is emulator-only. The next
work is to close these evidence gaps and the broader V02–V05 acceptance gates;
parity is not complete yet.

After this build, the original-resource KQ4 MAME gameplay route passed again
with a one-Space intro, measured rightward motion, retained-scene look popup,
menu/Inventory and scene restoration. Rosella moved from screen-X 487.1 to
143.9 in the standard run; look and Inventory each restored X=183.9. A second
current-build run with `--audio-trace --audio-wav` passed the exact four intro
sound-command sequence and observed 669 game-owned PSG writes. MAME's stereo
48 kHz WAV has a varying signal during the intro window (AC RMS 47.67,
peak-to-peak 231). Artifacts are in
`/private/tmp/wildbits-kq4-post-full-check-20261108b` and
`/private/tmp/wildbits-kq4-audio-post-full-check-20261108`. This confirms the
emulator audio path, not the host speaker volume or physical hardware.

The current-build KQ4 `--persistence --audio-trace` route passed too. Its
34,745-byte `KQ4` save was followed by 173,352 changed pixels; restore returned
room/X/Y exactly to `(26, 41, 127)`, retained every saved flag and every
non-animation payload byte, and resumed the original look logic. Animation
countdowns advanced as expected while logic continued. The MAME trace recorded
1,169 game-owned PSG writes. Artifacts are in
`/private/tmp/wildbits-kq4-persistence-post-full-check-20261108`.

The real-driver multi-terminal save test also passes on this build through
`check_wbpic_mame.py --native-game sierra/kingsquest4 --interpreter
--persistence`. It saves twice to the same filename while the save controller
is still active, changes a variable, restores the original pixels, rejects a
valid-CRC state with an invalid field count, a wrong-game ID, a bad checksum,
and a truncated state, then exits and relaunches both terminals with the
original free-memory map. An earlier
version scheduled the overwrite after the synthetic controller script had
finished and misreported the resulting generic error as a replacement failure;
the corrected timeline now tests overwrite immediately after the first save.
Artifacts are in
`/private/tmp/wildbits-multiterminal-state-negative-cases-20261108`.

#### S06 `config.screen` trace geometry comparison (2026-11-08)

`check_trace.py` now executes the actual CoCo command sequence
`config.screen`, `trace.info`, `trace.on` at two relocated code bases. For all
five legal first-operand values (0 through 4), it verifies that the trace
window starts at `picture-top + 2` with the configured eight rows. The test
also preserves the exhaustive byte-valued `trace.info` cases and trace
activation checks. `check_wbgame.py` runs the corresponding actual Wild Bits
logic sequence at all five values and verifies the same trace row boundaries,
event display, stepping, caller continuation and trace-page cleanup. Both
checks pass. This establishes the shared trace-geometry use of the operand for
these legal layouts; opcode 111 remains open for its broader screen-layout,
popup-offset and invalid-operand behavior differences documented above.

Reproduce with `python3 tests/check_trace.py` and
`python3 tests/check_wbgame.py`.

#### S06 `config.screen` all-offset modal preview checkpoint (2026-11-08)

The loaded `wbgame` preview integration now exercises all five legal first
operand values, 0 through 4. Each fixture applies `config.screen` before
drawing its picture, then opens `show.obj`. It checks the popup glyphs at the
configured horizontal text offset, the preview sprite at the corresponding
picture-top position, and exact full-frame restoration against a control run
with the same layout. The complete object-preview helper, including malformed
view-description cleanup and its CoCo `show.obj` reference cases, passes on
XRoar. It was rerun independently on 2026-11-08. Literal and variable Wild Bits
commands select views 4 and 13, show the expected descriptions and preview
pixels, restore the exact scene, preserve a previously cached view and clean up
malformed descriptions. The actual CoCo `cmd_show_obj` and `cmd_show_obj_v`
handlers also pass at two code bases against real expanded KQ1 view 4 data,
consuming operands, displaying its description, restoring the redraw flag and
preserving stack/code guards. The test runs actual view lookup and loop/cel
selection, then exercises `AllocViewEntry` and issues the MMU sequence: sprite
draw, priority render, screen draw, sprite erase and background redraw. Both
calls use position `(69,167)`; the cel is 21x22 and the MMU temporary buffer is
22x22 after its alignment adjustment. The MMU renderer in that command-boundary
test is stubbed. Reproduce with `python3 tests/check_wbgame.py
--object-previews-only`. The focused CoCo check also runs the
actual `view_find`, `SetViewForObj`, `SetLoopHelper`, and `SetCelHelper` code
against expanded KQ1 `viewDir/4`, with only `SetLogicPage` intercepted. It
resolves the first cel to resource offset `$001A` and verifies its `$15` by
`$16` (21 by 22) dimensions. This confirms the resource-table selection feeding
the renderer. It then runs CoCo's production `ObjBlit` over that cel and checks
all 22 rasterized rows against an independent RLE decoder, including untouched
guard pixels at both horizontal edges. Wild Bits' loaded `show.obj` path now
uses the same expanded KQ1 view 4 (only the description-offset field is changed
to point at a test string); its modal sprite pixels also match the independent
RLE oracle row by row. The test checks the description and exact scene
restoration. This is paired real-resource rendering evidence. The direct CoCo
`cmd_show_obj` MMU call itself still uses renderer stubs, so hardware-MMU
integration remains open and opcodes 129 and 162 stay open.

`check_screen_config.py` now executes CoCo's real `MsgBoxColCalc` after
`config.screen` at offsets 0 through 4, at both module addresses, and verifies
the dialog's actual left-column result. Together with the CoCo stride writes,
the Wild Bits modal-preview pixels, and the paired trace-top test, this confirms
the tested legal screen/text offsets. The expanded screen test also measures
the CoCo menu and invalid-byte behavior described below.
The expanded probe also calls CoCo's actual `CalcMenuItemGeometry` with visible
item counts 1, 4, 8 and 21, for all five legal `config.screen` offsets at both
module bases. Its verified height formula is
`((visible_items + 2 - offset) * 8 + 7) & 255`; row, width, column, and stack
guards also match. The probe additionally confirms CoCo accepts out-of-range
bytes and applies wrapped byte arithmetic; for example, offset 255 produces a
right edge of 20 and a 39,680-byte stride. Wild Bits rejects offset 5 and rows
25 atomically with `E$IllArg`, leaving its layout unchanged. The test now totals
94 calls: 76 CoCo command/helper cases and 18 Wild Bits owner cases. This records
CoCo's reference geometry, but does not establish paired
AGI dropdown-menu equivalence: Wild Bits' Escape game menu is a separate fixed
text-plane UI. Reproduce with `python3 tests/check_screen_config.py`.

This covers native modal rendering and restore, and the CoCo command-to-MMU
boundary plus paired real-resource renderer pixels. Opcodes 129 and 162 remain
open for the complete MMU-backed draw/priority/erase lifecycle comparison.
Opcode 111 remains open because its menu-window geometry has only been
measured on the CoCo reference; Wild Bits' Escape menu is a separate fixed
text-plane UI. CoCo accepts malformed bytes and applies wrapped arithmetic,
whereas Wild Bits rejects them atomically. These cases still need an explicit
platform policy and paired AGI menu behavior evidence.

#### Full native regression rerun after screen configuration probes (2026-11-08)

`python3 tests/check_wbgame.py` passes against the current worktree. The run
includes the original KQ1 loaded quest chains and endings, text and modal
restoration, object previews and real KQ1 cel rendering, menus/input/joystick,
screen and status behavior, room transitions, UI ownership, restart, save-name
and replacement failures, text/graphics modes, resources, and cleanup. The
focused CoCo `show.obj` handlers and `ObjBlit` pixel oracle also pass inside
this run, but their MMU draw/priority/erase services remain stubs at the command
boundary. This broad regression supports the current playable paths; it does
not close the open semantic checklist rows or emulator-versus-physical V06.
Reproduce with `python3 tests/check_wbgame.py`.

#### Current real-driver modal rerun (2026-11-08)

After rebuilding the release MAME target so it registered `wbjr2`,
`check_wbgame_previews_mame.py` passed graphics-mode item preview, text-mode
item preview and interpreter-information modes. The tests check the rendered
text-plane position, foreground/background colors, word wrapping, preview
pixels, keyboard dismissal, script continuation, full-frame restoration and
memory recovery. The interpreter-info source has two CR-separated strings;
the first wraps, producing three visible text rows. Outputs and reproduction
details are in [`WILDBITS-MAME.md`](WILDBITS-MAME.md#current-real-driver-modal-rerun--2026-11-08).
This verifies the generated modal fixtures with MAME's Wild Bits display
drivers; original-game-wide display parity and physical V06 remain open.

#### S08 exact state-write transfer checkpoint (2026-11-08)

`check_wbstate_transfer.py` invokes the assembled `wbstate` module's real
`StateWriteExact` routine and intercepts its OS-9 `I$Write` call. A full write
and a sequence of short writes complete with byte-exact source progression;
zero-byte and over-reported writes fail with `E$BMode`, and an OS-9 write error
is propagated. The test also enters the actual `StateBegin` save command. An
`I$Create` `E$Full` is returned unchanged without close/delete cleanup because
no file was opened. In a second case the header completes via a short-write
retry, then the first state block receives `E$Full`; `StateFail` requests close
for the created descriptor and delete for the exact incomplete filename, and
both cleanup services return success. The error is preserved, and the routine
returns with the caller stack, game ID and guard data intact. Since file
services are intercepted here, this verifies provider control flow; the
separate real-driver test covers filesystem operations. Full-disk presentation
through the complete user-facing save command remains open under S08.

Reproduce with `python3 tests/check_wbstate_transfer.py` from `sierra/`, or
`make -f wildbits.mk check` from `sierra/objs`.

#### S08 real-driver restore rejection checkpoint (2026-11-08)

The current-build two-terminal MAME persistence scenario uses the actual
Wild Bits Jr2 drivers and invokes restore through the running game. It rejects
a valid-CRC snapshot with an invalid field count, a wrong-game ID, a bad CRC,
and a truncated snapshot. Each rejection presents its error and leaves the
active picture unchanged. Both terminals then exit and relaunch with the
original free-memory map. This gives the restore command real-driver failure
and recovery evidence; CoCo error-dialog/resumed-state equivalence and the
remaining S08 cases are still open. Captures are documented in
[`WILDBITS-MAME.md`](WILDBITS-MAME.md).

#### C13 current all-title audit (2026-11-08)

`python3 tests/audit_game_scripts.py --all-games --output-dir
/private/tmp/wildbits-audit-current-20261108` completed against the current
worktree after refreshing the config.screen evidence.
It parsed 1,470 logics and 300,305 instructions across all 14 bundled titles,
reported zero unsupported opcodes, and matched the checked-in command manifest
(182 command rows and 19 predicate rows). The audit classifies 315 CoCo-ignored
operations, 18 formatter findings, 101 dynamic destinations and three
overlapping instruction bytes in Manhunter I logic 159. Predicate rows have
focused results. The command inventory gate C13 is now complete: the seven
still-open semantic comparisons (111, 125, 126, 128, 129, 134 and 162) each
retain focused evidence and an explicit unresolved condition. This static audit
does not close those runtime parity questions or S01–S08 and V02–V06.

#### S08 CoCo automatic restart and normalized outcome comparison (2026-11-08)

The actual CoCo `cmd_restart_game` fixture now also enters the automatic branch
with the real auto-restart flag set. It verifies that this branch bypasses
`message_box`, invokes the same reset services exactly once, sets the room
change bit, preserves score-display bits and module-owned menu/name fields,
clears the tick counter, resets the script pointer, and balances the caller
stack. The actual CoCo handler passes manual cancellation at two code bases,
manual confirmation, and automatic restart. Reset/loader services remain
instrumented stubs in this focused command test.

The loaded Wild Bits `check_restarts` matrix passes again alongside it: manual
confirm, ordinary and Escape cancellation, automatic restart, maximum nested
depth, and the maximum-length root path. The normalized outcomes agree for the
tested decisions: cancellation resumes the existing caller state; confirmation
or automatic mode unwinds to a fresh root, clears stale input/gameplay state,
and releases active sound/clock resources. The implementations intentionally
differ in timing: CoCo resets synchronously and Wild Bits applies restart at
the root VM safe point. Wild Bits uses terminal Escape where CoCo uses
CTRL-BREAK to continue.

The nested CoCo path now also runs actual root bytecode `call 1`, child
bytecode `restart.game`, the command dispatch, prompt return, and `ExecLogic`
unwinding. The harness confirms affirmative restart returns through the nested
frames without running the caller's next assignment, calls each reset service
once, sets the room-change bit, preserves score-display state, and returns with
root context, stack, and code guards intact. The external reset services are
still instrumented stubs.

Opcode 128 remains open because service side effects and the complete CoCo game
restart state have not been compared end to end. The remaining S08 saved-field
and persistence failure matrix is also open.

Reproduce with `check_coco_restart_cancel(d, coco, symbols)`,
`check_nested_coco_restart(d, coco, symbols)`, and `check_restarts(d)` from
`tests/check_wbgame.py`.

#### V04 repeated original-game terminal lifecycle (2026-11-08)

`check_wbgame_mame.py --larry-pair kingsquest1` now runs a second original KQ1
launch/exit while Larry remains resident. It compares the second KQ1 opening
frame with the first run, switches to Larry after KQ1 exits and verifies its
scene, compares the exact Larry-only free-memory report after each KQ1 exit,
then exits Larry and compares the final memory report with startup. The test
passed on the compatible MAME image; the full run and screenshots are in
`/private/tmp/wildbits-larry-kq1-repeat-20261108-r8`; its expanded kernel is
preserved at `/private/tmp/wildbits-larry-kq1-repeat-20261108-r7/krnp2`. V04
still needs modal/audio/save and failure-injection
stress, including allocation/driver failure cleanup.

#### Current KQ4 single-Space gameplay rerun (2026-11-08)

Using the rebuilt `wbjr2` release MAME binary, the original-resource KQ4
single-Space intro and gameplay scenario passes again. It verifies Rosella
movement, look, menu/Inventory and restored scene pixels. Screen X changes
from 487.1 to 147.9 during movement; look and Inventory restore X=187.9. The
look popup leaves varied scene colors visible on both sides. Captures are in
`/private/tmp/wildbits-kq4-current-parity-20261108`; reproduction is the
standard `tests/check_kq4_mame.py` command in [`WILDBITS-MAME.md`](WILDBITS-MAME.md#current-kq4-gameplay-rerun--2026-11-08).
The separate direction-trace run also passes: rightward movement advances
Rosella with direction 3, view 0 loop 0 of 5 and AGI flag 20 set; artifacts
are in `/private/tmp/wildbits-kq4-current-direction-20261108`.
This scripted path does not close the open save/restore/restart equivalence
rows, complete-adventure parity or physical V06.

#### Current complete Wild Bits build/check target (2026-11-08)

From `sierra/objs`, `make -f wildbits.mk check` completed with exit status 0
after rebuilding the current worktree. The current target contains 88 Python
check commands. Every command passed, including the full `check_wbgame.py`
original-game integration, all CoCo/native command and predicate comparisons,
443 packed-picture comparisons, 11 streamed-picture cases, 228 original KQ1
LZW resources, priority/static-addition/persistent-window checks, and final
actual-6809 framebuffer and cleanup checks. Rebuilt sizes are `wbgame`
23,801/23,808 bytes, `wbui` 7,659/8,192, and `wbstate` 3,193/8,192. SHA-256:
`f959fc42bca34bbf74fc3800f3e931a535a1240f5da30daf34389c928b04f350`
(`wbgame`), `17ea23d483ac5237db7dd4b34c3d2624f7e42827320b8c400fea3ed9948277a9`
(`wbui`), and
`94090b80a1c6beb26136bac18f23ec04b496fd62663746a88c6d074867956773`
(`wbstate`). The complete console transcript was not saved to a file; the
command is reproducible with `make -f wildbits.mk check`. This refreshes the
build/regression evidence, not the still-open semantic S-gates, V02–V06, or
the remaining seven command equivalence rows.

#### Current fourteen-title startup/exit matrix (2026-11-08)

The rebuilt modules pass `check_all_title_startup_mame.py` for all fourteen
bundled titles on the Wild Bits-aware `mame` binary. Every original-resource
game reaches a changed display, returns to the shell under the controlled
interrupt, and restores the starting free-memory report. Per-title captures
and the test image are in `/private/tmp/wildbits-all-title-current-20261108`.
This verifies startup/display/cleanup only; richer gameplay checkpoints remain
incomplete for V02, and uninterrupted progression remains open under V03. See
[`WILDBITS-CHECKPOINTS.md`](WILDBITS-CHECKPOINTS.md#current-all-title-startup-rerun-2026-11-08).

#### CoCo 3 and Wild Bits KQ4 modal-display comparison (2026-11-11)

The original CoCo 3 KQ4 capture harness passed on the installed CoCo-only MAME
build using the bundled CoCo 3 and disk-controller ROMs and both original KQ4
disks. Its output is in `/private/tmp/wildbits-coco-kq4-compare-20261111`.
CoCo output is 640x239: Inventory is a full-screen black-and-white view
(32,048 black and 120,912 white pixels), and a fresh Space restores the game
picture with all 16 palette colors. The ordinary `look` popup has both white
and black text/window pixels while the scene remains visible outside its
bounds; dismissal returns the scene's 16 colors. `look room` likewise leaves
scene colors visible at both screen edges.

The matching original-resource Wild Bits KQ4 run is captured at
`/private/tmp/wildbits-kq4-current-parity-20261108`. Its 640x480 Inventory
capture is also full-screen black-and-white (two colors), and dismissal
restores the 16-color game picture. Its ordinary and room-look captures retain
the scene around the text popup, with 15 colors in the complete popup frame and
16 after dismissal. This establishes matching high-level behavior for these
specific modal paths, not pixel-identical layout: the display heights and
drivers differ, and the Wild Bits popup palette is not the CoCo's white/black
window treatment. It does not close the wider S04/S06 presentation/input gates
or the rest of V02.

Reproduce the CoCo capture with `tests/check_coco_kq4_inventory_mame.py` and the
CoCo MAME binary/ROM set; reproduce Wild Bits with `tests/check_kq4_mame.py`
and the Wild Bits MAME/firmware setup in [`WILDBITS-MAME.md`](WILDBITS-MAME.md).

The Wild Bits KQ4 acceptance was rerun on 2026-11-11 against the current
`wbgame`, `wbstate`, and `wbui` modules. The original intro/gameplay/movement,
look popup, menu/Inventory and scene-restoration assertions pass. The save/
move/restore route saved a 34,745-byte state and returned room and Rosella
coordinates to `(26, 42, 127)`, then continued into original look logic. The
restore-apply variable boundary and flags/payload checks pass. Artifacts are at
`/private/tmp/wildbits-kq4-parity-20261111-r2`; this refresh covers those
scenarios only and leaves S08's full failure/equivalence matrix open.

The 94-call `check_screen_config.py` probe also passes against the current
worktree on 2026-11-13. It reconfirms all legal offsets, actual CoCo dialog and
menu-geometry helpers, both platform owners' input/status state, and the
intentional invalid-range policy difference. It still does not exercise a
paired AGI dropdown interaction: the Wild Bits Escape menu is a separate
terminal UI, so visible and selectable-menu equivalence remains open.

#### S06 AGI menu interaction regression rerun (2026-11-13)

The complete loaded `check_wbgame.py` regression passes against the current
worktree. Its menu cases construct the same two-title/three-item menu through
the CoCo commands and Wild Bits VM, compare normalized entries and action codes,
run CoCo's actual input loop for Up/Down/Right/Escape, then drive the loaded
Wild Bits path through Enter, cancel, Up/Down/Left/Right, and one-item wrap.
It also passes 2,580 actual menu visibility/request/input-gate calls and 28
actual enable/disable-item comparisons at two code bases. Selected actions and
caller/state guards agree for these cases.

This does not establish rendered-layout equivalence. The CoCo loop's drawing,
window, and event services are stubbed in this differential test, and its
`CalcMenuItemGeometry` is tested separately. Wild Bits displays its submitted
AGI menu as a terminal list rather than CoCo dropdown windows. The user-visible
layout difference and the relation to `config.screen` remain open under S06;
this result closes only the tested menu construction, selection, and visibility
semantics.

#### S06 Wild Bits menu rendering and KQ4 rerun (2026-11-16)

The Wild Bits AGI menu keeps its established `Game menu` heading, ordered
`Title: Item` rows, selected-item highlight, disabled-item dimming, and help
line. The list is drawn into bounded text rows while preserving the underlying
character/color cells outside those rows. The character-plus-color snapshot is
2,000 bytes; `copywordentry` counts words, so its correct count is 1,000. A
held dialog retains ownership of `resourcecommands`; while that dialog is active,
the menu returns without borrowing that workspace.

`python3 tests/check_wbgame.py --menu-only` passes construction, visibility,
input, paging, selected/disabled colors, all outside-cell preservation, invalid
menu handling and ownership cleanup. `python3 tests/check_wbgame.py
--menu-render-only` separately captures the first actual-6809 menu frame and
checks its text/color layout. The original-resource KQ4 MAME rerun passes the
single-Space intro, gameplay movement, look popup, menu/Inventory interaction
and scene restoration; its result and captures are in
`/private/tmp/wildbits-kq4-postmenu4-20261116`. Rosella moved from screen X
487.1 to 235.9, and the look and Inventory dismissals restored X=295.9. The
original KQ1 hall scenario also passes its scripted room entry and arrow-key
walking checks (`[310.5, 243.5]` X samples) with unchanged free memory, in
`/private/tmp/wildbits-kq1-hall-postmenu-20261116`. The king-dialog scenario
passes with the speech and glyphs visible over the throne graphics for 2,000
frames, then restores the scene on a fresh key and recovers memory; artifacts
are in `/private/tmp/wildbits-kq1-king-dialog-postmenu-20261116`. These checks
cover the reported menu, hall movement and held-dialog paths; they do not close
the wider S06 input/modal gate or the full S01–S08/V02–V06 parity checklist.

#### S06/S08 KQ1 menu, persistence and restart MAME rerun (2026-11-16)

The complete `python3 tests/check_wbgame.py` regression passes against the
current worktree, including the submitted-menu rendering and ownership cases.
The separate `--menu-render-only` 6809 capture also passes. The original-resource
KQ1 sustained-input run passes repeated `look`, an unknown-word response, the
real menu Pause selection, pause/resume and a subsequent command. It verifies
the centered white-on-black pause glyphs pixel by pixel while the castle remains
visible at both sides of the dialog; captures are in
`/private/tmp/wildbits-kq1-sustained-postmenu5-20261116`.

The actual KQ1 File Restore path now passes on original game resources: open
the menu, select Restore with its arrow controls, assert a standalone `File:`
filename prompt (rather than mistaking the menu's `File: Restore` label for that
prompt), load the saved file, return Graham to the saved screen position, issue
another `look room`, and verify the scene remains visible outside the text
window. The saved file's version, length and CRC validate, and the free-memory
map is unchanged. Graham's measured X positions are
`449.5 -> 625.5 -> 449.5 -> 449.5`; captures are in
`/private/tmp/wildbits-kq1-persistence-postfix-20261116`.

The original KQ1 File Restart path also passes in MAME. The test opens the
actual menu, selects Restart, requires the restart confirmation prompt, confirms
it, checks Graham returns to the initial X position, then verifies arrow input
works again and settles; the free-memory map is unchanged. Measured X positions
are `449.5 -> 581.5 -> 449.5 -> 581.5 -> 609.5 -> 609.5`. Captures are in
`/private/tmp/wildbits-kq1-restart-fixed-nav2-20261116`.

These runs verify the exercised native menu, sustained input, original KQ1 save,
restore and restart paths on the emulator. They do not close the remaining S01–S08
command-semantic families, complete-adventure coverage, terminal/driver matrix,
or physical-hardware V06 gate.

The same original KQ1 menu runner now also passes plain open/cancel and the
Video Mode action. Escape opens the menu, Escape cancels it, and both left/right
scene margins remain colored; see
`/private/tmp/wildbits-kq1-menu-open-cancel-fixed-20261116`. Video Mode is
selected using the actual title/item navigation, switches to CoCo RGB and back
to the standard palette, and leaves gameplay and free memory intact; captures
are in `/private/tmp/wildbits-kq1-video-menu-fixed-20261116`. These MAME checks
also correct prior test assumptions that Up traverses menu titles or that a
menu overlay should turn the whole screenshot grayscale.

The current production modules also passed the all-title startup/display/exit
matrix after these UI changes. All fourteen original-resource games reached a
changed screen, returned to the shell after the controlled interrupt, and
recovered their exact starting free-memory report. Artifacts are in
`/private/tmp/wildbits-all-title-startup-menu-refresh-20261116`. This is a
startup/cleanup regression check and does not fill the ten titles' gameplay
checkpoint gaps in V02.

The current modules also pass the controlled original KQ1 `--quest-chain
quest-save` route after these menu changes. Original room logic acquires the
treasures, transfers through the quest rooms, saves and restores the state, and
reaches the ending; the snapshot replay stream and zero checkpoint are checked,
and the free-memory map recovers at exit. Artifacts are in
`/private/tmp/wildbits-kq1-quest-save-current-20261116`. This adds another
real-save/restore integration check but remains controlled room transfer, so it
does not close V03's uninterrupted fresh-start progression gate. Details are
in [`WILDBITS-CHECKPOINTS.md`](WILDBITS-CHECKPOINTS.md#current-module-kq1-quest-save-rerun-2026-11-16).

#### Complete Wild Bits build/check rerun (2026-11-16)

`make -f wildbits.mk check` completed successfully against the current working
tree. The captured transcript is `/tmp/wildbits-full-check-20261116.log`; all
88 test commands completed, including the full native game integration,
paired CoCo/native VM, parser, object, clock, sound, picture and state tests,
the all-title resource audits, 443 packed pictures, 11 streamed pictures, 228
original KQ1 LZW resources, and final actual-6809 picture/cleanup assertions.
One reference-emulator launch timed out once and was retried successfully; the
reference comparison then passed. The rebuilt module sizes are `wbgame`
23,801/23,808, `wbui` 7,769/8,192, and `wbstate` 3,193/8,192 bytes. SHA-256:
`f959fc42bca34bbf74fc3800f3e931a535a1240f5da30daf34389c928b04f350`
(`wbgame`),
`9d43c022e0e83f1429cc0eaf3bd5c09f2461462d78d7dc8c3775d3545cc54ec3`
(`wbui`), and
`94090b80a1c6beb26136bac18f23ec04b496fd62663746a88c6d074867956773`
(`wbstate`). This confirms the current build and regression suite; it does not
close S01–S08 semantic parity, the remaining V02/V03 gameplay coverage, V04/V05
acceptance, or the emulator-only V06 hardware gate.

#### KQ3 visual/save-restore rerun on current modules (2026-11-16)

The original-resource single-game KQ3 MAME scenario passes with the modules
rebuilt by the complete target. It checks the clock, movement, the `look room`
dialog while game-picture pixels remain visible in the overlay's transparent
cells, dismissal and exact static-room restoration, save/change/restore player
position, planned exit and unchanged free memory. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq3-current-fullcheck-20261116e`.
The prior pixel oracle incorrectly chose text polarity from the majority color
of each cell; that misread dense zero glyphs. It also required the entire popup
rectangle to be grayscale, which contradicted the transparent-cell overlay.
The updated oracle infers polarity from clear font corners and checks visible
text, preserved picture colors within the popup and both scene margins. This is
a bounded KQ3 checkpoint, not complete KQ3 progression or a CoCo raster
comparison; V02 and V03 remain open.

#### KQ3/KQ1 repeated-launch terminal stress rerun (2026-11-16)

The original-resource `check_kq3_mame.py --pair-game kingsquest1 --stress-pair`
scenario passes on the current modules and expanded-memory kernel. It verifies
KQ3 save/restore and movement, KQ1 inventory on the other terminal, the first
KQ1 exit, a second KQ1 launch and exit, KQ3's timed move from the entry hall to
its upside-down bedroom sequence, a later KQ3 `look room` response, and the
planned KQ3 exit. After the second KQ1 exit, the process table contains just
the surviving KQ3 game process; 16 KiB remains unavailable as free memory while
that game is alive. When KQ3 exits, the exact initial 856 KiB free-memory map is
restored. The run does not claim intermediate free-map identity across the
survivor's timed room change. Captures, memory/process snapshots and MAME log
are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq3-kq1-stress-current-20261116f5`.
This extends V04 repeat-launch coverage; occupied-terminal rejection, injected
allocation/driver failures, and broader modal/audio stress remain open.

#### KQ4 gameplay, Help and audio rerun (2026-11-16)

The original-resource KQ4 MAME route passes against the current full-check
modules with `--help-screen --direction-trace --audio-trace --audio-wav`. It
advances the intro with one Space, moves Rosella right with direction 3/view 0/
loop 0 of 5 and AGI flag 20 set, checks the `look` popup and scene restoration,
opens/dismisses Sierra Help and Inventory, and exits with memory restored. The
driver log contains 2,338 game-owned PSG writes; the accepted stereo WAV is
48 kHz with 34,433,281 frames and nonzero samples. Captures are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq4-current-fullcheck-20261116`.
This is emulator evidence for the tested intro, movement, dialog, menu and
audio paths; full KQ4 progression and hardware audio remain open.

#### Larry Lefty's entrance rerun (2026-11-16)

The original-resource `leisuresuitlarry --larry-enter` MAME route passes against
the current modules. It completes the age quiz, accepts `open door`, transitions
into Lefty's, displays and dismisses an interior `look`, then exits with the
same free-memory map. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/larry-enter-current-fullcheck-20261116`.
This refreshes Larry's opening gameplay probe for V02; save/persistence,
broader puzzle paths and full progression remain open.

#### KQ4 original-menu persistence rerun (2026-11-16)

The original-resource `check_kq4_mame.py --persistence` scenario passed against
the current full-check modules. It opens the original File menu, saves the
KQ4-tagged 34,745-byte state, changes the scene, restores it, and compares the
saved room and ego X/Y fields through a second save. The save flags and
non-animation payload remain unchanged; animation fields and four live
variables advance after restore, and the restored game accepts the original
`look` command. The prompt/overlay capture also confirms the underlying scene
remains visible. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq4-persistence-current-fullcheck-20261116b`.
This closes one deterministic persistence route, not KQ4's full save-state,
puzzle, death, ending or V02 acceptance matrix.

#### KQ1 menu restart rerun on complete-check modules (2026-11-16)

The original-resource `check_wbgame_mame.py --game kingsquest1 --restart`
scenario passed against the current complete-check modules. Restart unwinds the
room-logic stack, resets the ego to the original root position, resumes arrow
input, stops on a second direction press, and exits with the original free
memory report. The measured X positions were 449.5 before restart, 581.5
before reset, 449.5 after reset, and 609.5 after resumed movement. Artifacts
are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-restart-current-fullcheck-20261116`.
This confirms one restart route, not uninterrupted KQ1 completion (V03).

#### KQ1 menu save/restore rerun on complete-check modules (2026-11-16)

The original-resource `check_wbgame_mame.py --game kingsquest1 --persistence`
scenario passed against the current modules. The File menu save prompt accepted
the snapshot, Right moved the ego from X=449.5 to X=625.5, Restore returned the
ego to X=449.5, and an original `look` command ran after restoration. The game
exited with the same free-memory report it had at startup. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-persistence-current-fullcheck-20261116`.
This refreshes a bounded state route; it does not close the remaining S08
failure/UI cases or V03's uninterrupted quest progression.

#### KQ1 east/west journey rerun on complete-check modules (2026-11-16)

The original-resource `check_wbgame_mame.py --game kingsquest1 --journey`
scenario passed against the current modules. It loads the lake at the east
boundary, checks its exact room description, returns west to the castle and
checks the castle description, then exits with the unchanged free-memory map.
Both dialogs preserve game-scene colors outside their bounds. At that revision,
the pixel oracle checked the then-current dark-blue Wild Bits popup. The
2026-11-22 text-panel rerun below supersedes that palette and validates the
white text area with black tile border. Artifacts are in
`/Users/boisy/Projects/coco-shelf/.wildbits-test/kq1-journey-current-fullcheck-20261116c`.

#### Wild Bits Sierra text-panel rerun (2026-11-22)

The ordinary modal `print` path now uses a full-width white panel with a
one-cell black frame on rows 5–19. Text wraps inside its bounded interior; the
game picture remains visible above and below the window. The KQ4 `look` test
checks each frame edge and verifies its full description is visible inside the
panel. KQ1's lake/castle journey check uses the updated panel bounds and passes.
The separate `text.screen` king-dialog path still passes its 2,000-frame,
fresh-key dismissal and memory-recovery checks. MAME runs and captures are in
`.wildbits-test/kq4-overlay-verify-4`,
`.wildbits-test/kq1-panel-followup`, and
`.wildbits-test/kq1-panel-journey-followup2`. KQ4's positioned opening credits
remain part of the title sequence and are not converted to a modal panel.
