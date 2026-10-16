#!/usr/bin/env python3
"""Picture replacement removes old credits while retaining outside text rows."""
from pathlib import Path
import re
import subprocess
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
from check_wbplay import fixture

ROOT = Path(__file__).resolve().parents[1]


def main():
    font = bytes(int(v, 16) for v in re.findall(r'\$([0-9A-F]{2})',
        (ROOT / 'objs/font-data.asm').read_text()))
    with tempfile.TemporaryDirectory(prefix='wbcredits-') as tmp:
        d, emu = start_cpu(idle_rom(Path(tmp) / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for top in range(5):
                outside = 24 if top < 4 else 0
                # Paint old credits first, then replace the picture. Repeated
                # show.pic must not resurrect those saved overlay cells.
                script = bytes([103, top+2, 10, 1, 103, outside, 2, 2,
                                111, top, outside, outside, 3, 0, 1,
                                24, 0, 25, 0, 26, 26, 134, 1, 0])
                error, frame = exercise(d, fixture(script, b'\xff',
                    message=[b'Designed and written by', b'A']), module='wbgame',
                    base=0xa000, database=0x0000, window=0x8000,
                    blocks=None, multiple=True, firstblock=0x10,
                    frame_capture=True)
                assert not error, (top, error)
                expected = bytearray([1]) * 76800
                expected[top*8*320:(top+21)*8*320] = bytes([16]) * (21*8*320)
                for y in range(8):
                    for x in range(8):
                        expected[(outside*8+y)*320+16+x] = (
                            16 if font[ord('A')*8+y] & (128 >> x) else 1)
                assert frame == expected, ('stale credits or outside text lost', top)
            print('PASS: all five picture offsets replace old credits, preserve outside text and survive repeated show.pic; complete cleanup')
        finally:
            d.s.close(); emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill(); emu.wait(timeout=5)


if __name__ == '__main__':
    main()
