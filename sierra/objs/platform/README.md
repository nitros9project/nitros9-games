# Sierra platform features

This directory groups platform-specific code, private state and assembly
bindings by feature. It contains 26 assembly files, down from 208. Shared game
algorithms remain in `../shared`; `wildbits-runtime.asm` composes the native
module and its process-private layout.

| Feature | Responsibilities |
| --- | --- |
| `*-memory-resources.asm` | Loading, allocation, mapping, asset access, decompression and view/room resources |
| `*-graphics.asm` | Picture decoding/storage, screen setup, palettes, presentation, sprite backgrounds and rendering |
| `*-input.asm` | Keyboard/controller input, line input and terminal options |
| `*-text-ui.asm` | Messages, text, dialogs, inventory, menus and replay |
| `*-audio.asm` | Sound state and backend routines |
| `*-timing*.asm` | Clock bindings and timer interception |
| `*-logic.asm` | Logic stream/cache state and platform execution support |
| `*-objects.asm` | Motion, animation, blocking, positioning and object state |

The `coco-` and `wildbits-` prefixes identify the backend. Feature binding files
(`*-bindings.asm`) contain macros and constants and emit no code. The caller
loads each once using its `PLATFORM_*_BINDINGS` guard. This keeps related
interfaces together without duplicating macro definitions.

Feature implementation files contain named **layout sections**. An owner
includes `sections.d`, sets `PLATFORM_SECTION` to a descriptive constant, then
includes the feature file. For example:

```asm
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_INPUT_DATA
                    use platform/wildbits-input.asm
```

The corresponding section in `wildbits-input.asm` contains the actual state
allocation. Its input routines are in the same file, selected at their code
placement sites. Selection happens during assembly and emits no runtime
dispatch. This preserves the existing data offsets and module code order.
Sections use conditional chains so nested feature includes cannot select a
second section after changing `PLATFORM_SECTION`.

Common condition traversal, picture command/line/pen algorithms, formatting,
math, logic execution, object rules, parsing and string commands reside in
`../shared`. Feature files place those bodies and implement their storage,
service and presentation interfaces. Operand macros live in the corresponding
binding files, loaded once before the body is emitted. Timing keeps its small clock interface
in `coco-timing.asm` or `wildbits-timing.asm` alongside the feature boundary.

The old per-operation selector files have been removed. Their compile-time
CoCo/Wild Bits selection and unsupported-backend checks now appear at the
owner's inclusion site.

## Interface and ownership contracts

Platform bindings are assembly-time interfaces, not runtime function tables.
The shared body is expanded at its existing owner location; its binding macros
name the live registers, stack slots, process/object fields, result flags and
platform-specific branch targets. A binding must state any non-obvious register
or stack assumptions beside the macro. Adding a shared body must not introduce
hidden mutable state: scratch belongs to the owner or to an explicitly described
private frame. This keeps nested calls independent where the shared algorithm
can recurse and avoids changing the per-cycle cost with a platform dispatch.

| Boundary | Call and state contract | Errors and ownership |
| --- | --- | --- |
| Shared VM and predicates | `logic-executor.asm` owns a two-byte activation frame per invocation. `coco-logic-bindings.asm` and `wildbits-logic-bindings.asm` bind byte reads, command/predicate calls, branch application and scan starts to their existing owner state. | CoCo keeps its original contiguous-stream/table contract. Wild Bits bounds every stream read and unwinds the two-byte frame on success and error; the owning resource/cache layer retains and releases mapped logic. |
| Resource and codec services | The Wild Bits `LoadAsset` ABI returns `X=first owned block`, `B=block count`, `Y=expanded length`, `U=private base`, carry clear. Shared codec bodies obtain bytes through owner read/write bindings; codec scratch is reused only when the formats cannot overlap. | A failed Wild Bits load returns the OS-9/validation error in `B`, carry set, closes an opened path and releases partial allocation. A successful slab transfers to the caller, which must adopt or release it. CoCo keeps MMU/resource ownership in its existing module contract. |
| Object algorithms | Shared object/motion bodies expand in the caller's original code region. The object binding files define record base, candidate coordinates, horizon/terrain reads, collision identity, ego state and arrival/error branches. Wild Bits motion scratch is rooted at the current process-private base; CoCo operands retain the legacy stack frame and fixed engine fields. | Shared bodies do not retain mapped pointers across OS calls. Wild Bits error paths return through the owner cleanup path; CoCo keeps the original status/flag and room-edge policy. Intentional rule differences, including zero-width and horizon policies, are explicit in `*-objects-bindings.asm`. |
| Picture and sprite services | Shared picture command/coordinate/line/pen code calls the bound plotting and bounded-input operations at the same assembly site. View and cel code obtains storage, dimensions, priority and palette through each owner's layout. | CoCo uses contiguous/MMU-backed buffers; Wild Bits maps bounded windows and releases them before yielding to OS, input, clock or sound services. Each platform owns its frame buffer and restores it through its presentation contract. |
| Text, parser and modal UI | Shared tokenization, dictionary, said matching, formatting, string and inventory rules receive owner-selected buffers, input readers, output writers and flag/item storage. Recursive formatting callers own their saved registers and source frames as described in `shared/README.md`. | Resource pointers and output bounds are validated by their owner. Native cold UI runs from the matching immutable `sierraui` provider; callback tables are read-only, while dialog/menu/cache/timer state remains per game process. Provider entry layouts and cleanup are documented in `WILDBITS-ENGINE.md` under ABIs 8–14. |
| Input, clock and sound | Shared code requests logical key, cycle, timer and sound operations; platform code performs device access. The CoCo timer intercept and hardware routines remain in the CoCo backend. Wild Bits uses OS-9 terminal status, process clocks and the owned PSG driver. | No shared algorithm writes device registers. Wild Bits backgrounds mute that process's clock entries and terminate its current sound request, closing the owned audio path; foreground return unmutes and rebases its clock. Per-terminal movement and audio state are not stored in shared writable data. |
| Module and helper lifecycle | Owners select and include named layout sections to preserve code/data placement. Wild Bits resident-to-helper callbacks use the documented callback-table ABI, and helper linked code is read-only. | The resident owns linked-module references and releases them on all exits; `sierrastate` owns the bounded save-state copy, and game-private data remains with each process. CoCo's MMU allocator and four-module loader retain their independent OS contract. |

These contracts are backed by the local binding comments and the focused ABI
records in [`WILDBITS-ENGINE.md`](../../WILDBITS-ENGINE.md). In particular,
the logic executor tests compare both owners at two load addresses, resource
and picture tests inject bounded-read/map failures, object tests guard registers
and stack frames, and provider tests check callback layout, ownership and
cleanup. A platform change that moves a register, stack slot, state field or
error target must update the corresponding binding and its focused comparison.

Verification: all 56 CoCo engine modules (four modules for 14 titles) and native
`wbgame` match the preceding binaries byte for byte. Native probes also build.

The native text-store loop assembles into the existing `sierrastate` auxiliary
module and executes read-only while linked. Its variables and text cells remain
private to the caller. The frontend caches the validated entry and releases the
module during cleanup; clearing a text screen preserves that reference. Install
the matching helper for text output. Source grouping stays in
`wildbits-text-ui.asm`; no additional platform file is needed.

The same grouped text UI source supplies the immutable modal wait/key loop to
`sierrastate`. The resident passes a read-only callback table, and each game keeps
its own timer and cached entry. Both cold entry points share one validated,
retained helper link. Timed blocking prints use variable 21 in half-seconds;
SOL counter sampling handles frame wrap and foreground rebasing, with a
sleep-count fallback when the counter service is unavailable.

The helper's linked code image and writable state copy have separate limits:
8 KiB for linked code, 4 KiB for the prefix ending at `StateCopyEnd`. The loader
returns that validated prefix length for save/restore copying. Rectangle
clearing also executes read-only in the existing helper; sprite/glyph rendering
remains resident. Metadata and private cache pointers are ABI-checked together.

Restart also executes in the existing immutable helper. It requests root-level
unwinding before releasing resources, then reloads the original root without
recursively entering the interpreter. Cache records retain 32 slots at a
12-byte stride. Preserved helper pointers precede the font so deep calls and
long command-line parameters cannot overwrite them.

Infrequent screen configuration also uses the retained immutable helper in the
game build, with a resident callback for cursor messages. Diagnostics assemble
the same grouped implementation directly. Screen initialization and rendering
remain resident.

Inventory previews use the same immutable helper and grouped text UI source.
Resident callbacks select/render the view, present text and restore the scene.
Their temporary record occupies idle private renderer-list storage, while
cached entries and callback state stay private to each game.

Opcode 110 follows the CoCo `cmd_shake_screen` stub: it consumes its literal
operand and returns without changing the framebuffer. The old shake code was
removed; the immutable helper directory retains a tiny compatibility stub at
the former vector slot.

The menu frontend stays in grouped text UI, with display/navigation in that
same source's cold section. Its callback table reuses resident presentation
and foreground services; ordinary game cycles have no additional helper calls.

Joystick handling belongs to grouped Wild Bits input, calls the terminal's
`SS.Joy` interface and leaves hardware access to its driver. Its private
movement ownership and button edges stay separate from shared code and saves.


## Separate UI and persistence providers (ABI 8)

The current package is `sierra`, `sierraui`, `sierrastate` and `sierrafont`. Install the
three executable modules from the same ABI-14 build. UI/audio code now belongs
to the immutable `sierraui` provider; `sierrastate` supplies the bounded private copy
used for save/restore. Existing source feature groups are unchanged.
See [provider ownership, loader contracts, budgets and verification](../../WILDBITS-ENGINE.md#separate-ui-and-persistence-providers-abi-8).
Earlier combined-helper descriptions above document preceding revisions.


Object-status behavior and word formatting now share CoCo source, with native
private-buffer bindings in the grouped text UI backend. See the
[ABI-9 interface and verification record](../../WILDBITS-ENGINE.md#shared-object-status-diagnostic-abi-9).


Memory reporting uses native owned-page categories and the common word formatter.
The show callback interface preserves priority callbacks at 36 and adds a
read-only resident-header offset at 44, with assembly-time guards. See the
[ABI-10 interface and verification](../../WILDBITS-ENGINE.md#native-memory-diagnostic-and-callback-layout-contract-abi-10).


Menu visibility now uses two caller-private, module-lifetime bytes; flag 14
independently permits menu input. See the [ABI-11 contract and evidence](../../WILDBITS-ENGINE.md#menu-visibility-and-input-permission-abi-11).
No additional platform files or per-frame dispatch are introduced.


Menu input is now deferred until the next event stage, with a shared request
policy and private pending byte. Diagnostic/shake/restart commands share a cold
UI loader/cache; screen calls retain their distinct interface. See the
[ABI-12 ownership and verification record](../../WILDBITS-ENGINE.md#deferred-menu-requests-and-shared-ui-entry-abi-12).


Automatic save-name selection now shares CoCo's string-index copy rule. The
native backend maps that name to its filename interface; empty names restore
manual input. Filename staging is cold UI code, and the state provider matches
CoCo's existing-file replacement policy. See the
[ABI-13 contracts, bounds and verification](../../WILDBITS-ENGINE.md#shared-automatic-save-naming-and-replacement-abi-13).


Trace commands and event formatting are grouped in the existing Wild Bits
text-UI backend. Shared VM hooks select command/predicate events, while trace
history, configured geometry, and temporary page ownership live in each game
instance. The CoCo build expands the hooks to nothing. ABI-14 builds include
the backend, but live active-trace MAME acceptance is still pending; see the
[current trace status](../../WILDBITS-ENGINE.md#native-trace-backend-integration-abi-14-in-progress).
