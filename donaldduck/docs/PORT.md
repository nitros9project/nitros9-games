# Port survey and interfaces

Guide: https://github.com/jfed6000/f256_porting, revision
`a7065466c9754e26877b651bca730c76e1bdd865`, read on 2026-10-04. The guide was
reference material; its suggested workflows were evaluated against this game.
No actions were taken to publish, send, or modify its repository.

## Original

The source disks are OS-9 RBF images, 161,280 bytes each. DDP1 contains DONALD
(6,512 bytes, CRC $430349), the CoCo SOUND driver, DDSND descriptor, title and
logo. DDP2 contains six OS-9 subroutine modules, eleven pictures across both
disks, and eighteen packed shape/data assets. This is not an AGI interpreter
package. `original/` preserves extracted bytes; `*.disasm` are exploratory
f9dasm listings. The listings deliberately preserve the binary offsets and
contain data disassembled as instructions, so they are not rebuild sources.

DONALD establishes its process-data pointer at DP:$08 and uses U as an
auxiliary stack at data+$374C. Activity calls store a module-relative routine
offset at DP:$0A and dispatch into DONALD’s shared services. This byte pair
must not be used as the adapter’s signal flag. Some original text and tables
are written in place, so retained module sharing has not been made safe for
concurrent instances.

## Graphics seam

| Original module offset | Original purpose | Native replacement |
|---|---|---|
| $0679 | Obtain CoVDG buffers and second screen | Bitmap allocation, palette/layer setup, private software screens, window reservation |
| $054F | Display screen selected by DP:$77 | Convert selected private screen into bitmap zero; retain original sleep |
| $0055, $0302 | CoCo joystick GetStat | Scale native stick 0..255 to legacy 0..63; add held keyboard controls |
| $0AB5 | Blocking keyboard read | Present the current software screen before reading |
| $02F8 | Signal intercept | Rebase the intercept U pointer and update private flags |
| $0013 | Entry | Clear original process RAM before original initialization |
| $01F4 | Terminal restore on normal exit | Release visibility registration, mappings and bitmap, silence PSG, then original terminal restore |

The original blitters, shape restores, text drawing, collision data and screen
copy at $079C remain intact. Their screen pointers at DP:$0E and DP:$10 point
to process-private packed screens at data+$3900 and data+$5100. The display
adapter reads 32 bytes per original row, expands each two-bit pixel into two
one-byte bitmap pixels, and centers 256x192 inside 320x240. Palette index zero
is reserved; output uses indices 1..4. Graphics-driver allocation owns the
bitmap; the program does not touch VICKY or MMU registers directly.

Main $06E9’s disk-side prompt is removed because all assets are present.
All six `/D0/CMDS/` activity prefixes become `/s0/CMDS/` with no offset shift.
The build validates the original bytes at every code patch and pins the source
module’s SHA-256. The new code is appended before the CRC, and module size,
data size, header parity and CRC are regenerated. The ORG in platform.asm
only gives the assembler module-relative offsets; no runtime address is forced.

## Logical-space plan

| Occupant | 8 KB logical blocks |
|---|---:|
| DONALD, including adapter | 1 |
| Private data, $6C00 bytes | 4 |
| Largest activity module, 6,314 bytes | 1 |
| Reserved upper mapping | 1 |
| Bitmap service mapping | 1 |
| Total | 8 |

F$MapBlk chooses the highest free logical hole. $E000 is a possible result,
but its last $300 bytes decode fixed I/O rather than ordinary RAM. A complete
8 KB copy through that window corrupts MMU, interrupt, and display registers.
The adapter therefore maps a bitmap block once as a guard, never accesses its
bytes, and retains it until exit. Actual bitmap work uses a second one-block
window below $E000. A guard can share the bitmap’s physical block because
mapping does not allocate or duplicate that RAM. Actual mappings always use
the returned U, and spans split at the physical 8 KB boundary. An unexpected
$E000 service window is unmapped and rejected. The bitmap itself is allocated
outside logical space by the graphics driver.

There are never more than two one-block service mappings. The guard remains
while activity code is loaded; all maps are released before SS.FScrn.

## Input and lifecycle

Native stick buttons map to the original $FF pressed convention. The original
reader waits for release and produces bit 7 on the transition. Held arrows
supply the extremes of the legacy axes. Sierra interprets increasing Y as up,
so native joystick Y is inverted and Up supplies 63 while Down supplies zero.
Joystick polls do not redraw; frame commits and blocking key reads present the
screen. Frame commits yield for one tick after conversion rather than three. Space is accepted both as key-sense
bit 7 and as an ordinary held code, covering the guide’s K2/Jr2 distinction.
Q is polled during joystick reads, frame commits, and sound notes, and waits
for release while draining queued input before using the original quit path.

F$Icpt registers the original auxiliary-stack U, not the data-area base.
NativeSignal subtracts $374C before accessing private flags and does not rely
on the interrupted DP. $81/$82 set/clear Hidden; abort signals use a separate
Aborted byte. Bitmap work waits while hidden. Sound mutes and waits between
notes while hidden. The original wall-clock job timers have not been adjusted
for hidden time.

Bitmap allocation failure is not treated as permission to adopt another
application’s bitmap. Ordinary error/quit paths release only resources owned
by this process. The original activity unlink path is retained on Q exit.
Emulator free-memory snapshots must match before and after ordinary exit.

## Sound seam

Original $0F42 takes an effect number 1..20. The table at $0FBE contains
module-relative offsets to duration/pitch pairs terminated by zero duration.
SOUND’s CoCo DAC delay loop makes a square wave; its pitch byte controls the
half-period and each duration unit spans approximately 192 loop iterations.

The adapter keeps all twenty scripts and replaces the DAC with PSG channel
zero through the documented fixed decode at $FF92. The chosen tone period is
`min(1023, 4*pitch + 12)`; pitch zero mutes. Duration uses `floor(duration/5)+1`
OS ticks. These are approximations to the original 895 kHz 6809 timing, with
short notes quantized to one tick. The two software-hardware-specific modules
SOUND and DDSND are not loaded on Wildbits. Other PSG channels are not used.
Cleanup silences the game’s channel. Mixer gain and physical sound quality
still need hardware comparison.

The CPU test executes actual native sound code with trapped PSG writes and
OS calls. The emulator audio capture contains nonzero PSG output; it is not a
reference comparison or a physical-audio acceptance test.
