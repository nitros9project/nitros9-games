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

The imported sources retain their original notices and licensing terms where
provided. No repository-wide license is asserted over third-party game data.
