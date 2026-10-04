# Validation status — 2026-10-04

Validated DONALD: **7,794 bytes**, OS-9 CRC **$56A281**, private data **$6C00**.
Code, data, activity, and two mapping windows fit the eight logical blocks.
The local validated 2 MiB Jr2 image contained this module and the combined
assets. Boot firmware and the base OS disk must be supplied separately.

## Passed

- Updated bitmap conversion: paired stores, unrolled copy loops, exact pixel
  verification and physical Return/Space key-field boot/run/quit testing.

- Original module identity and SHA-256 pin, patch-byte assertions, regenerated
  header parity and CRC, one-block code budget.
- Actual assembled 6809 execution: bitmap initialization and refusal to adopt
  an existing bitmap, reserved upper window, private signal state with an
  arbitrary interrupted DP and the original intercept U convention.
- All four arrow directions executed through Sierra’s original direction reader,
  including corrected inverted joystick Y; input polls retain required sprite
  presentation and frame commits yield for one tick.
- Held arrows, original joystick scaling and buttons, Space in both K2/Jr2
  representations, preservation of the original auxiliary-stack U.
- Every output pixel of both packed screens at two code/data placements,
  including every 8 KiB boundary and a mapping failure partway through output.
- Execution of the first original sound script: 111 duration/pitch notes and
  302 PSG writes, with the caller’s registers restored.
- Initial town sprite has an explicit display commit and a screen-pixel
  regression assertions verifying Donald remains visible while idle and moves
  right, up and down in the expected screen directions.
- Real NitrOS-9 in the Wildbits `wbjr2` MAME fork: title, difficulty selection,
  instruction dismissal, town with Donald displayed, ordinary Q exit and shell
  completion marker.
- Diagnostic direct entry into **PRODUCE, AIRPORT, RAILROAD, PLAYGROUND, STORES,
  and TOYSTORE**, original asset loading and screens, Q exit, shell marker,
  and identical `mfree` output before/after each run.
- Boot/run/quit and identical before/after free memory using a private copy of
  the **actual packaged disk image**, without reinstalling the module.
- Emulator WAV capture contains nonzero PSG output during the introductory
  music (48 kHz stereo; sampled segment peak 497/32767). This proves the
  emulated sound path produced audio, not its perceptual accuracy.

The MAME checkout reports revision `078e0eeb`; the OS image is the local
`c45760a` Wildbits/multiterm build. Tests run with `wbjr2`, turbo BIOS, private
firmware/disk copies and native keyboard input. The emulator’s timing is not
used as evidence of physical performance.

## Not yet verified

- Physical K2 or Jr2 hardware, core-specific mixer gain and sound quality.
- A complete earning/shopping/playground session, end-of-game behavior,
  all difficulty levels, and every animation branch.
- Concurrent instances. The retained original modules share mutable content;
  use one game instance.
- Forced kill, persistent cleanup failures, restoration over an arbitrary
  pre-existing graphics application, or job-timer compensation while hidden.
- Analog CoCo artifact-color fidelity and byte/cycle-equivalent DAC playback;
  the display and PSG adaptation are documented approximations.

## Artifacts

- `../README.md`: running, installing and rebuilding.
- `../src/platform.asm`: native adapter; retained game code is binary.
- `../tools/build.py`: reproducible, asserted patching and OS-9 module build.
- `../tools/make_image.py`: installation into a private base-image copy.
- `../tests/check_platform.py`: actual 6809 CPU/service-contract tests.
- `../tests/check_mame.py`: boot, activity, input, exit and memory tests.
- `../build/patches.json`: original fingerprint and code-patch destinations.
- `ORIGINAL-SHA256.json`: all extracted original file fingerprints.
