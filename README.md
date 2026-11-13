# NitrOS-9 Games

This repository contains games, game data, and bootable disk-image builds for
[NitrOS-9](https://github.com/nitros9project/nitros9).

## Contents

- `arcadepak` — Smash, Shanghai, and Thexder
- `flightsim2` — Flight Simulator II
- `koronis` — Koronis Rift
- `kyumgai` — Kyum-Gai
- `mmission` — Microscopic Mission
- `pacos9` — Pac-OS9
- `rescueof` — Rescue on Fractalus
- `rogue` — Rogue
- `sierra` — Sierra AGI games and shared runtime sources
- `subsim` — Sub Battle Simulator

## C source ports

The following archive games have independent c3 cross-builds:

- `hordes` — Hordes & Holes
- `sokoban` — Sokoban, including all 50 levels
- `kalah` — Kalah and Dead-Pan
- `reversi` — Joel Rees’s graphical Reversi
- `walk` — James Delaney’s animated screen saver/demo
- `adventure` — Crowther/Woods Adventure
- `cocothello` — graphical Othello
- `solitaire` — Pyramid Solitaire

Build the sibling c3 host tools/runtime first, then build or launch a port:

```sh
make -C ../nitros9-languages/c3 runtime
make -C sokoban
make -C sokoban disk
make -C sokoban run
```

These ports build independently of the aggregate target. Each supplies a
private NitrOS-9 boot disk and MAME launcher; see its README for requirements,
controls, provenance, and validation. `make -C <port> clean` removes generated
outputs and listing/map files.

## Building

The games build against a neighboring NitrOS-9 source tree. Set
`NITROS9DIR` if it is not located at `../nitros9`:

```sh
export NITROS9DIR=/path/to/nitros9
make
```

Each game builds its own kernel track, bootfile, and disk image from the
modules it requires. Multi-disk Sierra games also format their additional
data-only disks.

Individual games can be built from their own directories. For example:

```sh
make -C rogue
```

Sierra games can likewise be built from their own directories:

```sh
make -C sierra/kingsquest3
```

See [Sierra instance support](sierra/README.md) for concurrent-game terminal,
memory, and bootfile requirements.

The imported sources retain their original notices and licensing terms where
provided. No repository-wide license is asserted over third-party game data.
