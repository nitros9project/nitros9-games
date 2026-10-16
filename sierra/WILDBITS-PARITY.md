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
  sprite depth, 52 static painting cases, 1,024 dispatch cases, 4,098
  index/formatter calls, object/global formatting, audio, and custom-priority
  two-terminal/cold-restore MAME acceptance pass.

Evidence and reproduction paths: [engine validation](WILDBITS-ENGINE.md#custom-priority-bands-and-fixed-priority-depth-2026-10-15)
and [MAME guide](WILDBITS-MAME.md). These checked baseline items do not close the
unchecked equivalence gates below.

## 1. Close the command coverage inventory

At the recorded baseline the catalog contained 182 commands: 171 had native
routes, including eight success-only routes; eleven were explicitly unsupported.
The C08–C11 correction gave 175 routed commands and seven unsupported
commands. C01–C03 and C07 raise that to 179 routed commands and three unsupported routes. Four added success-only routes reproduce actual CoCo stubs, rather
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
| C06 | 170: simple save naming | `cmd_set_simple` | Slot/name selection has an explicit native mapping; test subsequent save/restore, repeated selection, bounds and cancellation. |
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
- [ ] **C04–C06:** Close each remaining trace/simple-save behavior individually.
- [ ] **C07 — Menu visibility:** Literal values, flag-14 permission and module
  lifetime are verified, but request/display ordering remains different: CoCo
  queues `menu_input` for the next event loop; native still blocks inside it.
  Close request-then-hide/show interactions before checking this gate.
- [x] **C08–C11:** Close each CoCo-stub compatibility case above individually.
- [x] **C12 — Existing success-only routes:** Verify all of 127, 155, 163, 164,
  173, 176, 178 and 181 against their actual CoCo bodies. Record argument
  consumption, successful return and preserved state for each. In particular,
  155's fixed-origin behavior is a permitted platform difference only after its
  observable effect is explicitly documented.
- [ ] **C13 — Complete command manifest:** Account for all 182 commands and 19
  predicates with reference implementation, native implementation, shared
  component/backend boundary, meaningful test and result. Every unsupported or
  intentionally different result must link to its decision. Do not implement
  omitted PC behavior that CoCo does not implement merely to improve a count.

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

Evidence for C08–C12: `check_logic_executor.py` executes 43 controlled scripts
in both actual interpreters at two load addresses (172 executions). Tests use
return/branch/condition-looking operands, execute a following assignment, and
compare the entire variable and flag sets plus stack, cursor guards and immutable
initialized code. The new cases fail on the old native unsupported routes and
pass after the correction (`/tmp/sierra-parity-stub-baseline.log`,
`/tmp/sierra-parity-stubs.log`). Opcode 155's two ignored operands also match the
actual CoCo body; no additional platform exception is needed for that stub.
The final rerun also passes the overlap counterpart below. Native audio
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
  failures and restoration of caller context. Resolve the Manhunter format or
  overlapping-target audit failure before claiming support for those resources.
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
  Resolve remaining literal percent, malformed directive, missing operand,
  width/overflow and recursion policies against CoCo. Match return/error and
  caller context, not merely the visible happy-path text.
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

The all-title audit also emits `coverage.json`, a complete 182-command and
19-predicate inventory with effective routes, acceptance gates and candidate
regression families. C13 remains open: test suggestions and routed status are
not individual semantic comparison results, and predicate zero's reference/native
validity must be explicitly accounted for. Resource hashes identify the audited
versions without treating a game-directory name as sufficient provenance.

## 3. Finish the architecture and capacity work

- [ ] **A01 — Reclaim code capacity:** Establish space for C01–C07 before adding
  resident instructions. Baseline limits: game 23,807/23,808 bytes; helper
  8,190/8,192; writable prefix 3,191/4,096; private data 24,465/24,576.
  Short branches, arithmetic delegation and common copies made C01 fit. Current
  budgets are game 23,805, UI helper 6,265, state helper 3,180, copied prefix
  3,177 and private 24,470 bytes. All 64 owners compile; CoCo stays unchanged.
  This is initial capacity recovery, not enough evidence to close A01 for all
  remaining features.
  Record before/after budgets and preserve stack headroom and ABI checks.
  Do not solve this by silently increasing the address-space limits.
- [ ] **A02 — Complete duplication inventory:** Review remaining engine behavior
  in CoCo and native feature files; list each duplicate algorithm and either
  consolidate it or explain its necessary platform-specific representation.
  Common gameplay rules must have one maintained source. Backend grouping must
  remain understandable; avoid introducing per-operation fragment files.
- [ ] **A03 — Document interfaces:** Record register/stack, private-state,
  error/ownership and reentrancy contracts for remaining platform interfaces.
  Keep hardware/driver access in backends and common behavior in shared code.
  Identical module packaging is not required: CoCo's four modules and native
  `wbgame`/`wbui`/`wbstate` may remain different when behavior and ownership match.
- [ ] **A04 — Run the complete standard target:** All 58 current check commands
  pass on one revision, with reproducible logs; any debugger/test infrastructure
  failure is fixed or explicitly isolated and rerun. The older segmented
  baseline is useful evidence but does not satisfy this gate. Revision `78893f7`
  now passes the former 57-command target uninterrupted; the promoted
  priority/arithmetic/copy revision `a9a889a` passes all 58 commands. The
  ABI-8 capacity run now passes all 58 checks with exit status 0; the latest
  ABI-11 C07 run remains in progress. The ABI-10 run stopped on a missing
  prebuilt CoCo fixture; the test now compiles that reference itself. The
  ABI-9 partial run was superseded
  and is not a pass.

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
  do not make the user manually finish fourteen adventures.
- [ ] **V03 — Continuous progression:** Add an uninterrupted automated KQ1 route
  from a fresh start to ending, exercising resource changes and accumulated
  state. Extend progression scenarios to each supported title or record an
  explicit unverified exception. Injected quest checkpoints alone do not pass
  this gate.
- [ ] **V04 — Terminal stress and failure cleanup:** Repeatedly start/switch/exit
  two different games; exercise modal UI, audio, save/restore, occupied-terminal
  rejection, interruption and allocation/driver failures. Surviving instances
  keep input/display/audio/state and final memory/module/path ownership balances.
- [ ] **V05 — Performance:** Measure comparable movement/cycle, room-load,
  redraw, modal and sound workloads with specified emulator CPU/driver settings.
  Compare default and custom-priority paths and inactive terminals. Agree on
  acceptable differences before closing; bounded arithmetic and working motion
  are not measurements of parity or zero performance overhead.
- [ ] **V06 — Physical Wild Bits:** Record hardware/FPGA/NitrOS-9/driver versions
  and repeat movement, dialogs, audio, terminal switching, persistence and exit
  acceptance on the user's multiple-terminal target. Emulator success alone
  does not close this hardware gate.

## Execution order and completion rule

1. A01 and C08–C12: reclaim capacity and close bounded compatibility contracts.
2. C01–C07 and C13: finish the remaining command inventory and real behavior.
3. S01–S08 alongside A02–A04: replace assumptions with differential evidence.
4. V01–V06: broaden original-game progression, stress and performance evidence.

Maintain this file after each verified change. For grouped command rows, record
individual results before checking the group. Newly discovered defects belong
under the relevant existing gate with a reproducer; add a gate only when it
represents a distinct missing requirement.

**Parity is complete when every open gate is closed, or a specific difference is
explicitly accepted and documented by the user.** Do not convert unsupported
commands to success-only routes, reduce test scope, or redefine parity to mark
this checklist complete. Until then report closed gates and concrete blockers,
not a completion percentage or an unsupported delivery date.


## Confirmed remaining behavior differences

S05 now has direct CoCo/native reproducers: string-slot contents are recursive
on CoCo but literal on the baseline native owner; CoCo drops unknown two-byte
percent escapes, defaults missing numeric operands to zero and wraps indices
modulo 256. The baseline native owner differs on those paths. An isolated
candidate is under test in `/tmp/sierra-parity-next`, with direct comparison
logs `/tmp/sierra-format-reference.log` and
`/tmp/sierra-format-policies-isolated.log`. Do not count that candidate as merged
or close S05 until its complete required validation passes. Recursion-depth,
invalid/missing-message and malformed-source bounds also need explicit parity
or exception decisions.

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
branches remain errors in both modes. A controlled counterpart is included in
the actual CoCo/native executor suite to verify the two paths rather than
assuming the resource is malformed or silently ignoring the finding. This does
not prove Manhunter's complete control flow or puzzles.

The formatter inventory contains 18 findings across six titles: literal
percent punctuation/spacing and missing operands. Their byte locations and
classifications are recorded in the reports. Resolve them against CoCo under
S05 before treating them as either harmless text or native defects.


### Additional focused evidence, 2026-10-15

The formatter/predicate comparison results and the bounded reference-transport
retry policy are recorded in
[engine validation](WILDBITS-ENGINE.md#formatter-and-constant-true-predicate-parity).
531 direct formatter comparisons, 4,094 index/formatter cases and 192 executor
executions pass. S01 and S05 remain open: these results cover specific boundaries,
not their complete acceptance scope. Message index zero is safely normalized to
empty; recursion and malformed-resource policies still require final decisions.

The user confirmed emulator-only availability. V06 physical-hardware acceptance
remains unchecked and has not been waived. Independent software work continues.


### Capacity-provider evidence, 2026-10-15

The ABI-8 UI/persistence split, byte budgets, loader safety checks and matching
64-owner/MAME evidence are recorded in
[engine validation](WILDBITS-ENGINE.md#separate-ui-and-persistence-providers-abi-8).
It creates 3,108 UI bytes of headroom; A01 remains open for the complete
remaining feature set. The preceding ABI-7 complete 58-command target passed.
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
