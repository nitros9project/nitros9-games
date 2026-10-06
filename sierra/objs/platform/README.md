# Sierra platform features

This directory groups platform-specific code, private state and assembly
bindings by feature. It contains 34 assembly files, down from 208. Shared game
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

Eight substantial native implementation files retain their existing names:
condition stream, decoder, formatter, math, logic execution, object commands,
parser and string commands. They mix macro definitions with executable bodies;
keeping them as complete implementations avoids the assembler's handling of
macro parameters inside skipped conditional sections.

The old per-operation selector files have been removed. Their compile-time
CoCo/Wild Bits selection and unsupported-backend checks now appear at the
owner's inclusion site.

Verification: all 56 CoCo engine modules (four modules for 14 titles) and native
`wbgame` match the preceding binaries byte for byte. Native probes also build.
