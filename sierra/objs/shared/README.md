# Shared Sierra routines

These are body includes used by both the CoCo modules and native Wild Bits
owners. They allocate no state and contain no OS-9 module header.

- `random-command.asm`: inclusive random-range calculation and variable store;
  owners retain their seed generators, validation and variable-table bindings.
- `divide-byte.asm`: unsigned byte quotient/remainder with private DP scratch.
- `object-wander.asm`: direction/countdown changes shared with CoCo; native
  random state is process-private. Coordinate stepping remains separate.
- `object-position-test.asm`: inclusive rectangle checks for left/center/right/
  full object extents, with owner-provided scratch and boolean return adapters.
- `variable-commands.asm`: commands 1–11, including saturating increment/
  decrement, byte wrapping and both indirect assignment directions. Owners
  provide the variable-table address at assembly time.
- `inventory-commands.asm`: carried/dropped/room transfers, indirect item and
  room variables, room queries, and possession/room predicates; owners bind
  item lookup, bounds, room storage and condition-return conventions.
- `flag-commands.asm`: commands 12–17, using owner-specific packed-bit/byte
  flag storage adapters for set, clear and toggle.
- `condition-flow.asm`: common short-circuit AND/OR/NOT traversal, with owner
  stream callbacks and bounded native skipping/error handling.
- `condition-tests.asm`: the six unsigned comparisons and direct/indirect
  flag predicates, with owner-provided operands and boolean return adapters.
- `said-match.asm`: word-ID matching, single-word/rest wildcards, and expected
  operand cursor advancement; owners supply input flags and result adapters.
- `ascii-lower.asm`: ASCII-only folding with register preservation.
- `find-byte.asm`: NUL-terminated byte-set search, shared by text normalization.
- `tokenize-string.asm`: sentence delimiter collapsing, dropped punctuation and
  edge trimming; owners supply buffers and case-folding conventions.
- `parser-punctuation.asm`: common sentence delimiter/drop sets.
- `compare-strings.asm`: normalized 40-byte string-slot comparison for condition
  15, with owner-provided string-table and ASCII-fold interfaces.
- `string-punctuation.asm`: comparison-specific ignored bytes, kept distinct
  from sentence tokenization rules.
- `agi-test-table.asm`: one 19-entry condition catalog, expanded into CoCo
  handler/operand descriptors or native operand counts.
- `agi-command-table.asm`: one command catalog, expanded into CoCo handler
  descriptors or native operand-count bytes at assembly time.
- `object-distance.asm`: visible-object Manhattan distance with saturation;
  owners supply private scratch and result-store adapters.
- `object-flag-rules.asm`: one catalog of 14 loop/priority/terrain/horizon/
  collision/cycling mask rules, used by both owners.
- `object-flag-mask.asm`: common compile-time mask mutation body; owner supplies
  the record pointer register. Identity operations emit no instructions.
- `object-animation-state.asm`: idempotent animate.obj initialization.
- `object-coordinate-state.asm`: literal/variable position assignment, position
  queries, and signed reposition arithmetic; owners provide operand/storage
  adapters and retain their placement/collision boundaries.
- `object-cycle-state.asm`: continuous/endpoint animation modes and flags.
- `object-motion-setup.asm`: follow-distance selection and completion state,
  wander initialization, and saved/optional move speed with literal completion
  flags; owners provide flag, input-control and direction callbacks.
- `object-motion-state.asm`: normal/start/stop record transitions; ego control
  effects remain owner adapters.
- `object-rate-state.asm`: cycle/step preset and countdown writes.
- `object-block-test.asm`: strict rectangle containment, with owner-selected
  state addressing at assembly time.
- `picture-command-table.asm`: a single F0-FA handler catalog, expanded as
  CoCo load-relative or native immutable table-relative entries.
- `picture-colors.asm`: F0-F3 draw-color and priority-mask control, with
  assembly-time bounded/contiguous reads.
- `picture-commands.asm`: F4-F7 corners and absolute/relative segment commands,
  using the same plotting and coordinate interfaces on both owners.
- `picture-coordinates.asm`: common coordinate clamping and command-byte
  detection, with assembly-time contiguous/bounded input selection.
- `object-direction-tables.asm`: movement-direction to view-loop selection.
- `picture-line.asm`: integer line drawing with owner-provided direct-page
  coordinate and scratch symbols. Calls `SbuffPlot` through a direct `LBSR`.
- `picture-pen.asm`: pen geometry and texture sequence, using the same plotting
  interface and owner-provided direct-page scratch symbols.
- `picture-pen-tables.asm`: immutable circle masks and index tables.

The CoCo `shdw.asm` and Wild Bits decoder include these exact files. Owners
supply different symbol addresses without duplicating the algorithms. The
existing CoCo plot implementation uses contiguous storage; the Wild Bits
implementation uses bounded OS-managed mapping windows. Selection takes place
in `platform/picture-storage.asm` and emits no dispatch instructions.

This is the first actual shared-source migration. The native logic interpreter
(`platform/wildbits-logic-code.asm`) and CoCo `mnln.asm` still have different state layouts and command implementations;
that reconciliation is unfinished. Moving a native-only file here would not,
by itself, make it shared with CoCo.

`logic-executor.asm` now owns the complete opcode loop for both engines:
return, relative jump, condition traversal, command dispatch, and cleanup.
`platform/coco-logic-stream.asm` and `platform/wildbits-logic-stream.asm`
provide reads, branch application, command dispatch, and status conventions.
These are assembly-time bindings, with no runtime platform selector. Each
invocation owns two stack bytes, and every native success/error exit releases
that frame. Nested logic calls therefore keep independent condition state.
Native false-condition and unconditional jumps use the same checked branch
implementation. CoCo keeps its contiguous reader and existing dispatch tables.

`tests/check_logic_executor.py` executes both real owners at two load addresses,
including their actual command and condition handlers, and compares variables
and flags across the packed CoCo and byte-per-flag native layouts. It verifies
forward/backward branches, mixed conditions, stack guards and immutable code
after CoCo table initialization. The CoCo module remains byte-identical.
