# Shared Sierra routines

These are body includes used by both the CoCo modules and native Wild Bits
owners. They allocate no state and contain no OS-9 module header.

- `random-command.asm`: inclusive random-range calculation and variable store;
  owners retain their seed generators, validation and variable-table bindings.
- `bounded-string-copy.asm`: NUL-terminated copying with a positive character
  limit; owners bind destination registers and byte/stack-word countdowns.
- `decimal-byte.asm`: leading-space decimal conversion with modulo-256
  accumulation and a first-nondigit stop, using only stack-local scratch.
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
- `object-cel-advance.asm`: all four cel-cycle modes, one-tick suppression,
  unsigned reverse wrapping, endpoint completion flags and motion stopping;
  owners bind scratch, flag storage and view-selection/status callbacks.
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

The formatter now also shares `format-scan.asm` (character traversal),
`format-directives.asm` (substitution selection), `format-string-slot.asm`
(string-slot resolution), `decimal-index.asm` and `unsigned-decimal.asm`.
Their platform operands preserve each owner's storage, bounds and errors.
`nul-string-copy.asm` is used by CoCo `StrCopy` and native formatter source
frames/string/numeric emission; checked emitters stop before copying NUL,
while direct copies include it. Full formatting recursion and several
substitution providers remain owner-specific.

`format-recursive-call.asm` binds recursive formatting arguments/call/release;
`format-expansion.asm` shares substitution result application, checked error
return and outer-scan continuation. CoCo generic/global substitutions and
native message expansion use these pieces with their original argument ABI.
The actual recursion frame layout and message readers remain owner-specific.

`xor-decrypt.asm` is the in-place AGI buffer cipher used by CoCo and the
native object-file loader. `agi-xor-key.asm` defines their immutable key;
native streaming message decryption references it too. File/mapped-message
bounds and object validation stay in their storage providers.

`object-block-state.asm` shares allowed/crossing control-bit updates and
stopped-direction/ego handling. `object-unanimate.asm` shares bulk animated/
visible-bit clearing over owned records. `platform/*-object-control-operands.asm`
binds ego state and record iteration. `object-step-deltas.asm` supplies the
nine signed X/Y deltas used by both motion implementations. Arithmetic and
collision orchestration still remain in their owner components.

`object-scalar-state.asm` shares priority/direction mutations with operand,
range and ego-state interfaces. `object-field-query.asm` is the common
record-to-variable query used by priority, direction and the five view-state
handlers in `object-view-queries.asm`. Native range policies and the CoCo
byte-assignment policy remain explicit in `platform/*-object-scalar-operands.asm`.

`object-placement-step.asm` shares rejected-candidate spiral advancement;
one leg implementation expands to left/down/right/up, preserving the CoCo
instruction schedule. Owner operands bind frame offsets, continuation branches
and native exhaustion; bounds/collision/terrain validation remain providers.
The frozen CoCo step under `tests/probes` is a differential fixture only.

`object-bounds.asm` shares placement right-edge, baseline, height and horizon
validation. `platform/*-object-bounds-operands.asm` binds horizon/flags storage
and the explicit native zero-width rejection policy. CoCo's Boolean return
and native candidate branches retain their original instruction sequences.

`object-collision-filter.asm` shares actor/candidate ignore and activity/self
eligibility. Owner bindings preserve ID-versus-pointer identity and scratch
registers. Geometric collision rules and iteration remain owner-specific.

`dictionary-lookup.asm` is now used by both production owners. It owns prefix
traversal, character matching, longest phrase selection, ignored-word IDs, and
next-word boundaries. `platform/*-dictionary-operands.asm` binds dictionary
cursor reads and text policy: mapped addresses on CoCo, file offsets on Wild
Bits. CoCo retains case folding, its single-letter defaults, and in-place phrase
termination; native input is normalized beforehand and remains intact for its
private offsets/lengths. The native provider validates streamed records, locates
the encoded group, and performs cached reads without retaining a mapped slab.
It accepts zero letter indexes and an optional trailing zero as before.

`check_dictionary_lookup.py` executes the common kernel through both real owners
at two addresses each, checking immutable code, state and guards. The native
parser regression additionally covers dictionaries larger than its 512-byte
buffer, malformed records, typed input and `said` integration. CoCo binaries are
unchanged. Sentence orchestration, vocabulary acquisition/validation, and result
storage still have owner-specific implementations; sharing lookup does not
complete the broader engine migration.

The native dictionary adapter validates once per submitted line and temporarily
indexes encoded groups in the idle formatter-output scratch area. That index is
rebuilt after every `ParserParse`; no additional private bytes are allocated.
Native parser tests bound dictionary file reads per line and include a second
submission, protecting this scratch lifetime and avoiding repeated full scans.

Native per-cycle move-to direction now calls the existing `CalcMoveDir` in
`object-move-direction.asm`, removing its separate eight-way algorithm. Its
wrapper supplies threshold one so negative/zero/positive coordinate differences
retain the previous native direction choices; target clamping still uses the
real step size. The wrapper preserves private context X and object cursor U.
`check_move_direction.py` exercises both production paths at two addresses.

`object-coordinate-step.asm` owns direction-vector application to candidate X/Y
coordinates for both production runtimes. `platform/*-coordinate-step-operands.asm`
binds candidate/step storage and direction-table cursors. Store-joining policy
preserves each owner's original branch schedule, so all fourteen CoCo title
modules and native `wbgame` remain byte-identical. Candidate initialization,
clamping, terrain/collision checks and commit are still owner-specific.

`object-coordinate-clamp.asm` now owns candidate screen/horizon clamping in both
movement pipelines. Bindings reuse the coordinate-step storage interface and
preserve dimension checks, comparison scheduling, early vertical exits and
byte-versus-word horizon policy. Legacy entry aliases remain available. Native
and all fourteen rebuilt CoCo title modules are byte-identical; terrain,
object collision and position commit remain separate.

`object-terrain-scan.asm` and `object-terrain-constraints.asm` now supply baseline
control/water/trigger classification and water-only/land-only constraints for
both production owners. Pixel access, packed-priority representation, counters,
flag storage and blocked exits are bound in `platform/*-terrain-operands.asm`.
CoCo preserves clearing water before conditional-control rejection; native
clears it afterward. Native trigger counts and CoCo's raw signal value remain
owner policies. Mapping, priority-15 bypass, ego flag publication and cleanup
remain outside the common rules. The production-kernel regression covers all
priorities/control/status bytes, mixed baselines and both owners at two addresses.
