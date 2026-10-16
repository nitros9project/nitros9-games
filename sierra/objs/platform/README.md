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

Verification: all 56 CoCo engine modules (four modules for 14 titles) and native
`wbgame` match the preceding binaries byte for byte. Native probes also build.

The native text-store loop assembles into the existing `wbstate` auxiliary
module and executes read-only while linked. Its variables and text cells remain
private to the caller. The frontend caches the validated entry and releases the
module during cleanup; clearing a text screen preserves that reference. Install
the matching helper for text output. Source grouping stays in
`wildbits-text-ui.asm`; no additional platform file is needed.

The same grouped text UI source supplies the immutable modal wait/key loop to
`wbstate`. The resident passes a read-only callback table, and each game keeps
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

Screen shake lives in the grouped Wild Bits graphics source and uses the existing
immutable helper, private callbacks and idle fill scratch. It maps one bank at
a time and releases mappings before clock, sound and foreground calls.

The menu frontend stays in grouped text UI, with display/navigation in that
same source's cold section. Its callback table reuses resident presentation
and foreground services; ordinary game cycles have no additional helper calls.

Joystick handling belongs to grouped Wild Bits input, calls the terminal's
`SS.Joy` interface and leaves hardware access to its driver. Its private
movement ownership and button edges stay separate from shared code and saves.


## Separate UI and persistence providers (ABI 8)

The current package is `wbgame`, `wbui`, `wbstate` and `wbfont`. Install the
three executable modules from the same ABI-12 build. UI/audio code now belongs
to the immutable `wbui` provider; `wbstate` supplies the bounded private copy
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
UI loader/cache; screen calls retain their distinct interface. A cached shake
releases engine mappings before borrowing the framebuffer window. See the
[ABI-12 ownership and verification record](../../WILDBITS-ENGINE.md#deferred-menu-requests-and-shared-ui-entry-abi-12).
