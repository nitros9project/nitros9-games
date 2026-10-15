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

The catalog contains 182 commands: 171 have native routes, including eight
success-only routes; eleven are explicitly unsupported. Commands 0..17 execute
in the VM before platform dispatch and are included in the 171. These numbers
measure routing, not behavioral equivalence.

The catalog's CoCo symbol names are sometimes misleading: opcode 29 is labeled
`show pri` but calls `CmdSaveGame`; 144 and 175 both call `cmd_shake_screen`.
Compare the actual bodies and caller contracts, not symbol names alone.

| ID | Open route | CoCo reference | Acceptance required |
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

- [ ] **C01–C07:** Close each real diagnostic/UI/save behavior above individually.
- [ ] **C08–C11:** Close each CoCo-stub compatibility case above individually.
- [ ] **C12 — Existing success-only routes:** Verify all of 127, 155, 163, 164,
  173, 176, 178 and 181 against their actual CoCo bodies. Record argument
  consumption, successful return and preserved state for each. In particular,
  155's fixed-origin behavior is a permitted platform difference only after its
  observable effect is explicitly documented.
- [ ] **C13 — Complete command manifest:** Account for all 182 commands and 19
  predicates with reference implementation, native implementation, shared
  component/backend boundary, meaningful test and result. Every unsupported or
  intentionally different result must link to its decision. Do not implement
  omitted PC behavior that CoCo does not implement merely to improve a count.

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

## 3. Finish the architecture and capacity work

- [ ] **A01 — Reclaim code capacity:** Establish space for C01–C07 before adding
  resident instructions. Current limits: game 23,807/23,808 bytes; helper
  8,190/8,192; writable prefix 3,191/4,096; private data 24,465/24,576.
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
  `wbgame`/`wbstate` may remain different when behavior and ownership match.
- [ ] **A04 — Run the complete standard target:** All 57 current check commands
  pass on one revision, with reproducible logs; any debugger/test infrastructure
  failure is fixed or explicitly isolated and rerun. The older segmented
  baseline is useful evidence but does not satisfy this gate.

## 4. Acceptance across games, terminals and hardware

- [ ] **V01 — Audit every bundled title:** Run script/message audits for all 14
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
