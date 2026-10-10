# Shared Sierra routines

## Component layout

Formatter, motion and animation are grouped by feature rather than individual
operations. Each component is included once per owner and defines named
assembly macros. The owner expands a section where its code previously lived;
labels, branches and instruction order are preserved without runtime calls.

| Shared component | Contents | Platform interface |
| --- | --- | --- |
| `game-cycle.asm` | Logical clock rollover, transient flag resets and room-number publication | Timing, flag storage and room-variable bindings |
| `object-commands.asm` | Position, room-entry placement, animation, cycle/rate/motion state, flags, blocking and field queries | CoCo/Wild Bits `objects-bindings.asm` |
| `formatter.asm` | Character scan, directive selection, string slots, recursive calls and expansion | CoCo/Wild Bits `text-ui-bindings.asm` |
| `object-motion.asm` | Scheduling, coordinate steps, clamping, position commits and target motion | CoCo/Wild Bits `objects-bindings.asm` |
| `object-animation.asm` | Animation update, all cel-cycle modes and direction tables | CoCo/Wild Bits `memory-resources-bindings.asm` |
| `resource-lzw.asm` | LZW initialization/reset, code-window alignment, masks, dictionary traversal and insertion | Owner fields, bounded acquisition, dictionary cursor and stack bindings |

For example, `FORMAT_EMIT_SCAN` expands the scan body in `formatter.asm`;
`MOTION_EMIT_CLAMP` expands the clamp body in `object-motion.asm`. Algorithms
are contained directly in these component files. The old fragment files have
been removed. The shared components replaced 41 files with 12. Their platform interfaces
now live in the feature binding files described in `../platform/README.md`.


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
  random state is process-private. Coordinate stepping uses `object-motion.asm`.
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
  descriptors, native operand-count bytes and native platform-command
  relative dispatch entries at assembly time.
- `object-distance.asm`: visible-object Manhattan distance with saturation;
  owners supply private scratch and result-store adapters.
- `object-flag-rules.asm`: one catalog of 14 loop/priority/terrain/horizon/
  collision/cycling mask rules, used by both owners.
- `object-commands.asm`: object position/coordinate state, animate/unanimate,
  cycle and rate controls, normal/start/stop motion, block/flag mutations,
  priority/direction assignment and field query handlers.
- `object-animation.asm`: all four cel-cycle modes, one-tick suppression,
  unsigned reverse wrapping, endpoint completion flags and motion stopping;
  owners bind scratch, flag storage and view-selection/status callbacks.
- `object-motion-setup.asm`: follow-distance selection and completion state,
  wander initialization, and saved/optional move speed with literal completion
  flags; owners provide flag, input-control and direction callbacks.
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
- `object-animation.asm`: movement-direction to view-loop selection.
- `picture-line.asm`: integer line drawing with owner-provided direct-page
  coordinate and scratch symbols. Calls `SbuffPlot` through a direct `LBSR`.
- `picture-pen.asm`: pen geometry and texture sequence, using the same plotting
  interface and owner-provided direct-page scratch symbols.
- `picture-pen-tables.asm`: immutable circle masks and index tables.

The CoCo `shdw.asm` and Wild Bits decoder include these exact files. Owners
supply different symbol addresses without duplicating the algorithms. The
existing CoCo plot implementation uses contiguous storage; the Wild Bits
implementation uses bounded OS-managed mapping windows. Selection takes place
in `platform/sections.d` and emits no dispatch instructions.

The native owner (`platform/wildbits-logic.asm`) and CoCo `mnln.asm` retain
different storage layouts. Their common executor and command rules expand
from this directory through explicit operand and service bindings. Native-only
storage or presentation implementations remain in `platform`; moving those
bodies here alone would not make them shared.

`logic-executor.asm` now owns the complete opcode loop for both engines:
return, relative jump, condition traversal, command dispatch, and cleanup.
`platform/coco-logic-bindings.asm` and `platform/wildbits-logic-bindings.asm`
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

The formatter shares character traversal, substitution selection, string-slot
resolution and recursive call/return rules in `formatter.asm`, plus numeric
parsing and output in `decimal-index.asm` and `unsigned-decimal.asm`.
Their platform operands preserve each owner's storage, bounds and errors.
`nul-string-copy.asm` is used by CoCo `StrCopy` and native formatter source
frames/string/numeric emission; checked emitters stop before copying NUL,
while direct copies include it. Recursion-frame storage and substitution providers remain owner-specific.

`formatter.asm` binds recursive formatting arguments/call/release and shares
substitution result application, checked error
return and outer-scan continuation. CoCo generic/global substitutions and
native message expansion use these pieces with their original argument ABI.
The actual recursion frame layout and message readers remain owner-specific.

`xor-decrypt.asm` is the in-place AGI buffer cipher used by CoCo and the
native object-file loader. `agi-xor-key.asm` defines their immutable key;
native streaming message decryption references it too. File/mapped-message
bounds and object validation stay in their storage providers.

`object-commands.asm` shares allowed/crossing control-bit updates and
stopped-direction/ego handling. `object-commands.asm` shares bulk animated/
visible-bit clearing over owned records. `platform/*-objects-bindings.asm`
binds ego state and record iteration. `object-step-deltas.asm` supplies the
nine signed X/Y deltas used by both motion implementations. Vector arithmetic, clamping, terrain rules and collision scanning are described
below; per-cycle orchestration still remains in owner components.

`object-commands.asm` shares priority/direction mutations with operand,
range and ego-state interfaces. `object-commands.asm` is the common
record-to-variable query used by priority, direction and the five view-state
handlers in `object-commands.asm`. Native range policies and the CoCo
byte-assignment policy remain explicit in `platform/*-sections.d`.

`object-placement-step.asm` shares rejected-candidate spiral advancement;
one leg implementation expands to left/down/right/up, preserving the CoCo
instruction schedule. Owner operands bind frame offsets, continuation branches
and native exhaustion; placement calls the bounds/collision/terrain services
whose common rules and owner providers are described below.
The frozen CoCo step under `tests/probes` is a differential fixture only.

`object-bounds.asm` shares placement right-edge, baseline, height and horizon
validation. `platform/*-sections.d` binds horizon/flags storage
and the explicit native zero-width rejection policy. CoCo's Boolean return
and native candidate branches retain their original instruction sequences.

`object-collision-filter.asm` shares actor/candidate ignore and activity/self
eligibility. Owner bindings preserve ID-versus-pointer identity and scratch
registers. Complete traversal and geometry now live in
`object-collision-scan.asm`, with explicit owner policies.

`dictionary-lookup.asm` is now used by both production owners. It owns prefix
traversal, character matching, longest phrase selection, ignored-word IDs, and
next-word boundaries. `platform/*-sections.d` binds dictionary
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

`object-motion.asm` owns direction-vector application to candidate X/Y
coordinates for both production runtimes. `platform/*-sections.d`
binds candidate/step storage and direction-table cursors. Store-joining policy
preserves each owner's original branch schedule, so all fourteen CoCo title
modules and native `wbgame` remain byte-identical. Candidate initialization and per-cycle orchestration remain owner-specific; the common clamp,
terrain and collision components are described below.

`object-motion.asm` now owns candidate screen/horizon clamping in both
movement pipelines. Bindings reuse the coordinate-step storage interface and
preserve dimension checks, comparison scheduling, early vertical exits and
byte-versus-word horizon policy. Legacy entry aliases remain available. Native
and all fourteen rebuilt CoCo title modules were byte-identical for that
extraction. Terrain and collision rules are now shared too; position transactions are now shared as described below.

`object-terrain-scan.asm` and `object-terrain-constraints.asm` now supply baseline
control/water/trigger classification and water-only/land-only constraints for
both production owners. Pixel access, packed-priority representation, counters,
flag storage and blocked exits are bound in `platform/*-sections.d`.
CoCo preserves clearing water before conditional-control rejection; native
clears it afterward. Native trigger counts and CoCo's raw signal value remain
owner policies. Mapping, priority-15 bypass, ego flag publication and cleanup
remain outside the common rules. The production-kernel regression covers all
priorities/control/status bytes, mixed baselines and both owners at two addresses.

`object-collision-scan.asm` now owns the complete collision scan for both owners:
actor/candidate filtering, record traversal, horizontal overlap, baseline tests
and result selection. The two old routine bodies are replaced by aliases and
one include. Bindings select bounded-table versus counted iteration, candidate
registers, history reads and result ABI. Explicit engine policies retain CoCo
byte sums/inclusive edge contact versus native word comparisons/exclusive
contact, and their distinct baseline histories. The native first comparison's
high-byte handling is preserved exactly. All fourteen CoCo `mnln` binaries and
native `wbgame` remain byte-identical to the preceding revision.

`object-motion.asm` owns candidate commit, collision result handling,
rejection restoration, accepted-state transition and boundary publication for
both production movement paths. `platform/*-sections.d` binds
coordinate/variable storage, collision ABI, terrain validation and recovery,
and continuation into each owner's destination stage. CoCo validates terrain
after committing/testing collision and recovers rejected positions; native
enters after terrain validation and sends rejected positions to its blocked
handler. These sequencing policies are explicit and preserve the original
binary. All fourteen CoCo `mnln` modules and native `wbgame` are byte-identical.
Destination triggering and per-cycle orchestration still remain separate.

`object-motion.asm` shares the direction-call sequence and arrival
transition. Bindings select the threshold, context/result registers, packed or
byte completion flags, stopping order and ego state. CoCo retains its actual-step
threshold and zero-direction completion trigger; native retains threshold one
and its caller's exact-position trigger. CoCo flag-before-stop and native
stop-before-flag order are preserved, as are their different record/ego updates.
All fourteen CoCo `mnln` modules and native `wbgame` remain byte-identical.

`object-animation.asm` now owns the per-object direction-driven loop
selection and cycle countdown stage in both `mnln.asm` and the native motion
owner. It checks fixed-loop state, selects a direction loop, skips unchanged
loops, checks/decrements the cycle timer, invokes the existing shared cel
advance routine and reloads the timer. View selection, native error/context
handling, CoCo reverse-enable storage and continuation ABI are provided by
`platform/sections.d`.

Assembly-time policy preserves the existing differences: CoCo may use the
reverse table for views with more than four loops when its enable bit is set,
and only changes a loop when the record's step countdown equals one. Native
limits automatic selection to two through four loops and validates direction.
CoCo reloads cycle time after cel advancement; native reloads before its tail
call. The outer object traversal, motion scheduling and rendering remain
owner-specific. This extraction changes no instructions: all 14 CoCo `mnln`
modules and native `wbgame` were rebuilt and compared byte for byte.

`object-motion.asm` shares the active-object gate and complete
normal/wander/follow/move-to dispatch in CoCo `DispatchMotion` and native
`GameUpdateObjects`. `platform/sections.d` binds each
owner's step scheduling and continuation: CoCo dispatches only when its step
countdown equals one; native first advances animation, decrements or resets
the countdown, then dispatches. Native restores the object/private context
after follow-direction calculation and rejects unknown motion types; CoCo
retains its existing skip behavior. All 14 CoCo main-loop modules and native
`wbgame` remain byte-identical. Outer traversal and ordering of rendering,
animation and position updates remain owner-specific.

`OBJECT_VIEW_TABLE_ENTRY` in `object-commands.asm` now owns loop/cel table
index scaling, little-endian entry acquisition and pointer/offset resolution
for both owners. `coco-objects-bindings.asm` retains direct mapped reads and
byte-index arithmetic; `wildbits-objects-bindings.asm` retains the checked
word reader, logical offset base and lower/upper resource bounds. Native
loop/cel error labels and CoCo cel/loop helper entry points are unchanged.
All 14 CoCo main-loop modules and native `wbgame` are byte-identical after
rebuilding. Resource loading, cache lifetime and metadata validation policies
outside table traversal are still owner-specific.

The sprite visibility macros in `object-commands.asm` implement the CoCo
per-cel rule for both owners. Each draw begins hidden; a successful composed
pixel write clears that local state; a completed ego draw publishes AGI flag
1. CoCo binds its packed `StateFlag` bit and existing scratch byte; native
binds its byte flag and process-private scratch. Other objects cannot publish this
flag. This tracks the ego's writes during its draw, rather than recomputing
visibility after every later object has been composed.

The integrated native regression checks visible, background-occluded, fully
transparent, mirrored/clipped and erased cels, plus a hidden ego followed by
a visible non-ego. Pixel output is checked alongside the flag. All 14 CoCo
`shdw` modules remain byte-identical. The initial native implementation gained 46 code bytes and one
private byte because it previously omitted this flag update. Rendering now
reuses the first byte of `spritekey`: collection finishes before cel drawing,
and rendering reads the ordered list rather than the insertion key. This
recovers that private byte without changing the visibility rule.

`OBJECT_CEL_CLIP` reconciles the dimensions of a newly selected cel with the
object's position and clip-state bit. Both owners now use CoCo's existing
right-edge and height/horizon rule. CoCo retains its byte-add behavior; native
also checks carry so an off-screen coordinate cannot wrap into an accepted
right edge. The native view reader still validates dimensions before calling
the rule. Direct execution at two load addresses passes 5,920 cases covering
every coordinate, horizon and flag byte, all legal widths/heights, guards,
registers and unrelated fields. All 14 CoCo `mnln` modules remain identical.

The command catalog has four fields: CoCo handler, operand descriptor, native
platform handler and a game-only marker. CoCo expands its original two fields;
native expands operand counts and a separate relative dispatch table from the
same rows. A probe redirects game-only rows to the explicit unsupported error
handler. The production table replaces the native comparison chain and saves
115 code bytes; it allocates no state and needs no initialization patching.

`resource-lzw.asm` shares the actual three-byte window alignment and code
masking used by CoCo `ReadPicPixel` and native `LzwReadCode`. The native reader
now supplies that window from a raw pending byte and just enough bounded
source bytes, rather than accumulating a code one bit at a time. CoCo retains
its direct buffered window and original instructions. The mask table retains
its legacy 12-bit entry; both production decoders cap growth at 11 bits.
Dictionary management, string stacks and error/output policies remain with
the owners. The 228 compressed KQ1 resources match both actual decoders and
the independent byte-string oracle. Direct reader fixtures additionally check
code values, bit alignment, source consumption and relocation.

`RESOURCE_LZW_WALK` shares the dictionary prefix/suffix traversal as well.
Its literal test, entry traversal and suffix/prefix ordering are common.
`coco-memory-resources-bindings.asm` supplies direct mapped entries and the
hardware stack; `wildbits-memory-resources-bindings.asm` supplies checked
dictionary codes and bounded workspace-stack operations. Native animation
aliases in that binding file are conditional on VM support, allowing a
codec-only owner to load the resource bindings. All seven native modules and
all 56 CoCo modules remain byte-identical after this extraction.

Bounded picture callbacks own their cursor representation. Shared coordinate
and relative-line helpers use the returned/retained byte rather than rereading
`X-1`; native game input can therefore refill an 8-KiB private staging window
from a larger owned resource. CoCo keeps its contiguous input path.


`object-move-direction.asm` defines both the target-direction code emitter
and the common joystick classifier. Device bindings supply axis reads,
center limits and Y orientation; input backends retain sampling, button and
direction-ownership policy. Target code is emitted at its original owner
location with `MOVE_DIRECTION_CODE`.
