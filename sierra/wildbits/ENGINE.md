# Wild Bits engine structure

## What `objs/wildbits_engine.asm` does

The existing untracked scaffold sets `WILDBITS` and includes `sierra.asm`,
`mnln.asm`, `scrn.asm`, and `shdw.asm`. It is excluded from the build.
Those are complete CoCo OS-9 module sources, each with its own module header,
trailer, data definitions, and common labels such as `start`, `name`, and `eom`.
They also select backends that deliberately reject an unimplemented Wild Bits
target. An outer `EMOD` cannot convert that collection into one native module.
No native program requires this scaffold; it has been left intact.

## One module can still be the right eventual result

Including several assembly files is a useful way to organize **one program**,
provided they are body/data includes with explicit interfaces and one owning
`MOD`/`EMOD` pair. This is also the structure described by the porting guide.
Source-file boundaries do not require runtime dispatch or extra instructions.

The current King's Quest I binaries total 31,572 bytes:

| Module | Bytes |
| --- | ---: |
| `sierra` | 1,650 |
| `mnln` | 25,442 |
| `scrn` | 1,996 |
| `shdw` | 2,484 |

That makes a single resident native program a reasonable initial target,
subject to the real converted size and process mapping budget. It is not
proof that the finished port fits. The guide's 40,192-byte code budget assumes
an 8 KB private data area and at most two simultaneous one-block service
windows. More physical RAM does not enlarge the process's logical space.

The required conversion is deeper than removing module headers:

- Code references must be position independent; the native code must not
  require the old module load addresses or mutate linked code.
- Each process owns its state. Shared includes use a documented private
  data base rather than absolute CoCo data addresses.
- Cross-module remapping calls become explicit calls between converted
  routines, with register/state contracts. Any remaining banked component
  needs a real loader and bounded mapping lifetime.
- The combined picture/priority buffer, resources and framebuffers stay
  outside the resident state where needed, accessed through OS-managed
  windows. Mapping registers are not an application portability interface.
- Display, input, visibility, timing and sound follow their native platform
  contracts. The existing CoCo assembly remains a working reference.

## Building and proving reusable pieces

The current native executables are probes for implemented interfaces. They
are not separate processes intended to form the eventual game interpreter.

`wbpic.asm` owns one OS-9 module and exercises combined-buffer presentation.
`wbres.asm` owns another small test module and includes `resource-data.asm`
and `resource-code.asm`. `wbdecode.asm` now includes those same resource routines
directly, together with converted command, line, fill and mapped-storage bodies. It does not fork
`wbres` or reimplement its loader. `resource-cli.asm` supplies shared probe
argument/output handling. Each executable still has exactly one module header.

The current flow is:

```text
Native resource step: picDir + vol.N -> LoadPicture -> AGI command bytes
Presentation step:   combined color/priority buffer -> wbpic -> terminal bitmap
Native decoder:     F0-FA command bytes -> owned physical buffer, one mapped window
Still to convert:    compression, mapped logic/view resources and interpreter integration
```

The host renderer supplies the reference while the native decoder is converted.
The decoder has private state, bounded reads and immutable relative dispatch.
Mapped picture storage and bounded scanline fill now replace fixed CoCo buffer
and stack addresses. The private command buffer and fill stack still consume
two process blocks; integration must budget interpreter state alongside them.
Pen conversion and direct presentation now work together in `wbrun`.
The interpreter must next gain compressed logic/view storage.
The old fixed-address `shdw` body cannot simply be linked into the new module.

`wbrun.asm` now owns one module and includes the resource loader, decoder and
shared presentation routines directly. It does not fork the probes. The same
small presentation includes are used by the existing viewer, whose binary is
unchanged. This proves the single-program source structure before bringing in
the main interpreter; it does not claim that displaying a resource is gameplay.
