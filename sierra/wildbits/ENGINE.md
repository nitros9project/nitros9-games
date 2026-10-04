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
and `resource-code.asm`. The future native picture decoder can include those
same resource routines directly; it will not need to fork `wbres` or reimplement
its loader. This keeps executable tests on the code that will be integrated.

The current flow is:

```text
Native resource step: picDir + vol.N -> LoadPicture -> AGI command bytes
Presentation step:   combined color/priority buffer -> wbpic -> terminal bitmap
Still to convert:    AGI command bytes -> native picture decoder -> combined buffer
```

The host renderer continues to provide the expected combined buffer while
the native decoder is converted. Decoder state, mapped-buffer access and
malformed-command boundaries must be resolved before importing the existing
`shdw` body. Merely linking that fixed-address renderer would recreate the
problem the portability work is intended to remove.
