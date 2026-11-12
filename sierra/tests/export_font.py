#!/usr/bin/env python3
"""Export the shared assembler font exactly; no platform-specific glyph copy."""
from pathlib import Path
import re
import sys
source = Path(__file__).resolve().parents[1] / 'objs/font-data.asm'
values = re.findall(r'\$([0-9A-Fa-f]{2})', source.read_text())
font = bytes(int(value, 16) for value in values)
if len(font) != 1024:
    raise SystemExit(f'expected 128 eight-row glyphs, found {len(font)} bytes')
Path(sys.argv[1]).write_bytes(font)
