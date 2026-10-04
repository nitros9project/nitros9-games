#!/usr/bin/env python3
"""Create diagnostic color bars in the engine's combined picture format."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.write_bytes(bytes(((4 + y // 14) & 15) << 4 | (x // 10)
                             for y in range(168) for x in range(160)))
print(f'{args.output}: 26880 bytes, low-nibble color bars, varying high-nibble priority')
