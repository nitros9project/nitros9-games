# Shared Sierra routines

These are body includes used by both the CoCo modules and native Wild Bits
owners. They allocate no state and contain no OS-9 module header.

- `agi-command-table.asm`: one command catalog, expanded into CoCo handler
  descriptors or native operand-count bytes at assembly time.
- `object-distance.asm`: visible-object Manhattan distance with saturation;
  owners supply private scratch and result-store adapters.
- `object-block-test.asm`: strict rectangle containment, with owner-selected
  state addressing at assembly time.
- `picture-coordinates.asm`: common coordinate clamping and command-byte
  detection, with assembly-time contiguous/bounded input selection.
- `object-direction-tables.asm`: movement-direction to view-loop selection.
- `picture-line.asm`: integer line drawing with owner-provided direct-page
  coordinate and scratch symbols. Calls `SbuffPlot` through a direct `LBSR`.
- `picture-pen.asm`: pen geometry and texture sequence, using the same plotting
  interface and owner-provided direct-page scratch symbols.
- `picture-pen-tables.asm`: immutable circle masks and index tables.

The CoCo `shdw.asm` and Wild Bits decoder include these exact files. Owners
supply different symbol addresses without duplicating the algorithms. The
existing CoCo plot implementation uses contiguous storage; the Wild Bits
implementation uses bounded OS-managed mapping windows. Selection takes place
in `platform/picture-storage.asm` and emits no dispatch instructions.

This is the first actual shared-source migration. The native logic interpreter
and CoCo `mnln.asm` still have different state layouts and command implementations;
that reconciliation is unfinished. Moving a native-only file here would not,
by itself, make it shared with CoCo.
