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

Condition traversal, picture decoding, formatting, math, logic execution,
object commands, parsing and string commands now reside in their feature
files. Their local macro definitions live in the corresponding binding files,
loaded once before the body is emitted. Timing keeps its small clock interface
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
