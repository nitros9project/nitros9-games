#!/usr/bin/env python3
"""Run unchanged KQ3 startup through its formatted clock and enabled input."""
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise, idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    game = ROOT/'kingsquest3'
    files = {'/game/'+p.name: p.read_bytes() for p in game.iterdir()
             if p.name.startswith('vol.') or p.name in
             ('logDir', 'picDir', 'sndDir', 'viewDir', 'object', 'words.tok')}
    with tempfile.TemporaryDirectory(prefix='sierra-kq3-startup-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp)/'idle.rom'), timeout=1800)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\1'); d.write(0xffa8, bytes(range(8)))
            error, output, state = exercise(
                d, files, arguments=b'/game 0\r', module='wbgame', base=0xa000,
                database=0, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, cycle_limit=30,
                keyboard_by_cycle={2: (b' \r', 0), 10: (b' \r', 0)},
                os_call_limit=150000)
            assert error == 228, ('expected planned interrupt', error)
            assert state['cycles'] == 30
            assert state['vmgameid'] == b'KQ3\0\0\0\0\0'
            assert state['vmvariables'][0] == 7
            assert state['vminputenabled'] == b'\1'
            assert state['asseterror'] == state['vmerror'] == b'\0'
            # exercise also verifies terminal restoration, private allocations,
            # shared helper/code immutability and resource/path cleanup.
            print('PASS: unchanged KQ3 root/startup reaches room 7, formats its clock, enables input, survives 30 cycles and cleans up on planned interrupt; CPU services are simulated, full gameplay/MAME not claimed')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
